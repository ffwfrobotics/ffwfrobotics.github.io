---
title: "Quickstart"
---

# JMFTS — Quickstart

<p class="axis">Action × Acquisition</p>

Index a small corpus and run your first hybrid query.

You will stand up the appliance, put three documents in it, search them by meaning, add a BM25 index, and then run the hybrid query that uses both. Most of the time is the embedding model downloading.

Everything here is in the public [0.1.0 release](https://github.com/jmccardle/jmfts/releases/tag/0.1.0). Nothing on this page needs a branch.

## 1. Start it

```bash
git clone https://github.com/jmccardle/jmfts.git
cd jmfts
docker compose up --build -d
docker compose logs -f api
```

The first build downloads a CPU build of torch, and the first request downloads `nomic-ai/modernbert-embed-base` — a few hundred MB, cached in a volume so it only happens once.

The Compose file pins the API token to `jmfts-dev-local` so a local client can use a known value. Export it and the API root:

```bash
export TOKEN=jmfts-dev-local
export API=http://localhost:8100
```

Every request needs `Authorization: Bearer $TOKEN`. There is no mode where a blank token means "allow all" — if you had not pinned one, the server would have generated one and printed it to the log you just tailed.

## 2. Put something in it

Documents form a tree. Make a parent so you have something to scope searches to:

```bash
curl -sX POST "$API/documents" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title": "Notes", "usetype": "markdown"}'
```

Keep the `id` it returns as `$ROOT`, then add three children:

```bash
for t in \
  "Cosine similarity measures the angle between two vectors, ignoring magnitude." \
  "BM25 scores a document by term frequency, saturating so repeated words stop helping." \
  "The kettle needs descaling again and the good mugs are in the dishwasher."
do
  curl -sX POST "$API/documents" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "{\"parent_id\": $ROOT, \"content\": \"$t\", \"usetype\": \"markdown\"}"
done
```

`auto_embed` defaults to true, so each document was embedded as it was created — a 768-dim document vector plus per-token vectors for late interaction. That is why creates are slower than they look: embedding is roughly 100× the cost of the database write itself.

## 3. Search by meaning

Vector search needs no index. It reads the vectors that were written on create:

```bash
curl -sX POST "$API/search/vector" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"query\": \"how is relevance scored\", \"parent_id\": $ROOT, \"limit\": 3}"
```

The two retrieval sentences come back ahead of the kettle, and none of the query's words appear in either. Look at the scores, not just the order: cosine similarity **separates**, so the relevant hits sit meaningfully above the irrelevant one. That property matters in step 5.

## 4. Add the keyword leg

BM25 needs an inverted index, and an index needs to know which subtree it covers:

```bash
curl -sX POST "$API/indexes" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "notes", "description": "quickstart corpus"}'

curl -sX POST "$API/indexes/notes/roots" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"root_document_id\": $ROOT}"
```

Then index each document you created:

```bash
curl -sX POST "$API/indexes/notes/index-document/$DOC_ID" \
  -H "Authorization: Bearer $TOKEN"
```

This is idempotent — indexing a document twice subtracts its old contribution before adding the new one, so the corpus statistics BM25's IDF is derived from do not inflate. Index incrementally as content arrives. `POST /indexes/notes/refresh` rebuilds from scratch and costs time proportional to the whole corpus, so reach for it as a repair tool rather than a routine one.

Now a keyword query that vector search alone would do poorly on:

```bash
curl -sX POST "$API/search/bm25" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"query": "BM25", "index_name": "notes", "limit": 3}'
```

## 5. Run the hybrid query

```bash
curl -sX POST "$API/search/hybrid" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d "{\"query\": \"how is relevance scored\", \"parent_id\": $ROOT,
       \"index_name\": \"notes\", \"weights\": {\"vector\": 0.6, \"bm25\": 0.4}}"
```

Omit `weights` and you get the tuned 0.86/0.14 default. Pass an explicit `{}` for equal-weight RRF.

!!! warning "The hybrid score is not a similarity"
    Hybrid fuses by **rank**: each leg contributes `weight/(60+rank)`. The number that comes back says where a result placed, not how similar it was. Measured against a real store, a relevant query and a nonsense query returned the same five score values.

    So: **rank with `hybrid`, threshold with `vector`.** If anything downstream has to *decide* something from a score — inject this context or stay silent, keep this result or drop it — `vector` is the only method that answers.

## What you have

Three documents, two ways to search them, and one fused query. The tree is what makes `parent_id` a scope rather than a filter, so one appliance can hold several corpora and a search can name one.

## Next

- **Get a real corpus in.** [Ingest a directory](../cookbook.md#ingest-a-directory-and-watch-it-finish) — files rather than hand-written JSON, with a queue doing the tree-building. That path is on a branch, not in 0.1.0.
- **Tune what you just ran.** The [Cookbook](../cookbook.md#tune-the-hybrid-weight-to-the-corpus-dont-assume-one-number) has measured hybrid weightings per dataset, and why one global number does not hold.
- **Add reranking.** `?rerank=true` adds a second stage; the [Cookbook](../cookbook.md#pick-a-rerank-method-by-what-your-corpus-already-stores) explains why the choice is about prerequisites rather than quality.
- **Run it properly.** The [DevOps Manual](../devops.md) covers auth, the embedding device, and why bulk loading stays CPU-bound until you move it to CUDA.
