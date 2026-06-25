const AGENT_URL = import.meta.env.VITE_AGENT_URL || 'http://localhost:8000'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const LEVEL_KEYWORDS = {
  red: ['rouge', 'grave', 'urgence vitale', 'inconscient', 'ne respire plus'],
  orange: ['fièvre', 'fievre', 'douleur intense', 'saignement'],
  yellow: ['toux', 'fatigue', 'depuis quelques jours', 'léger', 'leger'],
}

function detectLevel(message) {
  const text = message.toLowerCase()
  for (const level of ['red', 'orange', 'yellow']) {
    if (LEVEL_KEYWORDS[level].some((keyword) => text.includes(keyword))) {
      return level
    }
  }
  return 'green'
}

const MOCK_FINAL_BY_LEVEL = {
  red: {
    orientation: 'Urgences / appeler le 15',
    delai: 'immédiat',
    conseils: [
      'Appelez le 15 (SAMU) sans attendre',
      'Restez au calme et ne vous déplacez pas seul si possible',
    ],
    message: "Vos symptômes nécessitent une prise en charge immédiate.",
  },
  orange: {
    orientation: 'Médecin généraliste',
    delai: 'sous 24h',
    conseils: ['Boire beaucoup d’eau', 'Prendre du paracétamol si besoin'],
    message: 'Une consultation rapide est recommandée.',
  },
  yellow: {
    orientation: 'Surveillance à domicile, médecin si aggravation',
    delai: 'sous 48h si pas d’amélioration',
    conseils: ['Reposez-vous', "Surveillez l'évolution des symptômes"],
    message: 'Vos symptômes demandent une simple surveillance pour le moment.',
  },
  green: {
    orientation: 'Pharmacie / repos à domicile',
    delai: 'sans urgence',
    conseils: ['Reposez-vous', 'Consultez un médecin si les symptômes persistent plus de 3 jours'],
    message: "Rien d'inquiétant à ce stade.",
  },
}

const MOCK_CONVERSATIONS = new Map()

function mockChat({ message, conversationId }) {
  const isFirstTurn = !conversationId
  const id = conversationId || crypto.randomUUID()

  let level
  if (isFirstTurn) {
    level = detectLevel(message)
    MOCK_CONVERSATIONS.set(id, level)
  } else {
    level = MOCK_CONVERSATIONS.get(id) || detectLevel(message)
  }

  const final = MOCK_FINAL_BY_LEVEL[level]

  const response = isFirstTurn
    ? {
        conversation_id: id,
        urgence: level,
        orientation: final.orientation,
        delai: final.delai,
        conseils: [],
        questions_complementaires: [
          'Depuis combien de temps avez-vous ces symptômes ?',
          'Avez-vous de la fièvre ?',
        ],
        justification: `Premier niveau estimé à partir des mots-clés détectés dans : "${message}".`,
        message: 'Pour affiner mon évaluation, pouvez-vous préciser quelques points ?',
        disclaimer_medical:
          "Cet outil ne remplace pas un avis médical. En cas d'urgence vitale, appelez le 15.",
        signals: [],
      }
    : {
        conversation_id: id,
        urgence: level,
        orientation: final.orientation,
        delai: final.delai,
        conseils: final.conseils,
        questions_complementaires: [],
        justification: `Niveau ${level} confirmé après vos précisions.`,
        message: final.message,
        disclaimer_medical:
          "Cet outil ne remplace pas un avis médical. En cas d'urgence vitale, appelez le 15.",
        signals: [],
      }

  return new Promise((resolve) => setTimeout(() => resolve(response), 800))
}

export async function submitChat({ message, photoBase64, conversationId }) {
  if (USE_MOCK) {
    return mockChat({ message, conversationId })
  }

  const response = await fetch(`${AGENT_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history: [],
      photo_base64: photoBase64 ?? null,
      conversation_id: conversationId ?? null,
    }),
  })

  if (!response.ok) {
    throw new Error(`Erreur agent (${response.status})`)
  }

  return response.json()
}
