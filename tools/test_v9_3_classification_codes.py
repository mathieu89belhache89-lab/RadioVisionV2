import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.radio_code_classifier import RadioCodeClassifier
from parser.intervention_tracker import InterventionTracker


classifier = RadioCodeClassifier()


def assert_equal(name, value, expected):
    if value != expected:
        raise AssertionError(f"{name}: attendu {expected!r}, reçu {value!r}")


def assert_true(name, value):
    if not value:
        raise AssertionError(f"{name}: valeur fausse")


def make_event(code, unit=None, location_name=None, incidents=None):
    location = None

    if location_name:
        location = {
            "name": location_name,
            "id": None,
            "category": "Test",
            "type": "zone",
            "score": 100,
            "raw": location_name,
        }

    signification = {
        "10-4": "Message bien reçu",
        "10-8": "Fusillade",
        "10-19": "Accident",
        "10-99": "Demande de renfort immédiat",
        "208": "Prise d’otage sur agent de l’état",
        "CODE 3": "Urgence avec sirène",
        "PO": "Prise d’otage",
    }.get(code, code)

    return {
        "text": f"test {code}",
        "raw_text": f"test {code}",
        "parse_text": f"test {code}",
        "code": code,
        "signification": signification,
        "location": location,
        "unit": unit,
        "direction": location_name,
        "direction_meta": None,
        "vehicle": None,
        "incidents": incidents or [],
        "is_code_lookup": False,
        "is_update": False,
        "is_unassigned": False,
    }


def run_tests():
    tests = []

    codes_file = ROOT_DIR / "data" / "radio_codes.json"

    with codes_file.open("r", encoding="utf-8") as f:
        official_codes = json.load(f)

    missing = []

    for code in official_codes:
        data = classifier.classify(code)

        if data.get("category") == "unknown" or data.get("action") == "display":
            missing.append(code)

    assert_equal("codes sans règle", missing, [])
    tests.append(("tous les codes officiels ont une règle", True))

    expected = {
        "10-4": ("radio_status", "status", False, False, False),
        "10-11": ("pursuit_start", "pursuit_start", False, False, True),
        "10-16": ("pursuit_update", "pursuit_update", False, True, False),
        "10-19": ("pursuit_or_intervention", "pursuit_or_case", True, True, False),
        "10-31": ("intervention", "case", True, False, False),
        "10-99": ("emergency", "case", True, False, False),
        "208": ("intervention", "case", True, False, False),
        "CODE 3": ("emergency", "case", True, False, False),
        "CODE OD": ("emergency", "case", True, False, False),
        "CODE S": ("radio_status", "status", False, False, False),
        "TANGO": ("unit_type", "unit_info", False, False, False),
        "PO": ("intervention", "case", True, False, False),
    }

    for code, wanted in expected.items():
        data = classifier.classify(code)
        got = (
            data.get("category"),
            data.get("action"),
            bool(data.get("creates_dossier")),
            bool(data.get("updates_pursuit")),
            bool(data.get("creates_pursuit")),
        )
        assert_equal(f"classification {code}", got, wanted)

    tests.append(("règles clés cohérentes", True))

    tracker = InterventionTracker()

    status_event = make_event("10-4", unit="21")
    assert_equal("10-4 ne crée pas intervention", tracker.process_event(status_event), None)
    tests.append(("10-4 ne crée pas de dossier", True))

    event_208 = make_event("208", unit="55", location_name="Mission Row", incidents=["🧍 Otage signalé"])
    tracked_208 = tracker.process_event(event_208)
    assert_true("208 crée dossier", tracked_208)
    assert_equal("type 208", tracked_208.get("case_type_label"), "Prise d’otage agent")
    assert_equal("kind 208", tracked_208.get("case_kind"), "intervention")
    tests.append(("208 crée intervention", True))

    event_1099 = make_event("10-99", unit="21", location_name="Mission Row", incidents=["🚨 Renfort demandé"])
    tracked_1099 = tracker.process_event(event_1099)
    assert_true("10-99 crée urgence", tracked_1099)
    assert_equal("type 10-99", tracked_1099.get("case_type_label"), "Renfort immédiat")
    assert_equal("kind 10-99", tracked_1099.get("case_kind"), "urgence")
    tests.append(("10-99 crée urgence", True))

    event_code3 = make_event("CODE 3", unit="12", location_name="Sandy Shores")
    tracked_code3 = tracker.process_event(event_code3)
    assert_true("CODE 3 crée urgence", tracked_code3)
    assert_equal("kind CODE 3", tracked_code3.get("case_kind"), "urgence")
    tests.append(("CODE 3 crée urgence", True))

    event_1019 = make_event("10-19", unit="44", location_name="Casino")
    tracked_1019 = tracker.process_event(event_1019)
    assert_true("10-19 crée intervention si pas poursuite", tracked_1019)
    assert_equal("type 10-19", tracked_1019.get("case_type_label"), "Accident")
    tests.append(("10-19 crée accident hors poursuite", True))

    ok_count = 0

    for label, ok in tests:
        if ok:
            ok_count += 1
            print(f"OK - {label}")
        else:
            print(f"ERREUR - {label}")

    print("=" * 70)
    print(f"Résultat : {ok_count}/{len(tests)} tests OK")

    if ok_count != len(tests):
        raise SystemExit("Certains tests V9.3 ont échoué.")

    print("V9.3 classification complète OK.")


if __name__ == "__main__":
    run_tests()
