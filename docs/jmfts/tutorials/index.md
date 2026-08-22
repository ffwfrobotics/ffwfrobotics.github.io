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

Once both are done, the [Cookbook](../cookbook.md) is the place to go for one specific
job — customizing chunking, choosing a summarization model, adding your own task type,
or routing work to a GPU pool.
