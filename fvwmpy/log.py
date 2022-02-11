import sys
import logging

class _BraceString(str):
    def __mod__(self, other):
        return self.format(*other)
    def __str__(self):
        return self


class _StyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra=None):
        super(_StyleAdapter, self).__init__(logger, extra)

    def process(self, msg, kwargs):
        msg = _BraceString(msg)
        return msg, kwargs
    
def _getloggers(name):
    logger   = _StyleAdapter(logging.getLogger(name))
    debug    = logger.debug
    info     = logger.info
    warning  = logger.warning
    error    = logger.error
    critical = logger.critical
    return logger, debug, info, warning, error, critical

logging.basicConfig(stream=sys.stderr)

