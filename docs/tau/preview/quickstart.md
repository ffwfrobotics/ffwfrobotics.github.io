---
title: "Tau 0.16 preview: Quickstart"
---

# Quickstart (0.16 preview)

!!! warning "Unreleased"
    This is Tau 0.16.0-dev, built from the repository's `master` branch. For the released
    Tau, see the [v0.15.0 quickstart](../tutorials/quickstart.md). Every command below was run
    against commit `c439c401` with a temporary `TAU_HOME` and the mock model, which needs no
    server and no API key.

## Build it

There is no 0.16 release on PyPI, so you build from a checkout. You need Python 3.12 or later and
Rust (`rustup`, cargo 1.89 or later).

```bash
git clone https://github.com/jmccardle/tau && cd tau
git checkout rust-rewrite
python3.12 -m venv .venv
.venv/bin/pip install --group dev           # pip 25.1 or later
VIRTUAL_ENV=$PWD/.venv .venv/bin/maturin develop --release
source .venv/bin/activate                   # puts `tau` on your PATH
tau --version                               # tau 0.16.0.dev0 (protocol 1)
```

Everything Tau keeps lives in `$TAU_HOME`, which is `~/.tau` unless you set it (an absolute
path, or one that starts with `~`).

## A config with one model

`$TAU_HOME/config.json` names your models. A **group** holds what its models share (here the
server); a model's **qualified name** is the group, a colon and the model: `local:qwen`.

```json
{
  "default_model": "local:qwen",
  "models": {
    "local": {
      "base_url": "http://localhost:8100/v1",
      "models": { "qwen": { "model": "qwen3-27b" } }
    },
    "mock": {
      "provider": "mock",
      "models": { "echo": { "model": "echo" } }
    }
  }
}
```

`local` is any server that speaks the OpenAI chat API (llama.cpp, vLLM, a hosted service). For a
hosted one add `"api_key_env": "NAME_OF_YOUR_KEY_VARIABLE"` to the group; the config names the
variable and never holds the key. `provider` is `openai` (the default), `anthropic`, `gemini` or
`mock`. Check the file:

```bash
tau config check
tau config check --show local:qwen
```

`check` prints nothing when the config is sound, and one line per problem otherwise.

## Ask once

`tau -p` sends one message, prints the answer on standard output and exits. `-m` picks the
model, `-n` names the session. The session is kept.

```bash
tau -p -m mock:echo -n quickstart "hello from a script"
# mock: hello from a script
```

Standard input that is not a terminal follows the words after a blank line, so
`git diff | tau -p "review this"` works. Exit status: `0` finished, `1` failure, `2` usage
error, `3` stopped before finishing (a step limit, a halting hook), `130` interrupted.
`--json` prints the session's events one JSON object per line, the same objects the wire sends.
`--set step_limit.limit=5` changes an extension option for one run. A question an extension
asks (a permission) has nobody to answer it under `-p` and is declined unless a rule answers:
`--answer permissions=yes`.

## Chat

`tau` with no `-p` opens the terminal UI. `-c` continues the newest session of this directory,
`-r` chooses one, `--session REF` opens one (attaching if a `tau serve` holds it), and
`--theme NAME` picks `mocha` (default), `latte`, `gruvbox` or `ansi`. Enter sends, Ctrl+J starts
a new line, Esc aborts the step, Ctrl+G shows the tree, Ctrl+Q quits.

```bash
tau -m mock:echo
```

## Look at what you did

```bash
tau sessions                      # this directory's sessions, newest first
tau sessions --json               # one object per line
tau export quickstart | head -n 12  # a session as Markdown (-o FILE, --thinking)
tau context                       # what a new session would be told, with sizes
tau ext list                      # every extension source, and why it is on or off
```

## Serve a session

```bash
tau serve -d --json --session quickstart
tau serve --stop --session quickstart
```

The first prints one JSON object: the `socket`, the server `pid`, the `session`, its `cwd`, the
`protocol` and `version`. Python programs connect with `RemoteClient`; other languages follow the
[wire protocol](reference.md#the-wire-protocol).

## Verified and not verified

All commands above except the build, `git clone`, `tau` (the interactive UI) and the
`local:qwen` model (which needs your server) were run by the repository's own documentation test
(`scripts/guide_examples.py`) during this pass. The build steps are quoted from the repository's
CLAUDE.md and were not re-run here: an existing `.venv` at that commit was used.
