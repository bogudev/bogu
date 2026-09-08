from __future__ import annotations

from ..core.models import DetectionResult, Entity
from ..core.protocols import Detector
from ..core.span_utils import merge_entities, sort_entities


class PIIPipeline:
    """
    Composes multiple Detectors, runs them in sequence, and merges results
    using the span-deduplication algorithm.

    Parameters
    ----------
    detectors:
        One or more Detector-conforming objects.
    """

    def __init__(self, detectors: list[Detector]) -> None:
        if not detectors:
            raise ValueError("PIIPipeline requires at least one detector.")
        self._detectors = list(detectors)

    @property
    def detectors(self) -> list[Detector]:
        return list(self._detectors)

    def run(self, text: str) -> DetectionResult:
        """Run all detectors and return a merged, deduplicated DetectionResult."""
        all_entities: list[Entity] = []
        for detector in self._detectors:
            result = detector.detect(text)
            all_entities.extend(result.entities)

        merged = merge_entities(all_entities)
        ordered = sort_entities(merged)
        return DetectionResult(original_text=text, entities=ordered)

    # Make the pipeline itself a Detector so it can be nested or passed to Anonymizer
    def detect(self, text: str) -> DetectionResult:
        return self.run(text)

    @property
    def name(self) -> str:
        names = ", ".join(d.name for d in self._detectors)
        return f"PIIPipeline[{names}]"

    def __repr__(self) -> str:
        return self.name
