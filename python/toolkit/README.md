# jharness-toolkit

**English** | [简体中文](#简体中文)

`jharness-toolkit` provides concrete Python tool registration, JSON Schema
validation, async function adaptation, retries, and circuit breaking for
JHarness applications.

The package targets Python 3.11 and newer and is fully typed.

## Install

```bash
uv add jharness-toolkit
```

Import its public API from `jharness.toolkit`.

## What It Provides

- `ToolRegistry` for thread-safe registration and immutable invocation-local
  catalogs;
- `function_tool` and `FunctionTool` for adapting async Python functions;
- JSON Schema Draft 2020-12 validation for tool inputs and structured outputs;
- eager schema compilation and rejection of unresolved references;
- duplicate-name and unknown-tool protection;
- `RetryingTool` for explicitly idempotent operations;
- `CircuitBreakingTool` for consecutive implementation failures.

## Quick Start

Define an async function with explicit schemas, then register it:

```python
import asyncio

from jharness.kernel import (
    ContentPart,
    SettledResult,
    ToolCall,
    ToolContext,
    ToolExecution,
    ToolResult,
    ToolSuccess,
)
from jharness.toolkit import ToolRegistry, function_tool


@function_tool(
    name="uppercase",
    description="Convert text to uppercase.",
    input_schema={
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}},
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}},
        "additionalProperties": False,
    },
    execution=ToolExecution(idempotent=True),
)
async def uppercase(call: ToolCall, context: ToolContext) -> ToolResult:
    del context
    text = str(call.arguments["text"]).upper()
    return SettledResult(
        ToolSuccess(
            (ContentPart.text_part(text),),
            structured_content={"text": text},
        )
    )


async def main() -> None:
    catalog = await ToolRegistry((uppercase,)).open_catalog()
    binding = catalog.bind(
        ToolCall("call-1", "uppercase", {"text": "hello"})
    )
    print(binding.spec.name)


asyncio.run(main())
```

`open_catalog()` returns an immutable snapshot. Later registry changes do not
alter catalogs already opened by active invocations.

## Validation

Schemas are checked when a tool is registered. Inputs are validated when a
call is bound, before implementation code runs. If an output schema is
declared, `structured_content` is validated after invocation.

Invalid schemas raise `ValueError`; invalid calls and outputs raise
`ToolError`. Schemas remain explicit—function signatures are not inspected to
invent a schema.

## Retry and Circuit Breaking

Decorators compose around any object implementing the `Tool` protocol:

```python
from jharness.toolkit import CircuitBreakingTool, RetryingTool

resilient_tool = CircuitBreakingTool(
    RetryingTool(
        uppercase,
        max_attempts=3,
        attempt_timeout_seconds=2.0,
    ),
    failure_threshold=3,
)
```

Retries require `spec.execution.idempotent=True`. They retry implementation
exceptions, while model-visible failure results remain normal results. Circuit
state is owned by the decorator and is not persisted as execution state.

## Public API

| Name | Purpose |
| --- | --- |
| `ToolRegistry` | Register tools and open immutable catalogs. |
| `Tool` | Runtime-checkable async tool protocol. |
| `function_tool` | Build a `FunctionTool` with explicit schemas and policy. |
| `FunctionTool` | Immutable async-function adapter. |
| `RetryingTool` | Retry idempotent implementation failures. |
| `CircuitBreakingTool` | Open a circuit after consecutive exceptions. |

## Related Links

- [jharness-kernel](https://pypi.org/project/jharness-kernel/)
- [Tool protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/tool-protocol.md)
- [Python package boundaries](https://github.com/Ezio2000/jharness-python/blob/main/docs/python-package-boundaries.md)
- [Issue tracker](https://github.com/Ezio2000/jharness-python/issues)

## License

MIT

## 简体中文

[English](#jharness-toolkit) | **简体中文**

`jharness-toolkit` 为 JHarness 应用提供具体的 Python 工具注册、JSON Schema
验证、异步函数适配、重试和熔断能力。

本包支持 Python 3.11 及以上版本，并提供完整类型标注。

### 安装

```bash
uv add jharness-toolkit
```

公共 API 从 `jharness.toolkit` 导入。

### 核心能力

- `ToolRegistry`：线程安全注册，并为每次调用创建不可变工具目录；
- `function_tool` 和 `FunctionTool`：适配异步 Python 函数；
- 使用 JSON Schema Draft 2020-12 验证工具输入和结构化输出；
- 提前编译 Schema，并拒绝无法解析的引用；
- 防止重复工具名和未知工具调用；
- `RetryingTool`：用于明确声明为幂等的操作；
- `CircuitBreakingTool`：针对连续实现异常进行熔断。

### 快速开始

使用明确的 Schema 定义异步函数，然后注册工具：

```python
import asyncio

from jharness.kernel import (
    ContentPart,
    SettledResult,
    ToolCall,
    ToolContext,
    ToolExecution,
    ToolResult,
    ToolSuccess,
)
from jharness.toolkit import ToolRegistry, function_tool


@function_tool(
    name="uppercase",
    description="Convert text to uppercase.",
    input_schema={
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}},
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "required": ["text"],
        "properties": {"text": {"type": "string"}},
        "additionalProperties": False,
    },
    execution=ToolExecution(idempotent=True),
)
async def uppercase(call: ToolCall, context: ToolContext) -> ToolResult:
    del context
    text = str(call.arguments["text"]).upper()
    return SettledResult(
        ToolSuccess(
            (ContentPart.text_part(text),),
            structured_content={"text": text},
        )
    )


async def main() -> None:
    catalog = await ToolRegistry((uppercase,)).open_catalog()
    binding = catalog.bind(
        ToolCall("call-1", "uppercase", {"text": "hello"})
    )
    print(binding.spec.name)


asyncio.run(main())
```

`open_catalog()` 返回不可变快照。之后对 Registry 的修改不会影响已经为活动调用
打开的目录。

### 验证

工具注册时会检查 Schema。调用绑定时会验证输入，验证发生在实现代码运行之前。
如果声明了输出 Schema，则会在调用结束后验证 `structured_content`。

无效 Schema 会引发 `ValueError`；无效调用和输出会引发 `ToolError`。Schema
始终需要明确声明，不会通过检查函数签名自动生成。

### 重试与熔断

装饰器可以组合到任何实现 `Tool` 协议的对象上：

```python
from jharness.toolkit import CircuitBreakingTool, RetryingTool

resilient_tool = CircuitBreakingTool(
    RetryingTool(
        uppercase,
        max_attempts=3,
        attempt_timeout_seconds=2.0,
    ),
    failure_threshold=3,
)
```

重试要求 `spec.execution.idempotent=True`。它只重试实现异常；模型可见的失败结果
仍然属于正常结果。熔断状态由装饰器持有，不会被保存为执行状态。

### 公共 API

| 名称 | 用途 |
| --- | --- |
| `ToolRegistry` | 注册工具并打开不可变目录。 |
| `Tool` | 可在运行时检查的异步工具协议。 |
| `function_tool` | 使用明确的 Schema 和策略构建 `FunctionTool`。 |
| `FunctionTool` | 不可变异步函数适配器。 |
| `RetryingTool` | 重试幂等操作的实现异常。 |
| `CircuitBreakingTool` | 连续异常达到阈值后打开熔断器。 |

### 相关链接

- [jharness-kernel](https://pypi.org/project/jharness-kernel/)
- [工具协议](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/tool-protocol.md)
- [Python 包边界](https://github.com/Ezio2000/jharness-python/blob/main/docs/python-package-boundaries.md)
- [问题跟踪](https://github.com/Ezio2000/jharness-python/issues)

### 许可证

MIT
