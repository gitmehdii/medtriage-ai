import { useState } from 'react'
import SymptomForm from './components/SymptomForm'
import ResultCard from './components/ResultCard'
import LoadingSpinner from './components/LoadingSpinner'
import ErrorBanner from './components/ErrorBanner'
import Disclaimer from './components/Disclaimer'
import { submitTriage } from './api/triage'
import { fileToBase64 } from './utils/fileToBase64'

export default function App() {
  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [result, setResult] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)
  const [lastSubmission, setLastSubmission] = useState(null)

  async function runTriage({ symptomes, photoFile }) {
    setStatus('loading')
    setErrorMessage(null)
    setLastSubmission({ symptomes, photoFile })

    try {
      const photoBase64 = photoFile ? await fileToBase64(photoFile) : ''
      const response = await submitTriage({ symptomes, photoBase64 })
      setResult(response)
      setStatus('success')
    } catch (err) {
      setErrorMessage(err.message || 'Une erreur est survenue, veuillez réessayer.')
      setStatus('error')
    }
  }

  function handleRetry() {
    if (lastSubmission) runTriage(lastSubmission)
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-100 bg-white">
        <div className="mx-auto max-w-2xl px-4 py-6">
          <h1 className="text-2xl font-bold text-slate-800">
            Med<span className="text-teal-600">Triage</span>AI
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Décrivez vos symptômes pour obtenir une orientation rapide.
          </p>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <div className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-100">
          <SymptomForm onSubmit={runTriage} isLoading={status === 'loading'} />
        </div>

        <div className="mt-6">
          {status === 'loading' && <LoadingSpinner />}
          {status === 'error' && <ErrorBanner message={errorMessage} onRetry={handleRetry} />}
          {status === 'success' && result && <ResultCard result={result} />}
        </div>
      </main>

      <footer className="mt-auto">
        <Disclaimer />
      </footer>
    </div>
  )
}
