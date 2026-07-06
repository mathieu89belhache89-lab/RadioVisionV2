import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.correction_parser import CorrectionParser


def print_result(title, ok, details=""):
    status = "OK" if ok else "ERREUR"
    print("=" * 70)
    print(f"{status} - {title}")
    if details:
        print(details)


def main():
    parser = CorrectionParser()

    tests = []

    success, message = parser.add_correction(
        "locations",
        "test v8 sambi",
        "Sandy Shores",
    )
    tests.append(("Ajout correction lieu", success, message))

    found = parser.find_exact("locations", "test v8 sambi")
    tests.append((
        "Lecture correction ajoutée",
        found == "Sandy Shores",
        f"Trouvé : {found}",
    ))

    replaced = parser.replace_in_text("central direction test v8 sambi")
    tests.append((
        "Remplacement dans une phrase",
        "sandy shores" in replaced.lower(),
        f"Résultat : {replaced}",
    ))

    success, message = parser.remove_correction("locations", "test v8 sambi")
    tests.append(("Suppression correction", success, message))

    found_after_delete = parser.find_exact("locations", "test v8 sambi")
    tests.append((
        "Correction supprimée absente",
        found_after_delete is None,
        f"Trouvé : {found_after_delete}",
    ))

    total = len(tests)
    ok_count = 0

    for title, ok, details in tests:
        if ok:
            ok_count += 1
        print_result(title, ok, details)

    print("=" * 70)
    print(f"Résultat : {ok_count}/{total} tests OK")

    if ok_count == total:
        print("Apprentissage V8 prêt.")
    else:
        print("Certains tests V8 sont encore à corriger.")


if __name__ == "__main__":
    main()
