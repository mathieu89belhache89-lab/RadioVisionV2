from PySide6.QtCore import QThread, Signal

from audio.capture import AudioCapture
from audio.whisper import Whisper


class AudioWorker(QThread):

    text_received = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False

        self.capture = AudioCapture()
        self.whisper = None

    def run(self):

        self.running = True

        self.capture.start()

        self.whisper = Whisper()

        self.text_received.emit("🎤 Capture continue démarrée")

        frames = []

        frames = []

        while self.running:

            pcm = self.capture.read()

            import numpy as np

            samples = np.frombuffer(pcm, dtype=np.int16)

            volume = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

            if volume > 400:

                frames.append(pcm)

            else:

                if len(frames) > 5:

                    audio = b"".join(frames)

                    text = self.whisper.transcribe_bytes(audio)

                    if text.strip():
                        self.text_received.emit(text)

                frames.clear()

        self.capture.stop()

    def stop(self):
        self.running = False