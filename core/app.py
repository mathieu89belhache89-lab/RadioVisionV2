import html
import time
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

        self.last_bubbles = {}
        self.duplicate_delay = 10

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

    def build_signature(
        self,
        code=None,
        unit=None,
        location=None,
        direction=None,
        vehicle=None,
        incidents=None,
    ):
        incidents = incidents or []

        location_name = ""
        if location:
            location_name = location.get("name", "")

        vehicle_key = ""
        if vehicle:
            vehicle_key = vehicle.get("key") or vehicle.get("vehicle", "")

        signature_parts = [
            str(code or ""),
            str(unit or ""),
            str(location_name or ""),
            str(direction or ""),
            str(vehicle_key or ""),
            "|".join(incidents),
        ]

        return " / ".join(signature_parts).lower().strip()

    def is_duplicate(self, signature):
        if not signature:
            return False

        now = time.time()
        old_keys = []

        for key, last_time in self.last_bubbles.items():
            if now - last_time > self.duplicate_delay:
                old_keys.append(key)

        for key in old_keys:
            del self.last_bubbles[key]

        if signature in self.last_bubbles:
            return True

        self.last_bubbles[signature] = now
        return False

    def get_missing_infos(
        self,
        code=None,
        unit=None,
        location=None,
        direction=None,
        vehicle=None,
    ):
        missing = []

        has_any_info = any([
            code,
            unit,
            location,
            direction,
            vehicle,
        ])

        if not has_any_info:
            return missing

        if not unit:
            missing.append("unité")

        if not code:
            missing.append("code radio")

        if not location and not direction:
            missing.append("lieu / direction")
        elif not direction:
            missing.append("direction")

        if code in ["10-10", "10-11"] and not vehicle:
            missing.append("véhicule")

        return missing

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

        missing_infos = self.get_missing_infos(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
        )

        signature = self.build_signature(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            incidents=incidents,
        )

        if self.is_duplicate(signature):
            self.window.radio_log.append(
                f"[{datetime.now():%H:%M:%S}] Doublon ignoré"
            )
            return

        time_now = datetime.now().strftime("%H:%M:%S")

        priority_color = "#5865f2"
        priority_label = "INFO"

        if code in ["10-99", "CODE 3", "460", "10-31"]:
            priority_color = "#ed4245"
            priority_label = "URGENT"

        elif code in ["10-10", "10-11"]:
            priority_color = "#faa61a"
            priority_label = "POURSUITE"

        if missing_infos:
            priority_color = "#faa61a"
            priority_label = "INCOMPLET"

        rows = []

        if unit:
            rows.append(("👮", "Unité", html.escape(str(unit))))

        if code:
            rows.append(("📟", "Code", html.escape(str(code))))

        if signification:
            rows.append(("📖", "Motif", html.escape(str(signification))))

        if location:
            rows.append(("📍", "Lieu", html.escape(str(location["name"]))))

        if direction:
            rows.append(("➡️", "Direction", html.escape(str(direction))))

        if vehicle:
            label = vehicle["vehicle"]

            if vehicle["color"]:
                label += f" {vehicle['color']}"

            rows.append(("🚗", "Véhicule", html.escape(str(label))))

        for incident in incidents:
            rows.append(("", "Info", html.escape(str(incident))))

        if missing_infos:
            missing_text = ", ".join(missing_infos)
            rows.append(("❔", "Manquant", html.escape(missing_text)))

        if not rows:
            return

        table_rows = ""

        for emoji, label, value in rows:
            table_rows += f"""
            <tr>
                <td style="width:24px; padding:2px 4px;">{emoji}</td>
                <td style="color:#ffffff; font-weight:bold; padding:2px 6px;">
                    {label}
                </td>
                <td style="color:#dbdee1; padding:2px 4px;">
                    {value}
                </td>
            </tr>
            """

        bubble = f"""
        <div style="
            background-color:#2b2d31;
            color:#dbdee1;
            border-left:5px solid {priority_color};
            padding:9px;
            margin:8px 4px;
            font-size:13px;
        ">
            <div style="
                color:#949ba4;
                font-size:11px;
                margin-bottom:6px;
            ">
                RADIOVISION • {time_now}
                <span style="
                    color:{priority_color};
                    font-weight:bold;
                    margin-left:8px;
                ">
                    {priority_label}
                </span>
            </div>

            <table cellspacing="0" cellpadding="0" style="
                width:100%;
                border-collapse:collapse;
                font-size:14px;
            ">
                {table_rows}
            </table>
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