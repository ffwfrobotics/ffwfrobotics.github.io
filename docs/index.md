# FFWF Robotics

Documentation for three projects, each organized the same way.

## Find your quadrant

Depth runs left to right. What you came here to do runs top to bottom. Pick the
cell you're actually in — the categories are a crosswalk, not a sequence, and
there's no order you're supposed to read them in.

<div class="crosswalk">
  <div class="crosswalk__corner"></div>
  <div class="crosswalk__axis crosswalk__axis--col">Fast</div>
  <div class="crosswalk__axis crosswalk__axis--col">In-depth</div>

  <div class="crosswalk__axis crosswalk__axis--row">Learning</div>
  <div class="crosswalk__cell">
    <h3>Quickstart</h3>
    <span class="crosswalk__coord">Fast × Learning</span>
    <p>The smallest path to seeing it run. No explanation of why — just enough
    to confirm it works on your machine.</p>
    <div class="crosswalk__links">
      <a href="tectum/quickstart/">Tectum</a>
      <a href="tau/quickstart/">Tau</a>
      <a href="jmfts/quickstart/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Tutorial</h3>
    <span class="crosswalk__coord">In-depth × Learning</span>
    <p>A guided build that teaches the concepts as you go. Assumes you've never
    seen the system before.</p>
    <div class="crosswalk__links">
      <a href="tectum/tutorial/">Tectum</a>
      <a href="tau/tutorial/">Tau</a>
      <a href="jmfts/tutorial/">JMFTS</a>
    </div>
  </div>

  <div class="crosswalk__axis crosswalk__axis--row">Self-guided</div>
  <div class="crosswalk__cell">
    <h3>Cookbook</h3>
    <span class="crosswalk__coord">Fast × Self-guided</span>
    <p>Recipes for one specific job, for people who already know the basics and
    want the steps without the narration.</p>
    <div class="crosswalk__links">
      <a href="tectum/cookbook/">Tectum</a>
      <a href="tau/cookbook/">Tau</a>
      <a href="jmfts/cookbook/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Reference</h3>
    <span class="crosswalk__coord">In-depth × Self-guided</span>
    <p>API surface, config, schemas, invariants. Built for search and lookup,
    not for reading start to finish.</p>
    <div class="crosswalk__links">
      <a href="tectum/reference/">Tectum</a>
      <a href="tau/reference/">Tau</a>
      <a href="jmfts/reference/">JMFTS</a>
    </div>
  </div>
</div>

The split follows [Diátaxis](https://diataxis.fr/), read here as depth against
intent.

## The projects

<div class="roster">
  <div class="roster__item">
    <h3>Tectum</h3>
    <p>A schema-driven event substrate. Nodes on substrates exchange immutable
    events over NATS subjects, and orchestration lives in declarative schema
    documents rather than Python wiring.</p>
  </div>
  <div class="roster__item">
    <h3>Tau</h3>
    <p>A programmable coding agent harness. Headless-first agent library with an
    optional TUI, Python-native extensions, and sessions stored as a tree rather
    than a flat chat log.</p>
  </div>
  <div class="roster__item">
    <h3>JMFTS</h3>
    <p>A retrieval appliance combining matryoshka embeddings, ColBERT-style late
    interaction, and BM25 hybrid search over PostgreSQL with pgvector.</p>
  </div>
</div>

!!! warning "This site is scaffolding"
    Navigation and styling are in place. The twelve category pages are stubs —
    no content has been written for them yet.
