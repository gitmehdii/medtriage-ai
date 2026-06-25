export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-xl border border-red-100 bg-red-50 p-4 text-red-700 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm font-medium">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="shrink-0 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
      >
        Réessayer
      </button>
    </div>
  )
}
