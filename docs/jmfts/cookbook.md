---
title: "Cookbook"
category: "cookbook"
status: "stub"
---

# JMFTS — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific JMFTS jobs — tuning matryoshka dimensions, reweighting BM25 against the vector score, adding a reranking stage.

!!! note "Marked stub on purpose"
    The recipes below are real, drawn from JMFTS's own benchmark runs and defect write-ups — but they have not been organized into full step-by-step walkthroughs or checked against a fresh deployment, so this page stays `stub` until that pass happens.

!!! note "The measurements are ahead of the release"
    Every endpoint and setting named here is in the public [0.1.0 release](https://github.com/jmccardle/jmfts/releases/tag/0.1.0). The evaluation harness that produced the numbers is not — it follows separately, along with the write-ups behind the defect recipes (see [Documents not in this release](devops.md#documents-not-in-this-release)). So the figures below are reported, not yet reproducible from a clone.

## Pick a rerank method by what your corpus already stores

Every search endpoint accepts `?rerank=true`, and `rerank_method` picks the second stage. The two are not ranked best-to-worst — they have different prerequisites, and the right one depends on your corpus.

**`maxsim`** reuses the per-token vectors already in `token_embeddings`, so it loads no model and adds no GPU memory. On the MultiHop-RAG benchmark (609 articles, 2,255 multi-hop queries — a case BEIR's single-hop datasets don't exercise), `vector→maxsim@200` measured **72.2% Hits@4 against plain vector's 58.4%**, a 13.8-point gain that BM25 alone (69.4%) and the tuned hybrid (63.8%) both fall short of.

The catch is the storage. Token embeddings are one row per selected token per document, so the late-interaction index is far larger than the document vectors. A candidate with no stored tokens scores 0 and sinks to the bottom of the reranked list. On a corpus where only part of the tree has been through `/documents/{id}/tokens`, that silently demotes real hits — so use `maxsim` when token coverage is complete, not merely present.

**`cross_encoder`** (the default) reads nothing from the database. It scores each (query, document) pair with a cross-encoder model set by `JMFTS_RERANKER_MODEL`, so it ranks any document the first stage can return, whether or not it has been tokenized. The cost is one forward pass per candidate and a second model in memory.

An honest caveat, and the 0.1.0 release notes lead with it: the shipped default, `cross-encoder/ms-marco-MiniLM-L-6-v2`, is standard and trained on relevance judgments, but it was chosen for size and CPU viability, and nobody has yet benchmarked it against `maxsim` on JMFTS's own datasets. The harness accepts `vector→crossenc@100` alongside `vector→maxsim@200` for exactly that comparison; the sweep has not been run, and the harness itself ships after the release. Until then, treat the choice as a prerequisites question, not a quality claim, and treat reranked ordering as unvalidated.

Neither method degrades quietly. If the stage you asked for cannot run, the request fails rather than returning the first-stage ranking under a `+rerank` label.

## Tune the hybrid weight to the corpus, don't assume one number

JMFTS's tuned hybrid default weights vector at 0.86 against BM25 at 0.14 (internally labelled `v86b14`). That number was tuned on the BEIR suite average — it is not universal:

| Dataset | vector alone | tuned hybrid | equal-weight `rrf` |
|---|---|---|---|
| TREC-COVID | **0.841** | 0.837 | 0.783 |
| SciFact | 0.677 | 0.709 (best: `v60b40`, 0.711) | — |
| NFCorpus | 0.308 | 0.326 (best: `v60b40`, 0.333) | — |
| FiQA | 0.391 | **0.399** | — |

TREC-COVID is vector-dominant enough that the tuned hybrid weighting is *worse* than plain vector search, and equal-weight `rrf` costs 5.4 points against the tuned hybrid — the clearest evidence that a fixed weighting only earns its keep when BM25 is actually a strong leg. SciFact and NFCorpus both prefer a heavier BM25 share (`v60b40`, 0.60/0.40) than the global default.

The `v86b14`/`v60b40` labels are the benchmark harness's, not the API's. On the wire it is one field on `POST /search/hybrid`: omit `weights` and you get the tuned 0.86/0.14 default, pass `{"vector": 0.60, "bm25": 0.40}` to reweight, and pass an explicit `{}` for equal-weight RRF. If retrieval quality matters more than a quick default, sweep those three shapes against a held-out query set from your own corpus rather than trusting the shipped weighting.

## halfvec is the safe compression default; don't reach for 4-bit quantization for production

Token embeddings can be stored at different compression levels. Internal TurboQuant experiments measured:

- `halfvec` (FP16): 2× compression, **no measured recall loss** — this is what production uses.
- A 4-bit quantized type (`tqvec`, used only in one benchmark database): 5.8× compression, but only **0.260 recall@10** on point queries — a real quality cliff, not a rounding error.

If you're evaluating storage tradeoffs, `halfvec` is the one with evidence behind it. The 0.1.0 schema declares no 4-bit column at all — `tqvec` lived in a benchmark database, and what survives in the release is a cast in the query path written to tolerate such a column if one existed. Nothing here suggests it is safe to run against real traffic.

## Over-window text is refused, so success needs no truncation field

The embedder used to truncate anything past 512 tokens and report bare success. That is fixed, and the fix is a refusal rather than a report: the chunker caps every splitting strategy to a hard size and bounds its merge step so short pieces can't glue back together into one oversized chunk, and `POST /documents/{id}/embed` **raises** on content that does not fit — a `text_too_long` error carrying `token_count`, `limit`, `chars_total`, and the remedy (chunk first, or ask for a document vector only with `with_tokens=false`).

A successful embed therefore still answers `{"document_id": …, "embedded": true, "with_tokens": …, "token_count": …}`, and that is now safe to trust: the only path to a partial embedding is the one that errors. `token_count` counts *selected* token embeddings and was never a truncation signal — do not read it as one.

The practical rule is unchanged for anything near the window: chunk first. This matters most for a corpus of conversation transcripts or long-form documentation, where individual messages or sections routinely sit near that boundary.

## Batch loads are embedding-bound, not database-bound

A write-path baseline (CPU embedding) measured document creation at ~1,900 ops/s *without* an embed call, dropping to ~13 ops/s once embedding is included — embedding is roughly 100× the cost of the database write itself. If you're loading a corpus in bulk: put the embedding step on CUDA before optimizing anything else, and don't expect gains from database-side tuning to matter until you do. There is no batch document-create endpoint yet (each document is a separate round trip), so a client-side embedding pipeline ahead of individual creates is the current path to real throughput.

## Gate on a score only when the method returns a real one

If a caller needs to *decide* something from a search score — inject retrieved context or stay silent, keep a result or discard it — the method choice stops being a quality question and becomes a correctness question. `hybrid` fuses by **rank**: each leg contributes `weight/(60+rank)`, so the fused score carries no information about how similar anything actually was. Measured live against a real store, a relevant query and a nonsense query returned the same five score values. `auto` frequently routes to `hybrid`, so it inherits the same property.

`vector` returns a cosine similarity that separates: in the same live measurement, relevant hits scored 0.46–0.54 against 0.22–0.33 for irrelevant ones on the same subtree. So: rank with `hybrid`, threshold with `vector`. A downstream consumer that applies a similarity floor — an agent memory deciding whether a recalled document is worth injecting, say — has exactly one usable method. This surfaced in the [Tau integration](../integrations/tau-jmfts.md), where a retrieval reflex has to make that call with no human in the loop.

---

The recipes above tune the retrieval stack. The rest of the page is corpus shapes — jobs the data model already supports that do not follow obviously from "hybrid search over PostgreSQL."

!!! note "Shipped surface, unrehearsed walkthroughs"
    Every endpoint named below exists in the current API. None of these entries has been run end to end as a written walkthrough, so treat them as designs you can build today, not procedures that were rehearsed.

## Turn a subtree into a question-answering service

`POST /search/synthesize` runs retrieval and then a grounded answer pass over what came back, using the OpenAI-compatible endpoint configured by `JMFTS_LLM_BASE_URL` / `JMFTS_LLM_MODEL` — JMFTS hosts no model of its own. Scope it with `parent_id` and you have "ask the docs" over exactly that slice of the corpus, with no agent framework and no separate vector-database-plus-glue deployment: ingestion, retrieval, and synthesis are one service. The answer pass is one LLM call, so its latency is your model's, not the appliance's — on a slow local model it can dominate the request.

## Keep a reading pile that files itself

The `wiki:arxiv`, `wiki:url`, and `wiki:pdf` ingestion pipelines are idempotent on `(content_hash, parent_id)`, so a cron job feeding a "reading" root can be dumb and safe — re-running an ingest is a no-op. From there the appliance does the librarian work: `raptor` builds summary nodes above the papers so the pile is skimmable top-down, `maxsim` answers "which paper said this phrase" at token-level precision, and typed `document_links` (`cites`, `derived_from`, …) record *why* two papers are related rather than just that they are. The `wiki:*` usetypes ship with seeded `usetype_presentations`, so `/view/{id}` renders the pile as browsable pages instead of JSON.

## Archive transcripts on the time they happened

`documents.event_time` is domain time, deliberately separate from `created_at` (system time). A meeting archive backfilled from two years of recordings gets `event_time` per document, so "what was discussed around the outage" is answerable even though everything was ingested last Tuesday. The `transcript` and `conversation` pipelines target exactly this shape, and idempotent ingestion means re-running a backfill fills gaps without duplicating what already landed.

## Record facts that can be corrected without being erased

The triple store is bitemporal: `valid_from`/`valid_until` say when a fact was true in the world; `recorded_at` says when this store learned it. Superseding a fact sets `invalidated_at`/`invalidated_by` and leaves the old row in place. That is the exact data model a postmortem or compliance question needs — "what did we believe on March 3rd" is a query, not an archaeology project. `fact_type` (`atemporal | static | dynamic`) marks which facts are even allowed to go stale, so a staleness audit knows what to skip.

## Audit a corpus the way you lint code

`POST /graph/lint` runs orphan, contradiction, staleness, and coverage audits in one transaction, with the thresholds in the request body. The rest of `/graph` describes structure rather than defects: `centrality` and `subtree-authority` find the load-bearing documents, `communities` finds the topic clusters nobody drew on purpose. Wire lint into the same cron that ingests, and a documentation corpus gets a health report on the same cadence as its content — the report names the orphaned page and the contradicted fact instead of a reviewer having to notice them.

## Serve several audiences from one appliance

Two features compose here. `search_contexts` are named, server-stored search presets — method, weights, `usetype`/`parent_id` filters — referenced by name via any search endpoint's `context` param, so "support search" and "research search" become one-word choices instead of client-side parameter lore. Subtree RBAC scopes who sees what: a grant on a document makes it an access-control root, grants are additive down the `path`, and `write` implies `read`. One appliance holds several projects' corpora with per-principal visibility — with one sharp default to respect: a document under no access-control root is unprotected.

## Store prompts in the corpus they run against

`/templates` is prompt-template CRUD plus `render` and `search`. The non-obvious half is the `search`: the prompt library is itself a corpus, so "which prompt do we have for summarizing incident timelines" is a retrieval query, not a grep through a `prompts/` directory. `render` produces the filled prompt server-side, so every caller shares one canonical copy instead of a locally drifted paste — and because templates are documents, they get the same tree placement and links as everything else.
