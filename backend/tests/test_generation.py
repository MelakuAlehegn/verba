from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from app.services.rag.generation import SYSTEM_INSTRUCTION, build_prompt
from app.services.rag.llm import GeminiLLM


def _chunk(content: str) -> SimpleNamespace:
    return SimpleNamespace(
        chunk_id=uuid4(), document_id=uuid4(), content=content, score=0.9, metadata={}
    )


def test_build_prompt_includes_context_and_question() -> None:
    prompt = build_prompt("How much tax?", [_chunk("Total tax owed: $4,210")])

    assert "Total tax owed: $4,210" in prompt
    assert "[Source 1]" in prompt
    assert "How much tax?" in prompt


def test_system_instruction_enforces_grounding() -> None:
    assert "ONLY the provided context" in SYSTEM_INSTRUCTION
    assert "never use prior or general knowledge" in SYSTEM_INSTRUCTION.lower()
    assert "couldn't find anything" in SYSTEM_INSTRUCTION  # explicit out-of-scope reply


def test_build_prompt_handles_no_context() -> None:
    prompt = build_prompt("anything?", [])

    assert "no relevant context" in prompt
    assert "anything?" in prompt


def test_build_prompt_includes_conversation_history() -> None:
    history = [("user", "What is the lease term?"), ("assistant", "It runs 24 months.")]
    prompt = build_prompt("When does it end?", [_chunk("The lease ends on 31 Dec.")], history)

    assert "Conversation so far" in prompt
    assert "What is the lease term?" in prompt
    assert "It runs 24 months." in prompt
    # Context + question still present and the continuity caveat is stated.
    assert "The lease ends on 31 Dec." in prompt
    assert "still answer strictly from the sources" in prompt


def test_build_prompt_truncates_long_history_turns() -> None:
    long_answer = "x" * 1000
    prompt = build_prompt("q", [_chunk("ctx")], [("assistant", long_answer)])

    assert "…" in prompt
    assert "x" * 1000 not in prompt  # capped, not verbatim


def test_build_prompt_without_history_omits_conversation_section() -> None:
    prompt = build_prompt("q", [_chunk("ctx")])

    assert "Conversation so far" not in prompt


def test_gemini_stream_yields_text_and_skips_empty() -> None:
    llm = GeminiLLM.__new__(GeminiLLM)  # bypass real client construction
    llm.model = "gemini-2.5-flash"
    llm._client = Mock()
    llm._client.models.generate_content_stream.return_value = [
        SimpleNamespace(text="Hel"),
        SimpleNamespace(text="lo"),
        SimpleNamespace(text=None),  # metadata-only chunk
        SimpleNamespace(text=" world"),
    ]

    assert "".join(llm.stream("a prompt")) == "Hello world"
