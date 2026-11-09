---
title: "Tau 0.16 preview: what changed from 0.15"
---

# What changed from 0.15

!!! warning "Unreleased"
    Describes 0.16.0-dev (commit `c439c401`) against the released v0.15.0. The Tau repository
    keeps a ledger, `docs/from-0.15.md`, with one row per 0.15 capability; it was written on
    2026-10-31 and some of its rows are older than the code (for example it lists `tau ext`
    and `tau serve` as missing; both now exist). Where the ledger and the current `--help`
    disagree, this page follows the code. **Built** means present at this commit and tested;
    **planned** means a document says it is coming; **dropped** is by design.

## Packaging and API

| 0.15 | 0.16 | State |
|---|---|---|
| Five distributions (`ffwf-tau`, `-llm`, `-agent-core`, `-coding-agent`, `-jmfts`), imports `tau_llm`, `tau_agent_core`, `tau_coding_agent` | One distribution `ffwf-tau`, import `tau`; Rust core `tau._core` | built |
| Python 3.11 or later, pure Python, all platforms | Python 3.12 or later, native wheels; Linux x86_64 only | built / platform wheels planned |
| `ExtensionAPI` (42 methods), lifecycle hooks | Extension objects with tools, commands, options and nine step hooks | rebuilt, no shim |
| `create_agent_session()` | `Driver`, `LocalClient`, `RemoteClient`, `start_session` | rebuilt |
| Session = JSONL file | Checksummed record log plus scratchpad per session; 0.15 files are ignored | changed, no converter |
| In-session `fork` | `branch`; `--fork` copies one walk into a new session | renamed |

## Command line

| 0.15 | 0.16 | State |
|---|---|---|
| `tau` TUI | `tau` TUI over a `Client` (cursor bar, tree, picker, themes, `/config`, `/model`) | built |
| `tau -p "msg"` (the flag took the message) | `tau -p MSG...` (a switch); exit codes 0/1/2/3/130 | built, changed |
| `--mode json` | `--json` (the wire's events) | built, changed |
| `--mode rpc` (stdio JSON-RPC, 45 verbs) | `tau serve`: JSON-RPC over WebSocket on a Unix socket; stdio is planned after 0.16.0 | changed; stdio planned |
| `--mode repl` | none | dropped (plan.md) |
| `--bus` (NATS), the `nats_bus` extension | none | not planned for 0.16 |
| `--ext-config NAME:KEY=VALUE` | `--set EXTENSION.FIELD=VALUE`, `TAU_SETTINGS`, `tau config set` | built, changed |
| `--ui-defaults` | `--answer EXTENSION[:TEXT]=VALUE` | built, changed |
| `--max-turns` | `--set step_limit.limit=N`; stopping there exits 3 | built, changed |
| `--tools`, `--no-tools`, `--exclude-tools`, `--no-builtin-tools` | none; `tau ext disable base_tools` turns the base tools off | deferred to after 0.16.0 |
| `--provider`, `--thinking` | `provider` key and provider `options` in config | dropped |
| `--prompt-template`, `--skill` and their `--no-` forms | files in `$TAU_HOME`/`.tau` `prompts/` and `skills/`; disable the `skills` extension | changed |
| `--store file\|jmfts`, import/export session | none; the JMFTS replica comes after 0.16.0 | not built |
| `--export-html` | `tau export` (Markdown) | HTML planned later |
| `--connect`, `tau serve --listen/--tail/--web-root` | attaching is automatic; `tau serve --socket` | `--tail`, web client not built |
| `tau ext list/enable/disable/authorize/revoke` | `tau ext list/enable/disable`; trust is `tau trust` | built, changed |
| (none) | `tau config check/set`, `tau trust`, `tau sessions`, `tau export`, `tau context`, `tau --version` | new |

## Behavior

| Area | 0.16 | State |
|---|---|---|
| API keys | Never discovered by default: a model names its `api_key_env` | changed (0.15 had per-vendor defaults) |
| Project config | Gated by `tau trust` with hashes of the exact files | new |
| Provider retry | Built-in `retry` wrapper, on by default (`load: {retry: false}` turns it off) | built |
| Compaction, prune | Built-in extensions (`/compact`, `/prune`, proactive trigger on `context_window`) | built |
| Permissions | Built-in `permissions` extension: `ask`, `allow`, `deny` rules; asks nothing until configured | built |
| Sub-agents | Built-in `agents` extension, off by default (`tau ext enable agents`); runs in-process as cursors | built |
| `@file`, prompt templates, skills | Built-in `attachments` and `skills`; no images; templates support `$ARGUMENTS`, `$1`..`$9` only | built, reduced |
| Usage and cost | `usage` extension (status line, `/usage`, `price`) | built |
| Steering and follow-up queues, step debugger suspensions, entry annotations | none | dropped by design |
| Image input, constrained decoding, models.dev catalog, code mode, background tools | none | not built; listed as post-0.16 candidates |
| Windows and macOS | none yet | planned (phase 9) |

## Things that still disagree

- The ledger `docs/from-0.15.md` predates the current CLI (see above) and is not regenerated.
- The Tectum integration targets 0.15's stdio RPC and `--no-tools`; neither exists in 0.16
  and both are planned only after 0.16.0 (`docs/plan.md`, "After 0.16.0").
