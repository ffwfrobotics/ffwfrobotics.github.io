---
title: "RPC"
category: "reference"
status: "draft"
---

# RPC

<p class="axis">Cognition × Application</p>

`tau --mode rpc` speaks JSON-RPC 2.0 over stdio, newline-delimited. τ as a
process a host drives, rather than a library it imports.

Twenty-one verbs are implemented. Seven more are **formally declined**, each
with a stated reason, rather than silently absent.

## A submission answers twice

<figure class="dia"><svg viewBox="0 0 680 250" role="img" aria-labelledby="dia-rpc-t dia-rpc-d"><title id="dia-rpc-t">Two answers on acceptance, one on rejection</title><desc id="dia-rpc-d">Two panels divided by a vertical rule. The left panel is headed accepted. A host lifeline and a tau lifeline run down it. The host sends submit across to tau; tau answers back with accepted. A thicker segment of the tau lifeline below that is glossed the turn runs. Then a red arrow crosses back from tau to the host, squared off in red where it leaves the lifeline, and is marked the second answer, glossed agent underscore end, when the turn ends. The right panel is headed rejected. The host again sends submit, and tau answers once with error minus 32000, SUBMISSION underscore REJECTED. Beneath it the panel notes there is no later event, and that the error is the answer.</desc><text x="0" y="26" class="label-soft">accepted</text><text x="60" y="44" text-anchor="middle" class="label">host</text><text x="270" y="44" text-anchor="middle" class="label">tau</text><line x1="60" y1="52" x2="60" y2="206" class="stroke-soft"/><line x1="270" y1="52" x2="270" y2="206" class="stroke-soft"/><text x="165" y="68" text-anchor="middle" class="label-soft">submit</text><line x1="60" y1="76" x2="262" y2="76" class="stroke-hair"/><path d="M270 76 L261 72 L261 80 Z" class="fill-ink"/><text x="165" y="102" text-anchor="middle" class="label-soft">accepted</text><line x1="270" y1="110" x2="68" y2="110" class="stroke-hair"/><path d="M60 110 L69 106 L69 114 Z" class="fill-ink"/><line x1="270" y1="122" x2="270" y2="176" class="stroke"/><text x="282" y="152" class="label-soft">the turn runs</text><rect x="265" y="191" width="10" height="10" class="fill-red"/><line x1="265" y1="196" x2="68" y2="196" class="stroke-red"/><path d="M60 196 L69 192 L69 200 Z" class="fill-red"/><text x="0" y="226" class="label-mark">the second answer</text><text x="0" y="242" class="label-soft">agent_end, when the turn ends</text><line x1="340" y1="20" x2="340" y2="240" class="stroke-soft"/><text x="350" y="26" class="label-soft">rejected</text><text x="410" y="44" text-anchor="middle" class="label">host</text><text x="620" y="44" text-anchor="middle" class="label">tau</text><line x1="410" y1="52" x2="410" y2="130" class="stroke-soft"/><line x1="620" y1="52" x2="620" y2="130" class="stroke-soft"/><text x="515" y="68" text-anchor="middle" class="label-soft">submit</text><line x1="410" y1="76" x2="612" y2="76" class="stroke-hair"/><path d="M620 76 L611 72 L611 80 Z" class="fill-ink"/><text x="515" y="102" text-anchor="middle" class="label-soft">-32000 SUBMISSION_REJECTED</text><line x1="620" y1="110" x2="418" y2="110" class="stroke-hair"/><path d="M410 110 L419 106 L419 114 Z" class="fill-ink"/><text x="350" y="158" class="label-soft">no later event follows</text><text x="350" y="174" class="label-soft">the error is the whole answer</text></svg><figcaption>The shape a host has to code for. <code>submit</code> and <code>prompt</code> return immediately with an acceptance, and the result of the turn arrives later as a notification — red, because a host that treats the first response as the answer will sit waiting for a turn that already finished. A rejected submission inverts it: the error arrives on the response and nothing follows, so a host waiting for <code>agent_end</code> after a rejection waits forever.</figcaption></figure>

## Verbs

| Tier | Verbs |
|---|---|
| A — turn and state | `submit`* · `prompt` · `abort` · `get_state` · `get_messages` · `get_commands` · `get_tools` · `get_capabilities` · `new_session` · `fork` · `switch_session` |
| B — session management | `compact` · `set_model` · `get_models` · `set_session_name` · `get_session_name` · `get_session_stats` · `list_sessions` · `set_auto_compaction` · `get_last_assistant_text` |

<small>* `submit` is Tier C on the generated table; it is grouped with the
turn verbs here because that is what a host uses it for.</small>

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
| `cycle_thinking_level` | The same judgment, and τ has no `thinkingLevel` on `AgentSession` for a `set_*` verb to act on. |
| `set_steering_mode` | `multitask_strategy` is already a per-submission parameter on `submit` and `prompt`, not a session-wide mode to toggle. |
| `set_follow_up_mode` | The same — `multitask_strategy="enqueue"` covers it per call. |
| `export_html` | Rendering is the host's job. τ hands back `get_messages` and events. |

Two of these share one principle worth stating plainly: **a second privileged
path into the same executor is a second thing to secure.**

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

The reader loop is strictly serial, so `abort` stays answerable while a turn
is in flight — measured at `get_state` answering in 0.44s and `abort` in 0.46s
against a 20-second provider call.

Embedding trades that away. `abort` becomes cooperative only, and a wedged
tool or a CPU-bound stretch shares the host's event loop.

## The generated reference

`docs/RPC-PROTOCOL.md` in the source repo is the exact wire reference. It is
generated from the real command table and event schema, and a drift test
asserts the checked-in file equals its own `render()` output — so it cannot
disagree with the code that serves it.

Treat the tables above as an index into that file, not a replacement for it.
