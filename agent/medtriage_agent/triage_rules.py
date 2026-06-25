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
    r"\bcrache(?:r)? du sang\b": "sang dans les crachats",
    r"\bcrachats? sanguinolents?\b": "sang dans les crachats",
    r"\bhemoptysie\b": "hémoptysie",
    r"\bperte de connaissance\b": "perte de connaissance",
    r"\bmalaise grave\b": "malaise grave",
    r"\bparalysie\b": "signe neurologique brutal",
    r"\bvisage deforme\b": "signe possible d'AVC",
    r"\bsaignement abondant\b": "saignement abondant",
    r"\bhemorragie\b": "hémorragie",
    r"\b(?:perdu|arrache|sectionne)\s+(?:une?\s+)?(?:jambe|bras|main|pied|membre)\b": "traumatisme majeur avec perte de membre",
    r"\bamputation\b": "amputation traumatique",
    r"\bmembre sectionne\b": "membre sectionné",
    r"\braideur de nuque\b": "fièvre avec raideur de nuque",
    r"\bconvulsion\b": "convulsion",
}

ORANGE_FLAGS = {
    r"\bfievre\b.*\b(40|41)\b": "fièvre très élevée",
    r"\b39\b.*\bfievre\b|\bfievre\b.*\b39\b": "fièvre élevée",
    r"\bdeshydrat": "signe possible de déshydratation",
    r"\bplaie profonde\b": "plaie profonde",
    r"\bdouleur intense\b": "douleur intense",
    r"\b(?:mal au ventre|douleur abdominale|douleur au ventre)\b.*\b(?:60|6[1-9]|[7-9][0-9])\s*ans\b": "douleur abdominale persistante chez une personne âgée",
    r"\b(?:60|6[1-9]|[7-9][0-9])\s*ans\b.*\b(?:mal au ventre|douleur abdominale|douleur au ventre)\b": "douleur abdominale persistante chez une personne âgée",
    r"\bessoufflement\b": "essoufflement",
}

YELLOW_FLAGS = {
    r"\bfievre\b": "fièvre",
    r"\bfrissons\b": "frissons",
    r"\btoux\b": "toux",
    r"\bmal a la gorge\b": "mal de gorge",
    r"\bmal au ventre\b": "douleur abdominale",
    r"\bdouleur abdominale\b": "douleur abdominale",
    r"\bdouleur au ventre\b": "douleur abdominale",
    r"\bvomissement": "vomissements",
    r"\bdiarrhee\b": "diarrhée",
    r"\brougeur\b": "rougeur",
}

FOLLOWUP_QUESTIONS = {
    "age": "Quel âge avez-vous ?",
    "duration": "Depuis combien de temps les symptômes sont-ils présents ?",
    "antecedents": "Avez-vous des antécédents médicaux importants ?",
    "medications": "Prenez-vous actuellement des médicaments ?",
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
    if urgency is UrgencyLevel.red:
        return []

    questions: list[str] = []
    text = normalize_text(request.symptomes)
    answered_followups = set(request.answered_followups)
    answered_followups.update(detect_answered_followups(request.symptomes))

    if request.age is None and "age" not in answered_followups:
        questions.append(FOLLOWUP_QUESTIONS["age"])
    if "duration" not in answered_followups and not _has_duration_answer(text):
        questions.append(FOLLOWUP_QUESTIONS["duration"])
    if (
        urgency in {UrgencyLevel.yellow, UrgencyLevel.orange}
        and not request.antecedents
        and "antecedents" not in answered_followups
    ):
        questions.append(FOLLOWUP_QUESTIONS["antecedents"])
    if (
        urgency in {UrgencyLevel.yellow, UrgencyLevel.orange}
        and not request.medicaments
        and "medications" not in answered_followups
    ):
        questions.append(FOLLOWUP_QUESTIONS["medications"])

    return questions[:3]


def followup_key_for_question(question: str) -> str | None:
    normalized_question = normalize_text(question)
    for key, expected_question in FOLLOWUP_QUESTIONS.items():
        if normalize_text(expected_question) == normalized_question:
            return key
    return None


def detect_answered_followups(text: str, pending_followups: list[str] | None = None) -> set[str]:
    normalized = normalize_text(text)
    answered: set[str] = set()

    if _has_age_answer(normalized):
        answered.add("age")
    if _has_duration_answer(normalized):
        answered.add("duration")
    if _has_antecedents_answer(normalized):
        answered.add("antecedents")
    if _has_medications_answer(normalized):
        answered.add("medications")

    pending = set(pending_followups or [])
    if pending:
        if "age" in pending and _looks_like_age_only(normalized):
            answered.add("age")
        if "duration" in pending and _looks_like_duration_only(normalized):
            answered.add("duration")

        yes_no_pending = pending & {"antecedents", "medications"}
        if yes_no_pending and _is_short_yes_no_answer(normalized):
            answered.update(yes_no_pending)

    return answered


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


def _has_age_answer(text: str) -> bool:
    return bool(
        re.search(r"\b(?:j'?ai|age|agee?|age de)\D{0,12}\d{1,3}\s*ans\b", text)
        or re.search(r"\bage\s*:?\s*\d{1,3}\b", text)
    )


def _has_duration_answer(text: str) -> bool:
    return bool(
        "depuis" in text
        or "hier" in text
        or "ce matin" in text
        or "cette nuit" in text
        or re.search(r"\b(?:ca|cela)\s+fait\b", text)
        or re.search(r"\b\d+\s*(?:h|heure|heures|jour|jours|semaine|semaines|mois)\b", text)
    )


def _has_antecedents_answer(text: str) -> bool:
    if re.search(r"\bantecedents?\b", text):
        return True
    return bool(
        re.search(r"\b(?:diabete|asthme|hypertension|cardiaque|epilepsie|immunodeprime)\b", text)
        or re.search(r"\b(?:pas|aucun|aucune|sans)\s+(?:d[' ]?)?antecedents?\b", text)
    )


def _has_medications_answer(text: str) -> bool:
    if re.search(r"\b(?:medicaments?|traitements?)\b", text):
        return True
    return bool(re.search(r"\b(?:paracetamol|doliprane|ibuprofene|antibiotique|anticoagulant)\b", text))


def _looks_like_age_only(text: str) -> bool:
    return bool(re.fullmatch(r"(?:j'?ai\s*)?\d{1,3}\s*ans", text))


def _looks_like_duration_only(text: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:depuis\s*)?(?:\d+\s*(?:h|heure|heures|jour|jours|semaine|semaines|mois)|hier|ce matin|cette nuit)",
            text,
        )
    )


def _is_short_yes_no_answer(text: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:oui|non|non merci|pas a ma connaissance|aucun|aucune|rien|je ne sais pas|je sais pas)",
            text,
        )
    )
