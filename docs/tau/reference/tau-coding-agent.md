---
title: "tau_coding_agent"
category: "reference"
status: "draft"
---

# `tau_coding_agent` — the command and the TUI

<p class="axis">Cognition × Application</p>

The `tau` command, and the Textual interface it can launch. This is the only
package that knows what a terminal is.

Distribution `ffwf-tau-coding-agent`, which needs Python 3.12 or newer. Its one
hard dependency is `ffwf-tau-agent-core`. `textual` and `rich` are the `[tui]`
extra; `rich` and `prompt_toolkit` are the separate `[repl]` extra, separate
because needing no Textual is the whole point of that head. `[serve]` adds
`websockets` for `tau serve` and `--connect`, and `[jmfts]` adds
`ffwf-tau-jmfts` for `--store jmfts`.

## One command, several destinations

<figure class="dia"><svg viewBox="0 0 680 342" role="img" aria-labelledby="dia-modes-t dia-modes-d"><title id="dia-modes-t">Where the tau command sends a run</title><desc id="dia-modes-d">The tau command feeds a box named c l i dot p y, glossed argv plus config, which branches to four boxes on the right. The branch to TauApp, the Textual TUI, leaves c l i dot p y as an ordinary line, then turns red where it is squared off, and the red segment is the last hop into TauApp; beneath that box the red mark reads c l i dot p y line 467, glossed the only import of the app. The other three branches are ordinary lines: one straight across to headless dot p y, glossed dash p and dash dash mode text or json, one down and across to r p c underscore mode dot p y, glossed dash dash mode r p c, and one further down to r e p l dot p y, glossed dash dash mode r e p l. Under c l i dot p y the figure notes one argv parser, five destinations, and that every mode writes real sessions, and that repl dot p y imports rich and prompt toolkit but never textual.</desc><rect x="0" y="130" width="110" height="40" class="fill-ground stroke"/><text x="55" y="155" text-anchor="middle" class="label">tau</text><line x1="110" y1="150" x2="142" y2="150" class="stroke"/><path d="M150 150 L141 146 L141 154 Z" class="fill-ink"/><rect x="150" y="130" width="140" height="40" class="fill-ground stroke"/><text x="220" y="148" text-anchor="middle" class="label">cli.py</text><text x="220" y="162" text-anchor="middle" class="label-soft">argv + config</text><path d="M290 142 H360 V80" class="stroke-hair fill-none"/><rect x="355" y="75" width="10" height="10" class="fill-red"/><path d="M360 75 V56 H462" class="stroke-red fill-none"/><path d="M470 56 L461 52 L461 60 Z" class="fill-red"/><rect x="470" y="34" width="200" height="44" class="fill-ground stroke"/><text x="570" y="54" text-anchor="middle" class="label">TauApp</text><text x="570" y="68" text-anchor="middle" class="label-soft">the Textual TUI</text><text x="470" y="98" class="label-mark">_launch_tui</text><text x="470" y="112" class="label-soft">the only import of the app</text><line x1="290" y1="150" x2="462" y2="150" class="stroke-hair"/><path d="M470 150 L461 146 L461 154 Z" class="fill-ink"/><rect x="470" y="128" width="200" height="44" class="fill-ground stroke"/><text x="570" y="148" text-anchor="middle" class="label">headless.py</text><text x="570" y="162" text-anchor="middle" class="label-soft">-p &#183; --mode text|json</text><path d="M290 158 H360 V228 H462" class="stroke-hair fill-none"/><path d="M470 228 L461 224 L461 232 Z" class="fill-ink"/><rect x="470" y="206" width="200" height="44" class="fill-ground stroke"/><text x="570" y="226" text-anchor="middle" class="label">rpc_mode.py</text><text x="570" y="240" text-anchor="middle" class="label-soft">--mode rpc</text><path d="M290 164 H336 V306 H462" class="stroke-hair fill-none"/><path d="M470 306 L461 302 L461 310 Z" class="fill-ink"/><rect x="470" y="284" width="200" height="44" class="fill-ground stroke"/><text x="570" y="304" text-anchor="middle" class="label">repl.py</text><text x="570" y="318" text-anchor="middle" class="label-soft">--mode repl</text><text x="0" y="196" class="label-soft">one argv parser, five destinations</text><text x="0" y="212" class="label-soft">every mode writes real sessions</text><text x="0" y="300" class="label-soft">repl.py imports rich and</text><text x="0" y="316" class="label-soft">prompt_toolkit, never textual</text></svg><figcaption>Red marks a single line of code, because that line is the reason the <code>[tui]</code> split is real rather than aspirational. The Textual app is imported inside <code>_launch_tui</code> and its <code>--connect</code> twin <code>_launch_remote_tui</code>, and nowhere else, so <code>tau -p</code>, <code>tau --mode rpc</code> and <code>tau --mode repl</code> run a full turn — extensions, tools and all — in an environment where <code>textual</code> is not installed. Move that import to the top of the file and the headless install stops working, silently, on someone else's machine.</figcaption></figure>

| Mode | Entry point | Shape |
|---|---|---|
| Interactive | `tau` | Textual TUI in a terminal. |
| Headless print | `tau -p "..."` | One turn, prints a transcript, exits. |
| Headless JSON | `tau -p --mode json "..."` | One turn, JSONL lifecycle events — the machine-readable equivalent of the TUI's stream. |
| RPC subprocess | `tau --mode rpc` | A persistent JSON-RPC 2.0 server over stdio. See [RPC](rpc.md). |
| REPL | `tau --mode repl` | An interactive prompt line in the terminal's own scrollback — no screen takeover. Behind the `[repl]` extra: `rich` renders and `prompt_toolkit` reads. |
| Remote TUI | `tau --connect ADDR` | The same TUI, driving a session on a running `tau serve` daemon instead of in this process. Needs the `[serve]` extra. |

Two subcommands are not run modes. `tau serve` is a WebSocket daemon that owns
sessions and serves them to any number of clients (`--listen HOST[:PORT]` or
`unix:/PATH`, default `127.0.0.1:8256`; `-d` to background it, logging to
`serve.log` in the τ home; `--stop`; `--tail [SESSION]`; `--web-root DIR`;
`--schema` prints the protocol's JSON Schema). Its wire is protocol 0.12. With
`"serve": {"autostart": true}` in `config.json`, a plain `tau` drives the local
daemon and starts one if nothing answers. A client has no store of its own: the
daemon builds sessions from its own `config.json`, so `--store` and friends are
refused under `--connect`. `tau ext {list,authorize,revoke,disable,enable}`
manages [extension](extensions.md) discovery and authorization without loading
anything.

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
| `--mode {text,json,rpc,repl}` | | headless output format; neither `rpc` nor `repl` combines with `--print` |
| `--model` | `-m` | config key, or `provider/id` shorthand |
| `--theme NAME` | | TUI colour theme for this run only. Built in: `mocha`, `latte`, `gruvbox`, `ansi`, plus any `<τ home>/themes/<name>.json`. Picking one from the palette saves; this flag never does |
| `--provider` | | long-only, matching pi |
| `--tools LIST` | `-t` | allowlist over built-in **and** extension tools; names are checked once extensions have loaded |
| `--no-tools` | `-nt` | offer the model **zero** tools, built-in and extension-registered alike. Extensions still load: hooks, commands, injections and subscriptions are untouched |
| `--exclude-tools LIST` | `-xt` | denylist over built-in and extension tools |
| `--no-builtin-tools` | `-nbt` | drop the built-in set; extension-registered tools survive and are still offered |
| `--extension PATH\|MODULE` | `-e` | repeatable, explicit load: a path (holds a `/` or ends in `.py`) or an installed module name. Naming it authorizes it, and it loads even under `--no-extensions` |
| `--no-extensions` | `-ne` | disable discovery of drop-ins and installed packages only |
| `--bus` | | declare this run may reach a message bus, so `TOUCHES_BUS` extensions may load. Exits 2 naming the `[bus]` extra if `nats-py` is missing |
| `--ext-config NAME:KEY=VALUE` | | repeatable per-extension override; the CLI wins over `config.json`. `VALUE` is JSON-decoded when it parses (`budget:ceiling=5.0`), else a string |
| `--ui-defaults METHOD=ANSWER,...` | | headless dialog auto-answers. `--print` and `--mode rpc` only — the TUI and `--mode repl` have a human to ask. Without it a headless dialog raises |
| `--max-turns N` | | stop after N LLM calls in one run; over `config.json`'s `max_turns` |
| `--system-prompt` / `--append-system-prompt` | | the first replaces the base prompt for this run (context files still load); the second appends and is repeatable |
| `--prompt-template PATH` / `--no-prompt-templates` | | load templates from a `.md` file or directory (repeatable), or skip discovery of `<τ home>/prompts` and `.tau/prompts` |
| `--skill PATH` / `--no-skills` | | load a skill directory, a `SKILL.md`, or a directory of skills (repeatable), or skip discovery of `<τ home>/skills` |
| `--no-context-files` | `-nc` | turn off `AGENTS.md` / `CLAUDE.md` discovery |
| `--continue` | `-c` | continue the most recent session; use with `--print` |
| `--resume` | `-r` | open the session picker at startup — the TUI and `--mode repl`. Raises under `--print`, which has no picker; name the session with `--continue` or `--session REF` there |
| `--session REF` | | resume a specific session by path or filename stem |
| `--fork REF` | | fork a session into a new one |
| `--name` | `-n` | session display title |
| `--no-session` | | ephemeral, nothing persisted |
| `--thinking {off,minimal,low,medium,high,xhigh}` | | requires a reasoning-capable model |
| `--store {file,jmfts}` | | session backend for this run |
| `--session-dir DIR` | | file store only. The default differs by mode — `<τ home>/sessions`, or a private temp directory under `--mode rpc` |
| `--import-session PATH` / `--export-session REF PATH` | | JMFTS store transfer, then exit |
| `--export-html REF [OUT ...]` | | write a saved session, every branch, as one self-contained HTML page, then exit. `REF` is a `.jsonl` path, a session id or a unique prefix; `OUT` defaults to `tau-session-<id>.html`, and `-` writes to stdout |
| `--connect ADDR` / `--cwd PATH` | | drive a session on a running `tau serve` at `HOST[:PORT]` or `unix:/PATH`; `--cwd` is the directory new sessions get, on the daemon's machine |
| `--fun` / `--no-fun` | | pick the startup tagline at random rather than always the same one |
| `--verbose` | | long-only |
| `--help` / `--version` | `-h` / `-v` | **`-v` is `--version`**, not verbose |

`--continue`, `--resume`, `--session` and `--fork` are mutually exclusive.

Tool flags are **run-level policy, not a per-model override**. They ride in
the run config rather than being written into one model entry, because a
mid-session `/model` switch to a different entry used to hand the tools back —
the denied set under `-nt`, the un-allowlisted set under `-t`.

## The τ home

`config.json`, sessions, extensions, themes and the serve log live in the τ
home. `$TAU_HOME` names it and must be an existing directory; otherwise
`<$TAU_PORTABLE_BASE>/.tau` if that directory exists, otherwise `~/.tau`. A
`.tau/` in the working directory layers on top. A set variable that names
something that is not a directory raises.

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

One writing process per session: a process hosting a session holds an
exclusive `flock` on a sidecar file, and a second process opening the same
session gets a read-only replica. Its writes raise, and the TUI shows a
`READ-ONLY` banner naming the holder.

`--resume`, `/resume` and the palette entry are one handler with three
bindings, not three implementations. `/resume <ref>` names a session directly,
using the same path / id / unique-prefix grammar as `--session`.

`SessionTreeModal` browses message, compaction, branch and navigate nodes with
a marker on the active leaf, and it **edits** the tree rather than only picking
from it. `Space` marks a row; `Ctrl+E` elides a span, `Ctrl+B` branches from
the marked messages, `c` copies a subtree and `v` pastes one; `Enter` hands the
chosen node to a follow-up action — navigate, summarise a branch, summarise
with custom instructions. `Ctrl+D` opens the detail pane. Fork is **not**
there: `/fork` is a separate command dispatched through
`AgentSession.submit()`.

The sidebar mounts **closed**. `Ctrl+B` opens it and the choice sticks.

## What the TUI is actually made of

Worth stating because an early design sketched a `widgets/` directory of ten
small files, and none of that layout exists.

`app.py` was once a single module of nearly ten thousand lines; it is now about
4,200, and the rest lives in these:

| Where | What |
|---|---|
| `app.py` | `TauApp` itself |
| `tree_browser.py` | the session-tree screens, the row and zone algebra, the elide |
| `transcript.py` | `ChatDisplay`, `MessageList`, the detail panes, lane rendering |
| `chat_widgets.py` | `MessageBox`, `ChatInput`, `ChatSidebar`, the tool-call formatters |
| `editor_widgets.py` | the editor's own bars and popups — attachments, commands, lanes |
| `modals.py` | the system-prompt, rollback and extension dialogs |
| `extension_ui.py` | the `ExtensionUI` delegate, its status bar and its panel |
| `dialogs.py` | `TauDialog` / `ChoiceDialog` / `TextDialog` — the frame, title, centering and cancel every modal inherits |
| `session_picker.py` | `SessionPickerModal`, which needs only a `SessionCatalog` and a cwd |
| `compare_view.py` | `CompareScreen`, the side-by-side columns for cursors running different models |
| `suspension_ui.py` | `SuspensionScreen`, which renders a parked [step-debugger suspension](extensions.md) and answers it |
| `tau.tcss` | every colour in the interface |

`backends.py` is the seam onto the core and is not a TUI module. Neither are
the four that make up the REPL head — `repl.py`, `repl_input.py`,
`repl_theme.py` and `steering.py` import no Textual at all, and a test asserts
`textual` never reaches `sys.modules` when `repl.py` is imported in a fresh
interpreter.

Input is a `TextArea` with history navigation. **Enter makes a newline and
`Ctrl+J` sends**, which is the reverse of most chat interfaces; `enter_key` in
`config.json` swaps the pair (`"newline"`, the default, or `"submit"`, where
Enter sends and `Shift+Enter` breaks the line). `@notes.txt` in the editor
attaches a file, and `Tab` completes — slash commands, their arguments, and
attachment paths, decided by where the cursor is. There is no `!command` bash
escape in the interface itself; `examples/37_inline_bash.py` is an extension
that adds one.

Status is the window header's subtitle: any running activity, the model name,
and one aggregate label derived from the transcript (tool-call count,
cumulative input, output, cache-read and cache-write tokens, and the current
context size as a separate number). A session open read-only shows a banner.

The palette is Textual's own, listing τ's commands from `get_system_commands`.

### On theming

Four themes ship — `mocha`, `latte`, `gruvbox`, `ansi` — and `themes.py`
resolves them. `--theme NAME` picks one for a run without saving; the command
palette picks one and does save; a `<τ home>/themes/<name>.json` file adds one.
The reason this was a file swap rather than a rewrite is where the colours
live: `tau.tcss` holds them all, and no widget names a colour in Python.


## Configuration

`<τ home>/config.json` (`~/.tau/config.json` by default) selects the default
model and holds per-extension config.
A model entry names its vendor with `backend` and, optionally, its wire
protocol with `api`:

```json
{
  "default_model": "sonnet",
  "models": {
    "sonnet": { "model": "claude-sonnet-5", "backend": "anthropic" },
    "local-llm": { "model": "…", "backend": "openai",
                   "base_url": "http://127.0.0.1:8080/v1" }
  }
}
```

Wire resolution is: a stated `api` wins, then the registered vendor's own
protocol, then the historical `openai-completions` default. So an entry that
worked before τ had more than one protocol builds the same model now.

A stated `api` τ does not implement **raises** against the registry rather
than falling through to the OpenAI wire.

A model entry that sets no `model` raises, and one whose `backend` is not a
registered vendor and that has no `base_url` raises too, rather than being sent
to OpenAI.

### Top-level keys the interface reads

There is no complete `config.json` reference; this is the set verified in the
`tau_coding_agent` source, and the packaged `tau_default_config.json` is what a
first run writes (it carries `models`, `default_model`, `theme`,
`steering_strategy`, `enter_key` and `attachment_inline_limit`).

| Key | Meaning |
|---|---|
| `models`, `default_model` | the model table and which entry a bare `tau` uses |
| `theme` | standing colour theme; `--theme` overrides it for one run |
| `enter_key` | `"newline"` (default) or `"submit"` |
| `steering_strategy` | where text typed during a turn lands: `"steer"` (default, at the running turn's next tool call) or `"enqueue"` (after the turn). Any other value raises |
| `attachment_inline_limit` | positive byte count above which only an `@file` attachment's path is sent rather than its content; default 10240 |
| `system_prompt` | replaces τ's base prompt; context-file discovery is independent of it |
| `max_turns` | stop after N LLM calls in one run; `--max-turns` wins |
| `compaction` | `auto` (bool), `reserve_tokens`, `keep_recent_tokens` (positive integers), `summarizer` (a model name). On by default; an unknown key raises `ConfigError`. A model entry's own `compaction` block replaces this one whole |
| `session_store` | `{"backend": "file" \| "jmfts", …}`; `--store` wins |
| `serve` | `listen`, `autostart`, `web_root` for `tau serve` and a plain `tau` |
| `sessions` | `allow_unlocked_fs` silences the warning for a lock-blind filesystem |
| `ui_defaults` | headless dialog auto-answers, as `--ui-defaults` |
| `extensions` | per-extension config, keyed by extension name |

See the [DevOps Manual](../devops.md#model-credentials) for credentials and
the vendor table, and [`tau_llm`](tau-llm.md) for what each field means.
