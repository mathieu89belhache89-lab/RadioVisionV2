import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.radio_parser import RadioParser
from parser.unit_parser import UnitParser
from parser.location_parser import LocationParser
from parser.direction_parser import DirectionParser
from parser.vehicle_parser import VehicleParser
from parser.incident_parser import IncidentParser


PURSUIT_CODES = {
    "10-10",
    "10-11",
    "10-12",
    "10-13",
    "10-14",
    "10-15",
    "10-16",
    "10-17",
    "10-19",
}


def print_result(title, ok, details=""):
    status = "OK" if ok else "ERREUR"

    print("=" * 70)
    print(f"{status} - {title}")

    if details:
        print(details)


def main():
    radio_parser = RadioParser()
    unit_parser = UnitParser()
    location_parser = LocationParser()
    direction_parser = DirectionParser()
    vehicle_parser = VehicleParser()
    incident_parser = IncidentParser()

    tests = [
        {
            "title": "10-12 doit être une poursuite",
            "text": "Central unité 27, 10-12 direction Casino, Mercedes AMG grise, quatre individus à bord.",
            "expected_code": "10-12",
            "expected_pursuit": True,
            "expected_unit": "27",
            "expected_location": "Casino",
            "expected_vehicle": "Mercedes AMG",
        },
        {
            "title": "10-13 doit être une poursuite moto",
            "text": "Central unité 6, 10-13 direction Del Perro, suspect en moto noire, dernier visuel.",
            "expected_code": "10-13",
            "expected_pursuit": True,
            "expected_unit": "6",
            "expected_location": "Del Perro",
        },
        {
            "title": "10-14 doit être une poursuite aérienne",
            "text": "Central unité Henry, 10-14 vers Sandy Shores, véhicule aérien en fuite.",
            "expected_code": "10-14",
            "expected_pursuit": True,
            "expected_unit": "Henry",
            "expected_location": "Sandy Shores",
        },
        {
            "title": "CODE OD doit rester CODE OD même avec renfort immédiat",
            "text": "Central code OD, agent à terre vers Mission Row, besoin de renfort immédiat.",
            "expected_code": "CODE OD",
            "expected_pursuit": False,
            "expected_location": "Mission Row",
        },
        {
            "title": "Tango doit être détecté comme unité / affiliation",
            "text": "Central unité Tango, 10-11 direction Paleto Bay, Audi RS6 noire.",
            "expected_code": "10-11",
            "expected_pursuit": True,
            "expected_unit": "Tango",
            "expected_location": "Paleto Bay",
            "expected_vehicle": "Audi RS6",
        },
        {
            "title": "Mary doit être détecté comme unité / affiliation",
            "text": "Central unité Mary, 10-13 direction Del Perro, moto noire.",
            "expected_code": "10-13",
            "expected_pursuit": True,
            "expected_unit": "Mary",
        },
    ]

    total = 0
    success = 0

    for test in tests:
        total += 1

        text = test["text"]

        code, signification = radio_parser.parse(text)
        unit = unit_parser.find(text)
        location = location_parser.find(text)
        direction_meta = direction_parser.find_detailed(text, location_parser)
        direction = direction_meta.get("name") if direction_meta else direction_parser.find(text)
        vehicle = vehicle_parser.find(text)
        incidents = incident_parser.find(text)

        is_pursuit = code in PURSUIT_CODES

        expected_code = test.get("expected_code")
        expected_pursuit = test.get("expected_pursuit")
        expected_unit = test.get("expected_unit")
        expected_location = test.get("expected_location")
        expected_vehicle = test.get("expected_vehicle")

        checks = []

        checks.append(code == expected_code)
        checks.append(is_pursuit == expected_pursuit)

        if expected_unit:
            checks.append(unit is not None and str(expected_unit).lower() in str(unit).lower())

        if expected_location:
            checks.append(location is not None and expected_location.lower() in str(location.get("name", "")).lower())

        if expected_vehicle:
            checks.append(vehicle is not None and expected_vehicle.lower() in str(vehicle.get("vehicle", "")).lower())

        ok = all(checks)

        if ok:
            success += 1

        details = (
            f"Phrase : {text}\n"
            f"Code : {code}\n"
            f"Motif : {signification}\n"
            f"Poursuite : {is_pursuit}\n"
            f"Unité : {unit}\n"
            f"Lieu : {location.get('name') if location else None}\n"
            f"Direction : {direction}\n"
            f"Véhicule : {vehicle.get('vehicle') if vehicle else None}\n"
            f"Incidents : {incidents}"
        )

        print_result(test["title"], ok, details)

    print("=" * 70)
    print(f"Résultat : {success}/{total} tests OK")

    if success == total:
        print("Tous les tests V4 sont bons.")
    else:
        print("Certains tests sont encore à corriger.")


if __name__ == "__main__":
    main()
