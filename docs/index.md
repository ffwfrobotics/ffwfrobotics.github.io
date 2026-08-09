# FFWF Robotics Docs

Documentation for three projects, each organized the same way.

## The four-category layout

Every project below is documented along two axes: how much depth you want, and
whether you're learning the system or already know it and just need to get
something done.

|                | **Fast**       | **In-depth** |
|----------------|-----------------|--------------|
| **Learning**   | Quickstart      | Tutorial     |
| **Self-guided**| Cookbook        | Reference    |

- **Quickstart** — smallest path to seeing it work.
- **Tutorial** — guided walkthrough that teaches the concepts.
- **Cookbook** — task-oriented recipes, assumes familiarity.
- **Reference** — exhaustive, lookup-oriented material.

(In the spirit of [Diátaxis](https://diataxis.fr/), adapted to this fast/in-depth ×
learning/self-guided split.)

## Projects

- **[Tectum](tectum/quickstart.md)** — a schema-driven cognitive event
  substrate: nodes on substrates exchange immutable events over NATS
  subjects, orchestrated by declarative schema documents.
- **[Tau](tau/quickstart.md)** — a programmable coding agent harness; a
  headless-first agent library with an optional TUI, Python-native
  extensions.
- **[JMFTS](jmfts/quickstart.md)** — a research-focused retrieval appliance
  combining matryoshka embeddings, ColBERT-style late interaction, and BM25
  hybrid search over PostgreSQL with pgvector.

!!! info "Status"
    This site is scaffolding. Structure and navigation are in place; category
    pages are stubs awaiting real content per project.
