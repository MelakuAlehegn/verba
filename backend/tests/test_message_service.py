from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.schemas.message import MessageCreate
from app.services.message_service import post_message_to_chat, stream_message_reply

MODULE = "app.services.message_service"


def _fake_llm(tokens):
    return SimpleNamespace(stream=lambda prompt, system=None: iter(tokens))


def test_post_message_generates_and_persists_both_turns(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    created = []

    def fake_create_message(_db, **kwargs):
        created.append(kwargs)
        return SimpleNamespace(id=uuid4(), **kwargs)

    monkeypatch.setattr(f"{MODULE}.create_message", fake_create_message)
    monkeypatch.setattr(f"{MODULE}.touch_chat", lambda db, c: c)
    monkeypatch.setattr(f"{MODULE}.get_recent_messages", lambda *a, **k: [])
    monkeypatch.setattr(f"{MODULE}.resolve_chat_scope", lambda db, chat: None)
    monkeypatch.setattr(f"{MODULE}.retrieve_context", lambda *a, **k: [])

    post_message_to_chat(
        db,
        chat,
        MessageCreate(content="how much tax?"),
        embedder=Mock(),
        vector_store=Mock(),
        llm=_fake_llm(["$4", ",210"]),
    )

    # user turn, then assistant turn with the joined LLM output.
    assert [c["role"] for c in created] == ["user", "assistant"]
    assert created[1]["content"] == "$4,210"
    db.commit.assert_called_once()


def test_post_message_persists_citations_for_retrieved_chunks(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    chunks = [
        SimpleNamespace(document_id=uuid4(), chunk_id=uuid4(), content="first", score=0.9),
        SimpleNamespace(document_id=uuid4(), chunk_id=uuid4(), content="second", score=0.5),
    ]
    citations = []

    monkeypatch.setattr(
        f"{MODULE}.create_message", lambda _db, **k: SimpleNamespace(id=uuid4(), **k)
    )
    monkeypatch.setattr(f"{MODULE}.touch_chat", lambda db, c: c)
    monkeypatch.setattr(f"{MODULE}.get_recent_messages", lambda *a, **k: [])
    monkeypatch.setattr(f"{MODULE}.resolve_chat_scope", lambda db, chat: None)
    monkeypatch.setattr(f"{MODULE}.retrieve_context", lambda *a, **k: chunks)
    monkeypatch.setattr(
        f"{MODULE}.create_message_citation", lambda _db, **k: citations.append(k)
    )

    post_message_to_chat(
        db,
        chat,
        MessageCreate(content="q"),
        embedder=Mock(),
        vector_store=Mock(),
        llm=_fake_llm(["answer"]),
    )

    assert [c["rank"] for c in citations] == [1, 2]
    assert citations[0]["chunk_id"] == chunks[0].chunk_id
    assert citations[0]["quote_preview"] == "first"


def test_post_message_rewrites_followup_using_history(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())

    monkeypatch.setattr(
        f"{MODULE}.create_message", lambda _db, **k: SimpleNamespace(id=uuid4(), **k)
    )
    monkeypatch.setattr(f"{MODULE}.touch_chat", lambda db, c: c)
    monkeypatch.setattr(f"{MODULE}.resolve_chat_scope", lambda db, chat: None)
    # Prior conversation exists → the follow-up should be rewritten before search.
    monkeypatch.setattr(
        f"{MODULE}.get_recent_messages",
        lambda *a, **k: [
            SimpleNamespace(role="user", content="Tell me about the lease term"),
            SimpleNamespace(role="assistant", content="It runs 24 months."),
        ],
    )
    captured = {}

    def fake_retrieve(_db, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(f"{MODULE}.retrieve_context", fake_retrieve)

    post_message_to_chat(
        db,
        chat,
        MessageCreate(content="when does it end?"),
        embedder=Mock(),
        vector_store=Mock(),
        # The fake LLM answers every prompt with this — including the rewrite.
        llm=_fake_llm(["When does the lease term end?"]),
    )

    # Retrieval ran on the rewritten standalone query, not the raw "when does it end?".
    assert captured["query"] == "When does the lease term end?"


def test_post_message_retrieves_within_chat_scope(monkeypatch) -> None:
    db = Mock()
    chat = SimpleNamespace(id=uuid4(), user_id=uuid4())
    scope = [uuid4(), uuid4()]

    monkeypatch.setattr(
        f"{MODULE}.create_message", lambda _db, **k: SimpleNamespace(id=uuid4(), **k)
    )
    monkeypatch.setattr(f"{MODULE}.touch_chat", lambda db, c: c)
    monkeypatch.setattr(f"{MODULE}.get_recent_messages", lambda *a, **k: [])
    monkeypatch.setattr(f"{MODULE}.resolve_chat_scope", lambda db, chat: scope)
    captured = {}

    def fake_retrieve(_db, **kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.setattr(f"{MODULE}.retrieve_context", fake_retrieve)

    post_message_to_chat(
        db,
        chat,
        MessageCreate(content="q"),
        embedder=Mock(),
        vector_store=Mock(),
        llm=_fake_llm(["answer"]),
    )

    # Retrieval is confined to the chat's attached sources.
    assert captured["document_ids"] == scope


def test_stream_reply_yields_tokens_then_persists(monkeypatch) -> None:
    db = Mock()
    monkeypatch.setattr(f"{MODULE}.retrieve_context", lambda *a, **k: [])
    finalized = {}

    def fake_finalize(_db, message_id, *, content, status, chunks=None):
        finalized.update(message_id=message_id, content=content, status=status)

    monkeypatch.setattr(f"{MODULE}.finalize_assistant_message", fake_finalize)

    message_id = uuid4()
    tokens = list(
        stream_message_reply(
            db,
            user_id=uuid4(),
            query="q",
            assistant_message_id=message_id,
            embedder=Mock(),
            vector_store=Mock(),
            llm=_fake_llm(["Hel", "lo"]),
        )
    )

    assert tokens == ["Hel", "lo"]
    assert finalized == {"message_id": message_id, "content": "Hello", "status": "complete"}
