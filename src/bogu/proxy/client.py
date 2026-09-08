"""
BoguClient — drop-in LLM client wrapper that anonymizes PII before every
request and restores it from the response.

Drop-in usage
-------------
    # Before
    client = OpenAI()
    response = client.chat.completions.create(messages=[...], model="gpt-4o-mini")

    # After (one-line change)
    from bogu.proxy import BoguClient
    client = BoguClient(OpenAI())
    response = client.chat.completions.create(messages=[...], model="gpt-4o-mini")

The proxy:
  1. Detects PII in every message using the configured pipeline.
  2. Replaces each PII value with a deterministic token, e.g. [EMAIL_1].
  3. Forwards the sanitized messages to the underlying LLM client.
  4. Scans the response and restores the original values.
  5. Prints a colour-coded audit log (disable with verbose=False).

Session scope
-------------
An EntityMap is kept alive for the lifetime of the proxy instance, so the
same original value always maps to the same token across a multi-turn
conversation.  Call proxy.reset_session() to start a fresh session.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Any

from ..bogu import Bogu
from ..pipeline.factory import Level, NERBackend, create_pipeline
from ..pipeline.pipeline import PIIPipeline
from ..policy import BoguPolicy
from ..preview import BoguPreview
from ..processing import TextProcessor

# ── ANSI colours (disabled automatically on non-TTY outputs) ─────────────────
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _c(colour: str, text: str) -> str:
    return f"{colour}{text}{_RESET}"


# ── Audit log ─────────────────────────────────────────────────────────────────


@dataclass
class AuditEntry:
    """Immutable record of one anonymize→LLM→deanonymize round-trip."""

    original_messages: list[dict[str, str]] = field(repr=False)
    sanitized_messages: list[dict[str, str]]
    token_map: dict[str, str] = field(repr=False)  # token → original
    raw_response: str
    restored_response: str
    pii_found: int

    def summary(self, *, include_sensitive: bool = False) -> str:
        lines = [
            _c(_BOLD, "┌─── Bogu Client — Audit Log ─────────────────────────────────"),
            _c(_BOLD, f"│  PII entities found & replaced: {self.pii_found}"),
        ]
        if include_sensitive and self.token_map:
            lines.append(_c(_YELLOW, "│  Token map (what was sent → original):"))
            for token, original in self.token_map.items():
                lines.append(f"│    {_c(_RED, token)}  →  {_c(_GREEN, original)}")
        lines.append(_c(_CYAN, "│"))
        lines.append(_c(_CYAN, "│  ── Sanitized messages sent to LLM ───────────"))
        for msg in self.sanitized_messages:
            role = msg.get("role", "?").upper()
            content = textwrap.indent(msg.get("content", ""), "│    ")
            lines.append(f"│  [{_c(_BOLD, role)}]\n{content}")
        lines.append(_c(_CYAN, "│"))
        lines.append(_c(_CYAN, "│  ── Raw LLM response ─────────────────────────"))
        lines.append(textwrap.indent(self.raw_response, "│    "))
        lines.append(_c(_CYAN, "│"))
        lines.append(_c(_GREEN, "│  ── Restored response (PII back) ─────────────"))
        if include_sensitive:
            lines.append(textwrap.indent(self.restored_response, "│    "))
        else:
            lines.append("│    [hidden; use include_sensitive=True to display]")
        lines.append(_c(_BOLD, "└───────────────────────────────────────────────"))
        return "\n".join(lines)


# ── Thin proxy shims (mirror OpenAI's client.chat.completions.create path) ───


class _CompletionsProxy:
    def __init__(self, proxy: BoguClient) -> None:
        self._proxy = proxy

    def create(
        self,
        *,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> _ProxyResponse:
        return self._proxy._create(messages=messages, **kwargs)


class _ChatProxy:
    def __init__(self, proxy: BoguClient) -> None:
        self.completions = _CompletionsProxy(proxy)


@dataclass
class _ProxyResponse:
    """Minimal response wrapper — mirrors openai.ChatCompletion just enough."""

    content: str
    audit: AuditEntry
    _raw: Any = field(repr=False)  # original openai response object

    # Mirror the real OpenAI response shape so existing code doesn't break.
    @property
    def choices(self) -> list[_Choice]:
        return [_Choice(self.content)]


@dataclass
class _Choice:
    content: str

    @property
    def message(self) -> _Message:
        return _Message(self.content)


@dataclass
class _Message:
    content: str


@dataclass(frozen=True)
class PendingRequest:
    """A locally sanitized request that has not been sent anywhere yet."""

    messages: list[dict[str, Any]]
    kwargs: dict[str, Any]
    preview: BoguPreview
    original_messages: list[dict[str, Any]] = field(repr=False)


# ── Main proxy ────────────────────────────────────────────────────────────────


class BoguClient:
    """
    Wraps any OpenAI-compatible client with a PII anonymize/deanonymize layer.

    Parameters
    ----------
    client:
        An ``openai.OpenAI`` (or compatible) instance.
    pipeline:
        A PIIPipeline to use for detection.  Defaults to ``create_pipeline("basic")``.
    level:
        Shorthand for building a pipeline when no explicit pipeline is given.
        Ignored if ``pipeline`` is provided.
    verbose:
        Print the colour-coded audit log after each call.  Default True.
    """

    def __init__(
        self,
        client: Any,
        *,
        pipeline: PIIPipeline | None = None,
        level: Level = "basic",
        ner_backend: NERBackend = "spacy",
        verbose: bool = True,
        sensitive_audit: bool = False,
        policy: BoguPolicy | None = None,
        preprocessors: tuple[TextProcessor, ...] = (),
        postprocessors: tuple[TextProcessor, ...] = (),
    ) -> None:
        self._client = client
        self._pipeline = pipeline or create_pipeline(level, ner_backend=ner_backend)
        self._privacy = Bogu(
            self._pipeline,
            policy=policy,
            preprocessors=preprocessors,
            postprocessors=postprocessors,
        )
        self.verbose = verbose
        self.sensitive_audit = sensitive_audit

        # Mirror OpenAI client attribute path
        self.chat = _ChatProxy(self)

    # ── Public API ────────────────────────────────────────────────────────────

    def reset_session(self) -> None:
        """Wipe the current session token map and start fresh."""
        self._privacy.clear()

    clear_session = reset_session

    def preview(
        self, *, messages: list[dict[str, Any]], **kwargs: Any
    ) -> PendingRequest:
        """Sanitize locally and return the exact request without transmitting it."""
        sanitized_messages: list[dict[str, Any]] = []
        categories: dict[str, int] = {}
        entity_count = 0
        for message in messages:
            sanitized = dict(message)
            content = message.get("content")
            if isinstance(content, str):
                result = self._privacy.protect(
                    content, metadata={"role": message.get("role", "unknown")}
                )
                entity_count += result.entity_count
                for kind, count in result.categories.items():
                    categories[kind] = categories.get(kind, 0) + count
                sanitized["content"] = result.redacted_text
            sanitized_messages.append(sanitized)
        rendered = "\n\n".join(
            f"[{message.get('role', 'unknown')}]\n{message.get('content', '')}"
            for message in sanitized_messages
        )
        return PendingRequest(
            messages=sanitized_messages,
            kwargs=dict(kwargs),
            preview=BoguPreview(
                redacted_text=rendered,
                entity_count=entity_count,
                categories=dict(sorted(categories.items())),
                policy="standard",
            ),
            original_messages=[dict(message) for message in messages],
        )

    def send(self, pending: PendingRequest) -> _ProxyResponse:
        """Send a previously reviewed request to the wrapped third-party client."""
        raw_response = self._client.chat.completions.create(
            messages=pending.messages, **pending.kwargs
        )
        raw_text = raw_response.choices[0].message.content
        restored = self._privacy.restore(raw_text)
        audit = AuditEntry(
            original_messages=[dict(message) for message in pending.original_messages],
            sanitized_messages=[dict(message) for message in pending.messages],
            token_map=self._privacy.session.export(),
            raw_response=raw_text,
            restored_response=restored,
            pii_found=pending.preview.entity_count,
        )
        if self.verbose:
            print(audit.summary(include_sensitive=self.sensitive_audit))
        return _ProxyResponse(content=restored, audit=audit, _raw=raw_response)

    @property
    def session_map(self) -> dict[str, str]:
        """Read-only view of the current token → original mapping."""
        return self._privacy.session.export()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _create(
        self,
        *,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> _ProxyResponse:
        return self.send(self.preview(messages=messages, **kwargs))
