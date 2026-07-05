import re
import unicodedata


class UnitParser:

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
            r"\bunite\s+(\d{1,3})\b",
            r"\bunit\s+(\d{1,3})\b",
            r"\bu\s*[- ]?\s*(\d{1,3})\b",
            r"\bpatrouille\s+(\d{1,3})\b",
            r"\bcentral\s+de\s+l\s*unite\s+(\d{1,3})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                return match.group(1)

        return None