---
title: "See a result on the page"
---

# JMFTS — See a result on the page

<p class="axis">Action × Acquisition</p>

Drag a PDF in, search it, click a result, and see the page with the answer boxed on it.

That sentence is the whole of 0.6.0's front end, and running it end to end takes about ten
minutes once the appliance is up. You will watch an ingest plan *before* it runs, watch the
queue settle the document, run one query down seven columns at once, and finish on a page
that shows you where the answer physically sits.

!!! note "Needs 0.6.0 or later"
    The front end is a separate distribution, `jmfts-web`, and `jmfts[web]` is what pulls it
    in. An appliance without it starts normally and serves no `/app`.

The [Quickstart](quickstart.md) does the same corpus by hand with `curl`. Do that one if you
want to know what the calls are; do this one if you want to see what they are *for*. Neither
depends on the other.

## 1. Get an appliance with a face

From a checkout, the dev stack carries the front end:

```bash
git clone https://github.com/jmccardle/jmfts.git
cd jmfts && docker compose up --build -d
docker compose logs -f api
```

Set `JMFTS_API_TOKEN` first (`export JMFTS_API_TOKEN="$(openssl rand -base64 32)"`); since 0.8.0 compose stops without it, and you will paste the same value into the page in step 2.

If you already have JMFTS running some other way, add the front end to it:

```bash
pip install 'jmfts[web]'
```

And from nothing, without Docker:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install 'jmfts[embed,web]'
export JMFTS_API_TOKEN="$(openssl rand -base64 32)"
jmfts-init-db
uvicorn jmfts_core.rest.main:app --host 0.0.0.0 --port 8100
```

`[embed]` is the model stack, and it is separate for a reason worth knowing: base JMFTS
carries no torch, because a storage worker can ask another appliance for
vectors. The machine serving `/search` embeds its queries locally whatever else is
configured, so it needs the model.

Then open:

```
http://localhost:8100/app/
```

## 2. Connect

There is one field at the top of the shell and it wants your `JMFTS_API_TOKEN`. Paste it and
press **Connect**.

The status line then says `connected — this browser keeps the token until you press Forget`,
and it means the browser, not the tab: open a second tab on the same appliance and it is
already signed in. **Forget** is the counterweight — it signs out every tab at once.

Nothing but `/health` works without a token, so if the views look broken, look at that line
first.

## 3. Drop a file, and read what *would* happen

Go to **Ingest**. Drop a PDF onto the panel.

Nothing has been stored. Dropping a file analyses it: probe runs over the bytes, and the page
fills a section headed **What would happen** — which carries the reassurance in its subtitle,
*Nothing below has been stored.*

Three things to read there:

- **The format, and what recognised it.** Not the file extension — what the bytes say.
- **The patterns.** What probe measured in the file: a text layer, tables, declared
  structure. Some are listed as known and unused, which is the appliance telling you it saw
  something it has no rung for.
- **The plan, with a cost.** One row per task: the task type, the scope it runs at, whether
  it is conditional and on what. Since 0.6.0 each row also carries counts — tasks, child
  nodes, embeddings, LLM calls.

Those counts are **intervals**, not numbers, and some of them have an open top. A fan-out
task declares a bound rather than a count, and `EXPLAIN` has not been given the bytes, so
"between 1 and 40 profile tasks" is the honest answer and `40` would not be. Anything that
could not be counted at all is named in `unmeasured` with the reason. This is the appliance
refusing to guess at you.

## 4. Ingest it, and watch the frontier

Press **Ingest**. Now it is stored, and the queue has work.

The panel switches to the settling frontier and polls it. Five numbers, and they are worth
understanding because they are the appliance's own lifecycle:

| Number | What it counts |
|---|---|
| `nodes_total` | Everything created under this upload so far |
| `nodes_settled` | Nodes whose whole subtree has finished |
| `nodes_in_flight` | Nodes still being worked on |
| `nodes_failed` | Nodes a task gave up on |
| `tasks_unfinished` | Queue items not yet drained |

**An in-flight node is invisible to search.** Every retrieval index is partial on `settled`,
which is why the page waits for the root to settle before it calls the ingest done rather
than reporting success the moment the upload returned.

If `nodes_total` keeps climbing, that is the tree being built — a PDF becomes a file node,
then sections, then chunks, each of which is a row.

## 5. One query, seven columns

Go to **Search** and type a question about something in the document.

The page runs it seven ways at once and puts the answers side by side:

| Column | What it is |
|---|---|
| `vector` | HNSW cosine over the 768-dim document embedding |
| `fulltext` | PostgreSQL `ts_vector`, with a trigram fallback |
| `bm25` | The inverted index, `k1`/`b` tuned |
| `maxsim` | Late interaction over the per-token 256-dim vectors |
| `hybrid` | Reciprocal Rank Fusion over the first two |
| `auto` | A router reads the query, picks one method, and says why |
| `quick (GET)` | The same algorithms in a URL |

This is the shortest explanation of the appliance there is. Try a question phrased in words
that are not in the document — `vector` and `maxsim` will find it and `bm25` will not. Then
try an exact string, a surname or a part number, and watch that reverse.

Read the `applied` block under `hybrid`. The page deliberately does not tell the server which
methods to fuse; it omits `methods` and lets the tuned default resolve, and `applied` reports
what that came out as. A page that named a default would be a second copy of it, and would be
wrong the day the default moved.

!!! warning "The hybrid score is not a similarity"
    Fusion is by **rank**: each leg contributes `weight/(60+rank)`. The number says where a
    result placed, not how close it was. **Rank with `hybrid`, threshold with `vector`.**

## 6. Click a hit

Click a result. You land on **Document**, on the node that matched — and if the appliance can
draw it, the page is rendered with a box around the passage.

The box comes from the hit itself. A search result carries its anchor, so the page needs no
extra call per hit to know where to draw: `{"kind": "pdf", "page": 3, "bbox": [...]}` in PDF
points, drawn by one overlay component that every surface shares.

For a `.docx` or `.pptx` there are **two** anchors and the page says which it is showing:

- **`source_anchor`** is the document's own address — an element of the uploaded package. It
  is exact, and it cannot be drawn.
- **`render_anchor`** is a rectangle found in the PDF LibreOffice paginated. It can be drawn,
  and it can be wrong: another version of LibreOffice may put the passage on a different
  page.

The page's own sentence for that case is the rule worth keeping: **cite the address; look at
the rectangle.**

When there is no box, the page tells you which of four reasons it is — the passage has an
exact address and nothing has paginated the document; a rendition exists and the passage was
not found in it, with the reason; and so on. "No highlight" and "the highlight could not be
recovered" are different answers, and only one of them is a problem.

## 7. Check that the page is thin

Go to **Call log**.

Every request any view made is there: operation id, method, resolved path, params, body,
status, elapsed milliseconds. Three things you can do with it, and the third is the reason it
exists:

1. **Replay** an event with edited arguments, and see the response render properly rather
   than as a blob.
2. **Audit the page.** Anything a view showed that has no call behind it was computed in the
   browser. You can see that here rather than take it on trust.
3. **Copy out.** Any event prints as `curl`, as a `RemoteJmftsClient` call, or as `fetch` —
   and none of the three prints your token. Each names the environment variable it lives in.

Point 3 is how this tutorial connects to the [Quickstart](quickstart.md): run something on
the page, copy it out as `curl`, and you have the hand-written form of the thing you just
clicked.

## What you have

One document, ingested with its plan shown first, searched seven ways, and a rectangle on a
page. The whole front end is ES modules over the same REST API any other client calls —
nothing loads from a CDN or a font host, because an appliance is expected to run air-gapped.

## Next

- **Save what you just ran.** The **Presets** view stores a search configuration as a search
  context and runs it again later.
- **Ask the appliance what it is.** **This appliance** is `GET /capabilities` — which extras
  are installed, whether it can embed at all, which formats it identifies, which methods will
  actually return something here.
- **Do it by hand.** The [Quickstart](quickstart.md) builds a small corpus with `curl` and
  explains what each call is doing.
- **Put a real corpus in.** [Ingest a document](ingest-a-document.md) covers the queue, the
  task types, and where a rung records what it did.
