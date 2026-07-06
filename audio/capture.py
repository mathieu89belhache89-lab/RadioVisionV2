import queue
import threading
import warnings

import numpy as np
import soundcard as sc


class AudioCapture:
    def __init__(self, capture_microphone=False):
        self.sample_rate = 16000
        self.block_seconds = 0.25
        self.block_size = int(self.sample_rate * self.block_seconds)

        self.capture_microphone = bool(capture_microphone)

        self.loopback_gain = 1.0
        self.microphone_gain = 0.85

        self.queue = queue.Queue(maxsize=80)
        self.loopback_queue = queue.Queue(maxsize=20)
        self.microphone_queue = queue.Queue(maxsize=20)

        self.running = False
        self.threads = []

        self.speaker = sc.default_speaker()
        self.loopback_microphone = sc.get_microphone(
            self.speaker.name,
            include_loopback=True,
        )

        self.user_microphone = None

        if self.capture_microphone:
            try:
                self.user_microphone = sc.default_microphone()
            except Exception:
                self.user_microphone = None

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
        self.threads = []

        if self.capture_microphone and self.user_microphone is not None:
            self._start_thread(self._loopback_to_queue_loop)
            self._start_thread(self._microphone_to_queue_loop)
            self._start_thread(self._mixer_loop)
        else:
            self._start_thread(self._loopback_direct_loop)

    def stop(self):
        self.running = False

        for thread in self.threads:
            thread.join(timeout=2)

        self.threads = []

    def _start_thread(self, target):
        thread = threading.Thread(
            target=target,
            daemon=True,
        )

        self.threads.append(thread)
        thread.start()

    def _normalize_block(self, data):
        if data is None:
            return None

        data = np.asarray(data, dtype=np.float32)

        if data.ndim == 2:
            data = np.mean(data, axis=1)

        if len(data) == 0:
            return None

        if len(data) > self.block_size:
            data = data[:self.block_size]

        if len(data) < self.block_size:
            padded = np.zeros(self.block_size, dtype=np.float32)
            padded[:len(data)] = data
            data = padded

        data = np.clip(data, -1.0, 1.0)

        return data.astype(np.float32)

    def _push(self, block):
        self._push_to_queue(self.queue, block)

    def _push_to_queue(self, target_queue, block):
        if block is None:
            return

        try:
            target_queue.put_nowait(block)
        except queue.Full:
            try:
                target_queue.get_nowait()
            except queue.Empty:
                pass

            try:
                target_queue.put_nowait(block)
            except queue.Full:
                pass

    def _get_latest(self, source_queue):
        latest = None

        while True:
            try:
                latest = source_queue.get_nowait()
            except queue.Empty:
                break

        return latest

    def _loopback_direct_loop(self):
        try:
            with self.loopback_microphone.recorder(
                samplerate=self.sample_rate,
                channels=2,
            ) as recorder:

                while self.running:
                    data = recorder.record(numframes=self.block_size)
                    block = self._normalize_block(data)
                    self._push(block)
        except Exception:
            self.running = False

    def _loopback_to_queue_loop(self):
        try:
            with self.loopback_microphone.recorder(
                samplerate=self.sample_rate,
                channels=2,
            ) as recorder:

                while self.running:
                    data = recorder.record(numframes=self.block_size)
                    block = self._normalize_block(data)
                    self._push_to_queue(self.loopback_queue, block)
        except Exception:
            pass

    def _microphone_to_queue_loop(self):
        if self.user_microphone is None:
            return

        try:
            with self.user_microphone.recorder(
                samplerate=self.sample_rate,
                channels=1,
            ) as recorder:

                while self.running:
                    data = recorder.record(numframes=self.block_size)
                    block = self._normalize_block(data)
                    self._push_to_queue(self.microphone_queue, block)
        except Exception:
            pass

    def _mixer_loop(self):
        silence = np.zeros(self.block_size, dtype=np.float32)

        while self.running:
            loopback_block = None

            try:
                loopback_block = self.loopback_queue.get(timeout=0.35)
            except queue.Empty:
                pass

            microphone_block = self._get_latest(self.microphone_queue)

            if loopback_block is None and microphone_block is None:
                continue

            if loopback_block is None:
                loopback_block = silence

            if microphone_block is None:
                microphone_block = silence

            mixed = (
                loopback_block.astype(np.float32) * self.loopback_gain
                + microphone_block.astype(np.float32) * self.microphone_gain
            )

            peak = float(np.max(np.abs(mixed)))

            if peak > 1.0:
                mixed = mixed / peak

            mixed = np.clip(mixed, -1.0, 1.0).astype(np.float32)

            self._push(mixed)

    def read(self, timeout=0.5):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None
