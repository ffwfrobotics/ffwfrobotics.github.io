---
title: "DevOps Manual"
category: "devops"
status: "draft"
---

# Tau — DevOps Manual

<p class="axis">Cognition × Acquisition</p>

How Tau is deployed and operated: where sessions live, how model credentials are supplied, and where the boundary between harness and agent actually falls.

!!! note "Draft"
    Written from the source repo's own README, `docs/PI-RPC-REPLACEMENT.md`,
    `docs/NATS-BUS-EXTENSION.md`, and `docs/REMOTE-CONTROL.md`. Not yet
    checked against a deployment outside the maintainer's own.

## Five ways to run τ

| Mode | Entry point | Shape |
|---|---|---|
| Interactive | `tau` | Textual TUI in a terminal. |
| Headless print | `tau -p "..."` | One turn, prints a transcript, exits. |
| Headless JSON | `tau -p --mode json "..."` | One turn, JSONL lifecycle events instead of text — the machine-readable equivalent of the TUI's stream. |
| RPC subprocess | `tau --mode rpc` | A persistent JSON-RPC 2.0 server over stdio — τ as a process a host drives, not a library it imports. See the [Reference](reference.md#rpc) page for the verb table. |
| Embedded (SDK) | `create_agent_session(...)` in Python | In-process, no subprocess boundary. `tau_agent_core` never imports `tau_coding_agent`, so this path has no Textual dependency at all. |

`tau -p` and `tau --mode rpc` both write and resume **real** sessions — a
headless run shows up in the TUI's sidebar and can be picked up
interactively later. There is no separate "headless-only" session format.

## Where sessions live

Default: `~/.tau/sessions` for the TUI and `tau -p`; a private
`<tmp>/.tau-<uid>/sessions` for `--mode rpc` (a subprocess a host spawns and
tears down shouldn't litter the shared directory by default).
`--session-dir DIR` overrides this for the file store. `--store {file,jmfts}`
picks the backend for the run — `tau-jmfts` is an optional package, loaded
lazily only when selected, never a hard dependency of the TUI or CLI.
`--no-session` skips persistence entirely (ephemeral).

Sessions are append-only JSONL, walked by `parent_id` to build model input —
not a flat chat log. That is what makes fork, branch, and rollback safe
operations rather than special cases: `AgentSession.submit()`'s
`multitask_strategy="rollback"` navigates back to the pre-turn leaf without
deleting anything (the abandoned turn becomes a sibling branch), and
`multitask_strategy="fork"` branches instead of extending the active leaf.
See the [Reference](reference.md#agent-loop-sessions-tau-agent-core) page
for the full submission-strategy table.

## Model credentials

`~/.tau/config.json` selects the default model (out of the box, a
`local-llm` entry pointing at a local OpenAI-compatible server — vLLM,
Ollama, or llama.cpp's server). A missing API key **raises** (`No API key
for provider: …`) rather than running with a fabricated placeholder key —
there is no silent fallback to try to guess a credential.

Per-extension credentials follow the same shape: `extensions.<name>` in
`config.json`, overridable per-run with `--ext-config NAME.KEY=VALUE`
(CLI wins over config.json). An extension that needs a bearer token for a
downstream service (JMFTS, a bus) reads it from `api.config`, not from an
environment variable the model's own shell could `printenv`.

## Running as a subprocess (RPC)

`--mode rpc` gives a host process the properties a plain Python import
cannot: **a real hard kill.** `terminate()`/`kill()` against a τ child works
the same way it works against any subprocess — a runaway tool-call loop is
stoppable from outside, not just cooperatively. The reader loop is strictly
serial, so `abort` stays answerable while a turn is in flight (measured:
`get_state` answered at +0.44s and `abort` at +0.46s against a 20-second
provider call in flight). Embedding τ in-process trades this away — `abort`
becomes cooperative only (`agent_loop.py` polls the abort signal per SSE
line), and a wedged tool or a CPU-bound stretch shares the host's own event
loop. Choose the RPC path over embedding whenever a runaway agent must not
be able to degrade its host.

A host driving `tau --mode rpc` should call `get_capabilities` first (it
publishes `limits.max_request_line_bytes` and the verb list) and give its
own subprocess reader an 8 MiB+ line limit before it does — `get_capabilities`'s
own response is tens of kilobytes, well over the stdlib `StreamReader`
default of 64 KiB. See `docs/PI-RPC-REPLACEMENT.md` in the source repo (a
real integration writeup, not a design doc) for the full porting notes.

## Extensions in a deployment

Extensions that touch a message bus declare `TOUCHES_BUS = True` and are
refused at load time unless the run explicitly opts in with `--bus` (CLI) or
`bus_available=True` (SDK) — a capability grant, not a default. The
declaration has a second half: such an extension must also declare a non-empty
`SUBJECTS`, naming the subjects it touches. "Leave it unset" is refused even
with `--bus` given, because the grant is per-subject rather than blanket. The shipped
example is `nats_bus.py` (tau-006/tau-007): τ speaking NATS directly as a
bus-native agent node, bridging to Tectum's effector nodes and to a
simulation engine's world verbs. See `docs/NATS-BUS-EXTENSION.md` in the
source repo for the full config surface and verb table.

Discovery is `~/.tau/extensions/` plus any explicit `-e PATH`. There is no
project-local `<cwd>/.tau/extensions/` discovery in a deployment today —
deliberately deferred pending a trust gate, not an oversight.

## Testing without a live backend

τ's own test suite sandboxes config with `monkeypatch.setattr` against
`tau_coding_agent.config.CONFIG_PATH`/`TAU_DIR` rather than relying on
environment variables alone — a test that reads the real
`~/.tau/config.json` will happily talk to whatever real backend that config
points at (a real JMFTS server, a real model endpoint), which is a slow and
non-hermetic default worth guarding against explicitly in any Tau-embedding
project's own test setup, not just Tau's.

## Dev loop

```bash
python -m venv venv && source venv/bin/activate
pip install -e ./tau-ai -e ./tau-agent-core -e ./tau-coding-agent
pip install -e ./tau-jmfts   # optional: JMFTS-backed session storage

pytest                # whole suite (config lives in the repo root pyproject.toml)
mypy tau-ai/src tau-agent-core/src tau-coding-agent/src
```

A pre-commit hook (`ruff check`, `ruff format --check`, `mypy`) hard-gates
commits on the source repo — `git config core.hooksPath .githooks` to
enable it locally.

## Known gaps

- `create_agent_session` (the documented SDK entry point) is not on the live
  TUI/headless path today — `tau_coding_agent`'s backend constructs
  `AgentSession` directly and never calls it. Real code, orphaned from the
  path that actually runs; worth knowing before assuming the SDK's own
  system-prompt-building helper is exercised in production.
- `--no-builtin-tools`/`-nbt` currently behaves identically to `--no-tools`
  — there are no extension-registered tools yet to make the distinction
  matter.
- The per-dispatch "thinking level" toggle some deployments want (switching
  a single running model between fast/slow per request) has no first-class
  field on `AgentLoopConfig` yet; the workaround is two model config entries
  plus `set_model` over RPC, not a true per-request toggle.

See the [Reference](reference.md) page for exact signatures and the
[Cookbook](cookbook.md) for worked examples built from real code in the
source tree.
