---
title: "Tutorials"
category: "tutorials"
status: "stub"
---

# Tau — Tutorials

<p class="axis">Action × Acquisition</p>

Guided builds for Tau, from a first headless run to a custom Python extension.

Tutorials are read in order. The [quickstart](quickstart.md) is the
first one — it gets something running so the rest have somewhere to
start from.

1. **[Quickstart](quickstart.md)** — install τ, take one headless turn, then
   open the same session in the TUI, roll a turn back, and find the rolled-back
   turn still on disk. Teaches that a session is a tree rather than a chat log,
   and that undo is navigation rather than deletion. *Scaffolded; not yet run
   against a fresh install.*
2. **Write your first extension** *(planned)* — a `tool_call` hook that vetoes a
   destructive command, grown into a registered tool. Teaches the extension
   contract: a plain Python module with a `register(api)`, no manifest and no
   compile step, and the one hook that can actually block execution. The
   [Cookbook's permission gate](../cookbook.md#veto-a-dangerous-tool-call-before-it-runs)
   is the finished code this would walk up to.
3. **Drive τ from another process** *(planned)* — `--mode rpc` over stdio, the
   `get_capabilities` handshake, and why a host that needs a real hard kill
   spawns a subprocess instead of importing the SDK.

Until 2 and 3 exist, the [Cookbook](../cookbook.md) is the fastest route to
both — every recipe there cites a file that ships in the source tree, so the
working version is always one `-e` away.
