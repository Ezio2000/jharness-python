# Contributing

JHarness Python changes must preserve the architecture and package boundaries in
`AGENTS.md`. Python is managed exclusively with `uv`.

```bash
uv sync --locked
uv run python scripts/sync_spec.py
uv run pytest -c pyproject.toml -q -p no:cacheprovider
uv run ruff check --config pyproject.toml .
uv run ruff format --check --config pyproject.toml .
uv run pyright --project .
uv run conformance \
  .jharness-spec/conformance/cases \
  --spec-dir .jharness-spec/contracts/v0
```

Portable changes must first be accepted and released in
[`Ezio2000/jharness`](https://github.com/Ezio2000/jharness). This repository then
updates `spec.lock` and the implementation in one focused pull request.
