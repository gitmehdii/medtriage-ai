const DEFAULT_TEXT = "Cet outil ne remplace pas un avis médical. En cas d'urgence vitale, appelez le 15."

export default function Disclaimer({ text }) {
  return (
    <p className="mx-auto max-w-2xl px-4 pb-6 text-center text-xs leading-relaxed text-slate-400">
      {text || DEFAULT_TEXT}
    </p>
  )
}
