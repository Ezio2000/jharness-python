# ADR 0010: Independent Preset Tools Project

Status: Accepted
Date: 2026-07-16

## Context

JHarness needs curated tool implementations that applications may install instead of
implementing every capability themselves. Presets have a different change rate,
dependency surface, and release lifecycle from the stable runtime contracts. Adding
them to this repository would also turn a growing capability catalogue into a fourth
coordinated product distribution.

The kernel must remain independently sufficient. Applications can implement every
kernel port themselves and must not need preset tools merely to construct or run an
agent.

## Decision

Maintain presets in the independent
[`Ezio2000/jharness-tools`](https://github.com/Ezio2000/jharness-tools) repository.
That repository owns the separately versioned `jharness-tools` distribution and the
`jharness.tools` child of the implicit PEP 420 namespace.

`jharness-tools` is not a uv workspace member, product artifact, coordinated release,
or dependency of this repository. Its permitted dependency direction is:

```text
jharness-tools -> jharness-toolkit -> jharness-kernel
jharness-tools --------------------> jharness-kernel
```

Kernel, toolkit, and providers never import or depend on `jharness.tools`. Installing
the external distribution does not automatically discover, register, or activate any
tool; applications explicitly construct the presets they choose and supply them
through kernel contracts.

## Consequences

- This repository continues to publish exactly the three distributions accepted by
  ADR 0009.
- Presets can evolve and release without changing the coordinated Python SDK version.
- Preset-specific dependencies and security policies remain outside the kernel.
- Kernel retains stable extension ports and remains sufficient without auxiliary
  packages.
- The installed `jharness` namespace may contain `jharness.tools`, but no wheel from
  this repository owns that subtree.
