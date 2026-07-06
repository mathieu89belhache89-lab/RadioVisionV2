import json
import re
import unicodedata
from pathlib import Path

from config import DATA_DIR


class RadioParser:

    def __init__(self):
        self.file = Path(DATA_DIR) / "radio_codes.json"

        with self.file.open("r", encoding="utf-8") as f:
            self.codes = json.load(f)

        self.aliases = []
        self.build_aliases()

    def clean(self, text: str) -> str:
        text = str(text).lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = text.replace("+", " plus")
        text = text.replace(".", " ")
        text = text.replace(",", " ")
        text = text.replace("'", " ")

        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        replacements = {
            "codes content": "10 10",
            "code content": "10 10",

            "codes 30": "10 30",
            "code 30": "10 30",
            "codes 31": "10 31",
            "code 31": "10 31",
            "codes 17": "10 17",
            "code 17": "10 17",

            "codes sont en cascant neuf": "10 99",
            "codes quatre vingt dix neuf": "10 99",
            "code quatre vingt dix neuf": "10 99",

            "10 89": "10 99",
            "10 98": "10 99",

            "450 9": "459",
            "code 5 59": "459",
            "code 559": "459",

            "codes de 108": "208",
            "code de 108": "208",
            "code 108": "208",
            "108": "208",

            "277": "207",

            "dix quatre vingt dix neuf": "10 99",
            "dix trente et un": "10 31",
            "dix trente deux": "10 32",
            "dix trente trois": "10 33",
            "dix trente": "10 30",
            "dix vingt neuf": "10 29",
            "dix vingt": "10 20",
            "dix dix sept": "10 17",
            "dix dix neuf": "10 19",
            "dix seize": "10 16",
            "dix quinze": "10 15",
            "dix quatorze": "10 14",
            "dix treize": "10 13",
            "dix douze": "10 12",
            "dix onze": "10 11",
            "dix dix": "10 10",
            "dix zero": "10 0",
            "dix un": "10 1",
            "dix deux": "10 2",
            "dix trois": "10 3",
            "dix quatre": "10 4",
            "dix cinq": "10 5",
            "dix six": "10 6",
            "dix sept": "10 7",
            "dix huit": "10 8",
            "dix neuf": "10 9",

            "quatre cent soixante et un": "461",
            "quatre cent soixante": "460",
            "quatre cent cinquante neuf": "459",
            "cent quatre vingt sept": "187",
            "deux cent huit": "208",
            "deux cent sept": "207",

            "code trois": "code 3",
            "code deux": "code 2",
            "code un": "code 1",
            "code zero": "code 0",

            "code oscar david": "code od",
            "code delta sierra": "code ds",
            "code delta oscar alpha": "code doa",
            "code delta charlie delta": "code dcd",
            "code romeo delta papa": "code rdp",

            "oscar david": "od",
            "delta sierra": "ds",
            "delta oscar alpha": "doa",
            "delta charlie delta": "dcd",
            "romeo delta papa": "rdp",

            "poste de police": "pdp",
            "prise d otage": "po",
            "tango plus": "tango plus",
        }

        for bad, good in sorted(
            replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            text = re.sub(
                r"\b" + re.escape(bad) + r"\b",
                good,
                text,
            )

        text = re.sub(r"\bcodes?\s+s\b", "code s", text)
        text = re.sub(r"\bcodes?\s+od\b", "code od", text)
        text = re.sub(r"\bcodes?\s+ds\b", "code ds", text)
        text = re.sub(r"\bcodes?\s+doa\b", "code doa", text)
        text = re.sub(r"\bcodes?\s+dcd\b", "code dcd", text)
        text = re.sub(r"\bcodes?\s+rdp\b", "code rdp", text)

        text = re.sub(r"\s+", " ", text).strip()

        return text

    def add_alias(self, code, alias):
        alias_clean = self.clean(alias)

        if not alias_clean:
            return

        self.aliases.append({
            "code": code,
            "alias": alias,
            "alias_clean": alias_clean,
        })

    def build_aliases(self):
        for code in self.codes.keys():
            self.add_alias(code, code)

        manual_aliases = {
            "10-10": [
                "10 10",
                "10-10",
                "dix dix",
                "codes content",
                "code content",
                "refus d obtemperer a pied",
            ],
            "10-11": [
                "10 11",
                "10-11",
                "dix onze",
                "refus d obtemperer en voiture",
            ],
            "10-30": [
                "10 30",
                "10-30",
                "dix trente",
                "code 30",
                "codes 30",
                "risque de braquage",
            ],
            "10-31": [
                "10 31",
                "10-31",
                "dix trente et un",
                "code 31",
                "codes 31",
                "braquage confirme",
            ],
            "10-99": [
                "10 99",
                "10-99",
                "10 89",
                "10-89",
                "dix quatre vingt dix neuf",
                "renfort immediat",
                "demande de renfort immediat",
            ],
            "459": [
                "459",
                "450 9",
                "450-9",
                "code 5 59",
                "quatre cent cinquante neuf",
                "cambriolage",
            ],
            "460": [
                "460",
                "quatre cent soixante",
                "braquage",
            ],
            "461": [
                "461",
                "quatre cent soixante et un",
                "superette",
            ],
            "207": [
                "207",
                "277",
                "deux cent sept",
                "enlevement",
            ],
            "208": [
                "208",
                "108",
                "code 108",
                "code de 108",
                "codes de 108",
                "deux cent huit",
                "prise d otage sur agent",
            ],
            "CODE 3": [
                "code 3",
                "code trois",
                "urgence",
            ],
            "CODE OD": [
                "code od",
                "code o d",
                "agent a terre",
            ],
            "CODE DS": [
                "code ds",
                "code d s",
                "suspect neutralise",
                "suspect abattu",
            ],
            "CODE DOA": [
                "code doa",
                "code d o a",
                "civil a terre",
            ],
            "CODE DCD": [
                "code dcd",
                "code d c d",
                "civil decede",
            ],
            "CODE RDP": [
                "code rdp",
                "code r d p",
                "recapitulatif des patrouilles",
            ],
            "CODE S": [
                "code s",
                "codes s",
                "silence radio",
            ],
            "MARY": [
                "mary",
                "marie",
                "mari",
                "mairie",
            ],
            "HENRY": [
                "henry",
                "henri",
                "enry",
            ],
            "AP": [
                "ap",
                "a p",
            ],
            "CP": [
                "cp",
                "c p",
            ],
            "LINCOLN": [
                "lincoln",
                "lincon",
            ],
            "ADAMS": [
                "adams",
                "adam",
            ],
            "TANGO": [
                "tango",
            ],
            "TANGO+": [
                "tango plus",
                "tango +",
            ],
        }

        for code, aliases in manual_aliases.items():
            for alias in aliases:
                self.add_alias(code, alias)

        self.aliases.sort(
            key=lambda item: len(item["alias_clean"]),
            reverse=True,
        )

    def alias_pattern(self, alias_clean):
        return (
            r"(?<![a-z0-9])"
            + re.escape(alias_clean)
            + r"(?![a-z0-9])"
        )


    def parse_explicit_report_code(self, text_clean):
        explicit_reports = [
            ("CODE DOA", ["code doa", "code d o a"]),
            ("CODE DCD", ["code dcd", "code d c d"]),
            ("CODE RDP", ["code rdp", "code r d p"]),
            ("CODE OD", ["code od", "code o d"]),
            ("CODE DS", ["code ds", "code d s", "code dsd", "code des"]),
            ("CODE S", ["code s", "codes s", "code esse", "code est"]),
        ]

        for code, aliases in explicit_reports:
            for alias in aliases:
                alias_clean = self.clean(alias)
                pattern = self.alias_pattern(alias_clean)

                if re.search(pattern, text_clean):
                    signification = self.codes.get(code)

                    if signification:
                        return code, signification

        return None, None

    def parse(self, text: str):
        text_clean = self.clean(text)

        explicit_code, explicit_signification = self.parse_explicit_report_code(text_clean)

        if explicit_code:
            return explicit_code, explicit_signification

        direct_numeric_codes = [
            "10 99",
            "10 33",
            "10 32",
            "10 31",
            "10 30",
            "10 29",
            "10 20",
            "10 19",
            "10 17",
            "10 16",
            "10 15",
            "10 14",
            "10 13",
            "10 12",
            "10 11",
            "10 10",
            "10 9",
            "10 8",
            "10 7",
            "10 6",
            "10 5",
            "10 4",
            "10 3",
            "10 2",
            "10 1",
            "10 0",
            "459",
            "460",
            "461",
            "187",
            "207",
            "208",
        ]

        for numeric in direct_numeric_codes:
            pattern = self.alias_pattern(numeric)

            if re.search(pattern, text_clean):
                code = numeric.replace(" ", "-")

                if numeric in ["459", "460", "461", "187", "207", "208"]:
                    code = numeric

                signification = self.codes.get(code)

                if signification:
                    return code, signification

        for item in self.aliases:
            alias = item["alias_clean"]
            code = item["code"]

            pattern = self.alias_pattern(alias)

            if re.search(pattern, text_clean):
                signification = self.codes.get(code)

                if signification:
                    return code, signification

        return None, None