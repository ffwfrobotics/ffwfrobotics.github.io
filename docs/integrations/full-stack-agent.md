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


<figure class="dia"><svg viewBox="0 0 680 1180" role="img" aria-labelledby="dia-fsa-t dia-fsa-d"><title id="dia-fsa-t">One turn, whole stack</title><desc id="dia-fsa-d">A tall figure in three grammars. At the top left an Android app hands a push-to-talk turn over a socket to a square Tectum node named audio dot handset, which publishes up onto the rail events dot sensation dot handset dot turn; captions note that the button was the wake signal and that the phone knows nothing but a socket. At the top right the schema praxis slash edge underscore asr underscore memory dot yaml is written out: it requires audio dot handset and agent dot edge underscore asr underscore memory, and binds the handset turn subject to that agent. Below a divider the same panel shows what the node renders per run — dash dash extension PATH and dash dash ext dash config stem dot key equals value, carrying the JMFTS roots, the NATS URL and the agent identity. One arrow leaves the rail and lands on a large square block, agent dot edge underscore asr underscore memory, which has its own credential and gives the model no shell. Inside that block the Tau grammar takes over: a rounded pill named memory underscore reflex sits on the inbound spine before a larger rounded pill named AgentSession, because reflexive retrieval searches JMFTS before the model sees the utterance and is not a tool the model can call or skip. Past the session the spine forks at a filled dot: one limb continues the conversation, the other runs every N user turns into a forked sub-agent that deposits what is worth keeping. A third pill, nats underscore bus, marked TOUCHES underscore BUS, is what puts the session on the substrate at all, and below it the outbound verbs speak and journal underscore append are drawn as boxes, with jmfts underscore write and delegate listed beside them. Below the block, two short rails carry the reflex's past-tense reports, ellipsis out dot recall dot device and ellipsis out dot memorize dot device; no arrowhead leaves either of them, because nothing binds to a past-tense report and the memory loop cannot become a cycle. To their right the rail events dot workspace dot agent dot out dot tool carries the journal write down into effector dot journal underscore append, which writes into a hatched, doubled-outline JMFTS slab named documents, the only durable thing in the picture. A soft line runs back up out of that slab into the agent block: that is slash search slash vector, scoring zero point four six to zero point five four against zero point two two to zero point three three, score rather than rank. The speak verb publishes onto events dot workspace dot edge underscore asr dot out dot speak dot handset, which loops back up the left margin into audio dot handset — the phone that asked. At the bottom the effector's acknowledgement lands on events dot journal dot kind dot binding underscore id. Down the right-hand margin runs the one red mark in the figure: a single red thread tapping three rails — the sensation event, the workspace publish, and the journal acknowledgement — labelled binding underscore id, one thread, three systems.</desc><defs><pattern id="dia-hatch-fsa" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="0" y="16" class="label-role">tectum</text><text x="0" y="470" class="label-role">tau</text><text x="0" y="736" class="label-role">tectum</text><text x="336" y="914" class="label-role">jmfts</text><rect x="60" y="36" width="280" height="28" class="fill-ground stroke-hair"/><text x="200" y="55" text-anchor="middle" class="label-soft">Android app, push-to-talk</text><line x1="200" y1="64" x2="200" y2="83" class="stroke-soft"/><path d="M200 92 L196 83 L204 83 Z" class="fill-ash"/><text x="208" y="80" class="label-soft">socket</text><rect x="60" y="92" width="280" height="32" class="fill-ground stroke"/><text x="200" y="113" text-anchor="middle" class="label">audio.handset</text><text x="72" y="150" class="label-soft">the button was the wake signal:</text><text x="72" y="164" class="label-soft">no wakeword gateway, no echo gate</text><text x="72" y="190" class="label-soft">the phone knows nothing</text><text x="72" y="204" class="label-soft">but a socket</text><line x1="320" y1="124" x2="320" y2="281" class="stroke"/><path d="M320 290 L316 281 L324 281 Z" class="fill-ink"/><rect x="356" y="24" width="280" height="238" class="fill-surface stroke-hair"/><text x="368" y="44" class="label">praxis/edge_asr_memory.yaml</text><line x1="356" y1="54" x2="636" y2="54" class="stroke-soft"/><text x="368" y="74" class="label-soft">requires:</text><text x="368" y="89" class="label-soft">&#160;&#160;nodes:</text><text x="368" y="104" class="label-soft">&#160;&#160;&#160;&#160;- audio.handset</text><text x="368" y="119" class="label-soft">&#160;&#160;&#160;&#160;- agent.edge_asr_memory</text><text x="368" y="134" class="label-soft">bindings:</text><text x="368" y="149" class="label-soft">&#160;&#160;- from: events.sensation.handset.turn</text><text x="368" y="164" class="label-soft">&#160;&#160;&#160;&#160;to: agent.edge_asr_memory</text><line x1="356" y1="178" x2="636" y2="178" class="stroke-soft"/><text x="368" y="196" class="label-soft">rendered by the node, per run:</text><text x="368" y="214" class="label">--extension PATH</text><text x="368" y="230" class="label">--ext-config &lt;stem&gt;.&lt;key&gt;=&lt;value&gt;</text><text x="368" y="250" class="label-soft">JMFTS roots, NATS URL, agent identity</text><text x="60" y="278" class="label-soft">events.sensation.handset.turn</text><line x1="60" y1="290" x2="628" y2="290" class="stroke"/><path d="M628 290 L619 286 L619 294 Z" class="fill-ink"/><line x1="420" y1="290" x2="420" y2="313" class="stroke"/><path d="M420 322 L416 313 L424 313 Z" class="fill-ink"/><text x="438" y="308" class="label-soft">nothing else hears it</text><rect x="60" y="322" width="568" height="382" class="fill-ground stroke"/><text x="72" y="342" class="label">agent.edge_asr_memory</text><text x="72" y="356" class="label-soft">own credential, no shell</text><path d="M420 322 V366 H250 V379" class="stroke fill-none"/><path d="M250 388 L246 379 L254 379 Z" class="fill-ink"/><rect x="170" y="388" width="160" height="26" rx="13" class="fill-ground stroke"/><text x="250" y="406" text-anchor="middle" class="label">memory_reflex</text><text x="350" y="380" class="label-soft">reflexive retrieval, every user turn:</text><text x="350" y="394" class="label-soft">searches JMFTS before the model</text><text x="350" y="408" class="label-soft">sees the utterance. Not a tool —</text><text x="350" y="422" class="label-soft">the model cannot call it or skip it</text><line x1="250" y1="414" x2="250" y2="443" class="stroke"/><path d="M250 452 L246 443 L254 443 Z" class="fill-ink"/><rect x="160" y="452" width="180" height="40" rx="20" class="fill-ground stroke"/><text x="250" y="477" text-anchor="middle" class="label">AgentSession</text><line x1="340" y1="472" x2="400" y2="472" class="stroke"/><circle cx="400" cy="472" r="4" class="fill-ink"/><path d="M400 472 V452 H600" class="stroke-hair fill-none"/><text x="410" y="446" class="label-soft">the conversation continues</text><path d="M400 472 V510 H429" class="stroke-hair fill-none"/><path d="M438 510 L429 506 L429 514 Z" class="fill-ink"/><text x="406" y="490" class="label-soft">every N user turns</text><rect x="438" y="496" width="178" height="28" rx="14" class="fill-ground stroke-hair"/><text x="527" y="514" text-anchor="middle" class="label-soft">forked sub-agent</text><text x="438" y="542" class="label-soft">deposits what is worth</text><text x="438" y="556" class="label-soft">keeping, deduplicated</text><line x1="250" y1="492" x2="250" y2="519" class="stroke"/><path d="M250 528 L246 519 L254 519 Z" class="fill-ink"/><rect x="170" y="528" width="160" height="26" rx="13" class="fill-ground stroke"/><text x="250" y="546" text-anchor="middle" class="label">nats_bus</text><text x="270" y="580" class="label">TOUCHES_BUS</text><text x="270" y="596" class="label-soft">a session cannot reach the substrate by accident</text><line x1="250" y1="554" x2="250" y2="616" class="stroke"/><line x1="112" y1="616" x2="550" y2="616" class="stroke"/><line x1="112" y1="616" x2="112" y2="623" class="stroke"/><path d="M112 632 L108 623 L116 623 Z" class="fill-ink"/><line x1="550" y1="616" x2="550" y2="623" class="stroke"/><path d="M550 632 L546 623 L554 623 Z" class="fill-ink"/><rect x="72" y="632" width="80" height="28" class="fill-ground stroke-hair"/><text x="112" y="651" text-anchor="middle" class="label">speak</text><rect x="480" y="632" width="140" height="28" class="fill-ground stroke-hair"/><text x="550" y="651" text-anchor="middle" class="label">journal_append</text><text x="200" y="648" class="label">jmfts_write · delegate</text><text x="200" y="668" class="label-soft">delegate is picked up by agent.jmfts_operator,</text><text x="200" y="682" class="label-soft">an A/B experiment</text><text x="150" y="728" class="label-soft">…out.recall.&lt;device&gt;</text><line x1="90" y1="740" x2="300" y2="740" class="stroke"/><path d="M300 740 L291 736 L291 744 Z" class="fill-ink"/><line x1="110" y1="704" x2="110" y2="731" class="stroke"/><path d="M110 740 L106 731 L114 731 Z" class="fill-ink"/><text x="150" y="762" class="label-soft">…out.memorize.&lt;device&gt;</text><line x1="90" y1="774" x2="300" y2="774" class="stroke"/><path d="M300 774 L291 770 L291 778 Z" class="fill-ink"/><line x1="130" y1="704" x2="130" y2="765" class="stroke"/><path d="M130 774 L126 765 L134 765 Z" class="fill-ink"/><text x="330" y="802" class="label-soft">events.workspace.&lt;agent&gt;.out.&lt;tool&gt;</text><line x1="330" y1="814" x2="628" y2="814" class="stroke"/><path d="M628 814 L619 810 L619 818 Z" class="fill-ink"/><line x1="590" y1="660" x2="590" y2="805" class="stroke"/><path d="M590 814 L586 805 L594 805 Z" class="fill-ink"/><line x1="450" y1="814" x2="450" y2="837" class="stroke"/><path d="M450 846 L446 837 L454 837 Z" class="fill-ink"/><rect x="380" y="846" width="220" height="32" class="fill-ground stroke"/><text x="490" y="867" text-anchor="middle" class="label">effector.journal_append</text><line x1="450" y1="878" x2="450" y2="909" class="stroke-soft"/><path d="M450 918 L446 909 L454 909 Z" class="fill-ash"/><rect x="380" y="918" width="160" height="46" fill="url(#dia-hatch-fsa)" class="stroke"/><rect x="384" y="922" width="152" height="38" class="fill-none stroke-soft"/><rect x="412" y="930" width="96" height="22" class="fill-ground"/><text x="460" y="946" text-anchor="middle" class="label">documents</text><text x="380" y="984" class="label-soft">the only durable thing</text><path d="M380 941 H315 V713" class="stroke-soft fill-none"/><path d="M315 704 L311 713 L319 713 Z" class="fill-ash"/><text x="305" y="878" text-anchor="end" class="label">/search/vector</text><text x="305" y="892" text-anchor="end" class="label-soft">0.46–0.54 vs 0.22–0.33</text><text x="305" y="906" text-anchor="end" class="label-soft">score, not rank</text><text x="100" y="936" class="label-soft">a document an agent was not</text><text x="100" y="950" class="label-soft">granted does not exist for it</text><text x="100" y="990" class="label-soft">events.workspace.edge_asr.out.speak.handset</text><line x1="60" y1="1002" x2="300" y2="1002" class="stroke"/><path d="M300 1002 L291 998 L291 1006 Z" class="fill-ink"/><line x1="80" y1="660" x2="80" y2="993" class="stroke"/><path d="M80 1002 L76 993 L84 993 Z" class="fill-ink"/><path d="M60 1002 H50 V108 H51" class="stroke-hair fill-none"/><path d="M60 108 L51 104 L51 112 Z" class="fill-ink"/><text x="60" y="1022" class="label-soft">bound back to audio.handset, the phone that asked</text><text x="60" y="1046" class="label-soft">records of work already done, never requests; nothing binds</text><text x="60" y="1060" class="label-soft">to a past-tense report, so the memory loop cannot become a cycle</text><text x="60" y="1084" class="label-soft">events.journal.&lt;kind&gt;.&lt;binding_id&gt;</text><line x1="60" y1="1096" x2="628" y2="1096" class="stroke"/><path d="M628 1096 L619 1092 L619 1100 Z" class="fill-ink"/><path d="M560 878 V1087" class="stroke-hair fill-none"/><path d="M560 1096 L556 1087 L564 1087 Z" class="fill-ink"/><line x1="650" y1="290" x2="650" y2="1096" class="stroke-red"/><line x1="632" y1="290" x2="645" y2="290" class="stroke-red"/><rect x="645" y="285" width="10" height="10" class="fill-red"/><line x1="632" y1="814" x2="645" y2="814" class="stroke-red"/><rect x="645" y="809" width="10" height="10" class="fill-red"/><line x1="632" y1="1096" x2="645" y2="1096" class="stroke-red"/><rect x="645" y="1091" width="10" height="10" class="fill-red"/><text x="628" y="1122" text-anchor="end" class="label">binding_id</text><text x="628" y="1138" text-anchor="end" class="label-mark">one thread, three systems</text><text x="628" y="1154" text-anchor="end" class="label-soft">minted on the sensation event, re-read on every publish, named in the ack subject</text><text x="60" y="1122" class="label-soft">what has actually been run together is the handset loop</text></svg><figcaption>The three grammars are the argument. Square blocks on rails are Tectum's: it owns the routing, the lifecycle, and the configuration handed down as flags. The pills inside one of those blocks are Tau's: the session, the reflex that runs before it, and the fork that lets remembering spend its own budget on its own branch. The hatched slab is JMFTS's, and it is the only durable thing here — every event carries ttl_ms and the session compacts, so the deployment's identity lives in its corpus, not its wiring. What the figure is really drawing is the negative space: nothing inside the Tau pills knows what a device token is, nothing in the slab knows what a turn is, and the phone knows nothing but a socket. Those facts live in the schema panel at the top right, which is why the reflex has to be told its roots rather than find them. The red thread is the exception that proves it — binding_id is the one token every layer does carry, minted when the handset publishes, re-read by the extensions on every publish, and still legible in the ack subject at the bottom, which is the only reason one turn can be reconstructed across all three systems afterwards.</figcaption></figure>

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
