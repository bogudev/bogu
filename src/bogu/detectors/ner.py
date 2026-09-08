from __future__ import annotations

from typing import Any, Literal

from ..core.models import DetectionResult, Entity, EntityType, Span

# Covers both spaCy v3 labels and dslim/bert-base-NER labels
_LABEL_MAP: dict[str, EntityType] = {
    "PER": EntityType.PERSON,
    "PERSON": EntityType.PERSON,
    "ORG": EntityType.ORG,
    "LOC": EntityType.LOCATION,
    "GPE": EntityType.LOCATION,
    "DATE": EntityType.DATE,
    "TIME": EntityType.DATE,
}

Backend = Literal["spacy", "huggingface"]


class NERDetector:
    """
    Level 2 — NER-based PII detector.

    Supports two backends (configurable at construction time):
    - "spacy": requires ``pip install bogu[ner-spacy]``
      then ``python -m spacy download en_core_web_sm``
    - "huggingface": requires ``pip install bogu[ner-hf]``

    The underlying model is loaded **lazily** on the first call to detect().

    Parameters
    ----------
    backend:
        "spacy" or "huggingface".
    model:
        Override the default model name.
        spaCy default: "en_core_web_sm"
        HuggingFace default: "dslim/bert-base-NER"
    device:
        For HuggingFace: "cpu" or "cuda".
    confidence_threshold:
        Minimum score for HuggingFace entities (spaCy doesn't expose per-entity
        scores from the standard pipeline, so this only applies to HF).
    """

    def __init__(
        self,
        backend: Backend = "spacy",
        *,
        model: str | None = None,
        device: str = "cpu",
        confidence_threshold: float = 0.7,
    ) -> None:
        self._backend = backend
        self._model_name = model or self._default_model(backend)
        self._device = device
        self._threshold = confidence_threshold
        self._loaded = False
        self._nlp: Any | None = None

    @property
    def name(self) -> str:
        return f"NERDetector[{self._backend}]"

    @staticmethod
    def _default_model(backend: Backend) -> str:
        return "en_core_web_sm" if backend == "spacy" else "dslim/bert-base-NER"

    # ------------------------------------------------------------------
    # Lazy loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._loaded:
            return
        if self._backend == "spacy":
            self._load_spacy()
        else:
            self._load_hf()
        self._loaded = True

    def _load_spacy(self) -> None:
        try:
            import spacy  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "spaCy is not installed.\n"
                "  pip install bogu[ner-spacy]\n"
                "  python -m spacy download en_core_web_sm"
            ) from exc
        try:
            self._nlp = spacy.load(self._model_name)
        except OSError as exc:
            raise OSError(
                f"spaCy model '{self._model_name}' not found.\n"
                f"  python -m spacy download {self._model_name}"
            ) from exc

    def _load_hf(self) -> None:
        try:
            from transformers import pipeline  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "transformers is not installed.\n"
                "  pip install bogu[ner-hf]"
            ) from exc
        self._nlp = pipeline(
            "ner",
            model=self._model_name,
            aggregation_strategy="simple",
            device=0 if self._device == "cuda" else -1,
        )

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def detect(self, text: str) -> DetectionResult:
        self._load()
        if self._backend == "spacy":
            return self._detect_spacy(text)
        return self._detect_hf(text)

    def _detect_spacy(self, text: str) -> DetectionResult:
        if self._nlp is None:
            raise RuntimeError("NER backend did not initialize")
        doc = self._nlp(text)
        entities: list[Entity] = []
        for ent in doc.ents:
            etype = _LABEL_MAP.get(ent.label_)
            if etype is None:
                continue
            entities.append(
                Entity(
                    text=ent.text,
                    entity_type=etype,
                    span=Span(ent.start_char, ent.end_char),
                    confidence=1.0,
                    source_detector=self.name,
                    metadata={"label": ent.label_},
                )
            )
        return DetectionResult(original_text=text, entities=entities)

    def _detect_hf(self, text: str) -> DetectionResult:
        if self._nlp is None:
            raise RuntimeError("NER backend did not initialize")
        raw = self._nlp(text)
        entities: list[Entity] = []
        for item in raw:
            score = float(item["score"])
            if score < self._threshold:
                continue
            etype = _LABEL_MAP.get(item["entity_group"])
            if etype is None:
                continue
            entities.append(
                Entity(
                    text=item["word"],
                    entity_type=etype,
                    span=Span(int(item["start"]), int(item["end"])),
                    confidence=score,
                    source_detector=self.name,
                    metadata={"label": item["entity_group"]},
                )
            )
        return DetectionResult(original_text=text, entities=entities)
