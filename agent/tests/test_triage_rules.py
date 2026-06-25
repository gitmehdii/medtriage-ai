from medtriage_agent.schemas import TriageRequest, UrgencyLevel
from medtriage_agent.triage_rules import default_questions, detect_answered_followups, evaluate_rules


def test_red_flag_chest_pain_is_red():
    request = TriageRequest(symptomes="J'ai une douleur thoracique et du mal à respirer")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.red
    assert signal.confidence == 1.0


def test_high_fever_is_orange():
    request = TriageRequest(symptomes="Fièvre 39°C avec frissons depuis 2 jours")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.orange


def test_coughing_blood_is_red():
    request = TriageRequest(symptomes="Je crache du sang")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.red
    assert "sang dans les crachats" in signal.summary


def test_traumatic_limb_loss_is_red():
    request = TriageRequest(symptomes="J'ai perdu une jambe")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.red
    assert "perte de membre" in signal.summary


def test_abdominal_pain_in_older_patient_is_orange():
    request = TriageRequest(symptomes="Ca fait 1 mois que j'ai mal au ventre et j'ai 60 ans")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.orange
    assert "douleur abdominale" in signal.summary


def test_common_sore_throat_is_yellow():
    request = TriageRequest(symptomes="Mal à la gorge et toux légère")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.yellow


def test_missing_context_generates_follow_up_questions():
    request = TriageRequest(symptomes="J'ai de la fièvre")

    questions = default_questions(request, UrgencyLevel.yellow)

    assert "Quel âge avez-vous ?" in questions
    assert any("Depuis combien de temps" in question for question in questions)


def test_red_urgency_does_not_delay_with_follow_up_questions():
    request = TriageRequest(symptomes="Je crache du sang")

    questions = default_questions(request, UrgencyLevel.red)

    assert questions == []


def test_answered_followups_are_not_repeated():
    request = TriageRequest(
        symptomes="J'ai de la fièvre. J'ai 34 ans et les symptômes sont présents depuis 2 jours.",
        answered_followups=["antecedents", "medications"],
    )

    questions = default_questions(request, UrgencyLevel.yellow)

    assert "Quel âge avez-vous ?" not in questions
    assert "Depuis combien de temps les symptômes sont-ils présents ?" not in questions
    assert "Avez-vous des antécédents médicaux importants ?" not in questions
    assert "Prenez-vous actuellement des médicaments ?" not in questions


def test_short_no_answer_resolves_pending_yes_no_followups():
    answered = detect_answered_followups("non", ["antecedents", "medications"])

    assert answered == {"antecedents", "medications"}
