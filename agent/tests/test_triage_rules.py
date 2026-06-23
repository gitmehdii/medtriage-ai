from medtriage_agent.schemas import TriageRequest, UrgencyLevel
from medtriage_agent.triage_rules import default_questions, evaluate_rules


def test_red_flag_chest_pain_is_red():
    request = TriageRequest(symptomes="J'ai une douleur thoracique et du mal à respirer")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.red
    assert signal.confidence == 1.0


def test_high_fever_is_orange():
    request = TriageRequest(symptomes="Fièvre 39°C avec frissons depuis 2 jours")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.orange


def test_common_sore_throat_is_yellow():
    request = TriageRequest(symptomes="Mal à la gorge et toux légère")

    signal = evaluate_rules(request)

    assert signal.urgency == UrgencyLevel.yellow


def test_missing_context_generates_follow_up_questions():
    request = TriageRequest(symptomes="J'ai de la fièvre")

    questions = default_questions(request, UrgencyLevel.yellow)

    assert "Quel âge avez-vous ?" in questions
    assert any("Depuis combien de temps" in question for question in questions)
