from uuid import uuid4

from app.services.rag.fusion import reciprocal_rank_fusion


def test_rrf_rewards_appearing_in_both_lists() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    # a is top of the vector list and second in keyword; b/c appear once each.
    fused = reciprocal_rank_fusion([[a, b], [c, a]])
    ranked = [chunk_id for chunk_id, _ in fused]

    assert ranked[0] == a  # only id in both lists → highest fused score
    assert set(ranked) == {a, b, c}  # de-duplicated union


def test_rrf_orders_by_rank_not_list_length() -> None:
    x, y = uuid4(), uuid4()
    # y is rank 1 in one list; x is rank 2 in each of two lists.
    fused = dict(reciprocal_rank_fusion([[x], [y, x]], k=1))
    # y: 1/(1+1)=0.5 ; x: 1/(1+1)+1/(1+2)=0.5+0.333=0.833
    assert fused[x] > fused[y]


def test_rrf_empty() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
