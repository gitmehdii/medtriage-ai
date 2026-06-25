from medtriage_agent.conversation import InMemoryConversationStore


def test_context_preserves_previous_symptoms_for_short_follow_up():
    store = InMemoryConversationStore()
    conversation = store.get_or_create("conv-1")
    store.add_turn("conv-1", "user", "J'ai de la fièvre")

    context = store.build_symptom_context(
        conversation=conversation,
        current_message="depuis 2 jours",
        provided_history=[],
    )

    assert "J'ai de la fièvre" in context
    assert "depuis 2 jours" in context
    assert "précision du contexte précédent" in context


def test_store_creates_conversation_id_when_missing():
    store = InMemoryConversationStore()

    conversation = store.get_or_create()

    assert conversation.conversation_id


def test_store_tracks_answered_followup_questions():
    store = InMemoryConversationStore()
    conversation = store.get_or_create("conv-1")
    store.set_pending_followups(
        "conv-1",
        [
            "Avez-vous des antécédents médicaux importants ?",
            "Prenez-vous actuellement des médicaments ?",
        ],
    )

    store.record_user_reply("conv-1", "non")

    assert conversation.answered_followups == {"antecedents", "medications"}
    assert conversation.pending_followups == []
