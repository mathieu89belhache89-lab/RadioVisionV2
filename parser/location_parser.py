import json
import re
import unicodedata
from pathlib import Path

from config import DATA_DIR


class LocationParser:

    MANUAL_LOCATIONS = {
        "mission row": "Mission Row",
        "mission raw": "Mission Row",
        "mission rho": "Mission Row",
        "mission ro": "Mission Row",
        "mission rô": "Mission Row",
        "mission road": "Mission Row",

        "sandy shores": "Sandy Shores",
        "sandy shore": "Sandy Shores",
        "sandy shoress": "Sandy Shores",
        "sandishore": "Sandy Shores",
        "sandi shore": "Sandy Shores",
        "sand dicher": "Sandy Shores",
        "sand diche": "Sandy Shores",
        "110 heures": "Sandy Shores",
        "110h": "Sandy Shores",
        "110 h": "Sandy Shores",

        "paleto bay": "Paleto Bay",
        "paleto": "Paleto Bay",
        "paletto": "Paleto Bay",
        "palais taubeille": "Paleto Bay",
        "palais-taubeille": "Paleto Bay",
        "palet au bay": "Paleto Bay",

        "legion square": "Legion Square",
        "les jeans square": "Legion Square",
        "le jeans square": "Legion Square",
        "legion": "Legion Square",

        "casino": "Casino",
        "bijouterie": "Bijouterie",
        "mirror park": "Mirror Park",
        "del perro": "Del Perro",
        "delpero": "Del Perro",
        "canaux": "Canaux",
    }

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
        text = str(text).lower()

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

    def make_manual_result(self, name):
        return {
            "name": name,
            "id": None,
            "category": "Manuel",
            "type": "zone",
        }

    def find(self, text: str):
        text_clean = self.clean(text)

        for alias, name in self.MANUAL_LOCATIONS.items():
            alias_clean = self.clean(alias)

            if re.search(r"\b" + re.escape(alias_clean) + r"\b", text_clean):
                return self.make_manual_result(name)

        for item in self.aliases:
            alias = item["alias_clean"]

            if len(alias) <= 2:
                continue

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text_clean):
                return item

        return None
