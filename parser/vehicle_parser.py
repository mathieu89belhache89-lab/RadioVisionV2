import json
import re
import unicodedata
from pathlib import Path

from config import DATA_DIR


class VehicleParser:

    COLORS = [
        "noir", "noire",
        "blanc", "blanche",
        "rouge",
        "bleu", "bleue",
        "vert", "verte",
        "jaune",
        "orange",
        "gris", "grise",
        "violet", "violette",
        "rose",
        "marron",
        "beige",
        "chrome",
        "dore", "doree", "doré", "dorée",
        "argent", "argente", "argentee", "argenté", "argentée",
    ]

    def __init__(self):
        self.vehicles = []

        self.load_imports()
        self.load_gta()

        self.vehicles.sort(
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
        text = text.replace("_", " ")
        text = text.replace("'", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        replacements = {
            "m quatre": "m 4",
            "m trois": "m 3",
            "m cinq": "m 5",
            "m huit": "m 8",
            "x cinq": "x 5",
            "x six": "x 6",
            "rs six": "rs6",
            "rs quatre": "rs4",
            "rs trois": "rs3",
            "r s six": "rs6",
            "r s quatre": "rs4",
            "r s trois": "rs3",
            "audi r s six": "audi rs6",
            "audi r s quatre": "audi rs4",
            "audi r s trois": "audi rs3",
            "bmw m quatre": "bmw m 4",
            "bmw m trois": "bmw m 3",
            "bmw m cinq": "bmw m 5",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        return text.strip()

    def should_skip_alias(self, alias: str) -> bool:
        alias_clean = self.clean(alias)

        if not alias_clean:
            return True

        if len(alias_clean) <= 2 and not any(c.isdigit() for c in alias_clean):
            return True

        blacklist = {
            "s",
            "r",
            "t",
            "f",
            "gt",
            "gp",
            "sc",
            "lm",
            "jb",
            "bf",
            "xa",
        }

        return alias_clean in blacklist

    def add_vehicle(self, key, label, alias, category=None, source=None):
        if self.should_skip_alias(alias):
            return

        alias_clean = self.clean(alias)

        self.vehicles.append({
            "key": key,
            "label": label,
            "alias": alias,
            "alias_clean": alias_clean,
            "category": category,
            "source": source,
        })

    def load_imports(self):
        file = Path(DATA_DIR) / "fivem_import_vehicle_aliases_fr.json"

        if not file.exists():
            return

        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        details = data.get("vehicles_details", {})

        for key, info in details.items():
            brand = info.get("brand", "")
            model = info.get("model", key)
            category = info.get("category", "Import")

            label = f"{brand} {model}".strip()

            for alias in info.get("aliases", []):
                self.add_vehicle(
                    key=key,
                    label=label,
                    alias=alias,
                    category=category,
                    source="import"
                )

        aliases = data.get("vehicles_aliases", {})

        for key, alias_list in aliases.items():
            if key in details:
                continue

            label = key.replace("_", " ").title()

            for alias in alias_list:
                self.add_vehicle(
                    key=key,
                    label=label,
                    alias=alias,
                    category="Import",
                    source="import"
                )

    def load_gta(self):
        file = Path(DATA_DIR) / "gta5_vehicle_names_fivem.json"

        if not file.exists():
            return

        with file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        vehicles = data.get("vehicles", [])

        for vehicle in vehicles:
            model_name = vehicle.get("model_name")
            category = vehicle.get("category", "GTA")

            if not model_name:
                continue

            aliases = vehicle.get("aliases", [])
            normalized_aliases = vehicle.get("normalized_aliases", [])

            all_aliases = set(aliases + normalized_aliases + [model_name])

            label = model_name

            for alias in all_aliases:
                self.add_vehicle(
                    key=model_name,
                    label=label,
                    alias=alias,
                    category=category,
                    source="gta"
                )

    def find_color(self, text_clean: str, alias_clean: str):
        for color in self.COLORS:
            color_clean = self.clean(color)

            patterns = [
                rf"\b{re.escape(alias_clean)}\s+{re.escape(color_clean)}\b",
                rf"\b{re.escape(color_clean)}\s+{re.escape(alias_clean)}\b",
            ]

            for pattern in patterns:
                if re.search(pattern, text_clean):
                    return color_clean

        return None

    def find(self, text: str):
        text_clean = self.clean(text)

        for vehicle in self.vehicles:
            alias = vehicle["alias_clean"]

            pattern = r"\b" + re.escape(alias) + r"\b"

            if re.search(pattern, text_clean):
                color = self.find_color(text_clean, alias)

                return {
                    "vehicle": vehicle["label"],
                    "key": vehicle["key"],
                    "alias": vehicle["alias"],
                    "category": vehicle["category"],
                    "source": vehicle["source"],
                    "color": color,
                }

        return None