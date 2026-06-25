from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    green = "green"
    yellow = "yellow"
    orange = "orange"
    red = "red"


URGENCY_RANK: dict[UrgencyLevel, int] = {
    UrgencyLevel.green: 0,
    UrgencyLevel.yellow: 1,
    UrgencyLevel.orange: 2,
    UrgencyLevel.red: 3,
}


class TriageRequest(BaseModel):
    symptomes: str = Field(..., min_length=1, description="User symptom description.")
    photo_base64: str | None = Field(default=None, description="Optional wound or symptom photo.")
    age: int | None = Field(default=None, ge=0, le=130)
    sexe: str | None = None
    antecedents: list[str] = Field(default_factory=list)
    medicaments: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    answered_followups: list[str] = Field(default_factory=list)
    conversation_id: str | None = None


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    photo_base64: str | None = None
    conversation_id: str | None = None


class ModuleSignal(BaseModel):
    source: str
    available: bool = True
    urgency: UrgencyLevel | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    summary: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class TriageResponse(BaseModel):
    conversation_id: str | None = None
    urgence: UrgencyLevel
    orientation: str
    delai: str
    conseils: list[str]
    questions_complementaires: list[str]
    justification: str
    message: str
    disclaimer_medical: str
    signals: list[ModuleSignal] = Field(default_factory=list)
