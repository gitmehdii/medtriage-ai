# ML Model — Classification de symptômes

Prédit le niveau d'urgence médicale à partir de symptômes en texte libre.

## Fichiers nécessaires

Mettre dans ce dossier :
- `model.pkl` — modèle entraîné sur Azure ML
- `feature_names.pkl` — liste des features

## Installation

```bash
pip install -r requirements.txt
```

## Lancer l'API

```bash
python3 app.py
# API disponible sur http://localhost:8002
```

## Endpoint

### POST /ml/predict

**Input :**
```json
{
  "symptomes": "fièvre frissons maux de tête"
}
```

**Output :**
```json
{
  "urgence": "orange",
  "score": 0.87,
  "orientation": "Médecin généraliste",
  "delai": "Sous 24h"
}
```

## Tester

```bash
python3 test.py
```
