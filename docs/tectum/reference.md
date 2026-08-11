---
title: "Reference"
category: "reference"
status: "draft"
---

# Tectum — Reference

<p class="axis">Cognition × Application</p>

Schema document format, node lifecycle hooks, subject naming rules, and the event envelope.

## The event envelope

Every message on the bus is a `TectumEvent`. Fields:

| Field | Type | Meaning |
|-------|------|---------|
| `event_id` | UUID | Identifies this envelope. A replay of the same logical event gets a fresh `event_id`. |
| `event_type` | str | Dotted namespace string, e.g. `vision.frame`, `speech.utterance`. |
| `source` | str | Producer identity, e.g. `camera.front`, `agent.planner`. |
| `timestamp` | datetime (UTC) | Wall-clock production time. |
| `sequence_number` | int | Monotonic counter scoped to `source`, for drop detection and ordering. |
| `ttl_ms` | int | Producer's hint for how long the event stays actionable. A sink may drop an expired one. |
| `payload` | dict | Type-specific body; schema is implied by `event_type`. |
| `origin_node` | str | The host that first emitted the event. |
| `hops` | list[str] | Ordered list of nodes/agents that have processed the event. |
| `seen_by` | set[str] | Subscribers that have acknowledged it. |
| `binding_id` | str \| None | Correlates events in the same logical flow (e.g. perceive → plan → act), preserved across hops. |
| `produced_by_schema` / `routed_by_schema` | str \| None | Which schema produced/routed the event, for audit and replay. |
| `expectation` / `residual` | dict \| None | Predictive-routing fields: what the producer expected next, and the post-hoc difference from what actually happened. |
| `audit` | dict \| None | Open dict for tracing and metrics. |

Events are immutable in spirit: a node that transforms one produces a new event with `hops`/`seen_by` reflecting its own identity, rather than mutating the original in place. Wire format is JSON over NATS (`to_json_bytes` / `from_json_bytes`).

## Subject namespace

The dotted prefix of every subject encodes which DAG it belongs to:

```
events.sensation.*   bottom-up: sensors -> filters -> ...in   (workspace is a TARGET)
events.workspace.*   the workspace layer: <agent>.in (dispatch), <agent>.out.<tool>
events.action.*      cross-effector / world-action coordination
events.system.*      Tectum's self-report: schema/node/substrate lifecycle
events.journal.*     durable-record emissions (effector write acknowledgements)
```

The sensation DAG is strictly bottom-up; the command DAG is strictly top-down (an agent-side wrapper publishes `events.workspace.<agent>.out.<tool>`, an effector consumes it). A subject belongs to at most one DAG.

**Device token.** A command-DAG subject may carry an optional fifth token: `events.workspace.<agent>.out.<tool>[.<device>]`. An agent that serves one specific device (a phone, say) stamps that token on everything it emits, and a schema binds the concrete deviced subject to the effector that reaches that device. The token's absence is not a default device — it means the agent has no device dimension. A binder that wants every device-scoped rail of one tool subscribes `…out.<tool>.>`, which does **not** also match the undeviced `…out.<tool>`; undeviced and device-scoped rails are deliberately different rails.

**Control plane.** `actions.praxis.*` is distinct from `events.*`: `events.*` is observation (anyone may watch), `actions.praxis.*` is actuation — the per-host control agent driving node processes. Keeping the trees separate lets a node subscribe its own control channels without pulling the whole observation stream.

| Builder | Produces |
|---------|----------|
| `agent_in(agent_type)` | `events.workspace.<agent_type>.in` |
| `agent_out(agent_type, tool, device=None)` | `events.workspace.<agent_type>.out.<tool>[.<device>]` |
| `agent_out_wildcard(agent_type="*")` | `events.workspace.<agent_type>.out.>` |
| `agent_out_device_wildcard(agent_type, tool)` | `events.workspace.<agent_type>.out.<tool>.>` |
| `praxis_bind(node_name)` | `actions.praxis.bind.<node_name>` |
| `praxis_exit(node_name)` | `actions.praxis.exit.<node_name>` |
| `journal_ack(kind, binding_id)` | `events.journal.<kind>.<binding_id or "none">` |

## Node manifest and lifecycle

A node declares its contract once, at the `@tectum_node` decorator that wraps its class — there is no sidecar YAML to drift from:

| Manifest field | Meaning |
|---|---|
| `name` | The node's registered name, e.g. `effector.speech`. |
| `substrate` | Which substrate this node belongs to. |
| `subscribes` | Subject patterns this node is designed to handle — a descriptive contract the schema loader validates bindings against, not a hard dependency on a publisher existing. |
| `publishes` | Subject patterns this node may emit. |
| `resources` | Advisory config, e.g. `llm_endpoint`, `llm_model`. |
| `restart_policy` | `never` \| `on_failure` \| `always`. |
| `delivery` | `queue` (a NATS queue group — many processes of this node form a worker pool, each event handled once) or `broadcast` (every instance sees every event; for taps/loggers). |
| `concurrency` | How many events one process handles at once. `1` serializes on a shared resource (an audio device, a model session); more runs that many `on_event` handlers concurrently. |

Importing a node module fires the decorator and registers the manifest — nothing else expensive is allowed to happen at import time. Heavy dependencies (model clients, `nats`, `torch`, transformers, …) are imported inside `setup()`, never at module top, so the scan pass can read every node's manifest offline without paying import or model-load cost.

A node implements three lifecycle hooks:

```python
async def setup(self) -> None: ...      # acquire resources, open connections
async def on_event(self, event: TectumEvent) -> None: ...  # handle one delivered event
async def teardown(self) -> None: ...   # release resources
```

Nodes do not subscribe to the bus themselves. Bindings live in Praxis: the activator subscribes each binding's `from` subject and delivers matching events to the target node's `on_event`.

## Praxis schema document

```yaml
name: listening_mode
version: 1                 # authoring metadata only (no enforcement yet)
author: hand                # who/what authored this schema
substrate: home              # advisory home substrate for the schema
immutable: false            # true => only operator-class callers may deactivate
ttl: forever                # forever | <seconds>
description: "..."
requires:
  nodes: [audio.gateway, agent.persona_reflection, effector.speech]
bindings:
  - from: events.sensation.audio.transcript
    to: audio.gateway
  - from: events.sensation.audio.filtered
    to: agent.persona_reflection   # 'agent.X' is just a node name
audit:
  journal_threshold: 0.5
```

A binding delivers events matching `from` to a **node** — `to` must be a registered node name listed in `requires.nodes`. Subject-to-subject re-publish bridges and inline payload predicates are deliberately not part of this model: payload filtering belongs in filter nodes, and behavior belongs in nodes. `predicates` (system-event reactions) are parsed but not yet acted on.

## CLI

```bash
tectum scan                       # offline node graph (delivery/slots too)
tectum status                     # live-stack reachability + control/supervision graph
tectum up                         # control agent + supervised node fleet, hold until Ctrl-C
tectum up --no-supervise          # force-fork every node, no supervision

tectum --node effector.speech     # one node as its own process; --module/-e for custom nodes

tectum schema validate praxis/listening_mode.yaml   # offline type-check
tectum schema apply    praxis/listening_mode.yaml   # apply (spawns required absent nodes)
tectum schema unapply  listening_mode               # refused if immutable
tectum schema list                                  # active schemas + binding refcounts
tectum node list                                    # instances, heartbeat age, slots, supervision
tectum node restart    effector.speech              # real restart (supervisor respawns it)
tectum node stop       effector.speech              # stop + suppress respawn
tectum node spawn      effector.speech              # bring a required node up from its spec
tectum spec list                                    # launch specs the agent can respawn from
```

See the [DevOps Manual](devops.md) for how these fit into a running deployment, and the [Cookbook](cookbook.md) for worked schema examples.
