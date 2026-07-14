# jharness-kernel

`jharness-kernel` is the dependency-free, model-neutral runtime distribution. It owns
immutable run state, `Runtime` and `Invocation`, model and tool protocols,
control, events, limits, atomic checkpoints, repository ports, and explicit
wire codecs.

Stable runtime concepts are imported from `jharness.kernel`. Portable codecs and
diagnostics are opt-in namespaces:

```bash
uv add jharness-kernel
```

```python
from jharness.kernel import Message, Runtime
from jharness.kernel.diagnostics import build_trace, verify_trace
from jharness.kernel.wire import decode_checkpoint, encode_checkpoint
```

See the repository
[architecture](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/architecture.md),
[state machine](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/state-machine.md), and
[Python package boundaries](https://github.com/Ezio2000/jharness-python/blob/main/docs/python-package-boundaries.md).
