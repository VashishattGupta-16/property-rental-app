import os
import multiprocessing
import logging
from gunicorn.glogging import Logger

class UptimeRobotFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return 'UptimeRobot' not in msg

class CustomLogger(Logger):
    def setup(self, cfg):
        super().setup(cfg)
        # Apply the filter to the access logger if it exists
        access_logger = logging.getLogger("gunicorn.access")
        access_logger.addFilter(UptimeRobotFilter())

logger_class = CustomLogger

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
try:
    workers = max(1, int(os.environ.get("WEB_CONCURRENCY", "")))
except ValueError:
    workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2

