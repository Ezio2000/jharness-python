# Python Package Boundaries

Python uses a uv workspace rooted at `python/` with standard `src` layouts.
Commands run from the repository root with `uv --project python`.

## Distributions and Workspace Projects

The product has exactly three published distributions:

| Distribution | Public import root | Required workspace dependency |
| --- | --- | --- |
| `jharness-kernel` | `jharness.kernel` | none |
| `jharness-toolkit` | `jharness.toolkit` | `jharness-kernel` |
| `jharness-providers` | `jharness.providers` | `jharness-kernel` |

`conformance` is the fourth uv workspace project. It is development-only, may
depend on `jharness-kernel` and `jharness-toolkit`, and is excluded from product
builds and published artifact verification.

`jharness.kernel.diagnostics` and `jharness.kernel.wire` are subpackages of the
kernel distribution. They are not separate manifests or versioned artifacts.

## Namespace Ownership

`jharness` is an implicit PEP 420 namespace shared by the three distributions.
There is no `jharness/__init__.py`, no root export surface, and no `jharness`
meta distribution. Each distribution exclusively owns one child subtree:

```text
jharness
├── kernel       owned by jharness-kernel
├── toolkit      owned by jharness-toolkit
└── providers    owned by jharness-providers
```

Only the documented `jharness.*` roots are product interfaces. Source
distributions, wheels, examples, tests, and documentation use those roots
directly.

## Dependency Graph

```text
jharness.kernel
├── jharness.toolkit
└── jharness.providers

conformance (development only) -> jharness.kernel, jharness.toolkit
```

The diagram points from a dependency to its dependent. `jharness.kernel`
imports no workspace sibling and has no required third-party runtime
dependency.

`jharness.toolkit` declares every schema library it imports directly.
`jharness.providers` declares every transport library it imports directly. A
transitive package is never treated as an implicit direct dependency.

## Source Layout

```text
python/
  pyproject.toml
  uv.lock
  kernel/
    pyproject.toml
    src/jharness/kernel/
      __init__.py
      py.typed
      runtime.py
      invocation.py
      commands.py
      state.py
      snapshot.py
      checkpoint.py
      events.py
      messages.py
      models.py
      tools.py
      repository.py
      approval.py
      history.py
      limits.py
      context.py
      errors.py
      wire/
        __init__.py
        ... explicit aggregate codecs
      diagnostics/
        __init__.py
        trace.py
        verification.py
      _engine/
        ... planning, tools, reduction, deadlines, control
  toolkit/
    pyproject.toml
    src/jharness/toolkit/
      __init__.py
      py.typed
      registry.py
      tool.py
      decorators.py
  providers/
    pyproject.toml
    src/jharness/providers/
      __init__.py
      py.typed
      _http.py
      openai/
      anthropic/
      deepseek/
  conformance/
    pyproject.toml
    src/conformance/
      ... fixture parser, local doubles, runner, CLI
```

The listing identifies ownership rather than requiring one file per type.
Every workspace project also owns a local `README.md`; published projects use
it as distribution metadata, while the conformance README distinguishes the
Python runner from the repository-level portable fixture directory.

Private modules may be combined when doing so removes a forwarding layer
without mixing invariants. Public modules must not exist solely to re-export an
internal `api.py` facade.

Module size and line count are not package boundaries. Split a module only when
the result gives distinct invariants, dependency directions, or test ownership;
do not create subpackages merely to make files shorter. Conversely, keep
unrelated invariants out of one module even when that module is still small.

## Placement Rules

- Python request, state, checkpoint, event, model, tool, policy, and repository
  values belong in `jharness.kernel`; their portable shapes belong in the pinned
  `Ezio2000/jharness` specification.
- Runtime orchestration and pure reduction belong in private kernel engine
  modules.
- Portable JSON encode/decode belongs in `jharness.kernel.wire`; domain classes
  do not own serialization methods.
- Trace construction and verification belong in
  `jharness.kernel.diagnostics` and use the kernel's pure change verifier.
- Concrete Python tool adaptation, compiled JSON Schema validation, and tool
  execution decorators belong in `jharness.toolkit`.
- Provider HTTP/SSE transport and wire codecs belong in `jharness.providers`.
- Fixture parsing, controlled doubles, behavior execution, and schema inventory
  belong in the development-only `conformance` project.
- General test doubles remain in the owning package's tests.

Message construction convenience belongs on immutable
`jharness.kernel.Message` factories. Workflow assembly uses `Runtime` directly.
Neither concern warrants another distribution.

## Import and Export Rules

Cross-distribution source imports use the public child packages. The documented
deeper public entry points are provider namespaces such as
`jharness.providers.openai` and `jharness.providers.anthropic`; deeper codec and
transport modules are private.

`jharness.kernel` exports stable domain and runtime concepts only.
`jharness.kernel.wire` and `jharness.kernel.diagnostics` are explicit opt-in
namespaces. Private engine classes, codec helpers, provider transport helpers,
and test doubles are never root exports.

The authoritative public surface is each child package's `__all__`. CI derives
and compares an API inventory from source; a hand-maintained duplicate list is
not a normative document.

## Build and Dependency Gates

CI must prove:

- only the three product distributions build sdists and wheels;
- each artifact imports in a fresh uv environment;
- each wheel owns exactly one `jharness` child subtree and no shared namespace
  initializer;
- no artifact contains the development-only project or test doubles;
- workspace imports are a subset of the graph above;
- every declared workspace dependency is actually imported;
- every direct third-party import is explicitly declared;
- `jharness.kernel` can import without optional diagnostics or provider
  dependencies;
- no runtime distribution imports conformance.

All three distributions are versioned and released together because their
portable contracts change atomically.

## Extension Rules

External implementations depend on kernel ports. The kernel never discovers or
imports them dynamically. Extension uses narrow protocols, pure strategies, and
decorators.

General hooks, service locators, plugin registries, execution schedulers,
reflection serializers, and compatibility packages are outside the package
architecture.
