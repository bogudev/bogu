from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import DetectionResult


@runtime_checkable
class Detector(Protocol):
    """
    Structural protocol for PII detectors.
    Any object with a `name` property and `detect()` method qualifies.
    """

    @property
    def name(self) -> str: ...

    def detect(self, text: str) -> DetectionResult: ...
