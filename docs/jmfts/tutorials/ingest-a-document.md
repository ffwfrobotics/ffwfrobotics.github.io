---
title: "Ingest a document"
---

# JMFTS — Ingest a document

<p class="axis">Action × Acquisition</p>

Upload a real file and watch a queue turn it into a tree.

The [quickstart](quickstart.md) had you write documents by hand, one JSON body at a time. That is not how a corpus arrives. This tutorial uploads a file and follows what happens to it — which is the part that surprises people, because almost none of it happens while you wait.

!!! warning "This needs the branch, not the release"
    The queued ingestion path is on `feat/ingest-lifecycle` and is not in 0.1.0:

    ```bash
    git clone https://github.com/jmccardle/jmfts.git
    cd jmfts && git checkout feat/ingest-lifecycle
    docker compose up --build -d
    ```

    If you already have a 0.1.0 database, apply `migrations/010`, `011` and `012` in order.

As before:

```bash
export TOKEN=jmfts-dev-local
export API=http://localhost:8100
```

## 1. Ask what would happen, before it happens

Start with the question no other retrieval system will answer: *what would you do to this file?*

```bash
curl -sX POST "$API/ingest/explain" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"format": "text"}'
```

!!! warning "`format` is a detector name, not a pipeline name and not a file extension"
    Pass the short name `probe` would report: `text`, `pdf`, `docx`, `pptx`, `zip`. Markdown
    is **not** one of them. Nothing in the bytes separates authored markdown from a `.txt`
    file that opens with a `#`, so the detector reports both as `text` and one entry covers
    them.

    The trap is that `markdown` *is* a valid name somewhere else — it is a pipeline on the
    older synchronous `POST /ingest`. Send it here and the request succeeds, because an
    unknown format is a legal question. The answer is a plan in which every row is
    `impossible` or `not_applicable`, which reads like "markdown is unsupported" and is
    really "no such format".

The response is the task plan, read out of the same declaration the scheduler works from — so the plan cannot drift from the run without the run changing too:

```json
{"format": "text", "prober_available": true,
 "patterns_known": false, "patterns_source": "unknown", "patterns_ignored": [],
 "options": {"structure": {"chunk_strategy": "sentence_packed", "max_tokens": 120,
                           "min_chunk_length": 20},
             "rollup": {"max_children": 16, "penalty": 1.0, "min_segment": 3,
                        "llm_model": ""}},
 "tasks": [
   {"task": "probe", "outcome": "enqueued", "write_mode": "self",
    "requires": [], "forbids": []},
   {"task": "extract:text", "outcome": "conditional", "if_condition_holds": "enqueued",
    "write_mode": "self", "requires": ["has_text_layer"], "forbids": ["has_markup"]},
   {"task": "structure:declared", "outcome": "conditional", "if_condition_holds": "enqueued",
    "write_mode": "children", "after": ["extract:text"],
    "requires": ["has_text_layer", "has_headings"], "forbids": []},
   {"task": "structure:inferred", "outcome": "conditional", "if_condition_holds": "enqueued",
    "write_mode": "children", "after": ["extract:text"],
    "requires": ["has_text_layer"], "forbids": ["has_headings"]}
 ]}
```

Read `patterns_source` first. It says `unknown`, and `patterns_known` is `false`: this format has a prober, nobody supplied any measurements, and so most rows came back `conditional`. That is the honest answer to a question asked without a file. Each conditional row names the patterns that would decide it — `structure:declared` needs `has_headings`, `structure:inferred` refuses it — rather than guessing, because a plan resting on a fabricated input is a wrong answer wearing a confident shape.

### Three ways to ask, not two

There are two ways to make those rows concrete. The first supplies the patterns as a **hypothesis** — still no file:

```bash
curl -sX POST "$API/ingest/explain" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"format": "text", "patterns": {"has_text_layer": true, "has_headings": true}}'
```

Now `patterns_source` reads `supplied`, `patterns_known` is `true`, and every row is decided: `extract:text` and `structure:declared` are `enqueued`, `structure:inferred` is `not_applicable` because it forbids the heading pattern the other one requires. This is how you ask "what happens to a scanned PDF" without owning one. A key no condition consults comes back in `patterns_ignored` instead of being rejected, which is what makes a misspelled pattern visible rather than silently planned as false.

The second gives it the actual bytes:

```bash
curl -sX POST "$API/ingest/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@README.md"
```

`analyze` runs the same two pure functions `probe` runs, hands the result to the same planner, and **stores nothing**. Nothing is created, nothing is enqueued. Its plan reads `patterns_source: "probed"` — measured, not assumed — and it wraps the plan in three things `explain` cannot know:

- `file` — what the bytes are, beside what your client claimed they were. `mime_agrees` is `null` rather than `false` when one side is unknown, because "they disagree" and "we cannot compare" are different answers.
- `probe_failed` — set when `probe` would raise. Check it **first**: `plan` is then `null`, and that null means "these bytes have no schedule", not "there is nothing to do".
- `already_stored` — set when this appliance already holds these bytes. An upload would resolve to that node and run no plan at all.

So: `explain` for a format, `explain` with patterns for a hypothesis, `analyze` for a file. This is the endpoint set to reach for when a file is behaving unexpectedly.

!!! note "The plan is the downward pass only"
    Every row above builds the tree on the way down. The rungs that run on the way back
    up — `summarize`, `summarize:llm`, `structure:semantic` — are **not** in the plan and
    never will be. Nothing can schedule them from a format name: they are decided by the
    settling walk, which re-reads the tree after the children exist, because a node's
    rollup depends on children that do not exist yet when `probe` runs.

## 2. Upload it

```bash
curl -sX POST "$API/ingest/file" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@README.md"
```

Note the returned document id as `$DOC`.

Read the response carefully: it comes back almost immediately, and it does **not** mean your document is ingested. It means the bytes are stored and one `probe` task is queued. A worker does everything after that.

Uploading the same bytes twice gives you one file record, not two — the path is idempotent on content, and `was_existing: true` in the response says which happened. Three consequences of that are worth learning now rather than from a confusing result later.

**Re-uploading with different options is refused.** The existing node records the options it was ingested with. An upload asking for anything else gets a 400 naming both sets, because the alternative — returning the node as though your new `max_tokens` had been applied — is a quiet wrong answer. Changing how an already-ingested file was processed has no path today; see [step 6](#6-when-something-goes-wrong).

**Uploading into a folder links, it does not copy — or reparent.** Pass `parent_id` for bytes that are already stored and the existing node is attached to that parent by a `contains` graph edge, with `linked_into_parent: true` in the response. Its `parent_id` is unchanged, so `GET /documents/{parent}/subtree` **does not reach it** and `GET /documents/{parent}/links` does. That is the honest cost of placing a file in two trees without duplicating its bytes, and it is worth knowing before an apparently empty folder listing sends you looking for a bug.

**An upload with no `parent_id` is governed by nothing.** Subtree RBAC works strictly on the tree path, so a node with no ancestor sits under no access-control root — and a grant made later cannot reach back and cover it. Both fixes are available only at upload time: give it a `parent_id` inside a subtree that is already governed, or pass `?private=true` to make the new node its own access-control root with you as its only grantee. The open default is deliberate — a token means the shared knowledgebase — but this is the one gap it leaves.

## 3. Watch the frontier

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/ingest/file/$DOC/frontier"
```

```json
{"document_id": 41, "settled": "in_flight", "nodes_total": 9,
 "nodes_settled": 6, "nodes_in_flight": 3, "nodes_failed": 0,
 "tasks_unfinished": 4}
```

Run it a few times. Nodes move from `in_flight` to `settled` as the tree is built from the top down and then rolled back up.

Notice what this endpoint does **not** return: a percentage. The task set below the current frontier does not exist until the frontier reaches it — the pipeline discovers work as it goes — so any denominator would move backward while you watched it. Counts are the honest answer.

`tasks_unfinished` counts the queued tasks under this root that still owe work — `pending`, `claimed`, `running`, or failed-but-retryable. It is there for one specific reading: **zero unfinished tasks while `nodes_in_flight` is above zero** means the frontier is waiting on something that is not in the queue. Nothing is going to arrive and finish those nodes.

Be careful about what the other readings do *not* tell you. A non-zero `tasks_unfinished` says work is queued; it does not say anything is running it. Tasks that sit `pending` forever — the shape a badge with no matching worker produces — count exactly the same as tasks a worker is draining right now. Two readings a minute apart distinguish them and one reading never does: if the counts have not moved, nothing is working.

When `settled` reads `settled`, ingestion is done. If it reads `failed`, one of its tasks failed permanently, and that is deliberately visible rather than silent.

## 4. Look at what you got

```bash
curl -s -H "Authorization: Bearer $TOKEN" "$API/documents/$DOC/subtree"
```

The file became a tree: a `file` node at the top, section nodes under it following the document's own headings, and chunk nodes under those. That shape came from `structure:declared` — the rung that builds the tree the document *declares*. A document that declares no structure gets `structure:inferred` instead, which chunks it.

Look at a container node's `structured_content`:

```json
{"effective_content": {"method": "concatenated", "source_children": 4,
                       "tokens": 812, "window": 8192, "characters": 4103}}
```

That is a container's answer to "what do you say?". It has no `content` of its own — the prose lives in its leaves, and putting it on the container too would enter the same text into the indexes twice. So instead it gets an embedding derived from its children, and a record of how.

`method` is the thing to read. `concatenated` means the children's text fit the embedding window and was used verbatim. `llm_summary` means it did not fit and a model paraphrased it. The first is a stronger record of what the document said; the deciding token count is recorded either way so you never have to infer which happened from the text.

## 5. Search it

Now the tree is `settled`, it is searchable:

```bash
curl -sX POST "$API/search/vector" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"query\": \"how do I run the tests\", \"parent_id\": $DOC, \"limit\": 5}"
```

Try that same query *before* a document finishes and you get nothing back. The retrieval indexes are partial on `settled`, so an unfinished tree is invisible. That is intended — a half-built tree should not answer queries — but it means "no results" and "still ingesting" look identical from outside. The frontier endpoint is how you tell them apart.

## 6. When something goes wrong

Two limits are worth knowing before you need them, because neither is obvious from the endpoints you have used so far.

**There is no API for the queue.** No endpoint lists task rows, shows you which one failed, or retries one. What you get is the frontier's counts and, if the appliance is yours, SQL against `task_queue`. For a corpus rather than a single file, `scripts/e2e_ingest_corpus.py report` is the tool that answers it — it lists every failed task with its error type, alongside what the trees became and what each task type cost.

**There is no re-ingest.** A file is processed once, with the options it was uploaded under. Changing those options for a file already in the appliance is specified — it diffs `(task, param_fingerprint)` against the node's attempt log and enqueues only the difference — and **not built**. Until it is, the only way to reprocess a document under new options is to delete it and upload it again.

So decide options before the upload, not after, and use `analyze` to check a file that is behaving strangely rather than uploading it to find out.

## What you learned

- **Ingestion is asynchronous.** A 200 from the upload means accepted, not ingested.
- **The plan is inspectable before it runs.** `explain` from a format name, `explain` with `patterns` from a hypothesis, `analyze` from real bytes — none of the three storing anything.
- **The plan covers the way down.** Rollup rungs are decided later, by a walk that re-reads the tree.
- **`settled` gates retrieval.** Unfinished documents are invisible on purpose.
- **A container's embedding is derived and labelled.** `effective_content.method` says whether you are searching the document's own words or a paraphrase of them.
- **Uploads deduplicate on content**, which makes placement a link rather than a copy, makes conflicting options a refusal, and makes options a decision you take before uploading.

## Next

- **Change what the pipeline does.** [Chunking per request](../cookbook.md#change-chunking-for-one-request) and [a different summarization model](../cookbook.md#use-a-different-llm-for-summaries-than-for-everything-else) are both one options key — read the chunking recipe's caveat before trying it on a file you have already uploaded.
- **Do a whole directory.** [`e2e_ingest_corpus.py`](../cookbook.md#ingest-a-directory-and-watch-it-finish) handles the upload/wait/index phases and reports what happened, including every failed task.
- **File the same document in two places.** [Placement is a link](../cookbook.md#place-a-file-in-a-folder-without-copying-it), which a subtree walk will not show you.
- **Control who sees an upload.** [`private=true` and the ungoverned-node gap](../cookbook.md#keep-an-upload-out-of-the-shared-knowledgebase) — a decision you can only make at upload time.
- **Add your own step.** [Register a task handler](../cookbook.md#add-your-own-ingest-task) to put your own work in the pipeline.
- **Scale it out.** The [DevOps Manual](../devops.md#ingestion-runs-on-a-queue) covers running workers as their own processes, the heartbeat lease, routing work to pools by badge, and [what you can monitor](../devops.md#what-you-cannot-see-and-what-to-monitor-instead) given there is no queue API.
