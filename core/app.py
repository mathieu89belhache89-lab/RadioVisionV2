import html
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QTextCursor

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
from parser.pursuit_tracker import PursuitTracker
from parser.correction_parser import CorrectionParser


DEFAULT_RUNTIME_SETTINGS = {
    "overlay_enabled": True,
    "overlay_duration": 15,
    "overlay_position": "top_right",
    "capture_microphone": False,
    "strict_analysis": True,
    "pending_delay": 6,
    "merge_window": 8,
    "pursuit_window": 3,
    "whisper_model": "base",
}


PURSUIT_START_CODES = [
    "10-10",
    "10-11",
    "10-12",
    "10-13",
    "10-14",
    "10-15",
]

PURSUIT_VEHICLE_CODES = [
    "10-11",
    "10-12",
]

REPORT_CODES = [
    "CODE OD",
    "CODE DS",
    "CODE DOA",
    "CODE DCD",
    "CODE RDP",
    "CODE S",
]


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
        self.pursuit_tracker = PursuitTracker()
        self.correction_parser = CorrectionParser()

        self.runtime_settings_file = Path("data") / "radiovision_settings.json"
        self.runtime_settings = self.load_runtime_settings()

        self.last_bubbles = {}
        self.duplicate_delay = 10

        self.pending_event = None
        self.pending_event_time = None
        self.pending_merge_window = int(self.runtime_settings["merge_window"])
        self.pending_delay_ms = int(self.runtime_settings["pending_delay"]) * 1000

        self.detail_bubbles = []
        self.bubble_counter = 0
        self.pursuit_bubble_ids = {}
        self.max_detail_bubbles = 80
        self.last_heard_text = ""
        self.recent_heard_texts = []
        self.max_recent_heard_texts = 30

        self.pending_timer = QTimer(self)
        self.pending_timer.setSingleShot(True)
        self.pending_timer.timeout.connect(self.flush_pending_event)

        apply_theme()

        self.window = MainWindow()
        self.overlay = OverlayWindow()
        self.audio_worker = None

        self._connect_signals()
        self.apply_runtime_settings(self.runtime_settings, update_ui=True)
        self.refresh_learning_ui()
        self.update_pursuit_history()

        self.logger.info("RadioVision démarré")

    def clamp_int(self, value, minimum, maximum, default):
        try:
            value = int(value)
        except Exception:
            value = default

        return max(minimum, min(value, maximum))

    def load_runtime_settings(self):
        settings = DEFAULT_RUNTIME_SETTINGS.copy()

        if not self.runtime_settings_file.exists():
            return settings

        try:
            with self.runtime_settings_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return settings

            settings["overlay_enabled"] = bool(
                data.get("overlay_enabled", settings["overlay_enabled"])
            )

            settings["overlay_duration"] = self.clamp_int(
                data.get("overlay_duration"),
                3,
                60,
                settings["overlay_duration"],
            )

            position = data.get("overlay_position", settings["overlay_position"])

            if position in ["top_right", "top_left", "bottom_right", "bottom_left"]:
                settings["overlay_position"] = position

            settings["capture_microphone"] = bool(
                data.get("capture_microphone", settings["capture_microphone"])
            )

            settings["strict_analysis"] = bool(
                data.get("strict_analysis", settings["strict_analysis"])
            )

            settings["pending_delay"] = self.clamp_int(
                data.get("pending_delay"),
                1,
                15,
                settings["pending_delay"],
            )

            settings["merge_window"] = self.clamp_int(
                data.get("merge_window"),
                2,
                20,
                settings["merge_window"],
            )

            settings["pursuit_window"] = self.clamp_int(
                data.get("pursuit_window"),
                1,
                10,
                settings["pursuit_window"],
            )

            model = data.get("whisper_model", settings["whisper_model"])

            if model in ["tiny", "base", "small"]:
                settings["whisper_model"] = model

        except Exception:
            return settings

        return settings

    def save_runtime_settings(self):
        self.runtime_settings_file.parent.mkdir(exist_ok=True)

        with self.runtime_settings_file.open("w", encoding="utf-8") as f:
            json.dump(
                self.runtime_settings,
                f,
                ensure_ascii=False,
                indent=4,
            )

    def apply_runtime_settings(self, settings, update_ui=False):
        self.pending_delay_ms = int(settings.get("pending_delay", 6)) * 1000
        self.pending_merge_window = int(settings.get("merge_window", 8))

        pursuit_window_seconds = int(settings.get("pursuit_window", 3)) * 60
        self.pursuit_tracker.set_active_window(pursuit_window_seconds)

        self.overlay.set_enabled(settings.get("overlay_enabled", True))
        self.overlay.set_display_seconds(settings.get("overlay_duration", 15))
        self.overlay.set_position(settings.get("overlay_position", "top_right"))

        if update_ui:
            self.window.set_settings_values(settings)

    def apply_settings_from_ui(self):
        old_model = self.runtime_settings.get("whisper_model", "base")
        old_capture_microphone = bool(
            self.runtime_settings.get("capture_microphone", False)
        )

        self.runtime_settings = self.window.get_settings_values()
        self.save_runtime_settings()
        self.apply_runtime_settings(self.runtime_settings, update_ui=False)

        new_model = self.runtime_settings.get("whisper_model", "base")
        new_capture_microphone = bool(
            self.runtime_settings.get("capture_microphone", False)
        )

        message = "Paramètres sauvegardés."

        restart_reasons = []

        if new_model != old_model:
            restart_reasons.append("le modèle Whisper")

        if new_capture_microphone != old_capture_microphone:
            restart_reasons.append("la source micro")

        if restart_reasons:
            message = (
                "Paramètres sauvegardés. "
                "Redémarre l’écoute pour appliquer : "
                + ", ".join(restart_reasons)
                + "."
            )

        self.window.setting_status.setText(message)
        self.window.status.showMessage(message, 6000)

    def reset_runtime_settings(self):
        self.runtime_settings = DEFAULT_RUNTIME_SETTINGS.copy()
        self.save_runtime_settings()
        self.apply_runtime_settings(self.runtime_settings, update_ui=True)

        message = "Paramètres réinitialisés."
        self.window.setting_status.setText(message)
        self.window.status.showMessage(message, 6000)

    def _connect_signals(self):
        self.window.start_button.clicked.connect(self.start)
        self.window.stop_button.clicked.connect(self.stop)

        self.window.action_start.triggered.connect(self.start)
        self.window.action_stop.triggered.connect(self.stop)

        self.window.setting_apply_button.clicked.connect(self.apply_settings_from_ui)
        self.window.setting_reset_button.clicked.connect(self.reset_runtime_settings)

        self.window.learning_add_button.clicked.connect(self.add_learning_correction)
        self.window.learning_reload_button.clicked.connect(self.reload_learning_corrections)
        self.window.learning_use_last_button.clicked.connect(self.use_last_call_for_learning)
        self.window.learning_use_selected_recent_button.clicked.connect(self.use_selected_recent_for_learning)
        self.window.learning_test_button.clicked.connect(self.test_learning_correction)
        self.window.learning_update_button.clicked.connect(self.update_selected_learning_correction)
        self.window.learning_delete_button.clicked.connect(self.delete_selected_learning_correction)
        self.window.learning_corrections_table.itemSelectionChanged.connect(
            self.load_selected_correction_into_form
        )
        self.window.learning_recent_list.itemDoubleClicked.connect(
            self.use_selected_recent_for_learning
        )


    def get_learning_options(self):
        location_names = set()

        for item in getattr(self.location_parser, "locations", []):
            name = item.get("name")

            if name:
                location_names.add(str(name))

        for item in getattr(self.location_parser, "aliases", []):
            name = item.get("name")

            if name:
                location_names.add(str(name))

        vehicle_names = set()

        for item in getattr(self.vehicle_parser, "vehicles", []):
            label = item.get("label")

            if label:
                vehicle_names.add(str(label))

        vehicle_names.update([
            "Moto",
            "Véhicule aérien",
            "Véhicule noir",
            "Véhicule blanc",
            "Véhicule gris",
        ])

        code_names = set()

        for code in getattr(self.parser, "codes", {}).keys():
            code_names.add(str(code))

        incident_names = [
            "vehicule immobilise",
            "vehicule accidente",
            "besoin de renfort",
            "coups de feu",
            "suspect arme",
            "arme visible",
            "dernier visuel",
            "plus de visuel",
            "suspect interpelle",
            "vehicule saisie",
            "fuite a pied",
            "poursuite en cours",
            "agent a terre",
        ]

        return {
            "locations": sorted(location_names),
            "vehicles": sorted(vehicle_names),
            "codes": sorted(code_names),
            "incidents": incident_names,
        }

    def learning_section_labels(self):
        return {
            "locations": "Lieu",
            "vehicles": "Véhicule",
            "codes": "Code radio",
            "incidents": "Incident / info",
        }

    def format_corrections_preview(self):
        labels = self.learning_section_labels()
        body = ""

        for section in ["locations", "vehicles", "codes", "incidents"]:
            corrections = self.correction_parser.get_section(section)
            title = labels.get(section, section)

            body += f"""
            <div style="
                color:#ffffff;
                font-weight:bold;
                font-size:14px;
                margin:10px 0 6px 0;
            ">
                {html.escape(title)}
            </div>
            """

            if not corrections:
                body += """
                <div style="color:#747f8d; margin-bottom:8px;">
                    Aucune correction.
                </div>
                """
                continue

            body += """
            <table cellspacing="0" cellpadding="0" style="
                width:100%;
                border-collapse:collapse;
                font-size:13px;
            ">
            """

            for heard, correction in sorted(corrections.items()):
                body += f"""
                <tr>
                    <td style="color:#949ba4; padding:3px 8px; width:45%;">
                        {html.escape(str(heard))}
                    </td>
                    <td style="color:#57f287; padding:3px 8px; width:10%;">
                        →
                    </td>
                    <td style="color:#dbdee1; padding:3px 8px;">
                        {html.escape(str(correction))}
                    </td>
                </tr>
                """

            body += "</table>"

        return f"""
        <html>
            <body style="
                background-color:#1e1f22;
                color:#dbdee1;
                font-family:Segoe UI, Arial;
                font-size:13px;
                margin:0;
                padding:8px;
            ">
                {body}
            </body>
        </html>
        """

    def format_corrections_rows(self):
        labels = self.learning_section_labels()
        rows = []

        for section in ["locations", "vehicles", "codes", "incidents"]:
            corrections = self.correction_parser.get_section(section)

            for heard, correction in sorted(corrections.items()):
                rows.append({
                    "section": section,
                    "section_label": labels.get(section, section),
                    "heard": heard,
                    "correction": correction,
                })

        return rows

    def refresh_learning_ui(self):
        self.window.set_learning_options(self.get_learning_options())
        self.window.set_corrections_preview(self.format_corrections_preview())
        self.window.set_corrections_table(self.format_corrections_rows())
        self.window.set_recent_calls(self.recent_heard_texts)

    def add_learning_correction(self):
        values = self.window.get_learning_values()

        success, message = self.correction_parser.add_correction(
            values.get("section"),
            values.get("heard"),
            values.get("correction"),
        )

        self.window.set_learning_status(message, error=not success)
        self.window.status.showMessage(message, 6000)

        if success:
            self.window.learning_heard_input.clear()
            self.refresh_learning_ui()

    def update_selected_learning_correction(self):
        selected = self.window.get_selected_correction()

        if not selected:
            message = "Sélectionne une correction à modifier."
            self.window.set_learning_status(message, error=True)
            self.window.status.showMessage(message, 4000)
            return

        values = self.window.get_learning_values()

        old_section = selected.get("section")
        old_heard = selected.get("heard")

        # Si le texte entendu ou le type change, on supprime l'ancienne entrée.
        new_section = values.get("section")
        new_heard = values.get("heard")

        if old_section != new_section or old_heard != new_heard:
            self.correction_parser.remove_correction(old_section, old_heard)

        success, message = self.correction_parser.add_correction(
            new_section,
            new_heard,
            values.get("correction"),
        )

        self.window.set_learning_status(message, error=not success)
        self.window.status.showMessage(message, 6000)

        if success:
            self.refresh_learning_ui()

    def delete_selected_learning_correction(self):
        selected = self.window.get_selected_correction()

        if not selected:
            message = "Sélectionne une correction à supprimer."
            self.window.set_learning_status(message, error=True)
            self.window.status.showMessage(message, 4000)
            return

        success, message = self.correction_parser.remove_correction(
            selected.get("section"),
            selected.get("heard"),
        )

        self.window.set_learning_status(message, error=not success)
        self.window.status.showMessage(message, 6000)

        if success:
            self.refresh_learning_ui()

    def test_learning_correction(self):
        values = self.window.get_learning_values()
        heard = values.get("heard", "")
        section = values.get("section")
        correction = values.get("correction", "")

        if not heard:
            message = "Mets d’abord un texte entendu à tester."
            self.window.set_learning_status(message, error=True)
            self.window.status.showMessage(message, 4000)
            return

        old_value = self.correction_parser.find_exact(section, heard)
        replaced = self.correction_parser.replace_in_text(heard)

        if old_value:
            message = f"Correction déjà active : {heard} → {old_value}."
        elif correction:
            message = f"Test : {heard} sera ajouté vers {correction}. Texte corrigé actuel : {replaced}"
        else:
            message = f"Texte corrigé actuel : {replaced}"

        self.window.set_learning_status(message, error=False)
        self.window.status.showMessage(message, 6000)

    def reload_learning_corrections(self):
        self.correction_parser.load()
        self.refresh_learning_ui()

        message = "Corrections rechargées."
        self.window.set_learning_status(message, error=False)
        self.window.status.showMessage(message, 4000)

    def use_last_call_for_learning(self):
        if not self.last_heard_text:
            message = "Aucun call entendu pour le moment."
            self.window.set_learning_status(message, error=True)
            self.window.status.showMessage(message, 4000)
            return

        self.window.set_learning_heard_text(self.last_heard_text)

        message = "Dernier call copié dans le champ entendu."
        self.window.set_learning_status(message, error=False)
        self.window.status.showMessage(message, 4000)

    def use_selected_recent_for_learning(self):
        text = self.window.get_selected_recent_call()

        if not text:
            message = "Sélectionne une ligne dans les derniers calls."
            self.window.set_learning_status(message, error=True)
            self.window.status.showMessage(message, 4000)
            return

        self.window.set_learning_heard_text(text)

        message = "Call sélectionné copié dans le champ entendu."
        self.window.set_learning_status(message, error=False)
        self.window.status.showMessage(message, 4000)

    def load_selected_correction_into_form(self):
        selected = self.window.get_selected_correction()

        if not selected:
            return

        self.window.set_learning_values(
            section=selected.get("section"),
            heard=selected.get("heard"),
            correction=selected.get("correction"),
        )

    def remember_heard_text(self, text):
        text = str(text or "").strip()

        if not text:
            return

        if self.recent_heard_texts and self.recent_heard_texts[0] == text:
            return

        if text in self.recent_heard_texts:
            self.recent_heard_texts.remove(text)

        self.recent_heard_texts.insert(0, text)
        self.recent_heard_texts = self.recent_heard_texts[:self.max_recent_heard_texts]

        self.window.set_recent_calls(self.recent_heard_texts)

    def start(self):
        if self.audio_worker and self.audio_worker.isRunning():
            return

        self.window.state.setText("🟢 Écoute")
        self.window.status.showMessage("Démarrage audio...")

        capture_microphone = bool(
            self.runtime_settings.get("capture_microphone", False)
        )

        if capture_microphone:
            source_label = "son PC / FiveM + micro"
        else:
            source_label = "son PC / FiveM"

        self.window.radio_log.append(
            f"[{datetime.now():%H:%M:%S}] ▶ Démarrage capture audio ({source_label})"
        )

        self.audio_worker = AudioWorker(
            capture_microphone=capture_microphone,
        )

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
    
    def should_prefer_direction_over_location(self, location, direction, direction_meta=None, code=None):
        if not location or not direction:
            return False

        location_name = str(location.get("name", "")).strip()
        direction_name = str(direction or "").strip()

        if not location_name or not direction_name:
            return False

        location_clean = self.clean_text_simple(location_name)
        direction_clean = self.clean_text_simple(direction_name)

        if location_clean == direction_clean:
            return False

        if direction_clean and direction_clean in location_clean:
            return True

        location_score = int(location.get("score", 100) or 100)
        direction_score = 100

        if direction_meta:
            direction_score = int(direction_meta.get("score", 100) or 100)

        noisy_specific_locations = [
            "zone rouge",
            "casse",
            "magasin",
            "vetement",
            "vêtement",
            "parking",
            "garage",
        ]

        if any(word in location_clean for word in noisy_specific_locations):
            return True

        pursuit_like_codes = set(PURSUIT_START_CODES + ["10-16", "10-17", "10-19"])

        if code in pursuit_like_codes and direction_score >= 78:
            return True

        if direction_score >= 92 and location_score < 92:
            return True

        return False

    def normalize_event_location(self, location, direction, direction_meta=None, code=None):
        if self.should_prefer_direction_over_location(
            location=location,
            direction=direction,
            direction_meta=direction_meta,
            code=code,
        ):
            return self.location_parser.find_by_name(
                direction,
                score=direction_meta.get("score", 100) if direction_meta else 100,
                raw=direction_meta.get("raw") if direction_meta else direction,
            )

        return location

    def is_raw_code_lookup_text(self, text, code):
        if not code:
            return False

        text_clean = self.parser.clean(text)

        if len(text_clean.split()) > 5:
            return False

        code_clean = self.parser.clean(code)

        accepted = {
            code_clean,
            f"code {code_clean}",
        }

        for item in self.parser.aliases:
            if item.get("code") != code:
                continue

            alias_clean = item.get("alias_clean")

            accepted.add(alias_clean)
            accepted.add(f"code {alias_clean}")

        return text_clean in accepted

    def parse_event(self, text):
        parse_text = self.correction_parser.replace_in_text(text)

        code, signification = self.parser.parse(parse_text)

        if code and self.is_raw_code_lookup_text(parse_text, code):
            return {
                "text": text,
                "raw_text": text,
                "parse_text": parse_text,
                "code": code,
                "signification": signification,
                "location": None,
                "unit": None,
                "direction": None,
                "direction_meta": None,
                "vehicle": None,
                "incidents": [],
                "is_update": False,
                "is_unassigned": False,
                "is_code_lookup": True,
                "pursuit_id": None,
                "pursuit_label": None,
                "pursuit_status": None,
                "pursuit_status_label": None,
                "tracker_action": None,
                "association_score": 0,
            }

        location = self.location_parser.find(parse_text)
        direction_meta = self.direction_parser.find_detailed(
            parse_text,
            self.location_parser,
        )

        direction = None

        if direction_meta:
            direction = direction_meta.get("name")

            if not location:
                location = self.location_parser.find_by_name(
                    direction,
                    score=direction_meta.get("score", 100),
                    raw=direction_meta.get("raw"),
                )

        if not direction and location and self.text_has_direction_hint(parse_text):
            direction = location.get("name")
            direction_meta = {
                "name": direction,
                "raw": location.get("raw") or direction,
                "score": location.get("score", 100),
                "source": "location",
                "probable": location.get("score", 100) < 92,
            }

        location = self.normalize_event_location(
            location=location,
            direction=direction,
            direction_meta=direction_meta,
            code=code,
        )

        vehicle = self.vehicle_parser.find(parse_text)

        # Le code radio 208 ne doit pas devenir Peugeot 208 sauf contexte véhicule clair.
        if code == "208" and vehicle:
            text_clean = self.clean_text_simple(parse_text)
            vehicle_context = any([
                "vehicule" in text_clean,
                "voiture" in text_clean,
                "auto" in text_clean,
                "peugeot" in text_clean,
            ])

            if not vehicle_context:
                vehicle = None

        return {
            "text": text,
            "raw_text": text,
            "parse_text": parse_text,
            "code": code,
            "signification": signification,
            "location": location,
            "unit": self.unit_parser.find(parse_text),
            "direction": direction,
            "direction_meta": direction_meta,
            "vehicle": vehicle,
            "incidents": self.incident_parser.find(parse_text),
            "is_update": False,
            "is_unassigned": False,
            "is_code_lookup": False,
            "pursuit_id": None,
            "pursuit_label": None,
            "pursuit_status": None,
            "pursuit_status_label": None,
            "tracker_action": None,
            "association_score": 0,
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

    def is_code_only_event(self, event):
        code = event.get("code")

        if not code:
            return False

        if any([
            event.get("unit"),
            event.get("location"),
            event.get("direction"),
            event.get("vehicle"),
            event.get("incidents"),
        ]):
            return False

        # Sécurité V8.1 :
        # un code radio seul doit vraiment être une phrase courte du type "10-99" ou "Code OD".
        # Si Whisper entend "central code od agent at", ce n'est pas un simple lookup :
        # on laisse l'évènement en attente pour pouvoir fusionner le morceau suivant
        # "mission row besoin de renfort".
        lookup_text = event.get("parse_text") or event.get("text") or ""

        return self.is_raw_code_lookup_text(lookup_text, code)

    def build_signature(
        self,
        code=None,
        unit=None,
        location=None,
        direction=None,
        direction_meta=None,
        vehicle=None,
        incidents=None,
        pursuit_id=None,
        is_unassigned=False,
        is_code_lookup=False,
    ):
        incidents = incidents or []

        location_name = ""

        if location:
            location_name = location.get("name", "")

        vehicle_key = ""

        if vehicle:
            vehicle_key = vehicle.get("key") or vehicle.get("vehicle", "")

        signature_parts = [
            str(pursuit_id or ""),
            str(code or ""),
            str(unit or ""),
            str(location_name or ""),
            str(direction or ""),
            str(vehicle_key or ""),
            "|".join(incidents),
            str(is_unassigned),
            str(is_code_lookup),
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
        direction_meta=None,
        vehicle=None,
        is_code_lookup=False,
    ):
        if is_code_lookup:
            return []

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

        if code in PURSUIT_VEHICLE_CODES and not vehicle:
            missing.append("véhicule")

        return missing

    def get_confidence(
        self,
        code=None,
        unit=None,
        location=None,
        direction=None,
        direction_meta=None,
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

        if code in PURSUIT_VEHICLE_CODES:
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
            direction_meta=event.get("direction_meta"),
            vehicle=event.get("vehicle"),
            is_code_lookup=event.get("is_code_lookup", False),
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

        previous_text = old.get("accumulated_text") or old.get("text", "")
        merged["accumulated_text"] = f"{previous_text} {new.get('text', '')}".strip()
        merged["text"] = new.get("text") or old.get("text", "")

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
            "direction_meta",
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

    def handle_event(self, event):
        if not self.event_has_content(event):
            return

        if self.is_code_only_event(event):
            event["is_code_lookup"] = True

            if self.pending_event:
                self.flush_pending_event()

            self.display_event(event)
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

            self.process_and_display_event(merged)
            return

        if (
            self.pursuit_tracker.has_active_pursuits()
            and self.pursuit_tracker.is_followup_like(event)
        ):
            if self.pending_event:
                self.flush_pending_event()

            self.process_and_display_event(event)
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

        self.process_and_display_event(event)

    def flush_pending_event(self):
        if not self.pending_event:
            return

        event = self.pending_event

        self.pending_event = None
        self.pending_event_time = None

        self.process_and_display_event(event)

    def process_and_display_event(self, event):
        tracked_event = self.pursuit_tracker.process_event(event)
        self.display_event(tracked_event)
        self.update_pursuit_history()

    def display_event(self, event):
        self.append_radio_bubble(
            text=event.get("text"),
            code=event.get("code"),
            signification=event.get("signification"),
            unit=event.get("unit"),
            location=event.get("location"),
            direction=event.get("direction"),
            direction_meta=event.get("direction_meta"),
            vehicle=event.get("vehicle"),
            incidents=event.get("incidents"),
            is_update=event.get("is_update", False),
            is_unassigned=event.get("is_unassigned", False),
            is_code_lookup=event.get("is_code_lookup", False),
            pursuit_id=event.get("pursuit_id"),
            pursuit_label=event.get("pursuit_label"),
            pursuit_status_label=event.get("pursuit_status_label"),
            association_score=event.get("association_score", 0),
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
        direction_meta=None,
        vehicle=None,
        incidents=None,
        is_update=False,
        is_unassigned=False,
        is_code_lookup=False,
        pursuit_id=None,
    ):
        incidents = incidents or []

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        file = logs_dir / f"radio_{datetime.now():%Y-%m-%d}.txt"

        lines = []
        lines.append("=" * 60)
        lines.append(f"Heure : {datetime.now():%H:%M:%S}")

        if pursuit_id:
            lines.append(f"Poursuite : #{pursuit_id}")

        if is_update:
            lines.append("Type : Mise à jour poursuite")

        if is_unassigned:
            lines.append("Type : Info non attribuée")

        if is_code_lookup:
            lines.append("Type : Code radio seul")

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

    def render_detail_bubbles(self):
        body = ""

        for item in self.detail_bubbles:
            body += item["html"]

        final_html = f"""
        <html>
            <body style="
                background-color:#1e1f22;
                color:#dbdee1;
                font-family:Segoe UI, Arial;
                font-size:13px;
                margin:0;
                padding:0;
            ">
                {body}
            </body>
        </html>
        """

        self.window.details.setHtml(final_html)
        self.window.details.moveCursor(QTextCursor.MoveOperation.End)

        scroll = self.window.details.verticalScrollBar()
        scroll.setValue(scroll.maximum())

    def add_or_update_detail_bubble(
        self,
        bubble_html,
        is_update=False,
        pursuit_id=None,
    ):
        updated = False

        if is_update and pursuit_id in self.pursuit_bubble_ids:
            bubble_id_to_update = self.pursuit_bubble_ids[pursuit_id]

            for index, item in enumerate(self.detail_bubbles):
                if item["id"] == bubble_id_to_update:
                    item["html"] = bubble_html

                    moved_item = self.detail_bubbles.pop(index)
                    self.detail_bubbles.append(moved_item)

                    updated = True
                    break

        if not updated:
            self.bubble_counter += 1

            bubble_id = self.bubble_counter

            self.detail_bubbles.append({
                "id": bubble_id,
                "html": bubble_html,
            })

            if pursuit_id:
                self.pursuit_bubble_ids[pursuit_id] = bubble_id

        while len(self.detail_bubbles) > self.max_detail_bubbles:
            removed = self.detail_bubbles.pop(0)

            for pursuit_key, bubble_id in list(self.pursuit_bubble_ids.items()):
                if bubble_id == removed["id"]:
                    del self.pursuit_bubble_ids[pursuit_key]

        self.render_detail_bubbles()

    def append_radio_bubble(
        self,
        text,
        code=None,
        signification=None,
        unit=None,
        location=None,
        direction=None,
        direction_meta=None,
        vehicle=None,
        incidents=None,
        is_update=False,
        is_unassigned=False,
        is_code_lookup=False,
        pursuit_id=None,
        pursuit_label=None,
        pursuit_status_label=None,
        association_score=0,
    ):
        incidents = incidents or []

        missing_infos = self.get_missing_infos(
            code=code,
            unit=unit,
            location=location,
            direction=direction,
            vehicle=vehicle,
            is_code_lookup=is_code_lookup,
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
            pursuit_id=pursuit_id,
            is_unassigned=is_unassigned,
            is_code_lookup=is_code_lookup,
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

        if is_code_lookup:
            priority_color = "#5865f2"
            priority_label = "CODE RADIO"

        elif is_unassigned:
            priority_color = "#747f8d"
            priority_label = "NON ATTRIBUÉ"

        elif code in ["10-99", "CODE 3", "460", "10-31", "CODE OD"]:
            priority_color = "#ed4245"
            priority_label = "URGENT"

        elif pursuit_id:
            priority_color = "#faa61a"
            priority_label = f"POURSUITE #{pursuit_id}"

        elif code in PURSUIT_START_CODES:
            priority_color = "#faa61a"
            priority_label = "POURSUITE"

        if is_update and pursuit_id:
            priority_color = "#57f287"
            priority_label = f"POURSUITE #{pursuit_id}"

        elif missing_infos and priority_label not in [
            "URGENT",
            "NON ATTRIBUÉ",
            "CODE RADIO",
        ]:
            priority_color = "#faa61a"
            priority_label = "INCOMPLET"

        rows = []

        if is_code_lookup:
            rows.append(("📘", "Type", "Signification code radio"))

        if pursuit_label:
            rows.append(("🚓", "Dossier", html.escape(str(pursuit_label))))

        if pursuit_status_label:
            rows.append(("📌", "Statut", html.escape(str(pursuit_status_label))))

        if text and not is_code_lookup:
            rows.append(("🎙️", "Call entendu", html.escape(str(text))))

        if is_update:
            rows.append(("🔄", "Type", "Mise à jour"))

        if is_unassigned:
            rows.append(("⚪", "Type", "Info non attribuée"))

        if association_score:
            rows.append((
                "🧠",
                "Association",
                html.escape(f"{association_score} points")
            ))

        if unit:
            rows.append(("👮", "Unité", html.escape(str(unit))))

        if code:
            rows.append(("📟", "Code", html.escape(str(code))))

        if signification:
            rows.append(("📖", "Signification", html.escape(str(signification))))

        if not is_code_lookup:
            rows.append((
                confidence_emoji,
                "Confiance",
                html.escape(f"{confidence_label} ({confidence_percent}%)")
            ))

        if location:
            rows.append(("📍", "Dernier lieu", html.escape(str(location["name"]))))

        if direction:
            direction_label = "Direction"
            direction_value = str(direction)

            if direction_meta:
                raw_direction = direction_meta.get("raw")
                score_direction = int(direction_meta.get("score", 100))
                is_probable = bool(direction_meta.get("probable", False))

                if is_probable:
                    direction_label = "Direction probable"
                    direction_value = f"{direction} ({score_direction}%)"

                    if raw_direction and self.clean_text_simple(raw_direction) != self.clean_text_simple(direction):
                        direction_value += f" — entendu : {raw_direction}"

            rows.append(("➡️", direction_label, html.escape(str(direction_value))))

        if vehicle:
            label = vehicle["vehicle"]

            if vehicle["color"]:
                label += f" {vehicle['color']}"

            rows.append(("🚗", "Véhicule", html.escape(str(label))))

        for incident in incidents:
            rows.append(("", "Info", html.escape(str(incident))))

        if "véhicule" in missing_infos and code in PURSUIT_VEHICLE_CODES:
            rows.append(("🚗", "Véhicule", "non identifié"))

        if missing_infos and not is_unassigned:
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

        self.add_or_update_detail_bubble(
            bubble_html=bubble,
            is_update=is_update,
            pursuit_id=pursuit_id,
        )

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
            is_update=is_update,
            is_unassigned=is_unassigned,
            is_code_lookup=is_code_lookup,
            pursuit_id=pursuit_id,
        )

    def update_pursuit_history(self):
        pursuits = self.pursuit_tracker.get_history()

        if not pursuits:
            self.window.pursuit_history.setHtml("""
            <html>
                <body style="
                    background-color:#1e1f22;
                    color:#dbdee1;
                    font-family:Segoe UI, Arial;
                    font-size:13px;
                    margin:0;
                    padding:0;
                ">
                    <div style="color:#949ba4; padding:8px;">
                        Aucune poursuite pour le moment.
                    </div>
                </body>
            </html>
            """)
            return

        body = ""

        for pursuit in pursuits:
            status = pursuit.get("status")
            status_label = pursuit.get("status_label", "-")

            color = "#faa61a"

            if status == "ended":
                color = "#57f287"
            elif status == "expired":
                color = "#747f8d"

            vehicle = pursuit.get("vehicle_label") or "-"
            location = pursuit.get("location_name") or "-"
            direction = pursuit.get("direction") or "-"
            unit = pursuit.get("unit") or "-"
            code = pursuit.get("code") or "-"

            incidents = pursuit.get("incidents") or []

            incidents_html = ""

            for incident in incidents:
                incidents_html += f"""
                <div style="color:#dbdee1; margin:2px 0;">
                    {html.escape(str(incident))}
                </div>
                """

            if not incidents_html:
                incidents_html = """
                <div style="color:#747f8d;">Aucune info</div>
                """

            body += f"""
            <div style="
                background-color:#2b2d31;
                border-left:5px solid {color};
                padding:10px;
                margin:8px 4px;
            ">
                <div style="
                    color:#ffffff;
                    font-weight:bold;
                    font-size:14px;
                    margin-bottom:6px;
                ">
                    🚓 Poursuite #{pursuit.get("id")}
                    <span style="
                        color:{color};
                        font-size:11px;
                        margin-left:8px;
                    ">
                        {html.escape(str(status_label))}
                    </span>
                </div>

                <table cellspacing="0" cellpadding="0" style="
                    width:100%;
                    border-collapse:collapse;
                    font-size:13px;
                ">
                    <tr>
                        <td style="color:#949ba4; width:120px;">Début</td>
                        <td>{html.escape(str(pursuit.get("started_at", "-")))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Dernière info</td>
                        <td>{html.escape(str(pursuit.get("last_update", "-")))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Unité</td>
                        <td>{html.escape(str(unit))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Code</td>
                        <td>{html.escape(str(code))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Véhicule</td>
                        <td>{html.escape(str(vehicle))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Dernier lieu</td>
                        <td>{html.escape(str(location))}</td>
                    </tr>
                    <tr>
                        <td style="color:#949ba4;">Direction</td>
                        <td>{html.escape(str(direction))}</td>
                    </tr>
                </table>

                <div style="
                    color:#ffffff;
                    font-weight:bold;
                    margin-top:8px;
                    margin-bottom:4px;
                ">
                    Infos
                </div>

                {incidents_html}
            </div>
            """

        final_html = f"""
        <html>
            <body style="
                background-color:#1e1f22;
                color:#dbdee1;
                font-family:Segoe UI, Arial;
                font-size:13px;
                margin:0;
                padding:0;
            ">
                {body}
            </body>
        </html>
        """

        self.window.pursuit_history.setHtml(final_html)
        self.window.pursuit_history.moveCursor(QTextCursor.MoveOperation.End)

    def on_text(self, text):
        self.last_heard_text = str(text or "").strip()
        self.remember_heard_text(self.last_heard_text)

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