---
title: "DevOps Manual"
category: "devops"
status: "draft"
---

# Tectum — DevOps Manual

<p class="axis">Cognition × Acquisition</p>

How a Tectum deployment fits together: NATS topology, how schema documents reach the nodes that need them, and what the substrate does when it partitions.

## The three primitives

| Primitive | What it is |
|-----------|-----------|
| **Tectum** | The event bus. **Nodes** on **substrates** exchange immutable `TectumEvent`s over NATS subjects. |
| **Praxis** | Declarative **schemas** — standing, additive intents. Activating a schema brings nodes up (RAII, ref-counted) and installs **bindings** (`subject -> node`). |
| **Workspace** | Agent dispatches, agent-side tool wrappers, and effector nodes that ride on top of the other two. |

Orchestration lives in declarative schema documents, not in Python wiring. A schema drives node lifecycle, binding install/remove, and the two-DAG topology described below.

## Two DAGs, one namespace

Every subject's dotted prefix says which DAG it belongs to. Schemas route by NATS wildcard against these prefixes, so the broker does the matching and stable routing dimensions live in the namespace instead of in payload predicates:

| Prefix | Direction | Meaning |
|--------|-----------|---------|
| `events.sensation.*` | bottom-up | sensors → filters → agent dispatch. A workspace node is only ever a *target* here. |
| `events.workspace.*` | — | the workspace layer itself: `<agent>.in` for dispatch, `<agent>.out.<tool>` for a tool call. |
| `events.action.*` | top-down | cross-effector / world-action coordination. |
| `events.system.*` | — | Tectum's self-report: schema/node/substrate lifecycle. |
| `events.journal.*` | — | durable-record emissions (effector write acknowledgements). |

The sensation DAG is strictly bottom-up; the command DAG (an agent-side tool wrapper publishing `events.workspace.<agent>.out.<tool>`, an effector consuming it) is strictly top-down. A subject never appears on both.

A command-DAG subject may carry an optional fifth token, the **device**: `events.workspace.<agent>.out.<tool>[.<device>]`. This exists because where a user spoke is where the reply must go — a phone turn is answered on the phone, a room turn through the room's speakers — and that is a routing question, not something a handler should decide from payload contents. An agent with no device dimension emits the undeviced subject, which is not a default device; it is a different rail from any `.handset`-style suffix.

## Schema activation

A schema is a YAML document naming the nodes it requires and the bindings it installs. Activating one:

1. Ref-counts each required node up. A node already running for another active schema is reused, not restarted.
2. Installs the schema's bindings — each one subscribes the `from` subject and delivers matching events to the `to` node's `on_event`.
3. Emits `events.system.schema.activated` so the activation is itself observable on the bus.

Deactivating a schema reverses both steps, unless the schema is marked `immutable: true`, in which case only an operator-class caller may unwind it. This is RAII: a node or binding lives exactly as long as at least one active schema needs it, and disappears the moment none do. Two schemas can require the same node without conflict — the reference count is the coordination mechanism, not a lock.

## Bringing a deployment up

Each node runs as its own OS process. A per-host **control agent** observes node registrations, holds the active-schema desired state, reconciles bindings against it, and supervises the node processes: when a schema needs a node that isn't running, the agent spawns it from a learned launch spec and restarts it per `restart_policy` with crash-loop backoff.

```bash
tectum scan                       # offline node graph (delivery/slots too)
tectum status                     # live-stack reachability + control/supervision graph
tectum up                         # control agent + supervised node fleet, hold until Ctrl-C
```

`tectum up` with no arguments activates whatever `praxis/active.yaml` lists — the boot default for that deployment — and then supervises the resulting fleet. A single node can also run standalone (`tectum --node <name>`), which is how you'd attach one more process to an already-running fleet without going through the control agent.

## What happens on partition

Substrate boundaries are represented in the graph, not left to broker reach. Two nodes, `bridge.egress` and `bridge.ingress`, are the only path across a boundary: `egress` is a sink that ships specific, named subjects across the link with identity preserved (one bridge hop appended, deduped by `event_id` on the far side); `ingress` is a pure source, like a hardware sensor node — it takes no inbound binding, because what it produces originates on the other substrate.

A schema on each side of the boundary declares its own half of the crossing contract explicitly: which subjects leave, which arrive, and at what quality of service (durable, idempotent, or fresh-only — a stale reply is TTL-dropped on the far side rather than acted on late). The two halves' egress and ingress sets are meant to line up; a mismatch — a subject bound to `bridge.egress` with no local producer, or consumed locally with only `bridge.ingress` producing it — surfaces as `events.system.subject.no_publisher` rather than failing silently.

This pattern has been exercised as a real WAN link between two physically separate hosts, not just as a design. What is **not** built: NATS leaf-node partition tolerance, control-agent federation across hosts (a JetStream-KV desired state), replica counts or worker pools, cross-host placement, and history anti-entropy after a long partition heals. A control agent that crashes outright (as opposed to a clean shutdown) currently orphans its supervised children — a pid-registry reaper is deferred, not built.

## Operating posture

A Tectum deployment runs against a live stack and does not fake liveness: if a dependency is down, the node that needs it raises a real error rather than degrading silently. A deployment typically depends on:

- A **NATS** broker, reachable from every host that runs a node.
- A **JMFTS** document store, for nodes that read or write durable memory.
- One or more **LLM inference endpoints**, for agent nodes. Endpoint addresses and model names are deployment-specific configuration, not part of Tectum itself.
- **Piper** (or another TTS) for any `effector.speech` instance, falling back further down the chain (e.g. `espeak-ng`, then a no-op recorder) rather than blocking on an unavailable voice.

None of these addresses belong in a schema document or in source control — they're read from environment configuration at node startup, and a missing one is a startup failure rather than a surprise mid-run.

## Dev loop

```bash
python3 -m venv .venv && ./.venv/bin/pip install -e '.[dev]'
./.venv/bin/python -m pytest -q                  # unit tier (no services)
./.venv/bin/python -m pytest -q -m integration   # live-stack tier (skips if unreachable)
```

See the [Reference](reference.md) page for the schema document format, the event envelope, and node lifecycle hooks; see the [Cookbook](cookbook.md) for worked examples built from schemas that actually ship in the tree.
