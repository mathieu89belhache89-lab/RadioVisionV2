import re
import unicodedata

from parser.fuzzy_matcher import best_match


class DirectionParser:

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

    def stop_direction(self, direction: str) -> str:
        direction = direction.strip()

        direction = re.split(
            r"\b(avec|en|sur|code|10|unite|central|vehicule|voiture|auto|bmw|audi|mercedes|moto|conducteur|individu|individus|suspect|suspects|arme|armes|besoin|renfort|coups|dernier|visuel|poursuite|a bord|bord)\b",
            direction,
        )[0].strip()

        return direction

    def correction_map(self):
        return {
            "sandy shoress": "Sandy Shores",
            "sandy shores": "Sandy Shores",
            "sandy shore": "Sandy Shores",
            "sandy short": "Sandy Shores",
            "sandishore": "Sandy Shores",
            "sandichore": "Sandy Shores",
            "sand dicher": "Sandy Shores",
            "sambi chap": "Sandy Shores",
            "sambi shap": "Sandy Shores",
            "sambi shore": "Sandy Shores",
            "mission row": "Mission Row",
            "mission raw": "Mission Row",
            "mission rho": "Mission Row",
            "mission ro": "Mission Row",
            "mission roux": "Mission Row",
            "paleto bay": "Paleto Bay",
            "paleto": "Paleto Bay",
            "palais taubeille": "Paleto Bay",
            "legion square": "Legion Square",
            "les jeans square": "Legion Square",
            "jeans square": "Legion Square",
            "casino": "Casino",
            "del perro": "Del Perro",
            "delpero": "Del Perro",
            "del pero": "Del Perro",
            "bijouterie": "Bijouterie",
            "mirror park": "Mirror Park",
        }

    def build_meta(self, name, raw, score=100, source="exact"):
        return {
            "name": name,
            "raw": raw,
            "score": score,
            "source": source,
            "probable": score < 92 or self.clean(name) != self.clean(raw),
        }

    def correct_direction(self, raw_direction, location_parser=None):
        raw_clean = self.clean(raw_direction)

        if not raw_clean:
            return None

        for bad, good in self.correction_map().items():
            bad_clean = self.clean(bad)

            if raw_clean == bad_clean or bad_clean in raw_clean or raw_clean in bad_clean:
                return self.build_meta(good, raw_direction, 100, "correction")

        if location_parser:
            fuzzy = location_parser.find_fuzzy_fragment(raw_clean, threshold=76)

            if fuzzy:
                return self.build_meta(
                    fuzzy.get("name"),
                    raw_direction,
                    fuzzy.get("score", 80),
                    "fuzzy_location",
                )

        candidates = []

        for bad, good in self.correction_map().items():
            candidates.append({"alias_clean": self.clean(bad), "name": good})

        result = best_match(raw_clean, candidates, threshold=78)

        if result:
            item = result["item"]
            return self.build_meta(
                item.get("name"),
                raw_direction,
                result.get("score", 80),
                "fuzzy_manual",
            )

        return None

    def find_detailed(self, text: str, location_parser=None):
        text_clean = self.clean(text)

        patterns = [
            r"\bdirection\s+([a-z0-9 ]+)",
            r"\ben direction de\s+([a-z0-9 ]+)",
            r"\bse dirige vers\s+([a-z0-9 ]+)",
            r"\bpart vers\s+([a-z0-9 ]+)",
            r"\bva vers\s+([a-z0-9 ]+)",
            r"\bdernier visuel vers\s+([a-z0-9 ]+)",
            r"\bvers\s+([a-z0-9 ]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if not match:
                continue

            raw_direction = self.stop_direction(match.group(1))

            if not raw_direction:
                continue

            corrected = self.correct_direction(raw_direction, location_parser)

            if corrected:
                return corrected

            # Mode strict : si ce n'est pas connu, on ne retourne pas de direction brute.
            return None

        return None

    def find(self, text: str):
        detailed = self.find_detailed(text)

        if detailed:
            return detailed.get("name")

        return None
