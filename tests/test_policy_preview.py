from bogu import (
    BoguPolicy,
    EntityType,
    PIIPipeline,
    PolicyDetector,
    RegexDetector,
    create_preview,
)


def test_policy_accepts_literal_examples() -> None:
    policy = BoguPolicy.from_examples({"ORG": ["Project Cedar"]})
    result = PolicyDetector(policy).detect("Notes for Project Cedar")
    assert result.entities[0].entity_type is EntityType.ORG


def test_preview_contains_redacted_payload_and_safe_summary() -> None:
    preview, mapping = create_preview(
        "Email alice@example.com", PIIPipeline([RegexDetector()])
    )
    assert preview.redacted_text == "Email [EMAIL_1]"
    assert preview.categories == {"EMAIL": 1}
    assert "alice@example.com" not in repr(preview)
    assert len(mapping) == 1


def test_irreversible_policy_does_not_store_value() -> None:
    policy = BoguPolicy(
        name="strict", irreversible_types=frozenset({EntityType.EMAIL})
    )
    preview, mapping = create_preview(
        "alice@example.com", RegexDetector(), policy=policy
    )
    assert preview.redacted_text == "[EMAIL_REDACTED]"
    assert len(mapping) == 0
