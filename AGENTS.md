# Repository Guidelines

## Scope

This repository is the Python implementation of the language-neutral JHarness
specification at `Ezio2000/jharness`. The implemented specification revision is
fixed in `spec.lock` and synchronized into the ignored `.jharness-spec/` directory.

Published distributions are exactly:

- `jharness-kernel`, imported as `jharness.kernel`;
- `jharness-toolkit`, imported as `jharness.toolkit`;
- `jharness-providers`, imported as `jharness.providers`.

The `conformance` workspace project is development-only. Do not add a meta
distribution, a shared `jharness/__init__.py`, or a top-level `sdks/` tree.

## Specification Ownership

- Never edit `.jharness-spec/` manually or commit it.
- Portable behavior changes begin in `Ezio2000/jharness` and receive a specification
  release before this repository updates `spec.lock`.
- An implementation PR updates its spec pin, code, tests, examples, and documentation
  together and must pass the pinned portable conformance suite.
- Python-specific behavior, packaging, providers, and performance documentation live
  here, not in the specification repository.

## Architecture and Dependencies

The canonical lifecycle and protocols are defined by the pinned specification. The
kernel has no workspace or third-party runtime dependency. Toolkit and providers may
depend on kernel and their declared direct dependencies. No published distribution
may import `conformance`.

Preset implementations are maintained in the independent `Ezio2000/jharness-tools`
repository. That external project may depend on the public kernel and toolkit APIs;
this repository must never depend on or import `jharness.tools`. Kernel remains
sufficient for applications that provide their own implementations through its ports.

Use immutable values, narrow async ports, pure policies, structural sharing, bounded
concurrency, monotonic deadlines, and atomic model-order commits. Do not add runtime
mutation hooks, schedulers, split persistence, reflection serialization, or duplicate
complete/stream protocols.

## Development

Python must be managed with `uv`; never use `pip`.

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
uv run python benchmarks/runtime_smoke.py
```

Do not claim completion until the spec pin, implementation, dependency gates,
examples, tests, formatting, strict types, conformance, package builds, isolated
artifact imports, and benchmark all pass.
