# Publishing Bogu

This checklist covers the first GitHub and PyPI release. Complete it from top
to bottom; do not upload production artifacts until the TestPyPI installation
has passed.

## 1. Repository readiness

- [x] Use the GitHub organization and repository `bogudev/bogu`.
- [x] Confirm that `bogu` is currently unregistered on PyPI (checked 2026-09-08).
      Recheck immediately before publishing because distribution names are
      global and availability can change.
- [x] Add the final repository URLs to `pyproject.toml`:

  ```toml
  [project.urls]
  Homepage = "https://github.com/bogudev/bogu"
  Repository = "https://github.com/bogudev/bogu"
  Issues = "https://github.com/bogudev/bogu/issues"
  ```

- [x] Review `README.md`, `LICENSE`, package classifiers, supported Python
      versions, and the security disclaimer.
- [x] Move reference documents and hackathon work under ignored `personal/` so
      they remain available locally but are absent from public distributions.
- [x] Search the complete Git history and working tree for credentials, private
      data, generated reports, local paths, and internal names.
- [x] Add `CONTRIBUTING.md`, `SECURITY.md`, and a code of conduct before inviting
      external contributors.

## 2. Package readiness

- [x] Decide whether `0.1.0` is the intended first public version. PyPI releases
      are immutable; a filename/version cannot be overwritten.
- [x] Keep OpenAI Privacy Filter outside package dependencies until OPF has a
      PyPI release. Public indexes may reject direct URL dependencies.
- [x] Run tests, Ruff, and strict mypy locally:

  ```bash
  python -m pip install --upgrade build twine
  python -m pip install -e '.[dev]'
  pytest -m 'not slow'
  ruff check src tests
  mypy src
  ```

- [x] Build both the wheel and source distribution. `twine check` remains part
      of the clean release-environment rehearsal:

  ```bash
  python -m build
  python -m twine check dist/*
  ```

- [x] Inspect their contents and ensure personal files are absent:

  ```bash
  python -m zipfile -l dist/*.whl
  tar -tzf dist/*.tar.gz
  ```

- [x] Install the wheel into a new environment and run a smoke test:

  ```bash
  python -m venv /tmp/bogu-release-test
  /tmp/bogu-release-test/bin/pip install dist/*.whl
  /tmp/bogu-release-test/bin/python -c \
    "from bogu import Bogu, RegexDetector; print(Bogu(RegexDetector()).protect('a@example.com'))"
  ```

## 3. TestPyPI rehearsal

- [ ] Create separate accounts on TestPyPI and PyPI and enable two-factor
      authentication.
- [ ] Configure a pending TestPyPI Trusted Publisher with these values:

      - Project: `bogu`
      - Owner: `bogudev`
      - Repository: `bogu`
      - Workflow: `test-pypi.yml`
      - Environment: leave blank

- [ ] Run the `Publish to TestPyPI` workflow manually from GitHub Actions. It
      builds, verifies, and uploads the candidate using short-lived OIDC
      credentials instead of an API token.

- [ ] Install from TestPyPI in a clean environment. Use `--no-deps` for the
      dependency-free core, because optional dependencies may not exist there:

  ```bash
  python -m pip install --index-url https://test.pypi.org/simple/ \
    --no-deps bogu==0.1.0
  ```

- [ ] Verify imports, metadata, README rendering, license inclusion, and the
      protect/restore/clear workflow.

## 4. GitHub release automation

- [x] Add a dedicated `.github/workflows/release.yml` that builds artifacts,
      stores them between jobs, and publishes only from a GitHub Release or
      version tag.
- [x] Give only the publish job `id-token: write` permission.
- [ ] Create a protected GitHub environment named `pypi` and require manual
      approval for production publishing.
- [x] Configure a pending or existing PyPI Trusted Publisher with the exact
      GitHub owner, repository, workflow filename (`release.yml`), and `pypi`
      environment.

      Use these values:

      - Owner: `bogudev`
      - Repository: `bogu`
      - Workflow: `release.yml`
      - Environment: `pypi`
- [x] Publish with `pypa/gh-action-pypi-publish@release/v1`; do not store a
      long-lived PyPI token in GitHub secrets.
- [ ] Protect the release workflow with branch protection and mandatory review.

## 5. First production release

- [ ] Merge only a clean, green commit.
- [ ] Create an annotated version tag such as `v0.1.0`.
- [ ] Create a GitHub Release with concise release notes.
- [ ] Approve the protected `pypi` environment deployment.
- [ ] Confirm the project and provenance on PyPI.
- [ ] Install from production PyPI in a completely new environment:

  ```bash
  python -m pip install bogu==0.1.0
  ```

- [ ] Test the README quick start exactly as written.
- [ ] Announce the release only after the production smoke test succeeds.

## 6. Every later release

- [ ] Update the version and changelog.
- [ ] Run the full quality, build, artifact-inspection, and clean-install gates.
- [ ] Tag the exact reviewed commit and publish through Trusted Publishing.
- [ ] Never reuse a PyPI version. Release a new patch version for corrections;
      yank a broken release only when necessary.

Official references:

- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Using a PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
