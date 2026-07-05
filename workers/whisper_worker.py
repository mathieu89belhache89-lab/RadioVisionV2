import queue

import numpy as np
from PySide6.QtCore import QThread, Signal

from audio.whisper import Whisper


class WhisperWorker(QThread):
    text_received = Signal(str)
    status = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False
        self.queue = queue.Queue(maxsize=20)

        self.whisper = None

    def add_audio(self, audio):
        if audio is None:
            return

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

                text = self.whisper.transcribe_array(audio)

                if text.strip():
                    self.text_received.emit(text.strip())

            except Exception as e:
                self.text_received.emit(f"ERREUR WHISPER : {e}")

    def stop(self):
        self.running = False
        self.queue.put(None)