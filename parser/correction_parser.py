import json
from pathlib import Path

from config import DATA_DIR
from parser.fuzzy_matcher import clean_text


class CorrectionParser:

    def __init__(self):
        self.file = Path(DATA_DIR) / "corrections_audio.json"
        self.data = {
            "locations": {},
            "vehicles": {},
            "codes": {},
        }
        self.load()

    def load(self):
        if not self.file.exists():
            return

        try:
            with self.file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict):
                for section in ["locations", "vehicles", "codes"]:
                    value = data.get(section, {})
                    if isinstance(value, dict):
                        self.data[section] = value
        except Exception:
            pass

    def get_section(self, section):
        return self.data.get(section, {})

    def find_exact(self, section, text):
        text_clean = clean_text(text)

        for bad, good in self.get_section(section).items():
            if clean_text(bad) == text_clean:
                return good

        return None

    def replace_in_text(self, text):
        result = str(text or "")
        result_clean = clean_text(result)

        # Remplacements prudents uniquement si l'expression est présente.
        for section in ["codes", "locations", "vehicles"]:
            for bad, good in self.get_section(section).items():
                bad_clean = clean_text(bad)
                if bad_clean and bad_clean in result_clean:
                    result_clean = result_clean.replace(bad_clean, clean_text(good))

        return result_clean
