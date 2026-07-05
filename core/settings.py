import json
from pathlib import Path

from config import DATA_DIR


class Settings:

    FILE = Path(DATA_DIR) / "settings.json"

    DEFAULTS = {
        "theme": "dark",
        "language": "fr",
        "whisper_model": "base",
        "sample_rate": 48000,
        "auto_start": False,
    }

    def __init__(self):
        self.data = {}

        if self.FILE.exists():
            self.load()
        else:
            self.data = self.DEFAULTS.copy()
            self.save()

    def load(self):
        with open(self.FILE, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self):
        with open(self.FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()