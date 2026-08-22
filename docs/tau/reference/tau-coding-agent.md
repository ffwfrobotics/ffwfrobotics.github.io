---
title: "tau_coding_agent"
category: "reference"
status: "draft"
---

# `tau_coding_agent` — the command and the TUI

<p class="axis">Cognition × Application</p>

The `tau` command, and the Textual interface it can launch. This is the only
package that knows what a terminal is.

Distribution `ffwf-tau-coding-agent`. Its one hard dependency is
`ffwf-tau-agent-core`; `textual` and `rich` are the `[tui]` extra.

## One command, four destinations

<figure class="dia"><svg viewBox="0 0 680 264" role="img" aria-labelledby="dia-modes-t dia-modes-d"><title id="dia-modes-t">Where the tau command sends a run</title><desc id="dia-modes-d">The tau command feeds a box named c l i dot p y, glossed argv plus config, which branches to three destinations on the right. The branch to Parley, the Textual TUI, leaves c l i dot p y as an ordinary line, then turns red where it is squared off, and the red segment is the last hop into Parley; beneath that box the red mark reads c l i dot p y line 519, glossed the only import of the app. The other two branches are ordinary lines: one straight across to headless dot p y, glossed dash p and dash dash mode text or json, and one down and across to r p c underscore mode dot p y, glossed dash dash mode r p c. Under c l i dot p y the figure notes one argv parser, four destinations, and that every mode writes real sessions.</desc><rect x="0" y="130" width="110" height="40" class="fill-ground stroke"/><text x="55" y="155" text-anchor="middle" class="label">tau</text><line x1="110" y1="150" x2="142" y2="150" class="stroke"/><path d="M150 150 L141 146 L141 154 Z" class="fill-ink"/><rect x="150" y="130" width="140" height="40" class="fill-ground stroke"/><text x="220" y="148" text-anchor="middle" class="label">cli.py</text><text x="220" y="162" text-anchor="middle" class="label-soft">argv + config</text><path d="M290 142 H360 V80" class="stroke-hair fill-none"/><rect x="355" y="75" width="10" height="10" class="fill-red"/><path d="M360 75 V56 H462" class="stroke-red fill-none"/><path d="M470 56 L461 52 L461 60 Z" class="fill-red"/><rect x="470" y="34" width="200" height="44" class="fill-ground stroke"/><text x="570" y="54" text-anchor="middle" class="label">Parley</text><text x="570" y="68" text-anchor="middle" class="label-soft">the Textual TUI</text><text x="470" y="98" class="label-mark">cli.py:519</text><text x="470" y="112" class="label-soft">the only import of the app</text><line x1="290" y1="150" x2="462" y2="150" class="stroke-hair"/><path d="M470 150 L461 146 L461 154 Z" class="fill-ink"/><rect x="470" y="128" width="200" height="44" class="fill-ground stroke"/><text x="570" y="148" text-anchor="middle" class="label">headless.py</text><text x="570" y="162" text-anchor="middle" class="label-soft">-p &#183; --mode text|json</text><path d="M290 158 H360 V228 H462" class="stroke-hair fill-none"/><path d="M470 228 L461 224 L461 232 Z" class="fill-ink"/><rect x="470" y="206" width="200" height="44" class="fill-ground stroke"/><text x="570" y="226" text-anchor="middle" class="label">rpc_mode.py</text><text x="570" y="240" text-anchor="middle" class="label-soft">--mode rpc</text><text x="0" y="196" class="label-soft">one argv parser, four destinations</text><text x="0" y="212" class="label-soft">every mode writes real sessions</text></svg><figcaption>Red marks a single line of code, because that line is the reason the <code>[tui]</code> split is real rather than aspirational. The Textual app is imported inside <code>_launch_tui</code> and nowhere else, so <code>tau -p</code> and <code>tau --mode rpc</code> run a full turn — extensions, tools and all — in an environment where <code>textual</code> is not installed. Move that import to the top of the file and the headless install stops working, silently, on someone else's machine.</figcaption></figure>

| Mode | Entry point | Shape |
|---|---|---|
| Interactive | `tau` | Textual TUI in a terminal. |
| Headless print | `tau -p "..."` | One turn, prints a transcript, exits. |
| Headless JSON | `tau -p --mode json "..."` | One turn, JSONL lifecycle events — the machine-readable equivalent of the TUI's stream. |
| RPC subprocess | `tau --mode rpc` | A persistent JSON-RPC 2.0 server over stdio. See [RPC](rpc.md). |

`tau -p` and `tau --mode rpc` write and resume **real** sessions. A headless
run shows up in the TUI's picker and can be continued interactively. There is
no separate headless session format.

## CLI flags

`tau --help` is the authoritative contract. This table is a snapshot, and a
hand-maintained snapshot *will* drift — an earlier version of it carried three
outright wrong claims. Treat a disagreement as this table being stale.

| Flag | Short | Notes |
|---|---|---|
| `--print` | `-p` | run one turn headlessly, print, exit |
| `--mode {text,json,rpc}` | | headless output format; `rpc` does not combine with `--print` |
| `--model` | `-m` | config key, or `provider/id` shorthand |
| `--provider` | | long-only, matching pi |
| `--tools LIST` | `-t` | allowlist |
| `--no-tools` | `-nt` | offer the model **zero** tools, built-in and extension-registered alike. Extensions still load: hooks, commands, injections and subscriptions are untouched |
| `--exclude-tools LIST` | `-xt` | denylist, built-ins only |
| `--no-builtin-tools` | `-nbt` | drop the built-in set; extension-registered tools survive and are still offered |
| `--extension PATH` | `-e` | repeatable, explicit load. Runs even under `--no-extensions` |
| `--no-extensions` | `-ne` | disable discovery only |
| `--bus` | | declare this run may reach a message bus, so `TOUCHES_BUS` extensions may load |
| `--ext-config NAME.KEY=VALUE` | | repeatable per-extension override; the CLI wins over `config.json` |
| `--ui-defaults METHOD=ANSWER,...` | | headless dialog auto-answers. `--print` only; without it a headless dialog raises |
| `--system-prompt` / `--append-system-prompt` | | the latter is repeatable |
| `--no-context-files` | `-nc` | turn off `AGENTS.md` / `CLAUDE.md` discovery |
| `--continue` | `-c` | continue the most recent session; use with `--print` |
| `--resume` | `-r` | open the session picker at TUI startup. Raises under `--print`, which has no screen to open one on |
| `--session REF` | | resume a specific session by path or filename stem |
| `--fork REF` | | fork a session into a new one |
| `--name` | `-n` | session display title |
| `--no-session` | | ephemeral, nothing persisted |
| `--thinking {off,minimal,low,medium,high,xhigh}` | | requires a reasoning-capable model |
| `--store {file,jmfts}` | | session backend for this run |
| `--session-dir DIR` | | file store only. The default differs by mode — `~/.tau/sessions`, or a private temp directory under `--mode rpc` |
| `--import-session PATH` / `--export-session REF PATH` | | JMFTS store transfer, then exit |
| `--fun` / `--no-fun` | | pick the startup tagline at random rather than always the same one |
| `--verbose` | | long-only |
| `--help` / `--version` | `-h` / `-v` | **`-v` is `--version`**, not verbose |

`--continue`, `--resume`, `--session` and `--fork` are mutually exclusive.

Tool flags are **run-level policy, not a per-model override**. They ride in
the run config rather than being written into one model entry, because a
mid-session `/model` switch to a different entry used to hand the tools back —
the denied set under `-nt`, the un-allowlisted set under `-t`.

## Sessions from the interface

Two things that sound alike and are not:

| | Picks | Opened by |
|---|---|---|
| `SessionPickerModal` | **which session** to open | `--resume`, `/resume`, the command palette |
| `SessionTreeModal` | a point **inside the current conversation** | `Ctrl+G` |

The picker filters fuzzily over name and first and last message, `Tab` widens
the scope from this directory to all, and a path is elided at the **front** —
`/home/john/Devel…` says only that it is under Development, which every row
already said, while the last component names the project.

`--resume`, `/resume` and the palette entry are one handler with three
bindings, not three implementations. `/resume <ref>` names a session directly,
using the same path / id / unique-prefix grammar as `--session`.

`SessionTreeModal` browses message, compaction, branch and navigate nodes with
a marker on the active leaf, and hands the chosen node to a follow-up action:
navigate, summarise a branch, summarise with custom instructions, or elide a
span. Fork is **not** there — `/fork` is a separate command dispatched through
`AgentSession.submit()`.

The sidebar mounts **closed**. `Ctrl+B` opens it and the choice sticks.

## What the TUI is actually made of

Worth stating because an early design sketched a `widgets/` directory of ten
small files, and none of that layout exists.

| Where | What |
|---|---|
| `chat_widgets.py` | `MarkdownLineFormatter`, `ReasoningRegion`, `ToolBox`, `ExchangeBox` |
| `app.py` | the `Parley` app plus its widgets and modals — `ChatSidebar`, `MessageList`, `MessageBox`, `ExtensionStatusBar`, `LaneStrip`, `ExtensionPanel`, `SessionTreeModal` and the extension dialogs |
| `session_picker.py` | `SessionPickerModal`, which needs only a `SessionCatalog` and a cwd |
| `parley.tcss` | every colour in the interface |

Input is a plain `TextArea` with history navigation and `Ctrl+Enter` to
submit. There is no `@` file reference, no `!command` bash escape and no tab
completion for paths — none of those were built.

Status is the window header's subtitle: the model name plus one aggregate
label. There is no context-window percentage and no session-name indicator
anywhere.

The palette is Textual's own, listing τ's commands from `get_system_commands`.

### On theming

The palette is Catppuccin Mocha, as real hardcoded values in `parley.tcss`.
It is **not** a swappable theme system — there is no `themes/` directory and
no second theme in the source. Because every colour lives in the one
stylesheet rather than in per-widget code, changing it is a file swap; that is
a property of where the colours are kept, not a feature that exists yet.

Streaming is throttled to 30 Hz, carried over from Parley and still the right
answer for not thrashing a terminal on token-by-token deltas.

## Configuration

`~/.tau/config.json` selects the default model and holds per-extension config.
A model entry names its vendor with `backend` and, optionally, its wire
protocol with `api`:

```json
{
  "default_model": "sonnet",
  "models": {
    "sonnet": { "model": "claude-sonnet-5", "backend": "anthropic" },
    "local-llm": { "model": "…", "backend": "local",
                   "base_url": "http://127.0.0.1:8080/v1" }
  }
}
```

Wire resolution is: a stated `api` wins, then the registered vendor's own
protocol, then the historical `openai-completions` default. So an entry that
worked before τ had more than one protocol builds the same model now.

A stated `api` τ does not implement **raises** against the registry rather
than falling through to the OpenAI wire.

See the [DevOps Manual](../devops.md#model-credentials) for credentials and
the vendor table, and [`tau_llm`](tau-llm.md) for what each field means.
