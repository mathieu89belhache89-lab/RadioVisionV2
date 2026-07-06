import queue
import re
import time
import unicodedata

import numpy as np
from PySide6.QtCore import QThread, Signal

from audio.whisper import Whisper

try:
    from rapidfuzz import fuzz
except Exception:
    fuzz = None


class WhisperWorker(QThread):
    text_received = Signal(str)
    status = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False
        self.queue = queue.Queue(maxsize=4)

        self.whisper = None

        self.last_text = ""
        self.last_text_time = 0.0

    def add_audio(self, audio):
        if audio is None:
            return

        while self.queue.qsize() >= 3:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

        try:
            self.queue.put_nowait(audio)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass

            try:
                self.queue.put_nowait(audio)
            except queue.Full:
                pass

    def normalize_text(self, text):
        text = str(text).lower().strip()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = text.replace("'", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def similarity(self, left, right):
        left = self.normalize_text(left)
        right = self.normalize_text(right)

        if not left or not right:
            return 0

        if fuzz:
            return int(fuzz.ratio(left, right))

        # Fallback sans rapidfuzz.
        import difflib

        return int(difflib.SequenceMatcher(None, left, right).ratio() * 100)

    def is_tiny_noise(self, text):
        text_clean = self.normalize_text(text)

        noises = {
            "",
            "central",
            "unite",
            "radio",
            "merci",
            "ok",
            "euh",
            "heu",
            "dis",
            "dis en",
            "exemples",
        }

        return text_clean in noises

    def remove_exact_repeated_prefix(self, text):
        current_clean = self.normalize_text(text)
        last_clean = self.normalize_text(self.last_text)

        if not current_clean or not last_clean:
            return text

        if current_clean == last_clean:
            return ""

        if current_clean.startswith(last_clean + " "):
            rest = current_clean[len(last_clean):].strip()

            if len(rest.split()) >= 2:
                return rest

            return ""

        return text

    def remove_fuzzy_repeated_prefix(self, text):
        current_clean = self.normalize_text(text)
        last_clean = self.normalize_text(self.last_text)

        if not current_clean or not last_clean:
            return text

        current_tokens = current_clean.split()
        last_tokens = last_clean.split()

        if len(current_tokens) < 5 or len(last_tokens) < 5:
            return text

        # Cas où Whisper renvoie quasiment la même phrase.
        if self.similarity(current_clean, last_clean) >= 92:
            return ""

        min_size = max(4, len(last_tokens) - 5)
        max_size = min(len(current_tokens), len(last_tokens) + 8)

        best_size = 0
        best_score = 0

        for size in range(max_size, min_size - 1, -1):
            candidate = " ".join(current_tokens[:size])
            score = self.similarity(candidate, last_clean)

            if score > best_score:
                best_score = score
                best_size = size

        if best_score >= 86 and best_size > 0:
            rest_tokens = current_tokens[best_size:]

            if len(rest_tokens) >= 2:
                return " ".join(rest_tokens)

            return ""

        return text

    def remove_repeated_prefix(self, text):
        now = time.time()

        if not self.last_text:
            return text

        if now - self.last_text_time > 25:
            return text

        text = self.remove_exact_repeated_prefix(text)

        if not text:
            return ""

        text = self.remove_fuzzy_repeated_prefix(text)

        return text

    def run(self):
        self.running = True

        self.status.emit("Chargement Whisper...")

        self.whisper = Whisper()

        self.status.emit("Whisper prêt.")

        while self.running:
            audio = self.queue.get()

            if audio is None:
                continue

            try:
                audio = np.asarray(audio, dtype=np.float32)

                text = self.whisper.transcribe_array(audio).strip()

                if not text:
                    continue

                text = self.remove_repeated_prefix(text).strip()

                if not text:
                    continue

                if self.is_tiny_noise(text):
                    continue

                self.last_text = text
                self.last_text_time = time.time()

                self.text_received.emit(text)

            except Exception as e:
                self.text_received.emit(f"ERREUR WHISPER : {e}")

    def stop(self):
        self.running = False
        self.queue.put(None)
