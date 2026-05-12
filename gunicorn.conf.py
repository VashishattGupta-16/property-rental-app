import os
import multiprocessing

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
try:
    workers = max(1, int(os.environ.get("WEB_CONCURRENCY", "")))
except ValueError:
    workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2
