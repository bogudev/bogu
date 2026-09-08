import pytest

from bogu import RegexDetector, create_pipeline
from bogu.core.models import Entity, EntityType, Span
from bogu.pipeline.pipeline import PIIPipeline


def _make_entity(
    text: str,
    start: int,
    end: int,
    confidence: float = 1.0,
    etype: EntityType = EntityType.PERSON,
) -> Entity:
    return Entity(
        text=text,
        entity_type=etype,
        span=Span(start, end),
        confidence=confidence,
        source_detector="test",
    )


# ---------------------------------------------------------------------------
# PIIPipeline construction
# ---------------------------------------------------------------------------

def test_empty_detectors_raises() -> None:
    with pytest.raises(ValueError, match="at least one detector"):
        PIIPipeline([])


def test_single_detector() -> None:
    pipeline = PIIPipeline([RegexDetector()])
    result = pipeline.run("email me at foo@bar.com")
    assert result.by_type(EntityType.EMAIL)


def test_pipeline_is_also_a_detector() -> None:
    pipeline = create_pipeline("basic")
    # detect() should be equivalent to run()
    r1 = pipeline.run("foo@bar.com")
    r2 = pipeline.detect("foo@bar.com")
    assert len(r1.entities) == len(r2.entities)


# ---------------------------------------------------------------------------
# Span merging via pipeline
# ---------------------------------------------------------------------------

def test_duplicate_entities_merged() -> None:
    """Two identical detectors should not produce duplicate entities."""
    pipeline = PIIPipeline([RegexDetector(), RegexDetector()])
    result = pipeline.run("alice@example.com")
    emails = result.by_type(EntityType.EMAIL)
    assert len(emails) == 1


def test_entities_sorted_by_offset() -> None:
    result = RegexDetector().detect(
        "alice@example.com foo@bar.com"
    )
    starts = [e.span.start for e in result.entities]
    assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_factory_basic_level() -> None:
    pipeline = create_pipeline("basic")
    assert len(pipeline.detectors) == 1
    assert pipeline.detectors[0].name == "RegexDetector"


def test_factory_advanced_requires_model_path() -> None:
    with pytest.raises(ValueError, match="llm_model_path"):
        create_pipeline("advanced")


def test_factory_basic_no_regex_raises() -> None:
    """include_regex=False with level=basic yields no detectors → ValueError."""
    with pytest.raises(ValueError, match="at least one detector"):
        create_pipeline("basic", include_regex=False)


def test_factory_rejects_unknown_level() -> None:
    with pytest.raises(ValueError, match="basic, mid, advanced"):
        create_pipeline("unknown")  # type: ignore[arg-type]
