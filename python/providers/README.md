# jharness-providers

**English** | [简体中文](#简体中文)

`jharness-providers` contains concrete async model adapters, profiles,
transports, errors, and wire codecs for JHarness applications.

The package targets Python 3.11 and newer and is fully typed.

## Install

```bash
uv add jharness-providers
```

Public adapters live in provider-specific namespaces. The top-level
`jharness.providers` namespace intentionally has no convenience exports.

## Supported APIs

| Namespace | API surface |
| --- | --- |
| `jharness.providers.openai` | OpenAI-compatible Chat Completions |
| `jharness.providers.anthropic` | Anthropic-compatible Messages |
| `jharness.providers.deepseek` | DeepSeek profiles for both wire formats |

The adapters support non-streaming and streaming responses, text, tool calls,
usage, normalized errors, and profile-gated structured or multimodal features.
Actual capabilities are exposed by each configured model instance.

## OpenAI Chat Completions

```python
import os

from jharness.providers.openai import (
    OpenAIChatCompletionsModel,
    OpenAIChatCompletionsProfile,
)

model = OpenAIChatCompletionsModel(
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.environ["OPENAI_API_KEY"],
    model=os.environ["OPENAI_MODEL"],
    profile=OpenAIChatCompletionsProfile(),
)

print(model.capabilities)
```

The adapter calls `POST /chat/completions`. A profile records endpoint-specific
capabilities such as streaming, tools, parallel tool calls, image input, JSON
mode, JSON Schema output, token field selection, and request extensions.

The Responses API and legacy text-completions API are intentionally outside
this adapter.

## Anthropic Messages

```python
import os

from jharness.providers.anthropic import AnthropicModel, AnthropicProfile

model = AnthropicModel(
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model=os.environ["ANTHROPIC_MODEL"],
    profile=AnthropicProfile(),
)

print(model.capabilities)
```

The adapter calls `POST /v1/messages`. Its profile controls authentication,
API version, streaming, tool choice, image and document input, structured
output, maximum output tokens, beta headers, and endpoint extensions.

Message Batches, file uploads, token counting, hosted tools, and managed
conversation sessions are intentionally outside this adapter.

## DeepSeek Profiles

DeepSeek factories configure one of the concrete wire-format adapters without
adding another client abstraction:

```python
import os

from jharness.providers.anthropic import AnthropicModel
from jharness.providers.deepseek import (
    deepseek_anthropic_profile,
    deepseek_openai_chat_profile,
)
from jharness.providers.openai import OpenAIChatCompletionsModel

api_key = os.environ["DEEPSEEK_API_KEY"]
model_name = os.environ["DEEPSEEK_MODEL"]

chat_model = OpenAIChatCompletionsModel(
    base_url="https://api.deepseek.com",
    api_key=api_key,
    model=model_name,
    profile=deepseek_openai_chat_profile(thinking=False),
)

thinking_model = AnthropicModel(
    base_url="https://api.deepseek.com/anthropic",
    api_key=api_key,
    model=model_name,
    profile=deepseek_anthropic_profile(thinking=True, effort="max"),
)
```

Thinking mode and effort are explicit profile options. Advertised capabilities
follow the selected DeepSeek protocol and mode.

## HTTP Client Ownership

Each model accepts an optional host-owned `httpx.AsyncClient`:

```python
import asyncio

import httpx

from jharness.providers.openai import OpenAIChatCompletionsModel


async def main() -> None:
    async with httpx.AsyncClient() as client:
        model = OpenAIChatCompletionsModel(
            base_url="https://api.example.com/v1",
            api_key="secret",
            model="example-model",
            client=client,
            timeout=30.0,
        )
        print(model.capabilities)


asyncio.run(main())
```

Inject a client to reuse connection pools in high-throughput applications. If
no client is supplied, each request owns a short-lived client. Response bodies
are closed and in-flight stream work is settled before cancellation escapes.

## Errors and Codecs

- `OpenAIChatCompletionsError` and `AnthropicError` describe malformed local
  wire data;
- remote and transport failures are normalized at the model boundary;
- `OpenAIChatCompletionsCodec` and `AnthropicCodec` are public for explicit
  request/response translation;
- provider-local details remain in profiles and metadata rather than changing
  portable execution semantics.

Adapters do not implement retry loops. Retry policy remains owned by the host
application so attempts, budgets, and observability stay explicit.

## Related Links

- [jharness-kernel](https://pypi.org/project/jharness-kernel/)
- [Provider documentation](https://github.com/Ezio2000/jharness-python/blob/main/docs/model-providers.md)
- [Model protocol](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/model-protocol.md)
- [Issue tracker](https://github.com/Ezio2000/jharness-python/issues)

## License

MIT

## 简体中文

[English](#jharness-providers) | **简体中文**

`jharness-providers` 为 JHarness 应用提供具体的异步模型适配器、Profile、
Transport、错误类型和 Wire 编解码器。

本包支持 Python 3.11 及以上版本，并提供完整类型标注。

### 安装

```bash
uv add jharness-providers
```

公共适配器位于各自的专属命名空间。顶层 `jharness.providers` 命名空间有意不提供
便捷导出。

### 支持的 API

| 命名空间 | API 范围 |
| --- | --- |
| `jharness.providers.openai` | OpenAI 兼容的 Chat Completions |
| `jharness.providers.anthropic` | Anthropic 兼容的 Messages |
| `jharness.providers.deepseek` | 两种 Wire 格式的 DeepSeek Profile |

适配器支持非流式和流式响应、文本、工具调用、Usage、统一错误，以及由 Profile
控制的结构化或多模态能力。实际能力由每个完成配置的模型实例公开。

### OpenAI Chat Completions

```python
import os

from jharness.providers.openai import (
    OpenAIChatCompletionsModel,
    OpenAIChatCompletionsProfile,
)

model = OpenAIChatCompletionsModel(
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.environ["OPENAI_API_KEY"],
    model=os.environ["OPENAI_MODEL"],
    profile=OpenAIChatCompletionsProfile(),
)

print(model.capabilities)
```

适配器调用 `POST /chat/completions`。Profile 记录端点的流式输出、工具、并行工具
调用、图像输入、JSON 模式、JSON Schema 输出、Token 字段和请求扩展能力。

Responses API 和旧版文本 Completions API 不属于此适配器范围。

### Anthropic Messages

```python
import os

from jharness.providers.anthropic import AnthropicModel, AnthropicProfile

model = AnthropicModel(
    base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    api_key=os.environ["ANTHROPIC_API_KEY"],
    model=os.environ["ANTHROPIC_MODEL"],
    profile=AnthropicProfile(),
)

print(model.capabilities)
```

适配器调用 `POST /v1/messages`。Profile 控制认证方式、API 版本、流式输出、工具
选择、图像和文档输入、结构化输出、最大输出 Token、Beta Header 和端点扩展。

Message Batches、文件上传、Token Counting、托管工具以及托管对话 Session
不属于此适配器范围。

### DeepSeek Profile

DeepSeek 工厂使用其中一种具体 Wire 格式配置适配器，不会增加另一层 Client 抽象：

```python
import os

from jharness.providers.anthropic import AnthropicModel
from jharness.providers.deepseek import (
    deepseek_anthropic_profile,
    deepseek_openai_chat_profile,
)
from jharness.providers.openai import OpenAIChatCompletionsModel

api_key = os.environ["DEEPSEEK_API_KEY"]
model_name = os.environ["DEEPSEEK_MODEL"]

chat_model = OpenAIChatCompletionsModel(
    base_url="https://api.deepseek.com",
    api_key=api_key,
    model=model_name,
    profile=deepseek_openai_chat_profile(thinking=False),
)

thinking_model = AnthropicModel(
    base_url="https://api.deepseek.com/anthropic",
    api_key=api_key,
    model=model_name,
    profile=deepseek_anthropic_profile(thinking=True, effort="max"),
)
```

Thinking 模式和 Effort 是明确的 Profile 选项。公开能力取决于所选 DeepSeek
协议和模式。

### HTTP Client 所有权

每个模型都可以接收由宿主拥有的 `httpx.AsyncClient`：

```python
import asyncio

import httpx

from jharness.providers.openai import OpenAIChatCompletionsModel


async def main() -> None:
    async with httpx.AsyncClient() as client:
        model = OpenAIChatCompletionsModel(
            base_url="https://api.example.com/v1",
            api_key="secret",
            model="example-model",
            client=client,
            timeout=30.0,
        )
        print(model.capabilities)


asyncio.run(main())
```

高吞吐量应用可以注入 Client 以复用连接池。没有提供 Client 时，每次请求会拥有
一个短生命周期 Client。取消操作向外传播前，Response Body 会被关闭，进行中的
流式工作也会结束。

### 错误与 Codec

- `OpenAIChatCompletionsError` 和 `AnthropicError` 描述本地 Wire 数据错误；
- 远程错误和传输错误会在模型边界统一处理；
- `OpenAIChatCompletionsCodec` 和 `AnthropicCodec` 可用于明确的请求和响应转换；
- 端点特有细节保留在 Profile 和 Metadata 中，不会改变可移植执行语义。

适配器不会实现重试循环。重试策略由宿主应用负责，从而保持尝试次数、预算和
可观测性都是明确的。

### 相关链接

- [jharness-kernel](https://pypi.org/project/jharness-kernel/)
- [适配器文档](https://github.com/Ezio2000/jharness-python/blob/main/docs/model-providers.md)
- [模型协议](https://github.com/Ezio2000/jharness/blob/v0.1.0/docs/model-protocol.md)
- [问题跟踪](https://github.com/Ezio2000/jharness-python/issues)

### 许可证

MIT
