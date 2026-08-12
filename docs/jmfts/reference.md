---
title: "Reference"
category: "reference"
status: "draft"
---

# JMFTS — Reference

<p class="axis">Cognition × Application</p>

Table schema, query API, scoring parameters, and the pgvector index definitions.

!!! note "Draft"
    Built for lookup, not narrative reading. Endpoint tables give verb, path, and purpose — not every parameter; a running instance's `/openapi.json` (or `/docs`) is the exact contract. Written from `schema.sql`, `.env.example`, and the source repo's `docs/API_UNIFICATION_CONTRACT_NOTES.md`.

## Data model

| Table | Holds |
|---|---|
| `documents` | The tree. `parent_id` + a `path` JSONB array of ancestor ids for subtree queries; `content`; a 768-dim `embed` vector; `usetype` for classification; a nullable explicit sibling `position`; `created_at`/`updated_at` (system time) and a separate nullable `event_time` (domain time, for imported content whose ingest time means nothing — transcripts, backfills). |
| `token_embeddings` | Per-token late-interaction vectors — `embed_256`/`384`/`512` as `halfvec`, one row per selected token, `tier` marking which top-N% importance band it fell in. Only 256-dim is populated in a default deployment; 384/512 exist for benchmarking retention levels. |
| `document_links` | Typed graph edges between documents (`link_type`, a `score`, JSONB `metadata`). |
| `predicates` / `triples` | The knowledge graph. A triple is `(subject_id, predicate_id, object_id)`, unique per combination, with a bitemporal split: `valid_from`/`valid_until` (when the fact was true) vs. `created_at`/`recorded_at` (when this store learned it). `fact_type` is `atemporal | static | dynamic` (Zep/Graphiti taxonomy). Superseding a fact sets `invalidated_at`/`invalidated_by` rather than deleting the row. |
| `search_indexes`, `search_index_members`, `search_index_entries`, `search_term_postings`, `search_term_stats` | The BM25 inverted index: which subtrees belong to an index, per-document length (for normalization), term→document postings, and per-term document frequency (for IDF). `search_indexes.config` carries `k1`/`b`; `capabilities` flags whether an index supports `bm25`/`maxsim`. |
| `search_contexts` | Named, reusable search-parameter presets (method, weights, `usetype`/`parent_id` filters) stored as JSONB `config`, referenced by name from any search endpoint's `context` param. |
| `usetype_presentations` | Per-`usetype` rendering rules for `/view/{id}` — which renderer, how children collapse, how links render. Seeded for the built-in `wiki:*` taxonomy and core usetypes (`markdown`, `chunk`, `conversation`, `raw`, `transcript`). |
| `principals`, `api_tokens`, `access_grants` | Subtree RBAC. The shared owner bearer token bypasses all checks and has no row. A grant on a document makes it an **access-control root**; a principal's effective right on any document is the highest grant on any ACR at or above it on its `path` (grants are additive; `write` implies `read`). A document under no ACR is unprotected — single-user default. |

## Auth and CORS

Every request needs `Authorization: Bearer <token>`.

| Setting | Default | Meaning |
|---|---|---|
| `JMFTS_API_TOKEN` | blank → ephemeral, printed to stdout at boot | Set a value to pin a fixed token. A blank token never means "allow all." |
| `JMFTS_CORS_ORIGINS` | `[]` | JSON list of allowed browser origins. Empty = server-to-server only. `"*"` is rejected. |

## Endpoint families

All routes are generated from a service-layer `@expose` registry (`jmfts_core/services/`), not hand-written per-route — see `docs/API_UNIFICATION_CONTRACT_NOTES.md` in the source repo for the conversion history and per-endpoint divergence notes.

| Family | Prefix | Covers |
|---|---|---|
| Documents | `/documents` | CRUD, tree navigation (`children`/`ancestors`/`siblings`/`subtree`), `embed`, `tokens`, `split`, `chunk`, `segment`, `raptor` (+ `raptor/portfolio`), `extract-facts`, `links`. |
| Search | `/search` | `vector`, `fulltext`, `bm25`, `maxsim`, `hybrid`, `synthesize`, `auto`, plus a convenience `GET /search/?q=`. |
| Triples | `/triples` | Predicates CRUD, triple create/query/path-find, `invalidate`, `supersede`. |
| Templates | `/templates` | Prompt-template CRUD, `render`, `search`. |
| Graph | `/graph` | `centrality`, `subtree-authority`, `spines`, `communities`, `diff`, `stats`, `lint`. |
| Indexes | `/indexes` | Index CRUD, root membership, `refresh`, `index-document/{id}`. |

A caller-facing note: several `GET` endpoints across these families lost their FastAPI-level numeric/pattern query-param validation during the migration to the `@expose` registry (a raw scalar query param carries no `Query(ge=..., pattern=...)` without importing FastAPI into the core layer). Examples: `GET /search/`'s `limit` no longer enforces `1–100` server-side; several `/graph/*` `metric`/`scope` params no longer enforce their allowed-value pattern. **Request-body** (`BaseModel`) field constraints are unaffected — `SearchRequest.limit`, `ChunkRequest.max_tokens`, `LintRequest`'s thresholds, and similar all still validate. If you are calling a `GET` endpoint's scalar query params with untrusted values, validate them client-side rather than relying on a 422.

## Response envelope

`DocumentResponse`: `id`, `parent_id`, `title`, `content`, `structured_content`, `path`, `usetype`, `position`, `event_time`, `created_at`, `updated_at`, `content_hash`. `embed` is opt-in (`?include_embed=true`) and omitted otherwise — every route that returns documents serializes through this one converter, so the field set is identical across `/documents`, `/search/*`, `/triples/*`, and `/templates/*`.

`SearchResponse`: `results[]` (each a scored `DocumentResponse`), `total`, `latency_ms`.

## Scoring parameters

| Setting | Default | Notes |
|---|---|---|
| `JMFTS_BM25_K1` | `1.2` | Term-frequency saturation. |
| `JMFTS_BM25_B` | `0.75` | Length normalization strength. |
| `JMFTS_TOKEN_TOP_PERCENT` | `0.10` | Fraction of a document's tokens kept for late interaction, selected by MMR + attention variance + stopword penalties. |
| `JMFTS_TOKEN_EMBED_DIMS` | `[256, 384, 512]` | Matryoshka dims the schema *supports*; only 256 is populated by default. |
| Hybrid vector/BM25 weight | corpus-dependent | Not a single global default — see the [Cookbook](cookbook.md) for measured weightings and why the right one varies by dataset. |
| `JMFTS_RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Second-stage model for `?rerank=true&rerank_method=cross_encoder`. Any Hub cross-encoder. |
| `JMFTS_RERANKER_DEVICE` | blank | Blank follows `JMFTS_EMBEDDING_DEVICE`. Pin only to split the two across devices. |
| `JMFTS_RERANKER_MAX_LENGTH` | `512` | Tokens per (query, document) pair. |
| `JMFTS_RERANKER_BATCH_SIZE` | `32` | Pairs scored per forward pass. |

## Embedding and LLM configuration

| Setting | Default | Notes |
|---|---|---|
| `JMFTS_EMBEDDING_MODEL` | `nomic-ai/modernbert-embed-base` | Produces the 768-dim document vector and the token-level embeddings. |
| `JMFTS_EMBEDDING_DEVICE` | `cpu` | Set `cuda` for GPU-accelerated bulk ingestion — see the [DevOps Manual](devops.md) for why this matters. |
| `JMFTS_EMBEDDING_BATCH_SIZE` | `32` | |
| `JMFTS_LLM_BASE_URL` / `JMFTS_LLM_MODEL` / `JMFTS_LLM_TIMEOUT` | none pinned | OpenAI-compatible endpoint for RAPTOR summarization and read-side synthesis. JMFTS does not host its own model — see the DevOps Manual. |
| `JMFTS_EXTRACTION_LLM_BASE_URL` / `_MODEL` / `_TIMEOUT` | none pinned | Separate endpoint/model for fact extraction, if you want it distinct from the summarization LLM. |

## Vector indexes

| Column | Index | Notes |
|---|---|---|
| `documents.embed` (768-dim `vector`) | HNSW, `m=16, ef_construction=64`, cosine | Document-level similarity. |
| `token_embeddings.embed_256` (`halfvec`) | IVFFlat, `lists=1024`, cosine | The active late-interaction column in a default deployment. |
| `token_embeddings.embed_384` / `embed_512` (`halfvec`) | HNSW, `m=16, ef_construction=64`, cosine | Present in schema, unpopulated unless a deployment opts into a higher retention tier. |

`pg_trgm` is also enabled, for fuzzy/trigram fallback in full-text search.
