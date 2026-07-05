import html
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

        self.logger = Logger()
        self.settings = Settings()

        self.parser = RadioParser()
        self.location_parser = LocationParser()
        self.unit_parser = UnitParser()
        self.direction_parser = DirectionParser()
        self.vehicle_parser = VehicleParser()
        self.incident_parser = IncidentParser()

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

    def append_radio_bubble(
        self,
        text,
        code=None,
        signification=None,
        unit=None,
        location=None,
        direction=None,
        vehicle=None,
        incidents=None,
    ):
        incidents = incidents or []

        time = datetime.now().strftime("%H:%M:%S")
        rows = []

        if unit:
            rows.append(f"👮 <b>Unité :</b> {html.escape(str(unit))}")

        if code:
            rows.append(f"📟 <b>Code :</b> {html.escape(str(code))}")

        if signification:
            rows.append(f"📖 <b>Motif :</b> {html.escape(str(signification))}")

        if location:
            rows.append(f"📍 <b>Lieu :</b> {html.escape(str(location['name']))}")

        if direction:
            rows.append(f"➡️ <b>Direction :</b> {html.escape(str(direction))}")

        if vehicle:
            label = vehicle["vehicle"]

            if vehicle["color"]:
                label += f" {vehicle['color']}"

            rows.append(f"🚗 <b>Véhicule :</b> {html.escape(str(label))}")

        for incident in incidents:
            rows.append(html.escape(str(incident)))

        if not rows:
            return

        body = "<br>".join(rows)

        bubble = f"""
        <div style="
            background-color:#313338;
            color:#dbdee1;
            border-left:4px solid #5865f2;
            padding:10px;
            margin:8px 4px;
            font-size:13px;
        ">
            <div style="color:#949ba4; font-size:11px; margin-bottom:6px;">
                RADIOVISION • {time}
            </div>

            <div style="font-size:14px; line-height:1.5;">
                {body}
            </div>
        </div>
        """

        self.window.details.append(bubble)

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

        self.append_radio_bubble(
            text=text,
            code=code,
            signification=signification,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            incidents=incidents,
        )

        if code:
            self.window.code.setText(f"📟 Code : {code}")
            self.window.signification.setText(f"📖 Signification : {signification}")

    def on_status(self, text):
        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )
        self.window.status.showMessage(text)

    def on_volume(self, value):
        self.window.volume.setValue(value)

    def show(self):
        self.window.show()