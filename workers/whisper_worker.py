from queue import Queue

from PySide6.QtCore import QThread, Signal

from audio.whisper import Whisper


class WhisperWorker(QThread):

    text_received = Signal(str)

    def __init__(self):
        super().__init__()

        self.queue = Queue()

        self.whisper = Whisper()

        self.running = True

    def add_audio(self, pcm):
        self.queue.put(pcm)

    def run(self):

        while self.running:

            pcm = self.queue.get()

            if pcm is None:
                continue

            try:

                text = self.whisper.transcribe_bytes(pcm)

                if text.strip():
                    self.text_received.emit(text)

            except Exception as e:
                self.text_received.emit(f"ERREUR : {e}")

    def stop(self):
        self.running = False
        self.queue.put(None)