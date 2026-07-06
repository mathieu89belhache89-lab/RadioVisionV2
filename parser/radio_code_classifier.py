class RadioCodeClassifier:
    """Table centrale de logique pour tous les codes radio.

    Objectif : chaque code reconnu reçoit une catégorie, une action et une priorité.
    Comme ça, un code complet ne tombe plus en "Non attribué" par manque de règle.
    """

    UNKNOWN = {
        "category": "unknown",
        "category_label": "Inconnu",
        "action": "display",
        "action_label": "Afficher l’information",
        "priority": "normal",
        "case_kind": None,
        "case_type_label": None,
        "creates_dossier": False,
        "updates_pursuit": False,
        "creates_pursuit": False,
    }

    RULES = {
        # Statuts simples / disponibilité radio.
        "10-0": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Retour poste / statut",
            "priority": "normal",
        },
        "10-1": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "En route",
            "priority": "normal",
        },
        "10-2": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Patrouille",
            "priority": "normal",
        },
        "10-3": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Demande de renfort simple",
            "priority": "medium",
        },
        "10-4": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Message reçu",
            "priority": "normal",
        },
        "10-5": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Négatif",
            "priority": "normal",
        },
        "10-6": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Occupé / en cours",
            "priority": "normal",
        },
        "10-7": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Transfert suspect",
            "priority": "normal",
        },
        "10-20": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Regroupement",
            "priority": "normal",
        },
        "10-29": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "RAS",
            "priority": "normal",
        },

        # Urgences opérationnelles : dossier urgence.
        "10-8": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "critical",
            "case_kind": "urgence",
            "case_type_label": "Fusillade",
            "creates_dossier": True,
        },
        "10-9": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "critical",
            "case_kind": "urgence",
            "case_type_label": "Tirs sur unité",
            "creates_dossier": True,
        },
        "10-99": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "critical",
            "case_kind": "urgence",
            "case_type_label": "Renfort immédiat",
            "creates_dossier": True,
        },
        "CODE 3": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "high",
            "case_kind": "urgence",
            "case_type_label": "Urgence sirène",
            "creates_dossier": True,
        },

        # Départ de poursuite.
        "10-10": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },
        "10-11": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },
        "10-12": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },
        "10-13": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },
        "10-14": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },
        "10-15": {
            "category": "pursuit_start",
            "category_label": "Poursuite",
            "action": "pursuit_start",
            "action_label": "Créer / mettre à jour une poursuite",
            "priority": "high",
            "creates_pursuit": True,
        },

        # Infos liées aux poursuites.
        "10-16": {
            "category": "pursuit_update",
            "category_label": "Mise à jour poursuite",
            "action": "pursuit_update",
            "action_label": "Mettre à jour une poursuite active",
            "priority": "medium",
            "updates_pursuit": True,
        },
        "10-17": {
            "category": "pursuit_update",
            "category_label": "Mise à jour poursuite",
            "action": "pursuit_update",
            "action_label": "Mettre à jour une poursuite active",
            "priority": "medium",
            "updates_pursuit": True,
        },
        "10-19": {
            "category": "pursuit_or_intervention",
            "category_label": "Accident",
            "action": "pursuit_or_case",
            "action_label": "Mettre à jour une poursuite ou créer une intervention",
            "priority": "medium",
            "case_kind": "intervention",
            "case_type_label": "Accident",
            "updates_pursuit": True,
            "creates_dossier": True,
        },

        # Interventions / crimes.
        "10-30": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "medium",
            "case_kind": "intervention",
            "case_type_label": "Risque de braquage",
            "creates_dossier": True,
        },
        "10-31": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "high",
            "case_kind": "intervention",
            "case_type_label": "Braquage confirmé",
            "creates_dossier": True,
        },
        "10-32": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "high",
            "case_kind": "intervention",
            "case_type_label": "Sniper",
            "creates_dossier": True,
        },
        "10-33": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "medium",
            "case_kind": "intervention",
            "case_type_label": "Unité parachutiste",
            "creates_dossier": True,
        },
        "459": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "medium",
            "case_kind": "intervention",
            "case_type_label": "Cambriolage",
            "creates_dossier": True,
        },
        "460": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "high",
            "case_kind": "intervention",
            "case_type_label": "Braquage",
            "creates_dossier": True,
        },
        "461": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "medium",
            "case_kind": "intervention",
            "case_type_label": "Supérette",
            "creates_dossier": True,
        },
        "187": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "critical",
            "case_kind": "intervention",
            "case_type_label": "Homicide",
            "creates_dossier": True,
        },
        "207": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "high",
            "case_kind": "intervention",
            "case_type_label": "Enlèvement",
            "creates_dossier": True,
        },
        "208": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "critical",
            "case_kind": "intervention",
            "case_type_label": "Prise d’otage agent",
            "creates_dossier": True,
        },
        "PO": {
            "category": "intervention",
            "category_label": "Intervention",
            "action": "case",
            "action_label": "Créer / mettre à jour une intervention",
            "priority": "high",
            "case_kind": "intervention",
            "case_type_label": "Prise d’otage",
            "creates_dossier": True,
        },

        # Codes spéciaux.
        "CODE 0": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Problème signalé",
            "priority": "medium",
        },
        "CODE 1": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Appel gouvernement",
            "priority": "medium",
        },
        "CODE 2": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Unité silencieuse",
            "priority": "normal",
        },
        "CODE OD": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "critical",
            "case_kind": "urgence",
            "case_type_label": "Agent à terre",
            "creates_dossier": True,
        },
        "CODE DS": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "medium",
            "case_kind": "urgence",
            "case_type_label": "Suspect neutralisé",
            "creates_dossier": True,
        },
        "CODE DOA": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "high",
            "case_kind": "urgence",
            "case_type_label": "Civil à terre",
            "creates_dossier": True,
        },
        "CODE DCD": {
            "category": "emergency",
            "category_label": "Urgence",
            "action": "case",
            "action_label": "Créer / mettre à jour une urgence",
            "priority": "high",
            "case_kind": "urgence",
            "case_type_label": "Civil décédé",
            "creates_dossier": True,
        },
        "CODE RDP": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Récapitulatif patrouilles",
            "priority": "normal",
        },
        "CODE S": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Silence radio",
            "priority": "high",
        },
        "PDP": {
            "category": "radio_status",
            "category_label": "Statut radio",
            "action": "status",
            "action_label": "Poste de police",
            "priority": "normal",
        },

        # Types / compositions d’unité.
        "MARY": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "HENRY": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "AP": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "CP": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "LINCOLN": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "ADAMS": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "TANGO": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
        "TANGO+": {
            "category": "unit_type",
            "category_label": "Type unité",
            "action": "unit_info",
            "action_label": "Information d’unité",
            "priority": "normal",
        },
    }

    def normalize_code(self, code):
        code = str(code or "").strip().upper()
        return code

    def classify(self, code):
        code = self.normalize_code(code)

        if not code:
            data = dict(self.UNKNOWN)
            data["code"] = None
            return data

        data = dict(self.UNKNOWN)
        data.update(self.RULES.get(code, {}))
        data["code"] = code

        data.setdefault("creates_dossier", False)
        data.setdefault("updates_pursuit", False)
        data.setdefault("creates_pursuit", False)
        data.setdefault("case_kind", None)
        data.setdefault("case_type_label", None)

        return data

    def is_status_only(self, code):
        return self.classify(code).get("action") in {"status", "unit_info"}

    def is_case_code(self, code):
        return self.classify(code).get("creates_dossier") is True

    def is_pursuit_start(self, code):
        return self.classify(code).get("creates_pursuit") is True

    def is_pursuit_update(self, code):
        return self.classify(code).get("updates_pursuit") is True

    def case_config(self, code):
        data = self.classify(code)

        if not data.get("creates_dossier"):
            return None

        return {
            "kind": data.get("case_kind") or "intervention",
            "type_label": data.get("case_type_label") or data.get("category_label") or "Intervention",
            "priority": data.get("priority") or "medium",
            "category": data.get("category"),
            "category_label": data.get("category_label"),
            "action": data.get("action"),
            "action_label": data.get("action_label"),
        }


CLASSIFIER = RadioCodeClassifier()


def classify_code(code):
    return CLASSIFIER.classify(code)


def is_status_only_code(code):
    return CLASSIFIER.is_status_only(code)


def is_case_code(code):
    return CLASSIFIER.is_case_code(code)


def is_pursuit_start_code(code):
    return CLASSIFIER.is_pursuit_start(code)


def is_pursuit_update_code(code):
    return CLASSIFIER.is_pursuit_update(code)


def get_case_config(code):
    return CLASSIFIER.case_config(code)


CASE_CODE_CONFIGS = {
    code: CLASSIFIER.case_config(code)
    for code in CLASSIFIER.RULES
    if CLASSIFIER.case_config(code)
}
