from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EntityType(str, Enum):
    # Regex-detectable
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    API_KEY = "API_KEY"
    URL = "URL"
    # NER-detectable
    PERSON = "PERSON"
    ORG = "ORG"
    LOCATION = "LOCATION"
    DATE = "DATE"
    ADDRESS = "ADDRESS"
    ACCOUNT_NUMBER = "ACCOUNT_NUMBER"
    SECRET = "SECRET"
    # LLM-detectable
    FINANCIAL = "FINANCIAL"
    MEDICAL = "MEDICAL"
    OTHER = "OTHER"


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def __len__(self) -> int:
        return self.end - self.start

    def overlaps(self, other: Span) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: Span) -> bool:
        return self.start <= other.start and self.end >= other.end

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError(f"Span start ({self.start}) must be <= end ({self.end})")


@dataclass
class Entity:
    text: str
    entity_type: EntityType
    span: Span
    confidence: float
    source_detector: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")


@dataclass
class DetectionResult:
    original_text: str
    entities: list[Entity]

    @property
    def has_pii(self) -> bool:
        return len(self.entities) > 0

    def by_type(self, entity_type: EntityType) -> list[Entity]:
        return [e for e in self.entities if e.entity_type == entity_type]
