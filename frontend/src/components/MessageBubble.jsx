import ResultCard from './ResultCard'

export default function MessageBubble({ message }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] space-y-2">
          {message.photoPreviewUrl && (
            <img
              src={message.photoPreviewUrl}
              alt="Photo envoyée"
              className="ml-auto h-28 w-28 rounded-xl object-cover ring-1 ring-slate-200"
            />
          )}
          <div className="rounded-2xl bg-teal-600 px-4 py-3 text-sm text-white shadow-sm">
            {message.text}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[90%] space-y-3">
        <div className="rounded-2xl bg-white px-4 py-3 text-sm text-slate-800 shadow-sm ring-1 ring-slate-100">
          {message.response.message}
        </div>
        <ResultCard result={message.response} />
      </div>
    </div>
  )
}
