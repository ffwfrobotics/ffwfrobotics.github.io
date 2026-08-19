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
