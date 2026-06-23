import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import base64

load_dotenv()

app = Flask(__name__)

AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")


def analyze_image_bytes(image_bytes):
    url = f"{AZURE_ENDPOINT}/computervision/imageanalysis:analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/octet-stream"
    }
    params = {
        "api-version": "2024-02-01",
        "features": "caption,tags"
    }

    response = requests.post(url, headers=headers, params=params, data=image_bytes)
    print("Status:", response.status_code)
    print("Response:", response.text)  # Ajoute cette ligne
    response.raise_for_status()
    return response.json()


def parse_result(raw):
    caption = raw.get("captionResult", {}).get("text", "Aucune description")
    tags = [t["name"] for t in raw.get("tagsResult", {}).get("values", [])[:5]]

    # Mots clés médicaux pour estimer la gravité
    urgent_keywords = ["wound", "blood", "injury", "cut", "burn", "bruise", "swelling"]
    moderate_keywords = ["rash", "redness", "skin", "inflammation"]

    all_tags = " ".join(tags).lower() + " " + caption.lower()

    if any(k in all_tags for k in urgent_keywords):
        gravite = "elevee"
    elif any(k in all_tags for k in moderate_keywords):
        gravite = "moderee"
    else:
        gravite = "faible"

    return {
        "description": caption,
        "tags": tags,
        "gravite": gravite
    }


@app.route("/vision/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    if not data or "image_base64" not in data:
        return jsonify({"error": "Champ image_base64 manquant"}), 400

    try:
        image_bytes = base64.b64decode(data["image_base64"])
        raw = analyze_image_bytes(image_bytes)
        result = parse_result(raw)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)