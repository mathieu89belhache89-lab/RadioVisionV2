from collections import deque

import numpy as np
from PySide6.QtCore import QThread, Signal

from audio.capture import AudioCapture
from workers.whisper_worker import WhisperWorker


class AudioWorker(QThread):
    text_received = Signal(str)
    status = Signal(str)
    volume = Signal(int)

    def __init__(self):
        super().__init__()

        self.running = False

        self.capture = AudioCapture()
        self.whisper = WhisperWorker()

        self.whisper.text_received.connect(self.text_received.emit)
        self.whisper.status.connect(self.status.emit)

        self.threshold = 0.0018
        self.silence_limit = 8
        self.min_blocks = 6
        self.max_blocks = 32
        self.pre_roll_blocks = 4

    def run(self):
        self.running = True

        self.status.emit("Démarrage capture audio...")

        self.capture.start()
        self.whisper.start()

        self.status.emit("Capture continue active.")

        frames = []
        pre_roll = deque(maxlen=self.pre_roll_blocks)

        recording = False
        silence_count = 0

        while self.running:
            block = self.capture.read(timeout=0.5)

            if block is None:
                continue

            rms = float(
                np.sqrt(
                    np.mean(block.astype(np.float32) ** 2)
                )
            )

            self.volume.emit(int(min(rms * 15000, 100)))

            is_voice = rms >= self.threshold

            if is_voice:
                if not recording:
                    frames = list(pre_roll)
                    recording = True
                    silence_count = 0

                frames.append(block)
                silence_count = 0

            else:
                if recording:
                    frames.append(block)
                    silence_count += 1

                    if silence_count >= self.silence_limit:
                        self._send_segment(frames)
                        frames = []
                        recording = False
                        silence_count = 0
                        pre_roll.clear()
                else:
                    pre_roll.append(block)

            if recording and len(frames) >= self.max_blocks:
                self._send_segment(frames)
                frames = []
                recording = False
                silence_count = 0
                pre_roll.clear()

        if frames:
            self._send_segment(frames)

        self.capture.stop()
        self.whisper.stop()
        self.whisper.wait()

        self.status.emit("Capture arrêtée.")

    def _send_segment(self, frames):
        if len(frames) < self.min_blocks:
            return

        audio = np.concatenate(frames).astype(np.float32)

        self.status.emit("Segment envoyé à Whisper")
        self.whisper.add_audio(audio)

    def stop(self):
        self.running = False