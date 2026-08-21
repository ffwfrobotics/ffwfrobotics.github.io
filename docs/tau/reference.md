---
title: "Reference"
category: "reference"
status: "draft"
---

# Tau — Reference

<p class="axis">Cognition × Application</p>

Extension API, session tree format, configuration keys, and CLI flags.

!!! note "Draft"
    Built for lookup, not narrative reading. Written from the source repo's own
    `docs/tau-llm.md`, `docs/tau-agent-core.md`, `docs/tau-coding-agent.md`,
    `docs/extensions.md`, and `docs/REMOTE-CONTROL.md` — each of those is
    itself checked against running code, not aspirational. `tau --help` is the
    exact contract for the CLI table below; treat a disagreement as this page
    being stale.

## Packages

Four distributions, each installable on its own. The `ffwf-` prefix is not
decoration: `tau-ai` and `tau-llm` on PyPI are unrelated third-party projects,
so `pip install tau-llm` fetches someone else's code.

| Distribution | Imports as | What it is |
|---|---|---|
| `ffwf-tau-llm` | `tau_llm` | Provider and streaming layer. |
| `ffwf-tau-agent-core` | `tau_agent_core` | Agent loop, tools, sessions, extensions. Headless. |
| `ffwf-tau-coding-agent` | `tau_coding_agent` | The `tau` command and the Textual TUI. |
| `ffwf-tau-jmfts` | `tau_jmfts` | JMFTS-backed session store. |

Installing the top of the stack pulls the rest:

```bash
pip install 'ffwf-tau-coding-agent[tui]'
```

Everything past the headless core is an extra, and each one reports its own
absence with the install command rather than a traceback:

| Extra | Adds | Needed for |
|---|---|---|
| `ffwf-tau-coding-agent[tui]` | `textual`, `rich` | the interactive TUI. `tau -p` and `tau --mode rpc` run a full turn without it. |
| `ffwf-tau-coding-agent[jmfts]` | `ffwf-tau-jmfts` | `--store jmfts`. |
| `ffwf-tau-agent-core[bus]` | `nats-py` | the built-in `nats_bus` extension. |
| `ffwf-tau-agent-core[testing]` | `pytest` | importing `tau_agent_core.testing`. |

The install puts **two** console scripts on PATH — `tau` and `ffwf-tau`, the
same entry point behind each. Type `tau`; write `ffwf-tau` in scripts, systemd
units and Dockerfiles. See the
[DevOps Manual](devops.md#which-command-name-to-write) for why.

## Provider layer (`tau_llm`)

τ speaks the OpenAI-compatible chat-completions API. `Model` carries the
usual fields (`id`, `provider`, `base_url`, `context_window`, `max_tokens`)
plus four τ-specific ones:

| Field | Meaning |
|---|---|
| `reasoning_replay` | `"turn"` (default) or `"all"`. Whether a prior turn's chain-of-thought is resent on every later call. τ defaults away from pi's always-resend behavior — measured 72%→28% of payload size on a real transcript. |
| `grammar_dialect` | Which constrained-decoding grammar flavor the target server speaks. |
| `extra_body` | Arbitrary per-model JSON merged into every request body — the escape hatch for a server-specific field (e.g. `chat_template_kwargs`) the provider has no first-class knob for. |
| `server_features` | Declares which optional server behaviors (e.g. native structured output) this endpoint actually supports, rather than τ probing for them. |

A `Provider` is one method: `stream_chat(messages, tools, model, options) ->
AsyncIterator[StreamEvent]`. There is no separate `api`/`name` property on
the interface — a provider is identified by the `Model.provider` string that
selects it.

**Providers are pooled, not registered.** An earlier registry design was
built, found to construct a fresh empty registry on every call (so it never
actually cached anything) and measured at 42ms of overhead per call, then
deleted outright. `tau_llm.client`'s connection pool (keyed on
provider+base_url+api_key) replaced it.

**Tool argument validation is hand-rolled**, not `jsonschema`/pydantic —
`validate_tool_arguments` checks `type` and `required` from a plain-dict
schema and nothing else: no `minLength`, no `minimum`, no `enum`. Writing one
of those into a tool schema looks enforced and is silently ignored.

`define_tool()` builds the definition and validates it, raising on a malformed
one rather than handing back a tool that fails later:

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

It returns a `ToolDefinition`. A single mapping may be passed positionally
instead of keywords. This is the provider-layer tool shape;
`api.register_tool()` in the [Extension API](#extension-api) takes a different
one, and the two are not interchangeable.

## Agent loop & sessions (`tau_agent_core`)

`AgentLoop.__init__(self, config: AgentLoopConfig, emit=None, tools=None,
model=None, abort_signal=None, hook_dispatcher=None, steer_queue=None)` —
`config`/`tools`/`model`/`abort_signal` are constructor arguments, not
fields on one shared object. `AgentLoopConfig` is deliberately small:
`model`, `system_prompt`, `tool_execution_mode`, `max_retries`, `max_turns`,
`temperature`, `api_key`, `reasoning`. Everything an earlier design put on
the config as callbacks (`before_tool_call`, `get_steering_messages`, …) is
now injected instead — extension hooks go through `hook_dispatcher`
(gated on `has_hook_handlers()`, so a zero-extension session pays nothing
for it), mid-turn steering goes through a shared `steer_queue`.

**Sessions are a tree, not a chat log.** Append-only JSONL; a
`ConversationTree` walks `parent_id` chains to build model input for the
active leaf — an *ephemeral frame* (system prompt, tool schemas) plus the
*exact linear path* to that leaf, no hidden channel either side of that. A
`SessionLog` Protocol (`append_message`, `append_navigate`,
`append_branch_summary`, `entries`, `cursor`, …) is the minimal contract
both the SDK's in-memory log and the TUI's file-backed one satisfy.

**The one door.** Every input source — TUI keystrokes, `tau -p`, the SDK, an
extension, an RPC client — funnels through `AgentSession.submit()`.
`multitask_strategy` decides what happens when a submission arrives while a
turn is already running:

| Strategy | Effect |
|---|---|
| `reject` | Refuse the new submission outright (`rejection_reason` explains why). |
| `enqueue` | Queue it; it runs after the current turn ends. |
| `steer` | Injected into the running turn without waiting for it to end. |
| `rollback` | Navigate back to the pre-turn leaf, then run as if from there — the running turn's output becomes an abandoned sibling branch, not a deletion. |
| `fork` | Branch the conversation instead of extending the active leaf. |

`prompt()` is a thin wrapper that builds a `Submission` and calls `submit()`
— not a second door.

**SDK entry point:**

```python
def create_agent_session(
    model: str | Model = "gpt-4o", provider: str = "openai",
    base_url: str | None = None, api_key: str | None = None,
    tools: list[str] | None = None, session_log: SessionLog | None = None,
    extensions: list[Callable] | None = None, system_prompt: str | None = None,
    thinking_level: str = "off", cwd: str | None = None,
    tool_execution_mode: Literal["sequential", "parallel"] = "parallel",
    compaction_policy: CompactionPolicy | None = None,
    bus_available: bool = False,
) -> AgentSession
```

`tools` takes built-in name strings only (`read`, `write`, `edit`, `bash`,
`grep`, `find`, `ls`) — a custom `AgentTool` instance needs the
`AgentSession` constructor directly. There is no `settings=` parameter: an
earlier version had one that was silently ignored, so it was removed rather
than kept as a no-op — passing it raises `TypeError`.

**Compaction** is LLM-backed with no fabricated-summary fallback:
`should_compact(context_tokens, context_window, settings) -> bool`;
`prepare_compaction(path_entries, settings) -> CompactionPreparation | None`;
`async def compact(preparation, model, api_key, *, custom_instructions=None,
thinking_level=None) -> CompactionResult`. A compaction error raises rather
than silently truncating the conversation.

## Extension API

Extensions are plain Python modules — `importlib`, no compile step, no
manifest language. A module exposes `def register(api): ...`; `api` is an
`ExtensionAPI`.

```python
# Events — subscribe a mutating hook or a notify-only event through the
# same call; api.on returns an unsubscribe callable.
api.on(event: str, handler: Callable) -> Callable[[], None]

# Tools
api.register_tool(definition: dict) -> None       # plain dict, not a pydantic model
api.get_all_tools() -> list[Any]
api.set_active_tools(names: list[str]) -> None

# Commands and shortcuts
api.register_command(name: str, command: dict) -> None
api.register_shortcut(...)

# Session state
api.append_entry(custom_type: str, data: dict) -> None   # durable, not RAM-only
api.set_session_name(name: str) -> None
api.get_session_name() -> str | None

# Messaging and turn origination — the "one door" for extensions
api.send_user_message(content: str, deliver_as: str = "followUp") -> None
await api.submit(...)
api.submit_threadsafe(...)

# Inter-extension pub/sub
await api.emit(topic: str, payload: Any) -> None    # ext:<name>:<topic> channels

# Per-extension config
api.config -> dict[str, Any]     # ~/.tau/config.json → "extensions.<name>", or --ext-config

api.ui -> ExtensionUI
api.context -> ExtensionContext
```

**Mutating hooks** (handler's return value is applied) — `tool_call`
(veto/patch args), `tool_result` (modify content/terminate), `before_agent_start`
(contribute to the system prompt), `input` (transform the user prompt),
`turn_end`, `user_turn_end`, `session_before_switch` (veto a session
new/fork/switch operation).

**Lifecycle hooks** — `session_start`, `session_shutdown` (carries a
`reason`, e.g. `"reload"`).

**Notify-only events** — `agent_start`, `agent_end`, `turn_start`,
`message_start`/`message_update`/`message_end`,
`tool_execution_start`/`tool_execution_update`/`tool_execution_end`, plus the
wildcard `"all"`.

**One sharp edge:** `api.on("turn_end", ...)` always resolves to the
*mutating* hook — there is no way to observe a plain notify-grade
`turn_end` via `api.on`. Use `"all"` or `AgentSession.subscribe()` for pure
observation.

**Discovery** — the global directory `~/.tau/extensions/` (loaded
alphabetically), then every explicit `-e`/`--extension PATH` (repeatable).
No project-local `<cwd>/.tau/extensions/` discovery, and no
dependency-manifest convention inside an extension directory. Collision
handling differs by kind: a duplicate **tool** name raises `ValueError` at
load time; **commands** are silent last-write-wins; **shortcuts** are
last-write-wins with a logged warning.

**Headless dialogs raise, not guess.** In headless mode, `ctx.ui.confirm` /
`select` / `input` / `form` raise `HeadlessDialogError` unless a policy is
configured (`--ui-defaults METHOD=ANSWER,...` or `config.json`'s
`ui_defaults`).

## RPC

`--mode rpc` speaks JSON-RPC 2.0 over stdio (newline-delimited). 20 verbs
are implemented, 7 are formally declined with a stated reason rather than
silently absent:

| Tier | Verbs |
|---|---|
| A/C — turn + state | `submit`, `prompt`, `abort`, `get_state`, `get_messages`, `get_commands`, `get_tools`, `get_capabilities`, `new_session`, `fork`, `switch_session` |
| B — session management | `compact`, `set_model`, `get_models`, `set_session_name`, `get_session_name`, `get_session_stats`, `list_sessions`, `set_auto_compaction`, `get_last_assistant_text` |

`submit`/`prompt` answer **twice**: an immediate acceptance response, then a
later `agent_end` notification when the turn finishes. A rejected submission
errors on the response instead (`-32000 SUBMISSION_REJECTED`), with no later
event.

Seven verbs are declined, each reachable via `get_capabilities().declined[]`:

| Verb | Why declined |
|---|---|
| `send_tool_result` | A second, unauthenticated path into the tool executor a host never drove the call for. |
| `bash` | Same reasoning — an out-of-band shell verb bypasses the loop's own admission rules. |
| `cycle_model` | A TUI keybinding affordance, not a protocol verb — a host names a model via `set_model` instead. |
| `cycle_thinking_level` | Same judgment; τ also has no `thinkingLevel` concept on `AgentSession` for a `set_*` verb to act on. |
| `set_steering_mode` | `multitask_strategy` is already a per-submission parameter, not a session-wide mode to toggle. |
| `set_follow_up_mode` | Same — `multitask_strategy="enqueue"` already covers it per-call. |
| `export_html` | Rendering is the host's job; τ hands back `get_messages` and events. |

The source repo's `docs/RPC-PROTOCOL.md` is the exact, generated, test-locked
wire reference (a drift test asserts the checked-in file equals its own
`render()` output) — treat the table above as an index into it, not a
replacement.

## CLI flags

| Flag | Short | Notes |
|---|---|---|
| `--print` | `-p` | run one turn headlessly, print, exit |
| `--mode {text,json,rpc}` | | headless output format; `rpc` doesn't combine with `--print` |
| `--model` | `-m` | config key or `provider/id` shorthand |
| `--provider` | | long-only |
| `--tools`/`--no-tools` | `-t`/`-nt` | allowlist / offer the model no tools at all, built-in or extension-registered |
| `--exclude-tools` | `-xt` | denylist |
| `--no-builtin-tools` | `-nbt` | drops the built-in set only; extension-registered tools survive and are still offered |
| `--extension PATH` (repeatable) | `-e` | explicit load, always runs even under `--no-extensions` |
| `--no-extensions` | `-ne` | disables discovery only |
| `--bus` | | declare this run may reach a message bus, so `TOUCHES_BUS` extensions (e.g. `nats_bus`) are allowed to load |
| `--ext-config NAME.KEY=VALUE` (repeatable) | | per-extension config override, CLI wins over `config.json` |
| `--ui-defaults METHOD=ANSWER,...` | | headless dialog auto-answers; `--print` only |
| `--system-prompt` / `--append-system-prompt` (repeatable) | | |
| `--continue` / `--resume` / `--session REF` / `--fork REF` | `-c` / `-r` | mutually exclusive. `--resume` is TUI-sidebar-only — it raises at the CLI |
| `--name` | `-n` | session display title |
| `--no-session` | | ephemeral, no persistence |
| `--thinking {off,minimal,low,medium,high,xhigh}` | | requires a reasoning-capable model |
| `--store {file,jmfts}` | | session backend for this run |
| `--session-dir DIR` | | file store only; default differs by mode (`~/.tau/sessions` vs. a private RPC temp dir) |
| `--import-session PATH` / `--export-session REF PATH` | | JMFTS store transfer, then exit |
| `--verbose` | | long-only — `-v` is `--version`, not verbose |
| `--help` / `--version` | `-h` / `-v` | |

See the [DevOps Manual](devops.md) for how these fit into a deployment, and
the [Cookbook](cookbook.md) for worked extension examples.
