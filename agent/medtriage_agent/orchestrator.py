import asyncio

import httpx

from medtriage_agent.llm import DeterministicProvider, LLMProvider
from medtriage_agent.module_clients import ExternalModuleClient
from medtriage_agent.schemas import ModuleSignal, TriageRequest, TriageResponse, URGENCY_RANK, UrgencyLevel
from medtriage_agent.triage_rules import DISCLAIMER, advice_for, default_questions, evaluate_rules


class TriageOrchestrator:
    def __init__(self, modules: ExternalModuleClient, llm: LLMProvider):
        self.modules = modules
        self.llm = llm

    async def triage(self, request: TriageRequest) -> TriageResponse:
        rule_signal = evaluate_rules(request)

        module_tasks = [self.modules.classify_symptoms(request)]
        if request.photo_base64:
            module_tasks.append(self.modules.analyze_photo(request))

        module_signals = await asyncio.gather(*module_tasks)
        signals = [rule_signal, *module_signals]
        urgency = highest_urgency(signals)
        orientation, delay, advice = advice_for(urgency)
        questions = default_questions(request, urgency)
        justification = build_justification(signals, urgency)

        try:
            message = await self.llm.compose_response(
                request=request,
                urgency=urgency,
                orientation=orientation,
                delay=delay,
                justification=justification,
                questions=questions,
            )
        except Exception as exc:
            signals.append(
                ModuleSignal(
                    source="llm",
                    available=False,
                    summary=f"LLM provider unavailable: {_safe_llm_error(exc)}",
                )
            )
            message = await DeterministicProvider().compose_response(
                request=request,
                urgency=urgency,
                orientation=orientation,
                delay=delay,
                justification=justification,
                questions=questions,
            )

        return TriageResponse(
            conversation_id=request.conversation_id,
            urgence=urgency,
            orientation=orientation,
            delai=delay,
            conseils=advice,
            questions_complementaires=questions,
            justification=justification,
            message=message,
            disclaimer_medical=DISCLAIMER,
            signals=signals,
        )


def highest_urgency(signals: list[ModuleSignal]) -> UrgencyLevel:
    urgency = UrgencyLevel.green
    for signal in signals:
        if signal.urgency and URGENCY_RANK[signal.urgency] > URGENCY_RANK[urgency]:
            urgency = signal.urgency
    return urgency


def build_justification(signals: list[ModuleSignal], urgency: UrgencyLevel) -> str:
    level_labels = {
        UrgencyLevel.green: "vert",
        UrgencyLevel.yellow: "jaune",
        UrgencyLevel.orange: "orange",
        UrgencyLevel.red: "rouge",
    }
    level = level_labels[urgency]
    useful_summaries = [
        f"{signal.source}: {signal.summary}"
        for signal in signals
        if signal.summary and (signal.available or signal.source == "rules")
    ]
    if useful_summaries:
        return f"Niveau {level} retenu à partir des signaux suivants: " + " | ".join(useful_summaries)
    return f"Niveau {level} retenu par défaut, faute de signal exploitable."


def _safe_llm_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        reason = exc.response.reason_phrase
        return f"HTTP {status} {reason}".strip()
    if isinstance(exc, httpx.RequestError):
        return exc.__class__.__name__
    return exc.__class__.__name__
