from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..core.models import EntityType


@dataclass
class EntityMap:
    """
    Session-scoped bidirectional mapping between placeholder tokens and
    original PII values.

    The same original value always maps to the same token within a session,
    ensuring consistent replacement and enabling reversible de-anonymization.

    Token format: ``[TYPE_N]`` e.g. ``[PERSON_1]``, ``[EMAIL_2]``.
    """

    _forward: dict[str, str] = field(default_factory=dict)   # original → token
    _reverse: dict[str, str] = field(default_factory=dict)   # token → original
    _counters: dict[str, int] = field(
        default_factory=lambda: defaultdict(int)
    )

    def get_or_create_token(self, original: str, entity_type: EntityType) -> str:
        """Return the existing token for `original`, or mint a new one."""
        if original in self._forward:
            return self._forward[original]
        type_key = entity_type.value
        self._counters[type_key] += 1
        token = f"[{type_key}_{self._counters[type_key]}]"
        self._forward[original] = token
        self._reverse[token] = original
        return token

    def resolve(self, token: str) -> str | None:
        """Resolve a token back to its original value, or None if unknown."""
        return self._reverse.get(token)

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-safe dict (token → original) for persistence."""
        return dict(self._reverse)

    def clear(self) -> None:
        """Irreversibly remove all values and reset token counters."""
        self._forward.clear()
        self._reverse.clear()
        self._counters.clear()

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> EntityMap:
        """Reconstruct an EntityMap from a persisted token→original dict."""
        em = cls()
        for token, original in data.items():
            em._reverse[token] = original
            em._forward[original] = token
            # Reconstruct per-type counters from token names
            inner = token.strip("[]")
            parts = inner.rsplit("_", 1)
            if len(parts) == 2 and parts[1].isdigit():
                type_key = parts[0]
                em._counters[type_key] = max(
                    em._counters[type_key], int(parts[1])
                )
        return em

    def __len__(self) -> int:
        return len(self._forward)

    def __contains__(self, original: str) -> bool:
        return original in self._forward
