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

The recipes above tune the retrieval stack. The next block is the write side — getting a corpus in, and changing what happens to it on the way.

!!! warning "Ingestion is ahead of the release"
    Every recipe in this block needs the `feat/ingest-lifecycle` branch. None of it is in 0.1.0. See the [Reference](reference.md#ingest-task-queue) for the queue's shape and the [DevOps Manual](devops.md#ingestion-runs-on-a-queue) for how to run workers.

## Ingest a directory and watch it finish

`POST /ingest/file` returns as soon as the bytes are stored, so a naive loop over a directory reports success long before anything is searchable. `scripts/e2e_ingest_corpus.py` is the tool that does this correctly, and its phases are separate subcommands because the middle one takes hours:

```bash
python -m scripts.e2e_ingest_corpus upload --state run.json ~/corpus
python -m scripts.e2e_ingest_corpus wait   --state run.json
python -m scripts.e2e_ingest_corpus index  --state run.json
python -m scripts.e2e_ingest_corpus report --state run.json
```

`report` answers four questions and keeps them apart: did every file finish (counts by lifecycle state, plus every failed task with its error type), what did the tree become (nodes by usetype and depth), is it retrievable (document vectors, token embeddings, BM25 entries, and the same query through each search method), and what did it cost (wall clock per task type).

Nothing in it is a fixture — the corpus is whatever directory you name and the report says what happened rather than asserting it matched an expectation. That is the point: run it against your own awkward files before trusting a pipeline on them.

For a single file, `POST /ingest/file` then poll:

```bash
curl -H "Authorization: Bearer $TOKEN" \
     "$API/ingest/file/$DOC_ID/frontier"
# {"document_id": 41, "settled": "in_flight", "nodes_total": 15,
#  "nodes_settled": 12, "nodes_in_flight": 3, "nodes_failed": 0, "tasks_unfinished": 5}
```

Counts, never a percentage — the work below the current frontier does not exist yet, so any denominator would move backward as it is discovered.

Poll on `tasks_unfinished` reaching zero, not on a timer. Zero unfinished tasks while `nodes_in_flight` is still above zero is the one reading that means *stuck*: nothing queued owes those nodes any work, so nothing is coming to finish them. A non-zero count says work is queued and says nothing about whether anything is running it — tasks that will sit `pending` forever look identical to tasks being drained right now, and only two readings apart in time tell them apart.

## See what a pipeline would do before you run it

Three ways to ask, along one axis: how much does the planner actually know about the file?

**`POST /ingest/explain` with a format name** — no file, and usually a conditional answer:

```json
{"format": "pdf", "options": {"structure": {"max_tokens": 60}}}
```

!!! warning "`format` is a detector name, not a pipeline name"
    Valid values are what `detect_format` produces: `text`, `pdf`, `docx`, `pptx`, `zip`.
    **`markdown` is not one of them** — nothing in the bytes separates authored markdown
    from a `.txt` opening with `#`, so both report as `text`. `markdown` *is* a valid
    pipeline name on the older synchronous `POST /ingest`, which is exactly why the mistake
    is easy. An unknown format is a legal question and answers 200, with every row
    `impossible` or `not_applicable` — which reads like "unsupported" and means "no such
    format".

Rows whose scheduling depends on something only `probe` can measure come back `conditional`, naming the patterns that would decide them and what they would become. Nothing is assumed in either direction — a plan resting on a fabricated input is a wrong answer wearing a confident shape.

**`POST /ingest/explain` with `patterns`** — still no file, but the conditions are now answerable:

```json
{"format": "pdf", "patterns": {"has_text_layer": true, "has_outline": false,
                               "is_scanned": false}}
```

Every row is decided and `patterns_source` reads `supplied`, so nobody can mistake a hypothesis for a measurement. This is how you answer "what would happen to a scanned PDF" or "what changes if this one has no outline" without owning either file — and how you test a routing or options change against shapes your corpus does not contain yet. A key no condition consults is reported in `patterns_ignored` rather than rejected, which is what makes a misspelled pattern visible instead of silently planned as false.

**`POST /ingest/analyze` with the actual file** — runs the two pure functions `probe` runs, hands the result to the same planner, and **stores nothing**:

```bash
curl -sX POST "$API/ingest/analyze" -H "Authorization: Bearer $TOKEN" -F "file=@paper.pdf"
```

`patterns_source` reads `probed`. Three fields wrap the plan that `explain` cannot produce: `file` (what the bytes are beside what your client claimed — a `.docx` that is really a bare ZIP shows up here rather than as an unexplained failure two tasks later), `probe_failed`, and `already_stored`.

Check `probe_failed` **first**. Exactly one of it and `plan` is set, and a null plan means "these bytes have no schedule", not "nothing to do". `already_stored` means the appliance already holds these bytes, so an upload would deduplicate to the named node and run no plan at all — it also carries that node's recorded options, which is the only way to predict the 400 in the next recipe.

All three reject an unknown option with a 400 naming it, from the same resolver the upload uses. Explaining a plan under options the run would refuse would be the exact wrong answer these endpoints exist to prevent.

!!! note "The plan is the downward pass only"
    `probe`, `extract:*`, `ocr` and the two `structure` rungs — the tasks that build the
    tree going down. `summarize`, `summarize:llm` and `structure:semantic` are never in a
    plan: they are scheduled by the settling walk after the children exist, and no function
    of `(format, patterns, options)` could decide them, because the children are what they
    depend on.

## Change chunking for one request

Options are namespaced by **group**, where a group names the parameters one kind of task takes. Pass overrides as a JSON object beside the upload:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
     -F "file=@paper.pdf" \
     -F 'options={"structure": {"max_tokens": 60, "chunk_strategy": "sentence_packed"}}' \
     "$API/ingest/file"
```

The `structure` group is read by both structure rungs; `rollup` is read at the settling boundary. A parameter belongs to the **task** that reads it, not to the format that fed it — which is why chunking parameters are not a property of `pdf`. Formats get to say where they *deviate*, and today none do.

!!! warning "A typo in an option is a 400, not a shrug"
    Write `max_token` instead of `max_tokens` and the request fails naming the key. It is not silently ignored. A run that quietly does something other than what was asked, and reports success, is precisely the swallowed failure this project refuses to ship.

### It works on a new file, not on one you already uploaded

Uploads deduplicate on content hash. Send bytes the appliance already holds and it resolves to the existing node — which recorded the options it was ingested under. **An upload asking for different options is a 400**, naming both sets:

```
Document 41 already holds these exact bytes, ingested with {'structure': {'max_tokens': 120, …}};
this upload asks for {'structure': {'max_tokens': 60, …}}. Uploading does not re-run work that
has already been done …
```

That refusal is the honest answer, not an obstacle to work around. Two answers are available — do the work, or say it was not done — and returning the node as though your `max_tokens` had been applied is the third one.

Reprocessing an already-ingested file under new options is specified (diff `(task_type, param_fingerprint)` against the node's attempt log, enqueue only the difference, no re-parse and no duplicate tree) and **is not built**. Until it is:

1. Settle chunking with `POST /ingest/analyze`, which stores nothing and costs one probe.
2. Upload once the options are what you want.
3. To change them afterwards, delete the document and upload it again.

For a corpus-wide sweep, that means deciding before the run — which is what makes `analyze` on a handful of representative files worth the ten minutes.

## Place a file in a folder without copying it

Pass `parent_id` on an upload and one of two things happens, and the response says which.

For **new bytes**, `parent_id` is ordinary parentage. The file node is a tree child and everything works the way you expect.

For **bytes already stored**, the existing node is attached to that parent by a `contains` **link** — a graph edge — and the response carries `linked_into_parent: true`. Its `parent_id` is unchanged. The consequence is the part to internalize:

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/documents/$FOLDER/subtree"  # does NOT include it
curl -s -H "Authorization: Bearer $TOKEN" "$API/documents/$FOLDER/links"    # does
```

A subtree walk is `path`/`parent_id` containment and this edge is in neither. Any UI that renders a folder from the subtree alone will show an empty folder for a file that is genuinely filed there. Read `linked_into_parent` and query links as well, or accept that a file lives in exactly one tree.

The node is deliberately **not** reparented instead. It is a record someone else created for their own purpose; moving it as a side effect of a third party uploading the same bytes would change what their document sits under and invalidate the rollups above its new parent, silently, in a request that said nothing about moving anything. Adoption is a curator action with its own verb.

## Keep an upload out of the shared knowledgebase

The default is open, and that is the design: a JMFTS token means access to the shared corpus, and an upload lands readable by every principal. "Private until shared" would be the opposite assumption and would breed bugs of ignorance in every deployment that holds the stated one.

The gap that default leaves is narrow and permanent. Subtree RBAC resolves strictly along the tree path — a principal's right on a document is the highest grant on any access-control root at or above it in `path`. So a file uploaded with **no `parent_id`** has no ancestor, therefore no access-control root above it, therefore nothing governs it. **A grant made later cannot reach back and cover it**, because there is no path for the grant to travel down.

Both fixes exist only at upload time:

```bash
# Either: land it inside a subtree that is already governed.
curl -sX POST "$API/ingest/file?parent_id=$GOVERNED" \
     -H "Authorization: Bearer $TOKEN" -F "file=@salary-review.pdf"

# Or: make the new node its own access-control root, with you as its only grantee.
curl -sX POST "$API/ingest/file?private=true" \
     -H "Authorization: Bearer $TOKEN" -F "file=@salary-review.pdf"
```

`private=true` grants you `write`, not `read` — you own what you uploaded and must be able to correct it.

!!! warning "`private=true` narrows deduplication, and it has to"
    The ordinary dedupe lookup matches any file node the caller can *read*, and an
    ungoverned node is readable by everyone. Under `private=true` the lookup is restricted
    to nodes you hold a grant on. Without that, a private upload of bytes already present
    as a shared node would resolve to the shared node and you would not be private at all.
    The cost is a second copy of the bytes when the same file exists in both forms.

Note that `private` and `parent_id` are **query** parameters while `options` is a form field. The bytes make the body multipart, so scalars land in the query string and only the structured parameter becomes a part.

## Use a different LLM for summaries than for everything else

Summarization is the only ingest step that always costs a model call, and it is the one you are most likely to want a different model for — a cheap one for bulk backfill, a strong one for the documents people actually read.

It is one option key:

```json
{"options": {"rollup": {"llm_model": "qwen2.5:7b-instruct"}}}
```

That value rides on the task row into `summarize:llm`, which prefers it over `JMFTS_LLM_MODEL`. Empty means "use the configured default". The **endpoint** is still global (`JMFTS_LLM_BASE_URL`) — this selects a model at that endpoint, not a different provider.

Two knobs pair with it. `max_children` (default 16) decides when a node is segmented instead of summarized, so raising it means fewer, longer summaries and lowering it means more, shorter ones. `penalty` and `min_segment` tune the PELT segmentation that produces those groups.

Remember what `summarize` actually does: it concatenates its children's text while that fits the embedding window and only calls a model when it does not. A concatenated span is a stronger record of what the document said than any paraphrase, and the deciding token count is recorded either way — so `structured_content.effective_content.method` tells you which happened without inferring it from the text.

## Add your own ingest task

A task type is a string, a handler, and a declaration of what it reserves.

```python
from jmfts_core.ingest_tasks import TaskOutcome, register_task_handler

@register_task_handler("classify:sensitivity")
def run_classify(session, task) -> TaskOutcome:
    node = session.get(Document, task.scope_document_id)
    label = my_classifier(node.content)
    node.structured_content = {**(node.structured_content or {}), "sensitivity": label}
    return TaskOutcome(detail={"label": label})
```

Four rules the contract enforces, all of them worth knowing before you write the handler:

1. **The session is the worker's**, one per task. Write what the task writes and return; the worker commits, or rolls back and records the failure.
2. **A handler that failed raises.** It does not return a status saying so. The worker has to classify the exception to decide about a retry, and a returned string carries no exception to classify.
3. **`status="skipped"` is for work that was never attempted**, and it requires `detail["reason"]`. A missing result is never silent.
4. **Registering two different functions under one name is an error**, not last-import-wins.

Declare a `write_mode` when you enqueue: `self` if the task writes only its own node, `children` if it writes the node's children, `subtree` if it rewrites the region. The claim query uses it to refuse overlapping work, so a task that lies about its scope is how two workers end up writing the same node.

If your task takes parameters, give it a group in `TASK_PARAM_DEFAULTS` rather than reading settings directly — that is what makes it visible to `explain`, overridable per request, and part of the re-run fingerprint.

## Route expensive tasks to the hardware that suits them

Two settings and one measurement.

The measurement first, because the policy should follow it: on a real corpus, `structure:declared` and `summarize` are 54% and 46% of ingest wall clock, and `probe` + `extract:text` together are 0.07%. The expensive types are the ones whose handlers run the embedding model.

```bash
# On the appliance: which task types go to which pool.
JMFTS_TASK_BADGES='{"structure:declared":"embed","structure:inferred":"embed","summarize":"embed","summarize:llm":"llm"}'

# On a GPU host: claim the embedding work.
jmfts-worker --badge embed

# On a host with a local model, or a light runner forwarding to a metered API:
jmfts-worker --badge llm
```

A worker takes a **list** of badges, because capability and routing are different things. A host with a local LLM on a GPU can answer both the expensive badge and the cheap one; a runner that only forwards to a web API can answer only the cheap one. Listing both is what lets an otherwise-idle expensive worker fill cycles with bulk work.

!!! warning "Set a badge with no worker and ingestion stalls with no error"
    Tasks sit `pending`, their nodes never leave `in_flight`, they stay out of the retrieval indexes, and nothing reports it. The policy is empty by default for exactly this reason. Turn it on only where every badge it names has a running pool — and give every worker in a fleet a badge, because an un-badged one claims everything including GPU work.

## Halve the LLM bill on a backfill

`summarize:llm` is the one task type that always costs a model call, which makes it the one worth batching. `batch_worker/` routes it through OpenAI's or Anthropic's batch API at roughly half price:

```bash
export OPENAI_API_KEY=...
jmfts-batch-worker run --provider openai --badge llm --model gpt-4o-mini
```

Try it against your own model first — the `mock` provider speaks the same protocol against a local llama-server, and holds a batch open until you finalize it so you can see the parked state:

```bash
jmfts-batch-worker run --provider mock --badge llm \
    --store /var/lib/jmfts/batches --llm-url http://localhost:8080 --once
jmfts-batch-worker status                       # what is parked
jmfts-batch-worker finalize mockbatch_… --store /var/lib/jmfts/batches
jmfts-batch-worker run --provider mock --badge llm --store /var/lib/jmfts/batches --once
```

Two operational facts, both covered in the [DevOps Manual](devops.md#batch-processing-halves-the-llm-bill): a parked batch is invisible to the lease, so `jmfts-batch-worker stalled` is your only stall signal; and gather size is bounded by how much of the tree you are willing to freeze for a day, not by the provider's cap.

!!! note "Set `JMFTS_SUMMARIZATION_DISABLE_THINKING=true` for a reasoning model"
    Measured against llama-server with `Qwen3.8-27B-Q4_0`: without it the model spent its whole token budget on the reasoning trace and returned the fragment `The appliance` as the summary. That fragment is not an error at any layer — it embeds, it stores, and the node ends up advertising an `effective_content` that says nothing.

---

The rest of the page is corpus shapes — jobs the data model already supports that do not follow obviously from "hybrid search over PostgreSQL."

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
