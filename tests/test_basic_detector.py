import pytest

from bogu import EntityType, RegexDetector
from tests.conftest import (
    SAMPLE_MIXED,
    SAMPLE_NO_PII,
    SAMPLE_WITH_API_KEY,
    SAMPLE_WITH_CREDIT_CARD,
    SAMPLE_WITH_EMAIL,
    SAMPLE_WITH_IP,
    SAMPLE_WITH_PHONE,
    SAMPLE_WITH_SSN,
)


@pytest.fixture
def detector() -> RegexDetector:
    return RegexDetector()


def test_email_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_EMAIL)
    assert result.has_pii
    emails = result.by_type(EntityType.EMAIL)
    assert len(emails) == 1
    assert emails[0].text == "alice@example.com"


def test_email_span_accuracy(detector: RegexDetector) -> None:
    text = SAMPLE_WITH_EMAIL
    result = detector.detect(text)
    entity = result.by_type(EntityType.EMAIL)[0]
    assert text[entity.span.start : entity.span.end] == entity.text


def test_phone_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_PHONE)
    phones = result.by_type(EntityType.PHONE)
    assert len(phones) == 1
    assert "5309" in phones[0].text


def test_ssn_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_SSN)
    ssns = result.by_type(EntityType.SSN)
    assert len(ssns) == 1
    assert ssns[0].text == "123-45-6789"


def test_ssn_invalid_ranges_rejected(detector: RegexDetector) -> None:
    # 000-xx-xxxx, 666-xx-xxxx and 9xx-xx-xxxx are invalid SSNs
    for invalid in ("000-12-3456", "666-12-3456", "900-12-3456"):
        result = detector.detect(invalid)
        assert not result.by_type(EntityType.SSN), f"{invalid} should not match"


def test_credit_card_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_CREDIT_CARD)
    cards = result.by_type(EntityType.CREDIT_CARD)
    assert len(cards) == 1
    assert cards[0].text == "4111111111111111"


def test_ip_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_IP)
    ips = result.by_type(EntityType.IP_ADDRESS)
    assert len(ips) == 1
    assert ips[0].text == "192.168.1.100"


def test_api_key_detection(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_API_KEY)
    keys = result.by_type(EntityType.API_KEY)
    assert len(keys) >= 1


def test_mixed_text_multiple_types(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_MIXED)
    assert result.by_type(EntityType.EMAIL)
    assert result.by_type(EntityType.PHONE)
    assert result.by_type(EntityType.SSN)
    assert result.by_type(EntityType.CREDIT_CARD)


def test_no_pii_text(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_NO_PII)
    assert not result.has_pii


def test_confidence_is_one_for_exact_patterns(detector: RegexDetector) -> None:
    result = detector.detect(SAMPLE_WITH_EMAIL)
    entity = result.by_type(EntityType.EMAIL)[0]
    assert entity.confidence == 1.0


def test_add_custom_pattern(detector: RegexDetector) -> None:
    detector.add_pattern(EntityType.OTHER, r"\bACME-\d{6}\b")
    result = detector.detect("Reference: ACME-123456 for the contract.")
    others = result.by_type(EntityType.OTHER)
    assert len(others) == 1
    assert others[0].text == "ACME-123456"


def test_enabled_types_filter(detector: RegexDetector) -> None:
    filtered = RegexDetector(enabled_types={EntityType.EMAIL})
    result = filtered.detect(SAMPLE_MIXED)
    # Should only return emails, not phones/SSNs/etc.
    assert result.by_type(EntityType.EMAIL)
    assert not result.by_type(EntityType.PHONE)
    assert not result.by_type(EntityType.SSN)


def test_detector_name() -> None:
    assert RegexDetector().name == "RegexDetector"
