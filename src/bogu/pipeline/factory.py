from __future__ import annotations

from pathlib import Path
from typing import Literal

from ..core.protocols import Detector
from ..detectors.basic import RegexDetector
from .pipeline import PIIPipeline

Level = Literal["basic", "mid", "advanced"]
NERBackend = Literal["spacy", "huggingface"]


def create_pipeline(
    level: Level = "basic",
    *,
    ner_backend: NERBackend = "spacy",
    ner_model: str | None = None,
    llm_model_path: str | Path | None = None,
    include_regex: bool = True,
    openai_privacy_filter: bool = False,
) -> PIIPipeline:
    """
    Convenience factory that builds a PIIPipeline for the requested accuracy level.

    Parameters
    ----------
    level:
        "basic"    — RegexDetector only. Zero extra dependencies.
        "mid"      — RegexDetector + NERDetector.
                     Requires ``pip install bogu[ner-spacy]`` or
                     ``pip install bogu[ner-hf]``.
        "advanced" — RegexDetector + NERDetector + LLMDetector.
                     Requires ``pip install bogu[advanced]`` and a GGUF model.
    ner_backend:
        "spacy" or "huggingface". Only relevant at "mid" and "advanced" levels.
    ner_model:
        Override the default NER model name.
    llm_model_path:
        Path to a GGUF model file. Required when level="advanced".
    include_regex:
        Whether to include RegexDetector at every level. Default True.
    openai_privacy_filter:
        Opt in to the separately installed OpenAI Privacy Filter detector. The
        default package and pipeline never import it.
    """
    if level not in {"basic", "mid", "advanced"}:
        raise ValueError("level must be one of: basic, mid, advanced")

    detectors: list[Detector] = []

    if include_regex:
        detectors.append(RegexDetector())

    if level in ("mid", "advanced"):
        # Deferred import — keeps this module importable without NER deps installed
        from ..detectors.ner import NERDetector  # noqa: PLC0415

        detectors.append(NERDetector(backend=ner_backend, model=ner_model))

    if level == "advanced":
        from ..detectors.llm import LLMDetector  # noqa: PLC0415

        if llm_model_path is None:
            raise ValueError(
                "llm_model_path is required for level='advanced'.\n"
                "Download a GGUF model and pass its path, e.g.:\n"
                "  create_pipeline('advanced', llm_model_path='./models/mistral.gguf')"
            )
        detectors.append(LLMDetector(model_path=llm_model_path))

    if openai_privacy_filter:
        from ..detectors.openai_privacy_filter import (  # noqa: PLC0415
            OpenAIPrivacyFilterDetector,
        )

        detectors.append(OpenAIPrivacyFilterDetector())

    return PIIPipeline(detectors)
