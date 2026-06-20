from app.services.rag.chunking import chunk_text, count_tokens


def test_empty_text_produces_no_chunks() -> None:
    assert chunk_text("", max_tokens=100, overlap_tokens=10) == []


def test_short_text_is_one_chunk() -> None:
    chunks = chunk_text("hello world", max_tokens=100, overlap_tokens=10)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert chunks[0].content == "hello world"


def test_paragraphs_split_into_multiple_chunks() -> None:
    # Three 5-word paragraphs, budget 6 tokens → can't all fit in one chunk.
    text = "a a a a a\n\nb b b b b\n\nc c c c c"
    chunks = chunk_text(text, max_tokens=6, overlap_tokens=0)

    assert len(chunks) == 3
    assert [c.index for c in chunks] == [0, 1, 2]
    assert all(c.token_count <= 6 for c in chunks)


def test_overlap_shares_content_between_chunks() -> None:
    text = "alpha alpha\n\nbeta beta\n\ngamma gamma"
    no_overlap = chunk_text(text, max_tokens=2, overlap_tokens=0)
    with_overlap = chunk_text(text, max_tokens=2, overlap_tokens=2)

    # Without overlap each paragraph is isolated; with overlap a chunk carries
    # the previous paragraph as shared context across the boundary.
    assert not any("alpha" in c.content and "beta" in c.content for c in no_overlap)
    assert any("alpha" in c.content and "beta" in c.content for c in with_overlap)


def test_oversized_paragraph_is_hard_split() -> None:
    text = " ".join(["word"] * 250)  # one 250-token paragraph
    chunks = chunk_text(text, max_tokens=100, overlap_tokens=0)

    assert len(chunks) >= 3
    assert all(count_tokens(c.content) <= 100 for c in chunks)
