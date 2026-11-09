---
title: "Changelog"
---

# JMFTS — Changelog

What each release changed, newest first.

This page is the release record, current through **0.8.0** plus the unreleased work on `master` after it. The full per-commit record is [`CHANGELOG.md`](https://github.com/jmccardle/jmfts/blob/master/CHANGELOG.md) in the repository; this page keeps what an operator or client author needs. The [Reference](reference.md), the [Cookbook](cookbook.md) and the [DevOps Manual](devops.md) were written against **0.2.0** and have been corrected in place since; where a later release moved something one of them describes, the entry below says what moved. The three pages the appliance generates from its own registries are always current by construction, and are the better answer where they overlap — see [The three pages that cannot go stale](reference.md#the-three-pages-that-cannot-go-stale).

!!! warning "Two numbers are missing from PyPI, for two different reasons"
    Every release is tagged on GitHub. `pip install jmfts` resolves **0.8.0** (checked against PyPI, which lists 0.2.0, 0.3.0, 0.5.0 through 0.5.2, 0.6.0 through 0.6.2, 0.7.0, 0.7.1 and 0.8.0).

    **0.2.1 was never uploaded.** Its tag push ran the publish workflow and the upload step failed on a leftover configuration from the hand-built 0.2.0 bootstrap. `pip install jmfts==0.2.1` finds nothing. The gap is recorded rather than repaired — republishing a superseded version under a new number would make the release record lie about what 0.2.1 was.

    **There is no 0.4.0 at all.** Most of what its sprint planned shipped inside 0.5.0 instead, because the two sprints ran together. Cutting a 0.4.0 tag after the fact would name a tree that never existed.

## Unreleased (on `master` after 0.8.0)

Not tagged and not on PyPI. Issue #59: a BM25-only install.

### One break: `pip install jmfts` no longer ingests PDFs

`pymupdf`, `ruptures` and `transformers` (about 480 MB with their dependencies) left the base install. Three new extras carry them: `pdf`, `segment` and `tokenizer`, and **`ingest` is all three, which is the old base**. `embed` implies `tokenizer`; `dev` implies `ingest`. Each is imported at the point of use, and without its extra the operation raises `PdfStackNotInstalled`, `SegmentStackNotInstalled` or `TokenizerStackNotInstalled` (PERMANENT in the queue, 501 over REST), naming `pip install "jmfts[<extra>]"`. A PDF probed without `pdf` fails by name instead of reporting an empty pattern set.

Affected: any install, image or worker that relied on base for PDF probing and extraction, `rollup` segmentation, `check_fit` or the chunker, a thin worker included. Fix: `pip install 'jmfts[ingest]'`. `Dockerfile.worker` now defaults to `EXTRAS=[embed,ingest]`, and whether it bakes the model is decided by `EXTRAS` containing `embed`, so the thin build is `--build-arg EXTRAS='[ingest]'` (an empty value no longer means a working thin worker). `Dockerfile` installs `ingest` too.

### Added

- **`JMFTS_AUTO_EMBED_DEFAULT`** (default `true`, so existing deployments behave as before). `DocumentCreate.auto_embed` and `embed_tokens` are now optional and resolve from it; so do `StructuralSplitRequest.auto_embed` and `ChunkRequest.auto_embed`. An explicit `auto_embed=true` with no model still fails. `GET /capabilities` reports `embedding.auto_embed_default`.
- **`Containerfile.bm25`**, a base-install-only image on `python:3.13-slim`: no torch, ingest worker off, `JMFTS_AUTO_EMBED_DEFAULT=false`, non-root, and a start command that runs `jmfts-init-db` first. See [A BM25-only appliance](devops.md#a-bm25-only-appliance-no-torch-no-model).

## 0.8.0

Released 2026-10-24 as tag [`v0.8.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.8.0). Three wheels.

**A request the server would have ignored is refused, and a conflict names the row it hit.**

### Breaking

1. **An empty `JMFTS_API_TOKEN` makes the API server refuse to start (#51).** Before, it generated a token and printed it, and a client sharing the environment sent an empty bearer and got 401 on every call. `docker-compose.yml` no longer defaults it to `jmfts-dev-local`. Fix: `export JMFTS_API_TOKEN="$(openssl rand -base64 32)"`. See [Auth](devops.md#auth).
2. **A request field the contract does not declare is a 422 (#47).** Every JSON request contract forbids extras, nested ones included, and the `/runner` bodies too. The `X-JMFTS-Ignored-Fields` header is removed. Unknown query parameters and extra multipart form fields are still dropped. Fix: stop sending the field (tectum's `max_context_tokens`, removed in 0.6.0, is the known one). See [Wire behaviour since 0.7](reference.md#wire-behaviour-since-07).

### Added

- `GET /documents/{id}/subtree` takes `usetype` (#49).
- `JMFTS_SEARCH_EXCLUDE_USETYPES` and `JMFTS_BM25_EXCLUDE_USETYPES` accept `*` and `?` globs (#52), and a request's `exclude_types` does too: `exclude_types: ["*"]` now drops every non-NULL usetype. BM25 applies usetype filters inside the scored SQL, so a filtered page is no longer short (#57).
- A triple's object can be a literal: `object_literal` and `object_datatype` on `POST`/`PUT /triples` and `supersede` (#48).
- `jmfts-eval beir`, the BEIR harness, restored under `jmfts_core/eval/`. It has no default data directory or database, and refuses over-window documents unless told to skip them.

### Changed and fixed

- A duplicate triple or predicate is a 409 with `detail: {"message", "existing_id"}`; the predicate 409 used to carry a bare string (#54, #55). `GET /triples/predicates` lists predicates with no triples by default.
- An LLM-backed verb with no `JMFTS_LLM_*` endpoint answers 501, not 500 (#56).
- `jmfts-init-db` on an initialised database loads nothing: `already initialised, 0 pending` (exit 0) or the pending deltas named (exit 1) (#50).
- `POST /documents` with `auto_index_bm25` indexes into the named index that covers the document, not always `default` (#53).
- PDF tables on PyMuPDF 2.0: floor is now `pymupdf>=1.27.1`; `ffwf-tau-llm` floor is `>=0.14.1` (typed errors; JMFTS owns the retry).

No migration.

## 0.7.1

Released 2026-10-18. Three wheels.

**Office previews work end to end.** Compose now runs a `libreoffice` service and installs the `office` and `convert` extras; `Dockerfile.libreoffice` gains Carlito, Caladea and Noto CJK fonts (626 MB to 723 MB). Rendition matching was measured against real LibreOffice output and every test case now locates all of its blocks. PDF tables on rotated pages read in order; tables on a page both rotated and cropped are no longer detected. A PDF table node can be previewed.

**One break:** a `render_anchor` now carries the `rendition_hash` it was measured on, and `/region` and `/image` refuse (409) a rectangle whose hash does not match the stored rendition. Every office preview made before 0.7.1 has no hash and is refused until `anchor:render` runs again on its file node. No endpoint re-runs one task yet, so delete and re-upload the document (a re-upload of the same bytes is deduplicated). PDF anchors are unaffected. No migration.

## 0.7.0

Released 2026-10-17. Three wheels.

**Chunks are measured in words, and a summary stops outliving its source.**

### Breaking

- **`structure.max_tokens` is now `structure.max_words` (#1).** The option always counted words. The old name is refused with a hint to rename it, and `/chunk` answers 422 to unknown fields. A queued structure task still carrying `max_tokens` fails PERMANENT: re-ingest the document.
- **A queued `structure:conversation` row from before this release fails PERMANENT (#4)**; re-ingest.
- `EmbeddingService.chunk_to_fit` is removed; call `chunk_text(text, fits=service.fits_token_window)`.

### Added

- `jmfts-ui`, a standalone Vue console (unpackaged; `jmfts-web` at `/app` is unchanged), and a page preview of a node's anchor.
- PDF tables become `table` nodes (`extract:tables`); spreadsheet nodes carry `cells` source anchors.
- `JMFTS_EMBEDDING_REVISION` pins the default embedding model to a Hub commit.
- The `sentence_window` chunk strategy.

### Changed and fixed

- A `summarize:tree` node carries no vector, and deleting a document deletes the summary nodes that stood for it (ROADMAP gap 11).
- Ten operations that ignored subtree access now respect it (#30).
- An LLM failure inside a queued task is retried by the endpoint's HTTP status: a 4xx other than 408 and 429 is PERMANENT (#8).
- PDF rectangles on rotated pages are stored in the displayed page's space (#38). Anchors written before this are not migrated; re-run `citation`, or `extract:text` then `extract:tables`.
- Security floors: `python-multipart>=0.0.31`, `starlette>=1.3.1`, `transformers>=5.10`.

### Upgrading

Two migrations, `024_max_words.sql` and `025_summary_tree_no_vector.sql`. **Read them first:** `024` refuses to run while a structure task that could still run is queued, and `025` rebuilds `idx_documents_embed` under a write lock on `documents`. See [the migration list](devops.md#what-the-compose-stack-actually-runs).

## 0.6.2

Released 2026-10-12.

- **`JMFTS_EMBEDDING_BATCH_SIZE` is gone** because nothing read it. A `.env` *file* that still sets it stops startup; delete the line.
- Synthesis catches only LLM failures, so an unexpected error is a 500 rather than `llm_available: false` (#32). `llm_error` is added to the synthesize response, and a 502/503/504 from the LLM is retried within `JMFTS_SYNTHESIS_RETRY_BUDGET` (default 4 s).
- Dependency floors rose to the versions the suite runs against, `ffwf-tau-llm` 0.12.0 among them. There are no upper bounds.
- An uncached tokenizer on an offline host raises `TokenizerNotCached` and answers 501.
- 0.6.2 added an `X-JMFTS-Ignored-Fields` header; 0.8.0 removed it when unknown fields became a 422.

## 0.6.1

Released 2026-10-12.

- **`JMFTS_LLM_BASE_URL` is used as given; JMFTS no longer appends `/v1`.** Set it to the URL the server advertises, version segment included. A config that gives a server root now 404s; `GET /health/llm` names the URL it tried. `GET /health/llm` now makes one outbound call, not two.

## 0.6.0

Released 2026-10-12 as tag [`v0.6.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.6.0). **Three** wheels — `jmfts-web` is new.

A web front end, and the things a web front end found. It has its own page — see **[0.6.0 — eyes and hands](release-0-6-0.md)**, which runs the changes rather than describing them.

### Two breaks a client can see

Both are access control, and both are why this is a minor version.

1. **An edge takes write on its source and read on its target.** `create_link` flushed a `DocumentLink` with no principal check at all, and five `TripleService` write verbs gated neither endpoint. A principal with read-only access to a document could attach edges to it. A call that used to succeed now returns 403.
2. **The four graph-analytics verbs compute over the caller's graph.** `/graph/centrality`, `/graph/subtree-authority`, `/graph/spines` and `/graph/communities` took no principal at all, and returned ids and titles of documents that are 404 for that caller everywhere else. The filter went into the vertex and title queries rather than onto the result, so **scores change** for a principal without full grants — a centrality number computed over rows you cannot see is a number about somebody else's corpus.

A standing audit test now holds every `@expose`'d verb to being principal-scoped or explicitly listed. It found eleven more gaps on its first run.

### A third wheel

`jmfts-web` carries built static files and one module that says where they are. It has no dependencies of its own; everything the front end does it does in the browser, over the same REST API any other client calls.

```bash
pip install 'jmfts[web]'      # then open http://localhost:8100/app/
```

`jmfts`, `jmfts-client` and `jmfts-web` release in lockstep: one number, three wheels, one tag. A UI one release behind its server renders controls for operations that have moved.

### Three routes that answer with bytes

`ExposeSpec` grew a response media type, so an exposed operation can answer with something that is not JSON. `GET /documents/{id}/blob` serves the original upload as an attachment, `/image` serves one page as a PNG, and `/region` serves a rectangle of a page — from the node's own anchor, or from explicit bounds in PDF points. Naming both is a 400 rather than a precedence rule.

### `.docx` and `.pptx` get rectangles

LibreOffice paginates an office document into a stored PDF and a citation's rectangle is recovered off that, so a node can carry two anchors: `source_anchor` for its exact `ooxml` address, `render_anchor` for the approximate rectangle. `PdfAnchor.of` says which — `"source"` or `"rendition"` — and defaults to `"source"`, so every anchor written before this release still parses as what it is.

Two new task types (`render:pdf`, `convert:ooxml`), a third dependency tier (`jmfts[convert]` is the client; `Dockerfile.libreoffice` builds the server), and `JMFTS_CONVERT_URL` to connect them. `render:pdf` is **advisory**: an appliance with no LibreOffice ingests office documents normally and gets no rectangles, rather than stalling them short of settling.

### A workbook's rows reach BM25

`index:bm25` named three prose rungs and did not name `structure:sheets`. On the reference corpus that read as zero `index:bm25` tasks anywhere in a 21-workbook subtree, while 4,601 `record` nodes under it carried text averaging 457 characters — so every spreadsheet was absent from its own index and from `universal`. It is now planned at the settling boundary.

### `EXPLAIN` says how many

The ingest plan folds a cost: tasks, child nodes, embeddings, LLM calls. Every accumulator returns an interval, because a fan-out atom declares a bound rather than a number, and the top is allowed to be open. `PlanCost.unmeasured` names what could not be counted — an unmeasurable count is reported, never guessed.

### A collection configures what is ingested under it

`GET` and `PUT /documents/{id}/ingest-options` write an options row onto a node, and upload walks up the ancestors to find one. No bindings table and no migration: a collection is a subtree, the tree is already there, and access control already answers "who may configure this collection" with "who may write to this node".

### Upgrading

One migration, `023_document_renditions.sql`, and it is additive. `jmfts-init-db --pending` names what a database has not applied.

Nothing fails at deploy time. Calls that used to succeed start returning 403, which is the point of the two breaks above — read them before upgrading a multi-principal deployment.

## 0.5.1

Released 2026-09-13 as tag [`v0.5.1`](https://github.com/jmccardle/jmfts/releases/tag/v0.5.1). Both wheels.

**Development moved into the public repository.** Up to 0.5.0 the public tree was a per-release squash — one commit per version, copied out of a private tree by a publish step, with the working record left behind. From this release there is one history on two remotes, and a commit reaches both as it is made. The commits are the ones that were actually written, the branches are real, and the release history stops being a thing you are told about.

Nothing already published was rewritten; the squash chain is still there behind it.

The rest of the release is test repairs, and they are worth reading as a group because none of them was a defect in the appliance:

- **An ANN gate test was asserting a cost estimate rather than the `ORDER BY` it was written for.** It read the planner's unforced choice of plan, which on a 230-row fixture depends on whether `documents` carries statistics — and that is a property of the test database across the whole run, not of the fixture. It passed on a development machine running one file and failed on a runner running the whole suite. The test now makes its statistics rather than finding them, and forces out every route that produces distance order by *sorting*.
- **Intermittent ANN failures were the fixtures, not the appliance.** Both files stored one vector in every document and queried with that same vector; a rolled-back row leaves its node in the HNSW graph until `VACUUM` runs, so repeating the fixture piles dead nodes onto the exact point the next query enters at. Reproduced standalone in about forty lines of SQL with no application code. This is a documented pgvector behaviour — removing a node means repairing its neighbours' adjacency lists, so it is deferred — and the fixtures were walking into it.
- **A recall test could fail on a measurement that met its threshold.** It read `assert 0.8999999999999999 >= 0.9`. The measurement was exactly 0.90 and floating-point accumulation order lost it. The threshold is still 0.90; the comparison is against a floor about 13 ULP under it, which one genuinely missing neighbour clears by four hundred times the tolerance.

## 0.5.0

Released 2026-09-12 as tag [`v0.5.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.5.0). Both wheels.

The release with no 0.4.0 in front of it. Two sprints ran together and shipped as one number.

### A database can be asked what it is missing

`jmfts-init-db --pending` names the shipped deltas a database has not applied, and `schema_migrations` (migration `017`) is the row-per-delta it reads. Before this, choosing and applying deltas was entirely an operator's problem with nothing to check the answer against.

### The token index is HNSW, and it was IVFFlat

Migration `022`. The property that decided it: an HNSW graph is built by insertion, so a partial index over `settled` rows can be added to as documents settle. IVFFlat cannot do that — no `lists` value and no `probes` value makes it possible — so its lists were built once and drifted from the corpus underneath them.

MaxSim also now returns the documents it ranked, rather than a ranking over a set it had already narrowed.

### SHACL shapes run

0.2.1 stored shapes and bound them to scopes. This release runs them: `POST /ontologies/{name}/validate` enqueues `validate:shape`, and `POST /ontologies/{name}/derive` enqueues `derive:rule` for `sh:rule` derivation. `JMFTS_SHACL_MAX_SCOPE_DOCUMENTS` (default 512) bounds a validation or derivation, and refuses rather than silently truncating.

### `GET /capabilities`

What this appliance accepts, asked without sending it anything: installed extras, whether it can produce a vector at all, the formats it identifies from the bytes, the ingest entry points, the retrieval methods and their weights, and the usetypes held out of every result set. Answered from the live registries; it makes no network call. `?corpus=true` adds the counts that say whether a method will return anything *here*.

### `GET /access/audit`

What is not protected by any access-control root. A document under no ACR is readable and writable by anyone with a token, which is the default; this is how to ask which documents are in that state. Owner-only.

### `GET /health` became the cheap probe

It ran up to two outbound HTTP calls at a 5 s timeout, which is not what a liveness probe should do. `/health` is now one `SELECT 1` and needs no token; the LLM reachability probe moved to `/health/llm`, which does.

### Fixed

- **`vector_search` ordered by the similarity label, so the HNSW index was never read.**
- **A filtered vector search could return an empty page with thousands of matching readable rows.** The gate now goes inside the scored statement rather than after it: a post-filter trims the page after `LIMIT` and returns a short page instead of a wrong one.
- **BM25's leaf scan returned in-flight documents the other three methods hid.**
- **`query_triples` applied its endpoint access filter after aggregation.**
- **A RAPTOR summary took its members' parent slot**, reparenting every document it summarized.
- **A relative date in fact extraction resolved against the clock of the run** rather than of the document.
- **A NUL byte in a PDF text layer cost a 900-page book every vector, three times over.**
- **Three office defects in released code**, each with a deterministic corpus fixture.
- **A summary gets a node in its own tree.** `summarize:tree` — the RAPTOR roll-up stops being a column on something else.
- **A container's text reaches the wire**, and BM25 scores a container on the text it stands for without indexing that text twice.
- **A spreadsheet row too long to embed is a container, not a dead node.**

### Upgrading

Migrations `017` through `022`. `022` rebuilds the token index, which costs time proportional to the number of token rows.

## 0.3.0

Released 2026-09-03 as tag [`v0.3.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.3.0). Both wheels, and the first release the publish workflow uploaded by itself.

The job system: one rule table decides every task at every scope, and every node records which rule made it. It has its own page — see **[0.3.0 — the job system](release-0-3-0.md)**, which runs the changes rather than describing them.

### Two breaks a client can see

Both are why this is a minor version and not a patch.

1. **Evidence left `documents.structured_content`** for its own table. A client reading `matched.patterns` out of that column now reads nothing; `GET /documents/{id}/evidence` is where it went.
2. **`PipelineStageInfo` and `PipelineInfo.stages` are gone from the contracts,** so `GET /ingest/pipelines` no longer reports `stages`, `enabled` or `params`. There are no stages — there are tasks, and `POST /ingest/explain` answers which of them a document runs.

### There is one ingest path

The synchronous `execute_pipeline` and its `PipelineDefinition` registry are deleted. `POST /ingest` survives and is still synchronous, but it now creates a file node with stored bytes and drains **that document's** queue tasks before returning — the same tasks, handlers and settling walk the background worker runs, with the request acting as the worker. Its seven entry points survive as a table of option defaults rather than a table of stages.

`pipeline_config` is refused with a 400 naming `options` instead. There is no translation between the two vocabularies, and accepting one while doing something else is the swallowed failure this codebase does not ship.

The [Reference](reference.md#one-ingest-path) described these as two paths from two eras. That section has been rewritten.

### A missing optional stack answers 501 everywhere

`GET /documents/{id}/cells` used to be the only route that mapped an optional-stack error, so a base install answered it with a 501 naming the missing extra and answered `POST /search/hybrid` with a bare 500. Both are one deployment fact. `ModelStackNotInstalled` and the office/rdf/sketch errors now map to **501** from one default in the registry, on every operation.

501 and not 503: an install without the extra is a supported deployment, not a server having a bad afternoon, so no retry changes the answer.

### Upgrading

Two migrations, `015_evidence_rows.sql` and `016_document_produced_by.sql`, applied in order. 015 moves data a running 0.2.1 process reads — deploy the code with the migration, not around it. 016 is additive and backfills nothing: nodes that predate it read as asserted.

## 0.2.1

Tagged `v0.2.1` on GitHub and **not on PyPI** — see the note at the top of this page. Upgrading from 0.2.0 by way of PyPI means going to 0.3.0, which contains everything below.

!!! warning "Upgrade if you extract facts across documents with different grants"
    In 0.2.0 and earlier, `fact_extraction.resolve_entity` matched a name against every entity node in the store with no access filter. Two entities named in a restricted document resolved onto existing public nodes, and the triple written between them was readable by everyone — because `query_triples` scopes a fact by the readability of its endpoints, and both endpoints were public.

    The placement rule that was supposed to be the protection — a **new** entity goes under its source document — never ran, because nothing was created.

    A single-user appliance with no `access_grants` rows was never exposed by this. The rest of this page is features; this one is the reason to upgrade.

### Spreadsheets are read

`.xlsx` moves from *detected and probed* to *read*. Three new task types do it:

| Task | Scope | What it does |
|---|---|---|
| `structure:sheets` | the workbook | The sheet list becomes child nodes, one per worksheet. |
| `profile:sheet` | one sheet | Measures the worksheet — used range, per-column type and fill, header evidence — and writes a profile node. |
| `extract:sheet` | one sheet | Turns each row into a record node: labelled prose in `content`, typed values in `structured_content.record`. |

This does **not** go through `extract:text`. `TEXT_EXTRACTORS` is still `("pdf", "text", "docx", "pptx")`, and a spreadsheet is not prose — rendering one as a wall of markdown would index something nobody wrote. `structure:sheets` is gated on probe's existing `has_sheets` pattern, so nothing in the format table had to change to turn it on.

**One of four shapes is built.** A sheet whose first row holds a distinct text value in every column has record keys, and gets records. A sheet that does not gets none, and the reason is written on the node rather than guessed around. The `matrix`, `small_table` and `unstructured` shapes are still unbuilt: they are chosen by numbers that have not been calibrated against real workbooks, and inventing the numbers is worse than waiting.

Tier 2's `openpyxl` now has a caller. A worker draining these tasks needs `jmfts[office]`.

### `GET /documents/{id}/cells`

Serves a rectangle of a stored workbook, read from the source bytes.

```bash
curl -H "Authorization: Bearer $JMFTS_API_TOKEN" \
  "http://localhost:8100/documents/41/cells?ref=C3:D4"
```

Three ways to say which rectangle, and `ref_source` in the response says which one answered: the `ref` you passed, the node's own `cells` anchor, or the sheet's used range. You get values, formulas, and a rendered grid — column letters across the top, worksheet row numbers down the side, so a region starting at `C3` is not mislabelled as a table with its own header.

The read is capped at 50,000 **cells**, not rows, because `A1:XFD400` is 6.5 million cells and only 400 rows. The rectangle's area is checked before the package is opened, so an absurd `ref` costs one multiplication and comes back `413` naming the limit. It is never silently clamped to something smaller.

No page image. Rendering a spreadsheet answers a different question, and that is tier 3.

### The triple store says what it holds, in Turtle

The store was always an RDF store with integers for names. This release lets it say so out loud, and be told a vocabulary in return.

- **A triple's object can be a literal.** `object_literal` plus an `xsd:` datatype, with the lexical form kept verbatim — `1.50` and `1.5` are the same decimal and different literals. Previously every object had to be a document node, so extracting the value `128000` created a document whose title and content were both `128000`, embedded it at 768 dimensions, and put it in the retrieval index where it was a hit for anything numerically adjacent. Being RDF-shaped afterwards is a consequence; the defect is the reason.
- **`derived_by` separates an asserted fact from a materialized one.** Nothing writes it yet, and that is the point: the first inference rule to land must not be indistinguishable from something a document actually said.
- **Predicates carry an `iri`**, and `predicates.domain` is renamed `predicates.namespace`. The column has always meant "the group this predicate belongs to", which is not what `rdfs:domain` means.
- **New endpoints** — `POST /ontologies` accepts `text/turtle`, `GET /rdf/turtle` serializes the graph back out, and `/shape-bindings` binds a SHACL shape to a scope.

Turtle out exists mostly so extraction output can be reviewed. A wall of integer foreign keys is unreadable; twenty lines of Turtle is not.

The shape subset is deliberate and bounded: `sh:NodeShape`, `sh:targetClass`, `sh:property`, `sh:path`, `sh:minCount`, `sh:maxCount`, `sh:datatype`, `sh:in`, `sh:class`. **SHACL, not OWL** — SHACL is closed-world, so it can report that a record is incomplete, and an OWL reasoner never will. There is no reasoner in the query path and none in this release.

### Two new extras

Both are pure Python, unlike `office` — no C extension, no build toolchain.

| Extra | Carries | Needed by |
|---|---|---|
| `jmfts[rdf]` | `rdflib`, `pyshacl` | the Turtle and ontology endpoints |
| `jmfts[sketch]` | `datasketch` | `profile:sheet`, which sketches every column by default |

`jmfts_core.rdf` and `jmfts_core.sketch` are the only modules permitted to import them, and only through `require_*()` guards at the point of use. Getting it wrong is loud: the task fails PERMANENT with `RdfStackNotInstalled` or `SketchStackNotInstalled` naming the extra, on the first attempt.

`pyshacl` is declared although nothing calls it yet. This release stores shapes and binds them to scopes; running a shape against data is the step after. Which tier it belongs to is the packaging decision, and a validator arriving later would otherwise show up as a quiet top-level import.

Sketching can be turned off per task with the `sketch_columns` param. It is on by default because a column with no sketch is invisible to the cross-sheet containment search, whatever its cardinality.

### One new base dependency

The four LLM call sites — synthesis, RAPTOR summarization, fact extraction and span summarization — moved behind `ffwf-tau-llm`. It is a base dependency rather than an extra, because an extra whose absence breaks shipped behaviour is not an extra. The transitive cost is zero: it declares `pydantic>=2` and `httpx>=0.27`, both of which JMFTS already carried.

### Fixes

- `find_path` walked a literal into an unfiltered query. A literal is a leaf.
- A cut coreference cluster now raises instead of returning a partial walk as if it were the whole one.
- A `.docx` or `.pptx` whose ZIP opens but whose members fail to inflate now fails once as PERMANENT, rather than being retried three times. A local file header does not repair itself between attempts.

### Upgrading

Two migrations, `013_rdf_layer.sql` and `014_entity_roots.sql`, applied in order. There is no migration ledger — choosing and applying deltas is still a deliberate act by an operator who knows the target's state.

!!! warning "013 renames a column a running 0.2.0 process reads"
    `TripleRepository.list_predicates` filters on `predicates.domain`, which becomes `predicates.namespace`. Deploy the code together with the migration, not around it. Everything else in both files is additive.

    Entities that predate the migration are not backfilled.

## 0.2.0

`.docx` and `.pptx` text extraction, PDF table extraction, the citation task types, and a second distribution — `jmfts-client`, carrying the wire contracts and a generated `RemoteJmftsClient` on `httpx` and `pydantic` alone. The two release in lockstep: one number, two wheels, one tag.

## 0.1.1

The queued ingestion system: `task_queue`, `document_blobs`, `documents.settled`, the `/ingest` family, ingest options, the worker fleet, and the `/runner` surface that lets a worker ask another appliance for vectors instead of loading the model itself.
