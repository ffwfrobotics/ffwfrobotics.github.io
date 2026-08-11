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
