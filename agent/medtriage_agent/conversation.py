from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from medtriage_agent.schemas import ChatMessage


@dataclass
class Conversation:
    conversation_id: str
    turns: list[ChatMessage] = field(default_factory=list)


class InMemoryConversationStore:
    """Small process-local memory for chat context.

    This is enough for local/demo usage. In Azure, replace this class with
    Redis, Cosmos DB, or another shared store so context survives restarts and
    multiple replicas.
    """

    def __init__(self, max_turns: int = 12):
        self.max_turns = max_turns
        self._items: dict[str, Conversation] = {}
        self._lock = Lock()

    def get_or_create(self, conversation_id: str | None = None) -> Conversation:
        with self._lock:
            if conversation_id and conversation_id in self._items:
                return self._items[conversation_id]

            new_id = conversation_id or str(uuid4())
            conversation = Conversation(conversation_id=new_id)
            self._items[new_id] = conversation
            return conversation

    def add_turn(self, conversation_id: str, role: str, content: str) -> None:
        with self._lock:
            conversation = self._items.setdefault(
                conversation_id, Conversation(conversation_id=conversation_id)
            )
            conversation.turns.append(ChatMessage(role=role, content=content))
            if len(conversation.turns) > self.max_turns:
                conversation.turns = conversation.turns[-self.max_turns :]

    def build_symptom_context(
        self,
        conversation: Conversation,
        current_message: str,
        provided_history: list[ChatMessage],
    ) -> str:
        user_messages = [
            turn.content.strip()
            for turn in [*provided_history, *conversation.turns]
            if turn.role == "user" and turn.content.strip()
        ]

        if not user_messages:
            return current_message

        previous = "\n".join(f"- {message}" for message in user_messages[-6:])
        return (
            "Contexte patient déjà donné:\n"
            f"{previous}\n"
            "Dernière réponse utilisateur:\n"
            f"- {current_message}\n"
            "Si la dernière réponse est courte ou relative, l'interpréter comme une précision "
            "du contexte précédent."
        )
