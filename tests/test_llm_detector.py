"""
LLM detector tests.

Requires a GGUF model file. Pass it with:
    pytest tests/test_llm_detector.py --model-path ./models/mistral.gguf

All tests are skipped if --model-path is not provided.
"""

from __future__ import annotations

import pytest

from bogu import EntityType


@pytest.fixture
def llm_detector(model_path: str | None):  # type: ignore[no-untyped-def]
    if model_path is None:
        pytest.skip("--model-path not provided; skipping LLM tests.")
    from bogu.detectors.llm import LLMDetector

    return LLMDetector(model_path=model_path)


@pytest.mark.llm
def test_llm_detects_person(llm_detector) -> None:  # type: ignore[no-untyped-def]
    result = llm_detector.detect("Patient John Smith was admitted on 2024-01-15.")
    assert result.by_type(EntityType.PERSON), "Expected PERSON"


@pytest.mark.llm
def test_llm_detects_email(llm_detector) -> None:  # type: ignore[no-untyped-def]
    result = llm_detector.detect("Contact dr.jones@hospital.org for a referral.")
    emails = result.by_type(EntityType.EMAIL)
    assert emails


@pytest.mark.llm
def test_llm_empty_when_no_pii(llm_detector) -> None:  # type: ignore[no-untyped-def]
    result = llm_detector.detect("The weather is sunny today.")
    assert not result.has_pii


def test_llm_parse_malformed_json_returns_empty() -> None:
    from pathlib import Path

    from bogu.detectors.llm import LLMDetector

    det = LLMDetector.__new__(LLMDetector)
    det._model_path = Path("fake.gguf")
    det._confidence_floor = 0.5
    entities = det._parse("some text", "this is not json {{{")
    assert entities == []


def test_llm_parse_hallucinated_span_discarded() -> None:
    import json
    from pathlib import Path

    from bogu.detectors.llm import LLMDetector

    det = LLMDetector.__new__(LLMDetector)
    det._model_path = Path("fake.gguf")
    det._confidence_floor = 0.5

    # "FAKE_NAME" does not appear in original_text
    raw = json.dumps({"entities": [
        {"text": "FAKE_NAME", "type": "PERSON", "confidence": 0.9, "start": 0, "end": 9}
    ]})
    entities = det._parse("completely different text", raw)
    assert entities == []


def test_llm_parse_offset_correction() -> None:
    import json
    from pathlib import Path

    from bogu.detectors.llm import LLMDetector

    det = LLMDetector.__new__(LLMDetector)
    det._model_path = Path("fake.gguf")
    det._confidence_floor = 0.5

    original = "Call John Smith today."
    # Provide wrong offsets — parser should find-and-correct
    raw = json.dumps(
        {
            "entities": [
                {
                    "text": "John Smith",
                    "type": "PERSON",
                    "confidence": 0.95,
                    "start": 99,
                    "end": 109,
                }
            ]
        }
    )
    entities = det._parse(original, raw)
    assert len(entities) == 1
    assert entities[0].text == "John Smith"
    assert original[entities[0].span.start: entities[0].span.end] == "John Smith"


def test_llm_import_error_without_llama_cpp(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    original_import = builtins.__import__

    def mock_import(name: str, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "llama_cpp":
            raise ImportError("mocked missing llama_cpp")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    from bogu.detectors.llm import LLMDetector

    det = LLMDetector(model_path="./fake.gguf")
    with pytest.raises(ImportError, match="llama-cpp-python"):
        det.detect("test")
