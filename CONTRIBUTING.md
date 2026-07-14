# Contributing

JHarness Python changes must preserve the architecture and package boundaries in
`AGENTS.md`. Python is managed exclusively with `uv`.

```bash
uv --project python sync --locked
uv --project python run python scripts/sync_spec.py
uv --project python run pytest -c python/pyproject.toml -q -p no:cacheprovider
uv --project python run ruff check --config python/pyproject.toml .
uv --project python run ruff format --check --config python/pyproject.toml .
uv --project python run pyright --project python
uv --project python run conformance \
  .jharness-spec/conformance/cases \
  --spec-dir .jharness-spec/contracts/v0
```

Portable changes must first be accepted and released in
[`Ezio2000/jharness`](https://github.com/Ezio2000/jharness). This repository then
updates `spec.lock` and the implementation in one focused pull request.
