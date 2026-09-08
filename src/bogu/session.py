"""Explicit lifetime management for private restoration values."""

from __future__ import annotations

from dataclasses import dataclass, field

from .anonymizer.anonymizer import Anonymizer
from .anonymizer.entity_map import EntityMap
from .core.models import EntityType


@dataclass
class BoguSession:
    """In-memory restoration state.

    Nothing is persisted automatically. Call :meth:`clear` when the protected
    workflow finishes; afterwards old placeholders can no longer be restored.
    """

    _entity_map: EntityMap = field(default_factory=EntityMap, repr=False)

    @property
    def private_value_count(self) -> int:
        return len(self._entity_map)

    def restore(self, text: str) -> str:
        return Anonymizer.deanonymize(text, self._entity_map)

    def token_for(self, value: str, entity_type: EntityType) -> str:
        """Return a stable session token for a private value."""
        return self._entity_map.get_or_create_token(value, entity_type)

    def clear(self) -> int:
        removed = len(self._entity_map)
        self._entity_map.clear()
        return removed

    def export(self) -> dict[str, str]:
        """Explicitly export sensitive state for caller-managed persistence."""
        return self._entity_map.to_dict()

    @classmethod
    def from_export(cls, data: dict[str, str]) -> BoguSession:
        return cls(EntityMap.from_dict(data))
