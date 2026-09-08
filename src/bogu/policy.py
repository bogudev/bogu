"""User-configurable redaction policies."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .core.models import DetectionResult, Entity, EntityType, Span


@dataclass(frozen=True)
class BoguPolicy:
    """Describe what to detect and which categories cannot be restored.

    ``examples`` is a mapping from an entity type to literal values.  It is
    intended for private, organization-specific values (project names, customer
    identifiers, internal hosts, and similar data) that generic detectors cannot
    reliably recognize.
    """

    name: str = "standard"
    description: str = "Pseudonymize every detected value."
    irreversible_types: frozenset[EntityType] = frozenset()
    examples: dict[EntityType, tuple[str, ...]] = field(default_factory=dict)

    @classmethod
    def from_examples(
        cls,
        examples: dict[EntityType | str, list[str] | tuple[str, ...]],
        *,
        name: str = "custom",
        description: str = "User-provided sensitive examples.",
        irreversible_types: set[EntityType | str] | None = None,
    ) -> BoguPolicy:
        """Build a policy from friendly string keys and literal examples."""
        normalized = {
            EntityType(kind): tuple(value for value in values if value)
            for kind, values in examples.items()
        }
        irreversible = frozenset(
            EntityType(kind) for kind in (irreversible_types or set())
        )
        return cls(name, description, irreversible, normalized)


class PolicyDetector:
    """Detect literal examples supplied by a :class:`BoguPolicy`."""

    def __init__(self, policy: BoguPolicy, *, ignore_case: bool = False) -> None:
        self.policy = policy
        flags = re.IGNORECASE if ignore_case else 0
        self._patterns = [
            (entity_type, value, re.compile(re.escape(value), flags))
            for entity_type, values in policy.examples.items()
            for value in values
        ]

    @property
    def name(self) -> str:
        return f"PolicyDetector[{self.policy.name}]"

    def detect(self, text: str) -> DetectionResult:
        entities: list[Entity] = []
        for entity_type, _example, pattern in self._patterns:
            for match in pattern.finditer(text):
                entities.append(
                    Entity(
                        text=match.group(),
                        entity_type=entity_type,
                        span=Span(match.start(), match.end()),
                        confidence=1.0,
                        source_detector=self.name,
                        metadata={"policy": self.policy.name},
                    )
                )
        return DetectionResult(original_text=text, entities=entities)
