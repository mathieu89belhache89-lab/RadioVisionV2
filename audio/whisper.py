import json
import re
import unicodedata
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel


class Whisper:

    def __init__(self):
        self.model_name = self.load_model_name()

        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",
        )

    def load_model_name(self):
        settings_file = Path("data") / "radiovision_settings.json"

        allowed = ["tiny", "base", "small"]

        if not settings_file.exists():
            return "base"

        try:
            with settings_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            model_name = data.get("whisper_model", "base")

            if model_name in allowed:
                return model_name

        except Exception:
            pass

        return "base"

    def transcribe_array(self, audio):
        audio = np.asarray(audio, dtype=np.float32)

        if len(audio) < 4000:
            return ""

        audio = audio - np.mean(audio)

        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.95

        segments, _ = self.model.transcribe(
            audio,
            language="fr",
            beam_size=1,
            best_of=1,
            temperature=0.0,
            vad_filter=False,
            condition_on_previous_text=False,
            no_speech_threshold=0.65,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            initial_prompt=(
                "Communication radio police LSPD GTA FiveM. "
                "Codes radio courts possibles. "
                "Exemples codes seuls : 10-2, 10-4, 10-6, 10-7, 10-8, 10-10, 10-11, 10-12, 10-30, 10-31, 459, 460, 461, 10-99, 187, 207, 208. "
                "Exemples rapports : Code OD, Code DS, Code DOA, Code DCD, Code RDP, Code S. "
                "Exemples urgences : Code 0, Code 1, Code 2, Code 3. "
                "Exemples affiliations : Mary, Henry, AP, CP, Lincoln, Adams, Tango, Tango plus. "
                "Informations générales : PDP, PO."
            ),
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        )

        return self.clean_text(text)

    def known_code_tokens(self):
        return {
            "10-0",
            "10-1",
            "10-2",
            "10-3",
            "10-4",
            "10-5",
            "10-6",
            "10-7",
            "10-8",
            "10-9",
            "10-10",
            "10-11",
            "10-12",
            "10-13",
            "10-14",
            "10-15",
            "10-16",
            "10-17",
            "10-19",
            "10-20",
            "10-29",
            "10-30",
            "10-31",
            "10-32",
            "10-33",
            "10-99",
            "459",
            "460",
            "461",
            "187",
            "207",
            "208",
            "code 0",
            "code 1",
            "code 2",
            "code 3",
            "code od",
            "code ds",
            "code doa",
            "code dcd",
            "code rdp",
            "code s",
            "mary",
            "henry",
            "ap",
            "cp",
            "lincoln",
            "adams",
            "tango",
            "tango+",
            "pdp",
            "po",
        }

    def get_most_common_token(self, counts):
        most_common_token = ""
        most_common_count = 0

        for token, count in counts.items():
            if count > most_common_count:
                most_common_token = token
                most_common_count = count

        return most_common_token, most_common_count

    def is_prompt_noise(self, text):
        text = text.strip().lower()

        exact_noise = {
            "exemples",
            "dis",
            "dis dis",
            "dis dis dis",
            "dis en",
            "dis-en",
            "monique tamer",
            "monique ta mer",
            "ahead son son cop niff",
        }

        if text in exact_noise:
            return True

        noise_parts = [
            "faire foutre",
            "son son cop",
            "la question est a dire",
            "la question est à dire",
            "depute de la police",
            "député de la police",
        ]

        for part in noise_parts:
            if part in text:
                return True

        return False

    def is_repeated_sentence_noise(self, text):
        text = text.strip().lower()

        if len(text) < 60:
            return False

        words = re.findall(r"[a-z0-9]+", text)

        if len(words) < 12:
            return False

        for size in range(3, 9):
            chunks = []

            for index in range(0, len(words), size):
                chunk = " ".join(words[index:index + size])

                if len(chunk.split()) == size:
                    chunks.append(chunk)

            if not chunks:
                continue

            counts = {}

            for chunk in chunks:
                counts[chunk] = counts.get(chunk, 0) + 1

            _, count = self.get_most_common_token(counts)

            if count >= 3:
                return True

        return False

    def force_short_code_text(self, text):
        """
        Correction agressive pour les codes radio seuls.
        Ne s'applique que sur les phrases courtes pour éviter
        de casser les vraies phrases radio.
        """
        raw = str(text).lower().strip()

        raw = unicodedata.normalize("NFD", raw)
        raw = "".join(
            c for c in raw
            if unicodedata.category(c) != "Mn"
        )

        raw = raw.replace(",", " ")
        raw = raw.replace(".", " ")
        raw = raw.replace("_", " ")
        raw = raw.replace("'", " ")
        raw = raw.replace("-", " ")

        raw = re.sub(r"[^a-z0-9+ ]", " ", raw)
        raw = re.sub(r"\s+", " ", raw).strip()

        if not raw:
            return ""

        words = raw.split()

        # Sécurité : uniquement phrases courtes.
        if len(words) > 7:
            return text

        compact = raw.replace(" ", "")

        variants = {
            "10-0": [
                "10 0",
                "100",
                "dix zero",
                "dis zero",
                "dise zero",
                "dizo",
                "diso",
            ],

            "10-1": [
                "10 1",
                "101",
                "dix un",
                "dis un",
                "dise un",
                "dit un",
                "disons",
                "dis on",
                "disque",
                "disk",
                "dixain",
                "dizin",
            ],

            "10-2": [
                "10 2",
                "102",
                "6-2",
                "dix deux",
                "dis deux",
                "dise deux",
                "dit deux",
                "dix de",
                "dis de",
                "dis due",
                "disdue",
                "dis d",
                "disd",
                "dis deux",
                "dix due",
                "diz de",
            ],

            "10-3": [
                "10 3",
                "103",
                "dix trois",
                "dis trois",
                "dise trois",
                "dit trois",
                "distrois",
            ],

            "10-4": [
                "10 4",
                "14",
                "104",
                "dix quatre",
                "dis quatre",
                "dise quatre",
                "dit quatre",
                "dis quatre",
                "disquatre",
                "dis 4",
                "dix 4",
                "dit 4",
                "disquette",
                "disquet",
                "dixquette",
                "dix quattre",
            ],

            "10-5": [
                "10 5",
                "105",
                "dix cinq",
                "dis cinq",
                "dise cinq",
                "dit cinq",
                "dis sank",
                "dis cinq",
                "dix sank",
                "dissank",
                "cinq",
                "5",
            ],

            "10-6": [
                "10 6",
                "106",
                "dix six",
                "dis six",
                "dise six",
                "dit six",
                "dissix",
                "this is",
                "this six",
                "six six",
                "6 6",
                "cis cis",
                "cisse cisse",
                "cis",
                "cisse",
                "six",
                "6",
            ],

            "10-7": [
                "10 7",
                "107",
                "dix sept",
                "dis sept",
                "dise sept",
                "dit sept",
                "dix 7",
                "10 sept",
                "17",
                "set",
                "disces",
                "dices",
                "disses",
                "dixces",
                "dis c",
            ],

            "10-8": [
                "10 8",
                "18",
                "108",
                "dix huit",
                "dis huit",
                "dise huit",
                "dit huit",
                "dizuit",
                "dix huitre",
                "dissuite",
                "dis suite",
                "huit",
                "8",
            ],

            "10-9": [
                "10 9",
                "19",
                "109",
                "dix neuf",
                "dis neuf",
                "dise neuf",
                "dit neuf",
                "dis 9",
                "dix 9",
                "neuf",
                "9",
            ],

            "10-10": [
                "10 10",
                "1010",
                "this this",
                "dix dix",
                "dis dix",
                "dise dix",
                "dit dix",
                "codes content",
                "code content",
                "content",
                "est-ce-d'ici",
            ],

            "10-11": [
                "10 11",
                "1011",
                "1111",
                "dix onze",
                "dis onze",
                "dise onze",
                "dit onze",
            ],

            "10-12": [
                "10 12",
                "612",
                "1012",
                "dix douze",
                "dis douze",
                "dise douze",
                "disse douze",
                "disse ouz",
                "dis ouz",
                "dix douce",
                "dise douce",
                "dis douce",
                "douze",
            ],

            "10-13": [
                "10 13",
                "1013",
                "dix treize",
                "dis treize",
                "dise treize",
                "dit treize",
            ],

            "10-14": [
                "10 14",
                "1014",
                "dix quatorze",
                "dis quatorze",
                "dise quatorze",
                "dit quatorze",
            ],

            "10-15": [
                "10 15",
                "15",
                "1015",
                "disquins",
                "dix quinze",
                "dis quinze",
                "dise quinze",
                "dit quinze",
            ],

            "10-16": [
                "10 16",
                "1016",
                "dissez",
                "dix seize",
                "dis seize",
                "dise seize",
                "dit seize",
            ],

            "10-17": [
                "10 17",
                "1017",
                "dix dix sept",
                "code 17",
                "codes 17",
            ],

            "10-19": [
                "10 19",
                "1019",
                "dix dix neuf",
                "accident",
            ],

            "10-20": [
                "10 20",
                "1020",
                "dix vingt",
            ],

            "10-29": [
                "10 29",
                "1029",
                "dix vingt neuf",
                "ras",
                "r a s",
            ],

            "10-30": [
                "10 30",
                "30",
                "1030",
                "dix trente",
                "code 30",
                "codes 30",
            ],

            "10-31": [
                "10 31",
                "1031",
                "dix trente et un",
                "code 31",
                "codes 31",
            ],

            "10-32": [
                "10 32",
                "32",
                "1032",
                "dix trente deux",
                "sniper",
            ],

            "10-33": [
                "10 33",
                "33",
                "1033",
                "dix trente trois",
            ],

            "10-99": [
                "10 99",
                "1099",
                "10 89",
                "1089",
                "10 98",
                "1098",
                "dis 99",
                "dix 99",
                "dise 99",
                "dit 99",
                "dix quatre vingt dix neuf",
                "dis quatre vingt dix neuf",
                "quatre vingt dix neuf",
                "renfort immediat",
                "renfort immediate",
                "demande renfort immediat",
            ],

            "459": [
                "459",
                "450 9",
                "4509",
                "code 5 59",
                "code 559",
                "quatre cent cinquante neuf",
            ],

            "460": [
                "460",
                "quatre cent soixante",
            ],

            "461": [
                "461",
                "quatre cent soixante et un",
            ],

            "187": [
                "187",
                "cent quatre vingt sept",
            ],

            "207": [
                "207",
                "277",
                "deux cent sept",
            ],

            "208": [
                "208",
                "108",
                "code 108",
                "code de 108",
                "codes de 108",
                "deux cent huit",
            ],

            "CODE 0": [
                "code 0",
                "code zero",
            ],

            "CODE 1": [
                "code 1",
                "code un",
            ],

            "CODE 2": [
                "code 2",
                "code deux",
            ],

            "CODE 3": [
                "code 3",
                "code trois",
            ],

            "CODE OD": [
                "code od",
                "code o d",
                "code oscar david",
            ],

            "CODE DS": [
                "code ds",
                "code d s",
                "code dsd",
                "code des",
                "code delta sierra",
            ],

            "CODE DOA": [
                "code doa",
                "code d o a",
                "code delta oscar alpha",
            ],

            "CODE DCD": [
                "code dcd",
                "code d c d",
                "code delta charlie delta",
            ],

            "CODE RDP": [
                "code rdp",
                "code r d p",
                "code romeo delta papa",
            ],

            "CODE S": [
                "code s",
                "codes s",
                "code esse",
                "codesse",
                "code est",
            ],

            "MARY": [
                "mary",
                "marie",
                "mari",
                "merry",
                "mairie",
                "meri",
            ],

            "HENRY": [
                "henry",
                "henri",
                "enri",
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
                "tango+",
            ],

            "PDP": [
                "pdp",
                "p d p",
                "poste de police",
            ],

            "PO": [
                "po",
                "p o",
                "peau",
                "p eau",
                "prise otage",
                "prise d otage",
            ],
        }

        for code, alias_list in variants.items():
            for alias in alias_list:
                alias_clean = alias.lower().strip()

                alias_clean = unicodedata.normalize("NFD", alias_clean)
                alias_clean = "".join(
                    c for c in alias_clean
                    if unicodedata.category(c) != "Mn"
                )

                alias_clean = alias_clean.replace("-", " ")
                alias_clean = alias_clean.replace("'", " ")
                alias_clean = re.sub(r"[^a-z0-9+ ]", " ", alias_clean)
                alias_clean = re.sub(r"\s+", " ", alias_clean).strip()

                alias_compact = alias_clean.replace(" ", "")

                if raw == alias_clean:
                    return code.lower()

                if compact == alias_compact:
                    return code.lower()

        return text
    
    def fix_repetition_loop(self, text):
        text = text.strip()

        if not text:
            return ""

        if self.is_prompt_noise(text):
            return ""

        if self.is_repeated_sentence_noise(text):
            return ""

        lower = text.lower()

        joined_clean = re.sub(r"[^a-z0-9+-]+", " ", lower)
        joined_clean = re.sub(r"\s+", " ", joined_clean).strip()

        special_repeated_patterns = {
            "codes s": "code s",
            "code s": "code s",
            "codes od": "code od",
            "code od": "code od",
            "codes ds": "code ds",
            "code ds": "code ds",
            "code dsd": "code ds",
            "codes dsd": "code ds",
            "codes doa": "code doa",
            "code doa": "code doa",
            "codes dcd": "code dcd",
            "code dcd": "code dcd",
            "codes rdp": "code rdp",
            "code rdp": "code rdp",
        }

        for repeated, fixed in special_repeated_patterns.items():
            if joined_clean.count(repeated) >= 2:
                return fixed

        known_codes = self.known_code_tokens()

        for code in known_codes:
            if "-" in code and lower.count(code) >= 2:
                return code

        tokens = re.findall(r"10-\d{1,2}|[a-z0-9]+", lower)

        if len(tokens) < 3:
            return text

        counts = {}

        for token in tokens:
            counts[token] = counts.get(token, 0) + 1

        most_common_token, most_common_count = self.get_most_common_token(counts)

        if not most_common_token:
            return ""

        repetition_ratio = most_common_count / len(tokens)

        useless_tokens = {
            "code",
            "codes",
            "d",
            "o",
            "s",
            "dis",
            "content",
            "exemples",
            "question",
            "depute",
            "police",
        }

        if len(tokens) >= 3 and most_common_count == len(tokens):
            if most_common_token in known_codes:
                return most_common_token

            if most_common_token in ["208", "207", "459"]:
                return most_common_token

            return ""

        if repetition_ratio >= 0.60:
            if most_common_token in known_codes:
                return most_common_token

            if most_common_token in ["208", "207", "459"]:
                return most_common_token

            if most_common_token in useless_tokens:
                return ""

            return ""

        return text

    def clean_text(self, text):
        text = text.strip()

        replacements = {
            "code ds code 19": "code ds",
            "code dsd": "code ds",
            "codes dsd": "code ds",
            "code des": "code ds",
            "codes des": "code ds",

            "codes content": "10-10",
            "code content": "10-10",

            "codes 30": "10-30",
            "code 30": "10-30",
            "codes 31": "10-31",
            "code 31": "10-31",
            "codes 17": "10-17",
            "code 17": "10-17",

            "codes sont en cascant neuf": "10-99",
            "codes quatre vingt dix neuf": "10-99",
            "code quatre vingt dix neuf": "10-99",

            "10-89": "10-99",
            "10 89": "10-99",
            "10-98": "10-99",
            "10 98": "10-99",

            "450-9": "459",
            "450 9": "459",
            "code 5 59": "459",
            "code 5, 59": "459",
            "code 559": "459",

            "codes de 108": "208",
            "code de 108": "208",
            "code 108": "208",

            "277": "207",

            "dix quatre vingt dix neuf": "10-99",
            "dix quatre-vingt-dix-neuf": "10-99",

            "dix trente et un": "10-31",
            "dix trente deux": "10-32",
            "dix trente trois": "10-33",
            "dix trente": "10-30",

            "dix vingt neuf": "10-29",
            "dix vingt": "10-20",

            "dix dix sept": "10-17",
            "dix dix neuf": "10-19",
            "dix seize": "10-16",
            "dix quinze": "10-15",
            "dix quatorze": "10-14",
            "dix treize": "10-13",
            "dix douze": "10-12",
            "dix onze": "10-11",
            "dix dix": "10-10",

            "dix zéro": "10-0",
            "dix zero": "10-0",
            "dix un": "10-1",
            "dix deux": "10-2",
            "dix trois": "10-3",
            "dix quatre": "10-4",
            "dix cinq": "10-5",
            "dix six": "10-6",
            "dix sept": "10-7",
            "dix huit": "10-8",
            "dix neuf": "10-9",

            "10 99": "10-99",
            "10 33": "10-33",
            "10 32": "10-32",
            "10 31": "10-31",
            "10 30": "10-30",
            "10 29": "10-29",
            "10 20": "10-20",
            "10 19": "10-19",
            "10 17": "10-17",
            "10 16": "10-16",
            "10 15": "10-15",
            "10 14": "10-14",
            "10 13": "10-13",
            "10 12": "10-12",
            "10 11": "10-11",
            "10 10": "10-10",
            "10 9": "10-9",
            "10 8": "10-8",
            "10 7": "10-7",
            "10 6": "10-6",
            "10 5": "10-5",
            "10 4": "10-4",
            "10 3": "10-3",
            "10 2": "10-2",
            "10 1": "10-1",
            "10 0": "10-0",

            "quatre cent soixante et un": "461",
            "quatre cent soixante": "460",
            "quatre cent cinquante neuf": "459",

            "cent quatre vingt sept": "187",
            "deux cent huit": "208",
            "deux cent sept": "207",

            "code zéro": "code 0",
            "code zero": "code 0",
            "code un": "code 1",
            "code deux": "code 2",
            "code trois": "code 3",

            "code oscar david": "code od",
            "code delta sierra": "code ds",
            "code delta oscar alpha": "code doa",
            "code delta charlie delta": "code dcd",
            "code romeo delta papa": "code rdp",

            "tango plus": "tango+",

            "direction légion": "direction Legion Square",
            "direction legion": "direction Legion Square",
            "mission roux": "Mission Row",
            "mission rowe": "Mission Row",
            "mission road": "Mission Row",
            "sandy short": "Sandy Shores",
            "sandy shore": "Sandy Shores",
            "sandy shoress": "Sandy Shores",
            "paletto": "Paleto Bay",

            "pour suite": "poursuite",
            "pour suites": "poursuite",

            "a pcie": "à pied",
            "a pie": "à pied",
            "a pieds": "à pied",

            "poisons de renfort": "besoin de renfort",
            "besoins de renfort": "besoin de renfort",
            "besoin d un renfort": "besoin de renfort",

            "coup de feu": "coups de feu",
            "coups de feux": "coups de feu",

            "supermiss": "suspect",
            "super mis": "suspect",
            "sus permis": "suspect",

            "suspect armer": "suspect armé",
            "suspect arme": "suspect armé",
        }

        lower = text.lower()

        lower = lower.replace(",", " ")
        lower = lower.replace(".", " ")

        for bad, good in sorted(
            replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            lower = lower.replace(bad.lower(), good.lower())

        lower = re.sub(r"\bcodes?\s+s\b", "code s", lower)
        lower = re.sub(r"\bcodes?\s+od\b", "code od", lower)
        lower = re.sub(r"\bcodes?\s+ds\b", "code ds", lower)
        lower = re.sub(r"\bcodes?\s+doa\b", "code doa", lower)
        lower = re.sub(r"\bcodes?\s+dcd\b", "code dcd", lower)
        lower = re.sub(r"\bcodes?\s+rdp\b", "code rdp", lower)

        lower = re.sub(r"\b10\s*-\s*(\d+)\b", r"10-\1", lower)
        lower = re.sub(r"\s+", " ", lower).strip()

        forced = self.force_short_code_text(lower)

        if forced != lower:
            return forced.strip()

        lower = self.fix_repetition_loop(lower)

        return lower.strip()