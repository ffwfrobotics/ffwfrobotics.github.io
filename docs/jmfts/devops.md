---
title: "DevOps Manual"
category: "devops"
status: "draft"
---

# JMFTS — DevOps Manual

<p class="axis">Cognition × Acquisition</p>

How JMFTS runs in production: sizing PostgreSQL and pgvector, where the embedding model sits, and what an index rebuild costs you.

!!! note "Draft"
    Written against the public [0.1.0 release](https://github.com/jmccardle/jmfts/releases/tag/0.1.0) — its `Dockerfile`, `docker-compose.yml`, and setup scripts — plus benchmark and defect write-ups that are not in that release yet (see [Documents not in this release](#documents-not-in-this-release)). Not yet checked against a deployment outside the maintainer's own.

## Getting it

JMFTS is public as of `0.1.0`:

```bash
git clone https://github.com/jmccardle/jmfts.git
cd jmfts && git checkout 0.1.0    # or stay on the branch tip
```

Everything below runs from that checkout. `0.1.0` is a first public cut of a system that has been running as a personal appliance — it works, and it is not a product; the release notes are explicit that reranked ordering in particular is unvalidated.

## Two ways to run it

**Docker Compose** — a Postgres+pgvector container and the API container, both managed together. This is the fastest path to a working instance and the one the [quickstart](tutorials/quickstart.md) uses.

```bash
docker compose up --build -d      # first run builds the image (CPU torch)
docker compose logs -f api        # watch startup — this is where the auth token line appears
docker compose down               # stop (keeps the DB + model-cache volumes)
docker compose down -v            # stop and WIPE the DB + the downloaded embedding model
```

**Native** — your own PostgreSQL with the `pgvector` extension, plus a Python 3.11+ environment:

```bash
pip install -e ".[dev]"           # dev adds pytest/black/ruff; plain -e . is enough to run
python -m scripts.setup_db        # creates the DB (if missing) and applies schema.sql
uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload
```

Either way, the API listens on port 8100 and every setting reads from the environment with a `JMFTS_` prefix. `.env.example` is the annotated list of those settings; the [Reference](reference.md) gives the built-in default behind each one, which is not always what `.env.example` shows.

The test suite runs against a throwaway database, never the appliance's: `./scripts/run_tests_docker.sh` stands up its own pgvector container and CPU embedder, and bare `pytest` needs the local role to hold `CREATEDB`.

## What the Compose stack actually runs

| Container | Image | Notes |
|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | `schema.sql` is mounted as `01_schema.sql` and runs once, on a fresh data volume. `127.0.0.1:5433` → container `5432`, chosen so it never collides with a host Postgres. |
| `api` | built from the repo's `Dockerfile` | CPU-only image — `uvicorn --reload` with `jmfts_core/` and `api/` bind-mounted, so edits reload live without a rebuild. `127.0.0.1:8100`. |

Both publications are bound to loopback, not `0.0.0.0` — the dev stack is not reachable from the LAN unless you change that yourself.

`schema.sql` is the complete canonical DDL — extensions, every table, every index. It is what bootstraps a fresh database. The numbered files in `migrations/` (`002` through `010` in the 0.1.0 release) are upgrade deltas for a database that already exists; you do not need them to stand up a new instance, only to carry an existing one forward.

The Compose image is deliberately **not** a production build: embedding runs on CPU there, which is fine for development and wrong for bulk ingestion (see [Sizing the write path](#sizing-the-write-path-and-why-it-is-cpu-bound) below).

## Auth

Every request needs `Authorization: Bearer <token>`. Two modes, both controlled by `JMFTS_API_TOKEN`:

- **Left blank** — the server generates a token at startup and prints it to stdout, the same pattern Jupyter uses. There is no state where a blank token means "allow all."
- **Set to a value** — that token is pinned, and the startup message is silenced. The Compose file pins `jmfts-dev-local` by default specifically so other local services (an agent harness, a test client) can point at a known value; override it by exporting `JMFTS_API_TOKEN` before `docker compose up`.

`JMFTS_CORS_ORIGINS` is a JSON list of allowed browser origins and defaults to empty — server-to-server only, no `Origin` header accepted. `"*"` is rejected outright when credentials are in play; there is no wildcard escape hatch.

## The embedding model

Document and token embeddings both come from `nomic-ai/modernbert-embed-base` (configurable via `JMFTS_EMBEDDING_MODEL`). First boot downloads it — a few hundred MB — into a cache volume (`hf_cache` in Compose, `~/.cache/huggingface` natively), and it persists across restarts.

`JMFTS_EMBEDDING_DEVICE` is `cpu` in the dev image on purpose (no CUDA in that container). Set it to `cuda` for anything that embeds at volume — see the next section for why this matters more than it sounds like it should.

## The reranker is a second model, loaded only if asked

`?rerank=true&rerank_method=cross_encoder` loads a second model, separate from the embedder. The default is `cross-encoder/ms-marco-MiniLM-L-6-v2` (~22M params), small enough to run on CPU, and it downloads into the same Hugging Face cache on first use. Change it with `JMFTS_RERANKER_MODEL` — any Hub cross-encoder works, but a larger one is a real GPU-memory decision on top of the embedder, not a free swap.

`JMFTS_RERANKER_DEVICE` defaults to blank, which means "follow `JMFTS_EMBEDDING_DEVICE`". A CPU-only deployment therefore stays CPU-only without setting a second variable. Pin it only when you want the reranker on a different device from the embedder.

Nothing loads until a request actually asks for reranking, so a deployment that never passes `rerank=true` pays nothing. When a request does ask and the model cannot load, the request fails — it does not quietly return the unreranked ranking.

## Sizing the write path — and why it is CPU-bound

A 2026-07-23 baseline (`scripts/benchmark_write.py`, CPU embedding, empty pgvector DB) measured each write op in isolation. The 0.1.0 release keeps only the product CLI in `scripts/`, so the harness that produced these numbers is not in the tarball you can clone today — it ships with the evaluation work described [below](#documents-not-in-this-release):

| op | ops/s | p50 latency |
|---|---|---|
| document create (no embed) | ~1,943 | 0.50 ms |
| document create **+ embed** | ~13 | 49 ms |
| triple upsert | ~1,227 | 0.82 ms |

The bare insert path — the `path` trigger, HNSW index maintenance — is sub-millisecond and was never the bottleneck. Embedding is roughly **100× the cost** of everything else in the write path combined, and it is the thing the CPU dev image is worst at. If you are sizing a deployment for bulk ingestion, treat `JMFTS_EMBEDDING_DEVICE=cuda` as the first lever, not a nice-to-have; batching embedding calls is the other one, though there is no batch document-create endpoint yet — see [Known gaps](#known-gaps-and-hazards) below.

This baseline did not include the final commit's durability flush, and CUDA throughput was not measured — both are open items on the benchmark backlog that lands with the harness, not settled numbers.

## Index maintenance

The vector side (`documents.embed`, `token_embeddings.embed_256/384/512`) is maintained automatically by pgvector's HNSW/IVFFlat indexes on every insert — no separate rebuild step.

The BM25 side is different: `POST /indexes/{index_name}/index-document/{document_id}` (backed by `index_document`) is idempotent as of a since-fixed defect (it now subtracts a document's old contribution before re-adding, short-circuiting on an unchanged content hash), so indexing a document you've already indexed no longer inflates the corpus statistics BM25's IDF is derived from. You can index incrementally, document by document, as content arrives. `POST /indexes/{name}/refresh` remains available and rebuilds an index's statistics from scratch — correct by construction, but its cost is proportional to the whole indexed corpus, so reach for it as a repair tool, not a routine one.

## Documents not in this release

`0.1.0` ships code, `README.md`, and `CLAUDE.md`. The design and evaluation documents this manual and the [Cookbook](cookbook.md) cite are being refined for publication and land separately — the release notes say the same about the BEIR harness that produces the retrieval-quality numbers. Source comments citing `INGEST_SPEC.md`, `KNOWN-DEFECTS.md` and `ROADMAP.md` point at those pending documents.

Until they land, the summaries on these pages are the available version of them. Nothing here is retracted by their absence; you just cannot read the long form yet.

| Document | What it holds | Cited by |
|---|---|---|
| `INGEST_SPEC.md` | The ingest pipeline's specification — the part numbers dozens of source comments cite, including the task queue's write-mode reservations. | `task_queue`, `document_blobs`, the ingest worker |
| `KNOWN-DEFECTS.md` | The silent-failure defects below, and the embedding-window reasoning. | this page, the Cookbook |
| `RERANKER_CRITIQUE.md` | Why the original reranker backend was deleted. | this page, the Cookbook |
| `API_UNIFICATION_CONTRACT_NOTES.md` | Conversion history and per-endpoint divergence for the `@expose` registry. | the [Reference](reference.md#endpoint-families) |
| BEIR harness + `scripts/benchmark_write.py` | The measurements behind the hybrid weighting table and the write-path baseline. | the Cookbook, [above](#sizing-the-write-path-and-why-it-is-cpu-bound) |

## Known gaps and hazards

Two of those write-ups are worth knowing about before running this in anger, whether or not you can read them yet:

- **`docs/KNOWN-DEFECTS.md`** — a set of silent-failure defects (embedding truncation past 512 tokens, unbounded chunk merging, the BM25 double-count above) found and fixed against a live instance. All are resolved in the current codebase; the document is kept because the *pattern* — a system that loses text or corrupts a statistic and reports success — is the thing worth internalizing, not just the four fixes.
- **`docs/RERANKER_CRITIQUE.md`** — the write-up that condemned the original reranker backend, which repurposed an NLI model's entailment probability as a relevance score. Resolved on 2026-08-11 by deleting that backend: `?rerank=true` now runs a standard cross-encoder. The document is kept as the reasoning trail, and because its closing caution still holds — the shipped default model was chosen for size and CPU viability, not for measured retrieval quality. See the [Cookbook](cookbook.md) for choosing between the two rerank methods.

## LLM-backed features are optional, and JMFTS does not host one

RAPTOR summarization, fact extraction, and read-side synthesis (`/search/synthesize`) all call out to one OpenAI-compatible endpoint — `JMFTS_LLM_BASE_URL` / `JMFTS_LLM_MODEL` — and there is no second endpoint for the extraction path; `JMFTS_EXTRACTION_*` tunes that request, not its destination. Without one configured, those endpoints report a degraded response rather than failing outright — documents, embeddings, chunking, indexing, and every search method work regardless.

One sharp edge in the defaults: leaving `JMFTS_LLM_*` blank does not mean "no LLM". Each blank field falls through to its `JMFTS_ENSONET_*` counterpart, which points at `http://localhost:8853` — the maintainer's own model orchestrator. On any other host that address is simply not listening, which is why the degraded path is what you see; set `JMFTS_LLM_BASE_URL` explicitly rather than relying on the fallback to be absent.

The deliberate design choice, as of a 2026-07-23 decision: **JMFTS does not reserve a GPU or pin a local model of its own.** It is a client of whatever LLM the calling agent is already using. If you are integrating JMFTS behind an agent that has its own model endpoint, point these settings at that endpoint rather than standing up a separate one for JMFTS.
