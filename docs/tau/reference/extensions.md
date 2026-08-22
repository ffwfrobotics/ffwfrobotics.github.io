---
title: "Extensions"
category: "reference"
status: "draft"
---

# Extensions

<p class="axis">Cognition × Application</p>

Plain Python modules — `importlib`, no compile step, no manifest language. A
module exposes `def register(api): ...` and `api` is an `ExtensionAPI`.

Lives in `tau_agent_core`, so extensions work headlessly, under the TUI, and
over RPC without knowing which.

## Two vocabularies, two handler contracts

`api.on(name, handler)` subscribes to both kinds, and routes by name. The name
you subscribe to therefore decides which contract you owe.

<figure class="dia"><svg viewBox="0 0 680 274" role="img" aria-labelledby="dia-hooks-t dia-hooks-d"><title id="dia-hooks-t">A mutating hook returns a value; a notify event does not</title><desc id="dia-hooks-d">A turn runs left to right along a horizontal spine through four stages: input, tool underscore call, tool underscore result and turn underscore end. Above the spine, under the heading mutating hooks, the return value is applied, sits a box reading handler with the arguments event and c t x, glossed that event is a plain dict. A plain arrow runs up from the tool underscore call stage into that handler, and a red arrow runs back down from the handler into the same stage, squared off in red where it leaves the handler. The red mark beside it reads the return is applied, glossed veto the call or patch its arguments. Below the spine, under the heading notify-only events, observer, cannot block, a wider box reads api dot on of all, or AgentSession dot subscribe, where the event is an AgentEvent object. Two faint arrows drop into it from the tool underscore call and tool underscore result stages, and neither returns.</desc><text x="0" y="22" class="label-soft">mutating hooks &#8212; the return value is applied</text><rect x="150" y="34" width="180" height="40" class="fill-ground stroke"/><text x="240" y="54" text-anchor="middle" class="label">handler(event, ctx)</text><text x="240" y="68" text-anchor="middle" class="label-soft">event is a plain dict</text><line x1="200" y1="134" x2="200" y2="82" class="stroke-hair"/><path d="M200 74 L196 83 L204 83 Z" class="fill-ink"/><rect x="275" y="69" width="10" height="10" class="fill-red"/><line x1="280" y1="79" x2="280" y2="126" class="stroke-red"/><path d="M280 134 L276 125 L284 125 Z" class="fill-red"/><text x="346" y="52" class="label-mark">the return is applied</text><text x="346" y="68" class="label-soft">veto the call, or patch its arguments</text><rect x="0" y="134" width="110" height="32" class="fill-ground stroke"/><text x="55" y="155" text-anchor="middle" class="label">input</text><line x1="110" y1="150" x2="150" y2="150" class="stroke"/><rect x="150" y="134" width="140" height="32" class="fill-ground stroke"/><text x="220" y="155" text-anchor="middle" class="label">tool_call</text><line x1="290" y1="150" x2="330" y2="150" class="stroke"/><rect x="330" y="134" width="150" height="32" class="fill-ground stroke"/><text x="405" y="155" text-anchor="middle" class="label">tool_result</text><line x1="480" y1="150" x2="520" y2="150" class="stroke"/><rect x="520" y="134" width="150" height="32" class="fill-ground stroke"/><text x="595" y="155" text-anchor="middle" class="label">turn_end</text><text x="0" y="196" class="label-soft">notify-only events &#8212; observer, cannot block</text><line x1="220" y1="166" x2="220" y2="208" class="stroke-soft"/><path d="M220 216 L216 207 L224 207 Z" class="fill-ash"/><line x1="405" y1="166" x2="405" y2="208" class="stroke-soft"/><path d="M405 216 L401 207 L409 207 Z" class="fill-ash"/><rect x="150" y="216" width="380" height="42" class="fill-ground stroke-hair"/><text x="340" y="236" text-anchor="middle" class="label">api.on(&quot;all&quot;)</text><text x="340" y="250" text-anchor="middle" class="label-soft">or AgentSession.subscribe() &#8212; event is an AgentEvent</text></svg><figcaption>One call, <code>api.on</code>, two contracts. Red marks the arrow that comes back, because that is the whole distinction: a mutating hook's return value is applied to the turn, so its handler takes <code>(event, ctx)</code> and gets a plain dict. A notify handler takes one argument and gets an <code>AgentEvent</code> object, and nothing it returns is read. Subscribing to a hook with a one-argument handler raises <code>TypeError</code> the first time it fires — which for <code>tool_call</code> is the fail-closed path, where a raising handler blocks the call.</figcaption></figure>

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
| `input` | transform the user prompt |
| `turn_end` | — |
| `user_turn_end` | — |
| `session_before_switch` | veto a session new, fork or switch operation |

**Lifecycle hooks** — `session_start`, `session_shutdown`. Each carries a
`reason`, for example `"reload"`.

**Notify-only events** — `agent_start`, `agent_end`, `turn_start`,
`message_start` / `message_update` / `message_end`, `tool_execution_start` /
`tool_execution_update` / `tool_execution_end`, plus the wildcard `"all"`.

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
api.on(event: str, handler: Callable) -> Callable[[], None]

# Tools
api.register_tool(definition: dict | ExtensionToolDefinition) -> None
api.get_all_tools() -> list[Any]
api.set_active_tools(names: list[str]) -> None

# Commands and shortcuts
api.register_command(name: str, command: dict) -> None
api.register_shortcut(...)                    # guarded ctrl+e namespace

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

# Per-extension config
api.config -> dict[str, Any]

api.ui      -> ExtensionUI
api.context -> ExtensionContext
```

`api.config` is sourced from `~/.tau/config.json`'s `extensions.<name>` block,
keyed by file stem, and overridable per run with `--ext-config
NAME.KEY=VALUE`, where the CLI wins. It replaces `register_flag` and
`get_flag`, which were **deleted rather than deprecated** — they never
populated a value.

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

## Discovery and collisions

Discovery is the global directory `~/.tau/extensions/`, loaded
alphabetically, then every explicit `-e` / `--extension PATH`, which is
repeatable and loads even under `--no-extensions`. `--no-extensions` disables
discovery only.

There is **no** project-local `<cwd>/.tau/extensions/` discovery, and no
dependency-manifest convention inside an extension directory. The first is
deferred pending a trust gate rather than overlooked: a repository you cloned
should not be able to run code by being opened.

Collision handling differs by kind, on purpose:

| Kind | On a duplicate |
|---|---|
| tool | **raises** `ValueError` at load time |
| command | silent last-write-wins |
| shortcut | last-write-wins, with a logged warning |

## Headless dialogs raise

In headless mode, `ctx.ui.confirm`, `select`, `input` and `form` raise
`HeadlessDialogError` unless a policy is configured — `--ui-defaults
METHOD=ANSWER,...` or `config.json`'s `ui_defaults`. A dialog that quietly
picked a default would make an unattended run's result depend on a question
nobody saw.

## The bus capability grant

An extension that touches a message bus declares `TOUCHES_BUS = True` and is
**refused at load time** unless the run opts in with `--bus` (CLI) or
`bus_available=True` (SDK). It is a capability grant, not a default.

The declaration has a second half: such an extension must also declare a
non-empty `SUBJECTS`, naming what it touches. Leaving it unset is refused even
with `--bus` given, because the grant is per-subject rather than blanket.

The shipped example is `nats_bus.py`, which needs
`pip install 'ffwf-tau-agent-core[bus]'` for its NATS client.
