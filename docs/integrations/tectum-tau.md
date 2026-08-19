---
title: "Tectum + Tau"
kind: "integration"
summary: "Agents as nodes on the substrate: Tau sessions driven by Tectum events, and emitting their own back."
projects: [tectum, tau]
status: "draft"
---

# Tectum + Tau

Tau runs an agent; Tectum decides which agent runs, when, and on what
evidence. The integration puts a Tau agent behind a Tectum node
(`TauAgentNode`, in `tectum/tau_node.py`): the node owns one persistent
`tau --mode rpc` subprocess, feeds it events the schema routed to it, and
everything the agent does comes back out as events on the bus — where the
schema, not the agent, decides what happens next. τ stays what it is — a
process a host drives, not a library it imports — and the host here is the
substrate.

!!! note "Draft"
    Written from both sides of the seam: the Tau repo's
    `docs/PI-RPC-REPLACEMENT.md`, `docs/NATS-BUS-EXTENSION.md`,
    `docs/REMOTE-CONTROL.md`, and `scripts/tectum_responder.py`; and the
    Tectum repo's `tau_node.py`, `tau_extensions.py`, and `tau_ext/`. The
    substrate half has confirmed live runs; the τ-node half is attested by
    offline suites and run notes — see
    [What is demonstrated](#what-is-demonstrated-and-what-is-only-claimed)
    at the end.

That division is the point. The agent never subscribes to anything, never
picks its own inputs, and cannot reach an effector except by publishing a
verb some schema chose to bind. Rewiring who hears what, or swapping one
agent implementation for another, is a YAML edit — the agent's own code does
not know the difference. The Tectum Cookbook has the operational version of
that claim:
[Swap an agent under a live device](../tectum/cookbook.md#swap-an-agent-under-a-live-device).

## Two postures, one wire contract

There are two ways to put τ on a substrate, and they share the same
[envelope](../tectum/reference.md#the-event-envelope) and verb vocabulary:

- **As a plain NATS client.** τ's builtin `nats_bus` extension subscribes
  one inbound subject and registers one tool per outbound verb. No schema is
  written, no supervisor is involved — τ takes the same posture as a
  monitoring TUI. This is the right shape for driving experiments against a
  live substrate from outside it. The Tau Cookbook carries the wiring:
  [Bridge a session onto a NATS bus](../tau/cookbook.md#bridge-a-session-onto-a-nats-bus-tectum-integration).
- **As a Tectum node.** Tectum's `TauAgentNode` supervises the subprocess,
  restamps its bindings per turn, and gives the agent a workspace identity.
  The node — not the agent — is what the schema names in `requires.nodes`,
  so [activation](../tectum/devops.md#schema-activation), ref-counting, and
  degrade-and-restore apply to the agent like any other
  [node](../tectum/reference.md#node-manifest-and-lifecycle).

Either way, the verbs are the contract: `speak`, `journal_append`,
`jmfts_write`, `delegate`, each with a declared ack subject the extension
waits on before returning a tool result. Publish-and-hope is not in the
vocabulary — a `speak` whose completion ack never arrives is a tool error
the model sees, not a message lost in transit.

The subprocess itself is Tau's [RPC mode](../tau/reference.md#rpc): one
JSON-RPC 2.0 server over stdio, persistent across turns, writing real
sessions the TUI can open later.

## One process, one node

`TauAgentNode.setup()` starts τ headless (`--no-tools --no-extensions
--no-session`), performs the `get_capabilities` handshake, and holds the
process open across turns — the conversation lives in the τ process, not in
Tectum. On each inbound event the node writes the event's `binding_id` to a
per-run file that the extensions re-read on every publish, frames the
payload, and issues one `prompt` over JSON-RPC. A turn that exceeds the
node's wall-clock budget gets an `abort` RPC: interrupted, never abandoned
with a zombie turn in flight.

What Tectum adds is everything around the process. The schema decides which
subjects reach the agent; the control agent supervises it under a
`restart_policy` like any other
[node](../tectum/reference.md#node-manifest-and-lifecycle); and because τ is
a subprocess rather than an import, the supervisor holds a real hard kill
for the day the agent stops being a well-behaved tenant.

## Why the agent gets no shell

Every τ node runs with `--no-tools`. This looks like a restriction; it is
the design.

The earlier pi-based agent nodes exposed verbs as bash shims on `PATH` — the
agent ran a shell, and `tectum-speak` was a script that published an event.
Two problems were measured, not theorized:

- A shim cannot be schema-constrained. The prompt overlay described
  `tectum-speak "..."` as a command line while the API offered a generic
  `bash` tool — two surfaces for one verb, one of them fake. Measured on a
  live handset session, the model *typed* `tectum-speak "Blue."` as prose
  about a quarter of the time, and the utterance reached nobody. The same
  free-typing produced **17 `speak` calls for one question**, then 50, with
  replies arriving three turns stale.
- A shim cannot end an agent loop. A bash exit code carries no `terminate`
  flag, so the only brake was a sentence in the tool's stdout. One early
  version returned the raw completion ack as the tool result; the model read
  its own sentence quoted back, saw no turn-over signal, and looped for 28
  turns before being killed.

The τ integration replaces shims with real registered tools: each verb
carries a JSON schema the model is constrained against, and `speak` is
declared *terminal* — the tool result ends the turn mechanically, and the
result text tells the model so in words. Both halves are load-bearing; the
model's cooperation is welcome but not required.

## The schema is the feature flag

`agent.edge_asr` is a τ-backed agent that answers a phone's push-to-talk
turns. `agent.edge_asr_memory` is the same node class configured with one
more extension — reflexive memory. The two schema files differ by one node
name; the wiring is identical. Giving the agent a memory was not a refactor
of the agent. It was a different name in `requires.nodes`.

That is the integration in miniature: because a τ session is a node and
orchestration lives in
[schema documents](../tectum/reference.md#praxis-schema-document), an agent
variant is an activation decision. The A/B, the rollback, and the promotion
are all `tectum schema apply` and `unapply` — with the one standing rule
that the two variants never run together, because both publish the same
device-scoped speak rail. The Cookbook's
[push-to-talk recipe](../tectum/cookbook.md#add-a-push-to-talk-agent-on-a-second-device)
carries both schemas and that rule.

## Extensions are configuration, not code

τ extensions are plain Python with full access to the session. Tectum ships
two extension files (`tectum/tau_ext/`) and hands them to τ *by path* — it
never imports them. On the Tectum side, each extension is a frozen
dataclass (`tectum/tau_extensions.py`) that knows its own file path, which
run-context facts it needs, and how to render itself as `--extension PATH`
and `--ext-config <stem>.<key>=<value>` flags.

τ's own safety gate is honored in the same currency: an extension that
touches the bus declares `TOUCHES_BUS` on the τ side, the Tectum spec
restates it as `NEEDS_BUS`, and `--bus` is passed only when a loaded
extension needs it — decided before the τ process exists, because a flag
cannot be added to a running subprocess.

The stated design goal, from the source: a subclass that only names
different extensions is a different agent, and it should not have to be
different code.

One wire format, defined once: the extension files execute inside τ's
interpreter, but they import Tectum's stdlib-only `event` and `subjects`
modules rather than re-declaring the envelope. The `TectumEvent` an
extension publishes is the same class every other node on the substrate
speaks.

## The model's prose is the channel

The handset extension registers exactly one tool and then gets out of the
way. What routes an answer is the *shape of the turn*:

- Text in a turn that also called a tool → a status line, published to the
  reply rail; the turn continues.
- Text in a turn that called nothing → the answer. Speakable text goes to
  the device's `speak` subject; unspeakable text (a table, a code block)
  goes to the reply rail marked `spoken: false`, with the reason stated.
- No text and no tool → silence, which is a valid turn, not a failure.

A refusal to speak is published as a fact on the bus rather than raised as
an error inside the agent — downstream nodes can react to "declined to say
this aloud" the same way they react to anything else: by being bound to it,
or not.

The retry closes outside τ, and that is the seam working in both
directions. The extension cannot re-prompt from inside a `turn_end` hook —
that hook belongs to the in-flight turn's own task, and submitting there
raises. So the extension states the refusal in the reply event's payload;
the node, which subscribes its own `out.>` wildcard to see what its turn
actually put on the wire, reads that refusal off the bus and issues one
follow-up prompt asking for a speakable rewrite. The correction travels
back in as an ordinary prompt, and the failure is visible to anything
watching `events.>` instead of being an internal boolean two processes have
to agree about. Nothing in that loop required τ to know what a device token
is.

## Memory the model does not elect

The `memory_reflex` extension gives a τ node retrieval and memorizing that
run on cadence, outside the model's own choices: every user turn is preceded
by a search over the agent's memory trees, with hits threaded ahead of the
utterance; every N turns, a forked sub-agent reviews the conversation and
deposits what is worth keeping, after a dedup check.

Neither is a tool the model can call, skip, or spend its reasoning budget
deciding about. And both report themselves on subjects named in the past
tense — `recall`, `memorize` — as records of what already happened, never as
requests. Nothing binds a past-tense report back into the agent, so the
memory loop cannot become a cycle by construction.

This is the opposite posture from the one on the
[Tau + JMFTS](tau-jmfts.md#recall-is-a-tool-call-not-an-injection) page,
where recall is a tool call the agent elects and the transcript records.
Both are defensible; they answer different questions. A reflex guarantees
recall happens and costs the model nothing to decide; a tool call leaves an
auditable trace of what was recalled and when.

## A credential the agent cannot leak

Each agent node carries its own JMFTS bearer token, and the token *is* the
principal: the memory server gates every read and write on that identity's
grants, and a denied read is a 404 — the document does not exist for that
agent, in search counts and subtree walks included.

Under a shell-bearing agent this fence is decorative — any credential the
tools can use is one `printenv` away from the model. Under τ with
`--no-tools`, the model has no shell, so it has no mechanism to disclose
its own credential: the extension holds it, uses it, and never surfaces it
in a tool result. Two agents on one substrate can then hold genuinely
different views of the same memory tree, enforced by the store rather than
by prompt discipline.

One honest caveat: the token still reaches the agent subprocess's
environment — the fence is against the *model*, not against the process.

## What the seam taught

Three facts about driving τ as a subprocess that only showed up in
practice:

- **A prompt answers twice.** `prompt` and `submit` return an acceptance
  result first, then an `agent_end` event, correlated by submission id. The
  pair is the unit of completion; the first answer alone means only
  "queued", so a host that returns on it will talk over its own agent.
- **`get_capabilities` returns about 70 KiB on a single line.** Size stdio
  limits for the protocol you are actually speaking — the node runs with a
  16 MiB reader limit, not a default line buffer.
- **One session takes one turn at a time.** A second submission while a
  turn is in flight is refused with `-32000 a turn is already in flight`.
  That constraint is what shaped the memory extension's off-the-turn
  scheduling, covered on
  [the full stack page](full-stack-agent.md#lessons-that-needed-all-three).

## What is demonstrated, and what is only claimed

The substrate side of this page — schema activation, the verb and ack
contract, the WAN bridge — has confirmed live runs behind it. The τ node
track (the handset agent, the memory variant, the extensions above) has
passed its offline test suites (`test_tau_backend.py`, `test_tau_node.py`,
`test_tau_extensions.py`, `test_handset_bus.py`), but its live end-to-end
claims are so far commit-message notes, not automated checks. The two
memory variants also share an output subject, so a deployment runs one or
the other, never both — activating both answers every turn twice.

All three projects at once, including the deployment this page's handset
examples come from, are on
[The FFwF Full Stack Agent](full-stack-agent.md).
