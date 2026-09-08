from __future__ import annotations

import re
from dataclasses import dataclass

from ..core.models import DetectionResult, Entity, EntityType, Span


@dataclass
class _Pattern:
    entity_type: EntityType
    pattern: re.Pattern[str]
    confidence: float = 1.0


# Compiled once at module import time — never per detect() call.
_DEFAULT_PATTERNS: list[_Pattern] = [
    _Pattern(
        EntityType.EMAIL,
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ),
    _Pattern(
        EntityType.PHONE,
        re.compile(
            r"(\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"
        ),
    ),
    _Pattern(
        EntityType.SSN,
        re.compile(
            r"\b(?!000|666|9\d\d)\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"
        ),
    ),
    _Pattern(
        EntityType.CREDIT_CARD,
        re.compile(
            # Matches Visa, Mastercard, Amex, Discover — with or without
            # spaces/dashes between 4-digit groups (e.g. 4111 1111 1111 1111)
            r"\b(?:"
            r"4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"   # Visa 16-digit
            r"|4\d{3}[\s\-]?\d{6}[\s\-]?\d{5}"               # Visa 13-digit
            r"|5[1-5]\d{2}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"  # Mastercard
            r"|3[47]\d{2}[\s\-]?\d{6}[\s\-]?\d{5}"           # Amex
            r"|6(?:011|5\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"  # Discover
            r")\b"
        ),
    ),
    _Pattern(
        EntityType.IP_ADDRESS,
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    ),
    # Common secret/token patterns: OpenAI keys, AWS keys, generic long tokens
    _Pattern(
        EntityType.API_KEY,
        re.compile(
            r"\b(?:sk-[A-Za-z0-9]{32,}"
            r"|AKIA[A-Z0-9]{16}"
            r"|(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36})\b"
        ),
        confidence=0.9,
    ),
    _Pattern(
        EntityType.URL,
        re.compile(r"https?://[^\s<>\"{}|\\^`\[\]]+"),
    ),
]


class RegexDetector:
    """
    Level 1 — pure regex PII detector. Zero external dependencies.

    Parameters
    ----------
    patterns:
        Override the built-in pattern list entirely.
    enabled_types:
        Restrict detection to a specific subset of EntityTypes.
        None means all types are active.
    """

    def __init__(
        self,
        patterns: list[_Pattern] | None = None,
        *,
        enabled_types: set[EntityType] | None = None,
    ) -> None:
        self._patterns: list[_Pattern] = (
            list(patterns) if patterns is not None else list(_DEFAULT_PATTERNS)
        )
        self._enabled = enabled_types

    @property
    def name(self) -> str:
        return "RegexDetector"

    def detect(self, text: str) -> DetectionResult:
        entities: list[Entity] = []
        for pat in self._patterns:
            if self._enabled and pat.entity_type not in self._enabled:
                continue
            for m in pat.pattern.finditer(text):
                entities.append(
                    Entity(
                        text=m.group(),
                        entity_type=pat.entity_type,
                        span=Span(m.start(), m.end()),
                        confidence=pat.confidence,
                        source_detector=self.name,
                    )
                )
        return DetectionResult(original_text=text, entities=entities)

    def add_pattern(
        self,
        entity_type: EntityType,
        pattern: str | re.Pattern[str],
        confidence: float = 1.0,
    ) -> None:
        """Add a custom pattern at runtime without subclassing."""
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        self._patterns.append(_Pattern(entity_type, compiled, confidence))
