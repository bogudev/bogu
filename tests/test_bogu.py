from bogu import Bogu, BoguPolicy, ProcessingContext, RegexDetector


class PrefixProcessor:
    name = "prefix"

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix
        self.stages = []

    def process(self, text: str, context: ProcessingContext) -> str:
        self.stages.append(context.stage)
        return self.prefix + text


def test_layer_applies_pre_and_post_processors() -> None:
    before = PrefixProcessor("outbound: ")
    after = PrefixProcessor("inbound: ")
    layer = Bogu(
        RegexDetector(), preprocessors=(before,), postprocessors=(after,)
    )
    preview = layer.protect("alice@example.com")
    restored = layer.restore("Reply for [EMAIL_1]")
    assert preview.redacted_text == "outbound: [EMAIL_1]"
    assert restored == "inbound: Reply for alice@example.com"
    assert before.stages == ["before_protection"]
    assert after.stages == ["after_restoration"]


def test_layer_automatically_uses_policy_examples() -> None:
    policy = BoguPolicy.from_examples({"ORG": ["Project Cedar"]})
    layer = Bogu(RegexDetector(), policy=policy)
    assert layer.protect("Project Cedar").redacted_text == "[ORG_1]"


def test_clear_makes_old_tokens_irreversible_and_resets_counters() -> None:
    layer = Bogu(RegexDetector())
    layer.protect("alice@example.com")
    assert layer.clear() == 1
    assert layer.restore("[EMAIL_1]") == "[EMAIL_1]"
    assert layer.protect("bob@example.com").redacted_text == "[EMAIL_1]"


def test_irreversible_values_never_enter_session() -> None:
    policy = BoguPolicy.from_examples(
        {}, name="strict", irreversible_types={"EMAIL"}
    )
    layer = Bogu(RegexDetector(), policy=policy)
    assert layer.protect("alice@example.com").redacted_text == "[EMAIL_REDACTED]"
    assert layer.session.private_value_count == 0
