---
title: "Cookbook"
category: "cookbook"
status: "stub"
---

# JMFTS — Cookbook

<p class="axis">Action × Application</p>

Recipes for specific JMFTS jobs — tuning matryoshka dimensions, reweighting BM25 against the vector score, adding a reranking stage.

!!! note "Marked stub on purpose"
    The recipes below are real, drawn from the source repo's own benchmark runs and defect write-ups — but they have not been organized into full step-by-step walkthroughs or checked against a fresh deployment, so this page stays `stub` until that pass happens.

## Pick a rerank method by what your corpus already stores

Every search endpoint accepts `?rerank=true`, and `rerank_method` picks the second stage. The two are not ranked best-to-worst — they have different prerequisites, and the right one depends on your corpus.

**`maxsim`** reuses the per-token vectors already in `token_embeddings`, so it loads no model and adds no GPU memory. On the MultiHop-RAG benchmark (609 articles, 2,255 multi-hop queries — a case BEIR's single-hop datasets don't exercise), `vector→maxsim@200` measured **72.2% Hits@4 against plain vector's 58.4%**, a 13.8-point gain that BM25 alone (69.4%) and the tuned hybrid (63.8%) both fall short of.

The catch is the storage. Token embeddings are one row per selected token per document, so the late-interaction index is far larger than the document vectors. A candidate with no stored tokens scores 0 and sinks to the bottom of the reranked list. On a corpus where only part of the tree has been through `/documents/{id}/tokens`, that silently demotes real hits — so use `maxsim` when token coverage is complete, not merely present.

**`cross_encoder`** (the default) reads nothing from the database. It scores each (query, document) pair with a cross-encoder model set by `JMFTS_RERANKER_MODEL`, so it ranks any document the first stage can return, whether or not it has been tokenized. The cost is one forward pass per candidate and a second model in memory.

An honest caveat: the shipped default, `cross-encoder/ms-marco-MiniLM-L-6-v2`, is standard and trained on relevance judgments, but nobody has yet benchmarked it against `maxsim` on JMFTS's own datasets. The harness accepts `vector→crossenc@100` alongside `vector→maxsim@200` for exactly that comparison; the sweep has not been run. Until it is, treat the choice as a prerequisites question, not a quality claim.

Neither method degrades quietly. If the stage you asked for cannot run, the request fails rather than returning the first-stage ranking under a `+rerank` label.

## Tune the hybrid weight to the corpus, don't assume one number

JMFTS's tuned hybrid default weights vector at 0.86 against BM25 at 0.14 (internally labelled `v86b14`). That number was tuned on the BEIR suite average — it is not universal:

| Dataset | vector alone | tuned hybrid | equal-weight `rrf` |
|---|---|---|---|
| TREC-COVID | **0.841** | 0.837 | 0.783 |
| SciFact | 0.677 | 0.709 (best: `v60b40`, 0.711) | — |
| NFCorpus | 0.308 | 0.326 (best: `v60b40`, 0.333) | — |
| FiQA | 0.391 | **0.399** | — |

TREC-COVID is vector-dominant enough that the tuned hybrid weighting is *worse* than plain vector search, and equal-weight `rrf` costs 5.4 points against the tuned hybrid — the clearest evidence that a fixed weighting only earns its keep when BM25 is actually a strong leg. SciFact and NFCorpus both prefer a heavier BM25 share (`v60b40`, 0.60/0.40) than the global default. If retrieval quality matters more than a quick default, sweep `hybrid`, `hybrid_v60b40`, `hybrid_v78b22`, and `rrf` against a held-out query set from your own corpus rather than trusting the shipped weighting.

## halfvec is the safe compression default; don't reach for 4-bit quantization for production

Token embeddings can be stored at different compression levels. Internal TurboQuant experiments measured:

- `halfvec` (FP16): 2× compression, **no measured recall loss** — this is what production uses.
- A 4-bit quantized type (`tqvec`, used only in one benchmark database): 5.8× compression, but only **0.260 recall@10** on point queries — a real quality cliff, not a rounding error.

If you're evaluating storage tradeoffs, `halfvec` is the one with evidence behind it. Deeper compression exists in the codebase for benchmarking purposes only; nothing here suggests it is safe to run against real traffic.

## Check the embed response fields, not just the status code

The embedder used to truncate anything past 512 tokens and report bare success; that is fixed — the chunker now caps every splitting strategy to a hard size, bounds its merge step so short pieces can't glue back together into one oversized chunk, and `POST /documents/{id}/embed` reports `truncated`/`chars_embedded`/`chars_total` instead of a silent `{"embedded": true}`. The defaults are safe to trust now, but the fields exist because truncation is still possible at the boundary — worth checking them on anything near the 512-token window rather than assuming success means complete. This matters most for a corpus of conversation transcripts or long-form documentation, where individual messages or sections routinely sit near that boundary.

## Batch loads are embedding-bound, not database-bound

A write-path baseline (CPU embedding) measured document creation at ~1,900 ops/s *without* an embed call, dropping to ~13 ops/s once embedding is included — embedding is roughly 100× the cost of the database write itself. If you're loading a corpus in bulk: put the embedding step on CUDA before optimizing anything else, and don't expect gains from database-side tuning to matter until you do. There is no batch document-create endpoint yet (each document is a separate round trip), so a client-side embedding pipeline ahead of individual creates is the current path to real throughput.
