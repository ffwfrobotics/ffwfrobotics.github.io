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

<figure class="dia"><svg viewBox="0 0 680 586" role="img" aria-labelledby="dia-tj-t dia-tj-d"><title id="dia-tj-t">One session entry is one JMFTS document</title><desc id="dia-tj-d">The figure is in five bands, the same conversation drawn twice and then two things built on it. The top band, labelled tau, is a horizontal spine carrying three rounded pills in order: user message, toolCall, and toolResult, glossed that recall becomes entries on the path. Past the last pill the spine reaches a filled dot and forks into a solid limb that extends the leaf and a dashed limb left as the abandoned sibling, glossed fork is subtree copy. To the right of the heading the command tau dash dash store jmfts is given, with dash dash export dash session and dash dash import dash session named as two views of the same tree, as a dot j s o n l file. From the underside of the user message pill a red connector drops, squared off in red where it leaves the pill, down into the document row far below; it is marked one entry, one document, with the gloss same id, same parent links. Beside it a panel gives the document body: structured underscore content holds the entry full payload, and content is a plain-text projection kept only so search has something to match. The third band, labelled jmfts, is that same conversation as a document tree: a hatched, doubled-outline root slab typed tau colon conversation, one per session, with a hairline running right and down to four hatched child slabs typed tau colon message, tau colon compaction, tau colon branch underscore summary, and tau colon customMessage. The red connector lands on tau colon message. A dashed bracket drawn round the children is labelled parent underscore id, subtree scope. The fourth band, labelled tau again, is three tool boxes: jmfts underscore search and jmfts underscore read each send an arrow up into the bracketed subtree, while jmfts underscore ingest sends none, because it writes outside any conversation and refuses any usetype beginning tau colon. All three come from tau underscore jmfts slash ext slash tools dot p y, an ordinary extension with no injection hook. The last band, labelled jmfts, is a left-to-right chain of three boxes: auto underscore embed equals False, so a turn never waits; then tau underscore jmfts slash ext slash enrich dot p y, which runs at session shutdown and chunks rather than truncates; then index dash document, idempotent, so the pass costs order of new entries and resumes from is underscore embedded. The chain is captioned durably written at its left end and findable at its right.</desc><defs><pattern id="dia-hatch-tj" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="0" y="22" class="label-role">tau</text><text x="104" y="22" class="label-soft">a conversation is a tree of entries</text><text x="400" y="22" class="label">tau --store jmfts</text><text x="400" y="38" class="label-soft">--export-session &#183; --import-session</text><text x="400" y="52" class="label-soft">the same tree, as a .jsonl file</text><text x="0" y="116" class="label">AgentSession</text><text x="0" y="132" class="label-soft">session path</text><line x1="92" y1="120" x2="100" y2="120" class="stroke"/><rect x="100" y="106" width="104" height="28" rx="14" class="fill-ground stroke"/><text x="152" y="125" text-anchor="middle" class="label-soft">user message</text><line x1="204" y1="120" x2="228" y2="120" class="stroke"/><rect x="228" y="106" width="92" height="28" rx="14" class="fill-ground stroke"/><text x="274" y="125" text-anchor="middle" class="label">toolCall</text><line x1="320" y1="120" x2="344" y2="120" class="stroke"/><rect x="344" y="106" width="104" height="28" rx="14" class="fill-ground stroke"/><text x="396" y="125" text-anchor="middle" class="label">toolResult</text><text x="228" y="94" class="label-soft">recall becomes entries on the path</text><line x1="448" y1="120" x2="470" y2="120" class="stroke"/><circle cx="470" cy="120" r="4" class="fill-ink"/><path d="M470 120 V94 H660" class="stroke-hair fill-none"/><text x="478" y="86" class="label-soft">extends the leaf</text><path d="M470 120 V146 H660" class="stroke-hair stroke-dashed fill-none"/><text x="478" y="162" class="label-soft">abandoned sibling</text><text x="478" y="178" class="label-soft">fork is subtree copy</text><rect x="360" y="192" width="308" height="100" class="fill-surface stroke-hair"/><text x="372" y="210" class="label">structured_content</text><text x="372" y="224" class="label-soft">the entry&#39;s full payload</text><line x1="360" y1="236" x2="668" y2="236" class="stroke-soft"/><text x="372" y="254" class="label">content</text><text x="372" y="268" class="label-soft">a plain-text projection, kept only</text><text x="372" y="281" class="label-soft">so search has something to match</text><text x="0" y="238" class="label-role">jmfts</text><rect x="0" y="246" width="140" height="34" fill="url(#dia-hatch-tj)" class="stroke"/><rect x="4" y="250" width="132" height="26" class="fill-none stroke-soft"/><rect x="13" y="253" width="114" height="20" class="fill-ground"/><text x="70" y="268" text-anchor="middle" class="label-soft">tau:conversation</text><text x="0" y="296" class="label-soft">one per session</text><path d="M110 280 V294 H554 V316" class="stroke-hair fill-none"/><line x1="270" y1="294" x2="270" y2="316" class="stroke-hair"/><line x1="407" y1="294" x2="407" y2="316" class="stroke-hair"/><rect x="96" y="306" width="530" height="48" class="fill-none stroke-soft stroke-dashed"/><line x1="86" y1="330" x2="96" y2="330" class="stroke-soft"/><text x="0" y="328" class="label">parent_id</text><text x="0" y="342" class="label-soft">subtree scope</text><rect x="104" y="316" width="96" height="34" fill="url(#dia-hatch-tj)" class="stroke"/><rect x="108" y="320" width="88" height="26" class="fill-none stroke-soft"/><rect x="109" y="323" width="86" height="20" class="fill-ground"/><text x="152" y="338" text-anchor="middle" class="label-soft">tau:message</text><rect x="216" y="316" width="108" height="34" fill="url(#dia-hatch-tj)" class="stroke"/><rect x="220" y="320" width="100" height="26" class="fill-none stroke-soft"/><rect x="221" y="323" width="98" height="20" class="fill-ground"/><text x="270" y="338" text-anchor="middle" class="label-soft">tau:compaction</text><rect x="340" y="316" width="134" height="34" fill="url(#dia-hatch-tj)" class="stroke"/><rect x="344" y="320" width="126" height="26" class="fill-none stroke-soft"/><rect x="345" y="323" width="124" height="20" class="fill-ground"/><text x="407" y="338" text-anchor="middle" class="label-soft">tau:branch_summary</text><rect x="490" y="316" width="128" height="34" fill="url(#dia-hatch-tj)" class="stroke"/><rect x="494" y="320" width="120" height="26" class="fill-none stroke-soft"/><rect x="495" y="323" width="118" height="20" class="fill-ground"/><text x="554" y="338" text-anchor="middle" class="label-soft">tau:customMessage</text><text x="0" y="378" class="label-role">tau</text><line x1="174" y1="372" x2="174" y2="362" class="stroke-soft"/><path d="M174 354 L170 363 L178 363 Z" class="fill-ash"/><line x1="322" y1="372" x2="322" y2="362" class="stroke-soft"/><path d="M322 354 L318 363 L326 363 Z" class="fill-ash"/><rect x="104" y="372" width="140" height="30" class="fill-ground stroke-hair"/><text x="174" y="391" text-anchor="middle" class="label">jmfts_search</text><rect x="260" y="372" width="124" height="30" class="fill-ground stroke-hair"/><text x="322" y="391" text-anchor="middle" class="label">jmfts_read</text><rect x="400" y="372" width="140" height="30" class="fill-ground stroke-hair"/><text x="470" y="391" text-anchor="middle" class="label">jmfts_ingest</text><text x="104" y="420" class="label">tau_jmfts/ext/tools.py</text><text x="276" y="420" class="label-soft">an ordinary extension &#8212; no injection hook</text><text x="104" y="436" class="label-soft">scope=conversation|all|subtree</text><text x="104" y="450" class="label-soft">the live session&#39;s own client</text><text x="400" y="436" class="label-soft">writes outside any conversation</text><text x="400" y="450" class="label-soft">refuses any usetype beginning tau:</text><text x="0" y="484" class="label-role">jmfts</text><text x="104" y="484" class="label-soft">durable and findable are different states</text><rect x="0" y="494" width="184" height="40" class="fill-ground stroke-hair"/><text x="92" y="512" text-anchor="middle" class="label">auto_embed=False</text><text x="92" y="527" text-anchor="middle" class="label-soft">a turn never waits</text><line x1="184" y1="514" x2="214" y2="514" class="stroke-soft"/><path d="M222 514 L213 510 L213 518 Z" class="fill-ash"/><rect x="222" y="494" width="196" height="40" class="fill-ground stroke-hair"/><text x="320" y="512" text-anchor="middle" class="label">tau_jmfts/ext/enrich.py</text><text x="320" y="527" text-anchor="middle" class="label-soft">runs at session shutdown</text><line x1="418" y1="514" x2="448" y2="514" class="stroke-soft"/><path d="M456 514 L447 510 L447 518 Z" class="fill-ash"/><rect x="456" y="494" width="212" height="40" class="fill-ground stroke-hair"/><text x="562" y="512" text-anchor="middle" class="label">index-document</text><text x="562" y="527" text-anchor="middle" class="label-soft">idempotent &#183; O(new entries)</text><text x="0" y="552" class="label-soft">durably written</text><text x="222" y="552" class="label-soft">chunked, never truncated</text><text x="222" y="566" class="label-soft">resumes from is_embedded</text><text x="456" y="552" class="label-soft">findable</text><rect x="147" y="133" width="10" height="10" class="fill-red"/><line x1="152" y1="143" x2="152" y2="305" class="stroke-red"/><path d="M152 316 L146 305 L158 305 Z" class="fill-red"/><text x="166" y="196" class="label-mark">one entry, one document</text><text x="166" y="214" class="label-soft">same id &#183; same parent links</text><text x="166" y="230" class="label-soft">memory is not bolted on</text></svg><figcaption>Two grammars, one tree. Above the seam the session is a Tau spine of pills that forks at a filled dot and leaves the abandoned branch dashed; below it those same entries are JMFTS slabs hanging off one root document. Nothing converts between the two, which is why the red mark is an identity rather than an arrow through a protocol: tau --store jmfts makes one entry one document, same id and same parent link, so JMFTS’s subtree filter is already “only this conversation” and a fork is already a subtree copy. Recall stays inside the same shape — jmfts_search is a tool the model elects to call, so the call and its results land back on the spine as ordinary entries instead of arriving invisibly ahead of the turn. The one thing the shared shape does not hand you is findability: writes append with auto_embed=False, and enrich.py settles that debt once the session is over.</figcaption></figure>

!!! note "Draft"
    Written from the Tau repo's own `tau_jmfts` package sources and
    `docs/JMFTS-INTEGRATION-PLAN.md`. Behaviour at this seam is covered by
    Tau's own test suite; it has not been exercised against a JMFTS
    deployment outside the maintainer's own.

Everything below ships in the optional `ffwf-tau-jmfts` package
(`pip install 'ffwf-tau-coding-agent[jmfts]'`, which is a convenience spelling
for it). Tau never depends on it; the store loads
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
[extension](../tau/reference/extensions.md) — and the agent gets three
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
