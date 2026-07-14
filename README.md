# JHarness Python

This repository contains the Python SDK implementation of the
[JHarness specification](https://github.com/Ezio2000/jharness). It publishes
exactly three distributions:

| Distribution | Import root | Responsibility |
| --- | --- | --- |
| `jharness-kernel` | `jharness.kernel` | Immutable runtime, ports, checkpoints, wire codecs, and diagnostics. |
| `jharness-toolkit` | `jharness.toolkit` | Tool registry, schema validation, adapters, retries, and circuit breaking. |
| `jharness-providers` | `jharness.providers` | OpenAI, Anthropic, and DeepSeek provider adapters and profiles. |

`conformance` is a development-only workspace project and is not published.

## Install

```bash
uv add jharness-kernel jharness-toolkit jharness-providers
```

```python
from jharness.kernel import Message, Runtime
from jharness.providers.openai import OpenAIChatCompletionsModel
from jharness.toolkit import ToolRegistry
```

There is no `jharness-python` meta distribution and no `jharness_python` import.
The repository name is only the source-management boundary.

## Implemented Specification

The exact specification tag, commit, and archive digest are recorded in
[`spec.lock`](spec.lock). The generated `.jharness-spec/` directory is not edited
or committed. CI reconstructs it from the immutable specification commit and
verifies its digest before running conformance.

## Development

Python is managed exclusively with `uv`; do not use `pip`.

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
uv --project python run python benchmarks/runtime_smoke.py
```

## Documentation

- [Canonical architecture](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/architecture.md)
- [Portable contracts](https://github.com/Ezio2000/jharness/tree/v0.1.0/contracts/v0)
- [Python package boundaries](docs/python-package-boundaries.md)
- [Provider adapters](docs/model-providers.md)
- [Performance](docs/performance.md)
- [Release process](docs/releasing.md)
