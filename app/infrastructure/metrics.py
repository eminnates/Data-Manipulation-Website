import threading
import time
from collections import defaultdict

# Çok basit in-memory metrics store.
# Prod ortamında Prometheus client library tercih edilmeli.

_lock = threading.Lock()
_counters = defaultdict(int)
_histograms = defaultdict(list)
_gauges = {}


def inc(name: str, value: int = 1, **labels):
    key = _key(name, labels)
    with _lock:
        _counters[key] += value


def observe(name: str, value: float, **labels):
    key = _key(name, labels)
    with _lock:
        _histograms[key].append(float(value))


def set_gauge(name: str, value: float, **labels):
    key = _key(name, labels)
    with _lock:
        _gauges[key] = float(value)


def snapshot():
    with _lock:
        # Kopya üret
        counters = dict(_counters)
        hist = {k: list(v) for k, v in _histograms.items()}
        gauges = dict(_gauges)
    # Histograms summarization (count, avg, p50, p95)
    summarized_hist = {}
    for k, arr in hist.items():
        if not arr:
            continue
        arr_sorted = sorted(arr)
        n = len(arr_sorted)
        p50 = arr_sorted[int(0.5 * (n-1))]
        p95 = arr_sorted[int(0.95 * (n-1))]
        summarized_hist[k] = {
            'count': n,
            'avg': sum(arr_sorted)/n,
            'p50': p50,
            'p95': p95
        }
    return {
        'counters': counters,
        'histograms': summarized_hist,
        'gauges': gauges,
        'generated_at': time.time()
    }


def _key(base: str, labels: dict):
    if not labels:
        return base
    parts = [base] + [f"{k}={v}" for k, v in sorted(labels.items())]
    return '|'.join(parts)
