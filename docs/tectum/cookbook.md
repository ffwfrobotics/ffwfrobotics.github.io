---
title: "Cookbook"
category: "cookbook"
status: "draft"
---

# Tectum — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific Tectum jobs, each built from a schema that actually ships in the tree rather than a hypothetical. Tectum's `praxis/` directory holds many independently-tried schemas — most of these are experiments, not a single evolving design, so each recipe below says plainly whether the pattern is the stable boot default or a try that worked once and stopped there.

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
