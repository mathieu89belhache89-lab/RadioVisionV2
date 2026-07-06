import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.correction_parser import CorrectionParser


def check(title, ok, details=""):
    status = "OK" if ok else "ERREUR"
    print("=" * 70)
    print(f"{status} - {title}")
    if details:
        print(details)
    return ok


def main():
    parser = CorrectionParser()

    tests = []

    corrected_location = parser.replace_in_text(
        "central unite 21 direction sambi chap"
    )
    tests.append(check(
        "Correction lieu existante",
        "sandy shores" in corrected_location,
        corrected_location,
    ))

    corrected_vehicle = parser.replace_in_text(
        "central unite 14 od rs6 noir"
    )
    tests.append(check(
        "Correction véhicule existante",
        "audi rs6" in corrected_vehicle,
        corrected_vehicle,
    ))

    corrected_code = parser.replace_in_text(
        "central disquette"
    )
    tests.append(check(
        "Correction code existante",
        "10 4" in corrected_code or "10-4" in corrected_code,
        corrected_code,
    ))

    incidents = parser.get_section("incidents")
    tests.append(check(
        "Section incidents disponible",
        isinstance(incidents, dict),
        f"Nombre corrections incidents : {len(incidents)}",
    ))

    print("=" * 70)
    print(f"Résultat : {sum(tests)}/{len(tests)} tests OK")

    if all(tests):
        print("Apprentissage V7 prêt.")
    else:
        print("Certaines corrections V7 sont à vérifier.")


if __name__ == "__main__":
    main()
