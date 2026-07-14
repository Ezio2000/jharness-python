# Model Providers

Concrete model providers live outside the `jharness.kernel` package. They
implement the provider-neutral `Model` protocol by translating `ModelRequest`,
`ModelResponse`, and deltas to and from provider wire APIs.

Provider packages must not define runtime semantics. If a provider exposes a
feature that cannot be represented by the current model protocol, the adapter
must either reject that feature or carry provider-local detail in metadata. Add
new canonical schemas only when the portable runtime contract needs new
state, event, message, tool-call, or stream semantics.

## `jharness.providers`

`jharness.providers` owns concrete model provider adapters and provider-specific
request/response codecs. It may depend on `jharness.kernel` and provider transport
libraries. No core runtime or helper package may depend on it.

The distribution is optional. Host applications construct a concrete model
adapter and inject it into `Runtime`.

## HTTP Client Ownership

Provider adapters accept an optional host-owned `httpx.AsyncClient`. When no
client is injected, each request owns a short-lived client. High-throughput
hosts inject one client per compatible event-loop lifecycle to reuse pools and
close it during host shutdown. Runtime never owns that host client.

`jharness.providers._http` shares only genuine transport mechanics: client
ownership, POST/SSE response lifetime, success checks, cancellation cleanup,
transport exception context, and the common nested `error` envelope. Each
provider supplies its URL, headers, error-code priority, request-id locations,
additional retryable statuses, terminal stream rule, and request/response
codecs. Providers compose the shared helper; they do not inherit a behavioral
base class.

Repeated scalar JSON guards are also shared, but each provider injects its own
codec error type. Vendor message blocks and stream state machines remain
provider-owned.

## Model Invocation

Each adapter exposes the single `Model.invoke` operation. For a non-streaming
call it decodes one response into `ModelResponse`. For a streaming call its
provider codec incrementally decodes chunks, awaits the ordered delta sink, and
returns the same complete response type when the provider stream terminates.

The adapter owns the only stream accumulator. It closes response bodies and
settles emitter work before returning, failing, or propagating cancellation.
Started and finished observations are runtime events; provider deltas contain
only incremental content, reasoning, tool-call, or usage data.

## Historical Tool Calls

Portable tool calls contain only id, name, and arguments, matching the common
provider function-call model. Historical calls remain encodable even when a
later invocation opens a catalog that no longer advertises their name. An
adapter must encode durable history without consulting the current catalog.

## OpenAI Chat Completions

The first adapter is the OpenAI Chat Completions wire protocol. It maps
the existing model protocol to `POST /chat/completions` without changing
the [pinned specification](https://github.com/Ezio2000/jharness/tree/v0.1.0/contracts/v0).
The generic `jharness.providers.openai` package does not ship
provider-specific profile factories; hosts express provider differences with an
`OpenAIChatCompletionsProfile` with explicit fields such as reserved-safe
request extension fields and finish-reason mapping.

Initial supported surface:

- text messages;
- image URI or data URL inputs when the selected profile supports vision;
- video URI or data URL inputs when the selected profile supports video;
- file URI or ref inputs when the selected profile supports file input;
- tool specifications and calls using their portable names directly;
- `ToolChoice` values `auto`, `none`, `required`, and a named tool;
- `ResponseFormat(type="json_object")` when the profile supports JSON mode;
- `ResponseFormat(type="json_schema")` when the profile supports JSON schema
  output;
- non-streaming responses;
- streaming text, reasoning, tool-call, and usage deltas;
- provider errors normalized to `ModelError`;
- provider-local request extensions through profile configuration.

`OpenAIChatCompletionsProfile.supports_parallel_tool_calls` means the model may
return more than one tool call in a single response.
`supports_parallel_tool_call_control` is separate and controls whether the
adapter may send the Chat Completions `parallel_tool_calls` request field.
For streamed Chat Completions tool calls, independently chunked ids, names, and
arguments are accumulated into the same portable call index.

Initial non-goals:

- `/v1/responses`;
- the text-completions `/v1/completions` endpoint;
- provider-hosted tools;
- provider-managed conversation state such as response chaining;
- artifact upload or provider file-store upload;
- overriding reserved Chat Completions request fields through generic extras;
- adapter-owned retry loops.

Retries stay host-owned through `Model` decorators.

## Anthropic Messages

The Anthropic adapter maps the model protocol to the Anthropic Messages wire
protocol at `POST /v1/messages`. Its public names are `AnthropicModel`,
`AnthropicCodec`, `AnthropicProfile`, and `AnthropicError`.

`jharness.providers.anthropic` is independent from `jharness.providers.openai`. It
has its own codec, stream decoder, profile, and error type because Anthropic
uses top-level `system`, user/assistant-only message roles, content blocks,
`tool_use`/`tool_result` blocks, `output_config.format`, and named SSE events.

Initial supported surface:

- text messages;
- top-level system prompt conversion from kernel `system` messages;
- mid-conversation system messages when the selected profile explicitly enables
  them;
- image URI, data URL, or file ref inputs when the selected profile supports
  images;
- PDF URL/base64, text/plain data URL, or file ref inputs as Anthropic
  `document` blocks when the selected profile supports files;
- tool specifications and calls using their portable names directly;
- historical assistant tool calls as `tool_use` blocks;
- tool-result messages as user `tool_result` blocks;
- `ToolChoice` values `auto`, `none`, `required`, and a named tool;
- request-level parallel tool-call control through Anthropic
  `disable_parallel_tool_use` when the selected profile supports it;
- `ResponseFormat(type="json_object")` as a generic object JSON output request
  when the selected profile supports JSON mode;
- `ResponseFormat(type="json_schema")` through `output_config.format` when the
  selected profile supports JSON schema output, with `strict=True` translated
  by requiring object schemas to set `additionalProperties: false`;
- non-streaming responses;
- streaming text, reasoning, Anthropic thinking-block, tool-call, and usage
  deltas;
- provider errors normalized to `ModelError`;
- provider-local request extensions and header extensions through profile
  configuration.

Initial non-goals:

- Anthropic Message Batches, Files upload, Token Counting, Agents, Sessions, or
  tool-runner loops;
- provider-hosted tools such as web search and code execution;
- provider-managed conversation state;
- video input for the first-party Anthropic Messages protocol;
- overriding reserved Messages request fields through generic extras;
- adapter-owned retry loops.

The default `AnthropicProfile` targets the first-party Anthropic Messages
protocol. Hosts can adjust profile flags for providers that expose the same
wire shape with a narrower surface. DeepSeek, for example, documents an
Anthropic-format endpoint at `https://api.deepseek.com/anthropic`; it supports
text, tools, streaming, thinking, and `tool_choice`, but currently does not
advertise image or document input on that endpoint.

File refs use Anthropic `source: {"type": "file", "file_id": ...}`. The default
profile automatically adds the first-party Files API beta header when a request
contains that source shape; hosts can override or disable that behavior through
`AnthropicProfile.file_ref_beta_header` and explicit headers. Mid-conversation
system messages are disabled by default because they are model/provider gated;
enable `supports_mid_conversation_system` only for profiles known to support
`role: "system"` inside `messages[]`.

`AnthropicProfile.supports_parallel_tool_calls` means the model may return more
than one tool use in a single response. `supports_parallel_tool_call_control`
is separate and controls whether the adapter may send Anthropic
`disable_parallel_tool_use`.
## DeepSeek Profiles

DeepSeek-specific profile factories live in the `jharness.providers.deepseek`
namespace so the generic protocol packages stay provider-neutral. Protocol is
selected by the factory name; thinking mode and effort are explicit keyword
parameters so the public API does not grow a function for every combination.

```python
from jharness.providers.deepseek import (
    deepseek_anthropic_profile,
    deepseek_openai_chat_profile,
)
from jharness.providers.anthropic import AnthropicModel
from jharness.providers.openai import OpenAIChatCompletionsModel

openai_chat_tool_model = OpenAIChatCompletionsModel(
    base_url="https://api.deepseek.com",
    api_key=api_key,
    model="deepseek-v4-flash",
    profile=deepseek_openai_chat_profile(thinking=False),
)

anthropic_thinking_model = AnthropicModel(
    base_url="https://api.deepseek.com/anthropic",
    api_key=api_key,
    model="deepseek-v4-flash",
    profile=deepseek_anthropic_profile(thinking=True, effort="max"),
)
```

`deepseek_openai_chat_profile(thinking=True)` keeps DeepSeek thinking mode and
can set `reasoning_effort` when `effort` is provided. It does not advertise
tools because DeepSeek thinking-mode tool-call turns require
`reasoning_content` to be passed back in subsequent requests, while the OpenAI
Chat adapter currently treats reasoning deltas as live-only display data rather
than durable assistant history. `thinking=False` sends
`{"thinking": {"type": "disabled"}}` and advertises tools plus explicit
`tool_choice`. DeepSeek OpenAI Chat can return multiple tool calls, but the
profile does not advertise request-level parallel tool-call control because
DeepSeek does not document the Chat Completions `parallel_tool_calls` field for
that endpoint.

`deepseek_anthropic_profile(...)` returns an `AnthropicProfile` for
`https://api.deepseek.com/anthropic`. It supports tools in both thinking and
non-thinking modes because Anthropic thinking blocks are durable content and can
round-trip through the Anthropic adapter. Anthropic effort is expressed through
`output_config.effort`. DeepSeek's Anthropic-format endpoint does not currently
advertise image/document input, JSON object mode, JSON schema output, or
request-level parallel tool-call control. It can still return multiple tool
uses in one response; callers should control runtime execution concurrency with
`RunLimits.max_tool_concurrency`.

## Testing

Provider adapter behavior is tested in the owning package under
`python/providers/tests`.

Default tests use mocked HTTP transports and cover each Chat Completions feature
independently, including message/content encoding, model options, tool choice,
response formats, stream decoding, provider errors, and profile capability
switches. These tests never call a real provider.

The repository does not carry credential-gated live suites. Deployment hosts
own endpoint smoke tests for the exact model, profile, authentication, network,
and account configuration they operate.

## Codec Boundary

Provider adapters should keep wire-format branching in codecs instead of the
runtime-facing client flow:

- message/content conversion belongs in a message codec;
- tool schema and tool-call conversion belongs in a tool codec;
- request and response assembly belongs in a top-level model codec;
- SSE or chunk parsing belongs in a stream codec;
- HTTP and provider error normalization belongs in the shared transport/error
  boundary configured by each client.

This keeps `jharness.kernel` model-neutral and lets provider differences be handled by a
profile object rather than scattered conditionals.
