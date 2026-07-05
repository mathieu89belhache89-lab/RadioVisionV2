import queue
import threading
import warnings

import numpy as np
import soundcard as sc


class AudioCapture:
    def __init__(self):
        self.sample_rate = 16000
        self.block_seconds = 0.25
        self.block_size = int(self.sample_rate * self.block_seconds)

        self.queue = queue.Queue(maxsize=80)

        self.running = False
        self.thread = None

        self.speaker = sc.default_speaker()
        self.microphone = sc.get_microphone(
            self.speaker.name,
            include_loopback=True,
        )

        try:
            warnings.filterwarnings(
                "ignore",
                category=sc.SoundcardRuntimeWarning,
            )
        except Exception:
            pass

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )

        self.thread.start()

    def stop(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

    def _push(self, block):
        try:
            self.queue.put_nowait(block)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass

            try:
                self.queue.put_nowait(block)
            except queue.Full:
                pass

    def _loop(self):
        with self.microphone.recorder(
            samplerate=self.sample_rate,
            channels=2,
        ) as recorder:

            while self.running:
                data = recorder.record(numframes=self.block_size)

                if data is None:
                    continue

                data = np.asarray(data, dtype=np.float32)

                if data.ndim == 2:
                    data = np.mean(data, axis=1)

                data = np.clip(data, -1.0, 1.0)

                self._push(data)

    def read(self, timeout=0.5):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None