import pytest

from bogu import Anonymizer, EntityMap, create_pipeline
from tests.conftest import SAMPLE_MIXED, SAMPLE_NO_PII, SAMPLE_WITH_EMAIL


@pytest.fixture
def anon() -> Anonymizer:
    return Anonymizer(create_pipeline("basic"))


# ---------------------------------------------------------------------------
# anonymize()
# ---------------------------------------------------------------------------

def test_email_replaced(anon: Anonymizer) -> None:
    text = "Send to alice@example.com please."
    result, em = anon.anonymize(text)
    assert "alice@example.com" not in result
    assert "[EMAIL_1]" in result


def test_no_pii_unchanged(anon: Anonymizer) -> None:
    result, em = anon.anonymize(SAMPLE_NO_PII)
    assert result == SAMPLE_NO_PII
    assert len(em) == 0


def test_multiple_types_replaced(anon: Anonymizer) -> None:
    result, em = anon.anonymize(SAMPLE_MIXED)
    assert "alice@example.com" not in result
    assert "555-123-4567" not in result
    assert "234-56-7890" not in result


def test_same_value_gets_same_token(anon: Anonymizer) -> None:
    text = "alice@example.com and again alice@example.com"
    result, em = anon.anonymize(text)
    # The token should appear twice
    assert result.count("[EMAIL_1]") == 2
    assert len(em) == 1  # only one unique value


def test_token_counter_increments(anon: Anonymizer) -> None:
    text = "alice@example.com and bob@example.com"
    result, em = anon.anonymize(text)
    assert "[EMAIL_1]" in result
    assert "[EMAIL_2]" in result


# ---------------------------------------------------------------------------
# deanonymize()
# ---------------------------------------------------------------------------

def test_round_trip(anon: Anonymizer) -> None:
    anonymized, em = anon.anonymize(SAMPLE_WITH_EMAIL)
    restored = Anonymizer.deanonymize(anonymized, em)
    assert restored == SAMPLE_WITH_EMAIL


def test_round_trip_mixed(anon: Anonymizer) -> None:
    anonymized, em = anon.anonymize(SAMPLE_MIXED)
    restored = Anonymizer.deanonymize(anonymized, em)
    assert restored == SAMPLE_MIXED


def test_deanonymize_empty_map(anon: Anonymizer) -> None:
    em = EntityMap()
    assert Anonymizer.deanonymize("hello [PERSON_1]", em) == "hello [PERSON_1]"


# ---------------------------------------------------------------------------
# Session continuation
# ---------------------------------------------------------------------------

def test_session_continuation(anon: Anonymizer) -> None:
    """Passing the same EntityMap across calls ensures consistent tokens."""
    _, em = anon.anonymize("alice@example.com")
    result2, em = anon.anonymize("Contact alice@example.com again", entity_map=em)
    # alice should still be EMAIL_1, not EMAIL_2
    assert "[EMAIL_1]" in result2
    assert "[EMAIL_2]" not in result2


# ---------------------------------------------------------------------------
# EntityMap serialization
# ---------------------------------------------------------------------------

def test_entity_map_round_trip(anon: Anonymizer) -> None:
    anonymized, em = anon.anonymize(SAMPLE_WITH_EMAIL)
    serialized = em.to_dict()
    restored_em = EntityMap.from_dict(serialized)
    assert Anonymizer.deanonymize(anonymized, restored_em) == SAMPLE_WITH_EMAIL


def test_entity_map_len(anon: Anonymizer) -> None:
    _, em = anon.anonymize(SAMPLE_MIXED)
    assert len(em) > 0


def test_entity_map_contains(anon: Anonymizer) -> None:
    _, em = anon.anonymize("alice@example.com")
    assert "alice@example.com" in em
    assert "bob@example.com" not in em
