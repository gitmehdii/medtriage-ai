# MedTriageAI — Frontend

Interface React (Vite + Tailwind) pour décrire des symptômes, uploader une photo optionnelle, et afficher le résultat de triage renvoyé par l'agent IA.

## Lancer en dev

```bash
npm install
npm run dev
```

L'app est servie sur **http://localhost:3000**.

## Variables d'environnement

Copier `.env.example` en `.env` et ajuster si besoin :

```bash
VITE_AGENT_URL=http://localhost:8000   # URL de l'agent (endpoint POST /triage)
VITE_USE_MOCK=false                    # true pour simuler la réponse sans l'agent
```

Avec `VITE_USE_MOCK=true`, l'app répond avec une réponse simulée (vert/orange/rouge selon des mots-clés dans le texte des symptômes) sans appeler l'agent.

## Build

```bash
npm run build
npm run preview
```

## Docker

Le `Dockerfile` build l'app avec Vite puis la sert via nginx sur le port 3000 
