import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.location_parser import LocationParser
from parser.direction_parser import DirectionParser
from parser.vehicle_parser import VehicleParser
from parser.radio_parser import RadioParser


def check(title, ok, details):
    print("=" * 70)
    print(("OK" if ok else "ERREUR") + " - " + title)
    print(details)


def main():
    locations = LocationParser()
    directions = DirectionParser()
    vehicles = VehicleParser()
    radio = RadioParser()

    tests = [
        {
            "title": "sambi chap doit devenir Sandy Shores",
            "text": "central unité 21 10-11 direction sambi chap",
            "direction": "Sandy Shores",
            "code": "10-11",
        },
        {
            "title": "palais taubeille doit devenir Paleto Bay",
            "text": "central unité 14 10-10 direction palais taubeille audi rs6 noir",
            "direction": "Paleto Bay",
            "vehicle": "Audi RS6",
            "code": "10-10",
        },
        {
            "title": "mission rho doit devenir Mission Row",
            "text": "central code OD agent à terre vers mission rho besoin de renfort immédiat",
            "direction": "Mission Row",
            "code": "CODE OD",
        },
        {
            "title": "les jeans square doit devenir Legion Square",
            "text": "dernier visuel vers les jeans square véhicule accidenté",
            "direction": "Legion Square",
        },
        {
            "title": "code 208 ne doit pas devenir Peugeot 208",
            "text": "central unité 55 208 mission row agent pris en otage suspect armé",
            "code": "208",
            "vehicle": None,
            "location": "Mission Row",
        },
    ]

    success = 0

    for test in tests:
        text = test["text"]
        code, signification = radio.parse(text)
        location = locations.find(text)
        direction_meta = directions.find_detailed(text, locations)
        vehicle = vehicles.find(text)

        direction_name = direction_meta.get("name") if direction_meta else None
        location_name = location.get("name") if location else None
        vehicle_name = vehicle.get("vehicle") if vehicle else None

        ok = True

        if "code" in test:
            ok = ok and code == test["code"]

        if "direction" in test:
            ok = ok and direction_name == test["direction"]

        if "location" in test:
            ok = ok and location_name == test["location"]

        if "vehicle" in test:
            ok = ok and vehicle_name == test["vehicle"]

        if ok:
            success += 1

        details = (
            f"Phrase : {text}\n"
            f"Code : {code}\n"
            f"Motif : {signification}\n"
            f"Lieu : {location_name}\n"
            f"Direction : {direction_name}\n"
            f"Direction meta : {direction_meta}\n"
            f"Véhicule : {vehicle_name}"
        )

        check(test["title"], ok, details)

    print("=" * 70)
    print(f"Résultat : {success}/{len(tests)} tests OK")

    if success == len(tests):
        print("Tous les tests V6 fuzzy sont bons.")
    else:
        print("Certains tests V6 sont encore à corriger.")


if __name__ == "__main__":
    main()
