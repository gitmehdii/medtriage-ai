import { useState } from 'react'
import PhotoUpload from './PhotoUpload'

export default function ChatInput({ onSend, isLoading, variant = 'anchored' }) {
  const [message, setMessage] = useState('')
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
    if (!message.trim() || isLoading) return
    onSend({ message: message.trim(), photoFile })
    setMessage('')
    handleRemovePhoto()
  }

  const wrapperClass =
    variant === 'centered'
      ? 'space-y-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-100'
      : 'space-y-3 border-t border-slate-100 bg-white p-4 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]'

  return (
    <form onSubmit={handleSubmit} className={wrapperClass}>
      {previewUrl && (
        <PhotoUpload previewUrl={previewUrl} onSelect={handleSelectPhoto} onRemove={handleRemovePhoto} />
      )}

      <div className="flex items-end gap-2">
        {!previewUrl && (
          <PhotoUpload previewUrl={null} onSelect={handleSelectPhoto} onRemove={handleRemovePhoto} />
        )}

        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Décrivez vos symptômes..."
          rows={1}
          className="flex-1 resize-none rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 shadow-sm outline-none transition focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
        />

        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className="shrink-0 rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
        >
          Envoyer
        </button>
      </div>
    </form>
  )
}
