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
