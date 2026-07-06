import time
from datetime import datetime

from parser.radio_code_classifier import CASE_CODE_CONFIGS, get_case_config, is_case_code, is_pursuit_start_code


class InterventionTracker:
    """Crée des dossiers pour les appels qui ne sont pas des poursuites.

    Exemple : 208, 207, 187, 459, 460, 461, CODE OD.
    Le tracker reste volontairement séparé du PursuitTracker pour éviter
    qu'un appel 208 soit affiché en "Info non attribuée" lorsqu'une poursuite
    est déjà active.
    """

    INTERVENTION_CODES = CASE_CODE_CONFIGS


    PURSUIT_START_CODES = {
        "10-10",
        "10-11",
        "10-12",
        "10-13",
        "10-14",
        "10-15",
    }

    def __init__(self):
        self.cases = []
        self.next_id = 1
        self.active_window = 420
        self.association_threshold = 45

    def set_active_window(self, seconds):
        try:
            seconds = int(seconds)
        except Exception:
            seconds = 420

        self.active_window = max(120, min(seconds, 1800))

    def now_time(self):
        return time.time()

    def now_label(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_location_name(self, event):
        location = event.get("location")

        if location:
            return location.get("name")

        if event.get("direction"):
            return event.get("direction")

        return None

    def get_vehicle_key(self, event):
        vehicle = event.get("vehicle")

        if vehicle:
            return vehicle.get("key") or vehicle.get("vehicle")

        return None

    def get_vehicle_label(self, event):
        vehicle = event.get("vehicle")

        if not vehicle:
            return None

        label = vehicle.get("vehicle", "")

        if vehicle.get("color"):
            label += f" {vehicle.get('color')}"

        return label.strip()

    def is_end_event(self, event):
        incidents = event.get("incidents") or []
        text = str(event.get("parse_text") or event.get("text") or "").lower()

        end_words = [
            "interpelle",
            "interpellation",
            "menotte",
            "termine",
            "terminee",
            "scene securisee",
            "zone securisee",
            "otage libere",
            "liberation otage",
            "suspect neutralise",
        ]

        for incident in incidents:
            incident_lower = str(incident).lower()

            if "interpellation" in incident_lower:
                return True

        return any(word in text for word in end_words)

    def is_intervention_event(self, event):
        code = event.get("code")

        if is_pursuit_start_code(code):
            return False

        return is_case_code(code)

    def is_followup_like(self, event):
        if event.get("code") in self.PURSUIT_START_CODES:
            return False

        return any([
            event.get("unit"),
            event.get("location"),
            event.get("direction"),
            event.get("vehicle"),
            event.get("incidents"),
        ])

    def get_code_config(self, event):
        code = event.get("code")
        config = get_case_config(code)

        if config:
            return config

        return {
            "kind": "intervention",
            "type_label": event.get("signification") or "Intervention",
            "priority": "medium",
        }

    def score_case(self, case, event):
        score = 0

        event_unit = event.get("unit")
        case_unit = case.get("unit")

        if event_unit and case_unit:
            if str(event_unit).lower() == str(case_unit).lower():
                score += 70
            else:
                score -= 70

        event_code = event.get("code")
        case_code = case.get("code")

        if event_code and case_code:
            if event_code == case_code:
                score += 35
            else:
                score -= 20

        event_location = self.get_location_name(event)
        case_location = case.get("location_name")

        if event_location and case_location:
            if str(event_location).lower() == str(case_location).lower():
                score += 30
            else:
                score += 5

        event_vehicle = self.get_vehicle_key(event)
        case_vehicle = case.get("vehicle_key")

        if event_vehicle and case_vehicle:
            if str(event_vehicle).lower() == str(case_vehicle).lower():
                score += 30
            else:
                score -= 30

        seconds_since_update = self.now_time() - case.get("last_update_ts", 0)

        if seconds_since_update <= 45:
            score += 15
        elif seconds_since_update <= 150:
            score += 8
        elif seconds_since_update <= self.active_window:
            score += 3

        return score

    def get_active_cases(self):
        active = []
        now = self.now_time()

        for case in self.cases:
            if case.get("status") != "active":
                continue

            last_update = case.get("last_update_ts", 0)

            if now - last_update > self.active_window:
                case["status"] = "expired"
                case["status_label"] = "Expirée"
                continue

            active.append(case)

        return active

    def find_best_case(self, event):
        best_case = None
        best_score = -999

        for case in self.get_active_cases():
            score = self.score_case(case, event)

            if score > best_score:
                best_score = score
                best_case = case

        if best_case and best_score >= self.association_threshold:
            return best_case, best_score

        return None, best_score

    def create_case(self, event):
        case_id = self.next_id
        self.next_id += 1

        config = self.get_code_config(event)
        now = self.now_time()
        now_label = self.now_label()
        text = event.get("text", "")

        case = {
            "id": case_id,
            "kind": config.get("kind", "intervention"),
            "priority": config.get("priority", "medium"),
            "type_label": config.get("type_label") or event.get("signification") or "Intervention",
            "status": "active",
            "status_label": "Active",
            "started_at": now_label,
            "last_update": now_label,
            "started_ts": now,
            "last_update_ts": now,
            "unit": event.get("unit"),
            "code": event.get("code"),
            "signification": event.get("signification"),
            "location": event.get("location"),
            "location_name": self.get_location_name(event),
            "direction": event.get("direction"),
            "vehicle": event.get("vehicle"),
            "vehicle_key": self.get_vehicle_key(event),
            "vehicle_label": self.get_vehicle_label(event),
            "incidents": list(event.get("incidents") or []),
            "texts": [text] if text else [],
            "latest_text": text,
        }

        if self.is_end_event(event):
            case["status"] = "ended"
            case["status_label"] = "Terminée"

        self.cases.append(case)

        tracked_event = self.case_to_event(case)
        tracked_event["case_action"] = "created"
        tracked_event["is_update"] = False
        tracked_event["association_score"] = 100

        return tracked_event

    def update_case(self, case, event):
        now = self.now_time()
        now_label = self.now_label()

        case["last_update"] = now_label
        case["last_update_ts"] = now

        if event.get("unit") and not case.get("unit"):
            case["unit"] = event.get("unit")

        if event.get("code") and not case.get("code"):
            case["code"] = event.get("code")

        if event.get("signification") and not case.get("signification"):
            case["signification"] = event.get("signification")

        if event.get("location"):
            case["location"] = event.get("location")
            case["location_name"] = self.get_location_name(event)

        if event.get("direction"):
            case["direction"] = event.get("direction")

        if event.get("vehicle") and not case.get("vehicle"):
            case["vehicle"] = event.get("vehicle")
            case["vehicle_key"] = self.get_vehicle_key(event)
            case["vehicle_label"] = self.get_vehicle_label(event)

        for incident in event.get("incidents") or []:
            if incident not in case["incidents"]:
                case["incidents"].append(incident)

        if event.get("text"):
            case["texts"].append(event.get("text"))
            case["latest_text"] = event.get("text")

        if self.is_end_event(event):
            case["status"] = "ended"
            case["status_label"] = "Terminée"

        tracked_event = self.case_to_event(case)
        tracked_event["case_action"] = "updated"
        tracked_event["is_update"] = True

        return tracked_event

    def case_to_event(self, case):
        label_prefix = "Urgence" if case.get("kind") == "urgence" else "Intervention"

        return {
            "text": case.get("latest_text") or " ".join(case.get("texts", [])),
            "code": case.get("code"),
            "signification": case.get("signification"),
            "location": case.get("location"),
            "unit": case.get("unit"),
            "direction": case.get("direction"),
            "vehicle": case.get("vehicle"),
            "incidents": list(case.get("incidents") or []),
            "pursuit_id": None,
            "pursuit_label": None,
            "pursuit_status": None,
            "pursuit_status_label": None,
            "case_id": case.get("id"),
            "case_label": f"{label_prefix} #{case.get('id')}",
            "case_kind": case.get("kind"),
            "case_priority": case.get("priority"),
            "case_type_label": case.get("type_label"),
            "case_status": case.get("status"),
            "case_status_label": case.get("status_label"),
            "tracker_action": "case_snapshot",
            "is_update": False,
            "is_unassigned": False,
            "is_code_lookup": False,
        }

    def process_event(self, event):
        if event.get("is_code_lookup"):
            return None

        if not self.is_intervention_event(event):
            if not self.get_active_cases():
                return None

            if not self.is_followup_like(event):
                return None

            best_case, score = self.find_best_case(event)

            if best_case:
                tracked_event = self.update_case(best_case, event)
                tracked_event["association_score"] = score
                return tracked_event

            return None

        best_case, score = self.find_best_case(event)

        if best_case:
            tracked_event = self.update_case(best_case, event)
            tracked_event["association_score"] = score
            return tracked_event

        return self.create_case(event)

    def get_history(self):
        self.get_active_cases()

        return sorted(
            self.cases,
            key=lambda case: case.get("id", 0),
            reverse=True,
        )
