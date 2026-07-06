import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from parser.correction_parser import CorrectionParser
from parser.radio_parser import RadioParser
from parser.location_parser import LocationParser
from parser.direction_parser import DirectionParser
from parser.vehicle_parser import VehicleParser
from parser.incident_parser import IncidentParser


class Harness:
    def __init__(self):
        self.corrections = CorrectionParser()
        self.radio = RadioParser()
        self.locations = LocationParser()
        self.directions = DirectionParser()
        self.vehicles = VehicleParser()
        self.incidents = IncidentParser()

    def parse(self, phrase):
        corrected = self.corrections.replace_in_text(phrase)
        code, signification = self.radio.parse(corrected)
        location = self.locations.find(corrected)
        direction_meta = self.directions.find_detailed(corrected, self.locations)
        direction = direction_meta.get("name") if direction_meta else None
        vehicle = self.vehicles.find(corrected)
        incidents = self.incidents.find(corrected)
        return {
            "phrase": phrase,
            "corrected": corrected,
            "code": code,
            "signification": signification,
            "location": location.get("name") if location else None,
            "direction": direction,
            "vehicle": vehicle.get("vehicle") if vehicle else None,
            "vehicle_color": vehicle.get("color") if vehicle else None,
            "incidents": incidents,
        }


def add_error(errors, group, phrase, field, expected, got, parsed):
    errors.append({
        "group": group,
        "phrase": phrase,
        "field": field,
        "expected": expected,
        "got": got,
        "corrected": parsed.get("corrected"),
    })


def expect(h, errors, group, phrase, **expected):
    parsed = h.parse(phrase)
    for field, value in expected.items():
        if field == "incident_contains":
            joined = " | ".join(parsed.get("incidents") or [])
            if value not in joined:
                add_error(errors, group, phrase, field, value, joined, parsed)
        elif field == "no_code":
            if value and parsed.get("code") is not None:
                add_error(errors, group, phrase, "code", None, parsed.get("code"), parsed)
        elif field == "no_vehicle":
            if value and parsed.get("vehicle") is not None:
                add_error(errors, group, phrase, "vehicle", None, parsed.get("vehicle"), parsed)
        else:
            if parsed.get(field) != value:
                add_error(errors, group, phrase, field, value, parsed.get(field), parsed)
    return parsed


def main():
    h = Harness()
    errors = []
    total = 0

    print("=" * 74)
    print("TEST V8.3 - COMPREHENSION COMPLETE RADIOVISION")
    print("=" * 74)

    # 1) Tous les codes officiels + formats bruts.
    for code in h.radio.codes.keys():
        variants = [code]
        if code.startswith("10-"):
            variants += [code.replace("-", " "), f"central unite 21 {code} direction sandy shores"]
        if code.startswith("CODE "):
            variants += [code.lower(), f"central {code.lower()} mission row"]
        for phrase in variants:
            total += 1
            expect(h, errors, "codes officiels", phrase, code=code)

    # 2) Tous les alias internes du RadioParser, isolés et dans un call.
    for item in h.radio.aliases:
        alias = item.get("alias") or ""
        expected_code = item.get("code")
        for phrase in [alias, f"central unite 21 {alias} direction sandy shores"]:
            total += 1
            expect(h, errors, "alias radio", phrase, code=expected_code)

    # 3) Variantes Whisper critiques, dont celles entendues en test réel.
    radio_variants = {
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
        "agent pris en hotel": "208",
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
    for phrase, code in radio_variants.items():
        for wrapped in [phrase, f"central unite 21 {phrase} direction casino"]:
            total += 1
            expect(h, errors, "variantes whisper code", wrapped, code=code)

    # 4) CODE OD et codes de rapport doivent rester prioritaires face à renfort / 10-99.
    priority_calls = {
        "central code od agent a terre mission row besoin de renfort immediat": "CODE OD",
        "central code od agent at permission rô besoin de renfort immédiat": "CODE OD",
        "central code od agent atr mission raw besoin de renfort immediat": "CODE OD",
        "central code ds suspect neutralise besoin de renfort immediat": "CODE DS",
        "central code doa civil a terre besoin de renfort immediat": "CODE DOA",
        "central code dcd civil decede besoin de renfort immediat": "CODE DCD",
        "central code s silence radio total besoin de renfort immediat": "CODE S",
    }
    for phrase, code in priority_calls.items():
        total += 1
        expect(h, errors, "priorite codes sensibles", phrase, code=code)

    # 5) 208 positif, mais Peugeot 208 ne doit pas devenir un code radio.
    positive_208 = [
        "central unite 55 208 mission row agent pris en otage suspect arme",
        "central unité 55 deux cent huit mission raw agent pris en hotel suspect armé",
        "central unite 55 code de 108 mission row agent pris en otage",
    ]
    for phrase in positive_208:
        total += 1
        expect(h, errors, "code 208 positif", phrase, code="208")

    negative_208 = [
        "peugeot 208 blanche",
        "vehicule peugeot 208 blanc",
        "central unite 21 vehicule peugeot 208 direction sandy shores",
    ]
    for phrase in negative_208:
        total += 1
        expect(h, errors, "anti faux code 208", phrase, no_code=True)

    total += 1
    expect(
        h,
        errors,
        "anti faux code 208",
        "central unite 21 10-11 direction mission row peugeot 208 blanche",
        code="10-11",
    )

    # 6) Lieux / directions corrigés, avec et sans phrases complètes.
    direction_variants = {
        "direction sambi chap": "Sandy Shores",
        "direction sandishore": "Sandy Shores",
        "direction sandy short": "Sandy Shores",
        "vers 110 heures": "Sandy Shores",
        "direction mission raw": "Mission Row",
        "vers mission rho": "Mission Row",
        "direction palais-taubeille": "Paleto Bay",
        "direction palais taubeille": "Paleto Bay",
        "dernier visuel vers les jeans square": "Legion Square",
        "direction delpero": "Del Perro",
        "direction delpéro": "Del Perro",
        "direction casino": "Casino",
        "direction mirror park": "Mirror Park",
    }
    for phrase, direction in direction_variants.items():
        for wrapped in [phrase, f"central unite 21 10-11 {phrase} bmw m4 blanche"]:
            total += 1
            parsed = expect(h, errors, "lieux directions", wrapped, direction=direction)
            if parsed.get("direction") == direction and parsed.get("location") not in [direction, None]:
                add_error(errors, "lieux directions", wrapped, "location", direction, parsed.get("location"), parsed)

    location_only_variants = {
        "permission rô besoin de renfort immédiat": "Mission Row",
        "vermission euro vehicule immobilise": "Mission Row",
        "central code od agent at mission raw besoin de renfort immediat": "Mission Row",
    }
    for phrase, location in location_only_variants.items():
        total += 1
        expect(h, errors, "lieux sans direction", phrase, location=location)

    # 7) Véhicules, couleurs, faux positifs.
    vehicle_variants = {
        "wm4 blanche": "BMW M4",
        "w m4 blanche": "BMW M4",
        "w m 4 blanche": "BMW M4",
        "bmw m4 blanche": "BMW M4",
        "ds amg gris": "Mercedes AMG",
        "mercedes amg grise": "Mercedes AMG",
        "audi r s6 noire": "Audi RS6",
        "od rs6 noire": "Audi RS6",
        "moto noire": "Moto",
    }
    for phrase, vehicle in vehicle_variants.items():
        total += 1
        expect(h, errors, "vehicules", f"central unite 21 10-11 direction sandy shores {phrase}", vehicle=vehicle)

    vehicle_negative = [
        "inter bmw m2 individus a bord",
        "central unite 21 10-11 direction sandy shores inter bmw m2 individus a bord",
        "premier individu a bord",
        "oracle indique direction sandy shores",  # alias GTA ambigu sans contexte fiable
    ]
    for phrase in vehicle_negative:
        total += 1
        expect(h, errors, "anti faux vehicules", phrase, no_vehicle=True)

    # 8) Incidents et infos métier.
    incident_cases = [
        ("vehicule immobilisee", "Véhicule immobilisé"),
        ("vehicule immobilise", "Véhicule immobilisé"),
        ("dernier visuel", "Visuel signalé"),
        ("plus de visuel", "Visuel perdu"),
        ("suspect arme", "Individu armé"),
        ("coups de feu", "Coups de feu"),
        ("besoin de renfort", "Renfort demandé"),
        ("fuite a pied", "Fuite à pied"),
        ("suspect interpelle", "Interpellation"),
        ("deux individus a bord", "2 individu"),
        ("4 individus a bord", "4 individu"),
    ]
    for phrase, needle in incident_cases:
        total += 1
        expect(h, errors, "incidents", f"central unite 21 10-11 direction sandy shores {phrase}", incident_contains=needle)

    # 9) Scénarios complets entendus en vocal.
    full_scenarios = [
        ("central unite 21 10-11 direction sandy shores bmw m4 blanche deux individus a bord", {"code": "10-11", "direction": "Sandy Shores", "vehicle": "BMW M4", "incident_contains": "2 individu"}),
        ("unite 21 dernier visuel vers mission raw vehicule immobilisee", {"direction": "Mission Row", "incident_contains": "Véhicule immobilisé"}),
        ("central unite 27 10-12 direction casino mercedes amg grise quatre individus a bord", {"code": "10-12", "direction": "Casino", "vehicle": "Mercedes AMG", "incident_contains": "4 individu"}),
        ("central unite henry 10-14 vers sandy shores vehicule aerien en fuite", {"code": "10-14", "direction": "Sandy Shores"}),
        ("central code od agent at mission raw besoin de renfort immediat", {"code": "CODE OD", "location": "Mission Row", "incident_contains": "Renfort demandé"}),
        ("central unite tango 10-11 direction palais-taubeille audi rs6 noire", {"code": "10-11", "direction": "Paleto Bay", "vehicle": "Audi RS6"}),
        ("central unite 55 208 mission raw agent pris en hotel suspect arme", {"code": "208", "location": "Mission Row", "incident_contains": "Individu armé"}),
    ]
    for phrase, exp in full_scenarios:
        total += 1
        expect(h, errors, "scenarios complets", phrase, **exp)

    if errors:
        print(f"ERREUR : {len(errors)} / {total} vérifications ont échoué.")
        print("-" * 74)
        for error in errors[:120]:
            print(f"[{error['group']}] {error['phrase']!r}")
            print(f"  champ    : {error['field']}")
            print(f"  attendu  : {error['expected']}")
            print(f"  obtenu   : {error['got']}")
            print(f"  corrigé  : {error['corrected']}")
            print("-" * 74)
        if len(errors) > 120:
            print(f"... {len(errors) - 120} erreur(s) masquée(s)")
        raise SystemExit(1)

    print(f"OK : {total}/{total} vérifications passent.")
    print("Comprehension parser V8.3 stable sur codes, lieux, directions, véhicules et incidents.")


if __name__ == "__main__":
    main()
