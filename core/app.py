from datetime import datetime

from PySide6.QtCore import QObject

from core.logger import Logger
from core.settings import Settings
from ui.main_window import MainWindow
from ui.theme import apply_theme

from workers.audio_worker import AudioWorker


class RadioVisionApp(QObject):

    def __init__(self):
        super().__init__()

        self.logger = Logger()
        self.settings = Settings()

        apply_theme()

        self.window = MainWindow()

        self.audio_worker = None

        self._connect_signals()

        self.logger.info("RadioVision démarré")

    def _connect_signals(self):

        self.window.start_button.clicked.connect(self.start)
        self.window.stop_button.clicked.connect(self.stop)

        self.window.action_start.triggered.connect(self.start)
        self.window.action_stop.triggered.connect(self.stop)

    def start(self):

        if self.audio_worker and self.audio_worker.isRunning():
            return

        self.audio_worker = AudioWorker()
        self.audio_worker.text_received.connect(self.on_text)

        self.audio_worker.start()

        self.window.state.setText("🟢 Écoute")
        self.window.status.showMessage("Capture audio active")

        self.logger.info("Capture démarrée")

    def stop(self):

        if self.audio_worker:

            self.audio_worker.stop()
            self.audio_worker.wait()

        self.window.state.setText("🔴 Arrêtée")
        self.window.status.showMessage("Capture arrêtée")

        self.logger.info("Capture arrêtée")

    def on_text(self, text):

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )

    def show(self):
        self.window.show()