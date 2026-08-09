# ffwfrobotics.github.io

Source for the FFWF Robotics documentation site, built with
[MkDocs](https://www.mkdocs.org/) + [Material](https://squidfunk.github.io/mkdocs-material/).
Deployed as a GitHub user site at `https://ffwfrobotics.github.io/`.

## Layout

Docs for each project are organized into the same four categories:

| Category   | Axis                          |
|------------|--------------------------------|
| Quickstart | Fast + learning-oriented       |
| Tutorial   | In-depth + learning-oriented   |
| Cookbook   | Fast + self-guided             |
| Reference  | In-depth + self-guided         |

```
docs/
  index.md          # landing page
  tectum/            {quickstart,tutorial,cookbook,reference}.md
  tau/               {quickstart,tutorial,cookbook,reference}.md
  jmfts/             {quickstart,tutorial,cookbook,reference}.md
mkdocs.yml          # nav + theme config
```

Category pages currently ship as stubs (clearly marked "Not yet written") —
structure first, content per project as a follow-up pass.

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

1. Add a directory under `docs/<project>/` with the four category files.
2. Add the corresponding section to `nav:` in `mkdocs.yml`.
3. Link it from `docs/index.md`.
