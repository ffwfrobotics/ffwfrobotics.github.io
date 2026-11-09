---
title: "Tau 0.16 preview: Operating it"
---

# Operating Tau 0.16 (preview)

!!! warning "Unreleased"
    0.16.0-dev, commit `c439c401`. Operations for the released line are in the
    [v0.15.0 DevOps Manual](../devops.md). Nothing here is packaged for deployment yet.

## Install

Only from source (see the [quickstart](quickstart.md#build-it)): Python 3.12 or later and a Rust
toolchain. The package is `ffwf-tau`, the import is `tau`, the command is `tau`. Runtime
dependencies are `httpx`, `websockets` and `textual`. The planned wheels are one `cp312-abi3`
wheel for every GIL build from 3.12 and a version-specific `cp314t` wheel for free-threaded 3.14.
Only Linux x86_64 is built or tested; the base tools use `/proc` and are Linux-only. macOS,
aarch64, Windows and the PyPI publish workflow are phase 9, not started.

## What lives where

`$TAU_HOME` (default `~/.tau`): `config.json`, `trusted.json`, `sessions/` (one directory per
session), `extensions/`, `serve/` (sockets and records of `tau serve`), `prompts/`, `skills/`,
`themes/`, and an `AGENTS.md` or `CLAUDE.md` for every session. Keep it private: Tau refuses to
approve a project while `$TAU_HOME` or `trusted.json` is writable by other users. Sessions are
not 0.15's JSONL files: they are a checksummed record log plus a scratchpad file per session,
and Tau 0.16 ignores 0.15 session files.

## Configuration layers

Nearest wins: user (`$TAU_HOME/config.json`), project (`.tau/config.json` in a trusted project),
session (`--set`, `--system-prompt`, and the `TAU_SETTINGS` JSON environment variable). Objects merge by key,
lists and scalars replace, `null` removes. Top-level keys: `models`, `default_model`,
`extensions`, `load`, `system_prompt`, `tui`. An unknown key is an error with a suggestion.
`tau config check [--show MODEL] [--clean] [--purge EXT] [--layer user|project]` validates;
`tau config set EXT.FIELD=VALUE` writes an option. API keys are never in config: `api_key_env`
names the variable, read when a sample is made. A literal `api_key` works but warns. Unlike
0.15, there is no per-vendor default environment variable: a hosted model must say which
variable holds its key.

## Project trust

A project's `.tau/` can set `base_url` (where your key is sent) and run Python, so Tau does not
use it until you run `tau trust [DIR]`, which prints the config (keys blanked), the extension
files and the names, not values, of the `.env` variables, and then pins the exact bytes of
`config.json`, `.env`, `extensions/`, `SYSTEM.md`, `prompts/` and `skills/`. Any change untrusts
the project. With no terminal (a script, `tau serve -d`) an untrusted project is refused and the
message names `tau trust`.

## Serving

`tau serve [-d] [--json] [--socket PATH] [--stop] [--schema]` runs one session on a Unix socket
(file permissions are the only authentication) speaking JSON-RPC 2.0 over WebSocket. `-d`
detaches; the record is also `$TAU_HOME/serve/<id>.json`. A session a server holds is `Leased`
to it: `tau`, `tau -p` and `tau export` attach or read; to work on a copy use `--fork`. A session
held by another process is otherwise refused. `tau serve --schema` prints the JSON Schema of the
protocol; the TypeScript clients are generated from it. This is not 0.15's `tau serve`: there is
no `--listen`, `--connect`, `--tail` or `--web-root`, and no stdio RPC mode.

## CI

The repository's CI (`.forgejo/workflows/ci.yml`) runs `scripts/check.sh`: rustfmt, clippy,
cargo tests, a maturin build, rule lints, a complexity ratchet, stubtest, ruff, pyright, pytest
(the behavior suite runs twice: local, then over a socket), and checks that the generated API
docs, the protocol guide, the wire schema and the diagrams are current and that every example in
the guides runs. The same script (`scripts/check.sh`) runs locally.

## Errors you will meet

`tau: model 'x' is not in your config` (run `tau config check`); `project is not trusted` (run
`tau trust`); `session ... is in use by another process` (fork it or attach); an extension that
fails to load stops startup and names the way past it (`tau ext disable KEY` or `--no-extensions`).
