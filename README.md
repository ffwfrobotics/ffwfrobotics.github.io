# ffwfrobotics.github.io

Source for the FFWF Robotics documentation site, built with
[MkDocs](https://www.mkdocs.org/) + [Material](https://squidfunk.github.io/mkdocs-material/).
Deployed as a GitHub user site at `https://ffwfrobotics.github.io/`.

## Layout

Docs for each project are organized into the same four categories, on the
[Diátaxis](https://diataxis.fr/) axes:

|               | Acquisition (studying) | Application (working) |
|---------------|------------------------|-----------------------|
| **Action**    | Tutorials              | Cookbook              |
| **Cognition** | DevOps Manual          | Reference             |

```
docs/
  index.md              # landing page
  <project>/
    index.md            # kind: project — intro + the 2x2 for that project
    tutorials/
      index.md          # quickstart is the first tutorial
      quickstart.md
    cookbook.md
    devops.md
    reference.md
  integrations/         # cross-project pages, kind: integration
  style-guide.md
hooks/docstate.py       # expands the state table and integration roster
mkdocs.yml              # nav + theme config
```

Every page ships as a stub (clearly marked "Not yet written") — structure
first, content per project as a follow-up pass.

## Documentation state

Each category page declares `status: stub|outdated|draft|stable` in its own
frontmatter; project index pages declare `version` and, when the project is on
GitHub, `repo: owner/name`. `hooks/docstate.py` reads those declarations and
generates the state table on the home page, so there is no second list to keep
in sync.

A missing or misspelled `status` fails the build. The full frontmatter contract
is documented at the top of `hooks/docstate.py` and in `docs/style-guide.md`.

## Styling

The visual system is derived from the FFwF Robotics homepage: red as the only
accent, Courier New as the machine voice, dark by default. Tokens live in
`docs/stylesheets/ffwf.css`; `docs/style-guide.md` documents them with live
examples and records what was deliberately dropped from the homepage.

No webfonts are fetched — the site is self-contained.

## Local dev

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/mkdocs serve      # http://127.0.0.1:8000 with live reload
./.venv/bin/mkdocs build      # renders static site/ (gitignored)
```

## Deploy

`.github/workflows/deploy.yml` runs `mkdocs gh-deploy --force` on every push to
`main`, which builds the site and force-pushes it to the `gh-pages` branch.

**One-time repo setup:** in Settings → Pages, set the source to the
`gh-pages` branch (created by the first successful workflow run).

## Adding a new project

1. Create `docs/<project>/index.md` with `kind: project`, `title`, `version`,
   and optionally `repo`.
2. Add the four category pages, each with `category` and `status`.
3. Add the section to `nav:` in `mkdocs.yml` — the state table orders projects
   by their nav position.
4. Add a card to "The projects" on `docs/index.md`, and a link per quadrant in
   the crosswalk.

The state table and the integration roster pick the project up on their own.
