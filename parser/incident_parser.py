import re
import unicodedata


class IncidentParser:

    MAX_PEOPLE_COUNT = 8

    NUMBER_WORDS = {
        "un": 1,
        "une": 1,
        "deux": 2,
        "trois": 3,
        "quatre": 4,
        "cinq": 5,
        "six": 6,
        "sept": 7,
        "huit": 8,
    }

    def clean(self, text: str) -> str:
        text = text.lower()

        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text
            if unicodedata.category(c) != "Mn"
        )

        replacements = {
            "pour suite": "poursuite",
            "pour suites": "poursuite",

            "a pcie": "a pied",
            "a pie": "a pied",
            "a pieds": "a pied",
            "en fuite a pcie": "en fuite a pied",
            "individu en fuite": "individu a pied",
            "suspect en fuite": "suspect a pied",

            "poisons de renfort": "besoin de renfort",
            "besoins de renfort": "besoin de renfort",
            "besoin d un renfort": "besoin de renfort",

            "coup de feu": "coups de feu",
            "coups de feux": "coups de feu",

            "supermiss": "suspect",
            "super mis": "suspect",
            "sus permis": "suspect",

            "suspect armer": "suspect arme",
            "suspect arme": "suspect arme",
            "individu armer": "individu arme",
            "individu arme": "individu arme",

            "agent pris en hotel": "agent pris en otage",
            "pris en hotel": "pris en otage",
            "agent prit en otage": "agent pris en otage",
            "pris en otages": "pris en otage",
            "prise otage": "prise d otage",
        }

        for bad, good in replacements.items():
            text = text.replace(bad, good)

        text = text.replace("-", " ")
        text = text.replace("'", " ")
        text = re.sub(r"[^a-z0-9 ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def add_unique(self, results, value):
        if value and value not in results:
            results.append(value)

    def is_valid_people_count(self, count):
        if count is None:
            return False

        if count < 1:
            return False

        if count > self.MAX_PEOPLE_COUNT:
            return False

        return True

    def find_people(self, text_clean: str):
        patterns = [
            r"\b(\d{1,2})\s+(individus|individu|personnes|personne|occupants|occupant|suspects|suspect)\b",
            r"\b(un|une|deux|trois|quatre|cinq|six|sept|huit)\s+(individus|individu|personnes|personne|occupants|occupant|suspects|suspect)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if not match:
                continue

            value = match.group(1)

            if value.isdigit():
                count = int(value)
            else:
                count = self.NUMBER_WORDS.get(value)

            if self.is_valid_people_count(count):
                return f"👥 {count} individu(s) à bord"

        if re.search(
            r"\bconducteur seul\b|\bseul a bord\b|\bun seul individu\b|\bune seule personne\b",
            text_clean
        ):
            return "👥 1 individu à bord"

        return None

    def find_weapon(self, text_clean: str):
        if re.search(r"\barme visible\b|\barme apercue\b", text_clean):
            return "🔫 Arme visible"

        if re.search(
            r"\bindividu arme\b|\bindividus armes\b|\bsuspect arme\b|\bsuspects armes\b",
            text_clean
        ):
            return "🔫 Individu armé"

        if re.search(r"\barme de poing\b|\bpistolet\b|\brevolver\b", text_clean):
            return "🔫 Arme de poing"

        if re.search(
            r"\bfusil\b|\barme lourde\b|\bak\b|\bkalash\b|\bcarabine\b",
            text_clean
        ):
            return "🔫 Arme longue / lourde"

        if re.search(r"\bcouteau\b|\barme blanche\b", text_clean):
            return "🔪 Arme blanche"

        return None

    def find_hostage(self, text_clean: str):
        if re.search(
            r"\botage\b|\botages\b|\bprise d otage\b|\bpris en otage\b|\bprise en otage\b|\bagent pris en otage\b",
            text_clean,
        ):
            return "🧍 Otage signalé"

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
            "vehicule",
            "voiture",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_clean)

            if match:
                plate = match.group(1).strip()

                for word in stop_words:
                    plate = plate.split(word)[0].strip()

                plate = re.sub(r"\s+", "", plate).upper()

                if len(plate) >= 3:
                    return f"🔢 Plaque : {plate}"

        return None

    def find_pursuit_statuses(self, text_clean: str):
        statuses = []

        if re.search(
            r"\bpoursuite en cours\b|\ben poursuite\b|\bpoursuite active\b|\btoujours en poursuite\b",
            text_clean
        ):
            self.add_unique(statuses, "🚓 Poursuite en cours")

        if re.search(
            r"\bdernier visuel\b|\bdernier visu\b|\bun des visuels\b|\bvisuel vers\b|\bcontact visuel\b",
            text_clean
        ):
            self.add_unique(statuses, "👁️ Visuel signalé")

        if re.search(
            r"\bperdu de vue\b|\bplus de visuel\b|\bvisuel perdu\b|\baucun visuel\b",
            text_clean
        ):
            self.add_unique(statuses, "⚠️ Visuel perdu")

        if re.search(
            r"\bvehicule immobilise\b|\bvehicule bloque\b|\bvehicule stoppe\b|\bvehicule arrete\b",
            text_clean
        ):
            self.add_unique(statuses, "🛑 Véhicule immobilisé")

        if re.search(
            r"\baccident\b|\bcrash\b|\bvehicule accidente\b|\ba percute\b|\bcollision\b",
            text_clean
        ):
            self.add_unique(statuses, "💥 Accident signalé")

        if re.search(
            r"\bfuite a pied\b|\bpart a pied\b|\bindividu a pied\b|\bsuspect a pied\b|\bcontinue a pied\b",
            text_clean
        ):
            self.add_unique(statuses, "🏃 Fuite à pied")

        if re.search(
            r"\bindividu interpelle\b|\bsuspect interpelle\b|\binterpellation\b|\bindividu menotte\b|\bsuspect menotte\b",
            text_clean
        ):
            self.add_unique(statuses, "✅ Interpellation")

        if re.search(
            r"\brenfort demande\b|\bdemande renfort\b|\bbesoin de renfort\b|\bbesoin d un renfort\b|\bbackup\b",
            text_clean
        ):
            self.add_unique(statuses, "🚨 Renfort demandé")

        if re.search(
            r"\brefus d obtemperer\b|\brefus d obtempere\b|\brefus obtemperer\b",
            text_clean
        ):
            self.add_unique(statuses, "⚠️ Refus d'obtempérer")

        if re.search(
            r"\btirs\b|\bcoups de feu\b|\btire dessus\b|\bnous tire dessus\b|\bprise de tir\b",
            text_clean
        ):
            self.add_unique(statuses, "🚨 Coups de feu")

        return statuses

    def find(self, text: str):
        text_clean = self.clean(text)

        results = []

        people = self.find_people(text_clean)
        weapon = self.find_weapon(text_clean)
        hostage = self.find_hostage(text_clean)
        plate = self.find_plate(text_clean)
        statuses = self.find_pursuit_statuses(text_clean)

        self.add_unique(results, people)
        self.add_unique(results, weapon)
        self.add_unique(results, hostage)
        self.add_unique(results, plate)

        for status in statuses:
            self.add_unique(results, status)

        return results