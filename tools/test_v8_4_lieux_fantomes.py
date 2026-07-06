import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.location_parser import LocationParser
from parser.direction_parser import DirectionParser


def check_equal(label, value, expected):
    if value != expected:
        print("=" * 70)
        print(f"ERREUR - {label}")
        print(f"Obtenu  : {value}")
        print(f"Attendu : {expected}")
        return False

    print(f"OK - {label}")
    return True


def main():
    location_parser = LocationParser()
    direction_parser = DirectionParser()

    tests = []

    # Faux positifs vus en vocal : le parser ne doit pas inventer un lieu
    # quand le morceau entendu contient seulement véhicule / couleur / individus.
    false_location_phrases = [
        "bmw mk de blanche 2 individus a bord",
        "bmw m4 blanc 2 individus a bord",
        "inter bmw m2 individus a bord",
        "vehicule blanc deux individus a bord",
        "mercedes amg gris 4 individus a bord",
    ]

    for phrase in false_location_phrases:
        location = location_parser.find(phrase)
        tests.append(check_equal(
            f"pas de lieu fantome pour : {phrase}",
            location.get("name") if location else None,
            None,
        ))

    # Les vrais lieux doivent continuer à passer.
    positive_locations = [
        ("direction sandy shores", "Sandy Shores"),
        ("mission row vehicule immobilise", "Mission Row"),
        ("mission raw vehicule immobilise", "Mission Row"),
        ("casino mercedes amg gris", "Casino"),
        ("bijouterie trois individus armes", "Bijouterie"),
        ("direction paleto bay audi rs6 noire", "Paleto Bay"),
    ]

    for phrase, expected in positive_locations:
        location = location_parser.find(phrase)
        tests.append(check_equal(
            f"lieu reel : {phrase}",
            location.get("name") if location else None,
            expected,
        ))

    # Les directions restent prioritaires et fiables.
    direction_tests = [
        ("dernier visuel vers mission raw vehicule immobilise", "Mission Row"),
        ("direction sambi chap bmw m4 blanche", "Sandy Shores"),
        ("direction palais taubeille audi rs6 noire", "Paleto Bay"),
    ]

    for phrase, expected in direction_tests:
        direction = direction_parser.find_detailed(phrase, location_parser)
        tests.append(check_equal(
            f"direction : {phrase}",
            direction.get("name") if direction else None,
            expected,
        ))

    ok = sum(1 for item in tests if item)
    total = len(tests)

    print("=" * 70)
    print(f"Résultat : {ok}/{total} tests OK")

    if ok != total:
        print("Certains faux lieux sont encore possibles.")
        raise SystemExit(1)

    print("V8.4 lieux fantômes OK.")


if __name__ == "__main__":
    main()
