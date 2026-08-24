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

Two questions decide where you should be. Are you **acting** on the system or
trying to **understand** it? And are you here to **study**, or do you have a job
in front of you right now?

<div class="crosswalk">
  <div class="crosswalk__corner"></div>
  <div class="crosswalk__axis crosswalk__axis--col">Acquisition</div>
  <div class="crosswalk__axis crosswalk__axis--col">Application</div>

  <div class="crosswalk__axis crosswalk__axis--row">Action</div>
  <div class="crosswalk__cell">
    <h3>Tutorials</h3>
    <span class="crosswalk__coord">Action × Acquisition</span>
    <p>A guided build that teaches the concepts as you go. Start at the
    quickstart and keep going.</p>
    <div class="crosswalk__links">
      <a href="tectum/tutorials/">Tectum</a>
      <a href="tau/tutorials/">Tau</a>
      <a href="jmfts/tutorials/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Cookbook</h3>
    <span class="crosswalk__coord">Action × Application</span>
    <p>Recipes for one specific job, for someone who already knows the basics
    and wants the steps without the narration.</p>
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
    <p>How the system is deployed and operated, and why it is shaped that way.
    Read this before you run it in anger.</p>
    <div class="crosswalk__links">
      <a href="tectum/devops/">Tectum</a>
      <a href="tau/devops/">Tau</a>
      <a href="jmfts/devops/">JMFTS</a>
    </div>
  </div>
  <div class="crosswalk__cell">
    <h3>Reference</h3>
    <span class="crosswalk__coord">Cognition × Application</span>
    <p>API surface, config, schemas, invariants. Built for search and lookup,
    not for reading start to finish.</p>
    <div class="crosswalk__links">
      <a href="tectum/reference/">Tectum</a>
      <a href="tau/reference/">Tau</a>
      <a href="jmfts/reference/">JMFTS</a>
    </div>
  </div>
</div>

The split is [Diátaxis](https://diataxis.fr/). It is a crosswalk, not a
sequence — there is no order you are supposed to read the four in.

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
