---
title: "Tau 0.16 preview: Writing an extension"
---

# Writing an extension (0.16 preview)

!!! warning "Unreleased, and not the 0.15 API"
    This is the 0.16.0-dev extension model. It shares no code with 0.15's `ExtensionAPI`; a 0.15
    extension does not load in 0.16 and there is no compatibility shim. For 0.15 see
    [Extensions](../reference/extensions.md). Source: `docs/guide/extensions.md` at commit
    `c439c401`, whose examples the repository runs as tests.

An extension is a Python object with a `name` and any of:

- **tools** the model can call,
- **commands** a person types as `/name`,
- **options**, settings kept in the config,
- **hooks**, functions Tau calls at fixed points of a step.

It can also show a status on a cursor and ask whoever is watching a question. Extension objects
come from `import tau`; there is no `ExtensionAPI` object to receive.

## A complete extension

```python
from dataclasses import dataclass
from typing import Annotated, Literal

from tau import Body, CallDraft, Cursor, NodeHandle, ToolError


@dataclass(frozen=True)
class Options:
    max_chars: Annotated[int, "longest text the shout tool takes"] = 40


class Shouter:
    name = "shouter"
    options = Options

    def __init__(self) -> None:
        self.tools = (self.shout,)
        self.commands = (self.count,)

    def shout(self, text: Annotated[str, "what to say"], node: NodeHandle) -> str:
        """Return the text in capitals."""
        longest = node.options().max_chars
        if len(text) > longest:
            raise ToolError(f"say at most {longest} characters")
        return text.upper()

    async def count(self, cursor: Cursor) -> str:
        """Say how many nodes are on this branch."""
        mine = await cursor.ask("Count only the messages you sent?", bool)
        nodes = cursor.walk()
        if mine:
            nodes = [n for n in nodes if isinstance(n.body, Body.User)]
        cursor.show(f"{len(nodes)} counted")
        return f"{len(nodes)} nodes"

    async def pre_tool(self, node: NodeHandle, call: CallDraft) -> str | None:
        verdict = await node.ask(f"let the model call {call.tool}?", Literal["yes", "no"])
        return None if verdict == "yes" else "the user said no"


extensions = [Shouter()]
```

A module with a `name` is itself the extension; otherwise it defines `extensions = [...]`, a
non-empty list. Save the file as `shouter.py` and load it for one run with
`tau ext list -e shouter.py` or `tau -e shouter.py ...`.

## Tools

A tool is a plain function in `tools`. The **name** is the function name, the **description** is its
docstring (no docstring: `DefinitionError` at load), and the **parameters** are a JSON Schema
built from the type hints. Allowed hints: `str`, `int`, `float`, `bool`, `Literal`, `list[T]`,
`T | None`, `pathlib.Path`, and the named types `Model`, `CursorId`, `LabelName`, `NodeId`.
`Annotated[T, "text"]` adds a description. The function returns a `str`. Raise `ToolError` to tell
the model why it failed. Sync tools run in a worker thread; `async` ones on the loop. Tau fills
in `NodeHandle`, `TreeHandle` and `Progress` parameters by annotation and hides them from the
model. Tool names are not namespaced; two tools with one name are an error.

## Commands and options

A command is a function in `commands`, run as `/name`; its docstring is the help and its
parameters are the arguments. One that takes a `Cursor` runs as a step of that cursor. Two
extensions with the same command name make the bare name ambiguous; the qualified form
`/shouter:count` always works.

`options` names a frozen dataclass with plain defaults. Values come from `extensions.<name>` in
the config files, `tau config set shouter.max_chars=80`, `--set shouter.max_chars=80` for one
run, or `/config shouter max_chars=80` in a session.

## Hooks

An `async` method named for its point. A cursor hook is `hook(cursor, subject)`, a tool hook
`hook(node, call)`. In the order a step reaches them: `pre_step`, `pre_input`, `pre_sample`,
`pre_reply`, `post_reply`, `pre_tool`, `pre_result`, `post_result`, `post_step`.
Returning `None` carries on; returning a string **stops** the step with that reason (for a tool
hook the string becomes the call's error). An exception fails the step. A tool hook may rewrite
`call.args_raw` or set `call.outcome` to answer the call.

## Where Tau finds extensions

In load order: **built-in** (`agents`, `attachments`, `base_tools`, `compaction`,
`permissions`, `prune`, `skills`, `step_limit`, `usage`, and `retry` for the provider wrapper),
installed **packages** in the `tau.extensions` entry-point group (the value is a module),
**user** drop-ins in `$TAU_HOME/extensions/`, **project** drop-ins in `.tau/extensions/` (only
after `tau trust`), then `-e PATH|KEY` (naming it is the consent). A later source with the same
key shadows an earlier one. `tau ext list [--json]` shows every source and why it is on or off;
`tau ext enable KEY` and `tau ext disable KEY` write the `load` key of your config. A source that
fails to load stops Tau from starting rather than carrying on unguarded.

The six base tools (`read`, `write`, `edit`, `grep`, `find`, `bash`) come from the built-in
`base_tools`; `tau ext disable base_tools` starts sessions without them.

## Testing

Drive the extension with a scripted provider (an object with `name`, `check`, `aclose` and an
async-generator `sample`) through `Driver`, `Session.create` and a `Client`, with no network.
The repository's guide shows a complete runnable test; the `Harness` protocol in
`tests/behavior` is how Tau tests itself.
