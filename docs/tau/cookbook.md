---
title: "Cookbook"
category: "cookbook"
status: "stub"
---

# Tau — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific Tau jobs — writing an extension, branching a session, storing state in the tree, supervising a fleet, pointing the TUI at a different backend. Each one is drawn from an example or script that ships in the source tree; the cited file is always the working version.

!!! note "Marked stub on purpose"
    The recipes below are real, drawn from extensions and scripts that ship
    in the source tree and are exercised by its own test suite — but they
    have not been organized into full step-by-step walkthroughs or checked
    against a fresh install, so this page stays `stub` until that pass
    happens.

## Give the model a new tool

Three pieces, and `api.register_tool` wants all of them in one dict. From
`examples/05_custom_tool.py`, the smallest complete version:

```python
def greet_execute(tool_call_id, params, signal, on_update, ctx):
    return {"content": [{"type": "text", "text": f"Hello, {params['name']}!"}]}

GREET_TOOL = {
    "name": "greet",
    "label": "Greet",
    "description": "Greet someone by name.",
    "parameters": {
        "type": "object",
        "properties": {"name": {"type": "string", "description": "Who to greet."}},
        "required": ["name"],
    },
    "execute": greet_execute,          # required — see below
    "execution_mode": "sequential",
}

def register(api):
    api.register_tool(GREET_TOOL)
```

The `parameters` JSON Schema is what the model reads to decide how to call
the tool, and what τ validates every call against. `execute` takes **five**
arguments and may be sync or async; τ awaits it either way. The result dict
becomes the `toolResult` message the model reads on its next turn — add
`"is_error": True` to tell it the call failed.

Two things bite here, and both did in this repo's own examples until they
were caught by a contract test. `execute` is a required key, so defining the
function and forgetting to put it in the dict raises
`ValueError: register_tool: missing required key 'execute'` at load. And
`register` is the *only* name the file-path loader looks up — a
conventionally-named `greet_tool_extension` is not a substitute, and
`tau -e` will raise `AttributeError` on a module without it.

`examples/03_dynamic_env_tool.py` is the same shape with the two things a
real tool needs: it redacts values that look like credentials, and it bounds
its own output so a large environment cannot flood the context window.

## Know which handler signature you need

τ has two event vocabularies and they take different handlers. Getting this
wrong fails at dispatch time — which for `session_shutdown` means at the very
end of a session, and for `tool_call` means in the fail-closed path, where a
raising handler blocks the tool call.

| Kind | Names | Handler | `event` is |
|---|---|---|---|
| **notify** | `all`, `agent_start`, `message_update`, `tool_execution_end`, … | `handler(event)` | an `AgentEvent` **object** — attributes |
| **hook** | `tool_call`, `tool_result`, `input`, `before_agent_start`, `turn_end`, `user_turn_end`, `session_start`, `session_shutdown`, `session_before_switch` | `handler(event, ctx)` | a plain **dict** |

`api.on(name, handler)` routes by name, so you do not choose — the name you
subscribe to decides which contract you owe. Hooks can change the run
(block a call, patch arguments, append a durable message); notify events
cannot, and their return value is ignored.

The turn-boundary pair is the other easy mistake: `turn_end` fires once per
*agent-loop* turn, so one request resolved in six tool round-trips fires it
six times. `user_turn_end` fires once per `prompt()` — once per thing the
user actually asked for. `examples/02_git_checkpoint.py` uses the latter,
because six commits for one request is not a checkpoint.

## Veto a dangerous tool call before it runs

The `tool_call` hook is the one hook that can actually block execution — a
notify-only event's return value is ignored, so subscribing to
`tool_execution_start` instead (an earlier version of this exact demo did)
prints a warning and then lets the destructive command run anyway. The real
shape, from the source tree's `examples/01_permission_gate.py`:

```python
import re

BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bchmod\s+777",
    r"\bdd\s+",
    r"\bmkfs\b",
    r">\s*/dev/(sd|vd|nvme)",
]
COMPILED_PATTERNS = [re.compile(p) for p in BLOCKED_PATTERNS]

def permission_gate_tool_call(event, ctx):
    if event["tool_name"] != "bash":
        return None
    command = str(event.get("input", {}).get("command") or "")
    for pattern in COMPILED_PATTERNS:
        if pattern.search(command):
            return {
                "block": True,
                "reason": f"Denied: matches destructive pattern {pattern.pattern!r}",
            }
    return None

def register(api):
    api.on("tool_call", permission_gate_tool_call)
```

Returning `{"block": True, "reason": ...}` from a `tool_call` handler turns
into an error tool result the model reacts to — it does not silently
swallow the call. Load it directly: `tau -e examples/01_permission_gate.py`.
The human-in-the-loop variant (`ctx.ui.confirm`-gated instead of a hard
block) is `examples/30_permission_gate.py`; a config-driven path denylist is
`examples/31_protected_paths.py`.

## Bridge a session onto a NATS bus (Tectum integration)

`nats_bus.py` (tau-006/tau-007) lets τ speak NATS directly — subscribing an
inbound subject to drive turns, and registering one tool per outbound verb
(`speak`, `journal_append`, `jmfts_write`, `delegate`, plus world verbs for a
simulation engine: `move_to`, `wait`, `note`). Its NATS client is an extra
rather than a base dependency — `pip install 'ffwf-tau-agent-core[bus]'` — and
it requires an explicit capability grant on top of that, because it declares
`TOUCHES_BUS = True`:

```python
from tau_agent_core.sdk import create_agent_session

session = create_agent_session(
    model=my_model,
    tools=[],
    system_prompt=SYSTEM_PROMPT,
    bus_available=True,   # required — a TOUCHES_BUS extension is refused without it
)

result = await session.load_extensions(
    [str(nats_bus_path)],
    discover=False,
    extensions_config={
        "nats_bus": {
            "workspace": "responder",                             # required
            "inbound_subject": "events.sensation.audio.resolved.clean",  # required
            "nats_url": "nats://127.0.0.1:4222",
            "verbs": ("speak", "journal_append"),
        }
    },
)
```

`workspace` and `inbound_subject` have no defaults on purpose — a guessed
workspace publishes to the wrong subject, and a guessed inbound subject
silently never fires. The full working version of this, including CLI args
and a real llama.cpp model config, is `scripts/tectum_responder.py` in the
source tree — read it over hand-adapting the snippet above, since it is the
one thing this extension is actually exercised end to end against.

The wire format (the `TectumEvent` envelope, subject naming, ack shapes) is
shared with Tectum's own docs — see the [Tectum + Tau integration
page](../integrations/tectum-tau.md).

## Fork a session instead of extending it

`ctx.fork(entry_id=None, mode="in_place")` branches the conversation off a
point in the tree without touching the source log — the next turn appends a
new sibling branch rather than continuing the active leaf:

```python
async def fork_handler(event, ctx):
    # Branch off the current leaf (entry_id=None), staying in the same file.
    await ctx.fork(mode="in_place")
```

`mode="export"` instead copies the whole session into a **new** file via the
file-backed store's own `fork` — useful for "try an alternative from here
without touching the session someone is actively looking at." It raises on
an in-memory (SDK) log, which cannot be exported to a file — there is no
silent degrade to an in-place fork instead.

For undoing a turn rather than branching from it, `AgentSession.submit()`'s
`multitask_strategy="rollback"` navigates back to the pre-turn leaf; the
turn that gets rolled back becomes an abandoned sibling branch, not a
deletion — nothing in a Tau session is destroyed by a rollback. In the TUI
this is `Ctrl+Z`.

## Keep state in the tree, not beside it

The obvious way to give an agent a todo list is a JSON file next to the
session. `examples/38_todo.py` does it with **no side database at all**:
every mutation the tool performs writes the new list snapshot as a durable
`customEntry` node, and a read reconstructs the list from the latest
snapshot on the **active path**. `customEntry` nodes are excluded from the
model's context *by kind*, so this costs no tokens — the model sees the
list only when the tool shows it.

The payoff is that the state inherits every property of the tree, for free:

- `Ctrl+Z` rolls back a turn — and the todo mutations from that turn vanish
  with it, because they hang off the abandoned branch.
- Fork the session and each branch carries its own divergent list.
- Reload, resume, or export the session and the list comes along, because
  there is nothing beside the session to lose.

`ext_kit/state.py` ships `TreeStore`, the generic replaying wrapper, for any
extension state that should time-travel with the conversation instead of
outliving it in a stale file.

## Ask one model for a dozen verdicts, one forward pass each

`ctx.complete()` is stateless — no tree writes, no cursor movement — so it
is safe under `asyncio.gather` at any fan-out. Combine that with
`DecodeConstraints(choices=[...])` and a classification over N candidates
becomes N concurrent calls, each pinned to a label set so tightly that on a
llama.cpp/llguidance backend a verdict costs about one forward pass:

```python
from tau_llm.constraints import DecodeConstraints

constraints = DecodeConstraints(choices=["supported", "contradicted", "unrelated"])
```

`examples/60_retrieval_review.py` is the working version: it takes real
retrieval hits and scores every one concurrently against a claim. Three
contract details matter, all enforced at construction or at the boundary:

- Exactly one of `grammar` / `json_schema` / `choices` may be set.
- A hand-written `grammar=` string must also carry `verify=` — a callable that
  checks the output actually conforms. τ will not reimplement a grammar engine
  to check a grammar it did not build, and it will not report a constraint held
  when it cannot tell. Build the grammar with `tau_llm.grammar`
  (`choice`/`fixed`/`regex`/`sequence`, each of which carries its own checker)
  and the verifier comes with it; `choices=[...]` needs nothing extra.
- If the server's output somehow escapes the declared constraint, τ raises
  `ConstraintViolation` rather than returning it — a grammar that died
  mid-generation produces fabricated data, and fabricated data is a fault, not
  a near miss.

The second and third are the same rule at two moments: a constraint nobody can
check is indistinguishable from no constraint at all.

## Supervise a fleet from inside a session

The sanctioned isolated-child invocation is:

```bash
tau -p --mode json --no-session --no-extensions
```

— fully ephemeral, unhookable, machine-readable. `examples/51_delegate_fleet.py`
builds a `/fleet` command on it: read-only children fan out over
subtasks while the parent session paints a live dashboard with
`ctx.ui.panel` — and because panel `actions` dispatch registered commands
back into the extension, the dashboard is a control surface, not a report:
you can steer a running child from the panel mid-flight.

Panels are not TUI-only. In headless `--mode json` they serialize onto the
event stream as `{"type": "extension", "kind": "panel", ...}`, so a parent
process reading a child's stream sees the child's dashboard and its declared
actions. A τ supervising τs that supervise their own children is the same
recipe applied twice; `ext_kit/spawn.py` and `ext_kit/stream.py` provide the
pool, limits, and stuck-detection so the outer layer notices when an inner
one stalls.

## Wrap a built-in tool without forking it

Extension tools resolve *after* built-ins, so registering a tool named
`bash` shadows the built-in `bash` for the model. `ext_kit/steer.py` ships
`wrap_tool` on exactly this mechanism: keep the original schema, delegate to
the original implementation, and add before/after hooks with a
short-circuit veto.

This is a different altitude than the `tool_call` hook. The hook sees every
tool call and can block or patch arguments before execution; a wrapper owns
one tool's whole call — it can rewrite the input, run the real tool,
transform the result, or answer without running it at all. Audit logs,
dry-run modes, per-directory sandboxes, and result redaction all land here,
with no changes to the harness and no fork of the tool.

## Let the outside world join the conversation

`examples/36_file_trigger.py` starts a background watcher on
`session_start`; when the watched file changes, the extension calls
`api.send_user_message(content)` and the change becomes a conversational
turn. The same shape works for anything that can wake a coroutine — a timer,
a webhook, an MQTT topic, a mailbox.

`deliver_as` picks the urgency: `"followUp"` runs after the current turn,
`"nextTurn"` parks until the next submission, and `"steer"` delivers into
the *already running* turn, after its current tool calls and before its next
model call. And provenance is unforgeable by construction: the runtime
stamps `source="extension"` and the extension's own name as `submitter`,
and neither is a parameter — the transcript can never claim a machine-made
message came from the human.

## Hand the model the scissors

`examples/23_context_surgeon.py` registers session-control tools — compact
now, fork from here, summarize that branch — built on `ctx.compact()`,
`ctx.fork()`, and `ctx.summarize_branch()` with `defer=True`. The deferral
is the recipe: a tool that restructured the context *mid-turn* would saw off
the branch the model is standing on, so the intent is recorded when the tool
runs and applied exactly once at the tail of the submission.

The result is an agent that manages its own context window as a matter of
policy — noticing via `ctx.get_context_usage()` that it is running long and
compacting itself, or forking a clean continuation when the task changes
shape — instead of waiting for a human to notice on its behalf.
`examples/39_trigger_compact.py` is the fully automatic edge-triggered
variant; `examples/40_handoff.py` is the same idea aimed forward: summarize,
fork, and hand the work to a focused successor session.

## Remove the middle without deleting anything

Compaction replaces a span with an LLM-written summary. Its blunter cousin
is **elide**: a summary-less splice anchor that simply cuts a span out of
the model's context. Nothing is erased — the span stays on disk and on the
tree, and navigation can walk back into it — but the fold skips it, so the
model no longer pays for it.

In the TUI this is the fourth mode of the `Ctrl+G` tree browser: pick "elide
a span ending here", pick the two endpoints, done. It is the honest tool for
the case where a summary would add nothing: a hundred turns of test-and-fix
noise whose only useful residue is the final green run, or a pasted log the
agent has finished mining. You chose the cut; no model invented a summary
of what was cut.

## Point the TUI at a different session backend

`--store jmfts` swaps the file-backed session store for a JMFTS-backed
one — useful when a deployment wants sessions to be searchable the same way
a JMFTS-indexed document corpus is, rather than plain files on disk:

```bash
tau --store jmfts
tau -p --store jmfts "..."
```

`ffwf-tau-jmfts` is an optional package
(`pip install 'ffwf-tau-coding-agent[jmfts]'`), loaded
lazily only when `--store jmfts` (or the equivalent config key) selects it —
never a hard dependency of the TUI or CLI. See the [Tau + JMFTS integration
page](../integrations/tau-jmfts.md) for what that buys an agent beyond
session storage.
