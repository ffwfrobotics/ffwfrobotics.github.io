"""Frontmatter-driven page generation for the FFWF docs site.

Two markers are expanded at build time:

    <!-- docstate-table -->      per-project documentation state table
    <!-- integration-cards -->   roster of cross-project integration pages

Both read their data from the frontmatter of the pages they describe, so a
page's state is declared in exactly one place: the page itself. Nothing here
falls back to a default. A page with a missing or misspelled ``status`` fails
the build, because a state table that quietly reports the wrong thing is worse
than no state table.

Frontmatter contract
--------------------

Project index (``docs/<project>/index.md``)::

    kind: project
    title: Tectum
    version: 0.1.0
    repo: owner/name      # optional; omit for projects not hosted on GitHub

Category page (``docs/<project>/<category>.md`` or ``<category>/index.md``)::

    category: tutorials | cookbook | devops | reference
    status: stub | outdated | draft | stable

Integration page (``docs/integrations/<name>.md``)::

    kind: integration
    title: Tectum + Tau
    summary: One sentence.
    projects: [tectum, tau]
    status: stub
"""

import posixpath
from pathlib import Path

from mkdocs.exceptions import PluginError
from mkdocs.utils.meta import get_data

DOCSTATE_MARKER = "<!-- docstate-table -->"
INTEGRATION_MARKER = "<!-- integration-cards -->"

# Column order of the state table, and the only category slugs recognised.
CATEGORIES = (
    ("tutorials", "Tutorials"),
    ("cookbook", "Cookbook"),
    ("devops", "DevOps Manual"),
    ("reference", "Reference"),
)

# Grey reads as "nothing here", red as "actively wrong", yellow as "in hand",
# green as "trust it".
STATE_COLORS = {
    "stub": "grey",
    "outdated": "red",
    "draft": "yellow",
    "stable": "green",
}


# --- frontmatter ----------------------------------------------------------


def _load(path):
    _, data = get_data(path.read_text(encoding="utf-8"))
    return data


def _require(data, key, path):
    value = data.get(key)
    if value in (None, ""):
        raise PluginError(f"{path}: frontmatter is missing required key '{key}'")
    return value


def _require_status(data, path):
    status = _require(data, "status", path)
    if status not in STATE_COLORS:
        valid = " | ".join(STATE_COLORS)
        raise PluginError(f"{path}: status '{status}' is not one of: {valid}")
    return status


# --- discovery ------------------------------------------------------------


def _nav_paths(nav):
    """Flatten the configured nav into an ordered list of source paths."""
    found = []

    def walk(node):
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(nav)
    return found


def _nav_rank(nav_paths, src_path):
    """Position of a page in the nav, so generated lists match the sidebar."""
    for rank, path in enumerate(nav_paths):
        if path == src_path:
            return rank
    raise PluginError(f"{src_path}: not listed in mkdocs.yml nav")


def _category_page(project_dir, slug):
    """A category is either a single page or a directory with an index."""
    for candidate in (project_dir / f"{slug}.md", project_dir / slug / "index.md"):
        if candidate.exists():
            return candidate
    raise PluginError(
        f"{project_dir.name}: no page for category '{slug}' "
        f"(expected {slug}.md or {slug}/index.md)"
    )


def _collect(config):
    docs_dir = Path(config["docs_dir"])
    nav_paths = _nav_paths(config["nav"])

    projects = {}
    integrations = []

    for path in sorted(docs_dir.rglob("*.md")):
        data = _load(path)
        kind = data.get("kind")
        if kind is None:
            continue

        src_path = path.relative_to(docs_dir).as_posix()
        rank = _nav_rank(nav_paths, src_path)

        if kind == "project":
            slug = path.parent.name
            categories = {}
            for category, _label in CATEGORIES:
                page = _category_page(path.parent, category)
                page_data = _load(page)
                declared = _require(page_data, "category", page)
                if declared != category:
                    raise PluginError(
                        f"{page}: category '{declared}' does not match its "
                        f"location ('{category}')"
                    )
                categories[category] = {
                    "status": _require_status(page_data, page),
                    "url": page.parent.relative_to(docs_dir).as_posix()
                    if page.name == "index.md"
                    else page.with_suffix("").relative_to(docs_dir).as_posix(),
                }
            projects[slug] = {
                "rank": rank,
                "slug": slug,
                "title": _require(data, "title", path),
                "version": str(_require(data, "version", path)),
                "repo": data.get("repo"),
                "url": slug,
                "categories": categories,
            }

        elif kind == "integration":
            integrations.append(
                {
                    "rank": rank,
                    "title": _require(data, "title", path),
                    "summary": _require(data, "summary", path),
                    "projects": _require(data, "projects", path),
                    "status": _require_status(data, path),
                    "url": path.with_suffix("").relative_to(docs_dir).as_posix(),
                }
            )

        else:
            raise PluginError(f"{path}: unknown kind '{kind}'")

    if not projects:
        raise PluginError("no pages with 'kind: project' found under docs/")

    for entry in integrations:
        for slug in entry["projects"]:
            if slug not in projects:
                raise PluginError(
                    f"{entry['title']}: lists unknown project '{slug}'"
                )

    return (
        sorted(projects.values(), key=lambda p: p["rank"]),
        {p["slug"]: p for p in projects.values()},
        sorted(integrations, key=lambda i: i["rank"]),
    )


# --- rendering ------------------------------------------------------------


def _href(target, page_url):
    """Directory-URL link to *target*, relative to the page doing the linking."""
    start = page_url.rstrip("/") or "."
    return posixpath.relpath(target, start) + "/"


def _state(status, href=None):
    color = STATE_COLORS[status]
    if href is None:
        return f'<span class="state state--{color}">{status}</span>'
    return f'<a class="state state--{color}" href="{href}">{status}</a>'


def _version(project):
    """Link the version to its release only when there is one to link to."""
    version = project["version"]
    repo = project["repo"]
    if repo is None:
        return f'<span class="docstate__version">{version}</span>'
    if repo.count("/") != 1:
        raise PluginError(
            f"{project['slug']}: repo '{repo}' is not in owner/name form"
        )
    url = f"https://github.com/{repo}/releases/tag/{version}"
    return f'<a class="docstate__version" href="{url}">{version}</a>'


def _docstate_table(projects, page_url):
    heads = "".join(f"<th>{label}</th>" for _slug, label in CATEGORIES)
    rows = []
    for project in projects:
        cells = []
        for slug, _label in CATEGORIES:
            category = project["categories"][slug]
            cells.append(
                f'<td>{_state(category["status"], _href(category["url"], page_url))}</td>'
            )
        rows.append(
            "<tr>"
            f'<th scope="row"><a href="{_href(project["url"], page_url)}">'
            f'{project["title"]}</a></th>'
            f"<td>{_version(project)}</td>"
            + "".join(cells)
            + "</tr>"
        )
    return (
        '<div class="docstate">\n<table>\n'
        f"<thead><tr><th>Project</th><th>Version</th>{heads}</tr></thead>\n"
        "<tbody>\n" + "\n".join(rows) + "\n</tbody>\n</table>\n</div>"
    )


def _integration_cards(integrations, by_slug, page_url):
    cards = []
    for entry in integrations:
        badges = [
            f'<a class="chip" href="{_href(by_slug[slug]["url"], page_url)}">'
            f'{by_slug[slug]["title"]}</a>'
            for slug in entry["projects"]
        ]
        badges.append(_state(entry["status"]))
        cards.append(
            '  <div class="roster__item">\n'
            f'    <h3><a href="{_href(entry["url"], page_url)}">{entry["title"]}</a></h3>\n'
            f'    <p>{entry["summary"]}</p>\n'
            f'    <div class="roster__badges">{"".join(badges)}</div>\n'
            "  </div>"
        )
    return '<div class="roster">\n' + "\n".join(cards) + "\n</div>"


# --- hook -----------------------------------------------------------------


def on_page_markdown(markdown, page, config, files, **kwargs):
    wants_docstate = DOCSTATE_MARKER in markdown
    wants_integrations = INTEGRATION_MARKER in markdown
    if not (wants_docstate or wants_integrations):
        return None

    projects, by_slug, integrations = _collect(config)

    if wants_docstate:
        markdown = markdown.replace(
            DOCSTATE_MARKER, _docstate_table(projects, page.url)
        )
    if wants_integrations:
        markdown = markdown.replace(
            INTEGRATION_MARKER,
            _integration_cards(integrations, by_slug, page.url),
        )
    return markdown
