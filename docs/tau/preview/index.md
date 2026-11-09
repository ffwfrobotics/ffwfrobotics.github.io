---
title: "Tau 0.16 preview"
---

# Tau 0.16 "Trusty" (preview)

!!! warning "Unreleased"
    Everything under this heading documents the **0.16.0-dev** line: the `master` branch of the
    Tau repository (published on GitHub as the `rust-rewrite` branch of `jmccardle/tau`), version
    string `0.16.0.dev0`, protocol 1. It is not on PyPI, it has no release tag, and its
    interfaces can still change. The released Tau is [v0.15.0](../index.md), the Python
    five-package line; use that for anything you depend on.

0.16 is a rewrite, not an upgrade. A sans-IO Rust core (`crates/`) sits under a Python driver,
hooks, providers, tools and frontends (`python/tau`), shipped as one package, `ffwf-tau`, that
you `import tau`. The design is a session as a tree of nodes, with **cursors** that walk it,
and **steps** that hooks can change at fixed points.

Documented against: commit `c439c401` of `master`, `v0.15.0` plus 276 commits;
`Cargo.toml` says `0.16.0-dev.0`; `tau --version` prints `tau 0.16.0.dev0 (protocol 1)`.

## What state it is in

The project plan has ten phases; at this commit phases 0 to 6 are done, phases 7 (the wire,
the shared start, the API docs) and 8 (frontends, tools, standard extensions) are in progress,
and phase 9 (the release: wheels beyond Linux x86_64, the PyPI workflow, release notes) has not
started.

| Built (this commit) | Not built |
|---|---|
| Rust core, session store, Python bindings | Wheels for macOS, Windows or aarch64; Linux x86_64 only, and the base tools are Linux-only |
| Providers: OpenAI-compatible, Anthropic, Gemini, a scripted mock | PyPI release (no `0.16` wheel exists) |
| Base tools `read`, `write`, `edit`, `grep`, `find`, `bash` | Image input, constrained decoding, a models.dev catalog, code mode, background tools |
| The `tau` program: terminal UI, `tau -p`, `--json`, `--answer` | `--mode rpc` over stdio (the Tectum contract), `--mode repl`, `--bus` (NATS) |
| `tau serve` (JSON-RPC over a WebSocket on a Unix socket), `--schema` | Per-run tool lists (`--tools`, `--no-tools`, `--exclude-tools`) |
| Built-in extensions: retry, `@file` attachments, prompt templates and skills, usage and cost, compaction, prune, permissions, sub-agents (off by default), step limit | HTML export, the JMFTS session store |
| Project trust (`tau trust`), `tau config check`, layered config, `.env` | A converter for 0.15 session files (there will not be one) |
| A ratatui example client in `examples/ratatui` | Changes in the sibling clients (`tau-code`, `tau-search`), which sync after 0.16.0 |

[What changed from 0.15](differences.md) says what each 0.15 capability became.

## Pages

| Page | Covers |
|---|---|
| [Quickstart](quickstart.md) | Build it, configure one model, chat, list and export sessions, serve a session |
| [Writing an extension](extensions.md) | Tools, commands, options, hooks, and where extensions load from |
| [Operating it](operations.md) | `$TAU_HOME`, config layers, project trust, serving, CI and wheels |
| [Reference](reference.md) | The `tau` command line, the public Python API groups, the wire protocol |
| [What changed from 0.15](differences.md) | Built, changed, dropped and planned, per capability |
