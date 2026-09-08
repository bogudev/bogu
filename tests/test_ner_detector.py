"""
NER detector tests.

spaCy tests: pytest tests/test_ner_detector.py -k spacy
  Requires: pip install "bogu[ner-spacy]" && python -m spacy download en_core_web_sm

HuggingFace tests: pytest tests/test_ner_detector.py -k huggingface
  Requires: pip install "bogu[ner-hf]"
  Note: first run downloads ~400MB model.
"""

import pytest

from bogu import EntityType


@pytest.mark.slow
def test_spacy_person_detected() -> None:
    from bogu.detectors.ner import NERDetector

    det = NERDetector(backend="spacy")
    result = det.detect("Barack Obama visited Chicago last week.")
    assert result.by_type(EntityType.PERSON), "Expected PERSON entity"
    assert result.by_type(EntityType.LOCATION), "Expected LOCATION entity"


@pytest.mark.slow
def test_spacy_lazy_load_does_not_raise_on_construction() -> None:
    from bogu.detectors.ner import NERDetector

    # Should not raise — model is not loaded yet
    det = NERDetector(backend="spacy")
    assert det.name == "NERDetector[spacy]"


@pytest.mark.slow
def test_spacy_missing_model_raises_on_detect(monkeypatch: pytest.MonkeyPatch) -> None:
    from bogu.detectors.ner import NERDetector

    det = NERDetector(backend="spacy", model="nonexistent_model_xyz")
    with pytest.raises(OSError, match="not found"):
        det.detect("Hello world")


@pytest.mark.slow
def test_huggingface_person_detected() -> None:
    from bogu.detectors.ner import NERDetector

    det = NERDetector(backend="huggingface")
    result = det.detect("Angela Merkel was the Chancellor of Germany.")
    assert result.by_type(EntityType.PERSON)


@pytest.mark.slow
def test_huggingface_lazy_load() -> None:
    from bogu.detectors.ner import NERDetector

    det = NERDetector(backend="huggingface")
    assert det.name == "NERDetector[huggingface]"
    assert not det._loaded


def test_ner_import_error_without_spacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing NERDetector succeeds; ImportError is deferred to detect()."""
    import builtins

    original_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "spacy":
            raise ImportError("mocked missing spacy")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    from bogu.detectors.ner import NERDetector

    det = NERDetector(backend="spacy")
    with pytest.raises(ImportError, match="spaCy is not installed"):
        det.detect("test")
