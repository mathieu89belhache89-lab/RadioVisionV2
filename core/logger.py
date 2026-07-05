from pathlib import Path
from datetime import datetime

from config import LOG_DIR


class Logger:

    def __init__(self):
        self.file = Path(LOG_DIR) / "radiovision.log"

    def _write(self, level: str, message: str):

        line = (
            f"[{datetime.now():%d/%m/%Y %H:%M:%S}] "
            f"[{level}] {message}\n"
        )

        with open(self.file, "a", encoding="utf-8") as f:
            f.write(line)

    def info(self, message: str):
        self._write("INFO", message)

    def warning(self, message: str):
        self._write("WARNING", message)

    def error(self, message: str):
        self._write("ERROR", message)