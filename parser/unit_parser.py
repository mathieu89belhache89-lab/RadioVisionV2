import re
import unicodedata


class UnitParser:

    NUMBER_WORDS = {
        "zero": 0,
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
        "sept": 7,
        "huit": 8,
        "neuf": 9,
        "dix": 10,
        "onze": 11,
        "douze": 12,
        "treize": 13,
        "quatorze": 14,
        "quinze": 15,
        "seize": 16,
        "vingt": 20,
        "trente": 30,
        "quarante": 40,
        "cinquante": 50,
        "soixante": 60,
    }

    def clean(self, text: str) -> str:
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def words_to_number(self, words: str):
        words = words.strip()

        if words.isdigit():
            return int(words)

        parts = words.split()

        parts = [
            p for p in parts
            if p not in ["et", "l", "de", "la", "le"]
        ]

        if not parts:
            return None

        total = 0

        for part in parts:
            if part not in self.NUMBER_WORDS:
                continue

            total += self.NUMBER_WORDS[part]

        if total > 0:
            return total

        return None

    def find(self, text: str):
        text = self.clean(text)

        patterns = [
            r"\bunite\s+([a-z0-9 ]{1,30})",
            r"\bunit\s+([a-z0-9 ]{1,30})",
            r"\bu\s+([a-z0-9 ]{1,10})",
            r"\bpatrouille\s+([a-z0-9 ]{1,30})",
            r"\bcentral\s+unite\s+([a-z0-9 ]{1,30})",
            r"\bcentral\s+de\s+l\s+unite\s+([a-z0-9 ]{1,30})",
        ]

        stop_words = [
            "code",
            "10",
            "direction",
            "vehicule",
            "voiture",
            "audi",
            "bmw",
            "mercedes",
            "sultan",
            "mission",
            "sandy",
            "paleto",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)

            if match:
                raw = match.group(1).strip()

                for stop in stop_words:
                    raw = raw.split(stop)[0].strip()

                number = self.words_to_number(raw)

                if number is not None:
                    return str(number)

        return None