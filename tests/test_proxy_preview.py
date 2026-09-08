from dataclasses import dataclass

from bogu.proxy import BoguClient


@dataclass
class _Message:
    content: str


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Response:
    choices: list[_Choice]


class _Completions:
    def __init__(self) -> None:
        self.calls = 0
        self.last_messages = []

    def create(self, *, messages, **_kwargs):
        self.calls += 1
        self.last_messages = messages
        return _Response([_Choice(_Message("Reply to [EMAIL_1]"))])


class _Client:
    def __init__(self) -> None:
        self.chat = type("Chat", (), {"completions": _Completions()})()


def test_preview_does_not_send_until_explicit_send() -> None:
    raw = _Client()
    client = BoguClient(raw, verbose=False)
    pending = client.preview(
        messages=[{"role": "user", "content": "Email alice@example.com"}],
        model="example",
    )
    assert raw.chat.completions.calls == 0
    assert "alice@example.com" not in pending.preview.redacted_text
    response = client.send(pending)
    assert raw.chat.completions.calls == 1
    assert "alice@example.com" not in raw.chat.completions.last_messages[0]["content"]
    assert response.content == "Reply to alice@example.com"


def test_clear_session_forgets_local_values() -> None:
    client = BoguClient(_Client(), verbose=False)
    client.preview(messages=[{"role": "user", "content": "alice@example.com"}])
    assert client.session_map
    client.clear_session()
    assert client.session_map == {}


def test_default_audit_summary_does_not_print_private_values() -> None:
    client = BoguClient(_Client(), verbose=False)
    response = client.send(
        client.preview(
            messages=[{"role": "user", "content": "alice@example.com"}]
        )
    )
    assert "alice@example.com" not in response.audit.summary()
    assert "alice@example.com" in response.audit.summary(include_sensitive=True)
