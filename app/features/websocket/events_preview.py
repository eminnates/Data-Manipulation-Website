import json
import os
import time
from app.features.websocket.extensions import socketio
from flask_socketio import emit
from flask import current_app, request
from app.domain.models import ProjectContext
from app.services.cleaning.preview import PreviewPipelineRunner
from app.infrastructure import metrics
import uuid
from threading import Lock
from app.features.redis.redis_client import get_redis_client

# Sadece aynı process içindeki canlı runner objesini cancel edebilmek için tutulur.
_ACTIVE_PREVIEW_RUNNERS = {}
_ACTIVE_PREVIEW_LOCK = Lock()

REDIS_SESSION_PREFIX = 'preview:session:'  # key = prefix + session_id

def _redis_set_session(session_id: str, data: dict):
    try:
        r = get_redis_client()
        r.hset(REDIS_SESSION_PREFIX + session_id, mapping={k: json.dumps(v) for k, v in data.items()})
        # Varsayılan TTL (örn. 30 dk) – env ile değiştirilebilir
        ttl = int(os.environ.get('PREVIEW_SESSION_TTL', '1800'))
        r.expire(REDIS_SESSION_PREFIX + session_id, ttl)
    except Exception:
        pass

def _redis_update_status(session_id: str, status: str, **extra):
    payload = {'status': status, **extra}
    _redis_set_session(session_id, payload)

def _redis_get_session(session_id: str):
    try:
        r = get_redis_client()
        raw = r.hgetall(REDIS_SESSION_PREFIX + session_id)
        if not raw:
            return None
        out = {}
        for k, v in raw.items():
            try:
                out[k] = json.loads(v)
            except Exception:
                out[k] = v
        return out
    except Exception:
        return None

def _preview_callback(event_name: str, payload: dict):
    try:
        socketio.emit(event_name, payload)
        # Metrics: step done, error, cancelled etc.
        if event_name == 'preview_step_done':
            metrics.inc('preview_steps_total')
            metrics.observe('preview_step_ms', payload.get('ms', 0))
        elif event_name == 'preview_error':
            metrics.inc('preview_errors_total')
        elif event_name == 'preview_cancelled':
            metrics.inc('preview_cancelled_total')
        elif event_name == 'preview_complete':
            metrics.inc('preview_sessions_completed_total')
    except Exception as e:
        current_app.logger.error(f"Preview callback emit failed: {e}")

@socketio.on('preview_pipeline_request')
def handle_preview_pipeline(data):
    # Identity from websocket connection (set during connect)
    identity = request.environ.get('ws.identity', 'anon')
    from app.utils.rate_limit import check_rate_limit
    rl = check_rate_limit(identity, 'ws_preview_request')
    if not rl.allowed:
        emit('preview_error', {'error': 'rate_limit_exceeded', 'reset': rl.reset})
        return
    project_name = data.get('project_name')
    file_name = data.get('file_name')
    steps = data.get('steps', [])
    # Varsayılan güvenli limit (env ile override edilebilir)
    default_limit = 5000
    try:
        from os import environ
        default_limit = int(environ.get('PREVIEW_DEFAULT_SAMPLE_LIMIT', default_limit))
    except Exception:
        pass
    raw_limit = data.get('sample_limit')
    sample_limit = None
    if raw_limit is None:
        sample_limit = default_limit
        limit_source = 'default'
    else:
        try:
            val = int(raw_limit)
            if val <= 0:
                sample_limit = default_limit
                limit_source = 'corrected_non_positive'
            else:
                # Hard upper guard (örn. 200k) – aşılırsa clamp
                hard_cap = int(environ.get('PREVIEW_SAMPLE_HARD_CAP', '200000'))
                if val > hard_cap:
                    sample_limit = hard_cap
                    limit_source = 'clamped_hard_cap'
                else:
                    sample_limit = val
                    limit_source = 'client'
        except Exception:
            sample_limit = default_limit
            limit_source = 'parse_error'
    session_id = data.get('session_id') or str(uuid.uuid4())

    if not all([project_name, file_name]):
        emit('preview_error', {'session_id': session_id, 'error': 'Proje veya dosya adı eksik.'})
        return
    if not isinstance(steps, list) or len(steps) == 0:
        emit('preview_error', {'session_id': session_id, 'error': 'Geçersiz veya boş steps listesi.'})
        return

    with _ACTIVE_PREVIEW_LOCK:
        old = _ACTIVE_PREVIEW_RUNNERS.get(session_id)
        if old:
            try:
                old.cancel()
            except Exception:
                pass

    ack_payload = {
        'session_id': session_id,
        'status': 'accepted',
        'step_count': len(steps),
        'sample_limit': sample_limit,
        'sample_limit_source': limit_source
    }
    emit('preview_ack', ack_payload)
    metrics.inc('preview_sessions_started_total')
    _redis_set_session(session_id, {**ack_payload, 'created_at': time.time()})

    def _background_job():
        try:
            context = ProjectContext(project_name=project_name, file_name=file_name)
            df = context.get_data(use_cache=True)
        except FileNotFoundError:
            socketio.emit('preview_error', {'session_id': session_id, 'error': f'Dosya bulunamadı: {file_name}'})
            return
        except Exception as e:
            socketio.emit('preview_error', {'session_id': session_id, 'error': f'Veri yüklenemedi: {e}'})
            return

        runner = PreviewPipelineRunner()
        with _ACTIVE_PREVIEW_LOCK:
            _ACTIVE_PREVIEW_RUNNERS[session_id] = runner
        try:
            _redis_update_status(session_id, 'running', started_at=time.time())
            metrics.inc('preview_sessions_running_total')
            result = runner.run(df, steps, _preview_callback, session_id=session_id, sample_limit=sample_limit)
            # preview_complete runner callback zaten emit etti; ancak sample_limit bilgisini pekiştirmek istersek:
            socketio.emit('preview_meta', {
                'session_id': session_id,
                'sample_limit': sample_limit,
                'sample_limit_source': limit_source,
                'final_rows': int(result['df'].shape[0]),
                'final_cols': int(result['df'].shape[1])
            })
            _redis_update_status(session_id, 'finished', finished_at=time.time(), final_rows=int(result['df'].shape[0]), final_cols=int(result['df'].shape[1]))
            metrics.inc('preview_sessions_finished_total')
        finally:
            with _ACTIVE_PREVIEW_LOCK:
                _ACTIVE_PREVIEW_RUNNERS.pop(session_id, None)
            # Eğer cancel flag'i set edilmişse state'i güncelle
            existing = _redis_get_session(session_id) or {}
            if existing.get('status') != 'finished':
                _redis_update_status(session_id, 'terminated')
                metrics.inc('preview_sessions_terminated_total')

    socketio.start_background_task(_background_job)

@socketio.on('preview_cancel')
def handle_preview_cancel(data):
    session_id = data.get('session_id')
    if not session_id:
        emit('preview_error', {'error': 'session_id gerekli.'})
        return
    with _ACTIVE_PREVIEW_LOCK:
        runner = _ACTIVE_PREVIEW_RUNNERS.get(session_id)
        if runner:
            runner.cancel()
            emit('preview_cancel_ack', {'session_id': session_id, 'status': 'cancelling'})
            _redis_update_status(session_id, 'cancelling', cancel_requested_at=time.time())
            metrics.inc('preview_sessions_cancelling_total')
        else:
            emit('preview_cancel_ack', {'session_id': session_id, 'status': 'not_found'})
            # Redis kaydı varsa status not_found olarak işaretlenebilir
            if _redis_get_session(session_id):
                _redis_update_status(session_id, 'not_found_local')
