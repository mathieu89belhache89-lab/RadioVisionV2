from pathlib import Path
from datetime import datetime

from config import LOG_DIR


class Logger:

    def __init__(self):
        self.file = Path(LOG_DIR) / "radiovision.log"

        self.file.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, level: str, message: str):

        line = (
            f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
            f"[{level}] {message}\n"
        )

        with self.file.open("a", encoding="utf-8") as f:
            f.write(line)

    def info(self, message: str):
        self._log("INFO", message)

    def warning(self, message: str):
        self._log("WARNING", message)

    def error(self, message: str):
        self._log("ERROR", message)

    def exception(self, exception: Exception):
        self._log("EXCEPTION", str(exception))