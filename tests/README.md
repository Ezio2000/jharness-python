# Repository-level tests

This directory contains cross-package repository guards: portable contract
validation, protocol parity, dependency boundaries, public API shape,
documentation links, examples, and repository maintenance tools.

Behavior owned by one Python project stays with that project:

- kernel runtime and wire behavior: [`packages/kernel/tests`](../packages/kernel/tests/);
- concrete tool support: [`packages/toolkit/tests`](../packages/toolkit/tests/);
- provider adapters: [`packages/providers/tests`](../packages/providers/tests/);
- Python fixture-runner behavior: [`packages/conformance/tests`](../packages/conformance/tests/).

Portable runtime behavior belongs in the pinned specification snapshot under
`.jharness-spec/conformance/cases`,
not in Python tests alone. New root tests should enforce a repository-wide
boundary or workflow rather than duplicate an owning package's tests.
