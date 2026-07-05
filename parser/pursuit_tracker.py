import time
from datetime import datetime


class PursuitTracker:

    def __init__(self):
        self.pursuits = []
        self.next_id = 1
        self.active_window = 180
        self.association_threshold = 60

    def set_active_window(self, seconds):
        try:
            seconds = int(seconds)
        except Exception:
            seconds = 180

        self.active_window = max(60, min(seconds, 900))

    def now_time(self):
        return time.time()

    def now_label(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_location_name(self, event):
        location = event.get("location")

        if location:
            return location.get("name")

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
        text = event.get("text", "").lower()

        end_words = [
            "interpellation",
            "interpellé",
            "interpelle",
            "menotté",
            "menotte",
            "terminée",
            "terminee",
            "terminé",
            "termine",
            "fini",
            "saisi",
        ]

        for incident in incidents:
            incident_lower = incident.lower()

            if "interpellation" in incident_lower:
                return True

        for word in end_words:
            if word in text:
                return True

        return False

    def is_pursuit_related(self, event):
        code = event.get("code")
        incidents = event.get("incidents") or []

        if code in ["10-10", "10-11"]:
            return True

        pursuit_words = [
            "poursuite",
            "visuel",
            "fuite",
            "immobilisé",
            "immobilise",
            "accident",
            "interpellation",
            "renfort",
            "refus",
            "coups de feu",
            "arme",
        ]

        for incident in incidents:
            incident_lower = incident.lower()

            for word in pursuit_words:
                if word in incident_lower:
                    return True

        if event.get("vehicle") and (
            event.get("location") or event.get("direction")
        ):
            return True

        return False

    def get_active_pursuits(self):
        active = []
        now = self.now_time()

        for pursuit in self.pursuits:
            if pursuit.get("status") != "active":
                continue

            last_update = pursuit.get("last_update_ts", 0)

            if now - last_update > self.active_window:
                pursuit["status"] = "expired"
                pursuit["status_label"] = "Expirée"
                continue

            active.append(pursuit)

        return active

    def has_active_pursuits(self):
        return len(self.get_active_pursuits()) > 0

    def is_followup_like(self, event):
        if event.get("code") in ["10-10", "10-11"]:
            return False

        return any([
            event.get("location"),
            event.get("direction"),
            event.get("incidents"),
            event.get("vehicle"),
        ])

    def score_pursuit(self, pursuit, event):
        score = 0

        event_unit = event.get("unit")
        pursuit_unit = pursuit.get("unit")

        if event_unit and pursuit_unit:
            if str(event_unit) == str(pursuit_unit):
                score += 60
            else:
                score -= 100

        event_vehicle = self.get_vehicle_key(event)
        pursuit_vehicle = pursuit.get("vehicle_key")

        if event_vehicle and pursuit_vehicle:
            if str(event_vehicle) == str(pursuit_vehicle):
                score += 50
            else:
                score -= 80

        event_location = self.get_location_name(event)
        pursuit_location = pursuit.get("location_name")

        if event_location and pursuit_location:
            if event_location == pursuit_location:
                score += 20
            else:
                score += 5

        event_direction = event.get("direction")
        pursuit_direction = pursuit.get("direction")

        if event_direction and pursuit_direction:
            if str(event_direction).lower() == str(pursuit_direction).lower():
                score += 20
            else:
                score += 5

        event_code = event.get("code")
        pursuit_code = pursuit.get("code")

        if event_code and pursuit_code:
            if event_code == pursuit_code:
                score += 20

        seconds_since_update = self.now_time() - pursuit.get("last_update_ts", 0)

        if seconds_since_update <= 30:
            score += 15
        elif seconds_since_update <= 90:
            score += 10
        elif seconds_since_update <= self.active_window:
            score += 5

        return score

    def find_best_pursuit(self, event):
        active = self.get_active_pursuits()

        if not active:
            return None, 0

        event_has_strong_id = any([
            event.get("unit"),
            self.get_vehicle_key(event),
        ])

        if not event_has_strong_id and self.is_followup_like(event):
            if len(active) == 1:
                return active[0], 60

            return None, 0

        best_pursuit = None
        best_score = -999

        for pursuit in active:
            score = self.score_pursuit(pursuit, event)

            if score > best_score:
                best_score = score
                best_pursuit = pursuit

        if best_score >= self.association_threshold:
            return best_pursuit, best_score

        return None, best_score

    def create_pursuit(self, event):
        pursuit_id = self.next_id
        self.next_id += 1

        vehicle_key = self.get_vehicle_key(event)
        vehicle_label = self.get_vehicle_label(event)
        location_name = self.get_location_name(event)

        now = self.now_time()
        now_label = self.now_label()

        pursuit = {
            "id": pursuit_id,
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
            "location_name": location_name,
            "direction": event.get("direction"),
            "vehicle": event.get("vehicle"),
            "vehicle_key": vehicle_key,
            "vehicle_label": vehicle_label,
            "incidents": list(event.get("incidents") or []),
            "texts": [event.get("text", "")],
        }

        if self.is_end_event(event):
            pursuit["status"] = "ended"
            pursuit["status_label"] = "Terminée"

        self.pursuits.append(pursuit)

        tracked_event = self.pursuit_to_event(pursuit)
        tracked_event["tracker_action"] = "created"
        tracked_event["is_update"] = False

        return tracked_event

    def update_pursuit(self, pursuit, event):
        now = self.now_time()
        now_label = self.now_label()

        pursuit["last_update"] = now_label
        pursuit["last_update_ts"] = now

        if event.get("unit") and not pursuit.get("unit"):
            pursuit["unit"] = event.get("unit")

        if event.get("code") and not pursuit.get("code"):
            pursuit["code"] = event.get("code")

        if event.get("signification") and not pursuit.get("signification"):
            pursuit["signification"] = event.get("signification")

        if event.get("vehicle") and not pursuit.get("vehicle"):
            pursuit["vehicle"] = event.get("vehicle")
            pursuit["vehicle_key"] = self.get_vehicle_key(event)
            pursuit["vehicle_label"] = self.get_vehicle_label(event)

        if event.get("location"):
            pursuit["location"] = event.get("location")
            pursuit["location_name"] = self.get_location_name(event)

        if event.get("direction"):
            pursuit["direction"] = event.get("direction")

        for incident in event.get("incidents") or []:
            if incident not in pursuit["incidents"]:
                pursuit["incidents"].append(incident)

        if event.get("text"):
            pursuit["texts"].append(event.get("text"))

        if self.is_end_event(event):
            pursuit["status"] = "ended"
            pursuit["status_label"] = "Terminée"

        tracked_event = self.pursuit_to_event(pursuit)
        tracked_event["tracker_action"] = "updated"
        tracked_event["is_update"] = True

        return tracked_event

    def make_unassigned_event(self, event):
        unassigned = event.copy()
        unassigned["pursuit_id"] = None
        unassigned["pursuit_label"] = "Non attribué"
        unassigned["tracker_action"] = "unassigned"
        unassigned["is_update"] = False
        unassigned["is_unassigned"] = True

        return unassigned

    def pursuit_to_event(self, pursuit):
        return {
            "text": " ".join(pursuit.get("texts", [])),
            "code": pursuit.get("code"),
            "signification": pursuit.get("signification"),
            "location": pursuit.get("location"),
            "unit": pursuit.get("unit"),
            "direction": pursuit.get("direction"),
            "vehicle": pursuit.get("vehicle"),
            "incidents": list(pursuit.get("incidents") or []),
            "pursuit_id": pursuit.get("id"),
            "pursuit_label": f"Poursuite #{pursuit.get('id')}",
            "pursuit_status": pursuit.get("status"),
            "pursuit_status_label": pursuit.get("status_label"),
            "tracker_action": "snapshot",
            "is_update": False,
            "is_unassigned": False,
        }

    def process_followup_for_active_pursuit(self, event):
        best_pursuit, score = self.find_best_pursuit(event)

        if best_pursuit:
            tracked_event = self.update_pursuit(best_pursuit, event)
            tracked_event["association_score"] = score
            return tracked_event

        unassigned = self.make_unassigned_event(event)
        unassigned["association_score"] = score

        return unassigned

    def process_event(self, event):
        active_exists = self.has_active_pursuits()

        if active_exists and self.is_followup_like(event):
            if event.get("code") not in ["10-10", "10-11"]:
                return self.process_followup_for_active_pursuit(event)

        if not self.is_pursuit_related(event):
            return event

        best_pursuit, score = self.find_best_pursuit(event)

        if best_pursuit:
            tracked_event = self.update_pursuit(best_pursuit, event)
            tracked_event["association_score"] = score
            return tracked_event

        if event.get("code") in ["10-10", "10-11"]:
            tracked_event = self.create_pursuit(event)
            tracked_event["association_score"] = 100
            return tracked_event

        if event.get("vehicle") and (
            event.get("location") or event.get("direction")
        ):
            tracked_event = self.create_pursuit(event)
            tracked_event["association_score"] = 80
            return tracked_event

        if self.is_followup_like(event):
            unassigned = self.make_unassigned_event(event)
            unassigned["association_score"] = score
            return unassigned

        return event

    def get_history(self):
        self.get_active_pursuits()

        return sorted(
            self.pursuits,
            key=lambda pursuit: pursuit.get("id", 0),
            reverse=True,
        )