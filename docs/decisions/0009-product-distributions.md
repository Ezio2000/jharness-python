# ADR 0009: Three JHarness Product Distributions

Status: Accepted
Date: 2026-07-13

## Context

Each distribution adds a manifest, dependency surface, release artifact,
version relationship, import boundary, and public API. A separate artifact is
justified only by runtime dependencies or an independent implementation
boundary.

## Decision

Publish exactly `jharness-kernel`, `jharness-toolkit`, and
`jharness-providers`.

The distributions contribute `jharness.kernel`, `jharness.toolkit`, and
`jharness.providers` respectively to one implicit PEP 420 `jharness`
namespace. No distribution owns `jharness/__init__.py`; this prevents shared
files across wheels. No umbrella distribution or forwarding package is
published.

Message factories and workflow assembly belong in `jharness.kernel` APIs.
Diagnostics is an opt-in `jharness.kernel.diagnostics` namespace. Controlled
doubles remain local to tests and conformance. `conformance` remains a
development workspace project and CLI, excluded from product artifacts.

## Consequences

- `jharness-kernel` remains zero-dependency and `jharness-toolkit` keeps schema
  dependencies optional.
- Provider transport dependencies remain outside the kernel and toolkit
  distributions.
- Runtime capability is available through three coherent public surfaces.
- Product builds verify exactly three sdist/wheel pairs.
- Only the documented `jharness.*` package roots are product interfaces.
