import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.radio_parser import RadioParser

try:
    from parser.correction_parser import CorrectionParser
except Exception:
    CorrectionParser = None


def check(parser, phrase, expected, errors, label=None):
    code, signification = parser.parse(phrase)

    if code != expected:
        errors.append({
            "phrase": phrase,
            "expected": expected,
            "got": code,
            "label": label or phrase,
        })
        return False

    return True


def main():
    parser = RadioParser()
    errors = []
    total = 0

    print("=" * 70)
    print("TEST V8.2 - CODES RADIO COMPLETS")
    print("=" * 70)

    # 1) Chaque code officiel doit être reconnu en écriture brute.
    for code in parser.codes.keys():
        variants = [code]

        if code.startswith("10-"):
            variants.append(code.replace("-", " "))

        if code.startswith("CODE "):
            variants.append(code.lower())

        for phrase in variants:
            total += 1
            check(parser, phrase, code, errors, "code officiel")

    # 2) Chaque alias construit par RadioParser doit retomber sur son code.
    # C'est le test le plus important : il évite qu'un alias ajouté soit cassé par une autre règle.
    for item in parser.aliases:
        total += 1
        check(
            parser,
            item.get("alias", ""),
            item.get("code"),
            errors,
            "alias interne",
        )

    # 3) Variantes Whisper connues / entendues en jeu.
    known_variants = {
        "disquette": "10-4",
        "disquatre": "10-4",
        "dis sank": "10-5",
        "cis cis": "10-6",
        "six six": "10-6",
        "this is": "10-6",
        "disces": "10-7",
        "code content": "10-10",
        "codes content": "10-10",
        "disonze": "10-11",
        "dizonze": "10-11",
        "disons": "10-11",
        "dis douze": "10-12",
        "dis treize": "10-13",
        "dis quatorze": "10-14",
        "dis quinze": "10-15",
        "dis seize": "10-16",
        "code 17": "10-17",
        "dis dix neuf": "10-19",
        "code 30": "10-30",
        "code 31": "10-31",
        "code 32": "10-32",
        "code 33": "10-33",
        "dis 99": "10-99",
        "dix 99": "10-99",
        "10 89": "10-99",
        "10 98": "10-99",
        "renfort immediat": "10-99",
        "450 9": "459",
        "code 559": "459",
        "quatre cent soixante": "460",
        "superette": "461",
        "cent quatre vingt sept": "187",
        "deux cent sept": "207",
        "277": "207",
        "deux cent huit": "208",
        "code de 108": "208",
        "agent pris en otage": "208",
        "code oscar david": "CODE OD",
        "code o d": "CODE OD",
        "agent a terre": "CODE OD",
        "agent at": "CODE OD",
        "agent atr": "CODE OD",
        "code delta sierra": "CODE DS",
        "suspect neutralise": "CODE DS",
        "code delta oscar alpha": "CODE DOA",
        "civil a terre": "CODE DOA",
        "code delta charlie delta": "CODE DCD",
        "civil decede": "CODE DCD",
        "code romeo delta papa": "CODE RDP",
        "recapitulatif des patrouilles": "CODE RDP",
        "code esse": "CODE S",
        "silence radio": "CODE S",
        "tango plus": "TANGO+",
        "marie": "MARY",
        "henri": "HENRY",
        "lincon": "LINCOLN",
        "adam": "ADAMS",
    }

    for phrase, expected in known_variants.items():
        total += 1
        check(parser, phrase, expected, errors, "variante whisper")

    # 4) Tests avec phrases complètes.
    full_calls = {
        "central unite 21 10 11 direction sandy shores": "10-11",
        "central unite 27 dis douze direction casino": "10-12",
        "central unite henry dis quatorze vers sandy shores": "10-14",
        "central code od agent a terre mission row besoin de renfort immediat": "CODE OD",
        "central code od agent at mission raw besoin de renfort immediat": "CODE OD",
        "central unite 55 208 mission row agent pris en otage": "208",
        "central unite tango plus 10 11 direction casino": "10-11",
    }

    for phrase, expected in full_calls.items():
        total += 1
        check(parser, phrase, expected, errors, "phrase complete")

    # 5) Si CorrectionParser existe, on teste aussi le flux réel correction -> radio parser.
    if CorrectionParser:
        correction_parser = CorrectionParser()
        correction_calls = {
            "central code od agent at permission rô besoin de renfort immédiat": "CODE OD",
            "central unité 55 208 mission raw agent pris en hotel suspect armé": "208",
        }

        for phrase, expected in correction_calls.items():
            corrected = correction_parser.replace_in_text(phrase)
            total += 1
            check(parser, corrected, expected, errors, "correction + parser")

    if errors:
        print(f"ERREUR : {len(errors)} / {total} tests ont échoué.")
        print("-" * 70)

        for error in errors[:80]:
            print(f"[{error['label']}] {error['phrase']!r}")
            print(f"  attendu : {error['expected']}")
            print(f"  obtenu  : {error['got']}")

        if len(errors) > 80:
            print(f"... {len(errors) - 80} erreur(s) masquée(s)")

        raise SystemExit(1)

    print(f"OK : {total}/{total} tests codes radio passent.")
    print("RadioParser V8.2 prêt.")


if __name__ == "__main__":
    main()
