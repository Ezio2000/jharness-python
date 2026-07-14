# jharness-kernel

**English** | [简体中文](#简体中文)

`jharness-kernel` is the dependency-free, model-neutral execution core for
JHarness. It provides immutable run state, explicit lifecycle transitions,
atomic checkpoints, bounded execution, live events, durable wire codecs, and
opt-in trace verification.

The package targets Python 3.11 and newer and is fully typed.

## Install

```bash
uv add jharness-kernel
```

The distribution installs the implicit namespace `jharness` and is imported
through `jharness.kernel`. It has no required third-party runtime dependencies.

## What It Provides

- `Runtime`, an immutable configuration object that creates single-use
  `Invocation` executions;
- flat run states: `Planning`, `ToolsPending`, `Suspended`, `Completed`,
  `Failed`, and `Limited`;
- model-neutral messages, content parts, tool calls, model requests, model
  responses, and streaming deltas;
- atomic `Checkpoint` values containing both the next snapshot and its
  semantic fact;
- bounded concurrency, monotonic deadlines, run limits, approvals, history
  reduction, and repository ports;
- ordered live events separated from durable committed state;
- explicit JSON-compatible codecs under `jharness.kernel.wire`;
- trace construction and verification under `jharness.kernel.diagnostics`.

## Quick Start

Supply an object that implements the async `Model` protocol, create a runtime,
and await the invocation result:

```python
import asyncio

from jharness.kernel import (
    Completed,
    ContentPart,
    DeltaSink,
    Message,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    RunContext,
    Runtime,
)


class HelloModel:
    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def invoke(
        self,
        request: ModelRequest,
        context: RunContext,
        *,
        stream: bool,
        emit_delta: DeltaSink | None,
    ) -> ModelResponse:
        del request, context, stream, emit_delta
        return ModelResponse(
            parts=(ContentPart.text_part("Hello from JHarness."),),
            finish_reason="end_turn",
        )


async def main() -> None:
    invocation = Runtime(model=HelloModel()).start(
        (Message.user("Say hello."),)
    )
    checkpoint = await invocation.result()
    state = checkpoint.snapshot.state
    if not isinstance(state, Completed):
        raise RuntimeError(f"run stopped with {checkpoint.snapshot.status}")
    print("".join(part.text or "" for part in state.parts))


asyncio.run(main())
```

An invocation may also be observed while it runs:

```python
invocation = runtime.start(messages, stream=True)
events = tuple([event async for event in invocation.events()])
checkpoint = await invocation.result()
```

Each invocation is single-use. Create a new invocation with `start`,
`continue_from`, or `resume` for each execution boundary.

## Durable State

Checkpoints are immutable and can be persisted atomically. Encoding is
explicit rather than reflection-driven:

```python
from jharness.kernel.wire import decode_checkpoint, encode_checkpoint

payload = encode_checkpoint(checkpoint)
restored = decode_checkpoint(payload)
```

Suspended work can be resumed with an optional selector and appended external
messages. Terminal checkpoints cannot be continued or resumed.

## Diagnostics

Trace helpers are opt-in and do not add a second execution state machine:

```python
from jharness.kernel.diagnostics import build_trace, verify_trace

trace = build_trace(events, "start")
verification = verify_trace(trace)
print(verification.checkpoint_count)
```

## Public Namespaces

- `jharness.kernel` — runtime, state, messages, model and tool contracts,
  controls, limits, events, checkpoints, and repository ports;
- `jharness.kernel.wire` — explicit portable encoders and decoders;
- `jharness.kernel.diagnostics` — trace construction and verification.

## Design Guarantees

- public values are immutable;
- checkpoint persistence is atomic;
- model-order tool results commit as one batch;
- deadlines and concurrency are bounded;
- live deltas never become durable unless represented in a completed result;
- cancellation settles owned work before escaping;
- no hidden threads are created.

## Documentation

- [Architecture](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/architecture.md)
- [State machine](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/state-machine.md)
- [Model protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/model-protocol.md)
- [Tool protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/tool-protocol.md)
- [Event stream](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/event-stream.md)
- [Wire protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/wire-protocol.md)
- [Diagnostics](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/diagnostics.md)
- [Issue tracker](https://github.com/Ezio2000/jharness-python/issues)

## License

MIT

## 简体中文

[English](#jharness-kernel) | **简体中文**

`jharness-kernel` 是 JHarness 无第三方运行时依赖、模型中立的执行核心。它提供
不可变运行状态、明确的生命周期转换、原子检查点、有界执行、实时事件、持久化
Wire 编解码以及可选的 Trace 验证。

本包支持 Python 3.11 及以上版本，并提供完整类型标注。

### 安装

```bash
uv add jharness-kernel
```

发行包安装隐式命名空间 `jharness`，通过 `jharness.kernel` 导入。它没有必需的
第三方运行时依赖。

### 核心能力

- `Runtime`：不可变配置对象，用于创建单次使用的 `Invocation`；
- 扁平运行状态：`Planning`、`ToolsPending`、`Suspended`、`Completed`、
  `Failed` 和 `Limited`；
- 模型中立的消息、内容、工具调用、模型请求、模型响应和流式增量；
- 原子 `Checkpoint`，同时包含下一状态快照和对应的语义事实；
- 有界并发、单调截止时间、运行限制、审批、历史归约和存储端口；
- 与持久化提交状态分离的有序实时事件；
- `jharness.kernel.wire` 下明确的 JSON 兼容编解码器；
- `jharness.kernel.diagnostics` 下的 Trace 构建和验证。

### 快速开始

提供一个实现异步 `Model` 协议的对象，创建 Runtime，然后等待执行结果：

```python
import asyncio

from jharness.kernel import (
    Completed,
    ContentPart,
    DeltaSink,
    Message,
    ModelCapabilities,
    ModelRequest,
    ModelResponse,
    RunContext,
    Runtime,
)


class HelloModel:
    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities()

    async def invoke(
        self,
        request: ModelRequest,
        context: RunContext,
        *,
        stream: bool,
        emit_delta: DeltaSink | None,
    ) -> ModelResponse:
        del request, context, stream, emit_delta
        return ModelResponse(
            parts=(ContentPart.text_part("Hello from JHarness."),),
            finish_reason="end_turn",
        )


async def main() -> None:
    invocation = Runtime(model=HelloModel()).start(
        (Message.user("Say hello."),)
    )
    checkpoint = await invocation.result()
    state = checkpoint.snapshot.state
    if not isinstance(state, Completed):
        raise RuntimeError(f"run stopped with {checkpoint.snapshot.status}")
    print("".join(part.text or "" for part in state.parts))


asyncio.run(main())
```

也可以在执行期间观察事件：

```python
invocation = runtime.start(messages, stream=True)
events = tuple([event async for event in invocation.events()])
checkpoint = await invocation.result()
```

每个 Invocation 只能使用一次。每个执行边界都应通过 `start`、
`continue_from` 或 `resume` 创建新的 Invocation。

### 持久化状态

Checkpoint 不可变，并且可以原子持久化。编码过程是明确的，不依赖反射：

```python
from jharness.kernel.wire import decode_checkpoint, encode_checkpoint

payload = encode_checkpoint(checkpoint)
restored = decode_checkpoint(payload)
```

挂起的工作可以通过可选选择器和追加的外部消息恢复。终止状态的 Checkpoint
不能继续或恢复。

### 诊断

Trace 辅助功能按需启用，不会引入第二套执行状态机：

```python
from jharness.kernel.diagnostics import build_trace, verify_trace

trace = build_trace(events, "start")
verification = verify_trace(trace)
print(verification.checkpoint_count)
```

### 公共命名空间

- `jharness.kernel`：Runtime、状态、消息、模型和工具契约、控制、限制、事件、
  Checkpoint 和存储端口；
- `jharness.kernel.wire`：明确的可移植编码器和解码器；
- `jharness.kernel.diagnostics`：Trace 构建和验证。

### 设计保证

- 公共值不可变；
- Checkpoint 持久化是原子的；
- 工具结果按模型顺序作为一个批次提交；
- 截止时间和并发都有明确上限；
- 实时增量只有在完整结果中得到表示时才会成为持久化状态；
- 取消向外传播前会先结束自身拥有的工作；
- 不会创建隐藏线程。

### 文档

- [架构](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/architecture.md)
- [状态机](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/state-machine.md)
- [模型协议](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/model-protocol.md)
- [工具协议](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/tool-protocol.md)
- [事件流](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/event-stream.md)
- [Wire 协议](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/wire-protocol.md)
- [诊断](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/diagnostics.md)
- [问题跟踪](https://github.com/Ezio2000/jharness-python/issues)

### 许可证

MIT
