import json
import re
import unicodedata
from pathlib import Path

from config import DATA_DIR
from parser.fuzzy_matcher import best_match, clean_text


class LocationParser:

    def __init__(self):
        self.file = Path(DATA_DIR) / "ddr_emplacements_radio.json"

        with self.file.open("r", encoding="utf-8") as f:
            self.locations = json.load(f)

        self.manual_locations = {
            "mission row": "Mission Row",
            "mission raw": "Mission Row",
            "mission rho": "Mission Row",
            "mission ro": "Mission Row",
            "mission roux": "Mission Row",
            "mission rowe": "Mission Row",

            "sandy shores": "Sandy Shores",
            "sandy shore": "Sandy Shores",
            "sandy shoress": "Sandy Shores",
            "sandy short": "Sandy Shores",
            "sandishore": "Sandy Shores",
            "sandichore": "Sandy Shores",
            "sand dicher": "Sandy Shores",
            "sambi chap": "Sandy Shores",
            "sambi shap": "Sandy Shores",
            "sambi shore": "Sandy Shores",
            "sandy chap": "Sandy Shores",
            "110 heures": "Sandy Shores",
            "cent dix heures": "Sandy Shores",

            "paleto bay": "Paleto Bay",
            "paleto": "Paleto Bay",
            "palais taubeille": "Paleto Bay",
            "palais-taubeille": "Paleto Bay",

            "legion square": "Legion Square",
            "legion": "Legion Square",
            "les jeans square": "Legion Square",
            "jeans square": "Legion Square",

            "del perro": "Del Perro",
            "delpero": "Del Perro",
            "del pero": "Del Perro",
            "delpéro": "Del Perro",

            "casino": "Casino",
            "bijouterie": "Bijouterie",
            "mirror park": "Mirror Park",
        }

        self.aliases = []
        self.name_lookup = {}

        for location in self.locations:
            name = location.get("name", "")

            if name:
                self.name_lookup[self.clean(name)] = location

            aliases = location.get("aliases", [])
            all_aliases = list(aliases) + [name]

            for alias in all_aliases:
                alias_clean = self.clean(alias)

                if not alias_clean:
                    continue

                self.aliases.append({
                    "alias": alias,
                    "alias_clean": alias_clean,
                    "name": name,
                    "id": location.get("id"),
                    "category": location.get("category"),
                    "type": location.get("type"),
                })

        for alias, name in self.manual_locations.items():
            self.aliases.append({
                "alias": alias,
                "alias_clean": self.clean(alias),
                "name": name,
                "id": None,
                "category": "Correction audio",
                "type": "zone",
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

    def make_location(self, name, id_value=None, category="Manuel", type_value="zone", score=100, raw=None):
        return {
            "name": name,
            "id": id_value,
            "category": category,
            "type": type_value,
            "score": score,
            "raw": raw or name,
        }

    def find_by_name(self, name, score=100, raw=None):
        name_clean = self.clean(name)

        if name_clean in self.name_lookup:
            item = self.name_lookup[name_clean]
            return {
                "name": item.get("name", name),
                "id": item.get("id"),
                "category": item.get("category", "Liste"),
                "type": item.get("type", "zone"),
                "score": score,
                "raw": raw or name,
            }

        return self.make_location(
            name=name,
            category="Correction audio",
            score=score,
            raw=raw,
        )

    def find_exact(self, text_clean):
        for alias, name in self.manual_locations.items():
            alias_clean = self.clean(alias)

            if re.search(r"\b" + re.escape(alias_clean) + r"\b", text_clean):
                return self.find_by_name(name, score=100, raw=alias)

        for item in self.aliases:
            alias = item["alias_clean"]

            if len(alias) <= 2:
                continue

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text_clean):
                result = dict(item)
                result["score"] = 100
                result["raw"] = item.get("alias")
                return result

        return None

    def find_fuzzy_fragment(self, fragment, threshold=82):
        fragment_clean = self.clean(fragment)

        if len(fragment_clean) < 4:
            return None

        result = best_match(fragment_clean, self.aliases, threshold=threshold)

        if not result:
            return None

        item = result["item"]

        return {
            "name": item.get("name"),
            "id": item.get("id"),
            "category": item.get("category", "Fuzzy"),
            "type": item.get("type", "zone"),
            "score": result["score"],
            "raw": fragment,
            "matched_alias": item.get("alias"),
        }

    def find(self, text: str):
        text_clean = self.clean(text)

        exact = self.find_exact(text_clean)

        if exact:
            return exact

        # Fuzzy prudent : uniquement sur morceaux après un indice de lieu.
        patterns = [
            r"\bdirection\s+([a-z0-9 ]{3,35})",
            r"\bvers\s+([a-z0-9 ]{3,35})",
            r"\bsur\s+([a-z0-9 ]{3,35})",
            r"\ba\s+([a-z0-9 ]{3,35})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if not match:
                continue

            fragment = match.group(1)
            fragment = re.split(
                r"\b(vehicule|voiture|auto|bmw|audi|mercedes|moto|suspect|individu|individus|conducteur|arme|code|10|unite|central|besoin|coups|dernier)\b",
                fragment,
            )[0].strip()

            fuzzy = self.find_fuzzy_fragment(fragment, threshold=78)

            if fuzzy:
                return fuzzy

        return None
