# Vision — Azure Computer Vision

Analyse une photo et retourne une description + niveau de gravité médicale.

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
# Remplis AZURE_KEY et AZURE_ENDPOINT dans le fichier .env
```

## Lancer l'API

```bash
python app.py
# API disponible sur http://localhost:8001
```

## Endpoint

### POST /vision/analyze

**Input :**
```json
{
  "image_base64": "..."
}
```

**Output :**
```json
{
  "description": "a red rash on the arm",
  "tags": ["skin", "redness", "arm"],
  "gravite": "moderee"
}
```

Valeurs possibles pour `gravite` : `faible`, `moderee`, `elevee`

## Tester

```bash
python test.py
```
