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
        text = str(text or "").lower()

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
        text = text.replace("’", " ")

        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        replacements = {
            # Bruits / mauvaises lectures de codes 10.
            "codes content": "10 10",
            "code content": "10 10",
            "code contant": "10 10",
            "codes contant": "10 10",
            "code comptant": "10 10",
            "codes comptant": "10 10",

            "codes 30": "10 30",
            "code 30": "10 30",
            "codes trente": "10 30",
            "code trente": "10 30",
            "codes 31": "10 31",
            "code 31": "10 31",
            "codes trente et un": "10 31",
            "code trente et un": "10 31",
            "codes 32": "10 32",
            "code 32": "10 32",
            "codes trente deux": "10 32",
            "code trente deux": "10 32",
            "codes 33": "10 33",
            "code 33": "10 33",
            "codes trente trois": "10 33",
            "code trente trois": "10 33",
            "codes 17": "10 17",
            "code 17": "10 17",

            "codes sont en cascant neuf": "10 99",
            "code sont en cascant neuf": "10 99",
            "codes quatre vingt dix neuf": "10 99",
            "code quatre vingt dix neuf": "10 99",
            "codes quatre vingt dix neuf": "10 99",
            "dix quatre vingt dix neuf": "10 99",
            "dis quatre vingt dix neuf": "10 99",
            "dis 99": "10 99",
            "dix 99": "10 99",
            "10 89": "10 99",
            "10 98": "10 99",

            # Codes trois chiffres.
            "450 9": "459",
            "code 5 59": "459",
            "code 559": "459",
            "quatre cent cinquante neuf": "459",
            "quatre cent soixante et un": "461",
            "quatre cent soixante": "460",
            "cent quatre vingt sept": "187",
            "deux cent huit": "208",
            "deux cent sept": "207",
            "277": "207",
            "codes de 108": "208",
            "code de 108": "208",
            "code 108": "208",
            "108": "208",

            # Codes 10 parlés.
            "dix trente trois": "10 33",
            "dix trente deux": "10 32",
            "dix trente et un": "10 31",
            "dix trente": "10 30",
            "dix vingt neuf": "10 29",
            "dix vingt": "10 20",
            "dix dix neuf": "10 19",
            "dix dix sept": "10 17",
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

            "dis trente trois": "10 33",
            "dis trente deux": "10 32",
            "dis trente et un": "10 31",
            "dis trente": "10 30",
            "dis vingt neuf": "10 29",
            "dis vingt": "10 20",
            "dis dix neuf": "10 19",
            "dis dix sept": "10 17",
            "dis seize": "10 16",
            "dis quinze": "10 15",
            "dis quatorze": "10 14",
            "dis treize": "10 13",
            "dis douze": "10 12",
            "dis onze": "10 11",
            "dis dix": "10 10",
            "dis zero": "10 0",
            "dis un": "10 1",
            "dis deux": "10 2",
            "dis trois": "10 3",
            "dis quatre": "10 4",
            "dis cinq": "10 5",
            "dis six": "10 6",
            "dis sept": "10 7",
            "dis huit": "10 8",
            "dis neuf": "10 9",

            # Lectures très fréquentes de Whisper.
            "disons": "10 11",
            "dizonze": "10 11",
            "dis onze": "10 11",
            "disonze": "10 11",
            "disque": "10 4",
            "disquette": "10 4",
            "disquatre": "10 4",
            "dis quatre": "10 4",
            "dis sank": "10 5",
            "dis cinq": "10 5",
            "cis cis": "10 6",
            "six six": "10 6",
            "this is": "10 6",
            "disces": "10 7",
            "dix sept": "10 7",
            "diz neuf": "10 9",

            # Codes radio spéciaux.
            "code trois": "code 3",
            "code deux": "code 2",
            "code un": "code 1",
            "code zero": "code 0",
            "code oscar david": "code od",
            "code o d": "code od",
            "code delta sierra": "code ds",
            "code d s": "code ds",
            "code delta oscar alpha": "code doa",
            "code d o a": "code doa",
            "code delta charlie delta": "code dcd",
            "code d c d": "code dcd",
            "code romeo delta papa": "code rdp",
            "code r d p": "code rdp",
            "code esse": "code s",
            "code est": "code s",

            "oscar david": "od",
            "delta sierra": "ds",
            "delta oscar alpha": "doa",
            "delta charlie delta": "dcd",
            "romeo delta papa": "rdp",

            "poste de police": "pdp",
            "prise d otage": "po",
            "prise dotage": "po",
            "agent pris en otage": "208",
            "agent prise en otage": "208",
            "agent pris en hotel": "208",
            "tango plus": "tango plus",
        }

        for bad, good in sorted(
            replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            text = re.sub(
                r"\b" + re.escape(bad) + r"\b",
                good,
                text,
            )

        text = re.sub(r"\bcodes?\s+s\b", "code s", text)
        text = re.sub(r"\bcodes?\s+od\b", "code od", text)
        text = re.sub(r"\bcodes?\s+o\s+d\b", "code od", text)
        text = re.sub(r"\bcodes?\s+ds\b", "code ds", text)
        text = re.sub(r"\bcodes?\s+d\s+s\b", "code ds", text)
        text = re.sub(r"\bcodes?\s+doa\b", "code doa", text)
        text = re.sub(r"\bcodes?\s+d\s+o\s+a\b", "code doa", text)
        text = re.sub(r"\bcodes?\s+dcd\b", "code dcd", text)
        text = re.sub(r"\bcodes?\s+d\s+c\s+d\b", "code dcd", text)
        text = re.sub(r"\bcodes?\s+rdp\b", "code rdp", text)
        text = re.sub(r"\bcodes?\s+r\s+d\s+p\b", "code rdp", text)

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

    def add_aliases(self, code, aliases):
        for alias in aliases:
            self.add_alias(code, alias)

    def build_aliases(self):
        for code in self.codes.keys():
            self.add_alias(code, code)

        manual_aliases = {
            "10-0": [
                "10 0", "10-0", "dix zero", "dis zero",
                "retour au poste", "retour pdp",
            ],
            "10-1": [
                "10 1", "10-1", "dix un", "dis un", "en route",
                "en route sur les lieux",
            ],
            "10-2": [
                "10 2", "10-2", "dix deux", "dis deux", "en patrouille",
                "retour en patrouille",
            ],
            "10-3": [
                "10 3", "10-3", "dix trois", "dis trois", "demande de renfort code 3",
            ],
            "10-4": [
                "10 4", "10-4", "dix quatre", "dis quatre", "disquatre",
                "disquette", "disque", "message bien recu", "bien recu",
            ],
            "10-5": [
                "10 5", "10-5", "dix cinq", "dis cinq", "dis sank", "negatif",
            ],
            "10-6": [
                "10 6", "10-6", "dix six", "dis six", "cis cis", "six six",
                "this is", "occupe", "en cours",
            ],
            "10-7": [
                "10 7", "10-7", "dix sept", "dis sept", "disces",
                "transfert suspect", "transfert d un suspect",
            ],
            "10-8": [
                "10 8", "10-8", "dix huit", "dis huit", "fusillade",
            ],
            "10-9": [
                "10 9", "10-9", "dix neuf", "dis neuf", "diz neuf",
                "tirs sur notre unite",
            ],
            "10-10": [
                "10 10", "10-10", "dix dix", "dis dix", "codes content",
                "code content", "code contant", "refus d obtemperer a pied",
                "refus obtemperer a pied",
            ],
            "10-11": [
                "10 11", "10-11", "dix onze", "dis onze", "disonze", "dizonze",
                "disons", "refus d obtemperer en voiture", "refus obtemperer en voiture",
            ],
            "10-12": [
                "10 12", "10-12", "dix douze", "dis douze",
                "refus d obtemperer rapide", "refus d obtemperer en voiture rapide",
            ],
            "10-13": [
                "10 13", "10-13", "dix treize", "dis treize",
                "refus d obtemperer en moto", "refus obtemperer moto",
            ],
            "10-14": [
                "10 14", "10-14", "dix quatorze", "dis quatorze",
                "refus d obtemperer aerien", "vehicule aerien en fuite",
            ],
            "10-15": [
                "10 15", "10-15", "dix quinze", "dis quinze",
                "refus d obtemperer aquatique", "vehicule aquatique en fuite",
            ],
            "10-16": [
                "10 16", "10-16", "dix seize", "dis seize", "suspect perdu",
            ],
            "10-17": [
                "10 17", "10-17", "dix dix sept", "dis dix sept", "code 17",
                "autorisation de tirer sur les pneus", "tirer sur les pneus",
            ],
            "10-19": [
                "10 19", "10-19", "dix dix neuf", "dis dix neuf", "accident",
            ],
            "10-20": [
                "10 20", "10-20", "dix vingt", "dis vingt", "regroupement important",
            ],
            "10-29": [
                "10 29", "10-29", "dix vingt neuf", "dis vingt neuf", "ras", "r a s",
            ],
            "10-30": [
                "10 30", "10-30", "dix trente", "dis trente", "code 30", "codes 30",
                "risque de braquage",
            ],
            "10-31": [
                "10 31", "10-31", "dix trente et un", "dis trente et un", "code 31",
                "codes 31", "braquage confirme",
            ],
            "10-32": [
                "10 32", "10-32", "dix trente deux", "dis trente deux", "code 32",
                "sniper",
            ],
            "10-33": [
                "10 33", "10-33", "dix trente trois", "dis trente trois", "code 33",
                "unite parachutiste",
            ],
            "10-99": [
                "10 99", "10-99", "10 89", "10-89", "10 98", "10-98",
                "dix quatre vingt dix neuf", "dis quatre vingt dix neuf", "dix 99",
                "dis 99", "renfort immediat", "demande de renfort immediat",
            ],
            "459": [
                "459", "450 9", "450-9", "code 5 59", "code 559",
                "quatre cent cinquante neuf", "cambriolage",
            ],
            "460": [
                "460", "quatre cent soixante", "braquage",
            ],
            "461": [
                "461", "quatre cent soixante et un", "superette", "supérette",
            ],
            "187": [
                "187", "cent quatre vingt sept", "homicide",
            ],
            "207": [
                "207", "277", "deux cent sept", "enlevement",
            ],
            "208": [
                "208", "108", "code 108", "code de 108", "codes de 108",
                "deux cent huit", "prise d otage sur agent", "agent pris en otage",
                "agent pris en hotel",
            ],
            "CODE 0": ["code 0", "code zero", "probleme de tete"],
            "CODE 1": ["code 1", "code un", "appel gouvernement"],
            "CODE 2": ["code 2", "code deux", "unite silencieuse"],
            "CODE 3": ["code 3", "code trois", "urgence", "urgence sirene"],
            "CODE OD": [
                "code od", "code o d", "code oscar david", "agent a terre", "agent at", "agent atr",
            ],
            "CODE DS": [
                "code ds", "code d s", "code delta sierra", "suspect neutralise", "suspect abattu",
            ],
            "CODE DOA": [
                "code doa", "code d o a", "code delta oscar alpha", "civil a terre",
            ],
            "CODE DCD": [
                "code dcd", "code d c d", "code delta charlie delta", "civil decede",
            ],
            "CODE RDP": [
                "code rdp", "code r d p", "code romeo delta papa", "recapitulatif des patrouilles",
            ],
            "CODE S": [
                "code s", "codes s", "code esse", "code est", "silence radio",
            ],
            "PDP": ["pdp", "p d p", "poste de police"],
            "PO": ["po", "p o", "prise d otage"],
            "MARY": ["mary", "marie", "mari", "mairie"],
            "HENRY": ["henry", "henri", "enry"],
            "AP": ["ap", "a p"],
            "CP": ["cp", "c p"],
            "LINCOLN": ["lincoln", "lincon"],
            "ADAMS": ["adams", "adam"],
            "TANGO": ["tango"],
            "TANGO+": ["tango plus", "tango +"],
        }

        for code, aliases in manual_aliases.items():
            self.add_aliases(code, aliases)

        # Déduplication : garde le premier code associé à l'alias nettoyé.
        # L'ordre du dictionnaire ci-dessus garde les cas prioritaires.
        seen = set()
        deduplicated = []

        for item in self.aliases:
            key = (item["code"], item["alias_clean"])
            if key in seen:
                continue
            seen.add(key)
            deduplicated.append(item)

        self.aliases = sorted(
            deduplicated,
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
            ("CODE OD", ["code od", "code o d", "agent a terre", "agent at", "agent atr"]),
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
