---
title: "Reference"
category: "reference"
status: "draft"
---

# JMFTS — Reference

<p class="axis">Cognition × Application</p>

Table schema, query API, scoring parameters, and the pgvector index definitions.

!!! note "Draft"
    Built for lookup, not narrative reading. Endpoint tables give verb, path, and purpose — not every parameter; a running instance's `/openapi.json` (or `/docs`) is the exact contract. Tables are checked against `schema.sql`, `jmfts_core/config.py`, and the `@expose` registry that generates the routes.

!!! warning "Ingestion is ahead of the release"
    The queued ingestion system — `task_queue`, `document_blobs`, `documents.settled`, the `/ingest` family, ingest options, and the worker fleet — is **not in the public [0.1.0 release](https://github.com/jmccardle/jmfts/releases/tag/0.1.0)** and not on `master`. It is 26 commits on the `feat/ingest-lifecycle` branch.

    Everything else here — search, triples, graph, view, access — is 0.1.0. Sections covering unreleased ingestion say so in their own note. Clone the branch, not the tag, if you want to run any of it.

!!! note "Defaults come from the code, not from `.env.example`"
    Settings tables quote the built-in default in `jmfts_core/config.py`. `.env.example` ships a *filled-in* sample for the LLM block (an Ollama URL and a model name) rather than the blank built-in — copy it and you have configured an endpoint, not accepted a default.

## Data model

| Table | Holds |
|---|---|
| `documents` | The tree. `parent_id` + a `path` JSONB array of ancestor ids for subtree queries; `content`; a 768-dim `embed` vector; `usetype` for classification; a nullable explicit sibling `position`; `created_at`/`updated_at` (system time) and a separate nullable `event_time` (domain time, for imported content whose ingest time means nothing — transcripts, backfills). **(branch)** adds `settled` (`in_flight`, `settled` or `failed`), the ingestion lifecycle flag the retrieval indexes are partial on — an `in_flight` node is invisible to search until its subtree finishes. |
| `token_embeddings` | Per-token late-interaction vectors — `embed_256`/`384`/`512` as `halfvec`, one row per selected token, `tier` marking which top-N% importance band it fell in. Only 256-dim is populated in a default deployment; 384/512 exist for benchmarking retention levels. |
| `document_blobs` **(branch)** | Uploaded bytes for `POST /ingest/file`. One row per document (`UNIQUE`), holding the `lob_oid` of a Postgres **large object** plus `mime_type`, `byte_size`, `content_hash`. The bytes are not in the table: `ON DELETE CASCADE` removes the row and orphans the object, so deletion goes through `BlobRepository` (`lo_unlink` first), and `pg_dump` in plain format needs `-b` or the restore points at bytes that no longer exist. |
| `task_queue` **(branch)** | The ingest scheduler's rows — see [Ingest task queue](#ingest-task-queue) for the column set and the lifecycle. `scope_document_id` + `write_mode` (`self`, `children` or `subtree`) declare what region of the tree a task **reserves** while it runs, and the claim query refuses a task whose region overlaps one already `claimed`, `running` or `batched`. Retry policy lives in `TaskQueueRepository.fail()`, not in SQL. |
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

All routes are generated from a service-layer `@expose` registry (`jmfts_core/services/`), not hand-written per-route: one decorated service method is both the in-process Python call and the REST route, and `tests/test_api_parity.py` asserts the registry and the mounted routes stay in bijection. `docs/API_UNIFICATION_CONTRACT_NOTES.md`, which carries the conversion history and the per-endpoint divergence notes, is one of the design documents held back from 0.1.0 (see [Documents not in this release](devops.md#documents-not-in-this-release)).

| Family | Prefix | Covers |
|---|---|---|
| Documents | `/documents` | CRUD, tree navigation (`roots`/`children`/`ancestors`/`siblings`/`subtree`), `embed`, `tokens`, `split`, `chunk`, `segment`, `raptor` (+ `raptor/portfolio`), `extract-facts`, `links`. |
| Ingest | `/ingest` | Two paths under one prefix, from two different eras — see [Two ingest paths](#two-ingest-paths). `GET /ingest/pipelines` and `POST /ingest` are the synchronous named-pipeline path and are in 0.1.0. **(branch)** adds the queue: `POST /ingest/file` (multipart upload; stores bytes, enqueues `probe`, **returns before the work is done**), `file/{id}/frontier`, `explain`, `analyze`. |
| Conversations | `/conversations` | `ingest` — a whole conversation into the tree in one call. |
| Search | `/search` | `vector`, `fulltext`, `bm25`, `maxsim`, `hybrid`, `synthesize`, `auto`, plus a convenience `GET /search/?q=`. |
| Search contexts | `/search-contexts` | CRUD for the named parameter presets any search endpoint's `context` param resolves. |
| Triples | `/triples` | Predicates CRUD, triple create/query/path-find, `invalidate`, `supersede`. |
| Templates | `/templates` | Prompt-template CRUD, `render`, `search`. |
| Graph | `/graph` | `centrality`, `subtree-authority`, `spines`, `communities`, `neighbors`, `diff`, `stats`, `lint`. |
| Indexes | `/indexes` | Index CRUD, root membership, `refresh`, `index-document/{id}`. |
| View | `/view` | Rendered read side: `/view/{id}`, `expand-children`, `breadcrumbs`, `back-references`. |
| Presentations | `/usetype-presentations` | CRUD for the per-`usetype` rendering rules `/view` applies. |
| Access | `/access` | Principals, their tokens, and per-document grants — the subtree RBAC surface. |

A caller-facing note: several `GET` endpoints across these families lost their FastAPI-level numeric/pattern query-param validation during the migration to the `@expose` registry (a raw scalar query param carries no `Query(ge=..., pattern=...)` without importing FastAPI into the core layer). Examples: `GET /search/`'s `limit` no longer enforces `1–100` server-side; several `/graph/*` `metric`/`scope` params no longer enforce their allowed-value pattern. **Request-body** (`BaseModel`) field constraints are unaffected — `SearchRequest.limit`, `ChunkRequest.max_tokens`, `LintRequest`'s thresholds, and similar all still validate. If you are calling a `GET` endpoint's scalar query params with untrusted values, validate them client-side rather than relying on a 422.

## Response envelope

`DocumentResponse`: `id`, `parent_id`, `title`, `content`, `structured_content`, `path`, `usetype`, `position`, `event_time`, `created_at`, `updated_at`, `content_hash`. `embed` is opt-in (`?include_embed=true`) and omitted otherwise — every route that returns documents serializes through this one converter, so the field set is identical across `/documents`, `/search/*`, `/triples/*`, and `/templates/*`.

`SearchResponse`: `results[]` (each a scored `DocumentResponse`), `total`, `latency_ms`.

## Scoring parameters

| Setting | Default | Notes |
|---|---|---|
| `JMFTS_BM25_K1` | `1.2` | Term-frequency saturation. |
| `JMFTS_BM25_B` | `0.75` | Length normalization strength. |
| `JMFTS_TOKEN_TOP_PERCENT` | `0.50` | Fraction of a document's tokens kept for late interaction, selected by MMR + attention variance + stopword penalties. Half is a deliberately generous default — it keeps the tiered `tier<=X` bands usable for benchmarking rather than sizing the index for production. |
| `JMFTS_TOKEN_EMBED_DIMS` | `[256]` | Matryoshka dims actually populated. The schema reserves `embed_384`/`embed_512` columns and indexes them, but nothing writes them unless a deployment opts in here. |
| `JMFTS_BM25_EXCLUDE_USETYPES` | `["entity", "summary"]` | Usetypes held out of the BM25 index — derived nodes, not source text. |
| `JMFTS_SEARCH_EXCLUDE_USETYPES` | `["entity", "summary"]` | Usetypes held out of search results. |
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
| `JMFTS_EMBEDDING_BATCH_SIZE` | `32` | Texts per forward pass on the document path; `JMFTS_TOKEN_BATCH_SIZE` (also `32`) is the token path's. |
| `JMFTS_EMBEDDING_TOKEN_WINDOW` | `512` | The token/MaxSim path's cap. It is a **memory** budget, not a model limit: token embedding runs the transformer with `output_attentions=True`, which materializes every layer's attention matrix (~277 MB at 512, ~4.4 GB at 2048). Text over the window is refused, not truncated. |
| `JMFTS_EMBEDDING_DOC_WINDOW` | `8192` | The document-vector path's cap — the model's real limit. |
| `JMFTS_CHUNK_MAX_CHARS` | `1800` | Hard cap every chunking strategy is held to, sized to land inside the token window (~5 chars per subword token, plus prefix headroom). |
| `JMFTS_LLM_BASE_URL` / `JMFTS_LLM_MODEL` / `JMFTS_LLM_TIMEOUT` | blank / blank / `0` | OpenAI-compatible endpoint for RAPTOR summarization, fact extraction, and read-side synthesis. Each blank field falls back to its `JMFTS_ENSONET_*` counterpart, so what a stock instance actually dials is the fallback, not nothing. JMFTS does not host its own model — see the [DevOps Manual](devops.md). |
| `JMFTS_ENSONET_URL` / `_MODEL` / `_TIMEOUT` | `http://localhost:8853` / `THUDM_GLM4_32b` / `180.0` | The fallback the blanks above resolve to — the maintainer's own model orchestrator. Point `JMFTS_LLM_*` at your endpoint and these stop being reachable. |

There is no separate extraction endpoint. Fact extraction shares the LLM settings above; `JMFTS_EXTRACTION_*` tunes the extraction *request* (`MAX_FACTS` `5`, `CONFIDENCE_THRESHOLD` `0.5`, `ENTITY_SIMILARITY_THRESHOLD` `0.8`, `TEMPERATURE` `0.1`, `MAX_TOKENS` `4096`), not where it is sent.

## Two ingest paths

`/ingest` carries two unrelated designs, and the names in them do not interchange.

| | Synchronous pipelines | The queue **(branch)** |
|---|---|---|
| Endpoints | `GET /ingest/pipelines`, `POST /ingest` | `POST /ingest/file`, `file/{id}/frontier`, `explain`, `analyze` |
| Takes | text plus a **pipeline name** | bytes; the format is **detected** |
| Names | `markdown`, `raw`, `conversation`, `transcript`, `wiki:url`, `wiki:arxiv`, `wiki:pdf` | `text`, `pdf`, `docx`, `pptx`, `zip`, … from `detect_format` |
| Returns | a finished tree, in the request | an `in_flight` node and a queued `probe` |
| In 0.1.0 | yes | no |

The name sets overlap in exactly the way that causes trouble: **`markdown` is a pipeline and is not a format.** Nothing in the bytes distinguishes authored markdown from a `.txt` file starting with `#`, so `detect_format` reports both as `text` and one Part 4 entry covers them. `POST /ingest/explain` accepts `{"format": "markdown"}` — an unknown format is a legal question — and answers with every row `impossible` or `not_applicable`, which reads like a verdict on markdown and is a verdict on the name.

`POST /ingest` is being retired in favour of the queue; it keeps its synchronous behaviour unchanged in the meantime.

## Ingest task queue

!!! warning "Branch only"
    Everything from here to [Vector indexes](#vector-indexes) is on `feat/ingest-lifecycle`, not in 0.1.0.

`POST /ingest/file` stores the bytes, enqueues one `probe` task and returns. Everything after that is a worker draining `task_queue`. A task is one unit of work scoped to one node.

### Task types

Ten declared, seven with handlers today. A task type with no handler is enqueued only if something schedules it; nothing does.

| `task_type` | Handler in | Does |
|---|---|---|
| `probe` | `ingest_tasks.py` | Reads the stored bytes, detects the format, measures patterns, and schedules the rest from Part 4's table. |
| `extract:text` | `structure_tasks.py` | Pulls text out of the file — the entry point every format converges on. |
| `structure:declared` | `structure_tasks.py` | Builds the tree the document itself declares (headings, outline, page breaks). |
| `structure:inferred` | `structure_tasks.py` | Builds a tree for a document that declares none, by chunking. |
| `structure:semantic` | `rollup_tasks.py` | PELT changepoint segmentation over a node's children. Runs on the way back up, once the children have embeddings. |
| `summarize` | `rollup_tasks.py` | Gives a container node a text embedding from its children. Concatenates while that fits the window. |
| `summarize:llm` | `rollup_tasks.py` | The same job when concatenation does not fit. Split out so it can carry its own badge and its own pool. |
| `ocr` | — | Declared, no handler. |
| `extract:tables` | — | Declared, no handler. |
| `extract:images` | — | Declared, no handler. |

`summarize` does not call an LLM. It measures, and if the concatenated children are over the embedding window it enqueues `summarize:llm` and completes. That deferral is deliberate: whether a node needs a model is a fact about its children right now, and the only way to learn it is to concatenate and tokenize.

The ten split into two groups by **who schedules them**, which is why only seven ever appear in a plan:

| | Types | Scheduled by | In `explain`/`analyze` |
|---|---|---|---|
| Downward pass | `probe`, `extract:text`, `extract:tables`, `extract:images`, `ocr`, `structure:declared`, `structure:inferred` | `plan_after_probe`, a pure function of `(format, patterns, options)` | yes, all seven, in table order |
| Rollup | `structure:semantic`, `summarize`, `summarize:llm` | the settling walk, which re-reads the tree | **no** |

The rollup rungs cannot be forecast from a format name: they are decided by children that do not exist when `probe` runs. A plan that listed them would be describing work it cannot have evaluated.

### Row lifecycle

| `status` | Meaning | Claimable | Holds a reservation |
|---|---|---|---|
| `pending` | queued | yes | no |
| `claimed` | a worker took it, has not started | no | yes |
| `running` | a worker is executing it | no | yes |
| `batched` | submitted to an external batch provider | no | yes |
| `completed` | terminal | no | no |
| `failed` | terminal, or retryable with backoff | if retryable and under cap | no |

`pending` reserves nothing, which is what lets thousands of pending tasks sit over one subtree without blocking each other. `claimed` and `running` are separate so a row stuck in `claimed` reads as "the worker died before it began" rather than "died halfway through".

### Columns beyond the obvious

| Column | Notes |
|---|---|
| `write_mode` | `self`, `children`, or `subtree`. What the task reserves, checked at claim time. A `self` task conflicts with another `self` on the same node; a `subtree` task conflicts with anything at or under its node, in either direction. |
| `dependencies` | Integer array of task ids that must be `completed` first. Ordering **within** one node only. Cross-level ordering is not expressed here — a planned list goes stale the moment a child is added, so the settling walk re-reads the tree instead. |
| `params` / `param_fingerprint` | What the task was asked to do, and a hash of it. The re-run diff is keyed on `(task_type, param_fingerprint)`, so a task is not offered twice with the same parameters. |
| `service_badge` | Which pool should run this. Set from the routing policy at enqueue. `NULL` means anyone. |
| `claimed_by` | Worker identity, from `--worker-id`. |
| `heartbeat_at` | Liveness while the task is held. Measures "the worker is still alive", **not** "the task has run this long". |
| `batch_id` / `batched_at` | Where a `batched` task is parked and since when. Kept after completion as part of the record of how the answer was obtained. |
| `retry_count` / `max_retries` / `retryable` / `retry_after` | Backoff is exponential with jitter. `retryable` is derived from `error_type` on failure. |

`error_type` is one of `retryable`, `permanent`, `timeout`, `dependency`. `retryable` and `timeout` schedule another attempt; `permanent` and `dependency` do not, and a task that will not run again puts its node into `settled = 'failed'` so the settle walk stops waiting on it.

### No endpoint reads the queue

`task_queue` has no REST surface. Nothing lists rows, shows which task failed, retries one, or cancels one — the frontier's counts are the whole API-level view of a running ingestion. Operationally that leaves SQL against the appliance, or `scripts/e2e_ingest_corpus.py report`, which lists every failed task with its error type alongside the tree shape and per-task-type wall clock.

Re-ingest is in the same state. Reprocessing a document under changed options is specified — diff `(task_type, param_fingerprint)` against the node's attempt log and enqueue only the difference, no re-parse and no duplicate tree — and is not built. Delete and re-upload is the available path.

## Upload semantics

`POST /ingest/file` takes the bytes as a multipart part; `parent_id` and `private` are **query** parameters and `options` is a form field. That split is FastAPI's inference rather than a choice: the bytes make the body a form, so scalars publish as query parameters and only the structured parameter becomes a part.

**Uploads deduplicate on `sha256` of the bytes**, restricted to file nodes this caller may read. Two principals in isolated access zones each get their own node, because neither one's lookup can see the other's.

| Response field | Says |
|---|---|
| `document_id` | The `file` node — the root of the tree ingestion builds. |
| `settled` | `in_flight` at creation. |
| `content_hash` / `blob_ref` | `sha256:<hex>`, and `lob:<oid>` for the Postgres large object holding the bytes. |
| `detected_mime` / `detected_by` / `declared_mime` | What the bytes are, how that was decided (`magic_bytes`, `zip_manifest`, `content_sniff`), and what the client claimed. Nulls are recorded rather than guessed. |
| `attempts` | The node's attempt log as it stands, newest last. |
| `was_existing` | These bytes were already here; `document_id` names a node this request **found**. No document, no blob, nothing enqueued. |
| `linked_into_parent` | The found node was attached to `parent_id` by a `contains` link rather than by parentage. |

Three consequences of deduplication, each of which is a refusal or a surprise rather than a convenience:

**Conflicting options are a 400.** The existing node records the resolved options it was ingested under. An upload of the same bytes asking for anything else fails, naming both sets. The two honest answers are "do the work" and "it was not done"; returning the node as though the new options applied is neither, and the re-run diff that would make the first one possible is not built.

**Placement is a link, not a copy and not a reparent.** With a `parent_id`, an already-stored node gains a `contains` graph edge to that parent and keeps its own `parent_id`. So `GET /documents/{parent}/subtree` does **not** reach it and `GET /documents/{parent}/links` does — a subtree walk is `path`/`parent_id` containment and this edge is in neither. Reparenting instead was rejected: it would change what another principal's document sits under and invalidate the rollups above the new parent, silently, in a request that said nothing about moving anything.

**`private=True` narrows the lookup.** It restricts matching to nodes the caller holds a grant on. Without that, a private upload of bytes already present as a shared node would resolve to the shared node and the caller would not be private at all.

### `private` and the ungoverned-node gap

Access is open by default: a token means the shared knowledgebase, and an upload lands readable by every principal. That is the design, not an oversight — "private until shared" is the opposite assumption and produces bugs of ignorance wherever the stated one holds.

The gap it leaves is narrow and **not repairable after the fact**. Subtree RBAC resolves strictly along the tree path (`R = D.id OR R ∈ D.path`), so a file uploaded with no `parent_id` has no ancestor, no access-control root above it, and nothing governing it — and a grant made later has no path to travel down. The two fixes are both upload-time: a `parent_id` inside an already-governed subtree, or `private=true`, which makes the new node its own access-control root with the uploader as its only grantee at `write`.

## Plan inspection

`POST /ingest/explain` and `POST /ingest/analyze` answer the same question from different amounts of evidence, and both store nothing. Both resolve options through the resolver the upload uses, so an unknown option is a 400 in all three places.

| Call | `patterns_source` | Rows decided |
|---|---|---|
| `explain` `{format}` | `unknown` — nobody said | mostly `conditional` |
| `explain` `{format}` for a format with no prober | `no_prober` — the empty pattern set is a measured fact about this appliance | all |
| `explain` `{format, patterns}` | `supplied` — the caller's hypothesis | all |
| `analyze` `{file}` | `probed` — measured from the bytes | all |

`patterns_source` is load-bearing rather than metadata: an answer that did not say where its patterns came from would be indistinguishable from one that invented them. `patterns_known` is the boolean form of the right-hand column. `patterns_ignored` names supplied keys no condition consults for this format — reported, not rejected, so a real `matched.patterns` block can be pasted in whole and a misspelled pattern is visible instead of silently planned as false.

Per-task rows carry `outcome`, and the vocabulary is finer than it looks:

| `outcome` | Means |
|---|---|
| `enqueued` | The condition holds; a queue row would be written. |
| `skipped` | Recorded as never-attempted, with the reason. |
| `deferred` | The condition holds (or could) and **no handler is registered**, so nothing is queued. |
| `not_applicable` | The condition is false for these patterns. |
| `impossible` | The condition **cannot** hold for this format, whatever the bytes are. |
| `conditional` | Undecided; `if_condition_holds` says which of the first three it would become. |

Alongside: `requires` and `forbids` (patterns, resolved for this format — the declared-structure sentinel replaced by the pattern that format uses, or dropped, which is what makes a row `impossible`), `after`, `write_mode`, and `params` — the resolved options the queue row would carry.

`analyze` adds three blocks `explain` cannot produce. **Check `probe_failed` first**: exactly one of it and `plan` is set, and a null plan means these bytes have no schedule rather than no work. It carries the exception and the same `error_type` classification the real task would get. `file` reports what the bytes are beside what the client declared, with `mime_agrees` null — not false — when one side is unknown. `already_stored` reports that an upload would deduplicate to a named node and run no plan at all, and carries that node's recorded options, which is the only way to predict the conflicting-options 400 in advance.

## Ingest frontier

`GET /ingest/file/{id}/frontier` counts the root node and everything under it by `path`.

| Field | Notes |
|---|---|
| `settled` | The **root node's own** state: `in_flight`, `settled` or `failed`. |
| `nodes_total` / `nodes_settled` / `nodes_in_flight` / `nodes_failed` | Node counts across the subtree. |
| `tasks_unfinished` | Queued tasks under this root still owing work — `pending`, `claimed`, `running`, or failed-but-retryable. |

There is no percentage, deliberately: a node's children are only created when the node is processed, so the denominator is unknown while the run happens and any estimate of it moves backward as work is discovered.

`tasks_unfinished` at zero while `nodes_in_flight` is above zero is the one reading with a definite meaning — the frontier is waiting on something that is not in the queue, and nothing is coming to finish those nodes. A non-zero value says work is queued and nothing about whether a worker is claiming it: tasks stalled `pending` behind an unanswered badge are counted identically to tasks being drained. Two readings over time separate them; one reading cannot.

## Ingest options

Three layers, merged by `jmfts_core.ingest_options.resolve_options`:

```
TASK_PARAM_DEFAULTS[group]        the task's parameters — valid wherever it runs
  <- INGEST_PROFILES[fmt][group]  this format deviates  (empty today)
    <- caller overrides           this request deviates
```

Options are **namespaced by group**, where a group names the parameters one kind of task takes. A parameter belongs to the task that reads it, not to the format that fed it.

| Group | Key | Default | Read by |
|---|---|---|---|
| `structure` | `chunk_strategy` | `sentence_packed` | `structure:declared`, `structure:inferred` |
| `structure` | `max_tokens` | `120` | both structure rungs |
| `structure` | `min_chunk_length` | `20` | both structure rungs |
| `rollup` | `max_children` | `16` | the rollup planner — over this, segment instead of summarize |
| `rollup` | `penalty` | `1.0` | PELT changepoint penalty |
| `rollup` | `min_segment` | `3` | minimum children per segment |
| `rollup` | `llm_model` | `""` | `summarize:llm` — **per-request model selection**, empty falls back to `JMFTS_LLM_MODEL` |

Every group resolves for every format, so no document can reach a task whose parameters nobody set.

!!! warning "An unknown option is a 400, not a shrug"
    Writing `max_token` instead of `max_tokens` fails the request naming the key. It is not ignored. A run that does something other than what was asked and reports success is the swallowed failure the project's Fail Early rule exists to prevent — and it is what `/ingest/explain` rests on, since a plan that reports options the run would reject is a wrong answer rather than a partial one.

## Workers and routing

The same `IngestWorker` runs three ways: as a thread inside the API process, as `jmfts-worker` (its own process, possibly on another host), and as a k3s Deployment.

| Setting | Default | Notes |
|---|---|---|
| `JMFTS_INGEST_WORKER_ENABLED` | `true` | Whether the API process runs a worker thread. An appliance that accepts uploads and never processes them is not a useful default. |
| `JMFTS_INGEST_WORKER_POLL_SECONDS` | `1.0` | How long to wait after finding the queue empty. |
| `JMFTS_WORKER_HEARTBEAT_SECONDS` | `10.0` | How often a worker reports liveness while holding a task. |
| `JMFTS_WORKER_LEASE_SECONDS` | `90.0` | How long a worker may go **without beating** before another requeues its task. Must be at least 3× the heartbeat; below that a single missed beat costs a running task, and the constructor refuses. |
| `JMFTS_WORKER_REAP_SECONDS` | `30.0` | How often to try the fleet-wide expired-claim sweep. |
| `JMFTS_TASK_BADGES` | `{}` | JSON object mapping `task_type` → badge. **Empty by default, deliberately** — see the warning below. |
| `JMFTS_WORKER_BADGE` | unset | Comma-separated badges for `jmfts-worker`. Equivalent to repeating `--badge`. |
| `JMFTS_WORKER_ID` | host-pid | Written to `task_queue.claimed_by`. |
| `JMFTS_LLM_API_KEY` | `""` | Bearer token for the LLM endpoint. Sent **only** when set, so one worker image serves both a LAN llama-server and a metered API. |

### The lease is not a task timeout

It bounds how long a live worker may go without reporting in — a property of the loop. It does not bound how long a task may run. Task durations here vary by orders of magnitude with input, so a lease keyed on elapsed runtime would reap work that is still running and then run it a second time, concurrently, on another host.

### Badges filter, they do not order

`claim_next` orders by `priority DESC, created_at ASC`. Badges only decide what is in the candidate set. A worker listing `[urgent, bulk]` takes whatever is oldest and highest priority among **both** — so an idle expensive worker will start a bulk task a second before an urgent one arrives. `priority` on the row is the lever for that.

An un-badged worker claims **everything**, and an un-badged task is claimable by **anyone**.

!!! warning "A badge with no worker stalls silently and permanently"
    `JMFTS_TASK_BADGES` is empty by default and that is deliberate. Tasks carrying a badge no running worker answers to sit `pending` forever, and nothing reports it. The [DevOps Manual](devops.md#badges-route-work-to-pools) covers the failure shape and what to monitor.

`jmfts-worker` flags: `--badge` (repeatable), `--worker-id`, `--poll-seconds`, `--heartbeat-seconds`, `--lease-seconds`, `--reap-seconds`, `--drain`, `--max-tasks`, `--log-level`.

## Batch processing

`batch_worker/` is a **reference implementation**, shipped beside the appliance rather than inside it. It consumes `summarize:llm` through an external batch provider at roughly half the synchronous price. Nothing in `jmfts_core` imports it.

| Provider | Submit | Status field | Batch-level failure | Cap |
|---|---|---|---|---|
| `mock` | 1 call, directory-backed | — | cancel only | configurable |
| `openai` | 2 calls (upload file, create batch) | `status` | `failed` / `expired` / `cancelled` | 50,000 / 200 MB |
| `anthropic` | 1 call, requests inline | `processing_status` | none — always `ended` | 100,000 / 256 MB |

`custom_id` is the only mapping and is set to `task-{id}`, which satisfies Anthropic's `^[a-zA-Z0-9_-]{1,64}$`. A result whose `custom_id` this appliance did not write is skipped, never applied.

`jmfts-batch-worker` subcommands: `run`, `status`, `stalled`, `finalize` (mock only), `cancel`. `stalled` exits non-zero so a cron or probe can act on it.

!!! warning "A `batched` row is invisible to every other recovery mechanism"
    The claim query will not take it, the lease will not reap it — nothing beats for a parked row, because the work is at the provider — and the conflict predicate counts it as a live reservation, so nothing else can work that node either. `batched_at` and `jmfts-batch-worker stalled` are the only stall signal there is. Both providers expire a batch at 24 hours; the default stall threshold is 26.

## Vector indexes

| Column | Index | Notes |
|---|---|---|
| `documents.embed` (768-dim `vector`) | HNSW, `m=16, ef_construction=64`, cosine | Document-level similarity. |
| `token_embeddings.embed_256` (`halfvec`) | IVFFlat, `lists=1024`, cosine | The active late-interaction column in a default deployment. |
| `token_embeddings.embed_384` / `embed_512` (`halfvec`) | HNSW, `m=16, ef_construction=64`, cosine | Present in schema, unpopulated unless a deployment opts into a higher retention tier. |

`pg_trgm` is also enabled, for fuzzy/trigram fallback in full-text search.
