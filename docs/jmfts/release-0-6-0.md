---
title: "0.6.0 — eyes and hands"
---

# JMFTS 0.6.0 — eyes and hands

!!! note "Released 2026-10-12"
    0.6.0 was the current release when this page was written (the current one is 0.8.0; see the [Changelog](changelog.md)): tag [`v0.6.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.6.0), and **three** wheels on PyPI. The third is new — see [The appliance has a face](#1-the-appliance-has-a-face).

**Drag a PDF in, search it, click a result, see the page with the answer boxed on it.** That
is the release, and everything else here is either something that sentence needed or
something that was found by being able to run it.

Until now, every defect in this appliance was found by reading the source, because reading
the source was the only way anybody had ever looked at it. Two access gates did not close.
Three retrieval paths answered with nothing and said nothing about why. None of that was
subtle; it was just never in front of anyone.

## Where this is specified

`docs/SPRINT_0_6_0.md` is in the repository and is the plan this release was built from —
seven blocks, thirty-five steps, with the measurements that chose the scope. It is worth
reading if you want the arguments rather than the outcomes; the front end is Block F.

## 1. The appliance has a face

```bash
pip install 'jmfts[web]'
uvicorn jmfts_core.rest.main:app --host 0.0.0.0 --port 8100
# then open http://localhost:8100/app/
```

Seven views, reachable from the navigation and addressable by URL fragment:

| View | At | What it composes |
|---|---|---|
| Ingest | `#/ingest` | Drop a file, see what *would* happen, then do it and watch it settle |
| Search | `#/search` | The same query down seven columns, side by side |
| Tree | `#/documents` | The corpus as the tree it is stored as |
| Document | `#/document` | One node, rendered, with the box drawn on it |
| Presets | `#/presets` | Search contexts, saved from the browser and run from it |
| This appliance | `#/capabilities` | `GET /capabilities` — extras installed, formats identified, methods available |
| Call log | `#/calls` | Every request the page made, replayable |

An appliance without `jmfts-web` installed starts normally and serves no `/app`. The mount
is conditional on the import succeeding, and it happens after every API route, so a future
endpoint can never be shadowed by a static file.

### The token is a browser fact, not a tab fact

The token goes in one field at the top and stays until you press **Forget**. Forget signs
out every tab on that appliance at once, which is the counterweight to storing it at all.
The status line says which state you are in rather than only whether a value is present.

## 2. Seven columns, one query

The search view runs the same query through every retrieval method the appliance has and
puts the answers next to each other:

| Column | Route | What it is |
|---|---|---|
| `vector` | `POST /search/vector` | HNSW cosine over the 768-dim document embedding |
| `fulltext` | `POST /search/fulltext` | PostgreSQL `ts_vector`, with a trigram fallback |
| `bm25` | `POST /search/bm25` | The inverted index, `k1`/`b` tuned |
| `maxsim` | `POST /search/maxsim` | Late interaction over the per-token 256-dim vectors |
| `hybrid` | `POST /search/hybrid` | Reciprocal Rank Fusion over the first two by default |
| `auto` | `POST /search/auto` | A router reads the query, picks one method, and says why |
| `quick (GET)` | `GET /search/` | The same algorithms in a URL |

This is the demonstration, not a debug affordance. Four columns of the same query is the
shortest explanation of what this appliance is that anybody has written down, and the
[Call log](#3-a-page-that-can-prove-it-is-thin) shows it is four calls and nothing else.

The `hybrid` column deliberately does **not** send `methods`. Omitting it runs the tuned
default, and the `applied` block in the response reports what that resolved to — which is
the honest way to show a default, rather than the page naming one and being wrong later.

## 3. A page that can prove it is thin

Every view talks to the appliance through one generated TypeScript client, and that client
emits one event per call: operation id, method, resolved path, path params, query, body,
status, response, elapsed milliseconds. The Call log is that event stream. Three things
follow.

**Replay.** An event is a call plus its arguments, so it is re-sendable with any of them
edited, and the response renders through the right visualisation instead of as a blob. It is
`/docs`' "Try it out" with the result half fixed.

**Verifiable thinness.** A view that shows something the log has no call for computed it in
the browser. "The front end thinly wraps the API" stops being a claim about the source and
becomes something you can check on the page.

**Copy-out.** Any event prints three ways — `curl`, a `RemoteJmftsClient` call, and `fetch` —
and none of the three prints your token. Each names the environment variable it lives in
instead.

The generated half of the bundle is rendered from the appliance's own `/openapi.json`, the
way `jmfts-client`'s `_verbs.py` is rendered from the route table. A stale file fails the
suite.

!!! note "No build step, no bundler, no CDN"
    The front end is ES modules the browser runs as they stand. Nothing loads from another
    origin — not a script, not a stylesheet, not a font — and a test holds the whole bundle
    to that. An appliance is expected to run air-gapped, and a page that renders blank
    without internet access is worse than no page.

## 4. Three routes that answer with bytes

The beeline needed the appliance to hand over pixels, and no exposed operation could answer
with anything but JSON. `ExposeSpec` grew a response media type; three routes followed.

| Route | Answers with | Notes |
|---|---|---|
| `GET /documents/{id}/blob` | the original upload, unchanged | Served as an **attachment**, under the uploader's own filename |
| `GET /documents/{id}/image` | one page, PNG | `page` is **0-based**; `dpi` defaults to 150 and is bounded |
| `GET /documents/{id}/region` | a rectangle of a page, PNG | From the node's own anchor, or from explicit bounds |

The bytes were always there — stored as Postgres large objects since 0.1.1 — but nothing
under `jmfts_core/rest/` could reach one. All three callers were task handlers.

**`attachment` on `/blob` is the safe disposition, not a preference.** That route serves
uploaded bytes under the uploader's own content type from the appliance's own origin. An
ingested `.html` or `.svg` served `inline` would execute in it.

**`/region` takes one way of naming the rectangle, not two with a precedence rule.**
`anchor=true` asks for the node's own `source_anchor`, which is the form a client has after
a search hit. `page` with `bbox=x0,y0,x1,y1` names an explicit rectangle in PDF points.
Passing both is a 400: there is no way to tell which was meant, and serving the wrong
rectangle confidently is worse than serving none, because the reader cannot tell.

**Omitting `page` on `/image` asks for the page this node is addressed at.** A file node is
the whole document, so that is page 0. Anything else — a chunk, a section — names its page
through its own anchor, and a node with no anchor gets a 409 saying so rather than page 0.

### No `highlight` parameter, deliberately

Burning the rectangle into the PNG would make the page uncacheable per-anchor, make the box
unselectable and undismissable, and give the tree a second place where a rectangle is drawn.
The overlay is one client component that takes an anchor and a rendered surface, and
`pdf-page`, `image` and `sheet-region` all use it. Writing it three times is how three
surfaces end up disagreeing about which corner the origin is in.

## 5. A `.docx` gets a rectangle, and the page says whose page it is

Office parity was the cut line and it landed. A `.docx` or `.pptx` is paginated by
LibreOffice into a stored PDF, and a citation's rectangle is recovered off that.

That makes two anchors on one node, and they are two evidence rows because they are two
facts with different truth conditions:

| Row | What it is | How much to trust it |
|---|---|---|
| `source_anchor` | The document's own address — an `ooxml` element, or a source PDF's own geometry | Exact |
| `render_anchor` | A page and a rectangle recovered from the rendition | Approximate |

A `PdfAnchor` now carries `of`, which is `"source"` or `"rendition"`. It **defaults** to
`"source"`, and that is not laziness: every anchor written before this release is a source
document's own geometry, and a default that says so is the only reading under which an old
row and a new one parse alike.

!!! warning "\"Page 3\" and \"page 3 of our rendering\" are different claims"
    Two LibreOffice versions paginate differently, and the recovery can fail outright — in
    which case there is a `render_anchor.unresolved` row and no anchor at all. A viewer that
    draws the box says which of the two it has. The alternative is a reader opening the
    `.docx` in Word, finding the passage on page 4, and having no way to know why.

### Renditions are on, always, and the policy is eviction

Migration `023` adds `document_renditions`: derived bytes get their own table because the
uploaded ones will not share theirs. `document_blobs.document_id` is UNIQUE, and migration
`009` says why in its own DDL — one blob per document, a second version is a new node. A
rendition is not a second version of the upload; it is derived from it.

The storage argument was measured rather than assumed. On a 2988 MB reference database the
original bytes are 144 MB — 4.8% — so the upper bound, if every stored byte were an office
document with a same-sized rendition, is +4.8%. So renditions are on by default and the
policy for them is **cache eviction** rather than retention: every rendition row can be
deleted and regenerated by re-running `render:pdf`, and no row in `document_blobs` can be
regenerated by anything.

### LibreOffice is a system package, so it is an image

Two new task types, `render:pdf` and `convert:ooxml`, and a third dependency tier to run
them. `jmfts[convert]` is the **client only** — `unoserver` — and `Dockerfile.libreoffice`
builds something for it to talk to. `JMFTS_CONVERT_URL` is how a JMFTS finds one.

**`render:pdf` is advisory, and that is the part the plan got wrong first.** The original
design gated the office anchor on `after render:pdf`, which is a claim on a COMPLETED row of
an advisory task. On an appliance with no LibreOffice — the default — that stalls every
office document short of settling, silently, forever. `anchor:render` is offered at the
settling boundary instead. An appliance with no converter fails the conversion PERMANENTLY
with a message naming the setting and the image that serves one; it never degrades quietly.

## 6. Two access gates that did not close

Both are behaviour breaks and both are the reason this is a minor version.

### An edge takes write on its source

`DocumentRepository.create_link` constructed and flushed a `DocumentLink` with no principal
check of any kind. `DocumentService.create_link` checked only that the body's `source_id`
matched the id in the URL. So a principal with read-only access to a document could attach
edges to it.

The rule is **write on the source, read on the target**, and it now applies to triples too:
five `TripleService` write verbs took a subject document and an object document and gated
neither, while the read side has been gated since 0.5.0. A triple is an edge, so asserting
one takes write on its subject. Seventeen of the twenty-four cases in the new
`tests/test_access_triple_writes.py` failed against the commit before the fix.

### Graph analytics compute over your graph, not the corpus

`GET /graph/centrality`, `/graph/subtree-authority`, `/graph/spines` and `/graph/communities`
took no principal and consulted none. A caller with no grant read back the ids and titles of
documents that are 404 for it everywhere else.

!!! warning "This changes numbers, not just rows"
    There were two possible fixes and they are different products. Filtering the *returned
    ids* leaks nothing but reports numbers derived from rows the caller cannot see. A
    centrality score is a property of the graph it was computed on, so that answer is a
    number about somebody else's corpus.

    The filter went one layer down, into the vertex and title queries, so the graph itself is
    the caller's. A node dropping out also removes its descendants, so `subtree_size` and
    `spread` are computed over the part of the tree the caller can see. **If you run these
    verbs as a principal without full grants, expect different scores than 0.5.1 gave you.**
    They were wrong before.

There is now a standing audit: a test that every `@expose`'d verb is principal-scoped or
explicitly listed. It found eleven more gaps on its first run, and step 35 — the triple
write gate above — was added to the sprint because of it.

## 7. A workbook's rows reach its own index

`index:bm25` named three prose rungs in `after_any` and did not name `structure:sheets`, and
it required a text layer. So a spreadsheet was absent from its own index *and* from
`universal`. On the reference corpus that read as **zero** `index:bm25` tasks anywhere in a
21-workbook subtree, while 4,601 `record` nodes under it carried text averaging 457
characters.

`index:bm25` is now planned at the settling boundary. The entry condition was a test written
first and run against the tree before any fix: ingest one workbook under an indexed folder,
drain the queue, search BM25 for a string that is in a cell.

## 8. `EXPLAIN` says how many, not only which

The ingest plan could list the rungs a format would run and could not say how much work that
was. A forty-sheet workbook's `profile:sheet` read as one task beside `structure:sheets`.

The plan now folds a cost: tasks, child nodes, embeddings and LLM calls. Every accumulator
returns an **interval**, because a fan-out atom declares a bound rather than a number, and
the top of an interval is allowed to be open. `PlanCost.unmeasured` names what could not be
counted and why — an unmeasurable count is reported, never guessed.

This is what the Ingest view's "What would happen" panel displays, and it is why dropping a
file there stores nothing.

## 9. A collection configures what is ingested under it

`GET` and `PUT /documents/{id}/ingest-options` write an options row onto a node, and upload
walks up the ancestors to find one.

**A collection is not a scope a table has to express.** It is a subtree, and a setting on a
node reaches the documents beneath it. So this adds no bindings table and no migration — the
tree is already there, and access control, already subtree-scoped, answers "who may
configure this collection" with "who may write to this node", for free.

## Upgrading

One migration, `023_document_renditions.sql`. It is additive.

```bash
jmfts-init-db --pending     # ask the database which shipped deltas it has not applied
```

That command has existed since 0.5.0, and `schema_migrations` (migration `017`) is what it
reads. If you are coming from 0.3.0 you have `017` through `023` to apply, and `022` swaps
the token index from IVFFlat to HNSW — see the [Changelog](changelog.md#050).

Read [Two access gates that did not close](#6-two-access-gates-that-did-not-close) before
upgrading a multi-principal deployment. Nothing fails at deploy time; calls that used to
succeed start returning 403, which is the point.

## What is not here

- **The specifications are still held back.** `INGEST_SPEC.md`, `SPRINT_JOBS.md` and
  `OFFICE_SPEC.md` are cited by several hundred source comments and are not in the public
  repository yet. `docs/SPRINT_0_6_0.md` is, and so are the generated reference pages.
- **The sprint plans and the archive are staying internal**, and that is now a decision
  rather than a backlog item. The citations that name them dangle permanently.
- **No text-span search within a node's rectangle.** Asking "where in this node's region does
  this phrase sit" is a real capability and it is simply not in this release.
- **`/region` serves a spreadsheet as cells, not as a picture of cells.** For a sheet, JSON
  is the better answer, and `GET /documents/{id}/cells` already gives it.
