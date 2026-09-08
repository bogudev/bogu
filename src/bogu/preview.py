"""Inspectable redaction previews that contain no original private values."""

from __future__ import annotations

from dataclasses import dataclass

from .anonymizer.entity_map import EntityMap
from .core.protocols import Detector
from .policy import BoguPolicy


@dataclass(frozen=True)
class BoguPreview:
    """Safe payload and category summary to review before transmission."""

    redacted_text: str
    entity_count: int
    categories: dict[str, int]
    policy: str


def create_preview(
    text: str,
    detector: Detector,
    *,
    policy: BoguPolicy | None = None,
    entity_map: EntityMap | None = None,
) -> tuple[BoguPreview, EntityMap]:
    """Redact text locally and return a safe preview plus its private session map."""
    # Deferred imports avoid a module cycle: Bogu's result type lives here.
    from .bogu import Bogu  # noqa: PLC0415
    from .session import BoguSession  # noqa: PLC0415

    mapping = entity_map if entity_map is not None else EntityMap()
    session = BoguSession(mapping)
    preview = Bogu(detector, policy=policy, session=session).protect(text)
    return preview, mapping
