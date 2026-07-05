import re
import unicodedata


class DirectionParser:

    def clean(self, text: str) -> str:
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def find(self, text: str):
        text = self.clean(text)

        patterns = [
            r"\bdirection\s+([a-z0-9 '\-]+)",
            r"\ben direction de\s+([a-z0-9 '\-]+)",
            r"\bse dirige vers\s+([a-z0-9 '\-]+)",
            r"\bpart vers\s+([a-z0-9 '\-]+)",
            r"\bva vers\s+([a-z0-9 '\-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                direction = match.group(1).strip()

                direction = re.split(
                    r"\b(avec|en|sur|code|10-|unite|central)\b",
                    direction
                )[0].strip()

                corrections = {
                    "sandy shoress": "Sandy Shores",
                    "sandy shores": "Sandy Shores",
                    "sandy shore": "Sandy Shores",
                    "mission row": "Mission Row",
                    "paleto bay": "Paleto Bay",
                    "legion square": "Legion Square",
                }

                for bad, good in corrections.items():
                    if bad in direction:
                        direction = good
                        break

                return direction

        return None