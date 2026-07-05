import html
import time
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer

from core.logger import Logger
from core.settings import Settings
from ui.main_window import MainWindow
from ui.theme import apply_theme
from ui.overlay_window import OverlayWindow
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

        self.pending_event = None
        self.pending_event_time = None
        self.pending_merge_window = 8
        self.pending_delay_ms = 6000

        self.active_pursuit = None
        self.active_pursuit_time = None
        self.active_pursuit_window = 180

        self.pending_timer = QTimer(self)
        self.pending_timer.setSingleShot(True)
        self.pending_timer.timeout.connect(self.flush_pending_event)

        apply_theme()

        self.window = MainWindow()
        self.overlay = OverlayWindow()
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
        if self.pending_event:
            self.flush_pending_event()

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

    def clean_text_simple(self, text):
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = text.replace("'", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def text_has_direction_hint(self, text):
        text_clean = self.clean_text_simple(text)

        hints = [
            "direction",
            "vers",
            "visuel",
            "vue",
            "se dirige",
            "part",
            "va",
        ]

        for hint in hints:
            if hint in text_clean:
                return True

        return False

    def parse_event(self, text):
        code, signification = self.parser.parse(text)

        location = self.location_parser.find(text)
        direction = self.direction_parser.find(text)

        if not direction and location and self.text_has_direction_hint(text):
            direction = location.get("name")

        return {
            "text": text,
            "code": code,
            "signification": signification,
            "location": location,
            "unit": self.unit_parser.find(text),
            "direction": direction,
            "vehicle": self.vehicle_parser.find(text),
            "incidents": self.incident_parser.find(text),
            "is_update": False,
        }

    def event_has_content(self, event):
        return any([
            event.get("code"),
            event.get("unit"),
            event.get("location"),
            event.get("direction"),
            event.get("vehicle"),
            event.get("incidents"),
        ])

    def is_pursuit_event(self, event):
        code = event.get("code")
        incidents = event.get("incidents") or []

        if code in ["10-10", "10-11"]:
            return True

        pursuit_words = [
            "Poursuite",
            "Visuel",
            "Fuite",
            "Immobilisé",
            "Accident",
            "Interpellation",
            "Renfort",
            "Refus",
            "Coups de feu",
        ]

        for incident in incidents:
            for word in pursuit_words:
                if word.lower() in incident.lower():
                    return True

        if event.get("vehicle") and (
            event.get("location") or event.get("direction")
        ):
            return True

        return False

    def is_active_pursuit_valid(self):
        if not self.active_pursuit:
            return False

        if self.active_pursuit_time is None:
            return False

        if time.time() - self.active_pursuit_time > self.active_pursuit_window:
            self.active_pursuit = None
            self.active_pursuit_time = None
            return False

        return True

    def is_followup_for_active_pursuit(self, event):
        if not self.is_active_pursuit_valid():
            return False

        if event.get("code") in ["10-10", "10-11"]:
            return False

        has_followup_info = any([
            event.get("location"),
            event.get("direction"),
            event.get("incidents"),
        ])

        if not has_followup_info:
            return False

        if event.get("unit") and self.active_pursuit.get("unit"):
            if event.get("unit") != self.active_pursuit.get("unit"):
                return False

        return True

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

        if code in ["10-10", "10-11"] and not vehicle:
            missing.append("véhicule")

        return missing

    def get_confidence(
        self,
        code=None,
        unit=None,
        location=None,
        direction=None,
        vehicle=None,
        incidents=None,
    ):
        incidents = incidents or []

        score = 0
        max_score = 0

        max_score += 25
        if unit:
            score += 25

        max_score += 25
        if code:
            score += 25

        max_score += 25
        if location or direction:
            score += 25

        if code in ["10-10", "10-11"]:
            max_score += 25
            if vehicle:
                score += 25
        else:
            max_score += 10
            if vehicle:
                score += 10

        if incidents:
            max_score += 5
            score += 5

        percent = int((score / max_score) * 100)
        percent = min(percent, 100)

        if percent >= 85:
            return "Forte", percent, "✅"

        if percent >= 60:
            return "Moyenne", percent, "⚠️"

        return "Faible", percent, "❌"

    def event_missing_infos(self, event):
        return self.get_missing_infos(
            code=event.get("code"),
            unit=event.get("unit"),
            location=event.get("location"),
            direction=event.get("direction"),
            vehicle=event.get("vehicle"),
        )

    def should_merge_with_pending(self, new_event):
        if not self.pending_event:
            return False

        if self.pending_event_time is None:
            return False

        if time.time() - self.pending_event_time > self.pending_merge_window:
            return False

        missing = self.event_missing_infos(self.pending_event)

        if not missing:
            return False

        old = self.pending_event

        fills_missing = any([
            not old.get("unit") and new_event.get("unit"),
            not old.get("code") and new_event.get("code"),
            not old.get("location") and new_event.get("location"),
            not old.get("direction") and new_event.get("direction"),
            not old.get("vehicle") and new_event.get("vehicle"),
            not old.get("incidents") and new_event.get("incidents"),
        ])

        return fills_missing

    def merge_events(self, old, new, update_existing=False):
        merged = old.copy()

        merged["text"] = f"{old.get('text', '')} {new.get('text', '')}".strip()

        fill_only_keys = [
            "code",
            "signification",
            "unit",
            "vehicle",
        ]

        for key in fill_only_keys:
            if not merged.get(key) and new.get(key):
                merged[key] = new.get(key)

        update_keys = [
            "location",
            "direction",
        ]

        for key in update_keys:
            if update_existing:
                if new.get(key):
                    merged[key] = new.get(key)
            else:
                if not merged.get(key) and new.get(key):
                    merged[key] = new.get(key)

        incidents = []

        for item in old.get("incidents", []):
            if item not in incidents:
                incidents.append(item)

        for item in new.get("incidents", []):
            if item not in incidents:
                incidents.append(item)

        merged["incidents"] = incidents

        return merged

    def remember_active_pursuit(self, event):
        if self.is_pursuit_event(event):
            self.active_pursuit = event.copy()
            self.active_pursuit_time = time.time()

    def handle_event(self, event):
        if not self.event_has_content(event):
            return

        if self.should_merge_with_pending(event):
            merged = self.merge_events(
                self.pending_event,
                event,
                update_existing=True,
            )

            self.pending_timer.stop()
            self.pending_event = None
            self.pending_event_time = None

            self.display_event(merged)
            self.remember_active_pursuit(merged)
            return

        if self.is_followup_for_active_pursuit(event):
            if self.pending_event:
                self.flush_pending_event()

            merged = self.merge_events(
                self.active_pursuit,
                event,
                update_existing=True,
            )

            merged["is_update"] = True

            self.display_event(merged)
            self.remember_active_pursuit(merged)
            return

        missing = self.event_missing_infos(event)

        if missing:
            if self.pending_event:
                self.flush_pending_event()

            self.pending_event = event
            self.pending_event_time = time.time()
            self.pending_timer.start(self.pending_delay_ms)
            return

        if self.pending_event:
            self.flush_pending_event()

        self.display_event(event)
        self.remember_active_pursuit(event)

    def flush_pending_event(self):
        if not self.pending_event:
            return

        event = self.pending_event

        self.pending_event = None
        self.pending_event_time = None

        self.display_event(event)
        self.remember_active_pursuit(event)

    def display_event(self, event):
        self.append_radio_bubble(
            text=event.get("text"),
            code=event.get("code"),
            signification=event.get("signification"),
            unit=event.get("unit"),
            location=event.get("location"),
            direction=event.get("direction"),
            vehicle=event.get("vehicle"),
            incidents=event.get("incidents"),
            is_update=event.get("is_update", False),
        )

        if event.get("code"):
            self.window.code.setText(f"📟 Code : {event.get('code')}")
            self.window.signification.setText(
                f"📖 Signification : {event.get('signification')}"
            )

    def save_radio_event(
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

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        file = logs_dir / f"radio_{datetime.now():%Y-%m-%d}.txt"

        lines = []
        lines.append("=" * 60)
        lines.append(f"Heure : {datetime.now():%H:%M:%S}")
        lines.append(f"Phrase : {text}")

        if unit:
            lines.append(f"Unité : {unit}")

        if code:
            lines.append(f"Code : {code}")

        if signification:
            lines.append(f"Motif : {signification}")

        if location:
            lines.append(f"Lieu : {location['name']}")

        if direction:
            lines.append(f"Direction : {direction}")

        if vehicle:
            label = vehicle["vehicle"]

            if vehicle["color"]:
                label += f" {vehicle['color']}"

            lines.append(f"Véhicule : {label}")

        for incident in incidents:
            lines.append(f"Info : {incident}")

        lines.append("")

        with file.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines))

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
        is_update=False,
    ):
        incidents = incidents or []

        missing_infos = self.get_missing_infos(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
        )

        confidence_label, confidence_percent, confidence_emoji = self.get_confidence(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            incidents=incidents,
        )

        signature = self.build_signature(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            incidents=incidents,
        )

        if is_update:
            signature = f"update / {signature} / {int(time.time())}"

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

        if is_update:
            priority_color = "#57f287"
            priority_label = "MISE À JOUR"

        elif missing_infos and priority_label != "URGENT":
            priority_color = "#faa61a"
            priority_label = "INCOMPLET"

        rows = []

        if is_update:
            rows.append(("🔄", "Type", "Mise à jour poursuite active"))

        if unit:
            rows.append(("👮", "Unité", html.escape(str(unit))))

        if code:
            rows.append(("📟", "Code", html.escape(str(code))))

        if signification:
            rows.append(("📖", "Motif", html.escape(str(signification))))

        rows.append((
            confidence_emoji,
            "Confiance",
            html.escape(f"{confidence_label} ({confidence_percent}%)")
        ))

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

        self.overlay.show_radio_event(
            priority_label=priority_label,
            priority_color=priority_color,
            rows=rows,
        )

        self.save_radio_event(
            text=text,
            code=code,
            signification=signification,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            incidents=incidents,
        )

    def on_text(self, text):
        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )

        event = self.parse_event(text)
        self.handle_event(event)

    def on_status(self, text):
        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] {text}"
        )
        self.window.status.showMessage(text)

    def on_volume(self, value):
        self.window.volume.setValue(value)

    def show(self):
        self.window.show()