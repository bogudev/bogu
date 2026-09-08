# Contributing to Bogu

Thank you for helping improve Bogu. Privacy and predictable behavior are more
important than convenience in this project.

## Development setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Run the local checks before opening a pull request:

```bash
.venv/bin/pytest -m 'not slow'
.venv/bin/ruff check src tests
.venv/bin/mypy src
```

Tests marked `slow` require optional local models and are not part of the
dependency-free core check.

## Pull requests

- Keep changes focused and add tests for observable behavior.
- Do not include real personal data, credentials, customer data, or private
  model output in code, fixtures, issues, or pull requests.
- Preserve the local-only boundary: preview operations must never transmit data.
- Keep new integrations optional and lazily imported.
- Document compatibility changes and user-visible security tradeoffs.

By contributing, you agree that your contribution is licensed under the MIT
License included in this repository.
