import logging
logging.basicConfig(level=logging.INFO)


class LoggingUtils:

    def __init__(self, name, pre_log_msg: str = None):
        self._logger = logging.getLogger(name)
        self.pre_log_msg = pre_log_msg or ""


    # --------------------------------------------
    #              LOGGING HELPERS
    # --------------------------------------------


    def log(self, fn, msg):
        msg = f"{self.pre_log_msg} {msg}"
        fn(msg)

    def info(self, msg):
        return self.log(self._logger.info, msg)

    def warning(self, msg):
        return self.log(self._logger.warning, msg)

    def error(self, msg):
        return self.log(self._logger.error, msg)