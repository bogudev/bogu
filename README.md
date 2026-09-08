# Bogu

**Bogu** is a local-first Python toolkit for detecting and redacting private
information before text or documents are sent to an LLM or another third party.
The original values and reversible token map stay in your process.

Source and issue tracking: [github.com/bogudev/bogu](https://github.com/bogudev/bogu)

> Detection is best-effort. Review previews for sensitive or regulated data.

## Install

The default install is lightweight, has no runtime dependencies, and does **not**
include OpenAI Privacy Filter:

```bash
pip install bogu
```

Install optional capabilities only when needed:

```bash
pip install 'bogu[adapters]'       # PDF, DOCX, and datasets
pip install 'bogu[ner-spacy]'      # spaCy NER
```

OpenAI Privacy Filter is not currently distributed through PyPI. To use it,
install OPF directly and then opt in when creating the pipeline:

```bash
pip install 'opf @ git+https://github.com/openai/privacy-filter.git'
```

## Local redaction preview

```python
from bogu import RegexDetector, create_preview

preview, bogu_session = create_preview(
    "Email alice@example.com",
    RegexDetector(),
)
print(preview.redacted_text)  # Email [EMAIL_1]
print(preview.categories)     # {'EMAIL': 1}
```

`create_preview` performs no network operation. Keep or display the returned
preview for approval, then send only `preview.redacted_text`.

For an OpenAI-compatible client, the transmission boundary is explicit:

```python
from openai import OpenAI
from bogu.proxy import BoguClient

client = BoguClient(OpenAI(), verbose=False)
pending = client.preview(
    messages=[{"role": "user", "content": "Email alice@example.com"}],
    model="gpt-4o-mini",
)

print(pending.preview.redacted_text)  # inspect or ask for approval
response = client.send(pending)       # the first network call
client.clear_session()                # forget all local restoration values
```

## Custom policies from examples

Teach the detector private vocabulary without writing regular expressions:

```python
from bogu import PIIPipeline, PolicyDetector, BoguPolicy, RegexDetector

policy = BoguPolicy.from_examples(
    {"ORG": ["Project Cedar"], "ACCOUNT_NUMBER": ["CUSTOMER-42"]},
    name="internal",
    irreversible_types={"ACCOUNT_NUMBER"},
)
pipeline = PIIPipeline([RegexDetector(), PolicyDetector(policy)])
```

Values in `irreversible_types` become `[TYPE_REDACTED]` and are never added to
the restoration map. Other values use stable tokens such as `[ORG_1]`.

## Optional enhanced local detection

```python
from bogu import create_pipeline

pipeline = create_pipeline("basic", openai_privacy_filter=True)
```

This flag is opt-in and requires OPF to be installed separately. Without it,
OPF is neither installed nor imported.

## Reusable privacy layer

Use `Bogu` when integrating another AI SDK, queue, API, or storage
system:

```python
from bogu import Bogu, RegexDetector

bogu = Bogu(RegexDetector())
outbound = bogu.protect("alice@example.com")
# review outbound, then transmit outbound.redacted_text
inbound = bogu.restore("Result for [EMAIL_1]")
bogu.clear()
```

The layer accepts ordered `preprocessors` and `postprocessors`. Every processor
runs locally and implements:

```python
class Processor:
    name = "example"

    def process(self, text, context):
        # context.stage is "before_protection" or "after_restoration"
        return text
```

This extension boundary is intended for future local privacy-filter passes,
structured serialization, and database field filtering without embedding those
concerns in the detector or a vendor-specific client.

## Architecture

- **Detectors** locate sensitive spans and never mutate input.
- **Policies** add private examples and choose reversible or permanent removal.
- **Bogu** coordinates local processors, protection, and restoration.
- **BoguSession** owns the in-memory private map and its lifecycle.
- **Adapters** read documents and datasets without writing or transmitting them.
- **Proxy clients** provide explicit `preview()` and `send()` boundaries.

Private mappings are not persisted automatically. `BoguSession.export()` is
an explicit escape hatch for caller-managed encrypted persistence; avoid storing
its output in logs or plaintext databases.

## Roadmap

- Optional OpenAI Privacy Filter as a configurable local protection processor.
- Schema-aware serialization filters for JSON and database records.
- Async and streaming client adapters.
- Encrypted, expiring session stores with pluggable backends.
- Policy import/export with validation and versioning.

## Development

```bash
python -m pip install -e '.[dev]'
PYTHONPATH=src pytest -m 'not slow'
```

Licensed under MIT.

See [PUBLISHING.md](PUBLISHING.md) for the GitHub and PyPI release checklist.
Contributions are covered by [CONTRIBUTING.md](CONTRIBUTING.md), community
behavior by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and private vulnerability
reports by [SECURITY.md](SECURITY.md). Release history is recorded in
[CHANGELOG.md](CHANGELOG.md).
