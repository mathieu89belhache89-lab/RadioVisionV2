import json
import re
from pathlib import Path

from config import DATA_DIR


class RadioParser:

    def __init__(self):
        self.file = Path(DATA_DIR) / "radio_codes.json"

        with self.file.open("r", encoding="utf-8") as f:
            self.codes = json.load(f)

        self.pattern = self._build_pattern()

    def _build_pattern(self):
        keys = sorted(self.codes.keys(), key=len, reverse=True)
        escaped = [re.escape(key) for key in keys]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)

    def normalize(self, text: str) -> str:
        text = text.upper()

        replacements = {
            "DIX ZÉRO": "10-0",
            "DIX ZERO": "10-0",
            "DIX UN": "10-1",
            "DIX DEUX": "10-2",
            "DIX TROIS": "10-3",
            "DIX QUATRE": "10-4",
            "DIX CINQ": "10-5",
            "DIX SIX": "10-6",
            "DIX SEPT": "10-7",
            "DIX HUIT": "10-8",
            "DIX NEUF": "10-9",
            "DIX VINGT": "10-20",
            "DIX TRENTE": "10-30",
            "DIX TRENTE ET UN": "10-31",
            "DIX QUATRE VINGT DIX NEUF": "10-99",
            "DIX QUATRE-VINGT-DIX-NEUF": "10-99",

            "10 0": "10-0",
            "10 1": "10-1",
            "10 2": "10-2",
            "10 3": "10-3",
            "10 4": "10-4",
            "10 5": "10-5",
            "10 6": "10-6",
            "10 7": "10-7",
            "10 8": "10-8",
            "10 9": "10-9",
            "10 20": "10-20",
            "10 30": "10-30",
            "10 31": "10-31",
            "10 99": "10-99",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        text = re.sub(r"\b10\s*[- ]\s*(\d{1,2})\b", r"10-\1", text)

        return text

    def parse(self, text: str):
        text = self.normalize(text)

        match = self.pattern.search(text)

        if not match:
            return None, None

        code = match.group(1).upper()
        signification = self.codes.get(code)

        if not signification:
            return None, None

        return code, signification