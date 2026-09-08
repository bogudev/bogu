"""Local detector adapter for OpenAI Privacy Filter (OPF)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from ..core.models import DetectionResult, Entity, EntityType, Span

_LABEL_MAP: dict[str, EntityType] = {
    "private_person": EntityType.PERSON,
    "private_address": EntityType.ADDRESS,
    "private_email": EntityType.EMAIL,
    "private_phone": EntityType.PHONE,
    "private_url": EntityType.URL,
    "private_date": EntityType.DATE,
    "account_number": EntityType.ACCOUNT_NUMBER,
    "secret": EntityType.SECRET,
}


class OpenAIPrivacyFilterDetector:
    """Detect privacy spans with OpenAI Privacy Filter running locally."""

    def __init__(
        self,
        *,
        model: str | Path | None = None,
        device: Literal["cpu", "cuda"] = "cpu",
        redactor_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._model = model
        self._device = device
        self._redactor_factory = redactor_factory
        self._redactor: Any | None = None

    @property
    def name(self) -> str:
        return "OpenAIPrivacyFilterDetector[local]"

    def _load(self) -> None:
        if self._redactor is not None:
            return
        factory = self._redactor_factory
        if factory is None:
            try:
                from opf import OPF
            except ImportError as exc:
                raise ImportError(
                    "OpenAI Privacy Filter is not installed. Install OPF from "
                    "https://github.com/openai/privacy-filter before enabling it."
                ) from exc
            factory = OPF
        self._redactor = factory(
            model=self._model,
            device=self._device,
            output_mode="typed",
        )

    def detect(self, text: str) -> DetectionResult:
        self._load()
        redactor = self._redactor
        if redactor is None:
            raise RuntimeError("OpenAI Privacy Filter did not initialize")
        result = redactor.redact(text)
        if isinstance(result, str):
            raise RuntimeError("OPF must return structured typed output")

        entities: list[Entity] = []
        for detected in result.detected_spans:
            entity_type = _LABEL_MAP.get(detected.label)
            if entity_type is None:
                continue
            entities.append(
                Entity(
                    text=detected.text,
                    entity_type=entity_type,
                    span=Span(detected.start, detected.end),
                    confidence=1.0,
                    source_detector=self.name,
                    metadata={"label": detected.label},
                )
            )
        return DetectionResult(original_text=text, entities=entities)
