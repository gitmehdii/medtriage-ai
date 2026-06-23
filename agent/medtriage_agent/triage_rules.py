import re
import unicodedata

from medtriage_agent.schemas import ModuleSignal, TriageRequest, UrgencyLevel


DISCLAIMER = (
    "Cet assistant ne remplace pas un avis médical. En cas de doute, "
    "d'aggravation rapide ou de symptôme inquiétant, contactez le 15 ou le 112."
)


RED_FLAGS = {
    r"\bdouleur thoracique\b": "douleur thoracique",
    r"\boppression thoracique\b": "oppression thoracique",
    r"\bdifficulte a respirer\b": "difficulté respiratoire",
    r"\bdetresse respiratoire\b": "détresse respiratoire",
    r"\bperte de connaissance\b": "perte de connaissance",
    r"\bmalaise grave\b": "malaise grave",
    r"\bparalysie\b": "signe neurologique brutal",
    r"\bvisage deforme\b": "signe possible d'AVC",
    r"\bsaignement abondant\b": "saignement abondant",
    r"\bhemorragie\b": "hémorragie",
    r"\braideur de nuque\b": "fièvre avec raideur de nuque",
    r"\bconvulsion\b": "convulsion",
}

ORANGE_FLAGS = {
    r"\bfievre\b.*\b(40|41)\b": "fièvre très élevée",
    r"\b39\b.*\bfievre\b|\bfievre\b.*\b39\b": "fièvre élevée",
    r"\bdeshydrat": "signe possible de déshydratation",
    r"\bplaie profonde\b": "plaie profonde",
    r"\bdouleur intense\b": "douleur intense",
    r"\bessoufflement\b": "essoufflement",
}

YELLOW_FLAGS = {
    r"\bfievre\b": "fièvre",
    r"\bfrissons\b": "frissons",
    r"\btoux\b": "toux",
    r"\bmal a la gorge\b": "mal de gorge",
    r"\bvomissement": "vomissements",
    r"\bdiarrhee\b": "diarrhée",
    r"\brougeur\b": "rougeur",
}


def normalize_text(value: str) -> str:
    lowered = value.lower()
    without_accents = "".join(
        char for char in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_accents).strip()


def evaluate_rules(request: TriageRequest) -> ModuleSignal:
    text = normalize_text(request.symptomes)

    red_matches = _collect_matches(text, RED_FLAGS)
    if red_matches:
        return ModuleSignal(
            source="rules",
            urgency=UrgencyLevel.red,
            confidence=1.0,
            summary="Drapeau rouge détecté: " + ", ".join(red_matches),
        )

    orange_matches = _collect_matches(text, ORANGE_FLAGS)
    if orange_matches:
        return ModuleSignal(
            source="rules",
            urgency=UrgencyLevel.orange,
            confidence=0.85,
            summary="Signal de gravité modérée détecté: " + ", ".join(orange_matches),
        )

    yellow_matches = _collect_matches(text, YELLOW_FLAGS)
    if yellow_matches:
        return ModuleSignal(
            source="rules",
            urgency=UrgencyLevel.yellow,
            confidence=0.7,
            summary="Symptômes nécessitant une surveillance: " + ", ".join(yellow_matches),
        )

    return ModuleSignal(
        source="rules",
        urgency=UrgencyLevel.green,
        confidence=0.55,
        summary="Aucun signal de gravité immédiate détecté par les règles.",
    )


def default_questions(request: TriageRequest, urgency: UrgencyLevel) -> list[str]:
    questions: list[str] = []
    text = normalize_text(request.symptomes)

    if request.age is None:
        questions.append("Quel âge avez-vous ?")
    if "depuis" not in text and not re.search(r"\b\d+\s*(h|heure|jour|jours|semaine)", text):
        questions.append("Depuis combien de temps les symptômes sont-ils présents ?")
    if urgency in {UrgencyLevel.yellow, UrgencyLevel.orange} and not request.antecedents:
        questions.append("Avez-vous des antécédents médicaux importants ?")
    if urgency in {UrgencyLevel.yellow, UrgencyLevel.orange} and not request.medicaments:
        questions.append("Prenez-vous actuellement des médicaments ?")

    return questions[:3]


def advice_for(urgency: UrgencyLevel) -> tuple[str, str, list[str]]:
    if urgency is UrgencyLevel.red:
        return (
            "urgence vitale ou potentiellement vitale",
            "immédiatement",
            [
                "Appelez le 15 ou le 112 maintenant.",
                "Ne conduisez pas vous-même.",
                "Restez accompagné si possible en attendant les secours.",
            ],
        )
    if urgency is UrgencyLevel.orange:
        return (
            "avis médical rapide",
            "dans les 24 heures, plus tôt si aggravation",
            [
                "Contactez un médecin ou un service de soins non programmés.",
                "Surveillez l'évolution des symptômes.",
                "Appelez le 15 ou le 112 si l'état se dégrade.",
            ],
        )
    if urgency is UrgencyLevel.yellow:
        return (
            "médecin généraliste ou téléconsultation",
            "dans les 24 à 48 heures si les symptômes persistent",
            [
                "Hydratez-vous régulièrement.",
                "Reposez-vous et surveillez la température.",
                "Demandez un avis médical si les symptômes persistent ou s'aggravent.",
            ],
        )
    return (
        "auto-surveillance ou pharmacie",
        "surveillance à domicile",
        [
            "Surveillez l'apparition de nouveaux symptômes.",
            "Demandez conseil à un pharmacien si nécessaire.",
            "Consultez si les symptômes persistent ou s'aggravent.",
        ],
    )


def _collect_matches(text: str, patterns: dict[str, str]) -> list[str]:
    return [label for pattern, label in patterns.items() if re.search(pattern, text)]
