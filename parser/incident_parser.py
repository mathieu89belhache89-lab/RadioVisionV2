import re
import unicodedata


class IncidentParser:

    NUMBER_WORDS = {
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
    }

    def clean(self, text: str) -> str:
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        text = text.replace("-", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def find_people(self, text_clean: str):
        patterns = [
            r"\b(\d{1,2})\s+(individus|individu|personnes|personne|occupants|occupant)\b",
            r"\b(un|une|deux|trois|quatre|cinq|six)\s+(individus|individu|personnes|personne|occupants|occupant)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if match:
                value = match.group(1)

                if value.isdigit():
                    count = int(value)
                else:
                    count = self.NUMBER_WORDS.get(value)

                if count:
                    return f"{count} individu(s) à bord"

        if re.search(r"\bconducteur seul\b", text_clean):
            return "1 individu à bord"

        return None

    def find_weapon(self, text_clean: str):
        if re.search(r"\barme visible\b", text_clean):
            return "Arme visible"

        if re.search(r"\bindividu arme\b|\bindividus armes\b|\bsuspect arme\b", text_clean):
            return "Individu armé"

        if re.search(r"\barme de poing\b|\bpistolet\b", text_clean):
            return "Arme de poing"

        if re.search(r"\bfusil\b|\barme lourde\b|\bak\b|\bkalash\b", text_clean):
            return "Arme longue / lourde"

        return None

    def find_plate(self, text_clean: str):
        patterns = [
            r"\bplaque\s+([a-z0-9 ]{3,12})\b",
            r"\bimmat\s+([a-z0-9 ]{3,12})\b",
            r"\bimmatriculation\s+([a-z0-9 ]{3,12})\b",
        ]

        stop_words = [
            "direction",
            "avec",
            "code",
            "unite",
            "central",
            "individu",
            "individus",
            "arme",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if match:
                plate = match.group(1).strip()

                for word in stop_words:
                    plate = plate.split(word)[0].strip()

                plate = plate.upper()

                if len(plate) >= 3:
                    return plate

        return None

    def find_status(self, text_clean: str):
        statuses = []

        if re.search(r"\bperdu de vue\b|\bplus de visuel\b|\bvisuel perdu\b", text_clean):
            statuses.append("Visuel perdu")

        if re.search(r"\bdernier visuel\b|\bdernier visu\b", text_clean):
            statuses.append("Dernier visuel signalé")

        if re.search(r"\bpoursuite en cours\b|\ben poursuite\b", text_clean):
            statuses.append("Poursuite en cours")

        if re.search(r"\baccident\b|\bcrash\b|\bvehicule accidente\b", text_clean):
            statuses.append("Accident signalé")

        if re.search(r"\bvehicule immobilise\b|\bvehicule bloque\b|\bvehicule stoppe\b", text_clean):
            statuses.append("Véhicule immobilisé")

        if re.search(r"\brefus d obtemperer\b", text_clean):
            statuses.append("Refus d'obtempérer")

        return statuses

    def find(self, text: str):
        text_clean = self.clean(text)

        results = []

        people = self.find_people(text_clean)
        weapon = self.find_weapon(text_clean)
        plate = self.find_plate(text_clean)
        statuses = self.find_status(text_clean)

        if people:
            results.append(f"👥 {people}")

        if weapon:
            results.append(f"🔫 {weapon}")

        if plate:
            results.append(f"🔢 Plaque : {plate}")

        for status in statuses:
            results.append(f"⚠️ {status}")

        return results