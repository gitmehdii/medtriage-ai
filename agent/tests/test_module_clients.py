from medtriage_agent.module_clients import _build_fallback_summary


def test_ml_fallback_summary_uses_available_prediction_fields():
    summary = _build_fallback_summary(
        "ml-model",
        {
            "urgence": "orange",
            "score": 0.82,
            "orientation": "Médecin généraliste",
            "delai": "Sous 24h",
        },
    )

    assert summary == "ml-model classe le cas en orange, score 0.82, orientation Médecin généraliste, délai Sous 24h"
