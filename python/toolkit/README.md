# jharness-toolkit

`jharness-toolkit` is the concrete Python tool-support distribution for
`jharness.kernel`. It provides an immutable tool registry, JSON Schema
validation, async function adapters, and retry and circuit-breaking decorators.

```bash
uv add jharness-toolkit
```

```python
from jharness.toolkit import ToolRegistry, function_tool
```

Runtime semantics and portable tool values remain in `jharness.kernel`;
`jharness.toolkit` only implements concrete adaptation and execution policies. See the
[tool protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/tool-protocol.md) and
[Python package boundaries](https://github.com/Ezio2000/jharness-python/blob/main/docs/python-package-boundaries.md).
