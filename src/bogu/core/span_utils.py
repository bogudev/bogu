from __future__ import annotations

from .models import Entity


def merge_entities(entities: list[Entity]) -> list[Entity]:
    """
    Deduplicate and merge overlapping entity spans.

    Sort by (span.start ASC, span length DESC, confidence DESC) then sweep
    left-to-right. For each candidate:
    - If fully contained by an accepted entity → skip.
    - If it fully contains an accepted entity → replace accepted.
    - Partial overlap → keep the higher-confidence one; tie → keep longer span.
    """
    if not entities:
        return []

    sorted_candidates = sorted(
        entities,
        key=lambda e: (e.span.start, -len(e.span), -e.confidence),
    )

    accepted: list[Entity] = []

    for candidate in sorted_candidates:
        dominated = False
        to_remove: list[Entity] = []

        for accepted_entity in accepted:
            # No overlap — skip comparison
            if not candidate.span.overlaps(accepted_entity.span):
                continue

            if accepted_entity.span.contains(candidate.span):
                # Candidate is fully inside an accepted span → skip candidate
                dominated = True
                break

            if candidate.span.contains(accepted_entity.span):
                # Candidate contains an accepted span → replace accepted
                to_remove.append(accepted_entity)
                continue

            # Partial overlap → compare quality
            if accepted_entity.confidence > candidate.confidence:
                dominated = True
                break
            elif candidate.confidence > accepted_entity.confidence:
                to_remove.append(accepted_entity)
            else:
                # Equal confidence: keep longer span
                if len(candidate.span) > len(accepted_entity.span):
                    to_remove.append(accepted_entity)
                else:
                    dominated = True
                    break

        if not dominated:
            for r in to_remove:
                accepted.remove(r)
            accepted.append(candidate)

    return sort_entities(accepted)


def sort_entities(entities: list[Entity]) -> list[Entity]:
    """Sort entities by their start offset."""
    return sorted(entities, key=lambda e: e.span.start)
