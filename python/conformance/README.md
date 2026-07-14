# conformance Python runner

This development-only uv workspace project implements the Python reference
runner and `conformance` command. It parses portable fixtures, supplies
deterministic doubles, validates generated wire values, and checks exact
behavioral expectations.

It is distinct from the canonical specification repository's
[`conformance/`](https://github.com/Ezio2000/jharness/tree/v0.1.0/conformance)
directory: that directory contains language-neutral fixture data and the
normative runner contract, while this project contains Python implementation
code. This project is never included in product builds.

```bash
uv --project python run conformance \
  .jharness-spec/conformance/cases \
  --spec-dir .jharness-spec/contracts/v0
```

See the
[portable case contract](https://github.com/Ezio2000/jharness/blob/v0.1.0/conformance/README.md)
and [Python package boundaries](../../docs/python-package-boundaries.md).
