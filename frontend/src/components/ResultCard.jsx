const URGENCE_STYLES = {
  vert: {
    label: 'Non urgent',
    card: 'border-emerald-200 bg-emerald-50',
    badge: 'bg-emerald-600 text-white',
    icon: '🟢',
  },
  orange: {
    label: 'Consultation à prévoir',
    card: 'border-amber-200 bg-amber-50',
    badge: 'bg-amber-500 text-white',
    icon: '🟠',
  },
  rouge: {
    label: 'Urgence',
    card: 'border-red-200 bg-red-50',
    badge: 'bg-red-600 text-white',
    icon: '🔴',
  },
}

export default function ResultCard({ result }) {
  const style = URGENCE_STYLES[result.urgence] ?? URGENCE_STYLES.vert

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
    </div>
  )
}
