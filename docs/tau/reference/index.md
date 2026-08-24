---
title: "Reference"
category: "reference"
status: "draft"
---

# Tau — Reference

<p class="axis">Cognition × Application</p>

Four packages, five distributions, three wire protocols, one extension API.
This page is the map; each package has its own page below it.

!!! note "Draft"
    Built for lookup, not narrative reading. Written against the running code
    rather than against the source repo's own design docs, several of which
    predate the current provider layer. `tau --help` is the exact contract for
    every CLI table here; treat a disagreement as this page being stale.

## The stack

<figure class="dia"><svg viewBox="0 0 680 336" role="img" aria-labelledby="dia-stack-t dia-stack-d"><title id="dia-stack-t">The four packages and the one-way boundary</title><desc id="dia-stack-d">Four labelled boxes stacked down the left of the figure, each with a gloss to its right, and one red horizontal rule across the whole width. At the top, above the rule, sits tau underscore coding underscore agent, glossed as the tau command and the Textual TUI, and noted that c l i dot p y line 519 is the only import of the app so that tau dash p and tau dash dash mode r p c load no interface library. The red rule below it is marked the one-way boundary, with the gloss that nothing below the line imports anything above it. Under the rule are three more boxes. tau underscore agent underscore core holds the agent loop, tools, sessions and extensions, and assumes no terminal. tau underscore jmfts, drawn in a lighter outline because it is optional, sends an arrow up into tau underscore agent underscore core. tau underscore llm sits at the bottom holding the three wire protocols and the message, tool and streaming-event types, and depends on pydantic and httpx and nothing else. A downward arrow runs from the coding agent across the red rule into the agent core, and a second downward arrow runs from the agent core past the jmfts box into tau underscore llm. Every arrow points down; none points up.</desc><text x="0" y="36" class="label-role">interface</text><rect x="96" y="42" width="232" height="44" class="fill-ground stroke"/><text x="212" y="70" text-anchor="middle" class="label">tau_coding_agent</text><text x="352" y="56" class="label-soft">the tau command, and the Textual TUI</text><text x="352" y="72" class="label-soft">cli.py:519 is the only import of the app,</text><text x="352" y="88" class="label-soft">so tau -p loads no interface library</text><line x1="212" y1="86" x2="212" y2="126" class="stroke"/><path d="M212 134 L208 125 L216 125 Z" class="fill-ink"/><line x1="20" y1="110" x2="660" y2="110" class="stroke-red"/><text x="20" y="103" class="label-mark">the one-way boundary</text><text x="196" y="103" class="label-soft">nothing below this line imports anything above it</text><text x="0" y="146" class="label-role">headless</text><rect x="96" y="134" width="232" height="44" class="fill-ground stroke"/><text x="212" y="162" text-anchor="middle" class="label">tau_agent_core</text><text x="352" y="150" class="label-soft">the agent loop, tools, sessions, extensions</text><text x="352" y="166" class="label-soft">no textual, no stdin or stdout assumptions</text><line x1="140" y1="178" x2="140" y2="262" class="stroke"/><path d="M140 270 L136 261 L144 261 Z" class="fill-ink"/><rect x="200" y="204" width="200" height="40" class="fill-ground stroke-hair"/><text x="300" y="229" text-anchor="middle" class="label">tau_jmfts</text><line x1="300" y1="204" x2="300" y2="186" class="stroke-hair"/><path d="M300 178 L296 187 L304 187 Z" class="fill-ink"/><text x="420" y="220" class="label-soft">optional &#183; --store jmfts</text><text x="420" y="236" class="label-soft">an entry becomes a document</text><rect x="96" y="270" width="232" height="44" class="fill-ground stroke"/><text x="212" y="298" text-anchor="middle" class="label">tau_llm</text><text x="352" y="284" class="label-soft">three wire protocols, and the message,</text><text x="352" y="300" class="label-soft">tool and streaming-event types</text><text x="352" y="316" class="label-soft">depends on pydantic and httpx, nothing else</text></svg><figcaption>Read the arrows as "imports". Every one points down, and the red rule is the reason the split is worth having rather than a filing convention: because nothing under it reaches up, the headless half runs with no terminal libraries installed at all — measured at 15 packages and 13 MB, against 27 and 31 MB with <code>[tui]</code>. The same property is what lets <code>tau_agent_core</code> be embedded in a host process, driven over stdio, or run under the TUI without knowing which.</figcaption></figure>

## Packages

Each is installable on its own. The `ffwf-` prefix is not decoration:
`tau-ai` and `tau-llm` on PyPI are unrelated third-party projects, so
`pip install tau-llm` fetches someone else's code.

| Distribution | Imports as | What it is |
|---|---|---|
| `ffwf-tau` | — | The guessable name. A meta package: depends on `ffwf-tau-coding-agent[tui]` at the same version and nothing else. |
| [`ffwf-tau-llm`](tau-llm.md) | `tau_llm` | Wire protocols, message and tool types, streaming events. |
| [`ffwf-tau-agent-core`](tau-agent-core.md) | `tau_agent_core` | Agent loop, tools, sessions, [extensions](extensions.md), [RPC](rpc.md). Headless. |
| [`ffwf-tau-coding-agent`](tau-coding-agent.md) | `tau_coding_agent` | The `tau` command and the Textual TUI. |
| `ffwf-tau-jmfts` | `tau_jmfts` | JMFTS-backed session store. See [Tau + JMFTS](../../integrations/tau-jmfts.md). |

The meta package is the front door — the guessable name, and it pins the top
of the stack at the same version:

```bash
pip install ffwf-tau
```

Installing the top of the stack directly pulls the rest:

```bash
pip install 'ffwf-tau-coding-agent[tui]'
```

The meta deliberately does not pull `[jmfts]` — that store needs a running
server, so it stays an opt-in extra.

Everything past the headless core is an extra, and each one reports its own
absence with the install command rather than a traceback:

| Extra | Adds | Needed for |
|---|---|---|
| `ffwf-tau-coding-agent[tui]` | `textual`, `rich` | the interactive TUI. `tau -p` and `tau --mode rpc` run a full turn without it. |
| `ffwf-tau-coding-agent[jmfts]` | `ffwf-tau-jmfts` | `--store jmfts`. |
| `ffwf-tau-agent-core[bus]` | `nats-py` | the built-in `nats_bus` extension. |
| `ffwf-tau-agent-core[testing]` | `pytest` | importing `tau_agent_core.testing`. |
| `ffwf-tau-llm[anthropic]` | `anthropic` | calling Anthropic (`api: "anthropic-messages"`). |
| `ffwf-tau-llm[google]` | `google-genai` | calling Gemini or Gemma (`api: "google-generative-ai"`). |

The two vendor SDKs import lazily, on the first request rather than at module
import, so a plain install pulls neither and `import tau_llm` works without
them.

The install puts **two** console scripts on PATH — `tau` and `ffwf-tau`, the
same entry point behind each. Type `tau`; write `ffwf-tau` in scripts, systemd
units and Dockerfiles. See the
[DevOps Manual](../devops.md#which-command-name-to-write) for why.

## Where each subject lives

| Page | Covers |
|---|---|
| [`tau_llm`](tau-llm.md) | The three wire protocols, the two registries and the pool, `Model`, message and content types, streaming events, tool definitions, reasoning signatures. |
| [`tau_agent_core`](tau-agent-core.md) | The turn loop and its two event vocabularies, `submit()` and the one door, sessions as a tree, the SDK entry point, project context files, compaction. |
| [Extensions](extensions.md) | The `ExtensionAPI` surface, the hook vocabulary, discovery and collision rules, the bus capability grant. |
| [RPC](rpc.md) | The JSON-RPC verb tables, the two answers a submission gets, and the seven verbs τ declines. |
| [`tau_coding_agent`](tau-coding-agent.md) | The four run modes, the full CLI flag table, `config.json`, and what the TUI is actually made of. |

## Three things that are easy to get backwards

**A tool call is transformed four times** on its way from HTTP bytes to a
rendered widget — provider `ToolCall`, then a message dict block, then a
backend info dict, then a widget. When tool calling misbehaves, trace the
`arguments` value through all four hops rather than reading any one of them.
[`tau_llm`](tau-llm.md#streaming-events) and
[`tau_agent_core`](tau-agent-core.md#two-event-vocabularies) each own two of
those hops.

**`api` and `provider` are different questions.** `api` is which wire protocol
to speak; `provider` is which vendor, and therefore which base URL and which
credential. Many vendors share one protocol, which is why they are two fields
and two registries. See [`tau_llm`](tau-llm.md#two-registries-and-a-pool).

**Tool argument validation is hand-rolled.** `validate_tool_arguments` checks
`type` and `required` from a plain-dict schema and nothing else — no
`minLength`, no `minimum`, no `enum`. Writing one of those into a tool schema
looks enforced and is silently ignored. See
[`tau_llm`](tau-llm.md#tools).
