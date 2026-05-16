import logging

class UptimeRobotFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        if 'UptimeRobot' in msg:
            return False
        # Also filter standard health check logs without User-Agent in msg
        # if they come from the router, though those are hard to distinguish
        return True
