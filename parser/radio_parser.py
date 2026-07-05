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
        text = text.replace("'", " ")

        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        replacements = {
            "dix quatre vingt dix neuf": "10 99",
            "dix quatre vingt dix": "10 90",

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
            "10-0": [
                "10 0",
                "10-0",
                "dix zero",
                "dix zéro",
                "retour au poste",
                "retour poste",
            ],
            "10-1": [
                "10 1",
                "10-1",
                "dix un",
                "en route",
                "en route sur les lieux",
            ],
            "10-2": [
                "10 2",
                "10-2",
                "dix deux",
                "en patrouille",
                "retour patrouille",
            ],
            "10-3": [
                "10 3",
                "10-3",
                "dix trois",
                "demande de renfort",
            ],
            "10-4": [
                "10 4",
                "10-4",
                "dix quatre",
                "bien recu",
                "message bien recu",
                "confirmation",
            ],
            "10-5": [
                "10 5",
                "10-5",
                "dix cinq",
                "negatif",
                "négatif",
            ],
            "10-6": [
                "10 6",
                "10-6",
                "dix six",
                "en cours",
                "occupe",
                "occupé",
            ],
            "10-7": [
                "10 7",
                "10-7",
                "dix sept",
                "transfert suspect",
            ],
            "10-8": [
                "10 8",
                "10-8",
                "dix huit",
                "fusillade",
                "echange de coup de feu",
                "échange de coup de feu",
            ],
            "10-9": [
                "10 9",
                "10-9",
                "dix neuf",
                "tirs sur notre unite",
                "tirs sur notre unité",
            ],
            "10-99": [
                "10 99",
                "10-99",
                "dix quatre vingt dix neuf",
                "demande de renfort immediat",
                "demande de renfort immédiat",
                "renfort immediat",
                "renfort immédiat",
            ],

            "10-10": [
                "10 10",
                "10-10",
                "dix dix",
                "refus d obtemperer a pied",
                "refus d obtempere a pied",
            ],
            "10-11": [
                "10 11",
                "10-11",
                "dix onze",
                "refus d obtemperer en voiture",
                "refus d obtempere en voiture",
            ],
            "10-12": [
                "10 12",
                "10-12",
                "dix douze",
                "refus d obtemperer en voiture rapide",
            ],
            "10-13": [
                "10 13",
                "10-13",
                "dix treize",
                "refus d obtemperer en moto",
            ],
            "10-14": [
                "10 14",
                "10-14",
                "dix quatorze",
                "refus d obtemperer en vehicule aerien",
            ],
            "10-15": [
                "10 15",
                "10-15",
                "dix quinze",
                "refus d obtemperer en vehicule aquatique",
            ],
            "10-16": [
                "10 16",
                "10-16",
                "dix seize",
                "suspect perdu",
            ],
            "10-17": [
                "10 17",
                "10-17",
                "dix dix sept",
                "autorisation tirer sur les pneus",
                "tirer sur les pneus",
            ],
            "10-19": [
                "10 19",
                "10-19",
                "dix dix neuf",
                "accident",
            ],

            "10-20": [
                "10 20",
                "10-20",
                "dix vingt",
                "regroupement important",
            ],
            "10-29": [
                "10 29",
                "10-29",
                "dix vingt neuf",
                "ras",
                "r a s",
            ],
            "10-30": [
                "10 30",
                "10-30",
                "dix trente",
                "risque de braquage",
            ],
            "10-31": [
                "10 31",
                "10-31",
                "dix trente et un",
                "braquage confirme",
                "braquage confirmé",
            ],
            "10-32": [
                "10 32",
                "10-32",
                "dix trente deux",
                "sniper",
            ],
            "10-33": [
                "10 33",
                "10-33",
                "dix trente trois",
                "unite parachutiste",
                "unité parachutiste",
            ],

            "459": [
                "459",
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
                "supérette",
            ],
            "187": [
                "187",
                "cent quatre vingt sept",
                "homicide",
            ],
            "207": [
                "207",
                "deux cent sept",
                "enlevement",
                "enlèvement",
            ],
            "208": [
                "208",
                "deux cent huit",
                "prise d otage sur agent",
            ],

            "CODE 0": [
                "code 0",
                "code zero",
                "code zéro",
                "probleme de tete",
                "problème de tête",
            ],
            "CODE 1": [
                "code 1",
                "code un",
                "appel gouvernement",
            ],
            "CODE 2": [
                "code 2",
                "code deux",
                "unite silencieuse",
                "unité silencieuse",
            ],
            "CODE 3": [
                "code 3",
                "code trois",
                "urgence toutes les unites",
                "sirene et gyrophare",
                "sirène et gyrophare",
            ],

            "CODE OD": [
                "code od",
                "code o d",
                "code oscar david",
                "agent a terre",
                "agent à terre",
            ],
            "CODE DS": [
                "code ds",
                "code d s",
                "code delta sierra",
                "suspect neutralise",
                "suspect neutralisé",
                "suspect abattu",
            ],
            "CODE DOA": [
                "code doa",
                "code d o a",
                "code delta oscar alpha",
                "civil a terre",
                "civil à terre",
            ],
            "CODE DCD": [
                "code dcd",
                "code d c d",
                "code delta charlie delta",
                "civil decede",
                "civil décédé",
            ],
            "CODE RDP": [
                "code rdp",
                "code r d p",
                "code romeo delta papa",
                "recapitulatif des patrouilles",
                "récapitulatif des patrouilles",
            ],
            "CODE S": [
                "code s",
                "silence radio",
                "silence radio total",
            ],

            "PDP": [
                "pdp",
                "p d p",
                "poste de police",
            ],
            "PO": [
                "po",
                "p o",
                "prise d otage",
            ],

            "MARY": [
                "mary",
                "marie",
                "patrouille en moto",
            ],
            "HENRY": [
                "henry",
                "henri",
                "patrouille en helicoptere",
                "patrouille en hélicoptère",
            ],
            "AP": [
                "ap",
                "a p",
                "patrouille en avion",
            ],
            "CP": [
                "cp",
                "c p",
                "patrouille des hauts grades",
                "patrouille des hauts gradés",
            ],
            "LINCOLN": [
                "lincoln",
                "patrouille seul",
            ],
            "ADAMS": [
                "adams",
                "adam",
                "patrouille a deux",
                "patrouille à deux",
            ],
            "TANGO": [
                "tango",
                "patrouille a trois",
                "patrouille à trois",
            ],
            "TANGO+": [
                "tango plus",
                "tango +",
                "patrouille a quatre",
                "patrouille à quatre",
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

    def parse(self, text: str):
        text_clean = self.clean(text)

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