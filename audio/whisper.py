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
                "Communication radio police sur GTA FiveM. "
                "Phrases courtes possibles. "
                "Exemples : besoin de renfort, coups de feu, suspect armé. "
                "Exemples : central unité 21, 10-10 direction Sandy Shores, BMW M4 blanche. "
                "Exemples : dernier visuel vers Paleto, véhicule immobilisé, fuite à pied. "
                "Codes radio : 10-10, 10-11, 10-31, 10-99, CODE 3, 460. "
                "Lieux : Mission Row, Sandy Shores, Paleto Bay, Casino, Bijouterie."
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
            "direction légion": "direction Legion Square",
            "direction legion": "direction Legion Square",

            "mission roux": "Mission Row",
            "mission rowe": "Mission Row",
            "mission road": "Mission Row",

            "sandy short": "Sandy Shores",
            "sandy shore": "Sandy Shores",
            "sandy shoress": "Sandy Shores",

            "paletto": "Paleto Bay",

            "dix dix": "10-10",
            "dix onze": "10-11",
            "dix trente et un": "10-31",
            "dix quatre vingt dix neuf": "10-99",
            "dix quatre-vingt-dix-neuf": "10-99",

            "10 10": "10-10",
            "10 11": "10-11",
            "10 31": "10-31",
            "10 99": "10-99",

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

        for bad, good in replacements.items():
            lower = lower.replace(bad, good.lower())

        lower = re.sub(r"\b10\s*-\s*(\d+)\b", r"10-\1", lower)
        lower = re.sub(r"\s+", " ", lower)

        return lower.strip()