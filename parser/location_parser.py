import json
import re
import unicodedata
from pathlib import Path

from config import DATA_DIR


class LocationParser:

    def __init__(self):
        self.file = Path(DATA_DIR) / "ddr_emplacements_radio.json"

        with self.file.open("r", encoding="utf-8") as f:
            self.locations = json.load(f)

        self.aliases = []

        for location in self.locations:
            name = location.get("name", "")
            aliases = location.get("aliases", [])

            for alias in aliases:
                self.aliases.append({
                    "alias": alias,
                    "alias_clean": self.clean(alias),
                    "name": name,
                    "id": location.get("id"),
                    "category": location.get("category"),
                    "type": location.get("type"),
                })

        self.aliases.sort(
            key=lambda x: len(x["alias_clean"]),
            reverse=True
        )

    def clean(self, text: str) -> str:
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = text.replace("'", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def find(self, text: str):
        text_clean = self.clean(text)

        for item in self.aliases:
            alias = item["alias_clean"]

            if len(alias) <= 2:
                continue

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text_clean):
                return item

        return None