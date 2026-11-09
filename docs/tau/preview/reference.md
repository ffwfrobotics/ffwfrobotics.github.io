---
title: "Tau 0.16 preview: Reference"
---

# Reference (0.16 preview)

!!! warning "Unreleased"
    0.16.0-dev, commit `c439c401`. The released reference is [Tau v0.15.0 Reference](../reference/index.md).

## The `tau` command line

Checked against `tau --help` and each subcommand's `--help` at this commit.

```text
tau [options] [MESSAGE ...]          open the terminal UI; with -p send MESSAGE, print the answer, exit
tau COMMAND ...                      config | ext | sessions | export | context | serve | trust
```

The first argument decides: a subcommand's name runs it, anything else is the launch command
line (`tau -p sessions` sends the word "sessions").

| Flag | Meaning |
|---|---|
| `-p`, `--print` | send MESSAGE (stdin after a blank line if not a terminal), print the answer; exit 0 done, 1 failed, 2 usage, 3 stopped before finishing, 130 interrupted |
| `-m`, `--model NAME` | model of a new session (default: `default_model`) |
| `--json` | print the session's events, one JSON object per line |
| `--answer EXTENSION[:TEXT]=VALUE` | answer questions extensions ask (repeatable; first match wins; no match declines) |
| `--theme NAME` | terminal UI theme for this run (not with `-p`) |
| `-c`, `--continue` | open the newest session of this directory |
| `-r`, `--resume` | choose a session to open (not with `-p`) |
| `--session REF` | open a session: path, id, name or id prefix |
| `--fork REF[:NODE]` | start a new session as a copy of one walk of REF |
| `--no-session` | keep the session in memory |
| `-n`, `--name NAME` | name the session |
| `--session-dir DIR` | keep and find sessions in DIR (default `$TAU_HOME/sessions`) |
| `--system-prompt TEXT`, `--append-system-prompt TEXT`, `-nc`/`--no-context-files` | system prompt controls (an error with `-c`, `-r`, `--session`, `--fork`, except `-nc`) |
| `-e`, `--extension PATH\|KEY` | load this extension even if off (repeatable) |
| `--no-extensions` | skip packages and drop-ins; the built-ins still follow `load` |
| `--set EXTENSION.FIELD=VALUE` | extension option for this run (repeatable); `load.KEY=true\|false` too |
| `--verbose` | report the start, and under `-p` each node, on standard error |
| `-v`, `--version` | print the version and the protocol |

Subcommands: `tau config check [--show MODEL] [--clean] [--purge EXT] [--layer user|project]`,
`tau config set EXT.FIELD=VALUE...`, `tau ext list [-e] [--no-extensions] [--json]`,
`tau ext enable KEY`, `tau ext disable KEY`, `tau sessions [--all] [--json]`,
`tau sessions name REF [NAME]`, `tau export REF [-o FILE] [--thinking]`,
`tau context [--show] [prompt flags]`, `tau trust [DIR]`,
`tau serve [session and extension flags] [--socket PATH] [-d | --stop | --schema] [--json]`.
There is no `--mode`, `--store`, `--provider`, `--thinking`, `--tools` family, `--bus` or
`--connect`; see [what changed](differences.md).

## Environment

`TAU_HOME` (state directory), `TAU_SETTINGS` (JSON session settings with `load` and
`extensions`), and whatever variables your models' `api_key_env` name.

## The Python API

`from tau import Name` reaches every public name; the other public modules are `tau.cli`,
`tau.commandline`, `tau.tui` and `tau.trace`. Everything else is private (underscore-named).
The pages below are generated from docstrings, one per group:

[Overview](api/index.md) | [Extensions](api/extensions.md) | [Tools](api/tools.md) |
[Records](api/records.md) | [Clients](api/clients.md) | [Events](api/events.md) |
[Sessions](api/sessions.md) | [The wire](api/wire.md) | [Driver](api/driver.md) |
[Providers](api/providers.md) | [Step machine](api/machine.md) | [Config](api/config.md) |
[Errors](api/errors.md) | [Terminal UI](api/tui.md) | [Tracing](api/diagnostics.md)

## The wire protocol

[The wire protocol](api/wire-protocol.md) is generated from the JSON Schema that
`tau serve --schema` prints (protocol number 1, matched exactly by the server's `hello`).
