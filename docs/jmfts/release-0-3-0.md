---
title: "0.3.0 — the job system"
---

# JMFTS 0.3.0 — the job system

!!! note "Released 2026-09-03"
    0.3.0 is the current release: tag [`v0.3.0`](https://github.com/jmccardle/jmfts/releases/tag/v0.3.0), and both wheels on PyPI. One of the seven planned phases has not landed and two more are still under consideration — see [What is not here](#what-is-not-here).

    Every console block below is real output, captured by running `scripts/demo_release_0_3_0.py` against the tree. Regenerating that file is how this page is updated, so the page cannot describe a run the appliance no longer does.

Ingestion used to be decided in three places that did not know about each other. A declarative table decided what the uploaded file would do, eight hand-written lists inside task handlers decided what each created node would do, and a third planner decided the summarization rungs. This release makes one table decide all of it.

The consequence a user can see is small and specific: the spreadsheet options are settable, a rule's threshold is an option rather than a literal, `EXPLAIN` reports work below a fan-out, and every node in the tree records which rule made it.

## Where this is specified

`docs/SPRINT_JOBS.md` is the plan and `docs/INGEST_SPEC.md` is normative for the result. Neither ships in the public tree; the [README's note on documentation](https://github.com/jmccardle/jmfts) says which documents are held back and why.

| Phase | What | State |
|---|---|---|
| 1 | Every task handler declares what it reads, what it writes, and how many children it may create | landed |
| 2 | The evidence registry: one door onto everything ingestion writes about a node | landed |
| 2a | The synchronous ingest path onto the queue, then deleted | landed |
| 2b | Evidence leaves `documents.structured_content` for its own table | landed |
| 3 | A rule names its scope; a node names its rule; one planner replaces the hand-written lists | landed |
| 4 | Guards take operators, so a threshold is data | landed |
| 5 | Multiplicity and the cost fold, so `EXPLAIN` says how much | planned |
| 6 | Rule sets, bindings, budgets | under consideration |
| 7 | The settling walk generalised; the rollup special case deleted | under consideration |

## 1. One ingest path

`jmfts_core/pipeline.py` is deleted. `execute_pipeline`, `PipelineDefinition` and `StageConfig` are gone, and with them the idea of a *stage*. There are tasks, and which of them a document runs is a pure function of the format, what `probe` measured, and the options the upload carried.

```console
$ python -m scripts.demo_release_0_3_0 run one-path
probe measured 271 bytes of retrieval-notes.md
----------------------------------------------
  format    text
  patterns  has_headings, has_text_layer

What Part 4's table scheduled, at the file node
-----------------------------------------------
  extract:text           write self
  structure:declared     write children, after extract:text
                         params chunk_strategy='sentence_packed', max_tokens=120, min_chunk_length=20
  index:bm25             write self, after structure:declared

What it deliberately did not schedule, and why
----------------------------------------------
  ocr                    patterns.is_scanned was not measured
  structure:inferred     patterns.has_headings is true, and structure:inferred runs only when it is false
  structure:conversation patterns.is_conversation is false
  structure:sheets       format 'text' names no worksheet list a declared rung could read
  ... and 4 more rows, each with its own measured reason

  Every row of the table is decided. A task missing from a plan would be a
  wrong answer rather than a short one, so nothing is omitted for brevity here
  except by this script.
```

A row that did not fire says which measurement was false. That is not logging — it is what `POST /ingest/explain` returns, and it is the same string the run records on the node.

`POST /ingest` did **not** become asynchronous. The request enqueues, drains its own document's tasks, and returns the same finished tree it always did. The wire did not move; the work did. A caller who wants the asynchronous shape has it unchanged at `POST /ingest/file`.

## 2. A rule names its scope

Before this release a rule could only apply to the uploaded file node. Anything that had to run on a *created* node — each worksheet of a workbook, each chunk of a document — was a literal `TaskSpec` typed inside the handler that created the node. It had no name in the table, no declared parameters, and no way for a plan to report it.

A `TaskRow` now carries a scope, and a scope has two forms: the file node, or the children another rule produced.

<figure class="dia"><svg viewBox="0 0 680 300" role="img" aria-labelledby="dia-scope-t dia-scope-d"><title id="dia-scope-t">One rule table, three scopes, over one document tree</title><desc id="dia-scope-d">On the left, a box labelled TASK ROWS is divided into three bands. The top band is labelled at root and lists extract colon text, structure colon sheets and index colon bm25. The middle band is labelled at children of structure colon sheets, sheet, and lists profile colon sheet and extract colon sheet. The bottom band is labelled at children of dot dot dot, chunk, record or summary, and lists embed. On the right is a document tree: a solid file node at the top, two dashed sheet nodes below it, and three dashed leaf nodes below those, typed record, summary and record. Three connectors run from the bands to the tree regions they apply to. The middle connector is red, squared off where it leaves the band, and lands on the first dashed sheet node. The dashed nodes are annotated as not existing when the plan is made.</desc><text x="0" y="14" class="label-role">jmfts</text><rect x="20" y="40" width="300" height="200" class="fill-surface stroke"/><text x="32" y="62" class="label">TASK_ROWS</text><line x1="20" y1="72" x2="320" y2="72" class="stroke-soft"/><text x="32" y="94" class="label">@root</text><text x="32" y="114" class="label-soft">extract:text · structure:sheets · index:bm25</text><line x1="20" y1="128" x2="320" y2="128" class="stroke-soft"/><text x="32" y="150" class="label">@children_of(structure:sheets):sheet</text><text x="32" y="170" class="label-soft">profile:sheet · extract:sheet</text><line x1="20" y1="184" x2="320" y2="184" class="stroke-soft"/><text x="32" y="206" class="label">@children_of(…):chunk|record|summary</text><text x="32" y="226" class="label-soft">embed</text><path d="M320 110 H358 V70 H482" class="stroke-hair fill-none"/><path d="M490 70 L481 66 L481 74 Z" class="fill-ink"/><rect x="316" y="165" width="10" height="10" class="fill-red"/><path d="M321 170 H358 V147 H392" class="stroke-red fill-none"/><path d="M400 147 L391 143 L391 151 Z" class="fill-red"/><path d="M320 226 H382" class="stroke-hair fill-none"/><path d="M390 226 L381 222 L381 230 Z" class="fill-ink"/><rect x="490" y="56" width="110" height="28" class="fill-ground stroke"/><text x="545" y="75" text-anchor="middle" class="label">file</text><line x1="545" y1="84" x2="545" y2="110" class="stroke-hair"/><line x1="450" y1="110" x2="610" y2="110" class="stroke-hair"/><line x1="450" y1="110" x2="450" y2="134" class="stroke-hair"/><line x1="610" y1="110" x2="610" y2="134" class="stroke-hair"/><rect x="400" y="134" width="100" height="26" class="fill-ground stroke stroke-dashed"/><text x="450" y="152" text-anchor="middle" class="label">sheet</text><rect x="560" y="134" width="100" height="26" class="fill-ground stroke stroke-dashed"/><text x="610" y="152" text-anchor="middle" class="label">sheet</text><line x1="450" y1="160" x2="450" y2="188" class="stroke-hair"/><line x1="423" y1="188" x2="497" y2="188" class="stroke-hair"/><line x1="423" y1="188" x2="423" y2="212" class="stroke-hair"/><line x1="497" y1="188" x2="497" y2="212" class="stroke-hair"/><line x1="610" y1="160" x2="610" y2="212" class="stroke-hair"/><rect x="390" y="212" width="66" height="24" class="fill-ground stroke-hair stroke-dashed"/><text x="423" y="229" text-anchor="middle" class="label-soft">record</text><rect x="464" y="212" width="66" height="24" class="fill-ground stroke-hair stroke-dashed"/><text x="497" y="229" text-anchor="middle" class="label-soft">summary</text><rect x="577" y="212" width="66" height="24" class="fill-ground stroke-hair stroke-dashed"/><text x="610" y="229" text-anchor="middle" class="label-soft">record</text><text x="390" y="262" class="label-soft">dashed: does not exist yet</text><text x="20" y="272" class="label-mark">scope form 2</text><text x="20" y="290" class="label-soft">a rule naming nodes no plan can point at yet</text></svg><figcaption>The full third scope reads <code>@children_of(structure:declared|structure:inferred|structure:conversation|profile:sheet|extract:sheet):chunk|record|summary</code>. A scope names several producing rules because one rule — <code>embed</code> — applies to the leaves of five of them, and it names a usetype because without one an <code>embed</code> would land on every empty section container as well as on the chunks inside it.</figcaption></figure>

Asking the table at a scope is the same call, with one more argument:

```console
$ python -m scripts.demo_release_0_3_0 run scope
Every scope Part 4's table declares
-----------------------------------
  @root
      extract:text, ocr, structure:declared, structure:inferred, structure:conversation, structure:sheets, extract:tables, extract:images, citation, index:bm25, extract:facts
  @children_of(structure:sheets):sheet
      profile:sheet, extract:sheet
  @children_of(structure:declared|structure:inferred|structure:conversation|profile:sheet|extract:sheet):chunk|record|summary
      embed

The same table, asked at the file node and at a chunk
-----------------------------------------------------
  @root
      extract:text, structure:declared, index:bm25
  @children_of(structure:declared|structure:inferred|structure:conversation|profile:sheet|extract:sheet):chunk|record|summary
      embed

  The chunk does not exist yet. `structure:declared` has not run, so there is no
  node to name — and that is exactly why the row lives in the table rather than
  in the handler that creates the node. Before Phase 3 a plan could not report it.
```

## 3. The walk goes up, so a rule that fans out enqueues down

The obvious reading of "one planner" is that the planner enqueues everything and the handlers stop enqueuing. That is wrong, and the reason is worth stating because an earlier draft of the design got it wrong twice.

A node becomes searchable when the settling walk reaches it. The walk advances to a node's parent and never descends. So a node created with no work on it is never visited, never embedded, and nothing notices. A rule that creates children must therefore enqueue those children's work at the moment it creates them.

<figure class="dia"><svg viewBox="0 0 680 280" role="img" aria-labelledby="dia-walk-t dia-walk-d"><title id="dia-walk-t">The settling walk travels upward; a fan-out rule enqueues downward</title><desc id="dia-walk-d">A vertical tree of three nodes: file at the top, section in the middle, chunk at the bottom, joined by thin lines. On the left, a single long arrow runs upward alongside all three, from the chunk past the section to the file, labelled settle underscore walk, advances to parent id, never descends. On the right, a box labelled structure colon declared sits beside the file node and is joined to it by a short line captioned runs here. From that box a red connector runs down the right-hand side and turns left into the chunk node, with a red square where it leaves the box and a red arrowhead entering the chunk. It is annotated enqueue underscore frontier, the batch the new child gets.</desc><text x="0" y="14" class="label-role">jmfts</text><rect x="230" y="30" width="170" height="30" class="fill-ground stroke"/><text x="315" y="50" text-anchor="middle" class="label">file</text><line x1="315" y1="60" x2="315" y2="110" class="stroke-hair"/><rect x="230" y="110" width="170" height="30" class="fill-ground stroke"/><text x="315" y="130" text-anchor="middle" class="label">section</text><line x1="315" y1="140" x2="315" y2="190" class="stroke-hair"/><rect x="230" y="190" width="170" height="30" class="fill-ground stroke"/><text x="315" y="210" text-anchor="middle" class="label">chunk</text><path d="M230 205 H195 V72" class="stroke fill-none"/><path d="M195 62 L190 73 L200 73 Z" class="fill-ink"/><text x="10" y="120" class="label">settle_walk</text><text x="10" y="138" class="label-soft">advances to parent_id</text><text x="10" y="154" class="label-soft">never descends</text><rect x="450" y="30" width="200" height="30" class="fill-ground stroke"/><text x="550" y="50" text-anchor="middle" class="label">structure:declared</text><line x1="400" y1="45" x2="450" y2="45" class="stroke-hair"/><text x="404" y="24" class="label-soft">runs here</text><rect x="641" y="55" width="10" height="10" class="fill-red"/><path d="M646 60 V205 H408" class="stroke-red fill-none"/><path d="M400 205 L409 201 L409 209 Z" class="fill-red"/><text x="210" y="248" class="label-mark">enqueue_frontier</text><text x="210" y="266" class="label-soft">the batch a new child gets — planned once per fan-out, not per child</text></svg><figcaption>What this release removed is the hand-written list, not the call. Five handlers that carried a literal <code>TaskSpec</code> tuple now ask <code>plan_frontier</code> for one, and the rows it reads are declared beside every other scheduling decision. The frontier is planned once per fan-out and not once per child, because the answer is a function of the format, the patterns and the options, and every child of one run shares all three: a forty-sheet workbook is one evaluation and forty enqueues.</figcaption></figure>

## 4. `EXPLAIN` reaches the sheet tier

`POST /ingest/explain` answers what a format with a given set of options would do, without storing any bytes. `POST /ingest/analyze` runs `probe` over real bytes and answers the same way. Both call the same planner, which is what stops a forecast and a run from describing different work.

Until this release the forecast stopped at the worksheet list, because the per-sheet tasks were not rows. Each explained task now carries the scope it applies to.

```console
$ python -m scripts.demo_release_0_3_0 run explain
POST /ingest/explain — format xlsx, patterns probed
---------------------------------------------------
  task                   outcome      scope
  probe                  enqueued     @root
  structure:conversation impossible   @root
  structure:sheets       enqueued     @root
  profile:sheet          enqueued     @children_of(structure:sheets):sheet
  extract:sheet          enqueued     @children_of(structure:sheets):sheet
  citation               impossible   @root
  embed                  enqueued     @children_of(structure:declared|structure:inferred|structure:conversation|profile:sheet|extract:sheet):chunk|record|summary

The 3 rows that used to be invisible
------------------------------------
  profile:sheet
      scope   @children_of(structure:sheets):sheet
      params  sketch_columns=True
  extract:sheet
      scope   @children_of(structure:sheets):sheet
      params  max_rows=10000, with_cell_notes=True
  embed
      scope   @children_of(structure:declared|structure:inferred|structure:conversation|profile:sheet|extract:sheet):chunk|record|summary
      params  with_tokens=True

  None of these three name a node that exists yet. `structure:sheets` has not
  run, so there are no worksheets — and `embed` is one scope further down again,
  on the records `extract:sheet` will write.
```

`scope` is a new field on `ExplainedTaskResponse`. It is additive: a client that ignores it reads the same plan it read before, one task longer.

## 5. The spreadsheet options are settable

`max_rows`, `with_cell_notes` and `sketch_columns` were documented, validated and unreachable. The option group existed and was checked; the handler read its own literal default and never looked at the value. A row's `params_key` is what closes that, because it is what puts the resolved group on the queue row the handler reads.

```console
$ python -m scripts.demo_release_0_3_0 run knobs
Every option group, and which task reads it
-------------------------------------------
  embed            embed
  facts            extract:facts
  rollup           (no row names it)
  sheet_profile    profile:sheet
  sheet_records    extract:sheet
  structure        structure:declared, structure:inferred

Setting one, and watching it reach the row
------------------------------------------
  override   {'sheet_records': {'max_rows': 500}}
  resolved   max_rows=500, with_cell_notes=True
  on the row extract:sheet: max_rows=500, with_cell_notes=True

And refusing a bad one
----------------------
  {'sheet_records': {'max_rows': 0}}
      ValueError: option sheet_records.max_rows: expected a positive integer, got 0
  {'sheet_records': {'max_rows': True}}
      ValueError: option sheet_records.max_rows: expected an integer, got bool

  6 groups carry per-key checks, and `max_rows` reaching the
  handler is what Phase 3 closed. The group was validated before this release; the
  handler read its own literal default and never looked at the value.
```

`rollup` reporting `(no row names it)` is correct rather than a gap. Summarization belongs to the settling walk and not to the table, which is what phase 7 would change.

`max_rows: True` is refused because `bool` is a subclass of `int` in Python, and a workbook truncated at one row is not what anyone meant.

## 6. The table audits itself

Adding a scope adds a way to write a rule table that is silently wrong: a row ordered after a row below it, or scoped to the children of a rule that has not been decided yet. The design forbids answering that with a second checked-in list, because a test over a list only proves the list equals itself. The check is stated over the table the appliance runs, and it runs at import.

```console
$ python -m scripts.demo_release_0_3_0 run audit
Four mistakes the table refuses, at import time
-----------------------------------------------
  a duplicate task name
      ValueError: task 'structure:sheets' has two rows in TASK_ROWS; every outcome this table reports is keyed by task name, so one of the two would be invisible
  `after` naming a row that comes later
      ValueError: row 'a' is ordered after 'b', which is not above it in TASK_ROWS; within-node ordering can only name a task whose id the batch already has
  a child scope naming a producer below it
      ValueError: row 'a' is scoped to the children of 'structure:sheets', which is not above it in TASK_ROWS; a scope decides eligibility from the producing row's, which has to be decided first
  a `params_key` naming no group
      ValueError: row 'a' names option group 'not_a_group', which is not in TASK_PARAM_DEFAULTS; the declared groups are ['embed', 'facts', 'rollup', 'sheet_profile', 'sheet_records', 'structure']

  A test over a list only proves the list equals itself. These are stated over
  the table the appliance actually runs, so deleting a row moves the audit with it.
```

The appliance will not start with a bad table. That is the intended cost.

## 7. A guard is a comparison, and the threshold is the caller's

Until this release a rule's condition was a list of pattern names read for truthiness. Any question a rule wanted to ask had to reach it as a flag, which meant `probe` had to invent a name for the answer — a rule that wanted "more than one worksheet" needed a `has_several_sheets`, and the number that decided it lived in the prober rather than in the table.

A condition is now a list of terms, and a term is `left op right`. Six operators, `=` `!=` `<` `<=` `>` `>=`, and no `and`, `or` or `not`. Dropping the connectives is deliberate: `requires` is already a conjunction and `forbids` already a list of exclusions, and one term is what lets a plan report one sentence per condition rather than one per expression.

Either side may name an option instead of a value. That is what makes a threshold data — it resolves through the same three-layer stack every other option does, so a caller sets it per request and `EXPLAIN` reports both the name and the number it resolved to.

**`requires` and `forbids` are not each other's negation, and the difference is what an unmeasured name means.** A required pattern that nobody measured blocks the rule: the precondition cannot be confirmed. A forbidden pattern that nobody measured does not: no evidence of a blocker is not a blocker. Fold the two into one expression and `structure:inferred`'s condition reads `not (has_heading_styles = true)`, which is false for every `.docx` — because no prober emits that name — and every `.docx` finishes ingestion with no children.

```console
$ python -m scripts.demo_release_0_3_0 run guards
Every pattern a guard may read, and what it holds
-------------------------------------------------
  char_count           int
      extract:facts
  has_heading_styles   bool     (probe does not write it)
      structure:declared, structure:inferred
  has_headings         bool
      structure:declared, structure:inferred
  has_images           bool
      extract:images
  has_outline          bool
      structure:declared, structure:inferred
  has_sheets           bool
      structure:declared, structure:inferred, structure:sheets, profile:sheet, extract:sheet
  has_slides           bool
      structure:declared, structure:inferred
  has_text_layer       bool
      extract:text, structure:declared, structure:inferred, structure:conversation, extract:tables, citation, index:bm25, extract:facts
  is_conversation      bool
      structure:declared, structure:inferred, structure:conversation
  is_damaged           bool
      extract:text
  is_scanned           bool
      ocr
  pages_with_tables    list     (probe does not write it)
      extract:tables

  `matched.patterns` is an open namespace, and `evidence.pattern_type` answers
  `bool` for a name it has never heard of. That is right for storage and wrong for
  a guard: `has_hedings` would type-check, plan cleanly, and stand its row down on
  every document forever.

The two unknown policies, on a .docx
------------------------------------
  patterns supplied   has_text_layer=True
  has_heading_styles  guardable, and no prober emits it

  structure:declared     not_applicable
      patterns.has_heading_styles was not measured
  structure:inferred     enqueued
      its condition holds

  `structure:declared` requires that name and `structure:inferred` forbids it.
  Flatten the two lists into one expression and the second reads
  `not (has_heading_styles = true)`, which is false — and every .docx comes out of
  ingestion with no children.

A threshold the caller sets, on a file whose size was measured
--------------------------------------------------------------
  retrieval-notes.md probed as text: char_count=271
  facts=(the defaults)
      extract:facts   not_applicable
      options.facts.enabled is false, and extract:facts runs only when it is true
  facts=enabled=True
      extract:facts   enqueued
  facts=enabled=True, min_characters=400
      extract:facts   not_applicable
      patterns.char_count is 271, and extract:facts does not run when it is less than options.facts.min_characters (400)

The same floor, on a format nothing measures the size of
--------------------------------------------------------
  patterns supplied   has_outline=True, has_text_layer=True
  facts=enabled=True, min_characters=400
      extract:facts   enqueued

  probe emits `char_count` for `text` alone. Written as a `requires`, this floor
  would have stopped fact extraction on every PDF, .docx and .pptx — not because
  they are short, but because nobody measured. Written as a `forbids` it says what
  a caller means by a minimum: do not spend the LLM call on a document measured as
  too small, and do spend it where nobody measured a size.

Four terms the table refuses, at import time
--------------------------------------------
  a pattern name the vocabulary does not have
      ValueError: row 'a' guards on ['has_hedings'], which GUARDABLE_PATTERNS does not name; `matched.patterns` is an open namespace, so an unlisted name would read as a pattern nobody measures and stand the row down forever
  a count compared with a flag
      ValueError: row 'a' compares char_count (int) with True (bool); a guard's two sides have to be the same kind of thing
  an ordering operator on a flag
      ValueError: row 'a' orders has_text_layer with '>', and it holds a bool; ['<', '<=', '>', '>='] are for counts
  an option nothing declares
      ValueError: row 'a' guards on options.facts.min_chars, which is not a declared option; a guard's option reference is resolved by `resolve_options` and a name nothing declares would resolve to nothing

  Same shape as the four row mistakes above: the check is stated over the term the
  appliance runs, not over a checked-in list of names to compare it against.
```

**The names a guard may read are a closed list, and that is a departure.** Everything `probe` measures is stored in an open namespace: a new prober adds a name and nothing has to be told about it. A guard is the one reader for which an unknown name and a false one are indistinguishable, so `has_hedings` would be a well-typed comparison that plans without complaint and stands its rule down on every document forever. Twelve names are declared with their types, and a rule that reads anything else stops the appliance at import. Storage keeps its open namespace; only the guard vocabulary is closed.

The types are declared rather than derived for a reason the list shows. `pages_with_tables` holds a list of page numbers, and the storage rule — everything is a flag unless named otherwise — calls it a boolean. Truthiness survived that mistake. `>` would not.

`min_characters` is the first option that decides whether a task runs at all, rather than how it runs. It is written as an exclusion, and the measurement in the block above is why: `char_count` is emitted for plain text and nothing else, so the same floor written as a requirement would stop fact extraction on every PDF, `.docx` and `.pptx` — the `.docx` failure again, in a second costume.

Nothing on the wire moved. `ExplainedTask.requires` still holds strings: a rule that reads a name for truthiness renders as that name, exactly as before, and a comparison renders as the comparison. `facts.min_characters` is a new option in an existing group and defaults to `0`, which excludes nothing.

## 8. Evidence is rows, and the column is the caller's

Everything ingestion learned about a node — what `probe` matched, what the extractor found, the attempt log — used to live in `documents.structured_content`, alongside whatever the caller put there. Two handlers writing two different names to one node was a read-modify-write race, and one of the two writes was lost with nothing raised.

<figure class="dia"><svg viewBox="0 0 680 280" role="img" aria-labelledby="dia-ev-t dia-ev-d"><title id="dia-ev-t">Evidence moves out of a JSONB column and into its own table</title><desc id="dia-ev-d">Two panels separated by a vertical divider. On the left, headed 0.2.1, one hatched documents slab holds a knocked-out band labelled structured content, listing matched, attempts and extraction alongside whatever the caller wrote; it is captioned one JSONB column, read modify write, two writers and one surviving write. On the right, headed 0.3.0, two hatched slabs are stacked: documents, whose structured content band is now glossed as wholly the caller's, and below it document evidence, holding one row per document id and name with a value and a state. A red connector runs down from the documents slab into the document evidence slab, squared off where it leaves documents, and is annotated one row per name.</desc><defs><pattern id="dia-hatch-ev-a" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern><pattern id="dia-hatch-ev-b" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="0" y="14" class="label-role">jmfts</text><text x="20" y="38" class="label-soft">0.2.1</text><rect x="20" y="50" width="280" height="104" fill="url(#dia-hatch-ev-a)" class="stroke"/><rect x="24" y="54" width="272" height="96" class="fill-none stroke-soft"/><rect x="34" y="64" width="252" height="76" class="fill-ground"/><text x="160" y="86" text-anchor="middle" class="label">structured_content</text><text x="160" y="108" text-anchor="middle" class="label-soft">matched · attempts · extraction</text><text x="160" y="126" text-anchor="middle" class="label-soft">+ whatever the caller wrote</text><text x="20" y="238" class="label-soft">one JSONB column, read-modify-write</text><text x="20" y="256" class="label-soft">two writers, and one surviving write</text><line x1="330" y1="24" x2="330" y2="266" class="stroke-soft"/><text x="360" y="38" class="label-soft">0.3.0</text><rect x="360" y="50" width="290" height="62" fill="url(#dia-hatch-ev-b)" class="stroke"/><rect x="364" y="54" width="282" height="54" class="fill-none stroke-soft"/><rect x="372" y="58" width="266" height="46" class="fill-ground"/><text x="505" y="78" text-anchor="middle" class="label">documents</text><text x="505" y="97" text-anchor="middle" class="label-soft">structured_content — wholly the caller's</text><rect x="500" y="107" width="10" height="10" class="fill-red"/><line x1="505" y1="112" x2="505" y2="140" class="stroke-red"/><path d="M505 148 L501 139 L509 139 Z" class="fill-red"/><rect x="360" y="148" width="290" height="62" fill="url(#dia-hatch-ev-b)" class="stroke"/><rect x="364" y="152" width="282" height="54" class="fill-none stroke-soft"/><rect x="372" y="156" width="266" height="46" class="fill-ground"/><text x="505" y="176" text-anchor="middle" class="label">document_evidence</text><text x="505" y="195" text-anchor="middle" class="label-soft">(document_id, name) → value · state</text><text x="360" y="238" class="label-mark">one row per name</text><text x="360" y="256" class="label-soft">one statement to append; three states per name</text></svg><figcaption>Neither reason is performance. A read-modify-write lost writes under concurrency, and a name needs three states — written, written-and-known-empty, and never run — where a JSONB key has room for two, because staling a block means deleting it and a deleted key is indistinguishable from one that was never written.</figcaption></figure>

**This is a versioned break.** A client reading `matched.patterns` out of `structured_content` now reads nothing. `GET /documents/{id}/evidence` is where it went — a route rather than a field on `DocumentResponse`, because a field would join that table on every read including every search hit.

## 9. A node names its rule

`Document.produced_by` records which rule created a node. NULL means asserted: a person, an importer or an upload made it, not a rule. That is the same convention `Triple.derived_by` already used, and for the same reason — the first materialized thing must not be indistinguishable from something a document actually said.

`usetype` does not answer this question. That says what a node *is*, and one structure rung writes both `section` and `chunk`.

<figure class="dia"><svg viewBox="0 0 680 280" role="img" aria-labelledby="dia-pb-t dia-pb-d"><title id="dia-pb-t">produced by, and the one edit that clears it</title><desc id="dia-pb-d">A file node at the top carries produced by null, glossed as asserted because the upload wrote it. Below it, three chunk nodes hang off a rail. The first two carry produced by structure colon declared. The third also carries structure colon declared, and a red connector rises into it from a box below reading PATCH slash documents slash id with a content body, annotated a content edit clears the stamp. A footnote records that a retitle and a metadata patch leave it alone.</desc><text x="0" y="14" class="label-role">jmfts</text><rect x="240" y="30" width="200" height="46" class="fill-ground stroke"/><text x="340" y="50" text-anchor="middle" class="label">file</text><text x="340" y="67" text-anchor="middle" class="label-soft">produced_by = NULL</text><text x="452" y="48" class="label">asserted</text><text x="452" y="66" class="label-soft">the upload wrote it</text><line x1="340" y1="76" x2="340" y2="100" class="stroke-hair"/><line x1="100" y1="100" x2="580" y2="100" class="stroke-hair"/><line x1="100" y1="100" x2="100" y2="130" class="stroke-hair"/><line x1="340" y1="100" x2="340" y2="130" class="stroke-hair"/><line x1="580" y1="100" x2="580" y2="130" class="stroke-hair"/><rect x="30" y="130" width="140" height="46" class="fill-ground stroke"/><text x="100" y="150" text-anchor="middle" class="label">chunk</text><text x="100" y="167" text-anchor="middle" class="label-soft">structure:declared</text><rect x="270" y="130" width="140" height="46" class="fill-ground stroke"/><text x="340" y="150" text-anchor="middle" class="label">chunk</text><text x="340" y="167" text-anchor="middle" class="label-soft">structure:declared</text><rect x="510" y="130" width="140" height="46" class="fill-ground stroke"/><text x="580" y="150" text-anchor="middle" class="label">chunk</text><text x="580" y="167" text-anchor="middle" class="label-soft">structure:declared</text><rect x="470" y="212" width="210" height="30" class="fill-ground stroke-hair"/><text x="575" y="232" text-anchor="middle" class="label">PATCH {"content": …}</text><rect x="570" y="207" width="10" height="10" class="fill-red"/><line x1="575" y1="212" x2="575" y2="186" class="stroke-red"/><path d="M575 176 L570 187 L580 187 Z" class="fill-red"/><text x="20" y="222" class="label-mark">a content edit clears the stamp</text><text x="20" y="240" class="label-soft">a retitle does not, and neither does a metadata patch —</text><text x="20" y="256" class="label-soft">neither makes the node stop being what the rule produced</text></svg><figcaption>The column backfills nothing. A node written before it existed cannot be distinguished from one a caller wrote, and stamping those retroactively would be a guess presented as a record.</figcaption></figure>

Both halves, run against a live appliance:

```console
$ python -m scripts.demo_release_0_3_0 run stamp
retrieval-notes.md -> node 1, 7 tasks drained
---------------------------------------------
     id  usetype    produced_by            title
      1  file       (asserted)             retrieval-notes.md
      2  section    structure:declared     Retrieval notes
      3  chunk      structure:declared     Retrieval notes
      4  section    structure:declared     Late interaction
      5  chunk      structure:declared     Late interaction
      6  section    structure:declared     Segmentation
      7  chunk      structure:declared     Segmentation

  `(asserted)` is a NULL column and it means a person, an importer or an
  upload made the node. The file node is asserted because the upload wrote it.

Evidence is rows, not a column
------------------------------
  node 1 carries 6 evidence names:
      attempts, extraction, file, matched, options, structure
  structured_content is the caller's: {}

A person edits a produced node
------------------------------
  node 2 before   produced_by='structure:declared'
  after a retitle           produced_by='structure:declared'
  after a content edit      produced_by=None

  Only `content` clears it. A retitle does not make the node stop being what
  the rule produced, and neither does a metadata patch.
```

`produced_by` is a new field on `DocumentResponse`, and it is additive.

## Two breaks a client can see

1. **Evidence left `structured_content`.** Reading `matched.patterns` from that column returns nothing; read `GET /documents/{id}/evidence` instead.
2. **`PipelineStageInfo` and `PipelineInfo.stages` are gone from the contracts.** There are no stages. `POST /ingest/explain` answers what a document will run, from a format and a set of options rather than from a pipeline name.

Both are why this is a minor version and not a patch.

## Upgrading

Two migrations, applied in order:

| Migration | What |
|---|---|
| `015_evidence_rows.sql` | Creates `document_evidence` and moves twenty-nine names out of `documents.structured_content`. |
| `016_document_produced_by.sql` | Adds `documents.produced_by` and an index on `(parent_id, produced_by)`. |

There is no migration ledger. Choosing and applying deltas is still a deliberate act by an operator who knows the target's state.

!!! warning "015 moves data a running 0.2.1 process reads"
    Deploy the code together with the migration, not around it. 016 is additive and backfills nothing: nodes that predate it read as asserted, which is the honest answer rather than a guessed one.

## What is not here

**Planned, and it slipped this release.** Phase 5 folds cost over the plan, so `EXPLAIN` reports how much work as an interval instead of only which work. It takes the next number rather than this one.

**Under consideration, and not committed.** Phase 6 is rule sets, bindings and budgets — selecting a named set of rules and re-casting it at an existing subtree. Phase 7 generalises the settling walk and deletes the rollup planner as a special case. Both are specified; neither is scheduled, and this page will say so until that changes.

**Deliberately not built.** A re-run of a fan-out rule would need to match existing children, keep them, and reserve the subtree for deletions. Nothing re-runs a fan-out rule yet, so building the reservation would reserve a region for a delete that cannot happen.

**One finding, left open.** The conversation rung creates child nodes and declares no bound on how many. Declaring one needs `probe` to count message lines, which is a design decision rather than a patch.

## Running this page yourself

```bash
git clone https://github.com/jmccardle/jmfts && cd jmfts
python3 -m venv .venv
./.venv/bin/pip install -e ./jmfts-client
./.venv/bin/pip install -e ".[dev]"

./.venv/bin/python -m scripts.demo_release_0_3_0 list
./.venv/bin/python -m scripts.demo_release_0_3_0 run
```

The last command runs every section except `stamp`, which needs a database:

```bash
docker run -d --name jmfts-demo-pg \
  -e POSTGRES_USER=jmfts -e POSTGRES_PASSWORD=jmfts -e POSTGRES_DB=jmfts \
  -p 127.0.0.1:5434:5432 pgvector/pgvector:pg16
export JMFTS_DB_PORT=5434 JMFTS_EMBEDDING_DEVICE=cpu
./.venv/bin/jmfts-init-db
./.venv/bin/python -m scripts.demo_release_0_3_0 run stamp
```

`markdown --out demo.md` writes the same output as the fenced blocks above. That is how this page is regenerated.
