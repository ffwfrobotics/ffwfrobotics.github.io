# FFWF Robotics

*Loyal automatons for the inevitable machine uprising.*

Documentation for the FFwF agentic software stack.

## The projects

<div class="roster">
  <div class="roster__item">
    <h3><a href="tectum/">Tectum</a></h3>
    <p>Event substrate orchestrated with schema documents. Manage shared nodes
    by activating a task definition.</p>
    <div class="roster__badges">
      <a class="chip" href="tectum/tutorials/quickstart/">Quickstart</a>
    </div>
  </div>
  <div class="roster__item">
    <h3><a href="tau/">Tau</a></h3>
    <p>Hackable coding agent harness for CLI, TUI, or RPC. Extensions are
    Python. Sessions are a tree, context is a walk of it.</p>
    <div class="roster__badges">
      <a class="chip" href="tau/tutorials/quickstart/">Quickstart</a>
    </div>
  </div>
  <div class="roster__item">
    <h3><a href="jmfts/">JMFTS</a></h3>
    <p>Retrieval appliance. Matryoshka embeddings, ColBERT late interaction, and
    BM25, fused into one hybrid search on Postgres. The only durable store.</p>
    <div class="roster__badges">
      <a class="chip" href="jmfts/tutorials/quickstart/">Quickstart</a>
    </div>
  </div>
</div>

## Find your quadrant

Two axes, four quadrants. **Action** or **Cognition** — what to do, or why to
do it. **Application** or **Acquisition** — how to do it, or what's possible.

<div class="crosswalk">
  <div class="crosswalk__corner"></div>
  <div class="crosswalk__axis crosswalk__axis--col">Acquisition</div>
  <div class="crosswalk__axis crosswalk__axis--col">Application</div>

  <div class="crosswalk__axis crosswalk__axis--row">Action</div>
  <div class="crosswalk__cell">
    <h3>Tutorials</h3>
    <span class="crosswalk__coord">Action × Acquisition</span>
    <p>Guided builds. Concepts as you go, quickstart first.</p>
    <div class="crosswalk__links">
      <a href="tectum/tutorials/">Tectum</a>
      <a href="tau/tutorials/">Tau</a>
      <a href="jmfts/tutorials/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Cookbook</h3>
    <span class="crosswalk__coord">Action × Application</span>
    <p>Recipes for one job. Step by step.</p>
    <div class="crosswalk__links">
      <a href="tectum/cookbook/">Tectum</a>
      <a href="tau/cookbook/">Tau</a>
      <a href="jmfts/cookbook/">JMFTS</a>
    </div>
  </div>

  <div class="crosswalk__axis crosswalk__axis--row">Cognition</div>
  <div class="crosswalk__cell">
    <h3>DevOps Manual</h3>
    <span class="crosswalk__coord">Cognition × Acquisition</span>
    <p>Deployment, operation, and why it's like that.</p>
    <div class="crosswalk__links">
      <a href="tectum/devops/">Tectum</a>
      <a href="tau/devops/">Tau</a>
      <a href="jmfts/devops/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Reference</h3>
    <span class="crosswalk__coord">Cognition × Application</span>
    <p>API, config, schemas. Unfiltered lookup by module or endpoint.</p>
    <div class="crosswalk__links">
      <a href="tectum/reference/">Tectum</a>
      <a href="tau/reference/">Tau</a>
      <a href="jmfts/reference/">JMFTS</a>
    </div>
  </div>
</div>

Inspired by [Diátaxis](https://diataxis.fr/).

## Documentation state

Every page declares its own state in frontmatter. This table is generated from
those declarations at build time, so it cannot drift from the pages it reports
on.

<!-- docstate-table -->

<span class="state state--grey">stub</span> nothing written ·
<span class="state state--red">outdated</span> written, now wrong ·
<span class="state state--yellow">draft</span> usable, incomplete ·
<span class="state state--green">stable</span> trust it
{: .state-legend }

## Integrations

Each project stands on its own. These cover what happens at the seams.

<!-- integration-cards -->
