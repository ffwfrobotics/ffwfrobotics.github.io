---
title: "Extensions"
category: "reference"
status: "draft"
---

# Extensions

<p class="axis">Cognition × Application</p>

Plain Python modules — `importlib`, no compile step, no manifest language. A
module exposes `def register(api): ...` and `api` is an `ExtensionAPI`. The
parameter is conventionally named `api`.

Lives in `tau_agent_core`, so extensions work headlessly, under the TUI, and
over RPC without knowing which. Python 3.12 or later.

## Two vocabularies, two handler contracts

`api.on(name, handler)` subscribes to both kinds, and routes by name. The name
you subscribe to therefore decides which contract you owe.

<figure class="dia"><svg viewBox="0 0 680 274" role="img" aria-labelledby="dia-hooks-t dia-hooks-d"><title id="dia-hooks-t">A mutating hook returns a value; a notify event does not</title><desc id="dia-hooks-d">A turn runs left to right along a horizontal spine through four stages: input, tool underscore call, tool underscore result and turn underscore end. Above the spine, under the heading mutating hooks, the return value is applied, sits a box reading handler with the arguments event and c t x, glossed that event is a plain dict. A plain arrow runs up from the tool underscore call stage into that handler, and a red arrow runs back down from the handler into the same stage, squared off in red where it leaves the handler. The red mark beside it reads the return is applied, glossed veto the call or patch its arguments. Below the spine, under the heading notify-only events, observer, cannot block, a wider box reads api dot on of all, or AgentSession dot subscribe, where the event is an AgentEvent object. Two faint arrows drop into it from the tool underscore call and tool underscore result stages, and neither returns.</desc><text x="0" y="22" class="label-soft">mutating hooks &#8212; the return value is applied</text><rect x="150" y="34" width="180" height="40" class="fill-ground stroke"/><text x="240" y="54" text-anchor="middle" class="label">handler(event, ctx)</text><text x="240" y="68" text-anchor="middle" class="label-soft">event is a plain dict</text><line x1="200" y1="134" x2="200" y2="82" class="stroke-hair"/><path d="M200 74 L196 83 L204 83 Z" class="fill-ink"/><rect x="275" y="69" width="10" height="10" class="fill-red"/><line x1="280" y1="79" x2="280" y2="126" class="stroke-red"/><path d="M280 134 L276 125 L284 125 Z" class="fill-red"/><text x="346" y="52" class="label-mark">the return is applied</text><text x="346" y="68" class="label-soft">veto the call, or patch its arguments</text><rect x="0" y="134" width="110" height="32" class="fill-ground stroke"/><text x="55" y="155" text-anchor="middle" class="label">input</text><line x1="110" y1="150" x2="150" y2="150" class="stroke"/><rect x="150" y="134" width="140" height="32" class="fill-ground stroke"/><text x="220" y="155" text-anchor="middle" class="label">tool_call</text><line x1="290" y1="150" x2="330" y2="150" class="stroke"/><rect x="330" y="134" width="150" height="32" class="fill-ground stroke"/><text x="405" y="155" text-anchor="middle" class="label">tool_result</text><line x1="480" y1="150" x2="520" y2="150" class="stroke"/><rect x="520" y="134" width="150" height="32" class="fill-ground stroke"/><text x="595" y="155" text-anchor="middle" class="label">turn_end</text><text x="0" y="196" class="label-soft">notify-only events &#8212; observer, cannot block</text><line x1="220" y1="166" x2="220" y2="208" class="stroke-soft"/><path d="M220 216 L216 207 L224 207 Z" class="fill-ash"/><line x1="405" y1="166" x2="405" y2="208" class="stroke-soft"/><path d="M405 216 L401 207 L409 207 Z" class="fill-ash"/><rect x="150" y="216" width="380" height="42" class="fill-ground stroke-hair"/><text x="340" y="236" text-anchor="middle" class="label">api.on(&quot;all&quot;)</text><text x="340" y="250" text-anchor="middle" class="label-soft">or AgentSession.subscribe() &#8212; event is an AgentEvent</text></svg><figcaption>One call, <code>api.on</code>, two contracts. Red marks the arrow that comes back, because that is the whole distinction: a mutating hook's return value is applied to the turn, so its handler takes <code>(event, ctx)</code> and gets a plain dict. A notify handler takes one argument and gets an <code>AgentEvent</code> object, and nothing it returns is read. Subscribing to a hook with a one-argument handler raises <code>TypeError</code> the first time it fires — which for <code>tool_call</code> blocks that call and ends the turn.</figcaption></figure>

| Kind | Handler | `event` is |
|---|---|---|
| mutating hook, lifecycle hook | `handler(event, ctx)` | a plain **dict** |
| notify-only event | `handler(event)` | an `AgentEvent` **object** |

**Mutating hooks** — the return value is applied:

| Hook | What returning a value does |
|---|---|
| `tool_call` | veto the call, or patch its arguments, before execution |
| `tool_result` | modify content or details, or terminate, after execution |
| `before_agent_start` | contribute to the system prompt |
| `input` | transform the user prompt; `{"handled": True}` consumes it without a turn, `{"refuse": "<reason>"}` refuses the submission (`submit` reports `accepted=False` with that reason and writes nothing) |
| `turn_end` | return `{message}` for a durable append before the next request |
| `user_turn_end` | return `{message}` for a durable append |
| `session_before_switch` | veto a session new, fork or switch operation |
| `annotate` | return JSON, stored on the message entry about to be written as `ext[<extension name>]` and never sent to the model. At most one handler per extension |
| `entry_written` | observe `{kind, entry_id, message, blocks}` for each message entry after it is in the store (a deep copy; the return is ignored). Not dispatched when `store_history` is off |
| `turn_setting_changed` | observe `{cursor_id, setting, old, new, source}` when a model or thinking change is recorded (return ignored) |

**Lifecycle hooks** — `session_start`, `session_shutdown`. Each carries a
`reason`, for example `"reload"`.

**Notify-only events** — every `AgentEvent` type: `agent_start`, `agent_end`,
`turn_start`, `message_start` / `message_update` / `message_end`,
`tool_execution_start` / `tool_execution_update` / `tool_execution_end`,
`side_completion_start` / `_update` / `_end`, `provider_retry`,
`follow_ups_dropped`, `suspension_open` / `suspension_closed` and
`lock_changed`, plus the wildcard `"all"`.

### A raising handler

A hook whose result can change what the turn does **ends the turn** when its
handler raises: `input`, `before_agent_start`, `tool_call`, `tool_result`,
`turn_end`, `user_turn_end`, `session_before_switch` and `annotate`. The error
reaches the error listeners first, and `agent_end` then carries
`end_reason: "error"` naming your extension and the hook (`HookHandlerError`).
For `tool_call` the failing call is answered with its block text, every other
call in the batch is answered as aborted, and none runs. A raise at
`entry_written`, `turn_setting_changed`, `session_start` or `session_shutdown`
is reported and the turn goes on. `session_before_switch` has no turn: its
failure means the swap does not happen and the `new_session`, `fork` or
`switch_session` call raises. `turn_end` ends the turn even for a handler that
only observes, so use `"all"` or `AgentSession.subscribe()` for pure
observation. An unpoliced handler has no deadline.

### Handler policies

`api.on(event, handler, policy=NAME)` runs a handler under a policy that
decides its deadline and what its failure becomes. `gating`, `advisory` and
`human` are built in, and `api.register_policy(name, policy)` adds one (a policy
is anything with `async run(call, site)`). A policy applies to a mutating or
lifecycle hook or an `ext:` channel, never a notify event. Under a policy a
plain `def` handler runs on a worker thread and the hook returns at the
deadline; `gating` fails on timeout (which ends the turn) and `advisory`
proceeds and sets a `policy:<hook>` warning. Policies are experimental below
1.0.

**Handlers must not block.** With no policy a handler runs inline on the event
loop, so a `sleep()` or a slow call inside it stalls the agent. Give anything
slow or remote a timeout policy.

### Two sharp edges

**Choose the turn-boundary hook by cadence.** `turn_end` fires once per
*agent-loop* turn, so one user request resolved in six tool round-trips fires
it six times. `user_turn_end` fires once per `prompt()`. Anything that should
happen once per thing-the-user-asked-for wants the latter.

**`api.on("turn_end", ...)` always resolves to the mutating hook**, never the
notify event of the same name. There is no way to observe a plain
notify-grade `turn_end` through `api.on` — use `"all"` or
`AgentSession.subscribe()`. `context` was a hook in an earlier design and is
retired: calling `api.on("context", ...)` raises.

## The `ExtensionAPI` surface

```python
# Events — a mutating hook or a notify event through the same call.
# Returns an unsubscribe callable.
api.on(event: str, handler: Callable, *, policy: str | None = None) -> Callable[[], None]

# Tools
api.register_tool(definition: dict | ExtensionToolDefinition) -> None
api.get_all_tools() -> list[Any]
api.set_active_tools(names: list[str]) -> None

# Commands and shortcuts
api.register_command(name: str, command: dict) -> str | None   # None, or the qualified name that holds it
api.get_command(name: str) -> dict | None
await api.run_command(name: str, args: str = "")   # wrap or defer to another command
api.unregister_command(name: str) -> None
api.register_shortcut(key: str, command: str, *, args: str = "",
                      description: str | None = None) -> None   # ctrl+e <key>

# A command that declares what it TAKES, so every head can complete and ask for it
api.register_flow(name: str, description: str, handler, *,
                  argument=None, domain=None, values=None) -> str | None

# Put a request in front of whoever is attached; optionally lock the session
api.request_user_action(sentence: str, *, lock: bool = False,
                        ask: dict | None = None,
                        release: str | None = None) -> str

# Session state
api.append_entry(custom_type: str, data: dict) -> None   # durable, not RAM-only
api.set_session_name(name: str) -> None
api.get_session_name() -> str | None

# Messaging
api.send_user_message(content: str, deliver_as: str = "followUp") -> None
api.send_message(message: dict, options: dict | None = None) -> None

# Turn origination — the one door, for extensions
await api.submit(...)
api.submit_threadsafe(...)

# Inter-extension pub/sub, on ext:<name>:<topic> channels
await api.emit(topic: str, payload: Any) -> None
await api.request(topic: str, payload: Any, *, timeout_s: float) -> list[RequestReply]
api.subscriber_count(topic: str) -> int

# Waiting for an answer (step-debugger suspensions)
await api.suspend(spec: dict) -> dict
api.can_suspend() -> bool ; api.can_suspend_here() -> bool ; api.suspend_refusal() -> str | None
api.resumed() -> dict | None

# Handler policies
api.register_policy(name: str, policy) -> None

# Warnings that persist until cleared
api.set_warning(key: str, message: str, severity: str = "warning") -> None
api.clear_warning(key: str) -> None

# Per-extension config
api.config -> dict[str, Any]

api.ui      -> ExtensionUI
api.context -> ExtensionContext
```

`api.config` is sourced from `~/.tau/config.json`'s `extensions.<name>` block,
keyed by the extension's identifier (a drop-in's file stem, an installed
package's module name), and overridable per run with `--ext-config
NAME:KEY=VALUE`, where the CLI wins. The value is JSON-decoded when it parses
(`budget:ceiling=5.0`), else it is a string. It replaces `register_flag` and
`get_flag`, which were **deleted rather than deprecated** — they never
populated a value.

A module may declare `CONFIG_SCHEMA`, a `ui.form` spec (`{title, fields}`)
naming the keys `api.config` may hold. It is validated at load; an invalid one
raises `ExtensionCapabilityError` and `register` never runs. The RPC verbs
`get_extension_config` and `set_extension_config` read and write against it.
Values set that way last for the session and are not written to `config.json`.

`send_user_message`'s default is `"followUp"`, not `"steer"`. The other valid
values are `"nextTurn"` and `"steer"`.

### `register_tool` takes a plain dict

Not a `ToolDefinition`. `tau_llm.define_tool()` exists and is validated, but it
builds the *other* tool shape: its `execute` takes the tool's own parameters,
while an extension tool's `execute` is
`execute(tool_call_id, params, signal, on_update, ctx)` and receives the bound
`ExtensionContext`.

`register_tool` will not accept a `ToolDefinition`, and that is deliberate —
the two contracts are not interchangeable. See
[`tau_llm`](tau-llm.md#three-tool-shapes-and-what-bridges-them).

`ExtensionAPI.register_tool()` *does* default `label` to `name`, where
`define_tool` refuses to. That is a pi-compatible contract, not an
inconsistency to harmonise away.

## Discovery, authorization and collisions

Finding is not loading. τ discovers two kinds of source and loads one only once
it is authorized:

* **drop-ins** in `~/.tau/extensions/`, bare `*.py` files or `<dir>/__init__.py`
  packages, alphabetically. The identifier is the file stem.
* **installed packages** that declare an entry point in the `tau.extensions`
  group, naming a module that exposes `register(api)`:

  ```toml
  [project.entry-points."tau.extensions"]
  planner = "tau_router.planner"
  ```

  The identifier is the module name (`tau_router.planner`).

An unauthorized source is offered in the TUI and named on stderr by the
headless modes, which never prompt. The `tau ext` subcommands manage this:
`list` (every source found and whether it would load; imports nothing),
`authorize`, `revoke`, `disable` and `enable`. A package's authorization
record names its distribution and version, so a new version asks again.
Drop-ins present at the first 0.14.0 start were authorized once,
automatically. A discovered extension that fails to load gets one notice and
the run goes on; `tau ext disable` silences it.

Every explicit `-e` / `--extension PATH|MODULE` is authorized by being named.
It is repeatable, a value holding a `/` or ending in `.py` is a path and
anything else an installed module, and it loads even under `--no-extensions`,
which disables discovery only. An explicitly named extension that fails to load
stops startup in `-p` and `--mode rpc`.

There is **no** project-local `<cwd>/.tau/extensions/` discovery, and no
dependency-manifest convention inside an extension directory. The first is
deferred pending a trust gate rather than overlooked: a repository you cloned
should not be able to run code by being opened.

Collision handling differs by kind, on purpose:

| Kind | On a duplicate |
|---|---|
| tool | **raises** `ValueError` at load time |
| command | first-wins on the typed name. The loser keeps its qualified name `ext:<extension>:<command>`, and `register_command` returns it |
| shortcut | last-write-wins, with a logged warning |
| `tool_call` hook chain | the first `block: True` wins |
| `before_agent_start` system prompt | last contribution wins |

## Asking the user, and locking the session

`api.request_user_action` appends one reserved `extension_request` entry to the
session. That is what makes it different from a modal: it is on the record, it
survives a restart, and **every head renders it** — the TUI, the REPL, and an
RPC host through `get_pending_request` / `answer_request`.

Two keys give four states. `lock=True` refuses further submissions until the
request is answered; `ask` is a form spec (`{title, fields, actions}`) that
draws a control rather than a sentence. A request with neither is a notice; one
with both is a locked question. `release` names a command that clears the lock —
a command is exempt from a lock by *placement* in the pipeline, not by name.

Raise a request where nothing appends after it — `user_turn_end`,
`session_start`, or a command handler. A `tool_call` hook is mid-turn, so its
request ends up several entries behind the leaf and the cursor never reaches it.
`api.suspend` is the in-process cousin: it pauses the turn and waits for a
responder (a head, or an RPC host that has sent `declare_capabilities`), from
`tool_call`, `entry_written`, `turn_end` or `user_turn_end`. See
[RPC](rpc.md#suspensions). `examples/44_release_gate.py` is the worked demo, and
`examples/30_permission_gate.py` is the human-in-the-loop bash gate.

### Headless dialogs raise

`ctx.ui.form` raises `HeadlessDialogError` in headless mode unless a policy is
configured — `--ui-defaults form=defaults` or `config.json`'s `ui_defaults`. A
dialog that quietly picked a default would make an unattended run's result
depend on a question nobody saw.

`confirm`, `select` and `input` **no longer exist**. Each is replaced by a
field on an `ask` — a `confirm` field, a `select` field, a text field. They are
named rather than silently dropped:
`--ui-defaults confirm=yes` in an old script is refused with the replacement
named, instead of parsing into a policy that governs nothing.

## The bus capability grant

An extension that touches a message bus declares `TOUCHES_BUS = True` and is
**refused at load time** unless the run opts in with `--bus` (CLI) or
`bus_available=True` (SDK). It is a capability grant, not a default.

The declaration has a second half: such an extension must also declare a
non-empty `SUBJECTS`, naming what it touches. Leaving it unset is refused even
with `--bus` given, because the grant is per-subject rather than blanket.

The shipped example is `nats_bus.py`, which needs
`pip install 'ffwf-tau-agent-core[bus]'` for its NATS client.
