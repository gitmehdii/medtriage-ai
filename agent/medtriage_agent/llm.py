from abc import ABC, abstractmethod

import httpx

from medtriage_agent.config import Settings
from medtriage_agent.schemas import TriageRequest, UrgencyLevel


class LLMProvider(ABC):
    @abstractmethod
    async def compose_response(
        self,
        request: TriageRequest,
        urgency: UrgencyLevel,
        orientation: str,
        delay: str,
        justification: str,
        questions: list[str],
    ) -> str:
        raise NotImplementedError


class DeterministicProvider(LLMProvider):
    async def compose_response(
        self,
        request: TriageRequest,
        urgency: UrgencyLevel,
        orientation: str,
        delay: str,
        justification: str,
        questions: list[str],
    ) -> str:
        question_text = ""
        if questions:
            question_text = " Questions utiles: " + " ".join(questions)

        level_labels = {
            UrgencyLevel.green: "vert",
            UrgencyLevel.yellow: "jaune",
            UrgencyLevel.orange: "orange",
            UrgencyLevel.red: "rouge",
        }

        if urgency is UrgencyLevel.red:
            action = "Appelez le 15 ou le 112 maintenant, ou faites appeler quelqu'un près de vous."
        elif urgency is UrgencyLevel.orange:
            action = "Un avis médical rapide est recommandé, plus tôt si la douleur augmente ou si de nouveaux signes apparaissent."
        elif urgency is UrgencyLevel.yellow:
            action = "Surveillez l'évolution et demandez un avis médical si les symptômes persistent ou s'aggravent."
        else:
            action = "Une surveillance à domicile peut suffire pour l'instant, avec avis médical si aggravation."

        return (
            f"Niveau {level_labels[urgency]}. Orientation recommandée: {orientation}. Délai: {delay}. "
            f"{action} Raison principale: {justification}.{question_text}"
        )


class OllamaProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.request_timeout_seconds

    async def compose_response(
        self,
        request: TriageRequest,
        urgency: UrgencyLevel,
        orientation: str,
        delay: str,
        justification: str,
        questions: list[str],
    ) -> str:
        prompt = _build_prompt(request, urgency, orientation, delay, justification, questions)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip()


class GeminiProvider(LLMProvider):
    def __init__(self, settings: Settings):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.timeout = settings.request_timeout_seconds

    async def compose_response(
        self,
        request: TriageRequest,
        urgency: UrgencyLevel,
        orientation: str,
        delay: str,
        justification: str,
        questions: list[str],
    ) -> str:
        if not self.api_key:
            return await DeterministicProvider().compose_response(
                request, urgency, orientation, delay, justification, questions
            )

        prompt = _system_prompt() + "\n\n" + _build_prompt(
            request, urgency, orientation, delay, justification, questions
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(part.get("text", "") for part in parts).strip()


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    if settings.llm_provider == "gemini":
        return GeminiProvider(settings)
    return DeterministicProvider()


def _system_prompt() -> str:
    return (
        "Tu es l'agent conversationnel de MedTriageAI. Tu aides à orienter, pas à diagnostiquer. "
        "Respecte strictement le niveau d'urgence, l'orientation et le délai fournis. "
        "Réponds en français, de manière concise, prudente, non alarmiste, et rappelle de contacter "
        "le 15 ou le 112 en cas d'urgence."
    )


def _build_prompt(
    request: TriageRequest,
    urgency: UrgencyLevel,
    orientation: str,
    delay: str,
    justification: str,
    questions: list[str],
) -> str:
    return (
        f"Symptômes utilisateur: {request.symptomes}\n"
        f"Niveau d'urgence imposé: {urgency.value}\n"
        f"Orientation imposée: {orientation}\n"
        f"Délai imposé: {delay}\n"
        f"Justification médicale synthétique: {justification}\n"
        f"Questions complémentaires à poser si utile: {questions}\n"
        "Rédige une réponse courte avec: orientation, conseils immédiats, questions utiles."
    )
