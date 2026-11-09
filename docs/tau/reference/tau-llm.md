---
title: "tau_llm"
category: "reference"
status: "draft"
---

# `tau_llm` — the wire layer

<p class="axis">Cognition × Application</p>

Wire protocols, the message and tool types they carry, and the streaming
events they produce. Nothing in this package knows what an agent is.

Distribution `ffwf-tau-llm`, Python 3.12 or later. Depends on `pydantic` and
`httpx`, and nothing else — the two vendor SDKs are extras, imported on first
request. A third extra, `ffwf-tau-llm[tokenizers]`, adds exact token counting.

## Three wire protocols

A `Model` names the protocol it wants in `api` and the vendor it belongs to
in `provider`.

| `api` | Client | Vendor τ registers | Extra |
|---|---|---|---|
| `openai-completions` | `httpx` against the chat-completions wire | `openai` | — |
| `anthropic-messages` | the official `anthropic` SDK | `anthropic` | `ffwf-tau-llm[anthropic]` |
| `google-generative-ai` | the official `google-genai` SDK | `gemini` | `ffwf-tau-llm[google]` |

An `api` τ does not implement **raises**, naming what was asked for and what
is registered. It does not fall back to the OpenAI client — that fallback was
a real defect, and it is what got `openai-responses` unregistered rather than
quietly mis-served.

The Google vendor is registered as **`gemini`**, not `google`, because that is
the `backend` value existing config entries carry, including the one in the
shipped template.

## Two registries and a pool

Three separate questions. Confusing them is the usual way a request goes
somewhere it was not meant to.

<figure class="dia"><svg viewBox="0 0 680 300" role="img" aria-labelledby="dia-resolve-t dia-resolve-d"><title id="dia-resolve-t">How one request resolves a provider</title><desc id="dia-resolve-d">On the left, a Model box lists two of its fields: api, holding google-generative-ai, and provider, holding gemini. Two arrows leave the box's right edge. The upper one, carrying api, enters a box named the api registry, glossed as answering which client class and noted beside it that an unknown api raises and never falls back. The lower one, carrying provider, enters a box named the vendor registry, glossed as holding the base URL and key environment variables, noted beside it as one vendor per protocol and that registering your own is six lines. Below both, a row of four small labels reads provider, api, base_url and sha256 of the api key. A red rule runs under that row, ends in a small red square, and turns down into a box named the provider pool, glossed as one client per destination per event loop. The red mark is annotated the pool key, with the gloss that two destinations never share a client.</desc><rect x="0" y="40" width="250" height="96" class="fill-ground stroke"/><text x="14" y="62" class="label">Model</text><line x1="0" y1="72" x2="250" y2="72" class="stroke-soft"/><text x="14" y="92" class="label-soft">api</text><text x="62" y="92" class="label">google-generative-ai</text><text x="14" y="116" class="label-soft">provider</text><text x="80" y="116" class="label">gemini</text><path d="M250 92 H276 V84 H296" class="stroke-hair fill-none"/><path d="M304 84 L295 80 L295 88 Z" class="fill-ink"/><path d="M250 116 H276 V148 H296" class="stroke-hair fill-none"/><path d="M304 148 L295 144 L295 152 Z" class="fill-ink"/><rect x="304" y="62" width="232" height="44" class="fill-ground stroke"/><text x="420" y="82" text-anchor="middle" class="label">api registry</text><text x="420" y="98" text-anchor="middle" class="label-soft">which client class</text><text x="546" y="84" class="label-soft">unknown api raises</text><text x="546" y="98" class="label-soft">never falls back</text><rect x="304" y="126" width="232" height="44" class="fill-ground stroke"/><text x="420" y="146" text-anchor="middle" class="label">vendor registry</text><text x="420" y="162" text-anchor="middle" class="label-soft">base URL and key env vars</text><text x="546" y="148" class="label-soft">one per protocol</text><text x="546" y="162" class="label-soft">yours: six lines</text><text x="0" y="200" class="label-soft">provider</text><text x="70" y="200" class="label-soft">api</text><text x="110" y="200" class="label-soft">base_url</text><text x="180" y="200" class="label-soft">sha256(api_key)</text><line x1="0" y1="210" x2="290" y2="210" class="stroke-red"/><rect x="285" y="205" width="10" height="10" class="fill-red"/><line x1="290" y1="215" x2="290" y2="232" class="stroke-red"/><path d="M290 240 L286 231 L294 231 Z" class="fill-red"/><rect x="180" y="240" width="280" height="46" class="fill-ground stroke"/><text x="320" y="262" text-anchor="middle" class="label">the provider pool</text><text x="320" y="278" text-anchor="middle" class="label-soft">one client per destination, per event loop</text><text x="474" y="258" class="label-mark">the pool key</text><text x="474" y="274" class="label-soft">two destinations never share</text></svg><figcaption>The registries answer <em>what to build</em>; the pool answers <em>which instance</em>. Red marks the key because it is the part that has already gone wrong once: every input that varies what gets constructed has to be in it, or two models pointing at different servers quietly share one client. <code>api</code> joined the key when it started selecting the client class, since two protocols are two classes. The credential is hashed and never held raw — including the absent case, which hashes to a fixed digest distinct from any real key's.</figcaption></figure>

| Question | Answered by |
|---|---|
| Which client class serves this `Model.api`? | the **api registry** — `register_api(api, factory, sends_without_key=...)` |
| Where does this `Model.provider` point, and which environment variables hold its key? | the **vendor registry** — `register_provider(ProviderSpec(...))` |
| Which client *instance* serves this call? | the pool in `tau_llm.client`, keyed as drawn above |

τ ships one vendor per protocol it implements and **no model catalogs**. Every
URL and environment-variable name in a vendor list is a claim τ would have to
keep true as vendors move them. Adding your own is six lines at import time:

```python
from tau_llm.providers import ProviderSpec, register_provider

register_provider(ProviderSpec(
    id="groq",
    name="Groq",
    api="openai-completions",
    base_url="https://api.groq.com/openai/v1",
    api_key_env=("GROQ_API_KEY",),
))
```

Then point a model at it with `provider="groq"`.

A vendor's key environment variables reach **only that vendor's own endpoint**
(`ProviderSpec.reads_env_for`). A model that carries its own `base_url`, such as
a proxy in front of `anthropic`, never receives `ANTHROPIC_API_KEY`; it needs
its own `api_key` in config. τ never substitutes a placeholder key.

What happens with no key depends on the wire. `openai-completions` and
`anthropic-messages` are registered `sends_without_key=True`: the request goes
out and the endpoint's 401 is the error, because τ cannot know that an
endpoint needs a key. A `ProviderHttpError` 401 then carries a `hint` saying
what to set. `google-generative-ai` cannot build a keyless client, so it
**raises** before sending (`No API key for provider …`).

`aclose_providers()` tears the pool down; the TUI, headless and RPC entry
points all call it on shutdown.

## The `Provider` interface

```python
class Provider(ABC):
    @abstractmethod
    async def stream_chat(
        self, model: Model, messages: list[Any],
        tools: list[ToolDefinition] | None = None,
        options: dict[str, Any] | None = None,
    ) -> StreamEventStream: ...

    async def aclose(self) -> None: ...
```

One abstract method. There is **no non-streaming entry point** — a caller that
does not want deltas ignores them and reads `DoneEvent.final`. `Model.stream =
False` changes how τ talks to the server, not what the caller sees: the
buffered path fills the same accumulator and yields the same event sequence.

`client.stream_simple()` is the thin wrapper everything above calls. It
resolves a provider, calls `stream_chat`, and wraps the result once in
`AssistantMessageEventStream`, which adds queue buffering and a terminal
`async def result() -> AssistantMessage`.

## `Model`

Beyond `id`, `name`, `api`, `provider`, `base_url`, `context_window` and
`max_tokens`:

| Field | Meaning |
|---|---|
| `stream` | `True` by default. Set false for an OpenAI-shaped gateway with no SSE. Both paths share one final-message builder, so the buffered one inherits the same guards. What it cannot reproduce is granularity, and a request in flight cannot be interrupted. |
| `request_timeout` | Seconds, overriding the 300s default of the OpenAI wire. Also settable per call. An unusable value raises rather than reverting — a silently ignored timeout is the failure the knob exists to fix. |
| `reasoning` | Whether this model reasons. Declared per model, because one endpoint serves both kinds. Any level but `"off"` is not sent when this is false. |
| `thinking_level_map` | How this server spells a thinking level — a wire level name, a request fragment that names the field *and* its value, or `null` for "unsupported". See below. |
| `reasoning_replay` | `"turn"`, `"all"`, `"off"` or unset. Whether a prior turn's chain-of-thought is resent. Unset means the provider's default: `"turn"` on the OpenAI wire, `"all"` on Anthropic and Google. τ's OpenAI default departs from pi's always-resend: measured 72%→28% of payload on a real transcript. |
| `strict_reasoning_formats` | Turns a provider quirk τ is willing to work around into an error. Chiefly a signature minted by another vendor. |
| `requires_tool_call_id` | `True` by default, and measured rather than assumed. See below. |
| `supports_multimodal_function_response` | `False` by default — an image goes in its own turn rather than nested in a tool result. |
| `grammar_dialect` | `"llguidance"` or `"gbnf"`. Which constrained-decoding grammar the target server speaks. |
| `prompt_cache` | `True` by default, on every wire. Whether to ask the server to cache the prompt prefix. |
| `tokenizer` | A `tokenizer.json` path or HuggingFace repo id, for exact token counts (needs the `tokenizers` extra). Unset means counts are estimated from character composition and labelled as estimates. |
| `temperature` | 0.0–2.0; unset sends none. |
| `prompt_cache_dialect` | `"anthropic"` or unset. *How* an OpenAI-compatible endpoint must be asked — declared, never guessed from the model id. Two keys rather than one because they are two questions, and a single key made `null` mean "on" on one wire and "off" on the other. |
| `extra_body` | Per-model JSON merged into every request body. The escape hatch for a server-specific field with no first-class knob. |
| `server_features` | Advisory tags from config. Nothing in `tau_llm` reads them; they never gate behaviour. |
| `compat` | Three wire quirks, two of them auto-detected from the base URL. See below. |

### Thinking levels

The vocabulary is common to every wire: `off`, `minimal`, `low`, `medium`,
`high`, `xhigh` (`EXTENDED_THINKING_LEVELS`; `DEFAULT_THINKING_LEVEL` is
`medium`). Each provider translates it. Without a map entry a wire has native
names for only some levels: Anthropic has no `minimal`, Google has no `xhigh`,
and `xhigh` exists on the OpenAI wire only when `thinking_level_map` names it —
all measured as 400s. `get_supported_thinking_levels(model)` lists what a model
accepts, and `clamp_thinking_level` moves a request to the nearest supported
level, upward first. A non-reasoning model supports only `off`.

`check_thinking_request` is the pure check a head runs before sending, and it
raises `ThinkingRefused` for a level the wire cannot honour. One case matters:
`off` on an `openai-completions` model that neither declares `reasoning` nor
maps `off` is refused, because τ cannot know what turns reasoning off on that
endpoint and sending nothing would leave the default on. The refusal names the
config key to set. `AssistantMessage.reasoning_level` records the level that
was actually sent.

### Where the numbers come from

`python -m tau_llm.catalog` reads [models.dev](https://models.dev). Its
subcommands are `providers`, `search PATTERN`, `show PROVIDER/MODEL` and
`config PROVIDER/MODEL --base-url URL`; the last fills `context_window`,
`max_tokens`, `reasoning` and `thinking_level_map` and prints a config entry
to stdout for you to inspect. Nothing is vendored or written, and `--base-url`
is required rather than guessed — models.dev carries no base URL.

`tau_llm.compat` auto-detects the two keys `extra_body` cannot reach, one
because it is reserved and one because it is written after the spreads. A
third field, `tool_call_schema`, is never detected:

| Field | Detected from |
|---|---|
| `max_tokens_field` | `api.openai.com` and `openai.azure.com` want `max_completion_tokens`; everyone else keeps `max_tokens`. |
| `supports_usage_in_streaming` | whether to send `stream_options.include_usage`; detected as true everywhere. |
| `tool_call_schema` | `"openai"` unless an operator states `"anthropic"`, which translates tool calls a gateway returns in the Anthropic shape. It rewrites a response, so it can hide a fault and is never inferred. |

Detection is deliberately **inverted from pi's**. pi names the servers wanting
`max_tokens` and gives everyone else the newer spelling, so an unrecognised
endpoint — for τ, usually a local llama.cpp — gets a spelling it rejects. τ
names only the two that want the new one. τ also ignores the provider *name*
pi matches on, because an entry with no `backend` key defaults to
`provider="openai"`, so in τ that string usually means "unstated".

A stated value always wins over detection, field by field: stating one quirk
does not reset another.

### Two capabilities that were measured, not assumed

`requires_tool_call_id` defaults **true**. The question was whether sending a
tool-call id to a model that does not expect one is itself rejected. It is
not: every Google model tested accepted one on a tool result, including
`gemma-4-26b-a4b-it`, which pi classifies as id-less. So the permissive branch
is the safe one, and τ ships **no per-model table** — a table that can only
ever be wrong is worse than no table.

`supports_multimodal_function_response` defaults **false**. Only one model was
measured accepting a nested image, and one permissive data point does not earn
a permissive default when the conservative branch always works.

## Cancellation and token counts

`AbortSignal` is a thread-safe flag with a `reason`, `"user"` or
`"extension"` (`abort(reason="user")`; a user abort overrides an earlier
extension one, not the reverse). Blocking reads go through it, so an abort does
not wait for the next chunk.

`tau_llm.tokens` counts tokens by the best route available and says which it
used: `TokenCount.source` is `usage`, `tokenizer`, `classes`, `calibrated` or
`none`. `TokenizerCounter` is exact (needs the `tokenizers` extra and
`Model.tokenizer`); `CharClassCounter` estimates from character classes; and
`ContextCalibrator` learns the gap between an estimate and the server's reported
usage.

## Messages and content

All pydantic models.

```
Message  = UserMessage | AssistantMessage | ToolResultMessage

AssistantMessage.content   list[ TextContent | ThinkingContent | ToolCall ]
ToolResultMessage.content  list[ TextContent | ImageContent ]
```

`Usage` carries `input_tokens`, `output_tokens`, `cache_read_tokens`,
`cache_write_tokens`, `total_tokens`, a `reasoning_tokens` count (`None` when
the server does not report one), a `cost` dict, and an `extra: dict[str, Any]`
for server-reported telemetry that is not portable — llama.cpp's `timings`
block, τ's own tool-argument repair count. On the Google path `thoughts_token_count` is added
to output tokens, because Google reports `candidates_token_count` without it
and a reasoning turn would otherwise under-report its cost.

### Reasoning signatures

Anthropic's thinking blocks and Gemini 3's function calls both carry a
signature the vendor **validates** on replay. Sending one vendor's token to
another is a request that fails, so both are namespaced by vendor:

```python
ThinkingContent.provider_signature   # {"anthropic": {...}}
ToolCall.provider_signature          # {"google": {"thought_signature": "..."}}
```

The OpenAI writer **refuses** a foreign signature rather than forwarding it: it
raises under `strict_reasoning_formats`, and otherwise warns once per payload
shape and drops the token. The tool call still replays with its id, name and
arguments intact — the transcript is not broken to avoid leaking a field.

One rule is easy to get backwards:

| Signature on | Replayed |
|---|---|
| a **function call** | always, on every `reasoning_replay` setting including `"off"` |
| **text or thinking** parts | only as `reasoning_replay` allows |

A function-call signature is reasoning-*derived*, which is what makes it look
like the knob's business. It is not chain-of-thought the model reads back — it
is a token the API validates, and omitting it fails the request with a 400
naming the offending call. Signatures persist to session storage as base64
text, because a resumed session that lost one fails on its next turn.

## Streaming events

`stream_chat` yields these. They are `tau_llm`'s vocabulary, not the agent
loop's — see [`tau_agent_core`](tau-agent-core.md#two-event-vocabularies) for
the other one.

| Event | Carries |
|---|---|
| `TextDeltaEvent` | one fragment of assistant text |
| `ThinkingDeltaEvent` | one fragment of reasoning |
| `ToolCallDeltaEvent` | one fragment of a tool call |
| `DoneEvent` | `final`, the authoritative `AssistantMessage` |
| `RetryEvent` | a request failed before producing anything and is about to be re-sent: `attempt`, `max_retries`, `delay_seconds`, `error` |
| `ErrorEvent` | a failure, named; `exception` holds the typed error when the provider gave one |

**`DoneEvent.final` is the authority, not the accumulated deltas.** Its
`ToolCall` blocks carry the parsed `arguments` that actually get executed.
`DoneEvent.response_headers` carries the HTTP response headers, names
lowercased (a vendor's rate-limit counters, say), or `None` when the provider
did not capture them; they are not persisted on `final`.

### Typed failures and retry

Providers raise typed errors rather than strings, and
`AssistantMessageEventStream.result()` re-raises them with the type intact:

| Error | Meaning |
|---|---|
| `ProviderHttpError` | a non-2xx answer: `status_code`, `message`, `body` (bounded), `model_id`, `base_url`, `retry_after`, `headers`, `hint` |
| `ProviderConnectionError` | refused, reset or closed before any response. A timeout waiting for the response is not one of these, because the server may still be working |
| `ProviderStreamError` | the request was accepted, then an SSE `error` frame arrived |

`stream_simple` wraps every provider stream in a retry. The default
`DEFAULT_RETRY_POLICY` makes three re-sends at about 1s, 2s and 4s (doubling,
capped at 30s, up to 20% jitter), for a `ProviderHttpError` with status 408,
429, 502, 503, 504 or 529 and for any `ProviderConnectionError`. A
`Retry-After` replaces the backoff, and one longer than 60s is not waited out.
Retry happens only before the first event, so nothing from a failed attempt
needs discarding. 500 and 524 are not retried. Pass
`options["retry"]=RetryPolicy(...)` to change it, or `False` (`NO_RETRY`) to
send once. A `RetryEvent` is emitted before each wait so a head can show it.

The single most common way to get this wrong: **OpenAI streams tool-call
arguments as incremental fragments**, one piece per chunk, which must be
concatenated. Logic that treats a chunk's `arguments` as the complete
cumulative string corrupts the JSON. Local servers fragment aggressively, so
they exercise the path that single-chunk cloud responses can mask.

An argument buffer that does not decode to a dict **raises** rather than
becoming `{"raw": "..."}`. So does a tool call that arrives with no `name` —
a real defect on at least one hosted gateway. The raise names the call id, the
model and the base URL, because the fault is the gateway's and an operator
needs to know which deployment behind a shared endpoint is at fault.

A keepalive frame that is valid JSON but not an object (`data: []`) is skipped
rather than crashing the turn, and the skip logs at debug level. Skipping is
not swallowing: that path also catches genuinely malformed gateway output.

Errors always lead with the exception type and append HTTP status and body
when present. `httpx.ReadTimeout`, `ConnectError` and `RemoteProtocolError`
all stringify to the empty string, so a dropped connection used to surface as
`Streaming error: ` with nothing after the colon.

## Tools

`define_tool(**fields)` constructs a `ToolDefinition`. It takes the model
fields as keywords, or a single mapping positionally; both forms at once, or
neither, is a `TypeError`.

```python
from tau_llm import define_tool

word_count = define_tool(
    name="word_count",
    label="Word count",
    description="Count the words in a string.",
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
    execute=lambda text: {"words": len(text.split())},
)
```

It **validates rather than normalises** — nothing malformed is patched into
something that works:

| Rule | What it prevents |
|---|---|
| the five required fields (`name`, `label`, `description`, `parameters`, `execute`) are present | a pydantic error from a call site that reads fine |
| unknown field names are rejected | `ToolDefinition` is `extra="ignore"`, so a typo'd `prompt_snipet` would be dropped in silence |
| `execute` is callable | a failure the first time the *model* calls the tool, many turns after the mistake |
| `name` matches `[A-Za-z0-9_-]{1,64}` | OpenAI rejects the whole request for one bad tool name, with a 400 that does not say which tool |
| `parameters` is an object schema with `properties` | a non-object schema validates every call vacuously |
| every `required` name appears in `properties` | the model is never told about the field, so every call fails forever |
| `label` and `description` are non-empty | a blank chip in the TUI, and a tool the model is given no reason to call |

`label` is **required and never derived from `name`**. Inventing it would be a
fabricated default, and the failure mode is invisible — the TUI would show a
developer identifier as a human label and everything would appear to work.
(`ExtensionAPI.register_tool()` *does* default `label` to `name`; that is a
separate, pi-compatible contract, not an inconsistency to harmonise away.)

**`validate_tool_arguments` is hand-rolled**, not `jsonschema` and not
pydantic. It checks `required` and does ad-hoc per-type checking, raising
`ValueError` with the collected errors. A keyword it does not know —
`minLength`, `enum`, `pattern` — looks enforced and is silently ignored. That
is a known limitation, and it is exactly why `define_tool` does not validate
nested schemas either: checking them would advertise an enforcement that does
not exist, and would reject `pydantic.model_json_schema()` output, which is
the documented way to build `parameters`.

### Three tool shapes, and what bridges them

| Class | Package | Adds |
|---|---|---|
| `ToolDefinition` | `tau_llm` | the wire-facing shape — `name`, `label`, `description`, `parameters`, `execute`, plus optional `prompt_snippet`, `prompt_guidelines` and `execution_mode` (`"parallel"` by default; `"sequential"` forces its whole batch to run one at a time) |
| `ToolDefinition` | `tau_agent_core` | identity by name, so the loop can dedupe and shadow |
| `ExtensionToolDefinition` | `tau_agent_core` | `source`, recording which extension registered it |

What is not interchangeable is `execute`. The `tau_llm` form is called with
the tool's own arguments; the extension form is called
`execute(tool_call_id, params, signal, on_update, ctx)`. `AgentSession` adapts
between them. **Do not pass a `define_tool()` result to
`api.register_tool()`** — the shape validates and the call signature does not.

`ToolDefinition` also has four experimental fields — `exposure` (`direct`,
`model-only`, `callable`, `deferred`, `hidden`), `namespace`, `tags` and
`output_schema`. None of them reaches the model; the wire carries `name`,
`description` and `parameters` only.

`ToolSpec` is a `Protocol` naming the three members a provider actually reads
(`name`, `description`, `parameters`), so anything with those three may be
sent regardless of which package built it.

## Constrained decoding

`DecodeConstraints` (exactly one of `grammar`, `json_schema` or `choices`),
`ConstraintViolation` and the `grammar` module carry τ's own machinery for
binding a model's output to a grammar; `Model.grammar_dialect` selects the
flavour the server speaks, and unset makes a constrained request raise. The
output is verified, so a server that dropped the constraint produces a
`ConstraintViolation` rather than unconstrained text passed off as constrained.
The Anthropic wire has no decode-constraint parameter and refuses a
constrained call. This has no pi equivalent.

One consequence worth knowing before you combine it with reasoning: for a
`grammar` or `choices` constraint τ **disables thinking** on the OpenAI wire
(`chat_template_kwargs.enable_thinking=false`, unless the request already sets
`chat_template_kwargs`), because the grammar binds the model's *first* token,
which on a reasoning model is inside its thinking block. A `json_schema`
constraint goes out as `response_format` and does not do this. That is a workaround for an upstream limitation rather than a design
position.
