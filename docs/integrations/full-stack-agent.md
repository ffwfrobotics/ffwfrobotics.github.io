---
title: "The FFwF Full Stack Agent"
kind: "integration"
summary: "All three at once: Tau agents on a Tectum substrate with JMFTS as shared memory."
projects: [tectum, tau, jmfts]
status: "draft"
---

# The FFwF Full Stack Agent

Each pairwise page covers one seam. This page covers the shape that only
exists with all three running: Tectum routes events between nodes, Tau is
the mind inside an agent node, and JMFTS is the one memory every node reads
and writes. The claim worth examining is not that the three compose — most
software composes — but that each one holds a boundary the other two depend
on. Tau keeps the model away from the machinery; JMFTS makes every write
durable and searchable; and Tectum keeps every hand-off on the bus, where it
can be rerouted, observed, or replayed without any component's cooperation.

!!! note "Draft"
    Read [Tectum + Tau](tectum-tau.md) and [Tau + JMFTS](tau-jmfts.md)
    first — this page assumes both seams and describes only what the third
    combination adds. Status of each claim is at the
    [end of the page](#status).

The smallest complete instance fits in one sentence: a phone's
push-to-talk turn rides a Tectum subject to a τ-backed agent whose memory
is a reflex over JMFTS, and the answer rides a device-scoped subject back
to the phone that asked. The schema that wires all of it,
`edge_asr_memory.yaml`, names two nodes.

## Who owns what

- **Tectum** owns routing, lifecycle, and the seams: which subjects wake
  the agent, where its speech goes, who restarts it, and the configuration
  handed to everything below.
- **τ** owns the conversation: the persistent session, the extension hooks,
  and the one-turn-at-a-time door every input passes through.
- **JMFTS** owns what outlives the conversation: the memory subtrees,
  vector search over them, and the timestamps.

The demonstration is what each part does *not* know. τ has no concept of a
device token. JMFTS has no concept of a turn. The phone knows nothing but a
socket. Tectum is where those facts live: the memory extension learns its
JMFTS roots, its NATS URL, and its agent identity as configuration rendered
into [`--ext-config` flags](tectum-tau.md#extensions-are-configuration-not-code)
— not as imports, and not as decisions the model gets to make.

## One turn, whole stack

The most complete assembly in the tree is the handset memory agent. One
button press on a phone becomes:

1. The Android app streams its own on-device transcript to `audio.handset`,
   which publishes a sensation event. The button was the wake signal — no
   wakeword gateway, no echo gate, because a phone cannot overhear itself.
2. The active schema binds that subject to the agent node. Nothing else
   hears it; that isolation is a routing fact, not application logic.
3. Before the model sees the utterance, the memory reflex searches the
   agent's JMFTS trees and threads what it finds ahead of the turn.
   Retrieval is a reflex, not a decision — it never competes with the
   conversation for the model's reasoning budget.
4. The τ subprocess takes the turn. Speakable prose goes out on the
   device-scoped `speak` subject; text that should not be read aloud goes to
   the reply rail, marked and reasoned.
5. On cadence, a forked sub-agent reviews the conversation and deposits what
   is worth keeping into the memory tree — deduplicated, under the agent's
   own identity.

Every arrow in that sequence is an event with a subject. Any of them can be
watched from a monitoring client, bound to an extra consumer, or carried
across a network boundary, without the agent knowing. The schema side of
this one is the Tectum Cookbook's
[push-to-talk agent on a second device](../tectum/cookbook.md#add-a-push-to-talk-agent-on-a-second-device).

What puts the τ session on the bus in step 4 is the `nats_bus` extension. It
is declared `TOUCHES_BUS`, so a run that loads it must declare
`bus_available=True` — a session cannot reach the substrate by accident. From
there the agent's outbound verbs — `speak`, `journal_append`, `jmfts_write`,
`delegate` — are ordinary τ tools that publish command-DAG events, and
`agent.jmfts_operator` picks up whatever is delegated to it over the same
tree ([Tectum + JMFTS](tectum-jmfts.md#the-tree-gets-its-own-agent) has its
verbs and wake modes).

## JMFTS is the only durable thing here

Every event on the bus carries `ttl_ms` and is expected to expire. τ's
context window compacts. Node processes restart on a supervision policy. The
JMFTS tree is the one store that outlives all three, and each system routes
its survivors into it: τ sessions (`--store jmfts`, made findable by
enrichment), journal entries (via the effector), and facts (via curation into
the triple store).

The consequence is structural: the deployment's identity lives in its corpus,
not its wiring. Schemas can be swapped binding by binding, agents restarted,
models replaced — and the assembled thing still remembers, because the tree
does. Three systems' worth of state, one durability story, and it is
JMFTS's.

## Memory as a reflex, not a tool

`tau_ext.memory_reflex` is the load-bearing piece of steps 3 and 5, and its
two behaviors are deliberately not tools — the model cannot call them, and
cannot skip them:

- **Reflexive retrieval.** On every user turn, before the model sees the
  utterance, the extension queries JMFTS vector search against each
  configured memory root and threads anything above threshold into the
  conversation ahead of the utterance. Every search is recorded in the
  session even when nothing clears the threshold — a similarity floor
  nobody can see is a filter nobody can calibrate, and the record is the
  only data that can set the threshold honestly.
- **Reflexive memorizing.** Every N user turns, an evaluator runs over the
  recent conversation as a forked sub-agent and deposits what is worth
  keeping, deduplicating against what is already stored. The fork matters
  twice over: τ's branching gives the evaluator the full conversation
  without touching it, and remembering spends its own model budget on its
  own branch — never the conversation's.

Both behaviors report on the bus — `…out.recall.<device>` and
`…out.memorize.<device>` — as records of work already done, never as
requests. Reports keep the routing graph acyclic; a memory system that
*asked* the substrate for permission would be a cycle waiting to happen.
And because the reports are ordinary events, "what did the agent remember,
and when" is a question for the event log, not for the model. The reports
exist because τ's RPC surface has no verb that would let the owning node
see a recall or a deposit from outside — `get_messages` returns the flat
terminal message array, with no branch lane and no `customEntry` in it — so
the facts have to leave from inside the session, and they leave as events.

Stated the other way round: **the substrate can watch the agent remember,
and cannot interfere with it.** Every recall and every deposit is on the
bus, timestamped and correlated, available to any logger or monitor, and
there is no subject to publish to that would alter the reflex.

## One audit thread, end to end

A turn of the full stack can be reconstructed after the fact, across all
three systems, from records each system was already keeping:

- The event envelope names which schema produced and routed every event
  (`produced_by_schema` / `routed_by_schema`), and `binding_id` threads the
  flow from transcript to action.
- The τ session tree contains a `customEntry` for every reflex search — the
  query, the scores, how many results passed the floor — *even when nothing
  was injected*, so the memory filter's own behavior is in the transcript.
- The journal ack subject carries the `binding_id` of the flow that caused
  the write, tying the durable record to the exchange that produced it.
- The triple store is bitemporal, so "what did the deployment believe at the
  moment it said that" is a query, with supersession keeping the corrected
  belief and the correction both.

No one project provides this thread. It exists because JMFTS's records are
permanent and addressable, and the other two systems stamp their correlation
ids onto everything that flows toward them.

## Memory with an owner

JMFTS holds one tree for the whole deployment — workspace, journal,
knowledge, identity — and every agent addresses it with its own bearer
token, which *is* its principal. Grants are per-subtree; a document an agent
was not granted does not exist for it, in search results and tree walks
alike. (JMFTS's [Reference](../jmfts/reference.md#data-model) has the
`principals` / `api_tokens` / `access_grants` model and the access-control
root rule.)

This is a three-way property, and it takes all three systems to hold:

- JMFTS enforces the grants at the store, so no prompt discipline is
  involved.
- Tectum runs each agent as its own node with its own credential, so two
  agents are two principals rather than one process wearing two hats.
- Tau's node posture gives the model no shell, so an agent cannot disclose
  the credential that defines it.

Remove any one and the property collapses to trust: shared store access,
shared process identity, or a model that can `printenv` its own key.

## Many minds, one workspace

Multi-agent deployments share state through an append-only, multi-writer
workspace subtree. Nobody holds a lock: writers append records, records may
supersede earlier ones, and the current view is computed at read time. A
fast responder and a slow curator coordinate through it with two asymmetric
edges — the fast node *pulls* the latest view on its own next turn, and the
slow node's completed write *pushes* a wake-up event so an answer that lands
between turns does not sit unspoken. The schema pair is in the Tectum
Cookbook:
[Split an agent into a fast responder and a slow curator](../tectum/cookbook.md#split-an-agent-into-a-fast-responder-and-a-slow-curator).

The division of labor is enforced by capability, not by instruction. In the
fast/slow schemas the slow tier has no speak verb at all — its silence is
structural. The deepest variant swaps the slow tier for a knowledge-tree
operator: an agent whose whole job is answering, curating, and maintaining
the shared memory that every other agent merely uses.

## Cognition at home, ears anywhere

The stack's confirmed end-to-end run is also its best demonstration of what
the routing layer buys. A battery-powered board carries the microphone,
speech recognition, and the speaker; the models and the entire JMFTS tree
stay on the home machine; two
[bridge nodes](../tectum/cookbook.md#bridge-two-substrates-over-an-unreliable-link)
carry named subjects across an SSH tunnel between them. Only text crosses
the link — no audio, and no memory.

Each side's schema declares its own half of the crossing, so the contract is
checkable offline by comparing two YAML files. And because the cognition
schema on the home side is byte-identical whether its counterpart is the
real board or a keyboard-driven test client, "develop at a desk, deploy on a
backpack" is a schema swap, not a code path.

## Swap any layer without telling the others

The same substitutability runs through the whole stack, and it is the
practical reason the event contract earns its ceremony:

- **Swap the edge.** A
  [test TUI](../tectum/cookbook.md#drive-the-loop-without-a-microphone)
  stands in for the microphone and speaker by publishing and consuming the
  same subjects. The agents cannot tell.
- **Swap the mind.** Agent nodes have run two different harnesses behind
  the same verbs; moving from shell-shim tools to τ's schema-constrained
  tools changed the safety properties without changing a single binding.
- **Swap the memory posture.** The same JMFTS instance serves reflexive
  recall, journal appends, and — through
  [Tau's own store](tau-jmfts.md#the-conversation-is-the-corpus) — entire
  conversation histories, each under a different subtree and usetype
  namespace, searchable together or scoped apart.

## Lessons that needed all three

Each pairwise seam contributed one fact that only surfaced with everything
running together:

- **The τ seam: evaluation runs off the turn.** A τ session takes one turn
  at a time, and an extension hook that awaited the evaluator inside the
  turn made τ refuse the *next* user utterance — `-32000 a turn is already
  in flight`. Measured, it broke the handset agent's own summarize retry and
  swallowed the following utterance. So the hook captures the conversation
  position and returns immediately, one evaluator runs at a time, and an
  overlap is reported as `evaluator_busy` rather than silently queued.
- **The JMFTS seam: score, not rank.** The reflex queries `/search/vector`,
  deliberately not the hybrid router. Hybrid fuses by rank, so measured
  against the live store, relevant and fabricated-nonsense queries returned
  the same five score values; vector similarity separated them (0.46–0.54
  against 0.22–0.33 on the same subtree). Absolute cosine scores are worse
  rankers and better gatekeepers, and a reflex with no human in the loop
  needs the gatekeeper. JMFTS states the same rule from its own side:
  [gate on a score only when the method returns a real one](../jmfts/cookbook.md#gate-on-a-score-only-when-the-method-returns-a-real-one).
- **The Tectum seam: exclusivity is a runbook rule.** `agent.edge_asr` and
  `agent.edge_asr_memory` publish the same speak rail, and the substrate
  will happily deliver both if both schemas are active. Activate one, never
  both — the router cannot know which one you meant.

## Failure modes that need the full stack to exist

- **Durably written is not findable.** The journal ack means the commit
  landed; the embedding backfills later. A reflexive recall on the very next
  turn can miss a memory deposited seconds ago. This is invisible in any
  single system — it takes a write effector and a read reflex sharing one
  tree to surface it. The write side is on
  [Tectum + JMFTS](tectum-jmfts.md#the-ack-means-durably-written-and-only-that).
- **Substrate timeouts against retrieval latency.** A grounded synthesize can
  run about 180 seconds on a local model; `loose_loop3` raises the operator's
  wall clock to 220 seconds rather than letting supervision kill an honest
  slow answer. Any schema that adds a retrieval-backed node inherits this
  tuning obligation.
- **Lifecycle hooks that never fire** *(design note, not a shipped fix)*. The
  `enrich` pass that makes τ conversations findable keys on
  `session_shutdown` — correct for an interactive session, and never
  triggered by a bus-resident responder whose session lives for days. A
  long-lived deployment needs enrichment on a cadence or per-turn
  increments, not on a lifecycle edge. Until then, the most durable store in
  the stack holds conversations its own search cannot yet see.
- **Two publishers, one subject.** The variant pair
  [above](#lessons-that-needed-all-three) is the shipped instance, but the
  hazard is general: any two schemas that publish one rail answer every
  turn twice. The substrate cannot know this is wrong — the schema author
  must.
- **Acks are dialects.** Different effector families shape failure
  differently (`ok: false` against `status: refused`), and the tool layer
  reads both; a new effector that invents a third dialect fails silently at
  the seam.
- **Invisible memory is a feature until it isn't.** JMFTS excludes entity
  and summary documents from search by default; an agent that deposits
  distilled knowledge into those usetypes and then searches for it will not
  find it unless the query says so.
- **Reflex loops.** Anything that writes memory in reaction to reading it
  is one binding away from a cycle. The shipped design avoids this by
  publishing memory activity as past-tense reports nothing binds to — a
  convention future schemas must keep on purpose.

## Growing it

The handset loop is the full stack at its smallest: one device, one agent,
one memory. The same substrate already carries the room stack — streaming
ASR, wakeword gating, the fast/slow agent pairs — and a bridged second
substrate over a WAN. The composition the schemas make available is the
interesting part: pointing another agent's memory roots at the subtrees the
handset agent deposits into is configuration, not code, because every party
meets the others at a subject or a subtree and nowhere else.

What has actually been run together is the handset loop. The room stack's
agents still ride the older dispatch backend, so "the whole fleet on τ" is
a migration in progress, not a description of the deployment.

## Status

The substrate, the bridge, and the store are live-validated; the fast/slow
workspace pattern has run under text injection; the full handset memory
assembly passes its offline suites (`test_tau_node.py`,
`test_tau_backend.py`, `test_memory_reflex.py`, `test_handset_bus.py`),
with live operation so far attested by run notes rather than automated
checks. The τ-on-the-bus responder is exercised end to end by
`scripts/tectum_responder.py` in the τ source tree; the operator cohort is
an A/B experiment (`praxis/loose_loop3.yaml`); the enrichment lifecycle
note above is a design note, not a shipped fix. The WAN bridge is the one
piece of this stack with an independently confirmed live
incident-and-fix.

This page describes the one deployment shape all three projects are
converging on, at the honesty level each component has earned so far — not
a certification that the whole stack has run unattended.
