import { useRef } from 'react'

export default function PhotoUpload({ previewUrl, onSelect, onRemove }) {
  const inputRef = useRef(null)

  function handleChange(e) {
    const file = e.target.files?.[0]
    if (file) onSelect(file)
  }

  if (previewUrl) {
    return (
      <div className="relative inline-block">
        <img
          src={previewUrl}
          alt="Aperçu de la photo"
          className="h-32 w-32 rounded-xl object-cover ring-1 ring-slate-200"
        />
        <button
          type="button"
          onClick={onRemove}
          aria-label="Retirer la photo"
          className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-white text-slate-500 shadow ring-1 ring-slate-200 transition hover:bg-slate-50 hover:text-slate-700"
        >
          ✕
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="flex items-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-600 transition hover:border-teal-400 hover:bg-teal-50 hover:text-teal-700"
      >
        <span aria-hidden>📷</span>
        Ajouter une photo (optionnel)
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
      />
    </div>
  )
}
