import { useState } from 'react'
import PhotoUpload from './PhotoUpload'

export default function SymptomForm({ onSubmit, isLoading }) {
  const [symptomes, setSymptomes] = useState('')
  const [photoFile, setPhotoFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)

  function handleSelectPhoto(file) {
    setPhotoFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  function handleRemovePhoto() {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPhotoFile(null)
    setPreviewUrl(null)
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!symptomes.trim() || isLoading) return
    onSubmit({ symptomes: symptomes.trim(), photoFile })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label htmlFor="symptomes" className="mb-2 block text-sm font-semibold text-slate-700">
          Décrivez vos symptômes
        </label>
        <textarea
          id="symptomes"
          value={symptomes}
          onChange={(e) => setSymptomes(e.target.value)}
          placeholder="Ex : fièvre à 39°C, mal à la gorge depuis 2 jours..."
          rows={5}
          className="w-full rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-800 shadow-sm outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
        />
      </div>

      <PhotoUpload previewUrl={previewUrl} onSelect={handleSelectPhoto} onRemove={handleRemovePhoto} />

      <button
        type="submit"
        disabled={!symptomes.trim() || isLoading}
        className="w-full rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 sm:w-auto sm:px-8"
      >
        Analyser
      </button>
    </form>
  )
}
