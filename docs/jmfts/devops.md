---
title: "DevOps Manual"
category: "devops"
status: "draft"
---

# JMFTS — DevOps Manual

<p class="axis">Cognition × Acquisition</p>

How JMFTS runs in production: sizing PostgreSQL and pgvector, which container holds the embedding model and which ones deliberately do not, and what an index rebuild costs you.

!!! note "Draft. Written against 0.2.0; the current release is 0.3.0."
    Written against **0.2.0** — its `Dockerfile`, `Dockerfile.worker`, `docker-compose.yml`, `deploy/` manifests and entry points — plus benchmark and defect write-ups that are not in the public tree (see [Documents not in this release](#documents-not-in-this-release)). Not yet checked against a deployment outside the maintainer's own.

    Three things an operator needs have been corrected in place for the two releases since: [Getting it](#getting-it), the migration list under [What the Compose stack actually runs](#what-the-compose-stack-actually-runs), and the tier-2 note under [Office files](#office-files-three-tiers-two-extras). The [Changelog](changelog.md) is the release record; nothing else on this page has moved past 0.2.0.

!!! note "All of this page is released"
    [Ingestion](#ingestion-runs-on-a-queue), [the containers and worker types](#containers-and-worker-types), and [running a fleet](#running-a-fleet) shipped in **0.1.1**, along with `jmfts-worker`, `Dockerfile.worker`, `deploy/`, the `/runner` surface, and the `embed` extra that took torch out of the base install. 0.1.0 had none of it, and the notes that said "branch only" have been removed.

## Getting it

JMFTS is on PyPI, and `0.3.0` is the current release:

```bash
pip install jmfts                 # both wheels: jmfts, and the jmfts-client it depends on
```

`pip install jmfts==0.2.1` finds nothing. That release is tagged on GitHub and was never uploaded — the [Changelog](changelog.md) says why, and 0.3.0 contains everything it did.

The source is public too:

```bash
git clone https://github.com/jmccardle/jmfts.git
cd jmfts && git checkout v0.3.0    # or stay on master
```

The public repository is a squash, not a mirror: each release replaces the whole tree in one commit, so `git log` there is short by design. Tags before 0.2.0 carry no `v` prefix — `0.1.0`, `0.1.1`, then `v0.2.0`, `v0.2.1`, `v0.3.0`.

Everything below runs from that checkout. This is a system that has been running as a personal appliance — it works, and it is not a product; reranked ordering in particular is unvalidated.

For an editable install from a checkout, install the client distribution **first**. `jmfts` depends on `jmfts-client` with `==`, so an editable server install resolves the pinned version from PyPI and shadows the tree you are working in:

```bash
pip install -e ./jmfts-client
pip install -e ".[dev]"
```

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
pip install -e ./jmfts-client     # first; jmfts depends on it
pip install -e ".[dev]"           # dev adds pytest/black/ruff; plain -e . is enough to run
jmfts-init-db                     # creates the DB (if missing) and applies schema.sql
jmfts-server --host 0.0.0.0 --port 8100
```

!!! warning "0.1.0 spelled these differently"
    On 0.1.0 these were `python -m scripts.setup_db` and `uvicorn api.main:app`. The top-level `api` package is gone as of 0.1.1 — it claimed a very common name in every consumer's `site-packages` — and the setup script became an entry point. Running the 0.1.0 commands against a current checkout is an `ImportError`, not a subtle failure. `uvicorn jmfts_core.rest.main:app --reload` is still the way to get autoreload.

Either way, the API listens on port 8100 and every setting reads from the environment with a `JMFTS_` prefix. `.env.example` is the annotated list of those settings; the [Reference](reference.md) gives the built-in default behind each one, which is not always what `.env.example` shows.

The test suite runs against a throwaway database, never the appliance's: `./scripts/run_tests_docker.sh` stands up its own pgvector container and CPU embedder, and bare `pytest` needs the local role to hold `CREATEDB`.

## What the Compose stack actually runs

| Container | Image | Notes |
|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | `schema.sql` is mounted as `01_schema.sql` and runs once, on a fresh data volume. `127.0.0.1:5433` → container `5432`, chosen so it never collides with a host Postgres. |
| `api` | built from the repo's `Dockerfile` | CPU-only image — `uvicorn --reload` with `jmfts_core/` bind-mounted, so edits reload live without a rebuild. `127.0.0.1:8100`. |

Both publications are bound to loopback, not `0.0.0.0` — the dev stack is not reachable from the LAN unless you change that yourself.

`schema.sql` is the complete canonical DDL — extensions, every table, every index. It is what bootstraps a fresh database. The numbered files in `migrations/` are upgrade deltas for a database that already exists; you do not need them to stand up a new instance, only to carry an existing one forward.

`002` through `007` were in 0.1.0. 0.1.1 added five: `008_document_settled_lifecycle.sql` and `009_document_blobs.sql` for the lifecycle flag and the uploaded bytes, then `010_task_queue.sql` creating the queue, `011_task_queue_heartbeat.sql` adding `heartbeat_at` and the lease index, and `012_task_queue_batched.sql` adding the `batched` status with `batch_id`/`batched_at`. 0.2.0 adds none — office extraction needed no schema change.

0.2.1 adds two: `013_rdf_layer.sql` and `014_entity_roots.sql`. **`013` renames a column a running 0.2.0 process reads** — `predicates.domain` becomes `predicates.namespace`, and `TripleRepository.list_predicates` filters on it — so deploy the code together with that migration, not around it. Everything else in both files is additive, and entities that predate `014` are not backfilled.

0.3.0 adds two more: `015_evidence_rows.sql`, which creates `document_evidence` and **moves** twenty-nine names out of `documents.structured_content`, and `016_document_produced_by.sql`, which adds `documents.produced_by` with an index on `(parent_id, produced_by)`. `015` moves data a running 0.2.1 process reads; same rule. `016` is additive and backfills nothing — nodes that predate it read as asserted, which is the honest answer rather than a guessed one.

That is 15 migrations at 0.3.0, `002` through `016`.

Apply them in order against an existing database, or take `schema.sql` for a fresh one. Both live inside the installed package at `jmfts_core/sql/`, so `jmfts-init-db` finds them without a source checkout.

The Compose image is deliberately **not** a production build: embedding runs on CPU there, which is fine for development and wrong for bulk ingestion (see [Sizing the write path](#sizing-the-write-path-and-why-it-is-cpu-bound) below). It is also not the image the worker pools run — that one is [`Dockerfile.worker`](#four-images-two-dockerfiles), and the difference is deliberate rather than incidental.

## Auth

Every request needs `Authorization: Bearer <token>`. Two modes, both controlled by `JMFTS_API_TOKEN`:

- **Left blank** — the server generates a token at startup and prints it to stdout, the same pattern Jupyter uses. There is no state where a blank token means "allow all."
- **Set to a value** — that token is pinned, and the startup message is silenced. The Compose file pins `jmfts-dev-local` by default specifically so other local services (an agent harness, a test client) can point at a known value; override it by exporting `JMFTS_API_TOKEN` before `docker compose up`.

`JMFTS_CORS_ORIGINS` is a JSON list of allowed browser origins and defaults to empty — server-to-server only, no `Origin` header accepted. `"*"` is rejected outright when credentials are in play; there is no wildcard escape hatch.

There is a **second, unrelated credential** — `JMFTS_RUNNER_KEY`, which gates the embedding surface and resolves to no principal at all. It is described with [the runner container](#the-runner-container); the two are deliberately disjoint, and an API token cannot embed.

## The model stack is an extra, not a dependency

!!! note "Since 0.1.1"
    On 0.1.0, `torch` and `sentence-transformers` were ordinary dependencies and every install had them.

**`pip install jmfts` does not install torch.** Base JMFTS is storage, retrieval, the tree, BM25, the queue and the whole ingest pipeline. The only step in any of that which needs an accelerator is producing vectors, and since [`embed` became its own task type](#worker-types) that step is one HTTP call away from being another process's problem.

```bash
pip install jmfts                 # storage side: no torch, cannot embed
pip install 'jmfts[embed]'        # + torch (CUDA build) and sentence-transformers
```

Measured with a clean virtualenv by `scripts/check_base_install.sh`: **583 MB installed, against 5.2 GB with `[embed]`.** That gap is the whole reason the split exists, and it is paid on every cold start of every replica.

A base install is not a crippled install. It still **measures** text — `check_fit`, the chunker, and matryoshka truncation are tokenizer and numpy work, and `transformers` stays in the base dependency list precisely so that a storage-side process measures with the same tokenizer the model would have used. What it cannot do is produce a vector, and it says so by name:

```
ModelStackNotInstalled: No module named 'torch'

This JMFTS was installed without the embedding model stack, so it cannot produce
vectors itself. Either give it the model:
    pip install 'jmfts[embed]'                                  # CUDA build
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install 'jmfts[embed]'                                  # ...then CPU
or point it at a JMFTS that has one:
    JMFTS_RUNNER_URL=http://<host>:8100 JMFTS_RUNNER_KEY=<the shared secret>
```

Three operational consequences worth stating before you build an image:

- **An install with no model is a deployment, not a fault**, which is why the message names both exits rather than just the `pip` one.
- **`ImportError` classifies PERMANENT.** A package that is not installed is not installed on the third attempt, so the task fails the node immediately with a readable reason instead of arriving three backoffs later.
- **There is no `[cpu]` extra.** The wheel index is an install-time choice pip cannot take from a dependency specifier, so a `cpu` extra would be a name that installed the CUDA build anyway. CPU torch is two commands, and `Dockerfile.worker` takes them as one build argument.

## Office files: three tiers, two extras

!!! info "Tier 2 has three callers"
    `.docx` and `.pptx` extraction went live in 0.2.0, and 0.2.1 gave `openpyxl` a caller too: `structure:sheets`, `profile:sheet` and `extract:sheet` read a workbook into worksheet and record nodes. A worker that ingests any of the three **needs `jmfts[office]`**, and one that does not is correctly installed without it. `profile:sheet` also sketches every column by default, which needs `jmfts[sketch]`. The legacy binary formats are still detected and probed but not read — the [Reference](reference.md#office-formats) has the per-format table.

Office support splits the same way the model stack does, and for the same reason, but into three tiers rather than two — because one of the dependencies is not a wheel at all.

| Tier | What | Weight | Where it goes |
|---|---|---|---|
| 1 | `zipfile`, `xml.etree`, `olefile` | stdlib plus one pure-Python module | base install |
| 2 | `python-docx`, `python-pptx`, `openpyxl` | +44 MB, **not** pure Python | `jmfts[office]` |
| 3 | LibreOffice, driven by `unoserver` | ~500 MB system package | a badged worker image; `jmfts[convert]` is the client only |

```bash
pip install jmfts                 # detects and probes .docx/.pptx/.xlsx; cannot open one
pip install 'jmfts[office]'       # + the readers; .docx and .pptx now extract
pip install 'jmfts[convert]'      # + the unoserver client — useless without LibreOffice
```

**Which workers need tier 2 is now an operational decision, not a hypothetical one.** A fleet that ingests office documents needs `jmfts[office]` on the workers that drain `extract:text`. A storage-side worker that only settles nodes and writes rows does not. Getting it wrong is loud rather than quiet: the task fails PERMANENT with `OfficeStackNotInstalled` naming the extra, on the first attempt.

**Tier 1 must stay in the base install, and that is a hard constraint.** Probe depends on nothing, calls no model, and always runs. If probing a `.docx` needed the `office` extra, a base install would accept the upload, run probe, and report an empty pattern set — which is indistinguishable from a `.docx` that genuinely declares no structure. Reading `word/styles.xml` out of a ZIP needs no library, so honouring the constraint costs nothing.

**Tier 2 is separate even though it is small.** 44 MB is nothing like torch's 4.6 GB, and the split is not about weight.

!!! warning "Tier 2 is not pure Python, and the three names hide that"
    Measured 2026-08-22 in empty venvs against the 0.2.0 wheels: base is **585 MB**, `jmfts[office]` is **629 MB**. The three named packages are only 9 MB of that gap (docx 2.9, pptx 3.1, openpyxl 3.0). The rest is transitive: `python-docx` and `python-pptx` both require `lxml` (12 MB), and `python-pptx` also requires `Pillow` (7.1 MB) and `XlsxWriter` (1.9 MB).

    **`lxml` and `Pillow` are C extensions.** On a platform with a wheel for both — every platform this project targets — that is invisible. On one without, tier 2 needs a build toolchain in the image, which is exactly the possibility a "pure Python" label tells you not to plan for.

The split is about who pays, not about the number. The alternative is putting three readers into every install to serve the one worker in a fleet that ingests office files. A storage-side worker that never touches a `.docx` is correctly installed and correctly has no `python-docx`.

That claim is what the error message has to carry, so it names the extra rather than the module:

```
OfficeStackNotInstalled: No module named 'docx'

This JMFTS was installed without the office readers, so it can detect and probe
office files but cannot open one. Install them:
    pip install 'jmfts[office]'
A worker that does not ingest office files does not need them; see
jmfts_core/office/__init__.py.
```

There is no remote equivalent of `JMFTS_RUNNER_URL` here. The office readers are 44 MB, so "install it" is the whole answer, where for the model stack's 4.6 GB it is one of two. `OfficeStackNotInstalled` subclasses `ImportError` and therefore classifies **PERMANENT**, the same as `ModelStackNotInstalled`: a package that is not installed does not appear on the third attempt.

**Tier 3 is a worker, not an extra, because `pip install libreoffice` is not a thing.** It follows the `JMFTS_RUNNER_URL` shape instead — a task type, a worker badge, and an optional URL that makes it another process's problem. It earns a whole image by doing two jobs, which is why the extra is named `convert` rather than `render`:

1. **Legacy formats.** `.doc`, `.xls` and `.ppt` convert to OOXML so the tier-2 readers can open the result. The alternative was three more binary-format readers, each worse at its format than LibreOffice is.
2. **Renditions.** Any document converts to PDF once, at ingest, so serving a citation image is `pymupdf` over a stored PDF — and `pymupdf` is already a base dependency, so the query path needs no tier-3 dependency at all.

`unoserver` and not `unoconv`, which is unmaintained, and not `soffice --headless --convert-to` per file: that pays a cold start per document, and two concurrent invocations fight over the same user profile directory.

Three consequences for how you build images and place work:

- **`office` is implied by `dev`, `convert` is not.** The office tests open real packages. The `unoserver` pip package installs cleanly with no LibreOffice present and is useless without it, so a suite that installed it would be testing a configuration nobody runs.
- **A legacy file is read-only.** For `.doc`/`.xls`/`.ppt` the converted OOXML is what gets read, so the source of truth for any future edit is the conversion, not the upload. Editing one would hand back a `.docx` where the user supplied a `.doc`.
- **Renditions roughly double blob storage** for office documents. Off by default is the proposal; whether the policy is per-ingest, per-usetype or global is not decided.

## The embedding model

Document and token embeddings both come from `nomic-ai/modernbert-embed-base` (configurable via `JMFTS_EMBEDDING_MODEL`). First boot downloads it — a few hundred MB — into a cache volume (`hf_cache` in Compose, `~/.cache/huggingface` natively), and it persists across restarts. The worker images skip that download entirely by baking the model in at build time.

`JMFTS_EMBEDDING_DEVICE` is `cpu` in the dev image on purpose (no CUDA in that container). Set it to `cuda` for anything that embeds at volume — see the next section for why this matters more than it sounds like it should.

**Concurrency inside one process is one inference at a time.** `EmbeddingService` holds a lock across the whole forward pass, so two worker threads in one process serialise on the model and the second one buys nothing. Concurrency on a host is processes, and each process holds its own copy of the weights plus its own attention peak.

## The reranker is a second model, loaded only if asked

`?rerank=true&rerank_method=cross_encoder` loads a second model, separate from the embedder. The default is `cross-encoder/ms-marco-MiniLM-L-6-v2` (~22M params), small enough to run on CPU, and it downloads into the same Hugging Face cache on first use. Change it with `JMFTS_RERANKER_MODEL` — any Hub cross-encoder works, but a larger one is a real GPU-memory decision on top of the embedder, not a free swap.

`JMFTS_RERANKER_DEVICE` defaults to blank, which means "follow `JMFTS_EMBEDDING_DEVICE`". A CPU-only deployment therefore stays CPU-only without setting a second variable. Pin it only when you want the reranker on a different device from the embedder.

Nothing loads until a request actually asks for reranking, so a deployment that never passes `rerank=true` pays nothing. When a request does ask and the model cannot load, the request fails — it does not quietly return the unreranked ranking.

A cross-encoder is the same `sentence-transformers` stack, so it belongs to the same `[embed]` extra and is absent from a base install for the same reason. **Reranking has no `/runner` equivalent**: `JMFTS_RUNNER_URL` does not help here, and a container that must rerank must carry the model.

## Sizing the write path — and why it is CPU-bound

A 2026-07-23 baseline (`scripts/benchmark_write.py`, CPU embedding, empty pgvector DB) measured each write op in isolation. The public tree keeps only the product CLI in `scripts/`, so the harness that produced these numbers is not in the tarball you can clone today — it ships with the evaluation work described [below](#documents-not-in-this-release):

| op | ops/s | p50 latency |
|---|---|---|
| document create (no embed) | ~1,943 | 0.50 ms |
| document create **+ embed** | ~13 | 49 ms |
| triple upsert | ~1,227 | 0.82 ms |

The bare insert path — the `path` trigger, HNSW index maintenance — is sub-millisecond and was never the bottleneck. Embedding is roughly **100× the cost** of everything else in the write path combined, and it is the thing the CPU dev image is worst at. If you are sizing a deployment for bulk ingestion, treat `JMFTS_EMBEDDING_DEVICE=cuda` as the first lever, not a nice-to-have; batching embedding calls is the other one, though there is no batch document-create endpoint yet — see [Known gaps](#known-gaps-and-hazards) below.

This baseline did not include the final commit's durability flush, and CUDA throughput was not measured — both are open items on the benchmark backlog that lands with the harness, not settled numbers.

That 100× ratio is the fact every deployment decision on this page descends from. It is why embedding is a badge, why it is its own task type, and why a fleet's worth of storage-side containers can go without the model entirely.

## Index maintenance

The vector side (`documents.embed`, `token_embeddings.embed_256/384/512`) is maintained automatically by pgvector's HNSW/IVFFlat indexes on every insert — no separate rebuild step.

The BM25 side is different: `POST /indexes/{index_name}/index-document/{document_id}` (backed by `index_document`) is idempotent as of a since-fixed defect (it now subtracts a document's old contribution before re-adding, short-circuiting on an unchanged content hash), so indexing a document you've already indexed no longer inflates the corpus statistics BM25's IDF is derived from. You can index incrementally, document by document, as content arrives. `POST /indexes/{name}/refresh` remains available and rebuilds an index's statistics from scratch — correct by construction, but its cost is proportional to the whole indexed corpus, so reach for it as a repair tool, not a routine one.

## Ingestion runs on a queue

`POST /ingest/file` stores the uploaded bytes, enqueues one `probe` task, and **returns before any work is done**. Everything after that — detecting the format, pulling text out, building the tree, embedding it, rolling summaries back up — is a worker draining `task_queue`. The operational consequences are worth stating plainly:

- **A 200 from the upload means "accepted", not "ingested".** Poll `GET /ingest/file/{id}/frontier` for progress. It returns counts, never a percentage: the task set below the current frontier does not exist until the frontier reaches it, so any denominator would move backward as work is discovered.
- **An unfinished document is invisible to search.** The retrieval indexes are partial on `documents.settled`, so an `in_flight` node is not returned by any search method. That is a feature — a half-built tree should not answer queries — but it means "my document is not in search results" and "my ingestion is still running" look the same from the outside. The frontier endpoint is how you tell them apart.
- **A permanently failed task settles its node `failed`.** Without that, a node whose ingestion died would be indistinguishable from one still in progress, and the settle walk would wait on it forever.
- **Options are fixed at upload.** Uploads deduplicate on content hash, and an upload of stored bytes asking for different options is a 400 rather than a re-run. Reprocessing under changed options is specified and not built, so the available path is delete and re-upload — decide chunking and model selection before a bulk run, not during one.

### What you cannot see, and what to monitor instead

`task_queue` has **no REST surface**. No endpoint lists rows, names the task that failed, retries one, or cancels one. Plan monitoring around that rather than expecting to add a dashboard later:

- **Per document**, the frontier's `tasks_unfinished` is the closest thing to a health signal. Zero unfinished tasks while `nodes_in_flight` is above zero means the frontier is waiting on something outside the queue — nothing is coming to finish those nodes. A non-zero value says work is queued and says nothing about whether anything is claiming it, so alert on the counts **not moving**, not on their value.
- **Per corpus**, `scripts/e2e_ingest_corpus.py report` is the real instrument. It lists every failed task with its error type, the tree shape by usetype and depth, whether the result is retrievable through each search method, and wall clock per task type.
- **Per appliance**, SQL against `task_queue` is the only way to answer "which tasks are stuck and since when". `heartbeat_at`, `claimed_by` and `status` are the columns worth a saved query.
- **For batches**, `jmfts-batch-worker stalled` is separate and exits non-zero, because a `batched` row is invisible to everything above.

### Uploads with no parent are ungoverned, permanently

Worth stating here because it is a deployment property, not an API detail. Subtree RBAC resolves strictly along the tree path, so a file uploaded with no `parent_id` sits under no access-control root — and a grant made afterwards cannot reach it. The two fixes are both upload-time: a `parent_id` inside an already-governed subtree, or `private=true`. If your deployment relies on RBAC at all, make one of the two mandatory in the client rather than in a runbook. See the [Cookbook](cookbook.md#keep-an-upload-out-of-the-shared-knowledgebase).

## Containers and worker types

Everything that runs is one of five process roles over one of four JMFTS images, plus stock Postgres. The images differ in **whether they carry the embedding model**; the process roles differ in **what they do with it**. Those two axes are independent, which is the part worth internalizing: an image that holds the model can run a process that never uses it, and a process that answers for embedding work can run in an image that has no torch at all.

### Four images, two Dockerfiles

| Image | Built by | Torch | Size |
|---|---|---|---|
| `pgvector/pgvector:pg16` | upstream, unmodified | — | upstream |
| the API image | `Dockerfile` | CPU wheel, `[embed]` | not measured |
| `jmfts-worker-cpu` | `Dockerfile.worker`, defaults | CPU wheel, `[embed]` | **3.98 GB** |
| `jmfts-worker-gpu` | `Dockerfile.worker --build-arg TORCH_INDEX=…/cu126` | CUDA wheel, `[embed]` | larger; not measured |
| `jmfts-worker-thin` | `Dockerfile.worker --build-arg EXTRAS=` | **none** | **689 MB** |

```bash
docker build -f Dockerfile.worker -t jmfts-worker-cpu:latest .
docker build -f Dockerfile.worker -t jmfts-worker-gpu:latest \
       --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu126 .
docker build -f Dockerfile.worker -t jmfts-worker-thin:latest \
       --build-arg EXTRAS= .
```

Sizes are `docker images` against the two builds that were made; the CUDA one was not built for a number, so this page does not carry one for it.

Four notes on the recipes, each of which is a decision you can get wrong:

- **The images are named, not tagged.** `kustomize` matches an image override by *name*, so one `jmfts-worker` name with three tags would make a single override rewrite every pool — and the GPU pool would silently run the CPU image, working correctly and slowly with the card idle and nothing reporting a problem.
- **There is no CUDA base image.** The `cu126` wheels vendor the CUDA runtime as `nvidia-*` pip packages, so a slim Python base plus the right wheel index is a complete GPU install; the host contributes only the driver, through `nvidia-container-toolkit`. Using `nvidia/cuda` as the base would pin a second, redundant CUDA against the one torch already brings.
- **The model is baked in at build time.** Without that, every cold pod downloads a few hundred MB before it can claim its first task — which is exactly the wrong shape for autoscaling, since scale-up latency would be dominated by the download and a queue spike would be answered by pods that spend their first minute idle. The alternative, a shared ReadWriteMany volume, needs storage a k3s cluster may not have. `HF_HUB_OFFLINE=1` at runtime makes a missing model fail immediately rather than quietly reaching for the network.
- **The thin image still bakes the tokenizer.** It does not embed, but it does measure, and `check_fit` is called once per candidate piece by the chunker. A thin worker that fetched the tokenizer on first use would stall on precisely the cold start the bake exists to remove.

The API image is **not** a variant of the worker image. It exists to serve HTTP with `--reload` over a bind-mounted source tree, which a pod that scales up cannot do; the worker image runs `jmfts-worker` over code baked in at build time.

### The API container

Serves the REST surface, and always holds the model. `JMFTS_RUNNER_URL` does not empty it out, and the reason is worth being precise about: **that setting covers the ingest write path only** — the `embed` task and the vector `summarize` writes. Search embeds its query in the request path, and routing that over HTTP would put a network hop inside every search. A process that serves `/search` needs the model locally, whatever else is configured.

One setting decides whether an API container is also a worker:

```
JMFTS_INGEST_WORKER_ENABLED=true    # default: a worker thread inside the API process
JMFTS_INGEST_WORKER_ENABLED=false   # what deploy/k8s/10-config.yaml sets
```

The default is right for a single appliance, which would otherwise accept uploads and never process them. It is wrong for a fleet, where it would make total ingest capacity depend on how many API replicas happened to be running.

### The runner container

The same image and the same application, configured to sell embedding rather than to store anything. `GET /runner/info`, `POST /runner/embed`, and `POST /runner/embed/tokens` answer "embed this text" for a caller that keeps the documents somewhere else — possibly in a database this process cannot reach. None of the three routes opens a database session and none of them resolves a principal.

That is why the credential is separate:

| | `JMFTS_API_TOKEN` | `JMFTS_RUNNER_KEY` |
|---|---|---|
| resolves to | a principal, whose grants filter which subtree the request sees | nothing — there is no subtree to scope |
| stored as | a row in `api_tokens` | a shared secret in the environment |
| blank means | generate, print, and require an ephemeral token | the surface answers **503** |
| can it read a document? | yes | no |
| can it embed? | no | yes |

The two are disjoint in both directions, and the app-level bearer check steps aside for the `/runner` prefix rather than accepting either credential — making them alternatives inside one dependency would have produced exactly the coupling the split exists to avoid.

**Blank is the off switch here, not a generator.** `JMFTS_API_TOKEN` generates when blank because one appliance printing a token an operator reads is the case it serves. A fleet is the opposite case: two replicas would generate two different keys, and a worker would authenticate against whichever pod it happened to reach. So a blank runner key means "this deployment does not offer embedding", and it never means "come in."

### Worker types

The task type is what routes work; the container is what can do it. Five shapes exist, and they are not five programs — every one of them is `IngestWorker`.

| Shape | Image | Runs the model? | Badge |
|---|---|---|---|
| thread inside the API process | the API image | yes, locally | none |
| `jmfts-worker`, CPU pool | `jmfts-worker-cpu` | carries it, never uses it | `cpu` |
| `jmfts-worker`, embed pool | `jmfts-worker-gpu` | yes, on a card | `embed` |
| `jmfts-worker`, LLM pool | `jmfts-worker-gpu` or `-cpu` | yes, for the summary it stores | `llm` |
| `jmfts-worker --runner-url …` | `jmfts-worker-thin` | **no** — posts to a runner | `embed` |

```bash
jmfts-worker                                     # claims everything; one appliance
jmfts-worker --badge cpu --worker-id cpu-0       # a pool member
jmfts-worker --badge embed --badge llm           # two badges, one worker
jmfts-worker --drain                             # until the queue is empty, then exit
```

Three of those rows deserve a note.

**The CPU pool's badge names nothing.** `JMFTS_TASK_BADGES` maps `embed` and `summarize` to `embed`, and `summarize:llm` to `llm`. Nothing maps to `cpu`. Since a badged worker claims its own badges *plus* everything un-badged, a worker badged `cpu` claims exactly the un-badged task types — `probe`, `extract:text`, and the three structure rungs. The badge is a name for "this pool is not the scarce one", and it works by matching no policy entry at all.

So the CPU pool never runs the model, and still ships it: `jmfts-worker-cpu` is also the image the metered LLM pool runs, and *that* pool embeds the summary it stores. One image, two pools, one of which uses half of it. Building a third image to save the difference would be a third thing to keep in sync — but if a fleet grows enough CPU replicas for 3.98 GB each to matter, the thin build is already the answer, and it needs a runner rather than a new Dockerfile.

**The LLM pool is two deployments for one badge, and that is the point.** `llm` names a *resource* — "this worker can get a completion" — not a machine shape. `jmfts-worker-llm-local` runs a model on a card; `jmfts-worker-llm-api` forwards to a metered web API and needs no accelerator. Both answer the same badge, so adding a replica to either adds capacity for the same work, and an idle local GPU absorbs work the API would otherwise have been paid for. Both still carry the embedding model, because both embed the summary they store — which is why they are JMFTS workers and not scripts.

**A thin worker is answering for embedding work; it just is not doing it.** The badge and the location of the model are orthogonal, and confusing them is the easiest mistake on this page. A thin worker built with `EXTRAS=` **must** be given `--runner-url` — otherwise its first `embed` task raises `ModelStackNotInstalled` and fails the node permanently.

### Batch processing halves the LLM bill

A separate entry point (`jmfts-batch-worker`) for a separate concern: it consumes `summarize:llm` through an external batch provider at roughly half price. Nothing in `jmfts_core` depends on it, and it is not a badge.

The operational shape is a handoff between two schedulers. A worker claims a set of tasks, submits them, and trades its claim for a `batched` status that outlives the worker — so the answer it has already paid for is not bought a second time by whoever claims next. Any worker that can reach the provider may then adopt the batch and finish it.

Two things to know before running it:

- **A `batched` row is invisible to every other recovery mechanism.** The claim query will not take it, and the lease will not reap it — nothing beats for a parked row, because the work is at the provider rather than in a worker. `jmfts-batch-worker stalled` is the only stall signal, and it exits non-zero so a cron or a probe can act on it. Both providers expire a batch at 24 hours; the default threshold is 26.
- **Gather size is bounded by the tree, not by the API.** Both providers accept tens of thousands of requests per batch, but every gathered task holds its node's reservation for the batch's whole life. Gathering broadly freezes a large part of the tree for a day to save a few HTTP calls. The default is 32.

Scheduling the batch window is a Kubernetes concern, not a queue concern — spin the direct LLM pool down and the batch pool up on a cron scaler. The queue never needs to know what time it is.

### Embedding as a service

`--runner-url` is what makes the thin worker possible. It sends the `embed` task's text to another JMFTS's `/runner` surface instead of loading the model locally:

```bash
jmfts-worker --badge embed --runner-url http://jmfts-api:8100 --worker-id thin-0
```

Both sides read one `JMFTS_RUNNER_KEY`, and a URL with no key is refused **at startup** rather than tried anonymously — a misconfiguration should be a pod that will not come up, not one failed task in a log. No network call is made at startup, though: a runner briefly unreachable is a transient the retry policy already handles, and refusing to boot over it would turn a blip into an outage.

<figure class="dia"><svg viewBox="0 0 680 250" role="img" aria-labelledby="dia-fleet-t dia-fleet-d"><title id="dia-fleet-t">A fleet whose workers do not hold the model</title><desc id="dia-fleet-d">Three square boxes across the top, named thin dash zero, thin dash one and thin dash two, each started with the runner dash url flag. Short stubs drop from all three onto one horizontal bracket that joins them. From the middle of the bracket a single arrow runs down into a stack of two slabs — a hairline token embeddings slab above a hatched, doubled-outline documents slab — captioned as the rows the workers write. From the right end of the same bracket, marked with a small red square, a red connector runs right and then up into a fourth box on the far right named jmfts dash server, labelled slash runner, and annotated as holding the model with no database and no principal. The red connector is the only red element and is captioned one HTTP call, POST slash runner slash embed slash tokens.</desc><defs><pattern id="dia-fleet-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="20" y="18" class="label-soft">jmfts-worker --runner-url … (no torch)</text><rect x="20" y="28" width="130" height="34" class="fill-ground stroke"/><text x="85" y="50" text-anchor="middle" class="label">thin-0</text><rect x="160" y="28" width="130" height="34" class="fill-ground stroke"/><text x="225" y="50" text-anchor="middle" class="label">thin-1</text><rect x="300" y="28" width="130" height="34" class="fill-ground stroke"/><text x="365" y="50" text-anchor="middle" class="label">thin-2</text><line x1="85" y1="62" x2="85" y2="86" class="stroke"/><line x1="225" y1="62" x2="225" y2="86" class="stroke"/><line x1="365" y1="62" x2="365" y2="86" class="stroke"/><line x1="85" y1="86" x2="365" y2="86" class="stroke"/><line x1="225" y1="86" x2="225" y2="139" class="stroke"/><path d="M225 148 L220 138 L230 138 Z" class="fill-ink"/><rect x="105" y="150" width="240" height="22" class="fill-ground stroke-hair"/><text x="225" y="165" text-anchor="middle" class="label-soft">token_embeddings</text><rect x="105" y="172" width="240" height="34" fill="url(#dia-fleet-hatch)" class="stroke"/><rect x="109" y="176" width="232" height="26" class="fill-none stroke-soft"/><rect x="175" y="180" width="100" height="18" class="fill-ground"/><text x="225" y="193" text-anchor="middle" class="label">documents</text><text x="225" y="226" text-anchor="middle" class="label-soft">the rows, written by the workers</text><rect x="360" y="81" width="10" height="10" class="fill-red"/><path d="M365 86 L470 86 L470 45 L491 45" class="stroke-red fill-none"/><path d="M500 45 L490 40 L490 50 Z" class="fill-red"/><text x="470" y="116" text-anchor="middle" class="label-mark">one HTTP call</text><text x="470" y="133" text-anchor="middle" class="label-soft">POST /runner/embed/tokens</text><text x="580" y="22" text-anchor="middle" class="label-soft">/runner</text><rect x="500" y="28" width="160" height="34" class="fill-ground stroke"/><text x="580" y="50" text-anchor="middle" class="label">jmfts-server</text><text x="580" y="80" text-anchor="middle" class="label-soft">holds the model</text><text x="580" y="96" text-anchor="middle" class="label-soft">no database, no principal</text></svg><figcaption>The workers write every row; the runner writes nothing. Red marks the seam the arrangement exists to create — the one place a vector crosses a network — and it is the only thing in the picture that is not a storage-side process.</figcaption></figure>

**What this changes about capacity.** Without it, every worker that touches ingest owns weights, so the cards are allocated by which pool you started: an embedding pool with a card each and a summarization pool with a card each, sized before the corpus arrives. With it, the storage-side workers scale on CPU and the cards sit behind one runner that both kinds of work draw from — so a corpus that is mostly chunking and a corpus that is mostly summarizing get the same hardware without a redeploy.

**Cost.** Each `embed` becomes an HTTP round trip carrying a base64 float16 token matrix — measured at **171 KB for a 256×256 matrix, against 1,398 KB for the same numbers as JSON.** That is a LAN cost, not a WAN one. The tokenizer stays local, deliberately: forwarding `check_fit` would put a round trip inside every chunking decision.

**What it does not cover.** Search, as [above](#the-api-container). And reranking, which has no runner surface at all.

There is **no runner Deployment in `deploy/k8s/` yet.** An embedding pool plus a thin pool needs a Service and a second ScaledObject, and that has not been written; the code side is complete and the manifests are not.

### Four ways to arrange them

Each shape is a superset of the one above it. Start at the top and move down when a specific thing hurts.

| Shape | Processes | The model lives | Move on when |
|---|---|---|---|
| **Single appliance** | Postgres + API (worker thread on) | in the API process | ingestion starves search of CPU |
| **Two processes** | Postgres + API + `jmfts-worker` | in both | one worker cannot keep up, or you want it on another host |
| **Pooled fleet** | Postgres + API + CPU / embed / LLM pools | in every worker image | the cards are misallocated between embedding and summarizing |
| **Runner-backed fleet** | as above, but thin workers + a runner | in one runner | — |

The second row is the one most deployments should reach and stop at. The fourth is not a scale story so much as an allocation story: it exists because a fixed set of GPUs has to be shared between embedding and summarization, and the pooled shape decides that split at deploy time.

## Running a fleet

### The lease measures the worker, not the task

A worker writes `heartbeat_at` on a fixed interval while it holds a task. Another worker requeues a task whose heartbeat has gone stale for longer than `JMFTS_WORKER_LEASE_SECONDS`.

This is deliberately **not** a task timeout. Task durations here vary by orders of magnitude with input — a one-page text file and a 400-page PDF are the same task type — so a lease keyed on elapsed runtime would need a bound on legitimate task duration that nobody can supply. It would reap work that is still running and then run it a second time, concurrently, on another host. A bound on how long a live worker may go without reporting in is a property of the loop, and that is knowable.

The lease must be at least 3× the heartbeat interval; the worker refuses to start otherwise. Below that ratio one missed beat costs a running task.

There is a second, cheaper recovery path: a worker recovers **its own** claims at startup, which is provably safe with no clock at all — a process that is starting cannot also be running the task its previous incarnation claimed. That covers a restart, and it is why `JMFTS_WORKER_ID` is set from the pod name via the downward API: a restarted pod keeps its name and reclaims its own rows immediately, rather than waiting out the lease. The lease covers everything else: a pod rescheduled under a new name, or a host that never comes back.

Two settings follow from this and are worth pairing in your head:

- **No CPU limit on a worker pod.** Throttling a worker mid-task delays its heartbeat as readily as its work, and a throttled worker that misses beats is indistinguishable from a dead one. The memory limit stays — an OOM kill is a clean death the lease already handles.
- **`terminationGracePeriodSeconds` must exceed the longest task.** SIGTERM is handled: the worker stops the loop and lets the in-flight task commit. Too short a grace period and the runtime follows with SIGKILL, the task dies mid-flight, and the lease reaps it — correct, and a wasted run.

There are **no readiness or liveness probes** on a worker, on purpose. A worker serves no traffic, so readiness has nothing to gate, and the honest liveness signal is `task_queue.heartbeat_at`, which another worker already acts on. An HTTP probe would only report that the process is up, which is the one failure mode the lease already covers.

### Badges route work to pools

`JMFTS_TASK_BADGES` maps a `task_type` to a badge. A worker claims the badges it was given plus anything un-badged; an un-badged worker claims everything.

```json
{"embed": "embed", "summarize": "embed", "summarize:llm": "llm"}
```

| Badge | Scarce resource | Task types |
|---|---|---|
| `embed` | the embedding model | `embed`, `summarize` |
| `llm` | a completion | `summarize:llm` |
| *(none)* | neither | `probe`, `extract:text`, `structure:declared`, `structure:inferred`, `structure:semantic` |

Measured end to end over a real directory with `scripts/e2e_ingest_corpus.py` (5 files, 559 nodes, CPU embedding):

| task_type | runs | total_s | mean_s | share |
|---|---|---|---|---|
| `structure:declared` | 5 | 153.6 | 30.72 | 54% |
| `summarize` | 5 | 128.5 | 25.69 | 46% |
| `extract:text` | 5 | 0.1 | 0.01 | 0.04% |
| `probe` | 5 | 0.02 | 0.02 | 0.03% |

The two task types that cost anything are the two that ran the embedding model, and the two that cost nothing are the two the code documents as not embedding. So the split is not a judgement about heavy and light work — it is about which scarce resource the handler needs. Re-measure before changing the policy rather than reasoning about which work looks heavy.

**That table is also why `structure:declared` is no longer badged.** It was not a slow text splitter; it created every chunk with `auto_embed=True`, so its 30 seconds were N transformer forward passes running in a loop inside one claimed task. That embedding is now its own task type, `embed`, scoped to the node it embeds — so a document's chunks embed concurrently instead of in sequence, and the 54% above is redistributed across as many tasks as the document has chunks. The rungs dropped out of the policy in the same change: badging string work for a GPU pool would pin it to the scarce resource for nothing. This is the policy map getting **smaller** as it gets sharper.

**Why `summarize` and `summarize:llm` are separate task types.** Every `summarize` embeds. Only the ones whose concatenated children overflow the embedding window need a completion, and which ones those are is decided by `check_fit` *inside* the handler, after the claim — the queue cannot know it at enqueue time. So `summarize` does the fit check and either stores the concatenation itself or enqueues `summarize:llm`, which carries the `llm` badge. Before the split there was one badge for a handler needing two scarce resources, and no way to name the expensive one without also claiming the cheap one.

!!! warning "Two ways to get badges wrong, and one is silent"
    **A badge no worker answers to stalls forever.** Tasks sit `pending`, their nodes never leave `in_flight`, they stay out of the retrieval indexes, and nothing reports it — because a worker that does not exist cannot fail to report in. Delete a Deployment, delete its badge from the map. Turn the policy on only where every badge it names has a running pool.

    **An un-badged worker claims everything**, including GPU work. One un-badged worker anywhere in a fleet will run embedding on a CPU while the card idles, and will spend money on a metered API for work the local model would have done for free. In a fleet, every worker needs a badge.

Badges filter; they do not order. `claim_next` sorts by `priority DESC, created_at ASC` across the whole claimable set, so a worker listing two badges will start a bulk task a second before an urgent one arrives. `priority` on the row is the lever for that.

**Routing by cost and urgency** is a finer badge, not a new mechanism. Split `llm` into `llm-fast` and `llm-bulk` in the ConfigMap, give the local pool both and the metered pool only the cheap one. The exact names are yours; nothing in the code knows them.

This is why the routing policy is **empty by default** in `jmfts_core/config.py` and set in `deploy/k8s/10-config.yaml`, next to the Deployments that define the pools it names.

### Applying the manifests

```bash
kubectl -n jmfts create secret generic jmfts-worker-db \
        --from-literal=JMFTS_DB_PASSWORD='…'
kubectl apply -k deploy/k8s/
```

The manifests carry no registry, no storage class and no node labels, so they apply to any cluster; `deploy/k8s/kustomization.yaml` is the single place to point them at your images. The database is assumed reachable at `postgres.jmfts.svc.cluster.local` — change it in `10-config.yaml` if yours lives elsewhere.

`11-secret.example.yaml` is **not** in the kustomization, and applying it would install the literal string `CHANGE-ME` as the database password. Create the real secret first.

| Deployment | Image | Badge | Device | Replicas |
|---|---|---|---|---|
| `jmfts-worker-cpu` | `jmfts-worker-cpu` | `cpu` | cpu | 2 (KEDA 1–12) |
| `jmfts-worker-gpu` | `jmfts-worker-gpu` | `embed` | cuda | **= your GPU count** |
| `jmfts-worker-llm-local` | `jmfts-worker-gpu` | `llm` | cuda | 0 |
| `jmfts-worker-llm-api` | `jmfts-worker-cpu` | `llm` | cpu | 1 (KEDA 0–4) |

**One pod per GPU, one inference per pod.** The embed pool requests a whole `nvidia.com/gpu`, which gives the pod exclusive access and lets the scheduler — rather than luck — decide there is room. Raising `replicas` past the number of cards leaves pods Pending forever, because the device plugin has nothing to allocate.

### Autoscaling

Needs [KEDA](https://keda.sh), applied separately because the pools work without it:

```bash
kubectl apply -f deploy/k8s/40-keda-scaledobject.yaml
```

Two pools scale, on separate queries, because a backlog of `summarize:llm` says nothing about how much `probe` work is waiting:

| Pool | Range | Cooldown | Bounded by |
|---|---|---|---|
| `jmfts-worker-cpu` | 1–12 | 300 s | CPU and the database |
| `jmfts-worker-llm-api` | 0–4 | 600 s | **cost** — every replica is calls against a metered service |

The `embed` and `llm-local` pools are **not** scaled, because they are bounded by physical devices; an autoscaler on either could only produce Pending pods.

The scalers read queue depth rather than CPU percent. A worker blocked on the database or on an LLM looks idle by CPU, and scaling on that would shrink the pool exactly when the queue is deepest.

### Talking to a metered API

`JMFTS_LLM_API_KEY` is sent as `Authorization: Bearer …` and **only when non-empty**, so one worker image serves both an unauthenticated llama-server on the LAN and a paid API.

HTTP 429 classifies as retryable, so the existing exponential backoff absorbs rate limiting. A 4xx that is a statement about the request — a model name that does not exist, for instance — stays PERMANENT and fails the node, because it will not fix itself.

### Two hosts, no Kubernetes

Useful for checking that two machines really do share the queue before any of the Kubernetes machinery is involved. Both hosts need the database reachable.

1. Apply the migration once, against the shared database: `psql -f migrations/011_task_queue_heartbeat.sql`
2. On the GPU host, start a worker that answers both pools: `JMFTS_EMBEDDING_DEVICE=cuda jmfts-worker --badge embed --badge llm --worker-id gpu-0`
3. On the second host, start a CPU worker: `JMFTS_DB_HOST=<gpu-host> jmfts-worker --badge cpu --worker-id cpu-0`
4. Export the routing policy to both, or leave it unset and let either claim anything: `JMFTS_TASK_BADGES='{"embed":"embed","summarize":"embed","summarize:llm":"llm"}'`
5. Upload a directory and watch both `claimed_by` values appear: `SELECT claimed_by, task_type, count(*) FROM task_queue GROUP BY 1, 2;`

`jmfts-worker --drain` runs until the queue is empty and exits, which is the form to use for a one-shot batch or a smoke test.

### k3s on the GPU host

The image store lives under the k3s data directory, and a CUDA torch image is several GB. On a host whose root filesystem is nearly full, put it somewhere with room:

```bash
curl -sfL https://get.k3s.io | sh -s - server --data-dir /storage/k3s
```

Then install the NVIDIA device plugin, which is what makes `nvidia.com/gpu` schedulable. k3s's containerd detects the nvidia runtime when `nvidia-container-toolkit` is already installed on the host. Verify before deploying the GPU pool:

```bash
kubectl get nodes -o jsonpath='{.items[*].status.allocatable.nvidia\.com/gpu}'
```

A pod requesting `nvidia.com/gpu: 1` stays Pending forever if that comes back empty.

## Documents not in this release

The public repository ships code, `README.md`, and `CLAUDE.md`. The design and evaluation documents this manual and the [Cookbook](cookbook.md) cite are being refined for publication and land separately, as does the BEIR harness that produces the retrieval-quality numbers. Source comments citing `INGEST_SPEC.md`, `OFFICE_SPEC.md`, `CORPUS.md`, `KNOWN-DEFECTS.md` and `ROADMAP.md` point at those pending documents.

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

Two gaps specific to the container story, stated so they are not discovered in a runbook:

- **No runner Deployment ships.** The thin worker works and is covered by tests; the Kubernetes half of that arrangement is not written.
- **The CUDA worker image has no measured size.** The CPU and thin variants were built and measured; the `cu126` one was not, and no number is guessed for it here.

## LLM-backed features are optional, and JMFTS does not host one

RAPTOR summarization, fact extraction, and read-side synthesis (`/search/synthesize`) all call out to one OpenAI-compatible endpoint — `JMFTS_LLM_BASE_URL` / `JMFTS_LLM_MODEL` — and there is no second endpoint for the extraction path; `JMFTS_EXTRACTION_*` tunes that request, not its destination. Without one configured, those endpoints report a degraded response rather than failing outright — documents, embeddings, chunking, indexing, and every search method work regardless.

One sharp edge in the defaults: leaving `JMFTS_LLM_*` blank does not mean "no LLM". Each blank field falls through to its `JMFTS_ENSONET_*` counterpart, which points at `http://localhost:8853` — the maintainer's own model orchestrator. On any other host that address is simply not listening, which is why the degraded path is what you see; set `JMFTS_LLM_BASE_URL` explicitly rather than relying on the fallback to be absent.

The deliberate design choice, as of a 2026-07-23 decision: **JMFTS does not reserve a GPU or pin a local model of its own.** It is a client of whatever LLM the calling agent is already using. If you are integrating JMFTS behind an agent that has its own model endpoint, point these settings at that endpoint rather than standing up a separate one for JMFTS.

Note the asymmetry with embedding, which is the one place JMFTS *does* own a model: the embedding model is a JMFTS decision, so JMFTS ships a way to share it (`/runner`). The completion model is somebody else's, so JMFTS ships a way to point at it and nothing more.
