---
title: "Cookbook"
category: "cookbook"
status: "draft"
---

# Tectum — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific Tectum jobs. Most are built from a schema that actually ships in the tree rather than a hypothetical; a few are patterns assembled from shipped substrate mechanics that no single schema wires end to end, and those say so. Tectum's `praxis/` directory holds many independently-tried schemas — most of these are experiments, not a single evolving design — so each recipe below states plainly whether it is the stable boot default, a try that worked once and stopped there, or a pattern the substrate supports that is waiting for its schema.

## Wire a wakeword-gated agent loop

**Status: stable — this is the boot default most Tectum deployments ship with.**

The smallest complete loop: a transcript comes in, a wakeword filter decides whether it was addressed to the agent, the agent judges the event and may speak, and a durable record gets written before the turn is considered finished.

```yaml
name: listening_mode
requires:
  nodes:
    - audio.gateway
    - agent.persona_reflection
    - effector.speech
    - effector.journal_append
bindings:
  # sensation DAG: transcript -> wakeword filter -> agent dispatch
  - from: events.sensation.audio.transcript
    to: audio.gateway
  - from: events.sensation.audio.filtered
    to: agent.persona_reflection
  # command DAG: agent tool wrappers -> effectors
  - from: events.workspace.persona_reflection.out.speak
    to: effector.speech
  - from: events.workspace.persona_reflection.out.journal_append
    to: effector.journal_append
```

`audio.gateway` does a plain substring test against a configured wakeword — for example, an assistant named "Kevin" only reacts to a transcript that actually contains "kevin". Everything before the wakeword check is sensation; everything from `agent.persona_reflection` onward is workspace. Apply it:

```bash
tectum schema validate praxis/listening_mode.yaml
tectum schema apply    praxis/listening_mode.yaml
```

Activating this one file brings up all four nodes (RAII ref-counted — each is reused if another active schema already needs it) and installs all four bindings in one step.

## Split an agent into a fast responder and a slow curator

**Status: experimental — one try (`thinking_fast_slow`) among several later attempts at the same idea. Landed and ran, not the current boot default.**

A single LLM call has to trade latency against depth. This pattern splits the work across two agent nodes on the same underlying model instead: a **fast** node that reads the current view of shared state each turn and either speaks immediately or delegates, and a **slow** node that only runs on delegation, does one thinking-on call, and writes its answer back rather than speaking directly.

```yaml
requires:
  nodes:
    - agent.responder
    - agent.workspace_curator
bindings:
  # fast -> slow delegation
  - from: events.workspace.responder.out.delegate
    to: agent.workspace_curator
  # slow -> fast PUSH: a landed answer wakes the responder so it can be voiced
  # promptly, instead of waiting for the next turn to poll for it
  - from: events.workspace.workspace_curator.posted
    to: agent.responder
  - from: events.workspace.responder.out.speak
    to: effector.speech
```

The two directions are asymmetric on purpose. The fast node PULLs an answer from shared state on its own next turn if nothing pushes one sooner; the slow node's completed write also PUSHes a wake-up so an answer that lands between turns doesn't sit unspoken. Termination is behavioral — the fast node decides whether to speak — not structurally enforced, so a fast node can re-delegate on a push turn without deadlocking anything.

Shared state here is append-only and multi-writer: the slow node's write becomes visible to readers as soon as it lands, and nothing blocks the fast node's next turn waiting for a consolidation pass to finish. If your deployment needs read-after-write consistency stronger than "eventually visible, never gated," that's a property to design for explicitly — it isn't one this pattern gives you for free.

## Add a push-to-talk agent on a second device

**Status: experimental, recent. Runs against the stable core's persona/tool pattern but is not the boot default.**

A handset app that already has its own push-to-talk button doesn't need a wakeword — someone pressing the button *is* the wake signal. This pattern gives such a device its own sensation rail, skipping the wakeword gateway entirely, and its own command rail back, using the device token described in [Reference](reference.md#subject-namespace).

Bring up the transport on its own first — it's additive and does nothing without an agent behind it:

```yaml
# praxis/handset.yaml
requires:
  nodes: [audio.handset]
bindings:
  - from: events.workspace.*.out.reply.handset
    to: audio.handset
  - from: events.workspace.*.out.speak.handset
    to: audio.handset
```

Then wire an agent to actually answer it:

```yaml
# praxis/edge_asr.yaml
requires:
  nodes: [audio.handset, agent.edge_asr]
bindings:
  # the button was the wake signal — no gateway, no phonetic resolver, no echo gate
  - from: events.sensation.handset.turn
    to: agent.edge_asr
  - from: events.workspace.edge_asr.out.reply.handset
    to: audio.handset
  - from: events.workspace.edge_asr.out.speak.handset
    to: audio.handset
```

A second device is a copy of this pattern: a new sensation subject, a matching device-scoped output subject, and a new agent node — none of it touches the room-facing agents or their subjects, because the device token keeps the rails disjoint at the routing layer rather than in application logic.

**Adding memory:** a variant schema (`edge_asr_memory`) swaps in an agent that also runs a memory step before and after each turn — searching prior journal entries for relevant context before responding, and periodically evaluating whether the conversation was worth remembering. That evaluation is not something the model can choose to skip or call as a tool; it runs on a fixed cadence outside the model's own reasoning budget, specifically so remembering doesn't compete with the conversation for that budget. Run one variant or the other, never both — both publish the same output subject, and activating both would answer every turn twice.

## Bridge two substrates over an unreliable link

**Status: experimental, but exercised as a real link between two physically separate hosts, not just a design.**

When part of a deployment runs somewhere the rest can't reach directly — different network, different host entirely — two nodes represent the boundary explicitly instead of leaving it to broker reach: `bridge.egress` (a sink; ships specific named subjects across the link) and `bridge.ingress` (a pure source, like a hardware sensor node — it produces from the far side, so nothing binds to it locally).

Each side of the boundary declares only its own half of the contract:

```yaml
# the ears-and-mouth side: sends what it heard, receives what to say
requires:
  nodes: [bridge.egress, bridge.ingress]
bindings:
  - from: events.sensation.audio.resolved.clean
    to: bridge.egress
  - from: events.action.speech.completed.>
    to: bridge.egress
  # bridge.ingress takes no binding — it's a source, not a target
```

```yaml
# the cognition side: sends what to say, receives what was heard
requires:
  nodes: [bridge.egress, bridge.ingress]
bindings:
  - from: events.workspace.*.out.speak
    to: bridge.egress
  # bridge.ingress takes no binding here either
```

The two halves need to agree: one side's egress set is the other side's expected ingress, and vice versa. A subject bound to `bridge.egress` on one side with nothing consuming it on the other is a broken contract — and it's checkable offline, by comparing the two schema files' bindings, before ever deploying either half.

Each side also states a quality of service per subject — durable, idempotent, or fresh-only. A "what to say" event that arrives late is worse than one that never arrives at all, so that crossing is fresh-only: stale on arrival means dropped, not spoken late.

## Drive the loop without a microphone

**Status: stable tooling — `harness_text.yaml` and the `parley-nats` injector ship in the tree and were the daily drivers for the `loose_loop` experiments.**

Nothing in the sensation DAG checks that a transcript came from a microphone. A subject is a contract, not a provenance claim, so the whole physical edge — mic, streaming ASR, resolver, TTS — can be swapped for a keyboard without the cognition schemas noticing.

The one-shot version is two scripts:

```bash
# stand in for the whole mic -> STT -> resolver -> echo_gate chain
python scripts/heard.py --speaker john "Kevin, are you there?"

# stand in for an agent's out.speak rail; waits for the completion ack and prints it
python scripts/say.py "Hello from the other side."
```

The full version is `parley-nats`, a terminal UI that injects typed utterances onto `events.sensation.audio.resolved.clean`, renders the `events.>` scrollback with toggleable categories, and — the detail that keeps it honest — publishes the `events.action.speech.completed.<binding_id>` ack itself. The half-duplex gate that stops an agent from talking over its own ears behaves exactly as it does in a real room, because from the agents' side there is no way to tell the room is fake.

`harness_text.yaml` is the `thinking_fast_slow` cognition with the audio front end and TTS left out: the same agent pair, the same workspace wiring, meeting the world at a subject instead of a speaker. That is the general trick, not a test hack — edges and cognition are separate schemas that meet at a subject, so "run the same brain against a different world" is an apply, not a port.

## Trace one turn across the fleet

**Status: pattern — built from the event envelope and the ack rails, both untouched since the first commit. The trace is a filter over the event log, not a deployment.**

Every event carries a `binding_id`, preserved across hops and re-stamped by agent nodes at each turn, so one causal chain — utterance in, delegation, speech out, journal write — shares one id no matter how many processes and hosts it crossed. The acknowledgements are addressed by it too: a durable write acks on `events.journal.<kind>.<binding_id>`, a finished utterance on `events.action.speech.completed.<binding_id>`.

Tracing a turn end to end is therefore a filter, not an instrumentation project. `system.event_log` is a broadcast-delivery tap — it sees everything without consuming anything from a queue-delivery worker pool — and one additive schema points it at the whole bus:

```yaml
requires:
  nodes: [system.event_log]
bindings:
  - from: events.>
    to: system.event_log
```

Filter the log by one `binding_id` and the whole turn lines up in order. The envelope also stamps `produced_by_schema` and `routed_by_schema` on the way through, so "why did this event fire" is answered from the record itself rather than by re-reading YAML — the schema that caused the routing rides along inside the event it routed.

## Shadow-run a candidate agent on live traffic

**Status: pattern — every mechanism is shipped; the nearest shipped precedent is `loose_loop3`, which A/B'd its slow tier by swapping one node in an otherwise identical schema.**

A binding delivers a subject to a node, and nothing requires an agent's output subjects to be bound anywhere. Those two facts make a shadow deployment a routing decision rather than a codebase feature:

```yaml
# additive; the incumbent's schema is untouched
requires:
  nodes: [agent.candidate, system.event_log]
bindings:
  # the candidate hears exactly what the incumbent hears
  - from: events.sensation.audio.resolved.clean
    to: agent.candidate
  # its output goes to the record, not the room
  - from: events.workspace.candidate.out.>
    to: system.event_log
```

Two bindings on one sensation subject deliver to both agents, so the incumbent's traffic is unchanged. The candidate's speech reaches no speaker, but its `out.*` and `.reply` rails land in the log, timestamped and correlated against the incumbent's answers to the same utterances. Output rails are namespaced by agent type, so the shadow cannot collide with the incumbent by construction. Promotion afterward is a swap of two small schemas, not a deploy.

The honest caveat: a shadow burns real model capacity on every turn. It is silent, not free.

## Swap an agent under a live device

**Status: pattern — grounded in the activator's ref-counting (exercised by `tests/test_activator_raii.py`) and the shipped `edge_asr` / `edge_asr_memory` pair.**

A node lives exactly as long as at least one active schema needs it. That makes the *order* of an apply/unapply pair a real operational choice, because the two orders protect different things:

- **Overlap to protect shared nodes.** `edge_asr.yaml` and `edge_asr_memory.yaml` both require `audio.handset`. Apply the new schema before unapplying the old and the handset's ref-count goes 1 → 2 → 1 across the swap: the phone's connection never drops, because the count never touches zero.
- **Gap to protect exclusive rails.** Both agents publish `…out.speak.handset`, so while both schemas are active, every turn is answered twice. If a doubled voice is worse than a moment of silence, unapply first and accept the gap.

The substrate supports both orders; it does not choose for you. Which failure is worse — a dropped connection or a doubled answer — is a fact about your deployment, and it belongs in your runbook, not in the routing layer.

## Put code where a model is tempting

**Status: stable nodes — `audio.resolver` and `audio.echo_gate` ship in the tree and are wired by `persona_live_test.yaml`.**

Two shipped nodes do work that reads like it needs a model, with none:

- `audio.resolver` snaps misheard words to a closed per-conversation vocabulary by phonetic match (metaphone plus jaro-winkler), backed by a seeded alias list for the misses phonetics cannot reach. "cavin" resolves to the agent's name by metaphone; "heaven" and "coven" are H- and C-initial, phonetically unreachable from "kevin", and resolve only because the node ships them as seeded aliases. Both paths are microseconds per word, deterministic, with no inference endpoint — but they are two mechanisms, and a new mishearing may need the seed rather than the matcher.
- `audio.echo_gate` solves self-hearing by content instead of timing: it buffers what `effector.speech` actually said and drops any incoming utterance that matches it, emitting both `…resolved.clean` and `…resolved.suppressed` so every suppression is observable rather than silent.

The substrate point is where these live: each is a node in the rail, not a patch inside a consumer. The echo gate sits *before* the fan-out, so every downstream listener — however many schemas bind that subject — sees the cleaned stream. "Not every event needs an SLM" is a topology decision here, made once, in one place.

## Attach another worker to a hot node

**Status: stable runtime feature — queue delivery, standalone `tectum --node`, and slot-aware heartbeats all ship.**

A schema names nodes, not instances. A node declared with `delivery: queue` forms a NATS queue group: every process registered under that name is a member, and each event is handled once, by whichever member has a free slot. So when one node becomes the bottleneck, capacity is a process count:

```bash
tectum --node effector.journal_append    # from any host that reaches the broker
```

The new process registers, heartbeats with its load, and joins the group — no schema change, no config edit, no restart of anything already running. `tectum node list` shows the instances, their heartbeat age, and their slots. The inverse setting, `delivery: broadcast`, is for taps and loggers that must see every event; the two delivery modes together are why a fleet can grow workers without ever growing duplicates.

## Share one prompt cache across every agent

**Status: stable mechanism — `persona.py` composes every agent's system prompt persona-first for exactly this reason.**

Multi-agent topologies like `thinking_fast_slow` run several agent nodes against one inference server. Every one of those agents' system prompts begins with the same byte-identical persona prefix, with the per-agent material after it — so the server's prefix cache (llama.cpp's KV cache, in the deployments in the tree) stays warm no matter which agent dispatches next. The persona is shared identity and shared cache at once: N agents, one prefix computation.

The discipline that makes it work is boring and strict: the shared prefix must be byte-identical, so it is composed from one file, first, always — never templated per-agent.
