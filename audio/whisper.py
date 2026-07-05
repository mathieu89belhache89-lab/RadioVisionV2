import re
import numpy as np
from faster_whisper import WhisperModel


class Whisper:

    def __init__(self):
        self.model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

    def transcribe_array(self, audio):
        audio = np.asarray(audio, dtype=np.float32)

        if len(audio) < 16000:
            return ""

        audio = audio - np.mean(audio)

        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.95

        segments, _ = self.model.transcribe(
            audio,
            language="fr",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=False,
            condition_on_previous_text=False,
            no_speech_threshold=0.45,
            compression_ratio_threshold=2.4,
            initial_prompt=(
                "Communication radio police sur GTA FiveM. "
                "Exemples : Central de l'unité 32, 10-80 direction Legion Square, Sultan noire. "
                "Codes radio : 10-0, 10-1, 10-2, 10-3, 10-4, 10-5, 10-8, 10-20, 10-30, 10-31, 10-80, 10-99. "
                "Lieux : Legion Square, Mission Row, Sandy Shores, Paleto Bay, Vinewood, Vespucci, Davis, Pillbox."
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
            "direction région": "direction Legion Square",
            "direction les gens": "direction Legion Square",
            "légion": "Legion Square",
            "legion": "Legion Square",

            "mission roux": "Mission Row",
            "mission rowe": "Mission Row",
            "mission road": "Mission Row",

            "sandy short": "Sandy Shores",
            "sandy shore": "Sandy Shores",
            "sandy shores": "Sandy Shores",

            "paletto": "Paleto Bay",
            "paleto": "Paleto Bay",

            "dix quatre": "10-4",
            "dix cinq": "10-5",
            "dix vingt": "10-20",
            "dix quatre-vingt": "10-80",
            "dix quatre vingt": "10-80",

            "10 4": "10-4",
            "10 5": "10-5",
            "10 20": "10-20",
            "10 80": "10-80",
        }

        lower = text.lower()

        for bad, good in replacements.items():
            lower = lower.replace(bad, good)

        lower = re.sub(r"\b10\s*-\s*(\d+)\b", r"10-\1", lower)
        lower = re.sub(r"\s+", " ", lower)

        return lower.strip()