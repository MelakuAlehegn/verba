from types import SimpleNamespace

from app.services.rag.query_rewriting import rewrite_query


def _llm(tokens):
    return SimpleNamespace(stream=lambda prompt, system=None: iter(tokens))


def test_no_history_returns_query_unchanged_without_calling_llm() -> None:
    calls = []

    def stream(prompt, system=None):
        calls.append(1)
        return iter([])

    llm = SimpleNamespace(stream=stream)

    assert rewrite_query("what about section 5?", [], llm=llm) == "what about section 5?"
    assert calls == []  # first turn → no LLM call


def test_rewrites_followup_using_history() -> None:
    history = [("user", "Tell me about the lease term"), ("assistant", "It runs 24 months.")]
    llm = _llm(["When does the lease term end?"])

    assert rewrite_query("when does it end?", history, llm=llm) == "When does the lease term end?"


def test_strips_wrapping_quotes_and_whitespace() -> None:
    history = [("user", "x"), ("assistant", "y")]
    llm = _llm(['  "standalone query"  '])

    assert rewrite_query("q", history, llm=llm) == "standalone query"


def test_falls_back_to_original_when_rewrite_is_empty() -> None:
    history = [("user", "x")]
    llm = _llm(["   "])

    assert rewrite_query("original q", history, llm=llm) == "original q"


def test_falls_back_to_original_on_llm_error() -> None:
    def boom(prompt, system=None):
        raise RuntimeError("llm down")

    llm = SimpleNamespace(stream=boom)

    assert rewrite_query("original q", [("user", "x")], llm=llm) == "original q"
