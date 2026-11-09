---
title: "DevOps Manual"
category: "devops"
status: "draft"
---

# Tau — DevOps Manual

<p class="axis">Cognition × Acquisition</p>

How Tau is deployed and operated: where sessions live, how model credentials are supplied, and where the boundary between harness and agent actually falls.

!!! note "Draft"
    Written from the source repo's own README and design docs, and checked
    against the v0.15.0 source and a v0.15.0 install. Not yet checked against a
    deployment outside the maintainer's own.

## Install

```bash
pip install ffwf-tau                          # the meta package: CLI, RPC, TUI, all three wires
pip install ffwf-tau-coding-agent             # headless only: CLI and RPC
```

Python 3.12 or newer is required. 0.15.0 dropped 3.11; the release matrix runs
3.12, 3.13, 3.14 and the free-threaded 3.14t and 3.15t builds, and the project
gates on no module re-enabling the GIL. All five distributions are on PyPI at 0.15.0.

The meta package is the guessable name and ships no code. It depends, all at
the same version, on `ffwf-tau-coding-agent[tui]`,
`ffwf-tau-agent-core[images]` and `ffwf-tau-llm[anthropic,google]`, so a bare
`ffwf-tau` speaks all three wire protocols and reads screenshots. It
deliberately does not pull `[jmfts]` (that store needs a running server) or the
daemon (`ffwf-tau[serve]` adds that). The base distribution pulls
`ffwf-tau-agent-core` and `ffwf-tau-llm` behind it. `[tui]` adds Textual
and Rich, and that extra is the only thing an interactive `tau` needs that a
headless one does not — without it, `tau -p` and `tau --mode rpc` still run a
full turn, extensions and all. Measured: 15 packages and 13 MB against 27
packages and 31 MB. That gap is the argument for the split, because a container
that only ever runs headless turns has no reason to ship a terminal interface.

The other capabilities are extras on the same principle — `[repl]` for
`--mode repl`, `[jmfts]` for `--store jmfts`, `[serve]` for `tau serve` and
`--connect`, `ffwf-tau-agent-core[bus]` for the `nats_bus` extension. Each
reports its own absence with the install command rather than a traceback. The
[Reference](reference/index.md#packages) page carries the full table.

The `ffwf-` prefix is load-bearing rather than branding: `tau-ai` and `tau`
on PyPI are unrelated third-party projects, so an install command missing the
prefix installs someone else's code.

### Which command name to write

The install puts **both** `tau` and `ffwf-tau` on PATH — one entry point, two
wrappers pip owns and removes on uninstall. Type `tau` at a terminal; write
`ffwf-tau` in a systemd unit, a Dockerfile, or a cron line. PyPI reserves
distribution names but not command names, and an unrelated project ships its
own `tau`: in an environment holding both, whichever installed last owns the
name, and nothing tells you which one that was. `ffwf-tau` cannot be taken.

## Ways to run τ

| Mode | Entry point | Shape |
|---|---|---|
| Interactive | `tau` | Textual TUI in a terminal. |
| Headless print | `tau -p "..."` | One turn, prints a transcript, exits. |
| Headless JSON | `tau -p --mode json "..."` | One turn, JSONL lifecycle events instead of text — the machine-readable equivalent of the TUI's stream. |
| RPC subprocess | `tau --mode rpc` | A persistent JSON-RPC 2.0 server over stdio — τ as a process a host drives, not a library it imports. See the [Reference](reference/rpc.md) page for the verb table. |
| REPL | `tau --mode repl` | An interactive prompt line in the terminal's own scrollback, no screen takeover. Behind the `[repl]` extra (`rich` renders, `prompt_toolkit` reads); needs no Textual. |
| Daemon | `tau serve` | A WebSocket server that owns sessions (default `127.0.0.1:8256`, or `unix:/PATH`); `-d` backgrounds it, `--stop` stops it, `--tail` prints a session's events. Needs the `[serve]` extra. |
| Remote TUI | `tau --connect ADDR` | The TUI driving a session on a running daemon. The daemon builds sessions from its own `config.json`, so a client carries no store, keys or extension flags. |
| Embedded (SDK) | `create_agent_session(...)` in Python | In-process, no subprocess boundary. `tau_agent_core` never imports `tau_coding_agent`, so this path has no Textual dependency at all. |

`tau -p` and `tau --mode rpc` both write and resume **real** sessions — a
headless run shows up in the TUI's session picker and can be picked up
interactively later. There is no separate "headless-only" session format.

## Where sessions live

Default: `<τ home>/sessions` for the TUI and `tau -p`, where the τ home is
`$TAU_HOME` (which must exist), else `<$TAU_PORTABLE_BASE>/.tau` if that
directory exists, else `~/.tau`; a private
`<tmp>/.tau-<uid>/sessions` for `--mode rpc` (a subprocess a host spawns and
tears down shouldn't litter the shared directory by default).
`--session-dir DIR` overrides this for the file store. `--store {file,jmfts}`
picks the backend for the run — `ffwf-tau-jmfts` is an optional package
(`pip install 'ffwf-tau-coding-agent[jmfts]'`), loaded lazily only when
selected, never a hard dependency of the TUI or CLI.
`--no-session` skips persistence entirely (ephemeral).

A stored session has **one writing process**. Whatever hosts it takes an
exclusive `flock` on a sidecar file and holds it until the last cursor on that
session closes; a second process opening the same session gets a read-only
replica whose writes raise, naming the holder. On a filesystem where `flock`
excludes nothing (some NFS mounts) the session still opens for writing with a
warning, which `"sessions": {"allow_unlocked_fs": true}` silences. Running a
daemon (`tau serve`) is how several heads share one writer.

Sessions are append-only JSONL, walked by `parent_id` to build model input —
not a flat chat log. That is what makes fork, branch, and rollback safe
operations rather than special cases: `AgentSession.submit()`'s
`multitask_strategy="rollback"` navigates back to the pre-turn leaf without
deleting anything (the abandoned turn becomes a sibling branch), and
`multitask_strategy="fork"` branches instead of extending the active leaf.
See the [Reference](reference/tau-agent-core.md#sessions-are-a-tree) page
for the full submission-strategy table.

`tau --export-html REF [OUT]` writes a saved session, every branch of it, as one
self-contained HTML page: no script, a content-security policy that forbids
fetches, and images inlined as `data:` URIs.

## Model credentials

`~/.tau/config.json` selects the default model (out of the box, a
`local-llm` entry pointing at a local OpenAI-compatible server — vLLM,
Ollama, or llama.cpp's server). τ never invents a
credential. An environment key reaches **only its own vendor's endpoint**: a
vendor's variable is not sent to a gateway on another host. The Anthropic and
OpenAI wires send a request with no key and leave the refusal to the endpoint,
whose 401 says which variable to set; the Google wire cannot, and raises
(`No API key for provider …`). A 401 after
a key was sent says where the key came from, and `agent_end` carries
`key_sent` so a host can tell "no key" from "key refused".

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

### Retry, compaction and output caps

Defaults that changed since 0.10 and that an operator meets:

* **Provider retry is on.** A request that failed before yielding anything is
  re-sent up to 3 times (about 1, 2 and 4 s, honouring `Retry-After` up to 60 s)
  on 408, 429, 502, 503, 504 and 529 and on a refused or reset connection. A
  failure after any output reached the caller is never retried.
* **Compaction is on** in every head unless `config.json` says
  `"compaction": {"auto": false}`.
* **Output cap**: a model entry that sets no `max_tokens` gets 32768. A
  completion cut off at the cap runs none of its tool calls and ends the turn.
* **`--thinking off` means off.** It sends the wire's off form, or raises; an
  OpenAI-compatible model that cannot switch thinking off needs a
  `thinking_level_map` entry.

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
`config.json`, overridable per-run with `--ext-config NAME:KEY=VALUE`
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
becomes cooperative only (each provider races its pending read against the
abort signal, but a tool that never yields is not interrupted), and a wedged tool or a CPU-bound stretch shares the host's own event
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

Extensions come from three places: drop-ins in `<τ home>/extensions/`,
installed Python packages that declare a `tau.extensions` entry point, and
anything named with `-e PATH` or `-e MODULE`. Finding one does not load it:
a discovered extension loads only once it is authorized (recorded in
`extension-authorizations.json` beside the extensions directory), while an
extension named on the command line is authorized by being named, so a headless
host needs no approval step. `tau ext list` shows what is found and whether it
would load without importing anything; `tau ext authorize`, `revoke`, `disable`
and `enable` manage the records. An explicitly named extension whose setup
raises fails startup. There is no project-local `<cwd>/.tau/extensions/`
discovery — deliberately deferred pending a trust gate, not an oversight.

## Testing without a live backend

τ's own test suite points `$TAU_HOME` at a temporary directory (see
`tau_coding_agent.testing`, which needs the `[tui]` extra, and
`tau_agent_core.testing`) — a test that reads the real
`~/.tau/config.json` will happily talk to whatever real backend that config
points at (a real JMFTS server, a real model endpoint), which is a slow and
non-hermetic default worth guarding against explicitly in any Tau-embedding
project's own test setup, not just Tau's.

## Dev loop

From a checkout of the [source repo](https://github.com/jmccardle/tau), rather
than from PyPI:

```bash
python -m venv venv && source venv/bin/activate
pip install -e ./tau-llm -e './tau-agent-core[dev]' -e './tau-coding-agent[dev]' -e ./tau-jmfts   # Python 3.12+

pytest                # whole suite (config lives in the repo root pyproject.toml)
mypy tau-llm/src tau-agent-core/src tau-coding-agent/src tau-jmfts/src
```

The `[dev]` extras pull the TUI, REPL, serve, JMFTS, bus, images and code-mode extras transitively, so a plain
editable install is not enough to run the suite. `mypy` takes all four source
trees in one call — running it against a single package in isolation reports
errors that are artefacts of the missing siblings.

A pre-commit hook hard-gates commits on the source repo over all five `src`
trees — `ruff check`, `ruff format --check`, `mypy`, and a check that no
multi-line comment block was added. `git config core.hooksPath .githooks`
enables it locally; it requires the in-repo venv rather than falling back to a
PATH `ruff` or `mypy`, because a different tool version passing locally and
failing elsewhere is the failure the gate exists to prevent.

## Known gaps

- `create_agent_session` (the documented SDK entry point) is still not on the
  live TUI/headless path — `tau_coding_agent`'s backend constructs
  `AgentSession` directly. The consequence that used to matter is gone: the
  backend now calls the same prompt builder rather than copying a config key
  past it, so τ's base prompt and its context files reach the model on every
  path. What remains is that the factory's *other* defaults are exercised only
  by SDK callers.
- The reasoning level is no longer fixed per loop: `AgentLoop` re-reads model,
  key, reasoning and temperature before every request, and `set_reasoning`
  (RPC, `/thinking` in the TUI and REPL, `ctx.set_reasoning` in an extension)
  changes it mid-session. There is still no way back to "provider default" once
  a session has set a level.
- There is no trust gate for project-local content: project prompt templates
  load unguarded and project skills are held back until one exists.

See the [Reference](reference/index.md) page for exact signatures and the
[Cookbook](cookbook.md) for worked examples built from real code in the
source tree.
