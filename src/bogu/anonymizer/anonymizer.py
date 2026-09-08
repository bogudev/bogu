from __future__ import annotations

import re

from ..core.protocols import Detector
from .entity_map import EntityMap


class Anonymizer:
    """
    Wraps any Detector (or PIIPipeline) and performs reversible
    placeholder-based anonymization.

    Parameters
    ----------
    detector:
        Any object conforming to the Detector protocol, including a PIIPipeline.
    """

    def __init__(self, detector: Detector) -> None:
        self._detector = detector

    def anonymize(
        self,
        text: str,
        *,
        entity_map: EntityMap | None = None,
    ) -> tuple[str, EntityMap]:
        """
        Detect PII and replace each entity with a ``[TYPE_N]`` placeholder.

        Parameters
        ----------
        text:
            Input text to anonymize.
        entity_map:
            Existing session map to extend (enables multi-turn consistency).
            If None, a fresh map is created.

        Returns
        -------
        tuple[str, EntityMap]
            ``(anonymized_text, entity_map)`` where entity_map holds all
            token↔original mappings needed for de-anonymization.
        """
        em = entity_map if entity_map is not None else EntityMap()
        result = self._detector.detect(text)

        # Replace spans right-to-left so earlier character offsets stay valid
        # after each substitution changes the string length.
        sorted_entities = sorted(
            result.entities, key=lambda e: e.span.start, reverse=True
        )

        anonymized = text
        for entity in sorted_entities:
            token = em.get_or_create_token(entity.text, entity.entity_type)
            anonymized = (
                anonymized[: entity.span.start]
                + token
                + anonymized[entity.span.end :]
            )

        return anonymized, em

    @staticmethod
    def deanonymize(anonymized_text: str, entity_map: EntityMap) -> str:
        """
        Replace all ``[TYPE_N]`` tokens in `anonymized_text` with their
        original values using `entity_map`.

        Uses a single-pass regex substitution for efficiency.
        """
        tokens = list(entity_map.to_dict().keys())
        if not tokens:
            return anonymized_text

        pattern = re.compile("|".join(re.escape(t) for t in tokens))
        return pattern.sub(
            lambda m: entity_map.resolve(m.group()) or m.group(),
            anonymized_text,
        )
