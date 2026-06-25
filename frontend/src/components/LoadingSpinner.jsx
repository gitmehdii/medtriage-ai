export default function LoadingSpinner({ label = 'Analyse en cours...' }) {
  return (
    <div className="flex items-center justify-center gap-3 py-6 text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-teal-500" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}
