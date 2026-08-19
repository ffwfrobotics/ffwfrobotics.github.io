---
title: "Style guide"
category: "reference"
status: "stable"
---

# Style guide

The visual system here is derived from the
[FFwF Robotics homepage](https://github.com/ffwfrobotics), adapted for
long-form documentation. Everything on this page is rendered live — switch the
theme with the skull in the header to see both schemes.

Two rules govern the rest:

1. **One accent.** Red is the only chromatic color on the site. If something
   needs to stand out, it is red or it is not emphasized. The
   [state badges](#documentation-state) are the single deliberate exception.
2. **Courier is the machine voice.** Headings, code, nav, and labels are
   Courier New. Prose is not machine output, so prose is not Courier.

## Color

Tokens live in `docs/stylesheets/ffwf.css` and flip by scheme. Structural red
never flips — borders carry no text, so they hold the identity constant.

<div class="swatches">
  <div class="swatch">
    <div class="swatch__chip" style="background:#ff0000"></div>
    <div class="swatch__meta"><b>--ffwf-red</b><span>#FF0000 · rules, borders, pill outlines</span></div>
  </div>
  <div class="swatch">
    <div class="swatch__chip" style="background:var(--ffwf-ink-red)"></div>
    <div class="swatch__meta"><b>--ffwf-ink-red</b><span>headings + links · flips by scheme</span></div>
  </div>
  <div class="swatch">
    <div class="swatch__chip" style="background:var(--ffwf-ink)"></div>
    <div class="swatch__meta"><b>--ffwf-ink</b><span>body text</span></div>
  </div>
  <div class="swatch">
    <div class="swatch__chip" style="background:var(--ffwf-ash)"></div>
    <div class="swatch__meta"><b>--ffwf-ash</b><span>meta, captions, muted</span></div>
  </div>
  <div class="swatch">
    <div class="swatch__chip" style="background:var(--ffwf-surface)"></div>
    <div class="swatch__meta"><b>--ffwf-surface</b><span>code, cards, footer</span></div>
  </div>
  <div class="swatch">
    <div class="swatch__chip" style="background:var(--ffwf-ground)"></div>
    <div class="swatch__meta"><b>--ffwf-ground</b><span>page background</span></div>
  </div>
</div>

### Why the red has two values

`#FF0000` on white measures 4.0:1, under the 4.5:1 WCAG AA floor for body text.
The homepage never hit this because it is nearly all headings; a docs site is
mostly links and paragraphs, so it would hit it constantly.

So the text-carrying red flips: `#FF0000` on dark (4.8:1) and `#CC0000` on
light (5.9:1). Both clear AA at every size, and both still read unmistakably as
the brand red. Borders and rules stay `#FF0000` in both schemes.

Links are also underlined, so color is never the only signal.

## Type

| Role | Face |
|------|------|
| Headings, nav, labels, code | `"Courier New", Courier, monospace` |
| Body copy | system sans stack |

No webfonts are fetched. The site is self-contained, which keeps it forkable
and fast on first paint.

Making body copy sans is the one real departure from the homepage, and it buys
something specific: **code stops looking like prose.** When everything is
Courier, a command you are meant to type is typographically identical to a
sentence about that command — a distinction docs cannot afford to lose.

`h1` is red and uppercase. `h2` is red with a `2px` rule beneath it, carried
over from the homepage's section dividers. `h3` drops to body color; `h4` is
uppercase ash.

## The mark

The logo is a black skull and crossed wrenches over a red flame on a
transparent ground. That transparency is a problem on the dark scheme: the
black features have nothing to sit against, so the wrenches disappear
completely and the skull becomes a void inside the flame. Only the red survives.

Two fixes, because they live in different places:

- **Header logo** — a stack of four axis-aligned 1px white `drop-shadow`
  filters traces the alpha channel, plus one soft 4px glow so the edge doesn't
  read as a sticker cutout. Applied only under `[data-md-color-scheme="slate"]`.
- **Favicon** — no stylesheet can reach it, and dark browser tab strips have
  the same problem, so the halo is baked into `favicon.ico` at generation time.
  Each frame is dilated proportionally to its own size, so the outline stays
  1px at 16px instead of being downsampled away. On a light tab strip the white
  halo is simply invisible.

`docs/assets/logo.png` stays the clean original — the header treatment is
applied in CSS, not baked into the asset.

## Components

### Axis eyebrow

Every category page states its coordinates on the 2×2. The recipe — black
fill, `2px` solid red border, `15px` radius — is lifted verbatim from the
homepage's `ProjectTagLink` component.

<p class="axis">Action × Acquisition</p>

```html
<p class="axis">Action × Acquisition</p>
```

### Chips

The quiet pill: same geometry, hairline border instead of red. A chip is a
destination, never a claim about state.

<a class="chip" href="../tectum/tutorials/quickstart/">Quickstart</a>

```html
<a class="chip" href="../tectum/tutorials/quickstart/">Quickstart</a>
```

### Code blocks

Marked with a `2px` red left rule: the same "this is machine text" signal as
the tag pills.

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/mkdocs serve
```

### Admonitions

Material ships a rainbow of admonition colors. They are flattened to the
two-color system — red for anything demanding attention, ash for anything
neutral.

!!! note
    Neutral. Ash left rule.

!!! warning
    Demands attention. Red left rule, red title.

### Crosswalk and roster

`.crosswalk` draws the four categories as a 2×2 with real axis rails; the axis
labels are the content, not decoration. `.roster` is the auto-fitting card grid
used for the project list and the integration list. Both are on the
[home page](index.md).

The axes are Diátaxis's own: **action against cognition** on the rows, and
**acquisition against application** on the columns. An earlier version of this
site used "fast against in-depth", which quietly collapsed the cognition half —
every quadrant became a way of doing something, and nothing was a way of
understanding it.

|  | Acquisition (studying) | Application (working) |
|--|------------------------|-----------------------|
| **Action** | Tutorials | Cookbook |
| **Cognition** | DevOps Manual | Reference |

The home page's crosswalk links all three projects from each quadrant. A
project page reuses the same grid, but each quadrant is a single destination,
so the heading itself is the link and the shortcut row is dropped.

Cards lift `5px` on hover, matching the homepage's `ProjectCard`. The lift is
suppressed under `prefers-reduced-motion`.

Below 45em the crosswalk collapses to one column and the axis rails come out.
Each cell then prints its own coordinates instead — without that, the quadrants
would lose the only thing the grid exists to show.

## Documentation state

Every category page declares what it is worth in its own frontmatter:

```yaml
---
title: Cookbook
category: cookbook
status: stub        # stub | outdated | draft | stable
---
```

`hooks/docstate.py` reads those declarations at build time and expands the
`<!-- docstate-table -->` marker on the home page. There is no second list to
keep in sync, and a missing or misspelled `status` fails the build rather than
rendering a table that lies.

Four states, four colors — the one place the site is not monochrome plus red:

<span class="state state--grey">stub</span>
<span class="state state--red">outdated</span>
<span class="state state--yellow">draft</span>
<span class="state state--green">stable</span>

Status is data, not emphasis. A reader scanning a state table needs to sort it
without reading it, and red-or-nothing cannot express four ordered values.
Three concessions keep it inside the system: the badges are outlined rather
than filled, so they stay in the same pill vocabulary as chips and axis
eyebrows; the word is always spelled out, so color is never the only signal;
and the palette flips by scheme like every other text color, keeping all four
above the AA floor on both grounds.

Nothing else on the site may use these colors.

### Version

Project index pages carry `version`, and `repo` when the project is on GitHub:

```yaml
---
title: Tau
kind: project
version: v0.9.1
repo: jmccardle/tau
---
```

With a `repo`, the version links to that release tag. Without one it renders as
plain text — projects hosted elsewhere get an honest unlinked version rather
than a GitHub URL that does not resolve.

## Diagrams

Rule 1 makes the obvious approach illegal. A site with one accent cannot give
Tectum a blue, Tau a green and JMFTS an orange, so the three projects are told
apart by **form** instead — by the shape of a node and the way it is attached
to its neighbours.

That constraint turns out to be the accessible answer as well. A reader with
any form of color vision, a printed page, or a screenshot run through a
grayscale filter sees exactly the same distinctions, because color was never
carrying them.

### Three grammars

Each grammar is derived from what the project actually is, not assigned
arbitrarily, so the drawing and the architecture stay in sync.

<figure class="dia"><svg viewBox="0 0 680 252" role="img" aria-labelledby="dia-key-t dia-key-d"><title id="dia-key-t">The three project grammars</title><desc id="dia-key-d">Tectum is drawn as square-cornered blocks hung off a horizontal subject rail: audio dot gateway arrows up into the rail because it publishes, and agent dot persona underscore reflection takes an arrow down from the rail because it subscribes. Tau is drawn as a rounded pill on a spine, which continues past the pill to a filled dot where it forks into a solid branch and a dashed abandoned one. JMFTS is drawn as a stack of slabs with doubled outlines, the durable one filled with a 45-degree hatch.</desc><defs><pattern id="dia-hatch-key" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="0" y="58" class="label-role">tectum</text><text x="118" y="20" class="label-soft">events.sensation.audio.filtered</text><line x1="100" y1="32" x2="640" y2="32" class="stroke"/><path d="M640 32 L631 28 L631 36 Z" class="fill-ink"/><line x1="188" y1="64" x2="188" y2="40" class="stroke"/><path d="M188 32 L184 41 L192 41 Z" class="fill-ink"/><rect x="118" y="64" width="140" height="30" class="fill-ground stroke"/><text x="188" y="84" text-anchor="middle" class="label">audio.gateway</text><line x1="435" y1="32" x2="435" y2="56" class="stroke"/><path d="M435 64 L431 55 L439 55 Z" class="fill-ink"/><rect x="340" y="64" width="190" height="30" class="fill-ground stroke"/><text x="435" y="84" text-anchor="middle" class="label">agent.persona_reflection</text><text x="0" y="148" class="label-role">tau</text><line x1="100" y1="144" x2="118" y2="144" class="stroke"/><rect x="118" y="129" width="152" height="30" rx="15" class="fill-ground stroke"/><text x="194" y="149" text-anchor="middle" class="label">AgentSession</text><line x1="270" y1="144" x2="320" y2="144" class="stroke"/><circle cx="320" cy="144" r="4" class="fill-ink"/><path d="M320 144 L320 120 L372 120" class="stroke-hair fill-none"/><text x="378" y="124" class="label-soft">extends the leaf</text><path d="M320 144 L320 168 L372 168" class="stroke-hair stroke-dashed fill-none"/><text x="378" y="172" class="label-soft">abandoned sibling</text><text x="0" y="217" class="label-role">jmfts</text><rect x="118" y="186" width="220" height="22" class="fill-ground stroke-hair"/><text x="228" y="201" text-anchor="middle" class="label-soft">token_embeddings</text><rect x="118" y="208" width="220" height="32" fill="url(#dia-hatch-key)" class="stroke"/><rect x="122" y="212" width="212" height="24" class="fill-none stroke-soft"/><rect x="188" y="215" width="80" height="18" class="fill-ground"/><text x="228" y="228" text-anchor="middle" class="label">documents</text></svg><figcaption>The key. A subject is a rail and nodes hang off it, so Tectum is blocks on a line. A Tau session is one door onto a tree that branches, so Tau is a pill on a forking spine. JMFTS is tables in Postgres, so JMFTS is stacked slabs — and the hatched one is the durable one.</figcaption></figure>

Put all three on one page — which the [integration pages](integrations/index.md)
do — and the seams are obvious without a legend.

### Connectors carry direction

On a Tectum rail the arrowhead says which way the event moves, and it is the
only thing that says so. A node with an arrow pointing *at the rail* publishes;
an arrow pointing *at the node* subscribes.

<figure class="dia"><svg viewBox="0 0 680 180" role="img" aria-labelledby="dia-dir-t dia-dir-d"><title id="dia-dir-t">Arrowhead direction on a subject rail</title><desc id="dia-dir-d">Two panels. On the left, a node named audio dot gateway connects up to the subject it emits, with the arrowhead landing on the rail: this node publishes. On the right, a node named effector dot speech takes a connector down from the subject it handles, with the arrowhead landing on the node: this node subscribes.</desc><text x="40" y="38" class="label-soft">events.sensation.audio.filtered</text><line x1="40" y1="50" x2="310" y2="50" class="stroke"/><rect x="99" y="96" width="152" height="30" class="fill-ground stroke"/><text x="175" y="116" text-anchor="middle" class="label">audio.gateway</text><line x1="175" y1="96" x2="175" y2="58" class="stroke"/><path d="M175 50 L171 59 L179 59 Z" class="fill-ink"/><text x="175" y="150" text-anchor="middle" class="label-mark">publishes</text><text x="175" y="166" text-anchor="middle" class="label-soft">arrowhead at the rail</text><line x1="340" y1="20" x2="340" y2="172" class="stroke-soft"/><text x="368" y="38" class="label-soft">events.workspace.persona_reflection.out.speak</text><line x1="368" y1="50" x2="648" y2="50" class="stroke"/><rect x="432" y="96" width="152" height="30" class="fill-ground stroke"/><text x="508" y="116" text-anchor="middle" class="label">effector.speech</text><line x1="508" y1="50" x2="508" y2="88" class="stroke"/><path d="M508 96 L504 87 L512 87 Z" class="fill-ink"/><text x="508" y="150" text-anchor="middle" class="label-mark">subscribes</text><text x="508" y="166" text-anchor="middle" class="label-soft">arrowhead at the node</text></svg><figcaption>Direction is information, so it is drawn rather than captioned. The same convention applies to a Tau spine, where the dashed limb marks an abandoned sibling branch rather than a deletion.</figcaption></figure>

### Red marks the load-bearing idea

Rule 1 applies inside a figure too. Red is not a project color and never
outlines a node — it marks the one element the figure exists to explain, and a
figure gets at most one. On a project page that is the idea the page is about;
on an integration page it is the seam between the two systems.

<figure class="dia"><svg viewBox="0 0 680 176" role="img" aria-labelledby="dia-red-t dia-red-d"><title id="dia-red-t">A Praxis binding, drawn in red</title><desc id="dia-red-d">Three nodes from the listening underscore mode schema sit below one subject rail. Only agent dot persona underscore reflection is attached to it, by a red connector with a small red square where it taps the rail and an arrowhead entering the node. The other two, effector dot speech and effector dot journal underscore append, are required by the same schema but bound to different subjects, so they float unattached.</desc><text x="20" y="26" class="label-soft">events.sensation.audio.filtered</text><line x1="20" y1="42" x2="660" y2="42" class="stroke"/><path d="M660 42 L651 38 L651 46 Z" class="fill-ink"/><rect x="20" y="90" width="140" height="32" class="fill-ground stroke"/><text x="90" y="111" text-anchor="middle" class="label">effector.speech</text><text x="20" y="140" class="label-soft">bound elsewhere</text><rect x="245" y="90" width="190" height="32" class="fill-ground stroke"/><text x="340" y="111" text-anchor="middle" class="label">agent.persona_reflection</text><rect x="335" y="37" width="10" height="10" class="fill-red"/><line x1="340" y1="42" x2="340" y2="79" class="stroke-red"/><path d="M340 90 L334 79 L346 79 Z" class="fill-red"/><text x="340" y="146" text-anchor="middle" class="label-mark">binding</text><text x="340" y="165" text-anchor="middle" class="label-soft">declared in a praxis schema</text><rect x="484" y="90" width="190" height="32" class="fill-ground stroke"/><text x="579" y="111" text-anchor="middle" class="label">effector.journal_append</text><text x="484" y="140" class="label-soft">bound elsewhere</text></svg><figcaption>Red draws the thing it names rather than boxing it. A binding is a connector in the system, so it is a connector in the figure: a red tick from the rail into the node, squared off where it taps the rail. All three nodes are required by the same schema; only one is bound to this subject, and an unbound node is drawn unattached rather than annotated.</figcaption></figure>

### Hatch means durable, and nothing else

The 45° hatch is the only texture in the system, and reserving it to a single
meaning is what keeps it from being decoration. It is also the fact the
full-stack picture is built on.

<figure class="dia"><svg viewBox="0 0 680 130" role="img" aria-labelledby="dia-dur-t dia-dur-d"><title id="dia-dur-t">What survives, drawn as hatch</title><desc id="dia-dur-d">Three boxes in a row joined by arrows. A square Tectum event box, captioned that ttl underscore ms may drop it. A rounded Tau session box, captioned that it compacts. A hatched JMFTS documents slab, marked as the thing that survives all three.</desc><defs><pattern id="dia-hatch-dur" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><rect x="20" y="30" width="170" height="40" class="fill-ground stroke"/><text x="105" y="55" text-anchor="middle" class="label">TectumEvent</text><text x="105" y="92" text-anchor="middle" class="label-soft">ttl_ms may drop it</text><line x1="190" y1="50" x2="232" y2="50" class="stroke-soft"/><path d="M240 50 L231 46 L231 54 Z" class="fill-ash"/><rect x="240" y="30" width="170" height="40" rx="15" class="fill-ground stroke"/><text x="325" y="55" text-anchor="middle" class="label">AgentSession</text><text x="325" y="92" text-anchor="middle" class="label-soft">compacts</text><line x1="410" y1="50" x2="452" y2="50" class="stroke-soft"/><path d="M460 50 L451 46 L451 54 Z" class="fill-ash"/><rect x="460" y="30" width="170" height="40" fill="url(#dia-hatch-dur)" class="stroke"/><rect x="464" y="34" width="162" height="32" class="fill-none stroke-soft"/><rect x="505" y="41" width="80" height="18" class="fill-ground"/><text x="545" y="55" text-anchor="middle" class="label">documents</text><text x="545" y="92" text-anchor="middle" class="label-mark">survives all three</text></svg><figcaption>A Tectum event is a transient with a producer's expiry hint; a Tau session compacts as it runs. JMFTS is the only durable thing in a full-stack deployment, so it is the only hatched thing in the drawings.</figcaption></figure>

### The vocabulary

Figures are inline `<svg>`, never `<img>`: an image element cannot see the
theme tokens, so it cannot follow the skull toggle, while an inlined one
inherits the whole cascade and repaints for free. The SVG therefore carries
geometry and class names only — no color, no font, no knowledge of which
scheme it is in.

| Class | Draws |
|---|---|
| `stroke` | Structure: a rail, a node outline, a spine. |
| `stroke-hair` | Detail at the same ink, one weight down. |
| `stroke-soft` | An aside — an inner outline, a panel divider, a flow arrow between figures' subjects. |
| `stroke-red` | The one marked element. See above. |
| `stroke-dashed` | Modifier: dash pattern only, composes with any stroke. |
| `fill-none` `fill-ground` `fill-surface` | Open shape, knocked-out shape, filled shape. |
| `fill-ink` `fill-ash` `fill-red` | Solids: arrowheads, fork dots, the red tap square. |
| `hatch` | The pattern's own line. Durable storage only. |
| `label` | An identifier, quoted verbatim from the docs. |
| `label-soft` | A subject name, a caption, a gloss. |
| `label-role` | The project name in the gutter. |
| `label-mark` | The red annotation naming what red is marking. |

Stroke and fill are orthogonal, and an element usually needs one of each.
**A stroke class never declares `fill`, and a fill class never declares
`stroke`** — both would beat the SVG presentation attribute they collide with,
so a class setting `fill: none` silently erases a `fill="url(#hatch)"` on the
same element.

`label` is the one text class with no `text-transform`. Identifiers are quoted
from the reference pages and have to render exactly as they are written there;
`TectumEvent` is not `TECTUMEVENT`.

Where a label falls on hatch, it gets a `fill-ground` knockout behind it rather
than a lighter texture — the same move a dimension figure makes when it breaks
a hatched region on a real drawing.

### The accessibility contract

- `role="img"` plus `aria-labelledby` pointing at a `<title>` and a `<desc>`.
  The title names the figure; the desc is the prose a reader gets *instead of*
  the picture, so it describes the arrangement, not the file.
- Shape and label always carry the meaning. Color is a second channel, never
  the only one — which is the same rule the [state badges](#documentation-state)
  and underlined links follow.
- Every `<pattern>` needs a document-unique `id`, because two figures on one
  page share one DOM.
- Below `34rem` the figure scrolls sideways instead of scaling down. A diagram
  shrunk to phone width is not a smaller diagram, it is an unreadable one.

## What was deliberately dropped

The homepage carries some Vue-scaffold leftovers that are not part of the
identity:

- `#007BFF` Bootstrap blue on project links — a second accent competing with red.
- `#2C3E50` on nav links — Vue CLI's default.
- Three unrelated greys (`#555`, `#363636`, `#CCC`) with no scale between them,
  replaced by the ash/hairline/surface tokens.
- `text-align: center` applied globally, which is wrong for body copy.

## Writing

Match the homepage's register: plain, dry, specific. "Loyal automatons for the
inevitable machine uprising" is the tone — wry, never padded.

- Say what a thing does, not how impressive it is.
- Name things the way a reader controls them, not the way the system is built.
- An unwritten page says it is unwritten. It does not pretend to have content.
