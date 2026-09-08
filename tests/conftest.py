import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--model-path",
        action="store",
        default=None,
        help="Path to a GGUF model file for LLM detector tests.",
    )


@pytest.fixture
def model_path(request: pytest.FixtureRequest) -> str | None:
    return request.config.getoption("--model-path")


# ---------------------------------------------------------------------------
# Sample texts
# ---------------------------------------------------------------------------

SAMPLE_WITH_EMAIL = "Contact Alice at alice@example.com for details."
SAMPLE_WITH_PHONE = "Call us at 555-867-5309 any time."
SAMPLE_WITH_SSN = "His SSN is 123-45-6789."
SAMPLE_WITH_CREDIT_CARD = "Visa: 4111111111111111"
SAMPLE_WITH_IP = "Server IP is 192.168.1.100."
SAMPLE_WITH_API_KEY = "Use key " + "sk-" + ("x" * 36) + " for auth."
SAMPLE_MIXED = (
    "Alice (alice@example.com) called from 555-123-4567. "
    "Her SSN is 234-56-7890 and card 4111111111111111."
)
SAMPLE_NO_PII = "The quick brown fox jumps over the lazy dog."
