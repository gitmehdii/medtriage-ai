const URGENCE_STYLES = {
  green: {
    label: 'Non urgent',
    card: 'border-emerald-200 bg-emerald-50',
    badge: 'bg-emerald-600 text-white',
    icon: '🟢',
  },
  yellow: {
    label: 'Vigilance',
    card: 'border-yellow-200 bg-yellow-50',
    badge: 'bg-yellow-500 text-white',
    icon: '🟡',
  },
  orange: {
    label: 'Consultation à prévoir',
    card: 'border-amber-200 bg-amber-50',
    badge: 'bg-amber-500 text-white',
    icon: '🟠',
  },
  red: {
    label: 'Urgence',
    card: 'border-red-200 bg-red-50',
    badge: 'bg-red-600 text-white',
    icon: '🔴',
  },
}

export default function ResultCard({ result }) {
  const style = URGENCE_STYLES[result.urgence] ?? URGENCE_STYLES.green
  const hasOpenQuestions = result.questions_complementaires?.length > 0

  return (
    <div className={`rounded-2xl border p-6 shadow-sm ${style.card}`}>
      <div
        className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-semibold ${style.badge}`}
      >
        <span aria-hidden>{style.icon}</span>
        {style.label}
      </div>

      <dl className="mt-5 grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Orientation
          </dt>
          <dd className="mt-1 text-base font-medium text-slate-800">{result.orientation}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Délai</dt>
          <dd className="mt-1 text-base font-medium text-slate-800">{result.delai}</dd>
        </div>
      </dl>

      {result.conseils?.length > 0 && (
        <div className="mt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Conseils
          </h3>
          <ul className="mt-2 space-y-1.5">
            {result.conseils.map((conseil, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-slate-400" aria-hidden>
                  •
                </span>
                {conseil}
              </li>
            ))}
          </ul>
        </div>
      )}

      {hasOpenQuestions && (
        <div className="mt-5 rounded-xl bg-white/70 p-4 ring-1 ring-slate-200">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Pour affiner l'évaluation
          </h3>
          <ul className="mt-2 space-y-1.5">
            {result.questions_complementaires.map((question, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-0.5 text-slate-400" aria-hidden>
                  •
                </span>
                {question}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.justification && (
        <details className="mt-5 text-sm text-slate-600">
          <summary className="cursor-pointer font-medium text-slate-500 hover:text-slate-700">
            Voir la justification
          </summary>
          <p className="mt-2 leading-relaxed">{result.justification}</p>
        </details>
      )}
    </div>
  )
}
