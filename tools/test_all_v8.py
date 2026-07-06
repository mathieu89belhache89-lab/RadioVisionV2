import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

TESTS = [
    ROOT_DIR / "tools" / "test_v8_1_regression.py",
    ROOT_DIR / "tools" / "test_v8_2_codes_complets.py",
    ROOT_DIR / "tools" / "test_v8_3_comprehension_complete.py",
    ROOT_DIR / "tools" / "test_v8_4_lieux_fantomes.py",
]


def main():
    print("=" * 74)
    print("TEST GLOBAL RADIOVISION V8")
    print("=" * 74)

    for test_file in TESTS:
        if not test_file.exists():
            print(f"ERREUR : test introuvable : {test_file}")
            print("Installe d'abord les correctifs V8.1, V8.2, V8.3 puis V8.4.")
            raise SystemExit(1)

        print(f"\n>>> {test_file.name}")
        result = subprocess.run([sys.executable, str(test_file)], cwd=str(ROOT_DIR))

        if result.returncode != 0:
            print(f"\nERREUR : {test_file.name} a échoué.")
            raise SystemExit(result.returncode)

    print("\n" + "=" * 74)
    print("OK : tous les tests V8 passent.")
    print("=" * 74)


if __name__ == "__main__":
    main()
