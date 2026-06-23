import os
import joblib
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# Charger le modèle et les features au démarrage
model = joblib.load("model.pkl")
feature_names = joblib.load("feature_names.pkl")

URGENCE_LABELS = {
    "vert":   {"orientation": "Pharmacie", "delai": "Pas urgent"},
    "orange": {"orientation": "Médecin généraliste", "delai": "Sous 24h"},
    "rouge":  {"orientation": "Urgences / SAMU 15", "delai": "Immédiat"},
}


def symptomes_to_vector(symptomes_text):
    """Convertit un texte de symptômes en vecteur binaire pour le modèle."""
    vector = np.zeros(len(feature_names))
    symptomes_lower = symptomes_text.lower()

    # Mapping français -> noms de features anglais
    mapping = {
        "fièvre": ["high_fever", "mild_fever"],
        "toux": ["cough"],
        "fatigue": ["fatigue"],
        "maux de tête": ["headache"],
        "mal de tête": ["headache"],
        "douleur poitrine": ["chest_pain"],
        "essoufflement": ["breathlessness"],
        "vomissements": ["vomiting"],
        "nausées": ["nausea"],
        "diarrhée": ["diarrhoea"],
        "frissons": ["chills", "shivering"],
        "douleur abdominale": ["abdominal_pain", "stomach_pain"],
        "éruption": ["skin_rash"],
        "démangeaisons": ["itching"],
        "vertiges": ["dizziness"],
        "perte de conscience": ["coma", "altered_sensorium"],
        "convulsions": ["coma"],
        "saignement": ["bloody_stool"],
        "brûlure": ["burning_micturition"],
        "mal de gorge": ["patches_in_throat"],
        "douleur musculaire": ["muscle_pain"],
        "raideur nuque": ["stiff_neck"],
        "palpitations": ["palpitations"],
        "perte appétit": ["loss_of_appetite"],
        "sudation": ["sweating"],
        "jaunisse": ["yellowish_skin"],
        "urine foncée": ["dark_urine"],
    }

    for fr_symptome, en_features in mapping.items():
        if fr_symptome in symptomes_lower:
            for feat in en_features:
                if feat in feature_names:
                    idx = feature_names.index(feat)
                    vector[idx] = 1

    return vector


@app.route("/ml/predict", methods=["POST"])
def predict():
    data = request.get_json()

    if not data or "symptomes" not in data:
        return jsonify({"error": "Champ symptomes manquant"}), 400

    try:
        symptomes = data["symptomes"]
        vector = symptomes_to_vector(symptomes)
        vector_2d = vector.reshape(1, -1)

        prediction = model.predict(vector_2d)[0]
        probas = model.predict_proba(vector_2d)[0]
        score = float(max(probas))

        info = URGENCE_LABELS.get(prediction, {})

        return jsonify({
            "urgence": prediction,
            "score": round(score, 2),
            "orientation": info.get("orientation", ""),
            "delai": info.get("delai", ""),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002, debug=True)
