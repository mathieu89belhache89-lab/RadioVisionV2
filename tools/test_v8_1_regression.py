import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.correction_parser import CorrectionParser
from parser.location_parser import LocationParser
from parser.direction_parser import DirectionParser
from parser.vehicle_parser import VehicleParser


def ok(label, condition, detail=""):
    status = "OK" if condition else "ERREUR"
    print("=" * 70)
    print(f"{status} - {label}")
    if detail:
        print(detail)
    return bool(condition)


def main():
    correction = CorrectionParser()
    location_parser = LocationParser()
    direction_parser = DirectionParser()
    vehicle_parser = VehicleParser()

    success = 0
    total = 0

    tests = [
        ("permission rô besoin de renfort immédiat", "Mission Row"),
        ("vermission euro vehicule immobilise", "Mission Row"),
        ("mission raw", "Mission Row"),
        ("palais taubeille", "Paleto Bay"),
    ]

    for heard, expected in tests:
        total += 1
        corrected = correction.replace_in_text(heard)
        location = location_parser.find(corrected)
        result = location.get("name") if location else None
        success += ok(
            f"{heard} -> {expected}",
            result == expected,
            f"Corrigé : {corrected}\nLieu : {result}",
        )

    total += 1
    corrected = correction.replace_in_text("central code od agent at mission raw besoin de renfort immediat")
    success += ok(
        "agent at -> agent a terre",
        "agent a terre" in corrected,
        f"Corrigé : {corrected}",
    )

    total += 1
    text = correction.replace_in_text("inter bmw m2 individus a bord")
    vehicle = vehicle_parser.find(text)
    success += ok(
        "anti faux BMW M2 avant individus",
        vehicle is None,
        f"Texte : {text}\nVéhicule : {vehicle}",
    )

    total += 1
    text = correction.replace_in_text("wm4 blanche 2 individus a bord")
    vehicle = vehicle_parser.find(text)
    vehicle_name = vehicle.get("vehicle") if vehicle else None
    success += ok(
        "wm4 -> BMW M4",
        vehicle_name == "BMW M4",
        f"Texte : {text}\nVéhicule : {vehicle_name}",
    )

    total += 1
    direction = direction_parser.find_detailed(
        correction.replace_in_text("unite 21 dernier visuel vers mission raw vehicule immobilise"),
        location_parser,
    )
    direction_name = direction.get("name") if direction else None
    success += ok(
        "direction Mission Row",
        direction_name == "Mission Row",
        f"Direction : {direction_name}\nMeta : {direction}",
    )

    print("=" * 70)
    print(f"Résultat : {success}/{total} tests OK")

    if success == total:
        print("Correctifs V8.1 prêts.")
    else:
        print("Certains correctifs V8.1 doivent être revus.")


if __name__ == "__main__":
    main()