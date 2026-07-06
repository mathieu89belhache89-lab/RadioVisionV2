from collections import deque

import numpy as np
from PySide6.QtCore import QThread, Signal

from audio.capture import AudioCapture
from workers.whisper_worker import WhisperWorker


class AudioWorker(QThread):
    text_received = Signal(str)
    status = Signal(str)
    volume = Signal(int)

    def __init__(self, capture_microphone=False):
        super().__init__()

        self.running = False
        self.capture_microphone = bool(capture_microphone)

        self.capture = AudioCapture(
            capture_microphone=self.capture_microphone,
        )
        self.whisper = WhisperWorker()

        self.whisper.text_received.connect(self.text_received.emit)
        self.whisper.status.connect(self.status.emit)

        # V9 : lecture vocale plus fiable + segments longs.
        # Le bloc audio fait 0.20 ou 0.25 sec selon audio/capture.py.
        # Le but est d'éviter les coupures au milieu d'un call radio.
        self.threshold = 0.0014
        self.noise_floor = 0.00055
        self.noise_alpha = 0.04
        self.start_multiplier = 3.2
        self.stop_multiplier = 1.8

        # Avant : silence_limit=2 et max_blocks=16 (~4 sec).
        # Ça coupait trop vite les phrases longues.
        self.silence_limit = 6          # environ 1.2 à 1.5 sec de silence
        self.min_blocks = 4             # évite les micro-segments
        self.max_blocks = 90            # environ 18 à 22 sec max
        self.pre_roll_blocks = 5        # garde le début de la phrase
        self.speech_start_blocks = 2    # confirme la parole sur 2 blocs
        self.cooldown_blocks = 0        # ne perd pas le début du call suivant

    def dynamic_start_threshold(self):
        return max(self.threshold, self.noise_floor * self.start_multiplier)

    def dynamic_stop_threshold(self):
        return max(self.threshold * 0.70, self.noise_floor * self.stop_multiplier)

    def update_noise_floor(self, rms):
        # Mise à jour seulement sur les blocs bas pour éviter que la voix
        # augmente le niveau de bruit de référence.
        if rms <= self.dynamic_start_threshold():
            self.noise_floor = (
                self.noise_floor * (1.0 - self.noise_alpha)
                + float(rms) * self.noise_alpha
            )
            self.noise_floor = max(0.00020, min(self.noise_floor, 0.00600))

    def run(self):
        self.running = True

        self.status.emit("Démarrage capture audio...")

        self.capture.start()
        self.whisper.start()

        if self.capture_microphone:
            self.status.emit("Capture vocale V9 active avec micro.")
        else:
            self.status.emit("Capture vocale V9 active.")

        frames = []
        pre_roll = deque(maxlen=self.pre_roll_blocks)
        speech_start = deque(maxlen=self.speech_start_blocks)

        recording = False
        silence_count = 0
        cooldown_count = 0

        while self.running:
            block = self.capture.read(timeout=0.5)

            if block is None:
                continue

            block = block.astype(np.float32)
            rms = float(np.sqrt(np.mean(block ** 2)))

            self.volume.emit(int(min(rms * 15000, 100)))

            if cooldown_count > 0:
                cooldown_count -= 1
                pre_roll.clear()
                speech_start.clear()
                continue

            if not recording:
                self.update_noise_floor(rms)

            start_threshold = self.dynamic_start_threshold()
            stop_threshold = self.dynamic_stop_threshold()

            if not recording:
                if rms >= start_threshold:
                    speech_start.append(block)

                    if len(speech_start) >= self.speech_start_blocks:
                        frames = list(pre_roll) + list(speech_start)
                        recording = True
                        silence_count = 0
                        speech_start.clear()
                else:
                    speech_start.clear()
                    pre_roll.append(block)

                continue

            frames.append(block)

            if rms < stop_threshold:
                silence_count += 1
            else:
                silence_count = 0

            if silence_count >= self.silence_limit:
                self._send_segment(frames, forced_split=False)
                frames = []
                recording = False
                silence_count = 0
                pre_roll.clear()
                speech_start.clear()
                cooldown_count = self.cooldown_blocks
                continue

            if len(frames) >= self.max_blocks:
                # Cas rare : très long call sans silence. On coupe, mais on indique
                # au WhisperWorker que le morceau suivant peut être une suite.
                self._send_segment(frames, forced_split=True)
                frames = []
                recording = False
                silence_count = 0
                pre_roll.clear()
                speech_start.clear()
                cooldown_count = self.cooldown_blocks

        if frames:
            self._send_segment(frames, forced_split=False)

        self.capture.stop()
        self.whisper.stop()
        self.whisper.wait()

        self.status.emit("Capture arrêtée.")

    def _send_segment(self, frames, forced_split=False):
        if len(frames) < self.min_blocks:
            return

        audio = np.concatenate(frames).astype(np.float32)

        duration = len(audio) / float(self.capture.sample_rate)
        self.status.emit(f"Segment envoyé à Whisper ({duration:.1f}s)")
        self.whisper.add_audio(audio, forced_split=forced_split)

    def stop(self):
        self.running = False
