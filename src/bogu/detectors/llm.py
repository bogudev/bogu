from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from ..core.models import DetectionResult, Entity, EntityType, Span

_SYSTEM_PROMPT = """\
You are a PII (Personally Identifiable Information) extraction assistant.
Extract all PII from the user-provided text and return ONLY valid JSON.
No explanation, no markdown fences — just the raw JSON object.

Output schema:
{
  "entities": [
    {
      "text": "<exact substring copied from input>",
      "type": "<one of: PERSON, ORG, LOCATION, DATE, EMAIL, PHONE, SSN, \
CREDIT_CARD, IP_ADDRESS, API_KEY, URL, FINANCIAL, MEDICAL, OTHER>",
      "confidence": <float 0.0-1.0>,
      "start": <0-indexed character offset>,
      "end": <0-indexed character offset>
    }
  ]
}

Rules:
- "text" must be an exact copy-paste from the input (no paraphrasing).
- "start" and "end" are character offsets into the input string.
- If no PII is found, return {"entities": []}.
"""


class LLMDetector:
    """
    Level 3 — local LLM PII detector via llama-cpp-python.

    Requires a GGUF model file. Recommended: Mistral-7B-Instruct or
    Llama-3-8B-Instruct quantized to Q4_K_M for a good speed/accuracy balance.

    Requires: ``pip install bogu[advanced]``

    Parameters
    ----------
    model_path:
        Path to a GGUF model file.
    n_ctx:
        Context window size in tokens.
    n_gpu_layers:
        Layers to offload to GPU. 0 = CPU only, -1 = all layers.
    temperature:
        Sampling temperature. Keep at 0.0 for deterministic extraction.
    max_tokens:
        Maximum tokens for the model's JSON response.
    confidence_floor:
        Discard entities below this confidence score.
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        confidence_floor: float = 0.5,
    ) -> None:
        self._model_path = Path(model_path)
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._confidence_floor = confidence_floor
        self._llm: Any | None = None

    @property
    def name(self) -> str:
        return f"LLMDetector[{self._model_path.name}]"

    def _load(self) -> None:
        if self._llm is not None:
            return
        try:
            from llama_cpp import Llama  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "llama-cpp-python is not installed.\n"
                "  pip install bogu[advanced]"
            ) from exc
        if not self._model_path.exists():
            raise FileNotFoundError(
                f"GGUF model not found: {self._model_path}\n"
                "Download a model, e.g.:\n"
                "  huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF "
                "mistral-7b-instruct-v0.2.Q4_K_M.gguf --local-dir ./models"
            )
        self._llm = Llama(
            model_path=str(self._model_path),
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            verbose=False,
        )

    def detect(self, text: str) -> DetectionResult:
        self._load()
        raw_json = self._prompt(text)
        entities = self._parse(text, raw_json)
        return DetectionResult(original_text=text, entities=entities)

    def _prompt(self, text: str) -> str:
        llm = self._llm
        if llm is None:
            raise RuntimeError("LLM backend did not initialize")
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return cast(str, response["choices"][0]["message"]["content"].strip())

    def _parse(self, original_text: str, raw_json: str) -> list[Entity]:
        # Strip accidental markdown fences many models emit despite the instruction
        cleaned = raw_json.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else cleaned
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Graceful degradation — return empty rather than crashing
            return []

        entities: list[Entity] = []
        for item in data.get("entities", []):
            # Resolve EntityType — fall back to OTHER for unknown labels
            try:
                etype = EntityType(item["type"])
            except (ValueError, KeyError):
                etype = EntityType.OTHER

            confidence = float(item.get("confidence", 0.8))
            if confidence < self._confidence_floor:
                continue

            extracted_text = item.get("text", "")
            if not extracted_text:
                continue

            start = int(item.get("start", 0))
            end = int(item.get("end", start + len(extracted_text)))

            # Verify offsets — models often get them slightly wrong
            if original_text[start:end] != extracted_text:
                idx = original_text.find(extracted_text)
                if idx == -1:
                    # Model hallucinated a span that doesn't exist — discard
                    continue
                start, end = idx, idx + len(extracted_text)

            entities.append(
                Entity(
                    text=extracted_text,
                    entity_type=etype,
                    span=Span(start, end),
                    confidence=confidence,
                    source_detector=self.name,
                )
            )
        return entities
