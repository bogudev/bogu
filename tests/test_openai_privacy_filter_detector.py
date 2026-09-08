from __future__ import annotations

from dataclasses import dataclass

from bogu import EntityType
from bogu.detectors.openai_privacy_filter import OpenAIPrivacyFilterDetector


@dataclass
class FakeSpan:
    label: str
    start: int
    end: int
    text: str


@dataclass
class FakeResult:
    detected_spans: tuple[FakeSpan, ...]


class FakeOPF:
    def __init__(self, **_kwargs: object) -> None:
        pass

    def redact(self, text: str) -> FakeResult:
        name = "Alice Martin"
        start = text.index(name)
        return FakeResult((FakeSpan("private_person", start, start + len(name), name),))


def test_openai_privacy_filter_maps_local_spans() -> None:
    detector = OpenAIPrivacyFilterDetector(redactor_factory=FakeOPF)

    result = detector.detect("Patient Alice Martin requested a summary.")

    assert len(result.entities) == 1
    entity = result.entities[0]
    assert entity.entity_type is EntityType.PERSON
    assert entity.text == "Alice Martin"
    assert entity.source_detector == "OpenAIPrivacyFilterDetector[local]"


def test_openai_privacy_filter_maps_every_supported_label() -> None:
    labels = {
        "private_person": EntityType.PERSON,
        "private_address": EntityType.ADDRESS,
        "private_email": EntityType.EMAIL,
        "private_phone": EntityType.PHONE,
        "private_url": EntityType.URL,
        "private_date": EntityType.DATE,
        "account_number": EntityType.ACCOUNT_NUMBER,
        "secret": EntityType.SECRET,
    }

    class AllLabelsOPF:
        def __init__(self, **_kwargs: object) -> None:
            pass

        def redact(self, text: str) -> FakeResult:
            spans = []
            for label, value in zip(labels, text.split("|"), strict=True):
                start = text.index(value)
                spans.append(FakeSpan(label, start, start + len(value), value))
            return FakeResult(tuple(spans))

    text = "person|address|email|phone|url|date|account|secret"
    detector = OpenAIPrivacyFilterDetector(redactor_factory=AllLabelsOPF)

    result = detector.detect(text)

    assert [entity.entity_type for entity in result.entities] == list(labels.values())
