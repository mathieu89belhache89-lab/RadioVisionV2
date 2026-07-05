import queue
import threading

import numpy as np
import soundcard as sc


class AudioCapture:

    def __init__(self):

        self.sample_rate = 16000
        self.block_size = 320

        speaker = sc.default_speaker()

        self.microphone = sc.get_microphone(
            speaker.name,
            include_loopback=True,
        )

        self.queue = queue.Queue()

        self.running = False
        self.thread = None

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._record_loop,
            daemon=True,
        )

        self.thread.start()

    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join()

    def _record_loop(self):

        with self.microphone.recorder(
            samplerate=self.sample_rate
        ) as recorder:

            while self.running:

                audio = recorder.record(
                    numframes=self.block_size
                )

                audio = np.mean(audio, axis=1)

                audio = np.clip(audio, -1, 1)

                pcm = (audio * 32767).astype(np.int16)

                self.queue.put(pcm.tobytes())

                if len(pcm) != 320:
                    continue

    def read(self):

        return self.queue.get()