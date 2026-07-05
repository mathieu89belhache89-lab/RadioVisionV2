from PySide6.QtCore import QThread

import numpy as np

from audio.capture import AudioCapture
from workers.whisper_worker import WhisperWorker


class AudioWorker(QThread):

    def __init__(self):
        super().__init__()

        self.running = False

        self.capture = AudioCapture()

        self.whisper = WhisperWorker()

    def run(self):

        self.running = True

        self.capture.start()

        self.whisper.start()

        frames = []

        while self.running:

            pcm = self.capture.read()

            samples = np.frombuffer(pcm, dtype=np.int16)

            volume = np.sqrt(
                np.mean(samples.astype(np.float32) ** 2)
            )

            if volume > 400:

                frames.append(pcm)

            else:

                if len(frames) >= 8:

                    self.whisper.add_audio(
                        b"".join(frames)
                    )

                frames.clear()

        self.capture.stop()
        self.whisper.stop()
        self.whisper.wait()

    def stop(self):
        self.running = False