import requests

tests = [
    "fièvre frissons maux de tête sudation",
    "douleur poitrine essoufflement palpitations",
    "toux fatigue démangeaisons éruption",
]

for symptomes in tests:
    response = requests.post(
        "http://localhost:8002/ml/predict",
        json={"symptomes": symptomes}
    )
    result = response.json()
    print(f"Symptomes : {symptomes[:40]}")
    print(f"  Urgence    : {result['urgence']}")
    print(f"  Score      : {result['score']}")
    print(f"  Orientation: {result['orientation']}")
    print(f"  Delai      : {result['delai']}")
    print()
