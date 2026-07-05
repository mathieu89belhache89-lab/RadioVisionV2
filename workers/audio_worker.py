from PySide6.QtCore import QThread, Signal

from audio.capture import AudioCapture
from audio.whisper import Whisper


class AudioWorker(QThread):

    text_received = Signal(str)

    def __init__(self):
        super().__init__()

        self.running = False

        self.capture = None
        self.whisper = None

    def run(self):

        self.running = True

        self.capture = AudioCapture()
        self.text_received.emit("🎤 Capture audio démarrée...")

        if self.whisper is None:
            self.whisper = Whisper()
            self.text_received.emit("🧠 Whisper chargé.")

        while self.running:

            try:

                audio = self.capture.record(seconds=3)

                self.text_received.emit(f"✅ Audio capturé : {audio}")

                text = self.whisper.transcribe(audio)

                if text:
                    self.text_received.emit(f"📝 {text}")
                else:
                    self.text_received.emit("⚠️ Aucun texte reconnu")

            except Exception as e:
                self.text_received.emit(f"ERREUR : {e}")


    def stop(self):
        self.running = False