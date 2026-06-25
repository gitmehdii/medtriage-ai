const AGENT_URL = import.meta.env.VITE_AGENT_URL || 'http://localhost:8000'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

const MOCK_RESPONSES = {
  rouge: {
    urgence: 'rouge',
    orientation: 'Urgences / appeler le 15',
    delai: 'immédiat',
    conseils: [
      'Appelez le 15 (SAMU) sans attendre',
      'Restez au calme et ne vous déplacez pas seul si possible',
      "Préparez la liste des symptômes et l'heure de leur apparition",
    ],
  },
  orange: {
    urgence: 'orange',
    orientation: 'Médecin généraliste',
    delai: 'sous 24h',
    conseils: [
      'Boire beaucoup d’eau',
      'Prendre du paracétamol si besoin',
      'Surveiller l’évolution des symptômes',
    ],
  },
  vert: {
    urgence: 'vert',
    orientation: 'Pharmacie / repos à domicile',
    delai: 'sans urgence',
    conseils: ['Reposez-vous', "Surveillez l'évolution", 'Consultez un médecin si les symptômes persistent plus de 3 jours'],
  },
}

function mockTriage(symptomes) {
  const text = symptomes.toLowerCase()
  let level = 'vert'
  if (text.includes('rouge') || text.includes('grave') || text.includes('urgence')) {
    level = 'rouge'
  } else if (text.includes('fièvre') || text.includes('fievre') || text.includes('douleur')) {
    level = 'orange'
  }
  return new Promise((resolve) => {
    setTimeout(() => resolve(MOCK_RESPONSES[level]), 1000)
  })
}

export async function submitTriage({ symptomes, photoBase64 }) {
  if (USE_MOCK) {
    return mockTriage(symptomes)
  }

  const response = await fetch(`${AGENT_URL}/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symptomes,
      photo_base64: photoBase64 || '',
    }),
  })

  if (!response.ok) {
    throw new Error(`Erreur agent (${response.status})`)
  }

  return response.json()
}
