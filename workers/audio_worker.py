from PySide6.QtCore import QThread, Signal

from audio.capture import AudioCapture
from audio.vad import VoiceActivityDetector
from audio.whisper import Whisper


class AudioWorker(QThread):

    text_received = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False

        self.capture = AudioCapture()
        self.vad = VoiceActivityDetector()
        self.whisper = None

    def run(self):

        self.running = True

        self.capture.start()

        self.whisper = Whisper()

        self.text_received.emit("🎤 Capture continue démarrée")

        frames = []

        while self.running:

            pcm = self.capture.read()

            if self.vad.is_speech(pcm):

                frames.append(pcm)

            else:

                if len(frames) > 5:

                    audio = b"".join(frames)

                    text = self.whisper.transcribe_bytes(audio)

                    if text:
                        self.text_received.emit(text)

                frames.clear()

        self.capture.stop()

    def stop(self):
        self.running = False