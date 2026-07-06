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
        self.queue = queue.Queue(maxsize=8)

        self.whisper = None

        self.last_text = ""
        self.last_text_time = 0.0

        # V9 : petit tampon texte pour recoller les morceaux proches.
        self.pending_text = ""
        self.pending_time = 0.0
        self.pending_max_age = 1.35
        self.merge_max_age = 4.0

    def add_audio(self, audio, forced_split=False):
        if audio is None:
            return

        item = (np.asarray(audio, dtype=np.float32), bool(forced_split))

        while self.queue.qsize() >= 6:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

        try:
            self.queue.put_nowait(item)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass

            try:
                self.queue.put_nowait(item)
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

    def looks_incomplete(self, text):
        text_clean = self.normalize_text(text)

        if not text_clean:
            return False

        words = text_clean.split()

        if len(words) <= 3:
            return True

        last_word = words[-1]

        incomplete_endings = {
            "central",
            "unite",
            "direction",
            "vers",
            "agent",
            "vehicule",
            "besoin",
            "dernier",
            "visuel",
            "suspect",
            "code",
        }

        if last_word in incomplete_endings:
            return True

        # Les rapports sensibles sont souvent coupés :
        # "central code od agent at" + "mission row besoin de renfort".
        if "code od" in text_clean and len(words) <= 8:
            return True

        if "agent a terre" in text_clean and len(words) <= 8:
            return True

        if "agent at" in text_clean or "agent atr" in text_clean:
            return True

        if "prise d otage" in text_clean and len(words) <= 7:
            return True

        return False

    def looks_like_continuation(self, text):
        text_clean = self.normalize_text(text)

        continuation_words = [
            "mission",
            "row",
            "permission",
            "renfort",
            "immediat",
            "vehicule",
            "immobilise",
            "direction",
            "vers",
            "suspect",
            "arme",
            "otage",
            "individus",
            "bord",
            "dernier",
            "visuel",
        ]

        return any(word in text_clean for word in continuation_words)

    def should_merge_pending_with(self, next_text):
        if not self.pending_text:
            return False

        if time.time() - self.pending_time > self.merge_max_age:
            return False

        if self.looks_incomplete(self.pending_text):
            return True

        if self.looks_like_continuation(next_text) and len(self.normalize_text(next_text).split()) <= 7:
            return True

        return False

    def emit_final_text(self, text):
        text = str(text or "").strip()

        if not text:
            return

        text = self.remove_repeated_prefix(text).strip()

        if not text:
            return

        if self.is_tiny_noise(text):
            return

        self.last_text = text
        self.last_text_time = time.time()

        self.text_received.emit(text)

    def queue_or_emit_text(self, text):
        text = str(text or "").strip()

        if not text:
            return

        if self.pending_text:
            if self.should_merge_pending_with(text):
                combined = f"{self.pending_text} {text}".strip()
                self.pending_text = ""
                self.pending_time = 0.0
                self.emit_final_text(combined)
                return

            self.flush_pending(force=True)

        if self.looks_incomplete(text):
            self.pending_text = text
            self.pending_time = time.time()
            return

        self.emit_final_text(text)

    def flush_pending(self, force=False):
        if not self.pending_text:
            return

        if not force and time.time() - self.pending_time < self.pending_max_age:
            return

        text = self.pending_text
        self.pending_text = ""
        self.pending_time = 0.0
        self.emit_final_text(text)

    def get_queue_item(self, timeout=0.2):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def normalize_queue_item(self, item):
        if item is None:
            return None, False, True

        if isinstance(item, tuple):
            audio, forced_split = item
            return audio, bool(forced_split), False

        return item, False, False

    def merge_forced_audio_continuation(self, first_audio, first_forced_split):
        if not first_forced_split:
            return first_audio

        pieces = [first_audio]
        end_time = time.time() + 0.45

        while time.time() < end_time:
            timeout = max(0.01, end_time - time.time())
            item = self.get_queue_item(timeout=timeout)

            if item is None:
                break

            audio, forced_split, stop_signal = self.normalize_queue_item(item)

            if stop_signal:
                self.running = False
                break

            if audio is None:
                break

            pieces.append(np.asarray(audio, dtype=np.float32))

            if not forced_split:
                break

        if len(pieces) == 1:
            return first_audio

        return np.concatenate(pieces).astype(np.float32)

    def run(self):
        self.running = True

        self.status.emit("Chargement Whisper...")

        self.whisper = Whisper()

        self.status.emit(f"Whisper prêt ({self.whisper.engine_label()}).")

        while self.running:
            item = self.get_queue_item(timeout=0.2)

            if item is None:
                self.flush_pending(force=False)
                continue

            audio, forced_split, stop_signal = self.normalize_queue_item(item)

            if stop_signal:
                continue

            if audio is None:
                continue

            try:
                audio = np.asarray(audio, dtype=np.float32)
                audio = self.merge_forced_audio_continuation(audio, forced_split)

                before_engine = self.whisper.engine_label()
                text = self.whisper.transcribe_array(audio).strip()
                after_engine = self.whisper.engine_label()

                if after_engine != before_engine:
                    self.status.emit(f"Whisper basculé en secours ({after_engine}).")

                if not text:
                    self.flush_pending(force=False)
                    continue

                self.queue_or_emit_text(text)

            except Exception as e:
                self.text_received.emit(f"ERREUR WHISPER : {e}")

        self.flush_pending(force=True)

    def stop(self):
        self.running = False
        try:
            self.queue.put_nowait(None)
        except queue.Full:
            pass
