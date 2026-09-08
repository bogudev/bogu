
from bogu.core.models import Entity, EntityType, Span
from bogu.core.span_utils import merge_entities, sort_entities


def _e(text: str, start: int, end: int, confidence: float = 1.0,
       etype: EntityType = EntityType.PERSON) -> Entity:
    return Entity(
        text=text, entity_type=etype,
        span=Span(start, end), confidence=confidence,
        source_detector="test",
    )


def test_no_overlap_preserves_all() -> None:
    entities = [_e("Alice", 0, 5), _e("Bob", 10, 13)]
    result = merge_entities(entities)
    assert len(result) == 2


def test_identical_spans_deduplicated() -> None:
    entities = [_e("Alice", 0, 5), _e("Alice", 0, 5)]
    result = merge_entities(entities)
    assert len(result) == 1


def test_contained_span_removed() -> None:
    outer = _e("John Smith", 0, 10)
    inner = _e("John", 0, 4)
    result = merge_entities([inner, outer])
    assert len(result) == 1
    assert result[0].text == "John Smith"


def test_higher_confidence_wins_partial_overlap() -> None:
    low = _e("John Sm", 0, 7, confidence=0.6)
    high = _e("John Smith", 0, 10, confidence=0.9)
    result = merge_entities([low, high])
    assert len(result) == 1
    assert result[0].confidence == 0.9


def test_longer_span_wins_equal_confidence() -> None:
    short = _e("John", 0, 4, confidence=0.8)
    long_ = _e("John Smith", 0, 10, confidence=0.8)
    result = merge_entities([short, long_])
    assert len(result) == 1
    assert result[0].text == "John Smith"


def test_sort_entities_by_offset() -> None:
    entities = [_e("Bob", 10, 13), _e("Alice", 0, 5)]
    sorted_ = sort_entities(entities)
    assert sorted_[0].text == "Alice"
    assert sorted_[1].text == "Bob"


def test_empty_list() -> None:
    assert merge_entities([]) == []


def test_single_entity() -> None:
    e = _e("Alice", 0, 5)
    result = merge_entities([e])
    assert result == [e]
