import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.radio_parser import RadioParser
from parser.location_parser import LocationParser
from parser.unit_parser import UnitParser
from parser.incident_parser import IncidentParser
from parser.intervention_tracker import InterventionTracker
from parser.correction_parser import CorrectionParser


radio = RadioParser()
locations = LocationParser()
units = UnitParser()
incidents_parser = IncidentParser()
corrections = CorrectionParser()
tracker = InterventionTracker()


def make_event(text):
    parse_text = corrections.replace_in_text(text)
    code, signification = radio.parse(parse_text)
    location = locations.find(parse_text)

    return {
        "text": text,
        "raw_text": text,
        "parse_text": parse_text,
        "code": code,
        "signification": signification,
        "location": location,
        "unit": units.find(parse_text),
        "direction": location.get("name") if location else None,
        "direction_meta": None,
        "vehicle": None,
        "incidents": incidents_parser.find(parse_text),
        "is_update": False,
        "is_unassigned": False,
        "is_code_lookup": False,
        "pursuit_id": None,
        "pursuit_label": None,
        "pursuit_status": None,
        "pursuit_status_label": None,
        "association_score": 0,
    }


def assert_equal(name, value, expected):
    if value != expected:
        raise AssertionError(f"{name}: attendu {expected!r}, reçu {value!r}")


def assert_true(name, value):
    if not value:
        raise AssertionError(f"{name}: valeur fausse")


def run_tests():
    tests = []

    event_208 = make_event(
        "central unité 55 208 mission row agent pris en otage suspect armé"
    )
    tracked_208 = tracker.process_event(event_208)
    tests.append(("208 crée intervention", tracked_208 is not None))
    assert_equal("code 208", tracked_208.get("code"), "208")
    assert_equal("dossier 208", tracked_208.get("case_label"), "Intervention #1")
    assert_equal("type 208", tracked_208.get("case_type_label"), "Prise d’otage agent")
    assert_true(
        "otage détecté",
        any("Otage" in item for item in tracked_208.get("incidents") or []),
    )

    followup = make_event("unité 55 besoin de renfort immédiat mission row")
    tracked_followup = tracker.process_event(followup)
    tests.append(("follow-up 55 met à jour intervention", tracked_followup is not None))
    assert_equal("même intervention", tracked_followup.get("case_id"), 1)
    assert_true("mise à jour", tracked_followup.get("is_update"))

    pursuit = make_event("central unité 21 10-11 direction sandy shores bmw m4 blanche")
    tracked_pursuit = tracker.process_event(pursuit)
    tests.append(("10-11 ne devient pas intervention", tracked_pursuit is None))

    event_461 = make_event("central unité 12 461 supérette sandy shores besoin de renfort")
    tracked_461 = tracker.process_event(event_461)
    tests.append(("461 crée intervention", tracked_461 is not None))
    assert_equal("type 461", tracked_461.get("case_type_label"), "Supérette")

    event_od = make_event("central code od agent à terre vers mission row besoin de renfort")
    tracked_od = tracker.process_event(event_od)
    tests.append(("CODE OD crée urgence", tracked_od is not None))
    assert_equal("kind OD", tracked_od.get("case_kind"), "urgence")
    assert_equal("type OD", tracked_od.get("case_type_label"), "Agent à terre")

    event_31 = make_event("central unité 32 10-31 bijouterie trois individus armés")
    tracked_31 = tracker.process_event(event_31)
    tests.append(("10-31 crée intervention", tracked_31 is not None))
    assert_equal("type 10-31", tracked_31.get("case_type_label"), "Braquage confirmé")

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
        raise SystemExit("Certains tests V9.2 ont échoué.")

    print("V9.2 dossiers intervention OK.")


if __name__ == "__main__":
    run_tests()
