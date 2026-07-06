import re
import unicodedata


class UnitParser:

    AFFILIATIONS = {
        "mary": "Mary",
        "marie": "Mary",
        "mari": "Mary",
        "mairie": "Mary",
        "henry": "Henry",
        "henri": "Henry",
        "enry": "Henry",
        "ap": "AP",
        "a p": "AP",
        "cp": "CP",
        "c p": "CP",
        "lincoln": "Lincoln",
        "lincon": "Lincoln",
        "adams": "Adams",
        "adam": "Adams",
        "tango plus": "Tango+",
        "tango +": "Tango+",
        "tango": "Tango",
    }

    SIMPLE_NUMBERS = {
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

    STOP_WORDS = [
        "code",
        "10",
        "direction",
        "vers",
        "dernier",
        "visuel",
        "vue",
        "vehicule",
        "voiture",
        "conducteur",
        "individu",
        "individus",
        "suspect",
        "suspects",
        "poursuite",
        "fuite",
        "immobilise",
        "accident",
        "renfort",
        "arme",
        "audi",
        "bmw",
        "mercedes",
        "porsche",
        "ferrari",
        "mclaren",
        "lamborghini",
        "mission",
        "sandy",
        "paleto",
        "legion",
        "casino",
        "bijouterie",
    ]

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
        text = re.sub(r"\s+", " ", text).strip()

        replacements = {
            r"\bunitee\b": "unite",
            r"\buniter\b": "unite",
            r"\bunites\b": "unite",
            r"\bunit\b": "unite",
            r"\bcentral de l unite\b": "central unite",
            r"\bcentral de la unite\b": "central unite",
            r"\bcentral l unite\b": "central unite",
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        text = re.sub(r"\s+", " ", text).strip()

        return text

    def cut_after_stop_word(self, raw: str) -> str:
        raw = raw.strip()

        for stop in self.STOP_WORDS:
            raw = re.split(
                r"\b" + re.escape(stop) + r"\b",
                raw
            )[0].strip()

        return raw

    def words_to_number(self, words: str):
        words = words.strip()

        direct_digit = re.search(r"\b(\d{1,3})\b", words)

        if direct_digit:
            return int(direct_digit.group(1))

        parts = words.split()

        parts = [
            part for part in parts
            if part not in [
                "et",
                "de",
                "du",
                "la",
                "le",
                "l",
                "d",
            ]
        ]

        if not parts:
            return None

        total = 0
        found_number = False

        index = 0

        while index < len(parts):
            part = parts[index]

            if part.isdigit():
                total += int(part)
                found_number = True
                index += 1
                continue

            if part == "quatre" and index + 1 < len(parts):
                next_part = parts[index + 1]

                if next_part == "vingt":
                    total += 80
                    found_number = True
                    index += 2
                    continue

            if part in self.SIMPLE_NUMBERS:
                total += self.SIMPLE_NUMBERS[part]
                found_number = True

            index += 1

        if found_number and total > 0:
            return total

        return None

    def find_affiliation(self, text_clean: str):
        # Détection prioritaire uniquement quand l'affiliation est utilisée comme unité.
        patterns = [
            r"\bunite\s+([a-z ]{2,20})",
            r"\bcentral\s+unite\s+([a-z ]{2,20})",
            r"\bpatrouille\s+([a-z ]{2,20})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if not match:
                continue

            raw = match.group(1).strip()
            raw = self.cut_after_stop_word(raw)
            raw = re.sub(r"\s+", " ", raw).strip()

            # Tango+ doit passer avant Tango.
            for alias in sorted(self.AFFILIATIONS, key=len, reverse=True):
                pattern_alias = r"^" + re.escape(alias) + r"(\b|$)"

                if re.search(pattern_alias, raw):
                    return self.AFFILIATIONS[alias]

        return None

    def find(self, text: str):
        text = self.clean(text)

        affiliation = self.find_affiliation(text)

        if affiliation:
            return affiliation

        direct_patterns = [
            r"\bunite\s+(\d{1,3})\b",
            r"\bcentral\s+unite\s+(\d{1,3})\b",
            r"\bpatrouille\s+(\d{1,3})\b",
            r"\bu\s+(\d{1,3})\b",
        ]

        for pattern in direct_patterns:
            match = re.search(pattern, text)

            if match:
                return str(int(match.group(1)))

        word_patterns = [
            r"\bcentral\s+unite\s+([a-z0-9 ]{1,50})",
            r"\bunite\s+([a-z0-9 ]{1,50})",
            r"\bpatrouille\s+([a-z0-9 ]{1,50})",
            r"\bu\s+([a-z0-9 ]{1,20})",
        ]

        for pattern in word_patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            raw = match.group(1).strip()
            raw = self.cut_after_stop_word(raw)

            number = self.words_to_number(raw)

            if number is not None:
                return str(number)

        return None