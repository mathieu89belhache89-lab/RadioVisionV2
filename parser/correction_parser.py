import json
import re
from pathlib import Path

from config import DATA_DIR
from parser.fuzzy_matcher import clean_text


class CorrectionParser:

    VALID_SECTIONS = [
        "locations",
        "vehicles",
        "codes",
        "incidents",
    ]

    def __init__(self):
        self.file = Path(DATA_DIR) / "corrections_audio.json"
        self.data = self.default_data()
        self.load()

    def default_data(self):
        return {
            "locations": {
                "mission euro": "Mission Row",
                "vermission euro": "Mission Row",
                "ver mission euro": "Mission Row",
                "permission ro": "Mission Row",
                "permission rô": "Mission Row",
                "permission raw": "Mission Row",
                "permission rho": "Mission Row",
                "sambi chap": "Sandy Shores",
                "sambi shap": "Sandy Shores",
                "sambi shore": "Sandy Shores",
                "sandy chap": "Sandy Shores",
                "sandichore": "Sandy Shores",
                "sandishore": "Sandy Shores",
                "sand dicher": "Sandy Shores",
                "sandy short": "Sandy Shores",
                "sandy shore": "Sandy Shores",
                "110 heures": "Sandy Shores",
                "cent dix heures": "Sandy Shores",
                "palais taubeille": "Paleto Bay",
                "palais-taubeille": "Paleto Bay",
                "paleto": "Paleto Bay",
                "mission raw": "Mission Row",
                "mission rho": "Mission Row",
                "mission ro": "Mission Row",
                "mission roux": "Mission Row",
                "mission rowe": "Mission Row",
                "les jeans square": "Legion Square",
                "jeans square": "Legion Square",
                "legion": "Legion Square",
                "delpero": "Del Perro",
                "del pero": "Del Perro",
                "delpéro": "Del Perro",
            },
            "vehicles": {
                "wm4": "BMW M4",
                "w m4": "BMW M4",
                "w m 4": "BMW M4",
                "ds amg": "Mercedes AMG",
                "amg gris": "Mercedes AMG",
                "od rs6": "Audi RS6",
                "audi air s6": "Audi RS6",
                "audi r s6": "Audi RS6",
                "bm double v m4": "BMW M4",
                "bmw aime quatre": "BMW M4",
                "mercedes amg gris": "Mercedes AMG",
            },
            "codes": {
                "dis 99": "10-99",
                "disquette": "10-4",
                "disquatre": "10-4",
                "dis sank": "10-5",
                "cis cis": "10-6",
                "disces": "10-7",
            },
            "incidents": {
                "agent at": "agent a terre",
                "agents at": "agent a terre",
                "agent atr": "agent a terre",
                "agents atr": "agent a terre",
                "agent a tr": "agent a terre",
                "agents inter": "agent a terre",
                "agent inter": "agent a terre",
                "agent pris en hotel": "agent pris en otage",
                "agent pris en hôtel": "agent pris en otage",
                "pris en hotel": "pris en otage",
                "pris en hôtel": "pris en otage",
                "vehicules immobilises": "vehicule immobilise",
                "vehicule immobilises": "vehicule immobilise",
                "vehicules accidentes": "vehicule accidente",
                "besoin de renforts": "besoin de renfort",
                "dernier visual": "dernier visuel",
                "dernier visu": "dernier visuel",
                "en fuite a pie": "en fuite a pied",
                "suspes en fuite a pied": "suspect en fuite a pied",
            },
        }

    def load(self):
        base = self.default_data()

        if not self.file.exists():
            self.data = base
            return

        try:
            with self.file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                self.data = base
                return

            for section in self.VALID_SECTIONS:
                value = data.get(section, {})

                if isinstance(value, dict):
                    base.setdefault(section, {})
                    base[section].update(value)

        except Exception:
            pass

        self.data = base

    def save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)

        with self.file.open("w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                ensure_ascii=False,
                indent=4,
            )

    def normalize_section(self, section):
        section = str(section or "").strip().lower()

        aliases = {
            "lieu": "locations",
            "location": "locations",
            "locations": "locations",
            "vehicule": "vehicles",
            "véhicule": "vehicles",
            "vehicle": "vehicles",
            "vehicles": "vehicles",
            "code": "codes",
            "codes": "codes",
            "radio": "codes",
            "incident": "incidents",
            "incidents": "incidents",
            "info": "incidents",
            "infos": "incidents",
        }

        return aliases.get(section)

    def get_section(self, section):
        section = self.normalize_section(section)

        if not section:
            return {}

        return self.data.get(section, {})

    def find_exact(self, section, text):
        text_clean = clean_text(text)

        for bad, good in self.get_section(section).items():
            if clean_text(bad) == text_clean:
                return good

        return None

    def add_correction(self, section, heard, correction):
        section = self.normalize_section(section)
        heard = str(heard or "").strip()
        correction = str(correction or "").strip()

        if not section:
            return False, "Type de correction invalide."

        if not heard:
            return False, "Le texte entendu est vide."

        if not correction:
            return False, "La correction officielle est vide."

        if section not in self.data:
            self.data[section] = {}

        self.data[section][heard] = correction
        self.save()

        return True, f"Correction ajoutée : {heard} → {correction}"

    def remove_correction(self, section, heard):
        section = self.normalize_section(section)
        heard = str(heard or "").strip()

        if not section or section not in self.data:
            return False, "Type de correction invalide."

        if heard not in self.data[section]:
            return False, "Correction introuvable."

        del self.data[section][heard]
        self.save()

        return True, "Correction supprimée."

    def replace_in_text(self, text):
        result_clean = clean_text(str(text or ""))

        # Remplacements prudents uniquement sur mots complets.
        # Exemple du bug V8.1 :
        # "mission raw" -> "mission row", puis "mission ro" repassait derrière
        # et transformait le texte en "mission roww".
        replacements = []

        for section in self.VALID_SECTIONS:
            for bad, good in self.get_section(section).items():
                bad_clean = clean_text(bad)
                good_clean = clean_text(good)

                if not bad_clean or not good_clean:
                    continue

                if bad_clean == good_clean:
                    continue

                replacements.append((bad_clean, good_clean))

        replacements.sort(key=lambda item: len(item[0]), reverse=True)

        for bad_clean, good_clean in replacements:
            # Si le bon texte est déjà présent, ne pas appliquer un alias plus court
            # contenu dans ce bon texte.
            # Exemple : ne pas faire "paleto" -> "paleto bay" dans "paleto bay".
            if bad_clean in good_clean:
                good_pattern = r"(?<![a-z0-9])" + re.escape(good_clean) + r"(?![a-z0-9])"

                if re.search(good_pattern, result_clean):
                    continue

            bad_pattern = r"(?<![a-z0-9])" + re.escape(bad_clean) + r"(?![a-z0-9])"
            result_clean = re.sub(bad_pattern, good_clean, result_clean)

        return result_clean
