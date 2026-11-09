---
title: "RPC"
category: "reference"
status: "draft"
---

# RPC

<p class="axis">Cognition × Application</p>

`tau --mode rpc` speaks JSON-RPC 2.0 over stdio, newline-delimited. τ as a
process a host drives, rather than a library it imports.

Forty-five verbs are implemented. Seven more are **formally declined**, each
with a stated reason, rather than silently absent. (The count is printed in the
generated reference, `docs/RPC-PROTOCOL.md`, which is the place to cite it
from.) Eighteen event types are pushed.

Protocol version **3.1**. `protocol_version` is `MAJOR.MINOR`: MAJOR bumps when
something already on the wire breaks, MINOR when the change is purely additive.
A client must ignore any field, and any event type, it does not recognise.

`tau --mode rpc` is one of two out-of-process doors. `tau serve` is a daemon
that speaks a different protocol, with its own version, over WebSocket (JSON-RPC
2.0, one message per frame) and a `hello` handshake; 39 of its requests are
these same RPC verbs. Its error codes share one table with RPC, so `-32005`,
`-32006` and `-32007` appear below but are never sent over stdio. This page
covers the stdio protocol only.

## A submission answers twice

<figure class="dia"><svg viewBox="0 0 680 250" role="img" aria-labelledby="dia-rpc-t dia-rpc-d"><title id="dia-rpc-t">Two answers on acceptance, one on rejection</title><desc id="dia-rpc-d">Two panels divided by a vertical rule. The left panel is headed accepted. A host lifeline and a tau lifeline run down it. The host sends submit across to tau; tau answers back with accepted. A thicker segment of the tau lifeline below that is glossed the turn runs. Then a red arrow crosses back from tau to the host, squared off in red where it leaves the lifeline, and is marked the second answer, glossed agent underscore end, when the turn ends. The right panel is headed rejected. The host again sends submit, and tau answers once with error minus 32000, SUBMISSION underscore REJECTED. Beneath it the panel notes there is no later event, and that the error is the answer.</desc><text x="0" y="26" class="label-soft">accepted</text><text x="60" y="44" text-anchor="middle" class="label">host</text><text x="270" y="44" text-anchor="middle" class="label">tau</text><line x1="60" y1="52" x2="60" y2="206" class="stroke-soft"/><line x1="270" y1="52" x2="270" y2="206" class="stroke-soft"/><text x="165" y="68" text-anchor="middle" class="label-soft">submit</text><line x1="60" y1="76" x2="262" y2="76" class="stroke-hair"/><path d="M270 76 L261 72 L261 80 Z" class="fill-ink"/><text x="165" y="102" text-anchor="middle" class="label-soft">accepted</text><line x1="270" y1="110" x2="68" y2="110" class="stroke-hair"/><path d="M60 110 L69 106 L69 114 Z" class="fill-ink"/><line x1="270" y1="122" x2="270" y2="176" class="stroke"/><text x="282" y="152" class="label-soft">the turn runs</text><rect x="265" y="191" width="10" height="10" class="fill-red"/><line x1="265" y1="196" x2="68" y2="196" class="stroke-red"/><path d="M60 196 L69 192 L69 200 Z" class="fill-red"/><text x="0" y="226" class="label-mark">the second answer</text><text x="0" y="242" class="label-soft">agent_end, when the turn ends</text><line x1="340" y1="20" x2="340" y2="240" class="stroke-soft"/><text x="350" y="26" class="label-soft">rejected</text><text x="410" y="44" text-anchor="middle" class="label">host</text><text x="620" y="44" text-anchor="middle" class="label">tau</text><line x1="410" y1="52" x2="410" y2="130" class="stroke-soft"/><line x1="620" y1="52" x2="620" y2="130" class="stroke-soft"/><text x="515" y="68" text-anchor="middle" class="label-soft">submit</text><line x1="410" y1="76" x2="612" y2="76" class="stroke-hair"/><path d="M620 76 L611 72 L611 80 Z" class="fill-ink"/><text x="515" y="102" text-anchor="middle" class="label-soft">-32000 SUBMISSION_REJECTED</text><line x1="620" y1="110" x2="418" y2="110" class="stroke-hair"/><path d="M410 110 L419 106 L419 114 Z" class="fill-ink"/><text x="350" y="158" class="label-soft">no later event follows</text><text x="350" y="174" class="label-soft">the error is the whole answer</text></svg><figcaption>The shape a host has to code for. <code>submit</code> and <code>prompt</code> return immediately with an acceptance, and the result of the turn arrives later as a notification — red, because a host that treats the first response as the answer will sit waiting for a turn that already finished. A rejected submission inverts it: the error arrives on the response and nothing follows, so a host waiting for <code>agent_end</code> after a rejection waits forever.</figcaption></figure>

## Verbs

| Tier | Verbs |
|---|---|
| A — turn and state (10) | `prompt` · `abort` · `get_state` · `get_messages` · `get_commands` · `get_tools` · `get_capabilities` · `new_session` · `fork` · `switch_session` |
| B — session management (10) | `compact` · `set_model` · `get_models` · `set_session_name` · `get_session_name` · `get_session_stats` · `list_sessions` · `set_auto_compaction` · `get_last_assistant_text` · `complete_path` |
| C — the tree, the extensions, and provenance (25) | `submit` · `set_reasoning` · `navigate` · `get_tree` · `get_entry` · `elide_span` · `commit_branch` · `paste_subtree` · `summarize_and_navigate` · `complete_message_id` · `next_step` · `enumerate_domain` · `get_pending_request` · `answer_request` · `get_pending_suspensions` · `answer_suspension` · `declare_capabilities` · `enable_extension` · `disable_extension` · `reload_extension` · `list_managed_extensions` · `list_extensions` · `get_extension_state` · `get_extension_config` · `set_extension_config` |

<small>`submit` is Tier C rather than Tier A because it is τ's own verb rather
than one any harness has: it stamps `submission_id · source · submitter ·
correlation` on every event the turn produces, so a host multiplexing agents can
say which subject a prompt came from and get it back on each event.</small>

Verbs new since 0.10: `set_reasoning` names a thinking level (0.13.0, the
one path the TUI's `/thinking` and an extension's `ctx.set_reasoning` also
use); `list_extensions` lists what `tau ext list` lists, including extensions
found but not loaded (unauthorized, unusable, colliding), and authorizing one
is deliberately not a wire verb; `get_pending_suspensions`, `answer_suspension`
and `declare_capabilities` are the step-debugger verbs (0.15.0, see below).

**Call `get_capabilities` first** on a new connection, and check
`protocol_version` before sending anything mutating. It publishes the verb
list, the event schema, `declined[]`, and `limits.max_request_line_bytes`.

Give your own subprocess reader an 8 MiB line limit **before** that call —
`get_capabilities`'s own response is tens of kilobytes, well over the stdlib
`StreamReader` default of 64 KiB.

## The seven declined verbs

Each is reachable through `get_capabilities().declined[]`. Calling one returns
`-32601 METHOD_NOT_FOUND`; the published reason, not the bare error, is how a
host learns why.

| Verb | Why declined |
|---|---|
| `send_tool_result` | τ's loop executes tool calls itself. Accepting a result over RPC opens a second, unauthenticated path into the same executor that a host never drove the call for. |
| `bash` | The same reasoning. τ's bash is a tool the loop runs under a submission's provenance and admission rules; an out-of-band shell verb bypasses both. |
| `cycle_model` | A keybinding affordance, not a protocol verb. A host names a model with `set_model` rather than stepping through a list it cannot see. |
| `cycle_thinking_level` | The same judgment: a keybinding-shaped "next level". A host names the level with `set_reasoning`. |
| `set_steering_mode` | `multitask_strategy` is already a per-submission parameter on `submit` and `prompt`, not a session-wide mode to toggle. |
| `set_follow_up_mode` | The same — `multitask_strategy="enqueue"` covers it per call. |
| `export_html` | Rendering is the host's job. τ hands back `get_messages` and events. (The TUI and CLI do export HTML; this wire does not.) |

Two of these share one principle worth stating plainly: **a second privileged
path into the same executor is a second thing to secure.**

## Reading the tree

`get_tree` returns every entry in the log in the order a browser draws them —
preorder over the parent/child tree, roots in load order, children oldest first.

It is **flat**, with `parent_id` carrying the shape. A nested projection of a
five-hundred-message linear conversation is five hundred levels of nesting,
which is a serializer's recursion limit rather than a tree anyone wanted. It is
also **unbounded**: the shape is the answer, and a bounded shape is a different
tree. `count` is there so a host can say it read a whole one.

Each row is wider than the tree node it comes from, because drawing a tree and
colouring one need different facts:

| Field | What reads it |
|---|---|
| `entry_id` | every `message_id` argument — `navigate`, `elide_span`, `commit_branch`, `paste_subtree`, `summarize_and_navigate` |
| `parent_id` | the shape; null for a root |
| `role`, `preview`, `is_leaf`, `timestamp` | what a row is drawn from: the message role (null on bookkeeping kinds), the first line uncut, whether it is the head cursor's leaf, and the key children are sorted by |
| `kind` | `message`, `customMessage`, `compaction`, `elide`, `branch_summary`, `navigate`, `customEntry`, `model_change`. **Not a closed enum** — a kind added later arrives as a row a host can draw and does not recognise, rather than as a gap |
| `first_kept_id` | a fold's boundary: which entries it covers |
| `tool_call_ids` / `tool_call_id` | the call/result pairing a selection expands over |
| `copyable` | whether `paste_subtree` takes this row as a source |
| `from_id` | a branch summary and the line it is about |
| `is_system` | the prompt a fold carries across rather than dropping |
| `estimated_tokens` | a selection readout — an estimate, and says so |

The result also carries `leaf`, `count`, and `side`: session-level side
entries (a suspension opened before the first entry), which never appear as
root rows.

Nothing is filtered out. Which rows a browser declines to draw — a `navigate`
with one child, say — is the reader's rule, not the log's.

`get_entry` returns one entry's full body by id, **raw**, in its stored
camelCase shape (`parentId`, `firstKeptId`, `fromId`). `get_messages` does not
serve this: it answers for the *active path*, and the node a browser's cursor
sits on is very often not on it. The pair is what a detail pane needs — a
one-line `preview` per row from `get_tree`, and the body of the one node being
shown.

## Events

Every event is a `type: "event"` notification with a fixed record shape:
unpopulated fields are `null` or `false`, never omitted. No unbounded field is
pushed. `message_update` carries a bounded `delta` (with `block_type` and a
`replace` flag that means "reset your accumulator"), never the cumulative
message, and `agent_end` carries `message_count` and the resulting `leaf`; pull
the messages with `get_messages`. The types are the twelve loop events, the
`side_completion_*` triple, `provider_retry`, `follow_ups_dropped`,
`suspension_open`, `suspension_closed` and `lock_changed`; see
[`tau_agent_core`](tau-agent-core.md#two-event-vocabularies).

What a host should read off them:

* `agent_end.end_reason` says how a turn stopped (`done`, `terminate`,
  `aborted`, `max_turns`, `repeat_tool_calls`, `error`, `suspended`), and
  `error_detail` gives `type`, `status`, `retry_after`, `headers` and
  `retryable` for a provider failure. A `stop_reason` of `length` on
  `message_end` means the output cap cut the content off.
* `compact` answers twice, like `submit`: an immediate `{accepted,
  compaction_id}`, then a `compaction_end` notification. That notification is
  its own method, not an `event`; a host that treats every other notification as
  a violation will see `compact` never finish.
* `message_end` carries `reasoning_level` (the level actually sent, after the
  provider clamped it), `response_headers`, and `dropped_tool_calls`.

## Suspensions

An extension can pause a turn with `api.suspend` and wait for a responder. On
RPC the host is that responder only if it says so: `declare_capabilities` with
`suspensions: true`. A host that never declares gets `NoResponderError` from
every `api.suspend`, because a wait on a channel nobody sits on would hang the
turn. `suspension_open` and `suspension_closed` events carry the suspension and
its resolution; `get_pending_suspensions` is the snapshot to read after
starting; `answer_suspension` takes the first valid answer, and a later one
gets `accepted: false` rather than an error. These verbs, with `abort` and
`get_state`, run in a control lane that is served while a request is waiting on
a suspension.

## The lock a host can release

An extension can put a request in front of whoever is attached, and can lock the
session until it is answered. `get_pending_request` is the read a host makes at
every cursor move; **null is the ordinary answer and is not a failure.**

A request carries `{entry_id, extension, extension_name, sentence, label, lock,
ask, release}`. `sentence` is the extension's own line; `label` is τ's framing
of the four states over `lock` and `ask`, shipped rather than derived so a host
does not hold a second copy of that table; `ask` is a validated form spec
(`{title, fields, actions}`) or null; `release` names a command that clears the
lock.

`answer_request` appends the response and then dispatches the pressed action, in
that order, so the handler runs on a session that is already unlocked. The
append is what releases the lock — a lock is read at the cursor, and appending
moves the cursor — which is why the result carries `cursor` as the evidence the
session is answerable again.

`handled: false` is a **warning, not a failure**: the extension that raised the
request is not loaded, nothing ran, and the lock is gone anyway. A lock whose
owner cannot answer must not become a session nobody can continue.

## Where an RPC session lives

`--mode rpc` defaults its session base to a private `<tmp>/.tau-<uid>/sessions`
rather than `~/.tau/sessions`. A subprocess a host spawns and tears down should
not litter the shared directory.

The consequence is that a host and the human at the terminal are normally
looking at **different** session lists. `--session-dir DIR` is how a host joins
the user's. `list_sessions` returns `scope: {store, cwd}` precisely so a host
can tell which universe it is in, and its listing and `switch_session`'s
resolution are the same set by construction — an id this verb returns is an id
that verb accepts.

## Why a host might prefer RPC to embedding

A subprocess gives a host one property an in-process import cannot: **a real
hard kill.** `terminate()` and `kill()` against a τ child work the way they
work against any subprocess, so a runaway tool-call loop is stoppable from
outside rather than only cooperatively.

The reader loop is serial apart from a small control lane (`abort`,
`get_state`, `answer_suspension`, `get_pending_suspensions`), so `abort` stays
answerable while a turn is in flight — measured at `get_state` answering in 0.44s and `abort` in 0.46s
against a 20-second provider call.

Embedding trades that away. `abort` becomes cooperative only, and a wedged
tool or a CPU-bound stretch shares the host's event loop.

## Errors

Beyond JSON-RPC's own `-32700` to `-32603`, τ defines `-32000`
`SUBMISSION_REJECTED`, `-32001` `COMMAND_NOT_SUPPORTED`, `-32002`
`TURN_STILL_RUNNING` (a `new_session`, `fork` or `switch_session` could not stop
the in-flight turn in time; nothing was touched), `-32003` `REQUEST_TOO_LARGE`
(a request line over `limits.max_request_line_bytes`, 8 MiB; the connection
stays usable), and `-32004` `SESSION_NOT_PERSISTED` (a verb that appends was
called on a session with no durable location, as under `--no-session`).
`get_state` reports `addressable` so a host can know before it trips this.

## The generated reference

`docs/RPC-PROTOCOL.md` in the source repo is the exact wire reference. It is
generated from the real command table and event schema, and a drift test
asserts the checked-in file equals its own `render()` output — so it cannot
disagree with the code that serves it.

Treat the tables above as an index into that file, not a replacement for it.
