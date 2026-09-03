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

!!! note "This page describes 0.2.0. The current release is 0.3.0."
    Two releases have landed since this page was written, and it has not moved to either: 0.2.1 added the spreadsheet task types, the Turtle surface and two extras, and 0.3.0 replaced the ingest planner. The [Changelog](changelog.md) says what each one changed, and [0.3.0 — the job system](release-0-3-0.md) runs the changes rather than describing them.

    Two sections here have been corrected in place because they described designs that no longer exist: [One ingest path](#one-ingest-path) and the `.xlsx` row under [Office formats](#office-formats). Everything else is 0.2.0's surface, which 0.3.0 is a superset of except for the two breaks the changelog names.

!!! note "Defaults come from the code, not from `.env.example`"
    Settings tables quote the built-in default in `jmfts_core/config.py`. `.env.example` ships a *filled-in* sample for the LLM block (an Ollama URL and a model name) rather than the blank built-in — copy it and you have configured an endpoint, not accepted a default.

## Data model

| Table | Holds |
|---|---|
| `documents` | The tree. `parent_id` + a `path` JSONB array of ancestor ids for subtree queries; `content`; a 768-dim `embed` vector; `usetype` for classification; a nullable explicit sibling `position`; `created_at`/`updated_at` (system time) and a separate nullable `event_time` (domain time, for imported content whose ingest time means nothing — transcripts, backfills). 0.1.1 added `settled` (`in_flight`, `settled` or `failed`), the ingestion lifecycle flag the retrieval indexes are partial on — an `in_flight` node is invisible to search until its subtree finishes. |
| `token_embeddings` | Per-token late-interaction vectors — `embed_256`/`384`/`512` as `halfvec`, one row per selected token, `tier` marking which top-N% importance band it fell in. Only 256-dim is populated in a default deployment; 384/512 exist for benchmarking retention levels. |
| `document_blobs` | Uploaded bytes for `POST /ingest/file`. One row per document (`UNIQUE`), holding the `lob_oid` of a Postgres **large object** plus `mime_type`, `byte_size`, `content_hash`. The bytes are not in the table: `ON DELETE CASCADE` removes the row and orphans the object, so deletion goes through `BlobRepository` (`lo_unlink` first), and `pg_dump` in plain format needs `-b` or the restore points at bytes that no longer exist. |
| `task_queue` | The ingest scheduler's rows — see [Ingest task queue](#ingest-task-queue) for the column set and the lifecycle. `scope_document_id` + `write_mode` (`self`, `children` or `subtree`) declare what region of the tree a task **reserves** while it runs, and the claim query refuses a task whose region overlaps one already `claimed`, `running` or `batched`. Retry policy lives in `TaskQueueRepository.fail()`, not in SQL. |
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

All routes are generated from a service-layer `@expose` registry (`jmfts_core/services/`), not hand-written per-route: one decorated service method is both the in-process Python call and the REST route, and `tests/test_api_parity.py` asserts the registry and the mounted routes stay in bijection. `docs/API_UNIFICATION_CONTRACT_NOTES.md`, which carries the conversion history and the per-endpoint divergence notes, is one of the design documents held back from the public tree (see [Documents not in this release](devops.md#documents-not-in-this-release)).

| Family | Prefix | Covers |
|---|---|---|
| Documents | `/documents` | CRUD, tree navigation (`roots`/`children`/`ancestors`/`siblings`/`subtree`), `embed`, `tokens`, `split`, `chunk`, `segment`, `raptor` (+ `raptor/portfolio`), `extract-facts`, `links`. |
| Ingest | `/ingest` | One path, two doors onto it — see [One ingest path](#one-ingest-path). `POST /ingest/file` is a multipart upload that stores bytes, enqueues `probe` and **returns before the work is done**; `POST /ingest` takes content plus a named entry point and drains that document's tasks before returning. `GET /ingest/pipelines` lists the entry points, `file/{id}/frontier` reports what is still queued, and `explain` / `analyze` answer what a document will run before it runs. |
| Runner | `/runner` | Vectors for text, behind `JMFTS_RUNNER_KEY` rather than the API token. Owns no documents. This is what a worker set to `JMFTS_RUNNER_URL` calls instead of loading the model. |
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

### Calling them from Python

Do not write a client against `/openapi.json`. One already exists, and it is generated from the same route table.

```bash
pip install jmfts-client
```

```python
from jmfts_client import RemoteJmftsClient
from jmfts_client.contracts import DocumentCreate, HybridSearchRequest

with RemoteJmftsClient("http://localhost:8100", token="...") as jmfts:
    jmfts.create_document(DocumentCreate(title="Ada", content="Ada Lovelace"))
    hits = jmfts.hybrid_search(HybridSearchRequest(query="Ada", limit=10))
```

`jmfts-client` is a **second distribution** shipped from the same repository. It carries `httpx` and `pydantic` and nothing else — no SQLAlchemy, no numpy, no torch — so calling an appliance does not mean installing one.

| | `jmfts` | `jmfts-client` |
|---|---|---|
| Holds | the appliance | the wire contracts plus `RemoteJmftsClient` |
| Dependencies | the full stack | `httpx`, `pydantic` |
| Depends on | `jmfts-client==<same version>` | nothing in this repository |

**The two release in lockstep: one number, two wheels, one tag.** `_verbs.py` is generated from the server's resolved route table, so a client built from a different release was generated from a different surface — and that mismatch does not fail at install time. It fails at call time, as a verb that is missing or whose parameters moved. The `==` pin is what makes the pair one product.

The contracts are the single definition of every request and response shape. Both the in-process `LocalJmftsClient` and `RemoteJmftsClient` validate against the same classes, which matters when one process holds both — the `JMFTS_RUNNER_URL` case, where two copies equal by value and unequal by `isinstance` would bite.

So one `@expose`-decorated service method becomes four things: a REST route, an entry in the OpenAPI document, a `LocalJmftsClient` method, and a `RemoteJmftsClient` method. Nobody hand-writes the last three.

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

## One ingest path

!!! note "Corrected for 0.3.0"
    Through 0.2.1 this section described two unrelated designs under one prefix, and said `POST /ingest` was being retired. It was not retired — it was moved onto the queue, and the design it belonged to was deleted. `execute_pipeline` and the `PipelineDefinition` registry are gone.

`/ingest` has one implementation and two doors onto it. Both create a file node with stored bytes and run queue tasks against it; they differ in who waits and in whether the format is named or measured.

| | `POST /ingest` | `POST /ingest/file` |
|---|---|---|
| Takes | content plus a named **entry point** | bytes; the format is **detected** |
| Names | `markdown`, `raw`, `conversation`, `transcript`, `wiki:url`, `wiki:arxiv`, `wiki:pdf` | `text`, `pdf`, `docx`, `pptx`, `xlsx`, `zip`, … from `detect_format` |
| Returns | a finished tree, in the request | an `in_flight` node and a queued `probe` |
| Who drains the queue | the request, for that document only | a `jmfts-worker` process |
| Since | 0.1.0, on the queue since 0.3.0 | 0.1.1 |

Same tasks, same handlers, same settling walk. **An entry point is not a stage list.** `GET /ingest/pipelines` names the seven and reports, for each, where its content comes from and which options it resolves to — two facts `probe` cannot supply. Which tasks a document actually runs is `POST /ingest/explain`'s answer, decided from what was measured.

`pipeline_config` was the deleted design's stage vocabulary and is now **refused** with a 400 naming `options` instead. There is no translation between the two: that design's `summarize` stage was RAPTOR clustering, and the queue's is what gives a container node its vectors.

The two name sets overlap in exactly the way that causes trouble: **`markdown` is an entry point and is not a format.** Nothing in the bytes distinguishes authored markdown from a `.txt` file starting with `#`, so `detect_format` reports both as `text` and one Part 4 entry covers them. `POST /ingest/explain` accepts `{"format": "markdown"}` — an unknown format is a legal question — and answers with every row `impossible` or `not_applicable`, which reads like a verdict on markdown and is a verdict on the name.

## Office formats

`.docx` and `.pptx` are read as text. `.xlsx` is read as records, by a different route.

That difference is not a gap in the documentation — it is the state of the appliance, and `POST /ingest/explain` reports it per format. Ask before you load a corpus.

!!! note "Corrected for 0.2.1: `.xlsx` is read"
    The table below is 0.2.0's, where a workbook was detected and probed and nothing more. 0.2.1 added three task types that read one — `structure:sheets` makes a child node per worksheet, `profile:sheet` measures a worksheet, and `extract:sheet` turns each row into a record node. None of them is `extract:text`, and `TEXT_EXTRACTORS` is still `("pdf", "text", "docx", "pptx")`: a spreadsheet is not prose, and rendering one as a wall of markdown would index something nobody wrote. So the `xlsx` rows below stay correct about **text** and understate what the format does. See the [Changelog](changelog.md#spreadsheets-are-read).

### What is read, and what only measured

| Format | Detected | Probed | Text extracted |
|---|---|---|---|
| `docx` | yes | yes | **yes**, with `jmfts[office]` |
| `pptx` | yes | yes | **yes**, with `jmfts[office]` |
| `xlsx` | yes | yes — `has_sheets`, `sheet_count`, `has_comments` | no |
| `ole2` | yes | yes — separates an encrypted package from a legacy binary | no |

`detect_format` identifies `docx`, `pptx` and `xlsx` from the ZIP member list — `word/document.xml`, `ppt/presentation.xml`, `xl/workbook.xml` — and reports `detected_by: "zip_manifest"`, so the evidence is in the record rather than inferred from the filename. That needs `zipfile` and nothing else, which is why it is in every install.

`PROBERS_AVAILABLE` is `("pdf", "text", "docx", "pptx", "xlsx", "ole2")`, and `TEXT_EXTRACTORS` is `("pdf", "text", "docx", "pptx")`. The two lists are not the same list, and the second is the one that decides whether an upload produces anything to search.

### How the scheduler decides, per format

Nothing in the Part 4 table was changed to turn office ingestion on. `extract:text` is gated on `has_text_layer`, and the work was to **measure** that pattern rather than to add a row:

| Format | `has_text_layer` | `structure:declared` gated on |
|---|---|---|
| `docx` | measured by the docx prober | `has_heading_styles` |
| `pptx` | measured by the pptx prober | `has_slides` |
| `xlsx` | **not measured** | `has_sheets` |

For `docx` and `pptx` that makes every downstream row `conditional` when you ask without bytes, and decided once probe has run — the same shape `pdf` has always had. For `xlsx` the pattern is never reported, so `extract:text` comes back `not_applicable` with the reason `patterns.has_text_layer was not measured`, and every row that depends on it follows.

`DECLARED_STRUCTURE_PATTERN` already mapped all three. In 0.2.0 the `xlsx` entry was a decision waiting on a reader; 0.2.1 supplied one, and `has_sheets` now gates `structure:sheets` as well as `structure:declared`.

### What the markdown looks like

Both readers convert to markdown, because markdown is the intermediate format every text-bearing input converges on. Nothing downstream needed to learn what a `.docx` is.

**`.docx`** — a paragraph whose style resolves to `Heading 1`–`Heading 9` becomes the matching ATX heading, and `Title` becomes `#`. Body order is preserved by walking the body element rather than `Document.paragraphs`, which skips tables entirely. Lists become `-`. Tables become GFM.

The heading styles the reader writes from are the same ones the prober counted for `has_heading_styles`, so the pattern that lets `structure:declared` run and the structure it splits on are two readings of one fact.

**`.pptx`** — one `#` section per slide, body text frames, tables, and speaker notes under a `## Notes` subheading. A chunk is a slide.

**Slide titles are promoted when there is no title placeholder.** Across 22 real decks (220 slides), 80 had no title placeholder because the deck was built from a blank layout with the title typed into an ordinary text box. Falling through to `# Slide N` discarded the heading that becomes a search result's section title. The reader now promotes the slide's first line of text instead, and the attempt log carries `promoted_title_count` so you can see how many headings the reader chose rather than read.

The promoted line is **moved, not copied** — the rest of that shape stays in the body.

### Deliberately not covered

A wrong rendering is worse than a missing one, so these are named rather than attempted:

- **Ordered vs unordered lists.** A numbered list becomes `-` like any other. Telling them apart means resolving `w:numId` through `word/numbering.xml`, and a guess would renumber the author's list.
- **Images, charts, SmartArt.** `probe` reports `has_images` and `has_smartart`; reading them is `extract:images`, a different task.
- **Comments, footnotes, tracked changes.** `probe` reports each. Merging an unaccepted insertion into the prose would put text into the index that the document does not say. `w:delText` and `w:instrText` are excluded from `has_text_layer` for the same reason.
- **Legacy `.doc` / `.ppt` / `.xls`.** Not a ZIP at all. Tier 3.

### A corrupt package fails once, not three times

`_open_package` guards the *open* of a ZIP, but a member can still fail to inflate after the archive opens. The raw `zipfile.BadZipFile` derives straight from `Exception`, so `classify_exception` graded it RETRYABLE and probe attempted the same bytes three times. A local header does not repair itself between attempts.

`probe_patterns` now converts it to a `ValueError` naming the format and the member failure, which grades **PERMANENT**.

### The three dependency tiers

Office support splits by what the dependency actually is. The split is the operator's concern as much as the developer's, so it is described in full in the [DevOps Manual](devops.md#office-files-three-tiers-two-extras).

| Tier | What | Where it lives | Status |
|---|---|---|---|
| 1 | `zipfile`, `xml.etree`, `olefile` | base install | detection and all four probers ship |
| 2 | `python-docx`, `python-pptx`, `openpyxl` | `jmfts[office]` extra | the `docx` and `pptx` readers call it; `openpyxl` has no caller yet |
| 3 | LibreOffice, driven by `unoserver` | a badged worker image; `jmfts[convert]` is the client only | nothing yet |

`jmfts_core.office` is the only module permitted to import a tier-2 library, and only through its `require_docx()` / `require_pptx()` / `require_openpyxl()` guards, at the point of use and never at module scope. `tests/test_office_packaging.py` fails if one reaches the application's import path, and `scripts/check_base_install.sh` asserts the same thing against a real base virtualenv.

A base install asked to read a `.docx` raises `OfficeStackNotInstalled`, which subclasses `ImportError` and therefore classifies PERMANENT.

### `is_encrypted` is why `olefile` is in the base install

An encrypted OOXML package is not a ZIP. It is an OLE2 compound file, so it carries the same eight magic bytes as a legacy `.doc`, and `detect_format` reports both as `ole2` with nothing to separate them. The two go opposite ways — a legacy binary gets converted, an encrypted package must fail with a named reason — so probe has to tell them apart, and one directory listing does it.

`msoffcrypto-tool` is deliberately not carried. It decrypts a password-protected package, and there is no path by which a caller could supply a password. Detecting encryption is the requirement; decrypting is not.

### What is planned, and in what order

`docs/OFFICE_SPEC.md` in the repository is the plan, and it covers more than ingestion — rendering a page, addressing a region, editing a document in the tree, and generating one from a template.

| Step | What | Tier | Status |
|---|---|---|---|
| 0 | the extras, the `office` seam, the import guards | — | shipped |
| 1–3 | advisory task types and the PDF citation path | — | shipped |
| 4 | office probers; `is_encrypted` fails, `is_legacy_binary` schedules `convert:ooxml` | 1 | probers shipped |
| 5 | `extract:text` for `docx` and `pptx` | 2 | **shipped** |
| 6 | `profile:sheet`, `extract:sheet`, `GET /documents/{id}/cells` | 2 | open |
| 7 | `render:pdf` and `convert:ooxml`; the LibreOffice worker | 3 | open |

Step 6 is what makes `.xlsx` readable, and it is a different job from steps 5: a spreadsheet is not prose, so extracting it as a wall of markdown would index something nobody wrote. `convert:ooxml` in step 7 is also what makes legacy `.doc` / `.ppt` / `.xls` reachable, by converting them to OOXML for the tier-2 readers.

## Ingest task queue

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
