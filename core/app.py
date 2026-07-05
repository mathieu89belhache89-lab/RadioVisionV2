from ui.main_window import MainWindow
from ui.theme import apply_theme
from core.logger import Logger
from core.settings import Settings
from datetime import datetime
from PySide6.QtCore import QTimer


class RadioVisionApp:

    def __init__(self):

        self.logger = Logger()
        self.settings = Settings()

        apply_theme()

        self.window = MainWindow()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(100)

        self._connect_signals()

        self.logger.info("RadioVision démarré")

    def _connect_signals(self):

        self.window.start_button.clicked.connect(self.start)

        self.window.stop_button.clicked.connect(self.stop)

    def start(self):

        self.window.state.setText("🟢 Écoute")

        self.window.status.showMessage("Capture audio démarrée")

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] ▶ Capture démarrée"
        )

        self.window.volume.setValue(100)

        self.logger.info("Capture démarrée")


    def stop(self):

        self.window.state.setText("🔴 Arrêtée")

        self.window.status.showMessage("Capture arrêtée")

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] ⏹ Capture arrêtée"
        )

        self.logger.info("Capture arrêtée")

    def show(self):
        self.window.show()

    def update_ui(self):

        value = self.window.volume.value()

        if value > 0:
            value -= 1

        self.window.volume.setValue(value)    

