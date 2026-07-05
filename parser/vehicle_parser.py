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

    COLOR_NORMALIZE = {
        "noire": "noir",
        "blanche": "blanc",
        "bleue": "bleu",
        "verte": "vert",
        "grise": "gris",
        "violette": "violet",
        "doree": "dore",
        "dorée": "dore",
        "doré": "dore",
        "argente": "argent",
        "argentee": "argent",
        "argenté": "argent",
        "argentée": "argent",
    }

    MANUAL_VEHICLES = [
        {
            "key": "mercedes_amg",
            "label": "Mercedes AMG",
            "aliases": [
                "mercedes amg",
                "mercedes-amg",
                "merco amg",
                "mercedes benz amg",
                "mercedes benz",
            ],
            "category": "Import / générique",
        },
        {
            "key": "mercedes_amg_gt",
            "label": "Mercedes AMG GT",
            "aliases": [
                "mercedes amg gt",
                "amg gt",
                "merco amg gt",
            ],
            "category": "Import",
        },
        {
            "key": "mercedes_c63",
            "label": "Mercedes C63 AMG",
            "aliases": [
                "mercedes c63",
                "mercedes c 63",
                "c63",
                "c 63",
                "c63 amg",
                "mercedes c63 amg",
            ],
            "category": "Import",
        },
        {
            "key": "mercedes_g63",
            "label": "Mercedes G63 AMG",
            "aliases": [
                "mercedes g63",
                "mercedes g 63",
                "g63",
                "g 63",
                "g63 amg",
                "mercedes g63 amg",
            ],
            "category": "Import",
        },
        {
            "key": "mercedes_a45",
            "label": "Mercedes A45 AMG",
            "aliases": [
                "mercedes a45",
                "mercedes a 45",
                "a45",
                "a 45",
                "a45 amg",
            ],
            "category": "Import",
        },
        {
            "key": "mercedes_cls63",
            "label": "Mercedes CLS63 AMG",
            "aliases": [
                "mercedes cls63",
                "mercedes cls 63",
                "cls63",
                "cls 63",
                "cls63 amg",
            ],
            "category": "Import",
        },
        {
            "key": "audi_rs",
            "label": "Audi RS",
            "aliases": [
                "audi rs",
                "audi r s",
            ],
            "category": "Import / générique",
        },
        {
            "key": "audi_rs3",
            "label": "Audi RS3",
            "aliases": [
                "audi rs3",
                "rs3",
                "rs 3",
                "r s 3",
                "audi r s 3",
                "audi rs trois",
                "rs trois",
            ],
            "category": "Import",
        },
        {
            "key": "audi_rs4",
            "label": "Audi RS4",
            "aliases": [
                "audi rs4",
                "rs4",
                "rs 4",
                "r s 4",
                "audi r s 4",
                "audi rs quatre",
                "rs quatre",
            ],
            "category": "Import",
        },
        {
            "key": "audi_rs6",
            "label": "Audi RS6",
            "aliases": [
                "audi rs6",
                "rs6",
                "rs 6",
                "r s 6",
                "audi r s 6",
                "audi rs six",
                "rs six",
            ],
            "category": "Import",
        },
        {
            "key": "audi_r8",
            "label": "Audi R8",
            "aliases": [
                "audi r8",
                "audi r 8",
                "r8",
                "r 8",
                "audi r huit",
                "r huit",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_m",
            "label": "BMW M",
            "aliases": [
                "bmw m",
                "bm double v m",
                "b m w m",
            ],
            "category": "Import / générique",
        },
        {
            "key": "bmw_m3",
            "label": "BMW M3",
            "aliases": [
                "bmw m3",
                "m3",
                "m 3",
                "bmw m 3",
                "bmw m trois",
                "m trois",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_m4",
            "label": "BMW M4",
            "aliases": [
                "bmw m4",
                "m4",
                "m 4",
                "bmw m 4",
                "bmw m quatre",
                "m quatre",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_m5",
            "label": "BMW M5",
            "aliases": [
                "bmw m5",
                "m5",
                "m 5",
                "bmw m 5",
                "bmw m cinq",
                "m cinq",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_m8",
            "label": "BMW M8",
            "aliases": [
                "bmw m8",
                "m8",
                "m 8",
                "bmw m 8",
                "bmw m huit",
                "m huit",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_x5",
            "label": "BMW X5",
            "aliases": [
                "bmw x5",
                "x5",
                "x 5",
                "bmw x 5",
                "bmw x cinq",
                "x cinq",
            ],
            "category": "Import",
        },
        {
            "key": "bmw_x6",
            "label": "BMW X6",
            "aliases": [
                "bmw x6",
                "x6",
                "x 6",
                "bmw x 6",
                "bmw x six",
                "x six",
            ],
            "category": "Import",
        },
        {
            "key": "nissan_gtr",
            "label": "Nissan GTR",
            "aliases": [
                "nissan gtr",
                "nissan gt r",
                "gtr",
                "gt r",
                "skyline gtr",
                "skyline gt r",
            ],
            "category": "Import",
        },
        {
            "key": "toyota_supra",
            "label": "Toyota Supra",
            "aliases": [
                "toyota supra",
                "supra",
            ],
            "category": "Import",
        },
        {
            "key": "dodge_charger",
            "label": "Dodge Charger",
            "aliases": [
                "dodge charger",
                "charger",
            ],
            "category": "Import",
        },
        {
            "key": "dodge_challenger",
            "label": "Dodge Challenger",
            "aliases": [
                "dodge challenger",
                "challenger",
            ],
            "category": "Import",
        },
        {
            "key": "ford_mustang",
            "label": "Ford Mustang",
            "aliases": [
                "ford mustang",
                "mustang",
            ],
            "category": "Import",
        },
        {
            "key": "chevrolet_camaro",
            "label": "Chevrolet Camaro",
            "aliases": [
                "chevrolet camaro",
                "chevy camaro",
                "camaro",
            ],
            "category": "Import",
        },
        {
            "key": "chevrolet_corvette",
            "label": "Chevrolet Corvette",
            "aliases": [
                "chevrolet corvette",
                "chevy corvette",
                "corvette",
            ],
            "category": "Import",
        },
        {
            "key": "porsche_911",
            "label": "Porsche 911",
            "aliases": [
                "porsche 911",
                "porsche neuf cent onze",
                "neuf cent onze",
                "911",
            ],
            "category": "Import",
        },
        {
            "key": "porsche_cayenne",
            "label": "Porsche Cayenne",
            "aliases": [
                "porsche cayenne",
                "cayenne",
            ],
            "category": "Import",
        },
        {
            "key": "porsche_panamera",
            "label": "Porsche Panamera",
            "aliases": [
                "porsche panamera",
                "panamera",
            ],
            "category": "Import",
        },
        {
            "key": "lamborghini",
            "label": "Lamborghini",
            "aliases": [
                "lamborghini",
                "lambo",
            ],
            "category": "Import / générique",
        },
        {
            "key": "lamborghini_urus",
            "label": "Lamborghini Urus",
            "aliases": [
                "lamborghini urus",
                "urus",
                "lambo urus",
            ],
            "category": "Import",
        },
        {
            "key": "lamborghini_huracan",
            "label": "Lamborghini Huracan",
            "aliases": [
                "lamborghini huracan",
                "huracan",
                "lambo huracan",
            ],
            "category": "Import",
        },
        {
            "key": "ferrari",
            "label": "Ferrari",
            "aliases": [
                "ferrari",
            ],
            "category": "Import / générique",
        },
        {
            "key": "mclaren",
            "label": "McLaren",
            "aliases": [
                "mclaren",
                "maclaren",
                "mc laren",
            ],
            "category": "Import / générique",
        },
        {
            "key": "tesla",
            "label": "Tesla",
            "aliases": [
                "tesla",
            ],
            "category": "Import / générique",
        },
        {
            "key": "range_rover",
            "label": "Range Rover",
            "aliases": [
                "range rover",
                "rang rover",
                "land rover range",
            ],
            "category": "Import",
        },
        {
            "key": "jeep_trackhawk",
            "label": "Jeep Trackhawk",
            "aliases": [
                "jeep trackhawk",
                "trackhawk",
                "track hawk",
            ],
            "category": "Import",
        },
    ]

    GENERIC_BRAND_PATTERNS = [
        {
            "key": "mercedes_amg_generic",
            "label": "Mercedes AMG",
            "patterns": [
                r"\bmercedes\s+amg\b",
                r"\bmerco\s+amg\b",
                r"\bmercedes\s+benz\s+amg\b",
            ],
        },
        {
            "key": "audi_rs_generic",
            "label": "Audi RS",
            "patterns": [
                r"\baudi\s+rs\b",
                r"\baudi\s+r\s+s\b",
            ],
        },
        {
            "key": "bmw_m_generic",
            "label": "BMW M",
            "patterns": [
                r"\bbmw\s+m\b",
                r"\bb\s*m\s*w\s+m\b",
            ],
        },
        {
            "key": "porsche_generic",
            "label": "Porsche",
            "patterns": [
                r"\bporsche\b",
            ],
        },
        {
            "key": "ferrari_generic",
            "label": "Ferrari",
            "patterns": [
                r"\bferrari\b",
            ],
        },
        {
            "key": "lamborghini_generic",
            "label": "Lamborghini",
            "patterns": [
                r"\blamborghini\b",
                r"\blambo\b",
            ],
        },
        {
            "key": "mclaren_generic",
            "label": "McLaren",
            "patterns": [
                r"\bmclaren\b",
                r"\bmc\s+laren\b",
                r"\bmaclaren\b",
            ],
        },
        {
            "key": "tesla_generic",
            "label": "Tesla",
            "patterns": [
                r"\btesla\b",
            ],
        },
    ]

    def __init__(self):
        self.vehicles = []

        self.load_manual()
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

        replacements = {
            "mercedesse": "mercedes",
            "mercedez": "mercedes",
            "mercedes benz": "mercedes",
            "merco": "mercedes",

            "bm double v": "bmw",
            "b m w": "bmw",
            "bmw m sport": "bmw m",

            "maclaren": "mclaren",
            "mc laren": "mclaren",

            "rang rover": "range rover",

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

            "r s 6": "rs6",
            "r s 4": "rs4",
            "r s 3": "rs3",

            "audi r s six": "audi rs6",
            "audi r s quatre": "audi rs4",
            "audi r s trois": "audi rs3",

            "audi r s 6": "audi rs6",
            "audi r s 4": "audi rs4",
            "audi r s 3": "audi rs3",

            "bmw m quatre": "bmw m 4",
            "bmw m trois": "bmw m 3",
            "bmw m cinq": "bmw m 5",
            "bmw m huit": "bmw m 8",

            "neuf cent onze": "911",

            "gt r": "gtr",
            "g t r": "gtr",

            "track hawk": "trackhawk",

            "grise": "gris",
            "noire": "noir",
            "blanche": "blanc",
            "bleue": "bleu",
            "verte": "vert",
            "violette": "violet",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

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
            "amg",
            "rs",
            "m",
            "classe",
            "serie",
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

    def load_manual(self):
        for vehicle in self.MANUAL_VEHICLES:
            key = vehicle["key"]
            label = vehicle["label"]
            category = vehicle.get("category", "Manuel")

            for alias in vehicle.get("aliases", []):
                self.add_vehicle(
                    key=key,
                    label=label,
                    alias=alias,
                    category=category,
                    source="manual",
                )

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
                    source="import",
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
                    source="import",
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
                    source="gta",
                )

    def normalize_color(self, color):
        color_clean = self.clean(color)
        return self.COLOR_NORMALIZE.get(color_clean, color_clean)

    def find_color(self, text_clean: str, alias_clean: str):
        for color in self.COLORS:
            color_clean = self.clean(color)
            color_clean = self.normalize_color(color_clean)

            patterns = [
                rf"\b{re.escape(alias_clean)}\s+{re.escape(color_clean)}\b",
                rf"\b{re.escape(color_clean)}\s+{re.escape(alias_clean)}\b",
            ]

            for pattern in patterns:
                if re.search(pattern, text_clean):
                    return color_clean

        return None

    def find_exact_vehicle(self, text_clean):
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

    def find_generic_vehicle(self, text_clean):
        vehicle_words = [
            "vehicule",
            "voiture",
            "auto",
            "berline",
            "suv",
            "coupe",
            "sportive",
            "fuite",
            "poursuite",
            "direction",
            "visuel",
            "conducteur",
        ]

        has_vehicle_context = any(
            word in text_clean
            for word in vehicle_words
        )

        has_color = any(
            self.normalize_color(color) in text_clean
            for color in self.COLORS
        )

        for item in self.GENERIC_BRAND_PATTERNS:
            for pattern in item["patterns"]:
                match = re.search(pattern, text_clean)

                if not match:
                    continue

                if not has_vehicle_context and not has_color:
                    continue

                alias_clean = match.group(0).strip()
                color = self.find_color(text_clean, alias_clean)

                return {
                    "vehicle": item["label"],
                    "key": item["key"],
                    "alias": alias_clean,
                    "category": "Import / générique",
                    "source": "generic_fallback",
                    "color": color,
                }

        return None

    def find(self, text: str):
        text_clean = self.clean(text)

        exact = self.find_exact_vehicle(text_clean)

        if exact:
            return exact

        generic = self.find_generic_vehicle(text_clean)

        if generic:
            return generic

        return None