import logging
import sys

class NymLogging:

    def __init__(self):
        log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(log_format)

        self.logHandler = logging.getLogger('nym')
        self.logHandler.setLevel(logging.DEBUG)
        self.logHandler.addHandler(handler)
