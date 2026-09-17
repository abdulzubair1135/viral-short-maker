import logging
import sys
from pathlib import Path
from backend.app.config import LOGS_DIR

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

LOG_FILE = LOGS_DIR / "studio.log"

class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                stream.write(msg.encode("ascii", "replace").decode() + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logger(name: str = "studio") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    c_handler = SafeStreamHandler(sys.stdout)
    f_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")

    c_format = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    f_format = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

logger = setup_logger("studio")
