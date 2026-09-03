---
title: "Changelog"
---

# JMFTS — Changelog

What each release changed, newest first.

This page is the release record. The [Reference](reference.md), the [Cookbook](cookbook.md) and the [DevOps Manual](devops.md) were written against **0.2.0** and each says so at the top; where a later release moved something one of them describes, the entry below says what moved.

!!! warning "PyPI has 0.2.0 and 0.3.0, and nothing in between"
    Every release is tagged on GitHub. 0.2.1 is **not on PyPI**: its tag push ran the publish workflow and the upload step failed on a leftover configuration from the hand-built 0.2.0 bootstrap. `pip install jmfts` therefore resolves 0.3.0, and `pip install jmfts==0.2.1` finds nothing. The gap is recorded rather than repaired — republishing a superseded version under a new number would make the release record lie about what 0.2.1 was.

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
