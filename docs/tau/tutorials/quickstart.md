---
title: "Quickstart"
---

# Tau — Quickstart

<p class="axis">Action × Acquisition</p>

Run Tau headless against a repository and read the session tree it produces.

You will point τ at a model, take one turn without a terminal UI, then open the
same session interactively, roll a turn back, and find the rolled-back turn
still sitting on disk. The last part is the point: a τ session is a tree, and
nothing in it is destroyed by undo.

!!! warning "Scaffolding, not a tutorial"
    The shape below is drawn from [DevOps](../devops.md) and
    [Reference](../reference.md), both of which are written from the source
    repo. What is missing is a run: no command here has been executed against a
    fresh install, and the outputs are described rather than pasted. Every gap
    is named in [What this still needs](#what-this-still-needs) rather than
    filled with a plausible guess.

## 1. Install it and give it a model

Three packages, layered so nothing drags in Textual that does not need it:

```bash
python -m venv venv && source venv/bin/activate
pip install -e ./tau-llm -e ./tau-agent-core -e './tau-coding-agent[tui]'
```

The `[tui]` extra is what pulls in Textual. Leave it off and you have a working
headless τ with no interactive UI — which is a legitimate deployment, and not
what step 4 wants.

`~/.tau/config.json` names the default model. Out of the box it points at
`local-llm` — an OpenAI-compatible server on localhost, so vLLM, Ollama, or
`llama-server` all qualify.

> **Needs a run.** Paste the minimal working `config.json` for one local
> endpoint, and the exact `No API key for provider: …` failure. That refusal is
> the first thing this tutorial should teach: τ does not invent a credential to
> get further.

## 2. Take one turn, with no UI at all

```bash
cd ~/some/repo
tau -p "What does this project do? Read only what you need."
```

One turn, a printed transcript, exit.

The claim to land here: **that was a real session.** There is no headless-only
format — what you just wrote shows up in the TUI's sidebar and can be picked up
interactively later.

## 3. Look at what it wrote

Sessions live in `~/.tau/sessions` as append-only JSONL. Not a chat log: each
line is an entry with a `parent_id`, and the conversation the model actually
saw is the path from the root to the active leaf.

> **Needs a run.** Show one real session file, trimmed. The teaching moment is
> `parent_id` — a reader should be able to point at the chain by eye before the
> word "tree" is used again.

## 4. Open the same session interactively

```bash
tau --continue
```

Same session, same file, now with a UI on top. Headless and interactive are two
front doors onto one store, which is why step 2 was not a throwaway.

## 5. Undo a turn, then go find it

Ask a follow-up, then press `Ctrl+Z`.

That is `multitask_strategy="rollback"`: τ navigates back to the pre-turn leaf.
The turn you just undid becomes an **abandoned sibling branch** — it is still
on disk, and `Ctrl+G` opens the tree browser that will show it to you.

This is the whole reason the tree exists. Undo costs nothing and loses nothing,
so branching is an ordinary operation rather than a feature with a warning
label attached.

> **Needs a run.** A before/after of the `Ctrl+G` browser is the single most
> valuable artifact this page could carry — ideally the one screenshot in the
> tutorial.

## 6. Get it machine-readable

```bash
tau -p --mode json "..."
```

JSONL lifecycle events instead of prose — the same stream the TUI renders,
which is what makes a τ child process legible to a parent one.

## What you have

One repository, one model, and a session you have now read three ways: printed,
on disk, and in a UI. The tree is the thing to carry forward — every later Tau
feature (fork, compaction, elide, extension state) is that same tree used
harder.

## Next

- **Give it a rule it cannot break.** The Cookbook's
  [permission gate](../cookbook.md#veto-a-dangerous-tool-call-before-it-runs)
  is about twenty lines and is the shortest path to a real extension.
- **Keep state that time-travels.** [State in the tree, not beside
  it](../cookbook.md#keep-state-in-the-tree-not-beside-it) — a todo list that
  rolls back when you press `Ctrl+Z`.
- **Run it for real.** The [DevOps Manual](../devops.md) covers the five run
  modes, where credentials come from, and why a host that wants a hard kill
  should drive `--mode rpc` rather than importing the SDK.

## What this still needs

Named here rather than left for a reader to discover:

- A working `config.json` for one local endpoint, and the missing-key error.
- One real session file, trimmed to show `parent_id`.
- The `Ctrl+G` tree browser after a `Ctrl+Z`, showing the abandoned sibling.
- Confirmation that `--continue` is the right resume flag for a session written
  by `tau -p` (`--resume` raises at the CLI — it is TUI-sidebar-only).
- A decision on whether step 6 belongs here at all, or moves to a second
  tutorial about driving τ from another process.
