---
title: "Quickstart"
---

# Tau — Quickstart

<p class="axis">Action × Acquisition</p>

Run Tau headless against a repository and read the session tree it produces.

## 1. Install it

Tau needs Python 3.11 or newer. The distribution is **`ffwf-tau`** — the
guessable name, a meta package that pulls `ffwf-tau-coding-agent[tui]` at the
same version. The `ffwf-` prefix is load-bearing rather than branding: `tau-ai`
and `tau-llm` on PyPI are unrelated third-party projects, so a command missing
the prefix installs someone else's code.

Everything below installs the same release. Pick the installer you already use.

### uv

`uv tool install` gives Tau its own environment and puts the commands on PATH,
which is what you want for something you run as a program rather than import as
a library:

```bash
uv tool install ffwf-tau
tau --version
```

To try it without installing anything, run it straight from the index:

```bash
uvx --from ffwf-tau tau
```

Inside a project that already has a `uv` environment — an extension you are
writing, or a host embedding the SDK — add it as a dependency instead:

```bash
uv add ffwf-tau
```

### pipx

Same shape as `uv tool`: one isolated environment per application.

```bash
pipx install ffwf-tau
tau --version
```

### pip

pip installs into whichever environment is active, so make one. A modern
system Python is marked externally managed and will refuse a bare
`pip install` (PEP 668) rather than write into the OS's own site-packages.

```bash
python3 -m venv .venv
./.venv/bin/pip install ffwf-tau
./.venv/bin/tau --version
```

Activate the environment (`source .venv/bin/activate`) if you would rather type
`tau` than the path to it.

### Skipping the TUI, and the second command name

The meta package includes the TUI. If a deployment only ever runs `tau -p` or
`--mode rpc`, install `ffwf-tau-coding-agent` without the `[tui]` extra instead
— Textual and Rich are the only thing an interactive `tau` needs that a
headless one does not, and without the extra `tau -p` and `tau --mode rpc`
still run a full turn, extensions and all. Measured: 15 packages and 13 MB
without the extra, 27 packages and 31 MB with it:

```bash
uv tool install ffwf-tau-coding-agent      # or pipx install / pip install
```

Every install puts **two** commands on PATH, `tau` and `ffwf-tau`. They are one
entry point behind two wrappers, not a symlink, and they uninstall together.
Type `tau` at a terminal. Write `ffwf-tau` in a systemd unit, a Dockerfile, or
a cron line — PyPI reserves distribution names but not command names, and an
unrelated project ships its own `tau`, so in an environment holding both,
whichever installed last owns the short name.

The [DevOps Manual](../devops.md#install) covers the remaining extras
(`[jmfts]` for `--store jmfts`, `ffwf-tau-agent-core[bus]` for the `nats_bus`
extension) and the deployment shapes.

!!! warning "The rest of this page is not yet written"
    Installation is authored. The headless run against a repository, and
    reading back the session tree it produces, are still scaffolding.
