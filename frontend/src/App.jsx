import { useRef, useState } from 'react'
import ChatInput from './components/ChatInput'
import MessageBubble from './components/MessageBubble'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorBanner from './components/ErrorBanner'
import Disclaimer from './components/Disclaimer'
import { submitChat } from './api/chat'
import { fileToBase64 } from './utils/fileToBase64'

let nextId = 0

export default function App() {
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState(null)
  const pendingRequestRef = useRef(null)

  const lastResponse = [...messages].reverse().find((m) => m.role === 'assistant')?.response

  async function performRequest({ message, photoBase64, conversationIdAtRequest }) {
    setIsLoading(true)
    setErrorMessage(null)
    pendingRequestRef.current = { message, photoBase64, conversationIdAtRequest }

    try {
      const response = await submitChat({
        message,
        photoBase64,
        conversationId: conversationIdAtRequest,
      })
      setConversationId(response.conversation_id)
      setMessages((prev) => [...prev, { id: nextId++, role: 'assistant', response }])
      pendingRequestRef.current = null
    } catch (err) {
      setErrorMessage(err.message || 'Une erreur est survenue, veuillez réessayer.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSend({ message, photoFile }) {
    const photoPreviewUrl = photoFile ? URL.createObjectURL(photoFile) : null
    setMessages((prev) => [...prev, { id: nextId++, role: 'user', text: message, photoPreviewUrl }])

    const photoBase64 = photoFile ? await fileToBase64(photoFile) : null
    performRequest({ message, photoBase64, conversationIdAtRequest: conversationId })
  }

  function handleRetry() {
    if (pendingRequestRef.current) performRequest(pendingRequestRef.current)
  }

  function handleNewConversation() {
    setMessages([])
    setConversationId(null)
    setErrorMessage(null)
    pendingRequestRef.current = null
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-100 bg-white">
        <div className="mx-auto flex w-full max-w-2xl items-center justify-between px-4 py-6">
          <h1 className="text-2xl font-bold text-slate-800">
            Med<span className="text-teal-600">Triage</span>AI
          </h1>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleNewConversation}
              className="shrink-0 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
            >
              Nouvelle conversation
            </button>
          )}
        </div>
      </header>

      {messages.length === 0 ? (
        <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center px-4">
          <div className="w-full space-y-4">
            <p className="text-center text-sm text-slate-500">
              Décrivez vos symptômes pour commencer
            </p>
            <ChatInput onSend={handleSend} isLoading={isLoading} variant="centered" />
            {errorMessage && <ErrorBanner message={errorMessage} onRetry={handleRetry} />}
          </div>
        </main>
      ) : (
        <>
          <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 py-6">
            <div className="flex-1 space-y-4">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && <LoadingSpinner />}
              {errorMessage && <ErrorBanner message={errorMessage} onRetry={handleRetry} />}
            </div>
          </main>
          <ChatInput onSend={handleSend} isLoading={isLoading} variant="anchored" />
        </>
      )}

      <footer className="mt-auto bg-white">
        <Disclaimer text={lastResponse?.disclaimer_medical} />
      </footer>
    </div>
  )
}
