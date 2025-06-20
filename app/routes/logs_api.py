from flask import Blueprint, jsonify
import os
from app.features.redis.redis_client import get_redis_client

logs_blueprint = Blueprint('logs', __name__)

def is_meaningful_log(line):
    return (
        "State Machine initialized" in line or
        "Transitioning" in line or
        "Performing data" in line or
        ("INFO -" in line and "127.0.0.1" not in line)
    )

def is_process_complete(lines):
    """İşlemin tamamlanıp tamamlanmadığını kontrol eder"""
    for line in reversed(lines):  # En son satırlardan başla
        if "Final state reached" in line or "Processing complete" in line:
            return True
    return False

@logs_blueprint.route('/latest', methods=['GET'])
def get_latest_log():
    logs_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.isdir(logs_dir):
        return jsonify({'log': '', 'complete': False})
        
    log_files = sorted(
        [f for f in os.listdir(logs_dir) if f.startswith('state_machine_')],
        reverse=True
    )
    
    if not log_files:
        return jsonify({'log': '', 'complete': False})
    
    log_path = os.path.join(logs_dir, log_files[0])

    # Redis'ten kontrol
    redis_client = get_redis_client()
    redis_complete = redis_client.get("state_machine:complete")
    is_complete = redis_complete == b"1"

    filtered = []
    try:
        with open(log_path, encoding='utf-8') as f:
            lines = f.readlines()
            filtered = [line if line.endswith('\n') else line + '\n' for line in lines if is_meaningful_log(line)]
    except Exception as e:
        print(f"Log okuma hatası: {e}")

    return jsonify({
        'log': ''.join(filtered), 
        'complete': is_complete
    })