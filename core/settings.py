import json
from pathlib import Path

from config import DATA_DIR


class Settings:

    FILE = Path(DATA_DIR) / "settings.json"

    DEFAULTS = {
        "theme": "dark",
        "language": "fr",
        "sample_rate": 48000,
        "whisper_model": "base",
        "auto_start": False,
        "debug": False,
    }

    def __init__(self):
        self.data = self.DEFAULTS.copy()

        if self.FILE.exists():
            self.load()
        else:
            self.save()

    def load(self):
        try:
            with self.FILE.open("r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except Exception:
            self.data = self.DEFAULTS.copy()
            self.save()

    def save(self):
        self.FILE.parent.mkdir(parents=True, exist_ok=True)

        with self.FILE.open("w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                indent=4,
                ensure_ascii=False,
            )

    def get(self, key, default=None):
        return self.data.get(
            key,
            self.DEFAULTS.get(key, default),
        )

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def reset(self):
        self.data = self.DEFAULTS.copy()
        self.save()