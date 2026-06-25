import os
import json
import joblib
import numpy as np


URGENCE_LABELS = {
    "vert":   {"orientation": "Pharmacie", "delai": "Pas urgent"},
    "orange": {"orientation": "Médecin généraliste", "delai": "Sous 24h"},
    "rouge":  {"orientation": "Urgences / SAMU 15", "delai": "Immédiat"},
}

MAPPING = {
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

model = None
feature_names = None


def init():
    global model, feature_names
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    model = joblib.load(os.path.join(model_dir, "model.pkl"))
    feature_names = joblib.load(os.path.join(model_dir, "feature_names.pkl"))


def run(raw_data):
    data = json.loads(raw_data)
    symptomes = data.get("symptomes", "")

    vector = np.zeros(len(feature_names))
    symptomes_lower = symptomes.lower()
    for fr_symptome, en_features in MAPPING.items():
        if fr_symptome in symptomes_lower:
            for feat in en_features:
                if feat in feature_names:
                    vector[feature_names.index(feat)] = 1

    prediction = model.predict(vector.reshape(1, -1))[0]
    probas = model.predict_proba(vector.reshape(1, -1))[0]
    score = float(max(probas))
    info = URGENCE_LABELS.get(prediction, {})

    return {
        "urgence": prediction,
        "score": round(score, 2),
        "orientation": info.get("orientation", ""),
        "delai": info.get("delai", ""),
    }
