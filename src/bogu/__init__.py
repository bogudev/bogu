"""
Bogu — a local privacy layer for AI workflows.

Quick start
-----------
Level 1 (regex, zero deps):
    pip install bogu

Level 2 (NER):
    pip install "bogu[ner-spacy]"
    python -m spacy download en_core_web_sm
    # or
    pip install "bogu[ner-hf]"

Level 3 (local LLM):
    pip install "bogu[advanced]"
    # then download a GGUF model

Document/dataset adapters:
    pip install "bogu[adapters]"

Example
-------
    from bogu import create_pipeline, Anonymizer

    pipeline = create_pipeline("basic")
    anon = Anonymizer(pipeline)

    text = "Email me at alice@example.com or call 555-867-5309"
    anonymized, em = anon.anonymize(text)
    # "Email me at [EMAIL_1] or call [PHONE_1]"

    original = Anonymizer.deanonymize(anonymized, em)
    assert original == text
"""

from ._version import __version__
from .anonymizer.anonymizer import Anonymizer
from .anonymizer.entity_map import EntityMap
from .bogu import Bogu
from .core.models import DetectionResult, Entity, EntityType, Span
from .core.protocols import Detector
from .detectors.basic import RegexDetector
from .pipeline.factory import create_pipeline
from .pipeline.pipeline import PIIPipeline
from .policy import BoguPolicy, PolicyDetector
from .preview import BoguPreview, create_preview
from .processing import ProcessingContext, TextProcessor
from .session import BoguSession

__all__ = [
    "__version__",
    # Core types
    "Entity",
    "EntityType",
    "Span",
    "DetectionResult",
    "Detector",
    # Detectors
    "RegexDetector",
    # Pipeline
    "PIIPipeline",
    "create_pipeline",
    # Anonymizer
    "EntityMap",
    "Anonymizer",
    "BoguPolicy",
    "PolicyDetector",
    "BoguPreview",
    "create_preview",
    "Bogu",
    "BoguSession",
    "ProcessingContext",
    "TextProcessor",
]

# Optional imports — available from their submodules to avoid triggering
# ImportError for users who haven't installed optional deps:
#
#   from bogu.detectors.ner import NERDetector
#   from bogu.detectors.llm import LLMDetector
#   from bogu.adapters.document import DocumentAnonymizer
#   from bogu.adapters.dataset import DatasetAnonymizer
