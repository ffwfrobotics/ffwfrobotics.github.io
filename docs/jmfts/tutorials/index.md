---
title: "Tutorials"
category: "tutorials"
status: "draft"
---

# JMFTS — Tutorials

<p class="axis">Action × Acquisition</p>

Guided builds for JMFTS, from a first index to a tuned hybrid query.

Tutorials are read in order. The [quickstart](quickstart.md) is the
first one — it gets something running so the rest have somewhere to
start from.

1. **[Quickstart](quickstart.md)** — stand the appliance up, put three documents in it,
   and run vector, BM25 and hybrid queries over them. Teaches what the tree is for and
   why only one of those three scores can be thresholded.
2. **[Ingest a document](ingest-a-document.md)** — upload a real file and watch a queue
   turn it into a tree. Teaches that ingestion is asynchronous, what `settled` means, the
   three ways to see a pipeline's plan before running it, and what deduplication does to
   an upload you thought was new. Needs 0.1.1 or later.
3. **[See a result on the page](see-a-result-on-the-page.md)** — the same shape in the
   browser: drop a file, read the plan before it runs, search seven ways at once, and click
   a hit to see the page with the answer boxed on it. Teaches what an anchor is, why a
   `.docx` has two of them, and how to check that the page is not doing anything the API
   did not do. Needs 0.6.0 or later.

All three were last checked against 0.8.0, where the appliance needs `JMFTS_API_TOKEN` set before it starts.

The third one stands on its own — it needs nothing from the first two, and it is the
shortest way to see what the appliance does. Take it first if you would rather look than
type.

Once these are done, the [Cookbook](../cookbook.md) is the place to go for one specific
job — customizing chunking, choosing a summarization model, adding your own task type,
or routing work to a GPU pool.
