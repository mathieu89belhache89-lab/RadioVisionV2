import json
import re
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
            no_speech_threshold=0.85,
            compression_ratio_threshold=2.8,
            log_prob_threshold=-1.2,
            initial_prompt=(
                "Communication radio police LSPD GTA FiveM. "
                "Les codes radio peuvent être dits seuls. "
                "Codes patrol : 10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 10-6, 10-7, 10-8, 10-9, 10-99. "
                "Codes poursuite : 10-10, 10-11, 10-12, 10-13, 10-14, 10-15, 10-16, 10-17, 10-19. "
                "Codes braquage : 10-30, 10-31, 459, 460, 461. "
                "Codes divers : 10-20, 10-29, 10-32, 10-33, 187, 207, 208. "
                "Codes rapports : Code OD, Code DS, Code DOA, Code DCD, Code RDP, Code S. "
                "Codes urgence : Code 0, Code 1, Code 2, Code 3. "
                "Affiliations : Mary, Henry, AP, CP, Lincoln, Adams, Tango, Tango plus. "
                "Exemples : 10-10. 10-11. 10-30. 10-31. 459. 10-99. 207. 208."
            ),
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        )

        return self.clean_text(text)

    def clean_text(self, text):
        text = text.strip()

        replacements = {
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

        for bad, good in sorted(
            replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        ):
            lower = lower.replace(bad.lower(), good.lower())

        lower = re.sub(r"\b10\s*-\s*(\d+)\b", r"10-\1", lower)
        lower = re.sub(r"\s+", " ", lower)

        return lower.strip()