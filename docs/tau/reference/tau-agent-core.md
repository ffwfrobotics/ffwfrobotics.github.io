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

Distribution `ffwf-tau-agent-core`. `tau_agent_core` never imports
`tau_coding_agent`.

## The agent loop

```python
AgentLoop(
    config: AgentLoopConfig, emit=None, tools=None, model=None,
    abort_signal=None, hook_dispatcher=None, steer_queue=None,
)
```

`config`, `tools`, `model` and `abort_signal` are constructor arguments, not
fields on one shared object. `AgentLoopConfig` is deliberately small: `model`,
`system_prompt`, `tool_execution_mode`, `max_retries`, `max_turns`,
`temperature`, `api_key`, `reasoning`.

Everything an earlier design put on the config as callbacks —
`before_tool_call`, `get_steering_messages`, `transform_context` — is injected
instead. Extension hooks go through `hook_dispatcher`, gated on
`has_hook_handlers()` so a zero-extension session pays nothing for it;
mid-turn steering goes through a shared `steer_queue`.

`max_turns` defaults to 50. It is a τ-original safeguard — pi has no turn
bound at all — but it is a blunt one, and it does not notice that turns 2
through 50 are the same failure repeating.

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

Beyond the base event set, τ stamps provenance on every event —
`submission_id`, `source`, `submitter`, `correlation` — plus `blocked` and
`blocked_by` on `tool_execution_end` for extension vetoes, and `error` on
`agent_end` when the loop raised.

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

| Piece | Role |
|---|---|
| `SessionLog` (Protocol) | The minimal contract: `append_message`, `append_custom_message`, `append_custom_entry`, `append_compaction`, `append_elide`, `append_navigate`, `append_branch_summary`, `append_at`, `entries`, `cursor`. |
| `BranchView` / `open_branch()` | A lightweight view of one branch that does not disturb the parent log's cursor. |
| `ConversationTree` | Walks `parent_id` chains to build model input. |
| `SessionCatalog` | Lists and resolves sessions. File-backed or JMFTS-backed, chosen by `--store`. |

There is no method named `clone`, and none named `navigate` — the latter is
`append_navigate`, which appends a marker entry rather than mutating a cursor
in place.

`tau_agent_core.testing` ships contract suites for both `SessionCatalog` and
`SessionLog`. A new store costs about twenty lines of knobs to run them.

!!! warning "Release note for `SessionLog` implementors"
    The `branchOf` lane tag is gone. It recorded *who wrote an entry*, while
    three of its four consumers wanted *does this entry belong to the
    conversation being looked at* — which is ancestry from the cursor. The two
    agree for a sub-agent and disagree for a fork, so a three-way fork returned
    three mutually exclusive alternatives as one conversation, and a
    two-message session counted four messages.

    `Session.messages` and session listing now walk the cursor's ancestry.
    `resolve_cursor` is the last-entry rule again; the guarantee dropped on
    purpose is crash-exact resume under a second concurrent writer, which τ
    does not buy. `subtree_text` is bounded by descendants of the node the
    caller named rather than by write provenance.

    In the contract suite, one test is inverted rather than deleted: a store
    must not reintroduce a cursor filter.

## SDK entry point

```python
def create_agent_session(
    model: str | Model = "gpt-4o", provider: str = "openai",
    base_url: str | None = None, api_key: str | None = None,
    tools: list[str] | None = None, session_log: SessionLog | None = None,
    extensions: list[Callable] | None = None, system_prompt: str | None = None,
    no_context_files: bool = False,
    thinking_level: str = "off", cwd: str | None = None,
    tool_execution_mode: Literal["sequential", "parallel"] = "parallel",
    compaction_policy: CompactionPolicy | None = None,
    bus_available: bool = False,
    no_tools: Literal["all", "builtin"] | None = None,
) -> AgentSession
```

`tools` takes built-in name strings only — `read`, `write`, `edit`, `bash`,
`grep`, `find`, `ls`. A custom `AgentTool` instance needs the `AgentSession`
constructor directly.

There is deliberately **no** `settings=` parameter. An earlier version had one
that was silently ignored, so it was removed rather than kept as a no-op;
passing it raises `TypeError`.

`no_tools` is the SDK half of the CLI's two flags. `"all"` offers the model
nothing at all; `"builtin"` drops the built-in set and keeps whatever
extensions registered. Passing `tools=` and `no_tools=` together **raises** —
they ask for opposite things, and neither outranks the other at a call site.
`tools=None` and `tools=[]` stay legal alongside `"all"`, which also withholds
extension-registered tools.

This factory is not on the live TUI or headless path: `tau_coding_agent`'s
backend constructs `AgentSession` directly. What used to follow from that no
longer does — the backend now calls the same prompt builder, so τ's base
prompt and its context files reach the model on every path.

## Project context files

The system prompt is τ's base prompt, then any discovered context files, then
the tool schemas. `system_prompt` replaces the base text and **nothing else**;
setting it does not switch context files off.

Discovery takes the agent directory's file first, then walks every ancestor of
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
rather than silently truncating the conversation.

```python
should_compact(context_tokens, context_window, settings) -> bool
prepare_compaction(path_entries, settings) -> CompactionPreparation | None
async def compact(preparation, model, api_key, *,
                  custom_instructions=None, thinking_level=None) -> CompactionResult
```

Applying one is tree surgery rather than truncation: the first kept entry is
re-parented onto the compaction entry, so the summary is on the path and the
compacted span is still in the tree.

## Built-in tools

`read`, `write`, `edit`, `bash`, `grep`, `find`, `ls`. `--tools` allowlists,
`--exclude-tools` denylists, `--no-builtin-tools` drops the set while keeping
extension-registered ones, and `--no-tools` offers the model nothing at all.

Extensions still load under `--no-tools`: hooks, commands, injections and
subscriptions are untouched, and only callable tools are withheld.

See [Extensions](extensions.md) for the registration surface and
[RPC](rpc.md) for driving all of this from another process.
