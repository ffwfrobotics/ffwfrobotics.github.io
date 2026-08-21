---
title: "Tectum + JMFTS"
kind: "integration"
summary: "Retrieval as a substrate service: JMFTS queries and index updates carried as events."
projects: [tectum, jmfts]
status: "draft"
---

# Tectum + JMFTS

JMFTS holds the documents; Tectum decides how reads and writes reach it.
The working principle, stated once and used everywhere: **state lives in
JMFTS, control flow lives on the bus.** A read is an in-process call, off
the DAG. A durable write rides the
[command DAG](../tectum/devops.md#two-dags-one-namespace) as an event. And
"please handle this" is never a database row — it is a publish.

<figure class="dia"><svg viewBox="0 0 680 720" role="img" aria-labelledby="dia-tjm-t dia-tjm-d"><title id="dia-tjm-t">A write goes the long way round; a read goes straight in</title><desc id="dia-tjm-d">The figure has two paths from one pair of Tectum agents to one JMFTS store, and they are deliberately different shapes. Top left, a panel headed praxis slash loose underscore loop3 dot yaml marks the operator as experimental: one cohort, A slash B against loose underscore loop2, not a boot default, with a grounded ask taking 180 seconds and the operator's wall clock raised to 220 seconds. To its right, three subject rails descend in a staircase and every one of them ends in an arrowhead landing on the node agent dot jmfts underscore operator, which is how the drawing says the node subscribes: ellipsis out dot muse wakes it to curate, operator dot maintain wakes it to maintain, and events dot workspace dot responder dot out dot delegate wakes it to answer. That third rail is published from below by agent dot responder, whose arrowhead lands on the rail rather than on a node: please handle this is a publish, not a database row. From the operator's underside one thin hairline drops straight down the right margin, crosses no rail, taps nothing, and lands on the hatched documents slab. It is labelled a read is an in-process call, off the DAG, it taps no rail, slash search slash synthesize and slash search slash vector, and further down, no subject, no effector, no event to observe. The write path takes the opposite route. agent dot responder publishes down onto two command rails, events dot workspace dot angle bracket agent dot out dot journal underscore append and the generic events dot workspace dot angle bracket agent dot out dot angle bracket tool. Each rail hands down to an effector node: effector dot journal underscore append, which is the only code that knows the store's address, and effector dot jmfts underscore write, parameterized for any subtree. Each effector then runs a long dog-legged connector down and across into the same documents slab. Between the effectors and the store is the one red mark in the figure: the rail events dot journal dot angle bracket kind dot angle bracket binding underscore id, drawn in red, with effector dot journal underscore append publishing up onto it. It is annotated the ack is the fact, a tool wrapper waits on it, addressed by the binding underscore id. Bottom right, under the role label jmfts, two hatched doubled-outline slabs are stacked: documents and search underscore term underscore postings. Between them a panel names the two backfills, embed and index-document, dashed lines running up into documents and down into the postings, glossed eventually consistent backfill and a redelivered event re-indexes the same document, unchanged. Beneath it all: durably written is not findable. Bottom left, a panel lists the three things that fall out of routing writes through the substrate instead of around it: observability, enforceability, and substitution.</desc><defs><pattern id="dia-hatch-tjm" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="250" y="32" class="label-role">tectum</text><rect x="0" y="16" width="230" height="108" class="fill-surface stroke-hair"/><text x="12" y="36" class="label">praxis/loose_loop3.yaml</text><line x1="0" y1="44" x2="230" y2="44" class="stroke-soft"/><text x="12" y="60" class="label-soft">experimental — one cohort,</text><text x="12" y="73" class="label-soft">A/B against loose_loop2</text><text x="12" y="86" class="label-soft">not a boot default</text><text x="12" y="102" class="label-soft">a grounded ask: 180 s</text><text x="12" y="115" class="label-soft">operator wall clock: 220 s</text><text x="250" y="54" class="label-soft">…out.muse</text><text x="316" y="54" class="label-soft">curate · records, stays silent</text><line x1="250" y1="64" x2="668" y2="64" class="stroke"/><path d="M668 64 L659 60 L659 68 Z" class="fill-ink"/><line x1="650" y1="64" x2="650" y2="177" class="stroke"/><path d="M650 186 L646 177 L654 177 Z" class="fill-ink"/><text x="250" y="94" class="label-soft">operator.maintain</text><text x="366" y="94" class="label-soft">maintain · supersedes, never deletes</text><line x1="250" y1="104" x2="630" y2="104" class="stroke"/><path d="M630 104 L621 100 L621 108 Z" class="fill-ink"/><line x1="545" y1="104" x2="545" y2="177" class="stroke"/><path d="M545 186 L541 177 L549 177 Z" class="fill-ink"/><text x="0" y="144" class="label-soft">events.workspace.responder.out.delegate</text><text x="256" y="144" class="label-soft">answer · posting it pushes a wake</text><line x1="0" y1="156" x2="500" y2="156" class="stroke"/><path d="M500 156 L491 152 L491 160 Z" class="fill-ink"/><line x1="430" y1="156" x2="430" y2="177" class="stroke"/><path d="M430 186 L426 177 L434 177 Z" class="fill-ink"/><rect x="0" y="186" width="230" height="46" class="fill-ground stroke"/><text x="115" y="206" text-anchor="middle" class="label">agent.responder</text><text x="115" y="222" text-anchor="middle" class="label-soft">no database connection</text><line x1="115" y1="186" x2="115" y2="165" class="stroke"/><path d="M115 156 L111 165 L119 165 Z" class="fill-ink"/><rect x="310" y="186" width="358" height="46" class="fill-ground stroke"/><text x="489" y="206" text-anchor="middle" class="label">agent.jmfts_operator</text><text x="489" y="222" text-anchor="middle" class="label-soft">ask → /search/synthesize · lint → /graph/lint</text><line x1="630" y1="232" x2="630" y2="449" class="stroke-hair"/><path d="M630 458 L626 449 L634 449 Z" class="fill-ink"/><text x="616" y="250" text-anchor="end" class="label-soft">a read is an in-process call</text><text x="616" y="264" text-anchor="end" class="label-soft">off the DAG — it taps no rail</text><text x="616" y="314" text-anchor="end" class="label">/search/synthesize</text><text x="616" y="332" text-anchor="end" class="label">/search/vector</text><text x="616" y="422" text-anchor="end" class="label-soft">no subject, no effector,</text><text x="616" y="436" text-anchor="end" class="label-soft">no event to observe</text><text x="0" y="272" class="label-role">tectum</text><text x="200" y="286" class="label-soft">events.workspace.&lt;agent&gt;.out.journal_append</text><line x1="150" y1="296" x2="560" y2="296" class="stroke"/><path d="M560 296 L551 292 L551 300 Z" class="fill-ink"/><line x1="170" y1="232" x2="170" y2="287" class="stroke"/><path d="M170 296 L166 287 L174 287 Z" class="fill-ink"/><line x1="360" y1="296" x2="360" y2="371" class="stroke"/><path d="M360 380 L356 371 L364 371 Z" class="fill-ink"/><text x="90" y="318" class="label-soft">events.workspace.&lt;agent&gt;.out.&lt;tool&gt;</text><line x1="0" y1="328" x2="330" y2="328" class="stroke"/><path d="M330 328 L321 324 L321 332 Z" class="fill-ink"/><line x1="60" y1="232" x2="60" y2="319" class="stroke"/><path d="M60 328 L56 319 L64 319 Z" class="fill-ink"/><line x1="120" y1="328" x2="120" y2="371" class="stroke"/><path d="M120 380 L116 371 L124 371 Z" class="fill-ink"/><text x="390" y="350" class="label-soft">events.journal.&lt;kind&gt;.&lt;binding_id&gt;</text><line x1="390" y1="360" x2="612" y2="360" class="stroke-red"/><path d="M612 360 L603 356 L603 364 Z" class="fill-red"/><line x1="415" y1="380" x2="415" y2="369" class="stroke-red"/><path d="M415 360 L411 369 L419 369 Z" class="fill-red"/><text x="448" y="374" class="label-mark">the ack is the fact</text><text x="448" y="390" class="label-soft">a tool wrapper waits on it</text><text x="448" y="404" class="label-soft">addressed by the binding_id</text><rect x="20" y="380" width="190" height="42" class="fill-ground stroke"/><text x="115" y="400" text-anchor="middle" class="label">effector.jmfts_write</text><text x="115" y="415" text-anchor="middle" class="label-soft">parameterized · any subtree</text><rect x="240" y="380" width="200" height="42" class="fill-ground stroke"/><text x="340" y="400" text-anchor="middle" class="label">effector.journal_append</text><text x="340" y="415" text-anchor="middle" class="label-soft">knows the store’s address</text><path d="M390 422 L390 470 L452 470" class="stroke fill-none"/><path d="M460 470 L451 466 L451 474 Z" class="fill-ink"/><path d="M180 422 L180 498 L452 498" class="stroke fill-none"/><path d="M460 498 L451 494 L451 502 Z" class="fill-ink"/><text x="452" y="450" class="label-role">jmfts</text><rect x="460" y="458" width="208" height="52" fill="url(#dia-hatch-tjm)" class="stroke"/><rect x="464" y="462" width="200" height="44" class="fill-none stroke-soft"/><rect x="510" y="472" width="110" height="24" class="fill-ground"/><text x="564" y="489" text-anchor="middle" class="label">documents</text><line x1="620" y1="510" x2="620" y2="523" class="stroke-soft stroke-dashed"/><path d="M620 532 L616 523 L624 523 Z" class="fill-ash"/><line x1="500" y1="532" x2="500" y2="519" class="stroke-soft stroke-dashed"/><path d="M500 510 L496 519 L504 519 Z" class="fill-ash"/><rect x="452" y="532" width="216" height="76" class="fill-surface stroke-hair"/><text x="462" y="554" class="label">embed</text><text x="530" y="554" class="label">index-document</text><text x="462" y="572" class="label-soft">eventually consistent backfill</text><text x="462" y="586" class="label-soft">a redelivered event re-indexes</text><text x="462" y="600" class="label-soft">the same document, unchanged</text><line x1="560" y1="608" x2="560" y2="621" class="stroke-soft stroke-dashed"/><path d="M560 630 L556 621 L564 621 Z" class="fill-ash"/><rect x="460" y="630" width="208" height="52" fill="url(#dia-hatch-tjm)" class="stroke"/><rect x="464" y="634" width="200" height="44" class="fill-none stroke-soft"/><rect x="486" y="644" width="156" height="24" class="fill-ground"/><text x="564" y="661" text-anchor="middle" class="label">search_term_postings</text><text x="452" y="704" class="label-soft">durably written is not findable</text><rect x="0" y="532" width="400" height="158" class="fill-surface stroke-hair"/><text x="12" y="554" class="label-soft">three things fall out of routing writes</text><text x="12" y="568" class="label-soft">through the substrate instead of around it</text><line x1="0" y1="578" x2="400" y2="578" class="stroke-soft"/><text x="12" y="596" class="label-soft">observability · a source, a schema</text><text x="12" y="610" class="label-soft">attribution, a correlation id</text><text x="12" y="628" class="label-soft">enforceability · a closeout prompt when</text><text x="12" y="642" class="label-soft">a required tool call has not happened</text><text x="12" y="660" class="label-soft">substitution · the contract is a subject,</text><text x="12" y="674" class="label-soft">not a client library</text></svg><figcaption>Two routes to one store, and the difference is the interface. A durable write is not a database call: the agent publishes a verb, an effector subscribes it, and the write comes back as an event on events.journal.&lt;kind&gt;.&lt;binding_id&gt; — the red rail, and the only thing that turns a publish into a fact. That long way round is what buys observability, enforceability and substitution; the effector is the only code in the picture holding the store’s address. A read buys none of those and needs none of them, so it takes the hairline: straight down the margin, across no rail, no subject and no effector between the caller and the tree. The third rule is drawn on the delegate rail — asking another agent to act is a publish, never a row someone has to poll. What the ack does not promise is findability: the effectors write with auto_embed=False and commit, so the embedding and the BM25 postings arrive afterwards. That backfill is safe to redeliver only because index-document subtracts a document’s prior contribution before re-adding it.</figcaption></figure>

!!! note "Draft"
    Written from the Tectum repo's effector nodes (`effector.journal_append`,
    `effector.jmfts_write`), `agent.jmfts_operator`,
    `praxis/loose_loop3.yaml`, the workspace projection, and the roadmap.
    The effectors and the projection are covered by offline
    suites; the one live end-to-end run is scoped in
    [What is demonstrated](#what-is-demonstrated-and-what-is-only-claimed)
    at the end.

## Writes you can watch

An agent that wants something remembered does not hold a database
connection. Its tool wrapper publishes
`events.workspace.<agent>.out.journal_append`; an effector node —
`effector.journal_append` for the journal, or the parameterized
`effector.jmfts_write` for any subtree — performs the write; and the write
acknowledges on `events.journal.<kind>.<binding_id>`, addressed by the same
correlation id the originating utterance carried. Both halves are ordinary
[events](../tectum/reference.md#the-event-envelope) on ordinary
[subjects](../tectum/reference.md#subject-namespace).

Three things fall out of routing memory writes through the substrate
instead of around it:

- **Observability.** Every durable write is an event with a source, a
  schema attribution, and a correlation id. "What did the agent record, and
  why" is answered from the event log — the same trace the Tectum Cookbook
  follows in
  [Trace one turn across the fleet](../tectum/cookbook.md#trace-one-turn-across-the-fleet).
- **Enforceability.** Closeout discipline can require the write: the
  dispatcher injects a closeout prompt when a required tool call has not
  happened, so a turn is not allowed to end with remembering quietly
  skipped.
- **Substitution.** The agent's contract is a subject, not a client
  library. The effector is the only code that knows the store's address,
  which is how the same cognition ran against a keyboard harness and a
  WAN-bridged room without changing an agent.

The ack is what makes the write a fact rather than a hope. A `jmfts_write`
whose ack never arrives is a tool error the model sees, not a message lost
in transit — the same publish-and-wait contract the τ node uses on
[Tectum + Tau](tectum-tau.md#two-postures-one-wire-contract).

### The ack means durably written, and only that

The effectors write with `auto_embed=False` and commit synchronously, so the
acknowledgement is a statement about durability, not about search. Embedding
is a slower, eventually-consistent backfill. The seam property to respect:
**durably written is not findable.** A vector search fired immediately after
an ack may miss the entry until its embedding lands. A consumer that needs
read-after-write recall has to design for that gap rather than assume it
away.

The ack also carries the `binding_id`, so the durable record threads into the
same logical flow — perceive, plan, act — as every other event in the turn
that caused it. "What did this exchange leave behind" is answerable from the
subject name alone.

## Coordination without a lock manager

The moment a second agent shares the workspace, coordination becomes a real
question. The Tectum answer is assembled from the bus, append-only writes,
and JMFTS's own timestamps — no lock manager anywhere:

| Hazard | Pattern |
|---|---|
| Two writers clobber one subtree | **Append-only, multi-writer.** Nobody overwrites; a consolidator folds appended records later, asynchronously, and never gates a write. |
| Two agents act on the same thing | **In-force-bounded claims.** Write a claim with `in_force_to = now + budget + grace`; others read claims first and skip. A crashed claimant's claim expires on its own. |
| Read, then act on a since-changed view | **As-of reads.** A dispatch reads the workspace as of its own start timestamp; JMFTS's historical projection makes the snapshot free. |
| Agent A wants agent B to act | **Publish to B's inbound subject.** The bus is the queue; a handoff is never a database flag someone must remember to poll. |

The division of labor is exact. JMFTS provides the timestamps, the append
semantics, and the projection — its
[bitemporal fact model](../jmfts/cookbook.md#record-facts-that-can-be-corrected-without-being-erased)
is the same shape one layer down. Tectum provides the event rails and the
discipline about which primitive answers which hazard.

Honestly scoped: append-only multi-writer and inbound-publish handoff are
how the shipped experiments already coordinate; in-force claims and as-of
reads are the corrected design of record for the next agent that needs
them, not yet a shipped convention. The fast/slow schema pair that uses the
first two is in the Tectum Cookbook:
[Split an agent into a fast responder and a slow curator](../tectum/cookbook.md#split-an-agent-into-a-fast-responder-and-a-slow-curator).

## Keeping the index current from an event log

Event delivery is at-least-once, so index maintenance has to survive
redelivery. JMFTS's incremental `index-document` endpoint is idempotent — it
subtracts a document's previous contribution to the BM25 collection
statistics before re-adding it — so an event-driven indexer needs no
deduplication infrastructure at all. A redelivered event re-indexes the same
document and changes nothing.

This was once false: the pre-fix server inflated `total_docs` and `doc_freq`
on re-index, and every event-log consumer would have had to build its own
exactly-once machinery on top. Server-side idempotence is what makes the
naive consumer correct. The cost of those passes is the JMFTS
[DevOps Manual](../jmfts/devops.md#index-maintenance)'s side of the seam.

## The tree gets its own agent

**Status: experimental — the operator runs only under
`praxis/loose_loop3.yaml`, an A/B against a cohort that does not use it.**

`agent.jmfts_operator` turns the document tree from a passive store into a
tier of the cognition: a slow-tier agent whose tools are the tree's own
verbs. Where a generic agent gets a search tool, this one wields the JMFTS
surface as verbs:

| Verb | JMFTS surface it drives |
|---|---|
| `ask` | `/search/synthesize` — a grounded answer, not a result list |
| `find` | auto-routed search for the documents that bear on something |
| `read` | a document *properly*: its prose, its place in the tree, its links, its facts |
| `facts` | the triple graph — what is known about a thing, or how two things connect |
| `explore` | children / ancestors / siblings / links |
| `link` | a typed `document_links` edge between two documents |
| `consolidate` | RAPTOR / portfolio summarization, fact extraction |
| `lint` | `/graph/lint` — orphans, contradictions, staleness, coverage |

Several of those verbs are JMFTS features that only pay off when something
tends them on a cadence, which is what
[auditing a corpus the way you lint code](../jmfts/cookbook.md#audit-a-corpus-the-way-you-lint-code)
looks like with an agent holding the linter.

The interesting part is not the verbs but the *wake modes*, selected by event
suffix, which turn knowledge work into routed cognitive roles:

- **answer** (`…out.delegate`) — the fast conversational layer handed up a
  question. The operator queries the tree and posts an answer, and the posted
  event pushes a wake so the answer is voiced promptly instead of waiting to
  be polled.
- **curate** (`…out.muse`) — the operator is overhearing. It records a fact or
  a connection and stays silent. No reply is expected or produced.
- **maintain** (`operator.maintain`) — a quiet pass to tidy the knowledge
  base: lint, fix the cheap safe things, note what was done. It never deletes
  or overwrites.

Each mode leans on a JMFTS property the substrate could not supply itself.
`answer` exists because `synthesize` returns a grounded answer rather than
hits to re-read. `curate` exists because the triple store makes "record this
connection" a first-class write. And `maintain` is only safe to run
unattended because JMFTS **supersedes instead of deleting** — the worst an
autonomous maintenance pass can do is add a correction, never destroy a
record — while `/graph/lint` hands it a ready-made work queue of orphans,
contradictions, and stale facts to walk.

It was A/B'd against a generalist curator by swapping one node name in an
otherwise identical schema (`loose_loop3` against `loose_loop2`), and that
experiment is the one cognition loop in the tree with a dated, confirmed
live end-to-end run: a two-way spoken conversation over a WAN bridge, with
the operator working the corpus behind it.

The substrate's contribution to that experiment is the experiment itself.
When retrieval sits behind a subject and a node name, "what kind of mind
should tend the memory" becomes a question you can answer empirically, one
[schema activation](../tectum/devops.md#schema-activation) at a time.

## Timeouts must learn retrieval's latency

A grounded `ask` against a local model can legitimately run close to 180
seconds. `loose_loop3` raises the operator's wall-clock limit to 220 seconds
specifically so a slow synthesize is not killed mid-call. The lesson travels:
when a retrieval appliance sits behind an event substrate, the substrate's
supervision defaults — tuned for reflex-speed nodes — silently execute honest
slow answers unless the schema says otherwise.

## Sensation becomes corpus

`memory.transcript` binds the cleaned utterance rail to a durable record:
everything anyone says — after the echo gate has removed the agent's own
voice — becomes a JMFTS document under the current session's sub-root, with
the raw ASR text preserved beside the resolved version. The corpus of what
has been said in the room is a side effect of routing. There is no batch
importer, no export step, and nothing to fall behind, because the write
path *is* the event path.

What JMFTS adds to that record is time it can be asked about later: the
transcript pipeline keeps domain time separate from ingestion time, so the
room's history stays answerable on
[when things were said](../jmfts/cookbook.md#archive-transcripts-on-the-time-they-happened)
rather than on when the writer got around to it.

## Two postures on retrieval

This page is the write side and the routing side. The read side has two
shapes across the stack, and they are deliberately different:

- **Retrieval the agent elects.** A tool call the model makes, recorded in
  the session transcript — [Tau + JMFTS](tau-jmfts.md#recall-is-a-tool-call-not-an-injection).
- **Retrieval the agent cannot skip.** A reflex that runs before every user
  turn, threading hits ahead of the utterance —
  [Tectum + Tau](tectum-tau.md#memory-the-model-does-not-elect).

Both read the same store under the same
[principal model](../jmfts/reference.md#data-model). The choice is about
what you want auditable: what the agent asked for, or that it asked at all.

## What is demonstrated, and what is only claimed

The effectors, the ack rails, and the append-only workspace projection are
shipped and offline-tested (`test_workspace_projection.py`,
`test_closeout.py`). The coordination table reflects the 2026-08-09
correction to the roadmap's protocol section, and half of it is design of
record rather than shipped convention, marked above. `agent.jmfts_operator`
is an experiment that ran, not a boot default: it is active only in the
`loose_loop3` cohort. The live end-to-end claim is scoped to the
`loose_loop3` WAN run and nothing broader.

All three projects at once are on
[The FFwF Full Stack Agent](full-stack-agent.md).
