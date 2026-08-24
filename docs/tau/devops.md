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

## Install

```bash
pip install ffwf-tau                          # the meta package: CLI, RPC, TUI
pip install ffwf-tau-coding-agent             # headless only: CLI and RPC
```

The meta package is the guessable name: it depends on
`ffwf-tau-coding-agent[tui]` at the same version and nothing else, and it
deliberately does not pull `[jmfts]`. The base distribution pulls
`ffwf-tau-agent-core` and `ffwf-tau-llm` behind it. `[tui]` adds Textual
and Rich, and that extra is the only thing an interactive `tau` needs that a
headless one does not — without it, `tau -p` and `tau --mode rpc` still run a
full turn, extensions and all. Measured: 15 packages and 13 MB against 27
packages and 31 MB. That gap is the argument for the split, because a container
that only ever runs headless turns has no reason to ship a terminal interface.

The other capabilities are extras on the same principle — `[jmfts]` for
`--store jmfts`, `ffwf-tau-agent-core[bus]` for the `nats_bus` extension. Each
reports its own absence with the install command rather than a traceback. The
[Reference](reference/index.md#packages) page carries the full table.

The `ffwf-` prefix is load-bearing rather than branding: `tau-ai` and `tau-llm`
on PyPI are unrelated third-party projects, so an install command missing the
prefix installs someone else's code.

### Which command name to write

The install puts **both** `tau` and `ffwf-tau` on PATH — one entry point, two
wrappers pip owns and removes on uninstall. Type `tau` at a terminal; write
`ffwf-tau` in a systemd unit, a Dockerfile, or a cron line. PyPI reserves
distribution names but not command names, and an unrelated project ships its
own `tau`: in an environment holding both, whichever installed last owns the
name, and nothing tells you which one that was. `ffwf-tau` cannot be taken.

## Five ways to run τ

| Mode | Entry point | Shape |
|---|---|---|
| Interactive | `tau` | Textual TUI in a terminal. |
| Headless print | `tau -p "..."` | One turn, prints a transcript, exits. |
| Headless JSON | `tau -p --mode json "..."` | One turn, JSONL lifecycle events instead of text — the machine-readable equivalent of the TUI's stream. |
| RPC subprocess | `tau --mode rpc` | A persistent JSON-RPC 2.0 server over stdio — τ as a process a host drives, not a library it imports. See the [Reference](reference/rpc.md) page for the verb table. |
| Embedded (SDK) | `create_agent_session(...)` in Python | In-process, no subprocess boundary. `tau_agent_core` never imports `tau_coding_agent`, so this path has no Textual dependency at all. |

`tau -p` and `tau --mode rpc` both write and resume **real** sessions — a
headless run shows up in the TUI's session picker and can be picked up
interactively later. There is no separate "headless-only" session format.

## Where sessions live

Default: `~/.tau/sessions` for the TUI and `tau -p`; a private
`<tmp>/.tau-<uid>/sessions` for `--mode rpc` (a subprocess a host spawns and
tears down shouldn't litter the shared directory by default).
`--session-dir DIR` overrides this for the file store. `--store {file,jmfts}`
picks the backend for the run — `ffwf-tau-jmfts` is an optional package
(`pip install 'ffwf-tau-coding-agent[jmfts]'`), loaded lazily only when
selected, never a hard dependency of the TUI or CLI.
`--no-session` skips persistence entirely (ephemeral).

Sessions are append-only JSONL, walked by `parent_id` to build model input —
not a flat chat log. That is what makes fork, branch, and rollback safe
operations rather than special cases: `AgentSession.submit()`'s
`multitask_strategy="rollback"` navigates back to the pre-turn leaf without
deleting anything (the abandoned turn becomes a sibling branch), and
`multitask_strategy="fork"` branches instead of extending the active leaf.
See the [Reference](reference/tau-agent-core.md#sessions-are-a-tree) page
for the full submission-strategy table.

## Model credentials

`~/.tau/config.json` selects the default model (out of the box, a
`local-llm` entry pointing at a local OpenAI-compatible server — vLLM,
Ollama, or llama.cpp's server). A missing API key **raises** (`No API key
for provider: …`) rather than running with a fabricated placeholder key —
there is no silent fallback to try to guess a credential.

A model entry names its vendor with `backend` and, optionally, its wire
protocol with `api`. τ registers one vendor per protocol it implements:

| `backend` | `api` it implies | Key read from |
|---|---|---|
| `openai` (the default) | `openai-completions` | `OPENAI_API_KEY` |
| `anthropic` | `anthropic-messages` | `ANTHROPIC_API_KEY` |
| `gemini` | `google-generative-ai` | `GEMINI_API_KEY`, then `GOOGLE_API_KEY` |

Resolution order for the wire is: a stated `api` wins, then the registered
vendor's own protocol, then the `openai-completions` default. A stated `api`
τ does not implement **raises** against the registry rather than falling
through to the OpenAI wire — a model silently served over the wrong protocol
is a failure that looks like a bad model rather than a bad config.

The two vendor SDKs are extras (`ffwf-tau-llm[anthropic]`,
`ffwf-tau-llm[google]`) and import on the first request rather than at module
import, so a deployment that only talks to one vendor ships only that one.

An OpenAI-compatible vendor of your own — a gateway, a hosted inference
service — needs no τ change and no extra: register a `ProviderSpec` at import
time and point a model at it. See the
[Reference](reference/tau-llm.md#two-registries-and-a-pool) page.

### Gateways that are not quite OpenAI-shaped

Two knobs cover this, both per model and both settable per call:

* `stream: false` for a gateway that does not implement SSE.
* `request_timeout` for one that is slow to first byte — it overrides the
  300s read timeout and 10s connect timeout, which are otherwise fixed at
  client construction.

A tool call arriving with **no name** — a real defect on at least one hosted
gateway, on some deployments behind it and not others — raises at the wire,
naming the call id, the model and the base URL. The fault is the gateway's,
and the raise says so instead of surfacing as a model that misbehaves.

Per-extension credentials follow the same shape: `extensions.<name>` in
`config.json`, overridable per-run with `--ext-config NAME.KEY=VALUE`
(CLI wins over config.json). An extension that needs a bearer token for a
downstream service (JMFTS, a bus) reads it from `api.config`, not from an
environment variable the model's own shell could `printenv`.

## Project context files

Discovery walks from the working directory **to `/`**, taking at most one file
per directory. On a build agent or a shared host that means a `CLAUDE.md` in
`$HOME`, or in a parent of the checkout, is read on every run. `-nc`
(`--no-context-files`) turns discovery off, and it is run-level, so a
mid-session model switch cannot hand the files back.

Two Fail-Early choices follow from τ's own rules rather than from pi's:

* A file that is found but cannot be read or decoded **raises**, naming the
  path. A prompt silently missing its project instructions is
  indistinguishable from a model ignoring them.
* Every block is wrapped in `<project_instructions path="…">`, so a prompt
  cannot carry instructions whose origin it does not state. If you are auditing
  what a run was told, the path is in the prompt.

The shipped default config carries no `system_prompt` key. Setting one
replaces τ's base text and leaves context-file discovery alone — the two are
independent, and a deployment that sets a prompt does not silently lose its
`AGENTS.md`.

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
example is `nats_bus.py` (tau-006/tau-007), which needs
`pip install 'ffwf-tau-agent-core[bus]'` for its NATS client: τ speaking NATS directly as a
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

From a checkout of the [source repo](https://github.com/jmccardle/tau), rather
than from PyPI:

```bash
python -m venv venv && source venv/bin/activate
pip install -e ./tau-llm -e './tau-agent-core[dev]' -e './tau-coding-agent[dev]' -e ./tau-jmfts

pytest                # whole suite (config lives in the repo root pyproject.toml)
mypy tau-llm/src tau-agent-core/src tau-coding-agent/src tau-jmfts/src
```

The `[dev]` extras pull the TUI, JMFTS and bus extras transitively, so a plain
editable install is not enough to run the suite. `mypy` takes all four source
trees in one call — running it against a single package in isolation reports
errors that are artefacts of the missing siblings.

A pre-commit hook (`ruff check`, `ruff format --check`, `mypy`) hard-gates
commits on the source repo — `git config core.hooksPath .githooks` to
enable it locally.

## Known gaps

- `create_agent_session` (the documented SDK entry point) is still not on the
  live TUI/headless path — `tau_coding_agent`'s backend constructs
  `AgentSession` directly. The consequence that used to matter is gone: the
  backend now calls the same prompt builder rather than copying a config key
  past it, so τ's base prompt and its context files reach the model on every
  path. What remains is that the factory's *other* defaults are exercised only
  by SDK callers.
- The per-dispatch "thinking level" toggle some deployments want (switching
  a single running model between fast/slow per request) has no first-class
  field on `AgentLoopConfig` yet; the workaround is two model config entries
  plus `set_model` over RPC, not a true per-request toggle.

See the [Reference](reference/index.md) page for exact signatures and the
[Cookbook](cookbook.md) for worked examples built from real code in the
source tree.
