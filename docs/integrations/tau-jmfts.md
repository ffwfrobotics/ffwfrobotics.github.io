---
title: "Tau + JMFTS"
kind: "integration"
summary: "Retrieval-backed agents: giving a Tau session searchable memory over a JMFTS corpus."
projects: [tau, jmfts]
status: "draft"
---

# Tau + JMFTS

Tau stores a conversation as a tree of entries. JMFTS stores a corpus as a
tree of documents. The integration is the observation that these are the same
shape: point `tau --store jmfts` at a JMFTS server and every entry in the
session **is** a document — same id, same parent links, same search machinery
as anything else in the corpus. Memory is not a feature bolted onto the agent;
the agent's history is simply kept somewhere that can already be searched.

!!! note "Draft"
    Written from the Tau repo's own `tau-jmfts` package sources and
    `docs/JMFTS-INTEGRATION-PLAN.md`. Behaviour at this seam is covered by
    Tau's own test suite; it has not been exercised against a JMFTS
    deployment outside the maintainer's own.

Everything below ships in the optional `tau-jmfts` package
(`pip install -e ./tau-jmfts`). Tau never depends on it; the store loads
lazily when `--store jmfts` selects it, and a missing package, bad token, or
unreachable server is a clean startup error, never a silent fall-back to
files. The Tau [DevOps Manual](../tau/devops.md#where-sessions-live) covers
where the two stores sit relative to each other.

## The conversation is the corpus

```bash
tau --store jmfts                       # this run's sessions live in JMFTS
tau --export-session REF out.jsonl      # JMFTS → JSONL, then exit
tau --import-session out.jsonl          # JSONL → JMFTS, then exit
```

Each session becomes one `tau:conversation` root document; each entry — user
message, assistant message, tool call, compaction summary, branch marker —
becomes one child with `usetype="tau:message"`, `tau:compaction`, and so on.
The entry's full payload lives in `structured_content`; the document's
`content` is a plain-text projection kept only so search has something to
match.

Three consequences fall out of the shared shape, none of which needed new
code:

- **Fork is subtree copy.** Branching a conversation into a new session is
  the same operation as copying any document subtree, with the three
  cross-referencing entry fields remapped onto the new ids.
- **Scope is `parent_id`.** JMFTS's subtree filter — "only hits under this
  document" — is, unchanged, "only hits in this conversation" or "only hits
  in this project bucket".
- **A session survives its file.** `--export-session` writes a `.jsonl` the
  file store can open; `--import-session` walks one back up into a subtree.
  The two stores are interchangeable views of the same tree.

Writes stay cheap on purpose: the store appends documents with
`auto_embed=False`, so a conversational turn never waits on a GPU forward
pass.

## Recall is a tool call, not an injection

Load `tau_jmfts/ext/tools.py` — an ordinary Tau
[extension](../tau/reference.md#extension-api) — and the agent gets three
tools:

- `jmfts_search(query, scope=conversation|all|subtree, method, usetype, limit)`
- `jmfts_read(doc_id, children)`
- `jmfts_ingest(title, content, parent_id, usetype)`

The design choice worth noticing is what this extension does **not** do:
there is no hook that quietly prepends "relevant memories" to the prompt.
When the agent wants to remember, it calls `jmfts_search`, and that call and
its results become real `toolCall` / `toolResult` entries on the session
path — persisted, visible in the transcript, forkable, and subject to
compaction like everything else. You can read a session later and see
exactly what the agent recalled, when, and what it did with it. Retrieval
that influenced an answer is never invisible.

Two guard rails at the seam:

- The tools borrow the live session's own client, so they cannot search a
  different JMFTS instance than the one holding the conversation.
- `jmfts_ingest` refuses any `usetype` beginning with `tau:` — that
  namespace belongs to the store, and an agent must not be able to forge
  conversation entries into its own history.

The absence of injection is this extension's choice, not the only posture
available. `memory_reflex` — an ordinary Tau extension that happens to live
in the Tectum repo — takes the opposite one: it searches before every user
turn and the model cannot skip it, described on
[Tectum + Tau](tectum-tau.md#memory-the-model-does-not-elect). Anything that
*decides* from a score, as a reflex must, has to query `vector` rather than
`hybrid` or `auto`, whose rank-fused scores return the same values for a
relevant query and a nonsense one. The measurement is in the JMFTS
[Cookbook](../jmfts/cookbook.md#gate-on-a-score-only-when-the-method-returns-a-real-one).
A tool call has no such constraint: the model reads the results, so ranking
is enough.

## The agent takes notes it will find later

`jmfts_ingest` is the write half of memory: the agent can deposit a durable
note — a decision, a distilled finding, a project convention — as an ordinary
document, outside any conversation, under whatever subtree makes it
findable. A future session with `scope=all` retrieves it by content, not by
knowing where it was filed. The conversation is automatic memory; ingest is
deliberate memory. Both land in the same tree and the same indexes.

## A playbook stored as a versioned tree

`StrategyStore` (`tau_jmfts/ext/strategy_store.py`) is the demonstration that
the document tree alone can carry versioned mutable state with immutable
history. An agent's playbook is organized into *families*: each family is a
head document — the current consolidated strategy — with an append-only log of
immutable observation children beneath it.

- `append_log` adds an observation; nothing is ever edited in place.
- `assemble` reads back the head plus its unconsolidated tail, so the current
  strategy and the not-yet-digested evidence arrive together.
- `consolidate` rewrites the head and flips the tail's flags — a new version,
  with the old evidence still on disk.
- `history` returns the full ordered log, kept specifically for the poison
  audit: if a bad observation steered a consolidation, you can find which one
  and when.
- `find` is a two-step retrieval that searches heads only, so lookup cost
  scales with the number of strategies, not the number of observations.

There is no schema migration and no second storage system behind any of this.
It is documents, two usetypes (`memory:strategy:head`, `memory:strategy:log`),
and `structured_content` flags the store refuses to let a caller shadow. The
appliance's tree does the version-control work.

## Memory improves while the agent sleeps

The write path's `auto_embed=False` buys a cheap turn and leaves a debt: until
something settles it, Tau conversations sit in a retrieval appliance that
cannot retrieve them. In this integration, **durable and findable are
deliberately different states**, and one component exists to move
conversations from the first to the second.

Load `tau_jmfts/ext/enrich.py` and session shutdown triggers that pass. It
embeds every text-carrying entry kind — `tau:message`, `tau:compaction`,
`tau:branch_summary`, `tau:customMessage` — chunking anything longer than the
embedder's window instead of embedding it whole, because the server refuses
over-window text with a 400 rather than silently truncating it. Then it
indexes the conversation into a BM25 index, one document at a time.

The step that makes this trustworthy is on the JMFTS side:
`index-document` is idempotent — re-indexing subtracts a document's old
contribution before adding the new one, and short-circuits when the content
hash is unchanged. So enrichment is O(new entries), and a pass that crashes
halfway can simply run again; resumability is derived from server state
(`is_embedded`, existing chunks), never from a progress marker that can lie.
Sessions that ended yesterday are fully searchable today, and no turn ever
paid the embedding cost. What that costs the server is the JMFTS
[DevOps Manual](../jmfts/devops.md#index-maintenance)'s side of the seam.

## Recall with a sense of time

Because every entry document carries a timestamp, JMFTS's temporal search
features apply directly to conversation memory:

- `as_of` reruns any search as of a past moment — "what did the corpus look
  like when the agent made that decision?" is a query, not an archaeology
  project.
- `recency_weight` / `recency_halflife_days` bias hybrid search toward
  fresh entries. The project's own measurements say to treat this as a
  per-query policy, not a global default: recency weighting fixed staleness
  errors in one benchmark and degraded multi-session recall in another.
  Newer is a bias you opt into when the question is about *now* — the same
  argument the JMFTS
  [Cookbook](../jmfts/cookbook.md#tune-the-hybrid-weight-to-the-corpus-dont-assume-one-number)
  makes about the hybrid weight.

Both are reachable through the raw client today; the `jmfts_search` tool
does not yet expose them.

## What the seam refuses to do

Failure modes at this boundary are handled by refusal, not repair — a memory
system that silently degrades is worse than one that stops:

- A `--store jmfts` session with no reachable server, missing URL, or bad
  token exits with an error at startup. `--session-dir` combined with
  `--store jmfts` is a hard error, not a guess about which one you meant.
- `load()` rejects a root that is not a well-formed `tau:conversation`, and
  raises if the entry sequence shows a second writer touched the tree.
- Foreign documents filed under a conversation are tolerated and surfaced,
  but can never move the session's cursor — an out-of-band write cannot
  redirect where the next turn lands.
- Forking raises on an unresolvable cross-reference rather than copying a
  dangling anchor. (The dangling-anchor case was measured, not imagined: an
  early fork of a compacted session silently lost its kept messages.)
- `--no-session` uses an ephemeral in-memory log that refuses to touch the
  server at all. "Don't persist" means nothing is persisted.

Pointing a running TUI at this store is a Tau Cookbook recipe:
[Point the TUI at a different session backend](../tau/cookbook.md#point-the-tui-at-a-different-session-backend).
