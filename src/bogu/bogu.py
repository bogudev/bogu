"""High-level local privacy workflow."""

from __future__ import annotations

from collections import Counter

from .core.protocols import Detector
from .pipeline.pipeline import PIIPipeline
from .policy import BoguPolicy, PolicyDetector
from .preview import BoguPreview
from .processing import ProcessingContext, TextProcessor, run_processors
from .session import BoguSession


class Bogu:
    """Protect outbound text and restore inbound text using local-only state."""

    def __init__(
        self,
        detector: Detector,
        *,
        policy: BoguPolicy | None = None,
        session: BoguSession | None = None,
        preprocessors: tuple[TextProcessor, ...] = (),
        postprocessors: tuple[TextProcessor, ...] = (),
    ) -> None:
        self.policy = policy or BoguPolicy()
        if self.policy.examples:
            detector = PIIPipeline([detector, PolicyDetector(self.policy)])
        self.detector = detector
        self.session = session or BoguSession()
        self.preprocessors = tuple(preprocessors)
        self.postprocessors = tuple(postprocessors)

    def protect(
        self, text: str, *, metadata: dict[str, object] | None = None
    ) -> BoguPreview:
        """Create the exact outbound text locally; performs no network operation."""
        context = ProcessingContext("before_protection", dict(metadata or {}))
        prepared = run_processors(text, self.preprocessors, context)
        detection = self.detector.detect(prepared)
        categories = Counter(entity.entity_type.value for entity in detection.entities)
        protected = prepared
        for entity in sorted(
            detection.entities, key=lambda item: item.span.start, reverse=True
        ):
            if entity.entity_type in self.policy.irreversible_types:
                replacement = f"[{entity.entity_type.value}_REDACTED]"
            else:
                replacement = self.session.token_for(entity.text, entity.entity_type)
            protected = (
                protected[: entity.span.start]
                + replacement
                + protected[entity.span.end :]
            )
        return BoguPreview(
            redacted_text=protected,
            entity_count=len(detection.entities),
            categories=dict(sorted(categories.items())),
            policy=self.policy.name,
        )

    def restore(
        self, text: str, *, metadata: dict[str, object] | None = None
    ) -> str:
        """Restore known placeholders, then run local inbound processors."""
        restored = self.session.restore(text)
        context = ProcessingContext("after_restoration", dict(metadata or {}))
        return run_processors(restored, self.postprocessors, context)

    def clear(self) -> int:
        """Irreversibly clear every private value in the local session."""
        return self.session.clear()
