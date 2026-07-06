import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.radio_parser import RadioParser


def check(parser, text, expected):
    code, signification = parser.parse(text)
    ok = code == expected
    status = "OK" if ok else "ERREUR"
    print("=" * 70)
    print(f"{status} - {text}")
    print(f"Attendu : {expected}")
    print(f"Obtenu  : {code}")
    if signification:
        print(f"Motif   : {signification}")
    return ok


def main():
    parser = RadioParser()

    tests = [
        ("10-19", "10-19"),
        ("10 19", "10-19"),
        ("code 19", "10-19"),
        ("dix dix neuf", "10-19"),
        ("dis dix neuf", "10-19"),
        ("central unite 21 10-19 vehicule accidente", "10-19"),
        ("central unite 21 accident vehicule", "10-19"),
        ("central unite 21 vehicule accidente mission row", "10-19"),
        ("central unite 21 10-10 refus d obtemperer a pied", "10-10"),
        ("central unite 21 10-10 direction sandy shores", "10-10"),
    ]

    ok_count = 0

    for text, expected in tests:
        if check(parser, text, expected):
            ok_count += 1

    print("=" * 70)
    print(f"Résultat : {ok_count}/{len(tests)} tests OK")

    if ok_count != len(tests):
        raise SystemExit("Certains tests 10-19 / 10-10 ont échoué.")

    print("V9.3.1 anti-confusion 10-19 OK.")


if __name__ == "__main__":
    main()
