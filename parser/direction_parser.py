import re
import unicodedata


class DirectionParser:

    STOP_WORDS = [
        "bmw", "audi", "mercedes", "amg", "rs6", "rs 6", "m4", "m 4",
        "vehicule", "vehicules", "voiture", "auto", "moto", "conducteur",
        "blanc", "blanche", "noir", "noire", "gris", "grise", "rouge", "bleu", "bleue",
        "individu", "individus", "suspect", "suspects", "personne", "personnes",
        "arme", "armes", "arme visible", "a bord", "sur place",
        "dernier", "visuel", "visual", "besoin", "renfort", "renforts",
        "coups", "coup", "feu", "poursuite", "central", "centrale", "unite", "code",
        "10", "459", "460", "461", "187", "207", "208",
    ]

    KNOWN_DIRECTIONS = {
        "sandy shores": "Sandy Shores",
        "sandy shore": "Sandy Shores",
        "sandy shoress": "Sandy Shores",
        "sandishore": "Sandy Shores",
        "sandi shore": "Sandy Shores",
        "sand dicher": "Sandy Shores",
        "sand diche": "Sandy Shores",
        "sandy": "Sandy Shores",
        "110 heures": "Sandy Shores",
        "110h": "Sandy Shores",
        "110 h": "Sandy Shores",

        "mission row": "Mission Row",
        "mission raw": "Mission Row",
        "mission rho": "Mission Row",
        "mission ro": "Mission Row",
        "mission rô": "Mission Row",
        "mission road": "Mission Row",

        "paleto bay": "Paleto Bay",
        "paleto": "Paleto Bay",
        "palais taubeille": "Paleto Bay",
        "palais-taubeille": "Paleto Bay",
        "palet au bay": "Paleto Bay",
        "paletto": "Paleto Bay",

        "legion square": "Legion Square",
        "les jeans square": "Legion Square",
        "le jeans square": "Legion Square",
        "legion": "Legion Square",

        "casino": "Casino",
        "bijouterie": "Bijouterie",
        "mirror park": "Mirror Park",
        "del perro": "Del Perro",
        "delpero": "Del Perro",
        "delpero suspect": "Del Perro",
        "canaux": "Canaux",
    }

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

    def normalize_known_direction(self, value):
        value_clean = self.clean(value)

        for alias, name in self.KNOWN_DIRECTIONS.items():
            alias_clean = self.clean(alias)

            if re.search(r"\b" + re.escape(alias_clean) + r"\b", value_clean):
                return name

        return None

    def cut_noise_after_direction(self, value):
        value_clean = self.clean(value)

        known = self.normalize_known_direction(value_clean)
        if known:
            return known

        for stop_word in self.STOP_WORDS:
            stop_clean = self.clean(stop_word)
            value_clean = re.split(
                r"\b" + re.escape(stop_clean) + r"\b",
                value_clean,
                maxsplit=1,
            )[0].strip()

        words = value_clean.split()

        if len(words) > 4:
            words = words[:4]

        value_clean = " ".join(words).strip()

        known = self.normalize_known_direction(value_clean)
        if known:
            return known

        if not value_clean:
            return None

        return value_clean

    def find(self, text: str):
        text_clean = self.clean(text)

        patterns = [
            r"\bdirection\s+([a-z0-9 ]+)",
            r"\ben direction de\s+([a-z0-9 ]+)",
            r"\bse dirige vers\s+([a-z0-9 ]+)",
            r"\bpart vers\s+([a-z0-9 ]+)",
            r"\bva vers\s+([a-z0-9 ]+)",
            r"\bvers\s+([a-z0-9 ]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if not match:
                continue

            direction = self.cut_noise_after_direction(match.group(1))

            if direction:
                return direction

        return None
