---
title: "Cookbook"
category: "cookbook"
status: "stub"
---

# Tau — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific Tau jobs — writing an extension, branching a session, pointing the TUI at a different backend.

!!! note "Marked stub on purpose"
    The recipes below are real, drawn from extensions and scripts that ship
    in the source tree and are exercised by its own test suite — but they
    have not been organized into full step-by-step walkthroughs or checked
    against a fresh install, so this page stays `stub` until that pass
    happens.

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
simulation engine: `move_to`, `wait`, `note`). It requires an explicit
capability grant, because it declares `TOUCHES_BUS = True`:

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

## Point the TUI at a different session backend

`--store jmfts` swaps the file-backed session store for a `tau-jmfts`-backed
one — useful when a deployment wants sessions to be searchable the same way
a JMFTS-indexed document corpus is, rather than plain files on disk:

```bash
tau --store jmfts
tau -p --store jmfts "..."
```

`tau-jmfts` is an optional package (`pip install -e ./tau-jmfts`), loaded
lazily only when `--store jmfts` (or the equivalent config key) selects it —
never a hard dependency of the TUI or CLI. See the [Tau + JMFTS integration
page](../integrations/tau-jmfts.md) for what that buys an agent beyond
session storage.
