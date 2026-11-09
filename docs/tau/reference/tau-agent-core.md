---
title: "tau_agent_core"
category: "reference"
status: "draft"
---

# `tau_agent_core` — the runtime

<p class="axis">Cognition × Application</p>

The loop that drives a conversation, the door every input arrives through, and
the tree a session actually is. Headless: no Textual, no assumptions about
stdin or stdout. It runs under the TUI, in a host process, or as an RPC
subprocess, and cannot tell which.

Distribution `ffwf-tau-agent-core`, Python 3.12 or later. It depends on
`tau_llm`; `tau_agent_core` never imports `tau_coding_agent`.

## The agent loop

```python
AgentLoop(
    config: AgentLoopConfig, emit=None, tools=None, model=None,
    abort_signal=None, hook_dispatcher=None, steer_queue=None,
    mid_turn_compactor=None, writer=None, call_gate=None,
    turn_settings=None, input_failure=None, position=None,
)
```

`AgentLoop` lives in `tau_agent_core.agent_loop` and is not re-exported from
the package root. `config`, `tools`, `model` and `abort_signal` are constructor
arguments, not fields on one shared object. `AgentLoopConfig` is deliberately
small: `model`, `system_prompt`, `system_prompt_override`,
`tool_execution_mode`, `max_retries`, `max_turns`, `repeat_tool_call_limit`,
`temperature`, `api_key`, `reasoning`.

Everything an earlier design put on the config as callbacks —
`before_tool_call`, `get_steering_messages`, `transform_context` — is injected
instead. Extension hooks go through `hook_dispatcher`; mid-turn steering goes
through a shared `steer_queue`; `mid_turn_compactor` is offered the context at
each turn boundary; `writer` receives each message as it exists, so the loop
need not hold a turn's output in memory to persist it; `call_gate` refuses a
model-issued call by name while the tool stays declared (so the tool block and
the prompt cache hold); and `turn_settings` is awaited before every request for
its model, key, reasoning level and temperature, so a switch made between two
requests reaches the second. With a `turn_settings` source the config's own
`temperature`, `api_key` and `reasoning` are ignored.

`max_turns` defaults to `None`: no ceiling. pi has none either, and τ's former
hardcoded 50 is gone. Set it through `create_agent_session(max_turns=...)` or
the config. What bounds a runaway loop without one is the abort signal and
`repeat_tool_call_limit`, which stops the loop when that many turns in a row
repeat the same wholly-failing batch of tool calls (default 3; `None`
disables it). `agent_end` carries `end_reason`: `done`, `terminate`,
`aborted`, `max_turns`, `repeat_tool_calls`, `error` or `suspended`, so a
caller can tell a truncated answer from a complete one.

## Two event vocabularies

This is the thing most worth understanding, because it spans four files and
two sets of names that describe the same turn.

<figure class="dia"><svg viewBox="0 0 680 240" role="img" aria-labelledby="dia-vocab-t dia-vocab-d"><title id="dia-vocab-t">Where the provider's events become the loop's events</title><desc id="dia-vocab-d">Three columns. On the left, under the heading tau underscore l l m streaming events, four boxes: TextDeltaEvent, ThinkingDeltaEvent and ToolCallDeltaEvent drawn in a light outline, and DoneEvent dot final drawn in a heavier one. Each of the three light boxes sends a thin arrow right into a tall box in the middle named AgentLoop dot run. DoneEvent dot final instead sends a red connector, squared off in red where it leaves the box, which runs right then up and enters an inner box named get underscore tool underscore calls, glossed as reading off the final message. Below that inner box sits a second one named underscore execute underscore tool underscore calls, glossed sequential or parallel. On the right, under the heading tau underscore agent underscore core AgentEvents, four more boxes receive arrows from the loop: message start with update and end, tool execution start with update and end, turn start and turn end, and agent start and agent end. Beneath the left column the red mark reads what actually runs, glossed that get underscore tool underscore calls reads DoneEvent dot final and never the accumulated deltas.</desc><text x="0" y="22" class="label-soft">tau_llm streaming events</text><text x="460" y="22" class="label-soft">tau_agent_core AgentEvents</text><rect x="0" y="34" width="196" height="28" class="fill-ground stroke-hair"/><text x="98" y="53" text-anchor="middle" class="label">TextDeltaEvent</text><rect x="0" y="66" width="196" height="28" class="fill-ground stroke-hair"/><text x="98" y="85" text-anchor="middle" class="label">ThinkingDeltaEvent</text><rect x="0" y="98" width="196" height="28" class="fill-ground stroke-hair"/><text x="98" y="117" text-anchor="middle" class="label">ToolCallDeltaEvent</text><rect x="0" y="140" width="196" height="32" class="fill-ground stroke"/><text x="98" y="161" text-anchor="middle" class="label">DoneEvent.final</text><line x1="196" y1="48" x2="240" y2="48" class="stroke-hair"/><path d="M248 48 L239 44 L239 52 Z" class="fill-ink"/><line x1="196" y1="80" x2="240" y2="80" class="stroke-hair"/><path d="M248 80 L239 76 L239 84 Z" class="fill-ink"/><line x1="196" y1="112" x2="240" y2="112" class="stroke-hair"/><path d="M248 112 L239 108 L239 116 Z" class="fill-ink"/><rect x="191" y="151" width="10" height="10" class="fill-red"/><path d="M201 156 H220 V136 H240" class="stroke-red fill-none"/><path d="M248 136 L239 132 L239 140 Z" class="fill-red"/><rect x="248" y="30" width="182" height="190" class="fill-ground stroke"/><text x="339" y="54" text-anchor="middle" class="label">AgentLoop.run</text><text x="339" y="70" text-anchor="middle" class="label-soft">one turn, then loop</text><rect x="262" y="118" width="154" height="36" class="fill-surface stroke-hair"/><text x="339" y="136" text-anchor="middle" class="label">get_tool_calls()</text><text x="339" y="149" text-anchor="middle" class="label-soft">off the final message</text><rect x="262" y="164" width="154" height="36" class="fill-surface stroke-hair"/><text x="339" y="182" text-anchor="middle" class="label">_execute_tool_calls</text><text x="339" y="195" text-anchor="middle" class="label-soft">sequential or parallel</text><line x1="430" y1="53" x2="452" y2="53" class="stroke-hair"/><path d="M460 53 L451 49 L451 57 Z" class="fill-ink"/><line x1="430" y1="101" x2="452" y2="101" class="stroke-hair"/><path d="M460 101 L451 97 L451 105 Z" class="fill-ink"/><line x1="430" y1="146" x2="452" y2="146" class="stroke-hair"/><path d="M460 146 L451 142 L451 150 Z" class="fill-ink"/><line x1="430" y1="186" x2="452" y2="186" class="stroke-hair"/><path d="M460 186 L451 182 L451 190 Z" class="fill-ink"/><rect x="460" y="34" width="210" height="38" class="fill-ground stroke-hair"/><text x="565" y="52" text-anchor="middle" class="label">message_start</text><text x="565" y="66" text-anchor="middle" class="label-soft">update, end</text><rect x="460" y="82" width="210" height="38" class="fill-ground stroke-hair"/><text x="565" y="100" text-anchor="middle" class="label">tool_execution_start</text><text x="565" y="114" text-anchor="middle" class="label-soft">update, end</text><rect x="460" y="130" width="210" height="32" class="fill-ground stroke-hair"/><text x="565" y="150" text-anchor="middle" class="label">turn_start / turn_end</text><rect x="460" y="170" width="210" height="32" class="fill-ground stroke-hair"/><text x="565" y="190" text-anchor="middle" class="label">agent_start / agent_end</text><text x="0" y="196" class="label-mark">what actually runs</text><text x="0" y="212" class="label-soft">get_tool_calls() reads DoneEvent.final,</text><text x="0" y="226" class="label-soft">never the accumulated deltas</text></svg><figcaption>The loop consumes one vocabulary and emits another, which is why a single turn has two sets of names for the same moment. Red marks the crossing that carries execution rather than display: the three delta events exist so a reader can watch a turn happen, but the tool calls that actually run are pulled off <code>DoneEvent.final</code>, whose <code>arguments</code> the provider has already assembled and parsed. Reconstructing a call from the deltas would work until the day a server fragments differently.</figcaption></figure>

A tool call is transformed four times between HTTP bytes and a rendered
widget:

1. the provider's `ToolCall` block, off `DoneEvent.final`;
2. a message dict block `{"type": "toolCall", ...}` — `model_dump()` at the
   loop boundary;
3. a backend `tool_calls_info` dict;
4. a TUI widget.

When tool calling misbehaves, trace the `arguments` value through all four
hops rather than reading any one of them.

`AgentEvent.type` is one of eighteen values: the twelve above (`agent_*`,
`turn_*`, `message_*`, `tool_execution_*`) and six τ additions —
`side_completion_start`/`_update`/`_end` (a compaction or branch summary,
which belongs to no turn; `purpose` and `reason` say which and why),
`provider_retry` (a request is being re-sent; `attempt`, `max_retries`,
`delay_seconds`), `follow_ups_dropped` (a user abort discarded queued
follow-ups and waiting `enqueue` submissions; `dropped` lists their texts),
`suspension_open`/`suspension_closed` (a turn is waiting on a responder, see
below), and `lock_changed` (this process gained or lost write access to the
tree).

τ stamps provenance on turn events — `submission_id`, `source`, `submitter`,
`correlation` — and `cursor_id`, the cursor whose turn emitted the event,
because several cursors can run turns on one session at once. It adds
`blocked` and `blocked_by` on `tool_execution_end` for extension vetoes,
`details` there for a tool's structured facts about its own execution,
`error`/`error_detail` on `agent_end` when the loop raised, and
`response_headers` on the usage-bearing `message_end`.

## The one door

`AgentSession.submit()` is the real entry point every input source funnels
through: TUI keystrokes, `tau -p`, the SDK, an extension, an RPC client.
`prompt()` builds a `Submission` and calls `submit()` — it is a wrapper, not a
second door.

`multitask_strategy` decides what happens when a submission arrives while a
turn is already running. It is a policy rather than an answer improvised per
caller:

| Strategy | Effect |
|---|---|
| `reject` | Refuse the new submission outright; `rejection_reason` explains why. |
| `enqueue` | Queue it; it runs after the current turn ends. |
| `steer` | Inject it into the running turn without waiting. |
| `rollback` | Navigate back to the pre-turn leaf and run as if from there. The running turn's output becomes an abandoned sibling branch, not a deletion. |
| `fork` | Branch the conversation instead of extending the active leaf. |

## Sessions are a tree

Append-only entries, walked by `parent_id`. Model input for a turn is an
*ephemeral frame* — system prompt, tool schemas — plus the *exact linear path*
from the root to the active leaf. There is no hidden channel on either side of
that.

That is what makes fork, branch and rollback ordinary operations rather than
special cases, and it is why a rollback leaves the abandoned branch on disk
instead of deleting it.

A store keeps entries and nothing else. The position a new entry is parented
at belongs to a `Cursor`, and every writer holds one: a head, `tau -p`, an RPC
client and a sub-agent are all cursors on the same tree, none privileged.
Moving a cursor writes nothing, and a cursor is not durable.

| Piece | Role |
|---|---|
| `SessionLog` (Protocol) | The storage contract, four members: `id`, `entries()`, `async append_at(parent_id, entry_type, payload)` and `async finalize(entry_id, payload)`. |
| `Cursor` | A position in one tree and the only thing that appends at it. It holds the typed appenders (`append_message`, `append_custom_message`, `append_custom_entry`, `append_config`, `append_compaction`, `append_elide`, `append_branch_summary`), `move()`, and the turn state: abort signal, steer, follow-up and enqueue queues. One turn runs at a time on a cursor, any number across cursors. |
| `ConversationTree` | Walks `parent_id` chains to build model input. |
| `SessionCatalog` | Lists and resolves sessions. File-backed or JMFTS-backed, chosen by `--store file\|jmfts` or the config's `session_store.backend`. |

`BranchView`, `open_branch()` and `append_navigate` are gone. A sub-agent is a
cursor opened with a `TurnFrame` (the tool subset, model, reasoning level,
prompt and `max_turns` it runs under) rather than a second session. Config
(model, reasoning, tools) is recorded in the tree as `config` entries, so a
reopened session continues as it was.

Where a reopened tree continues is `default_leaf`: the newest finished entry a
person's turn wrote. Entries a sub-agent wrote (`source: "agent"`), incomplete
entries and side entries are passed over, so a session a child wrote last
reopens in the main conversation.

Two entry mechanisms are new in 0.15:

* **Incomplete entries.** An entry is opened with `status: "incomplete"` and
  later `finalize`d, keeping its id and position. A session interrupted
  mid-message reopens at the entry before it, and the interrupted branch stays
  beside the retry.
* **Side entries.** An entry of a kind in `SIDE_KINDS` (today only
  `suspension`) hangs beside its parent. It is never an ancestor of a later
  entry, so it is no branch, tip or leaf; `is_side_entry` is how a walker asks.

An `annotate` extension hook returns JSON for each message entry the loop
writes, and τ stores it at `ext[<extension name>]` on that entry, in the same
write. A failing `annotate` handler does not lose the entry: the entry is written
with the failure recorded in place of the annotation, and the turn is aborted.

`tau_agent_core.testing` ships contract suites for both `SessionCatalog` and
`SessionLog` (`SessionCatalogContractTests`, `SessionLogContractTests`). A new
store costs about twenty lines of knobs to run them. `SessionLog` contract:
several cursors may append concurrently within one process, and the store
keeps each write whole with a distinct id.

**One writer per stored session.** A process that hosts a session for writing
holds an exclusive `flock` on a `.lock` sidecar file beside it. Another process
opening the same session gets a read-only replica whose writes raise
`SessionReadOnlyError`, naming the holder; `lock_changed` reports the change.
On a filesystem where `flock` excludes nothing, the session opens for writing
with a warning, which `sessions.allow_unlocked_fs` silences.

!!! warning "Release note for `SessionLog` implementors"
    The `branchOf` lane tag is gone. It recorded *who wrote an entry*, while
    three of its four consumers wanted *does this entry belong to the
    conversation being looked at* — which is ancestry from the cursor. The two
    agree for a sub-agent and disagree for a fork, so a three-way fork returned
    three mutually exclusive alternatives as one conversation, and a
    two-message session counted four messages.

    `Session.messages` and session listing walk the cursor's ancestry.
    `subtree_text` is bounded by descendants of the node the caller named
    rather than by write provenance. In the contract suite, one test is
    inverted rather than deleted: a store must not reintroduce a cursor
    filter.

## SDK entry point

```python
def create_agent_session(
    model: str | Model | None = None, provider: str | None = None,
    base_url: str | None = None, api_key: str | None = None,
    tools: list[str] | None = None, session_log: SessionLog | None = None,
    extensions: list[Callable] | None = None, system_prompt: str | None = None,
    no_context_files: bool = False,
    thinking_level: str | None = None, cwd: str | None = None,
    tool_execution_mode: Literal["sequential", "parallel"] = "parallel",
    compaction_policy: CompactionPolicy | None = None,
    compaction_settings: CompactionSettings | None = None,
    model_resolver: Callable[[str], Model] | None = None,
    bus_available: bool = False,
    no_tools: Literal["all", "builtin"] | None = None,
    max_turns: int | None = None,
    tool_options: dict[str, dict[str, Any]] | None = None,
    prompt_template_paths=(), no_prompt_templates: bool = False,
    skill_paths=(), no_skills: bool = False,
) -> AgentSession
```

`model=None` is the built-in default, `gpt-4o`. A model id that is not built in
needs `provider`. `thinking_level=None` sends no reasoning control, `"off"`
sends the provider's off form, and any other level marks the model
reasoning-capable. `compaction_settings` and `compaction_policy` are mutually
exclusive. The template and skill parameters are described under
[prompt templates and skills](#prompt-templates-and-skills).

`tools` takes built-in name strings only — `read`, `write`, `edit`, `bash`,
`grep`, `find`, `ls`. A custom `AgentTool` instance needs the `AgentSession`
constructor directly.

There is deliberately **no** `settings=` parameter. An earlier version had one
that was silently ignored, so it was removed rather than kept as a no-op;
passing it raises `TypeError`.

`no_tools` is the SDK half of the CLI's two flags. `"all"` offers the model
nothing at all; `"builtin"` drops the built-in set and keeps whatever
extensions registered. Passing a non-empty `tools=` together with `no_tools=`
**raises** `ValueError` — they ask for opposite things, and neither outranks the
other at a call site. `tools=None` and `tools=[]` stay legal alongside `"all"`,
which also withholds extension-registered tools. An unknown tool name raises
`ValueError` too.

This factory is not on the live TUI or headless path: `tau_coding_agent`'s
backend constructs `AgentSession` directly. What used to follow from that no
longer does — the backend now calls the same prompt builder, so τ's base
prompt and its context files reach the model on every path.

## Project context files

The system prompt is τ's base prompt, then any discovered context files, then
the tool list. `system_prompt` replaces the base text and **nothing else**;
setting it does not switch context files off.

Discovery takes the agent directory's file first (τ home by default), then walks every ancestor of
the working directory, root-most first so the nearest file is read last. At
most one file per directory, deduplicated by resolved path, first match
winning among:

```
AGENTS.override.md   AGENTS.md   AGENTS.MD   CLAUDE.md   CLAUDE.MD
```

τ's own `.tau/SYSTEM.md` is read from the working directory only and appended
last. It is deliberately *not* in that tuple: inside it, it would compete with
a sibling `AGENTS.md` under the one-file-per-directory rule, so a project
carrying both — which τ has always read both of — would silently lose one.

A worktree nested inside its own main repository suppresses the main
repository's same-named file, so the walk does not load both.

Three departures from pi, each because Fail Early asks for it:

* A file that is **found and cannot be read raises**, naming the path and the
  escape hatch. pi warns to stderr and continues. A prompt silently missing
  its project instructions looks exactly like a model ignoring them.
* Decoding is strict. Replacing undecodable bytes turns a mis-encoded
  instruction file into replacement characters the model still reads as
  instructions.
* Every block is wrapped in `<project_instructions path="…">`, so a prompt
  cannot carry instructions whose origin it does not state.

The walk reaches `/`, so a `CLAUDE.md` in `$HOME` is read on every run.
`--no-context-files` / `-nc` turns discovery off, and it is run-level: a
mid-session `/model` switch cannot hand the files back.

## Compaction

LLM-backed, with no fabricated-summary fallback. A compaction error raises
(`CompactionError`) rather than silently truncating the conversation.

```python
should_compact(context_tokens, context_window, settings) -> bool
prepare_compaction(path_entries, settings) -> CompactionPreparation | None
async def compact(preparation, model, api_key, *, custom_instructions=None,
                  thinking_level=None, on_text_delta=None) -> CompactionResult
```

`CompactionSettings` defaults: `auto=True`, `reserve_tokens=16384`,
`keep_recent_tokens=20000`, `soft_limit_ratio=0.8`, and `hard_limit_tokens` /
`soft_limit_tokens` unset (derived). Auto-compaction is **on by default**; `auto`
was formerly called `enabled`. The hard limit is `context_window -
reserve_tokens`, and the soft limit sits at `soft_limit_ratio` of that.
Crossing the soft limit compacts at the end of a turn. Crossing the hard limit
compacts *inside* the loop at a turn boundary, after the turn so far has been
written to the tree, so a long tool-calling turn is not lost to a refused
request. A manual `/compact` or `AgentSession.compact()` ignores `auto`.

A compaction runs outside any turn, so it is reported as `side_completion_*`
events with `reason` `manual` or `threshold`, and the tokens it spent appear on
`side_completion_end.usage`. A declared `CompactionPolicy` (`disabled`,
`local_summarizer` or `turn_cap`) is for measured runs: it makes an undeclared
compaction impossible rather than changing how τ compacts.

Applying one is tree surgery rather than truncation: the first kept entry is
re-parented onto the compaction entry, so the summary is on the path and the
compacted span is still in the tree.

## Prompt templates and skills

`create_agent_session` and the CLI load prompt templates and skills from
discovered locations plus explicit paths (`prompt_template_paths`,
`skill_paths`); `no_prompt_templates` and `no_skills` skip discovery while
explicit paths still load. See `docs/PROMPT-TEMPLATES-AND-SKILLS.md` in the τ
source for the file formats.

## Waiting for an answer

An extension can pause a turn with `api.suspend` and wait in-process for a
responder's answer (a step debugger, an approval form). The session writes a
`suspension` side entry, queues per cursor, emits `suspension_open`, and
resolves on the first valid answer or on abort, emitting `suspension_closed`
with a `close_reason` of `answered`, `aborted`, `cursor_closed` or `abandoned`.
It may be called from the `tool_call`, `entry_written`, `turn_end` and
`user_turn_end` hooks. A turn that unwinds at a suspension ends with
`end_reason` `suspended`. Nothing resumes across a process boundary yet.

## Built-in tools

`read`, `write`, `edit`, `bash`, `grep`, `find`, `ls`. Two things ride on top
as extensions rather than core tools: `background`, which gives any named tool
a model-chosen `background` option plus a `bg` tool to check, wait on or cancel
jobs, and `codemode`, a sandboxed scripting tool (providers `cpython`, `monty`,
`typescript`, which per its source is prompt-only) that runs scripts which call
other tools. `--tools` allowlists,
`--exclude-tools` denylists, `--no-builtin-tools` drops the set while keeping
extension-registered ones, and `--no-tools` offers the model nothing at all.

Extensions still load under `--no-tools`: hooks, commands, injections and
subscriptions are untouched, and only callable tools are withheld.

See [Extensions](extensions.md) for the registration surface and
[RPC](rpc.md) for driving all of this from another process.
