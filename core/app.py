from datetime import datetime

from PySide6.QtCore import QObject

from core.logger import Logger
from core.settings import Settings
from ui.main_window import MainWindow
from ui.theme import apply_theme
from workers.audio_worker import AudioWorker
from parser.radio_parser import RadioParser
from parser.location_parser import LocationParser
from parser.unit_parser import UnitParser
from parser.direction_parser import DirectionParser
from parser.vehicle_parser import VehicleParser
from parser.incident_parser import IncidentParser


class RadioVisionApp(QObject):

    def __init__(self):
        super().__init__()

        self.incident_parser = IncidentParser()
        self.vehicle_parser = VehicleParser()
        self.direction_parser = DirectionParser()
        self.location_parser = LocationParser()
        self.unit_parser = UnitParser()

        self.logger = Logger()
        self.settings = Settings()
        self.parser = RadioParser()

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

        self.window.state.setText("🟢 Écoute")
        self.window.status.showMessage("Démarrage audio...")

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] ▶ Démarrage capture audio"
        )

        self.audio_worker = AudioWorker()

        self.audio_worker.text_received.connect(self.on_text)
        self.audio_worker.status.connect(self.on_status)
        self.audio_worker.volume.connect(self.on_volume)

        self.audio_worker.start()

        self.logger.info("Capture démarrée")

    def stop(self):
        if self.audio_worker:
            self.audio_worker.stop()
            self.audio_worker.wait()
            self.audio_worker = None

        self.window.state.setText("🔴 Arrêtée")
        self.window.status.showMessage("Capture arrêtée")
        self.window.volume.setValue(0)

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] ⏹ Capture arrêtée"
        )

        self.logger.info("Capture arrêtée")

    def on_text(self, text):
        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )

        code, signification = self.parser.parse(text)
        location = self.location_parser.find(text)
        unit = self.unit_parser.find(text)
        direction = self.direction_parser.find(text)
        vehicle = self.vehicle_parser.find(text)
        incidents = self.incident_parser.find(text)

        if unit:
            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] 👮 Unité : {unit}"
            )

        if location:
            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] 📍 Lieu : {location['name']}"
            )

        if direction:
            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] ➡️ Direction : {direction}"
            )

        if vehicle:
            label = vehicle["vehicle"]

            if vehicle["color"]:
                label += f" {vehicle['color']}"

            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] 🚗 Véhicule : {label}"
            )

        for incident in incidents:
            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] {incident}"
            )    

        if code:
            self.window.code.setText(f"📟 Code : {code}")
            self.window.signification.setText(f"📖 Signification : {signification}")

            self.window.details.append(
                f"[{datetime.now():%H:%M:%S}] {code} → {signification}"
            )

    def on_status(self, text):
        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )
        self.window.status.showMessage(text)

    def on_volume(self, value):
        self.window.volume.setValue(value)

    def show(self):
        self.window.show()