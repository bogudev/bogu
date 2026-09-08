"""Local processing hooks for AI workflow integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

ProcessingStage = Literal["before_protection", "after_restoration"]


@dataclass
class ProcessingContext:
    """Metadata shared with local pre- and post-processors."""

    stage: ProcessingStage
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TextProcessor(Protocol):
    """A local transformation that can be composed around privacy protection."""

    @property
    def name(self) -> str: ...

    def process(self, text: str, context: ProcessingContext) -> str: ...


def run_processors(
    text: str,
    processors: tuple[TextProcessor, ...],
    context: ProcessingContext,
) -> str:
    """Apply processors in declaration order."""
    result = text
    for processor in processors:
        result = processor.process(result, context)
        if not isinstance(result, str):
            raise TypeError(f"Processor {processor.name!r} must return str")
    return result
