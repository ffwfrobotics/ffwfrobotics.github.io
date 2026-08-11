---
title: "Tectum"
kind: "project"
version: "0.1.0"
---

# Tectum

Tectum is a schema-driven event substrate. Nodes attached to a substrate exchange immutable events over NATS subjects, and the orchestration between them lives in declarative schema documents rather than in Python wiring.

## Where to start

The four categories below are a crosswalk, not a sequence. Pick the
cell you are actually in.

<div class="crosswalk">
  <div class="crosswalk__corner"></div>
  <div class="crosswalk__axis crosswalk__axis--col">Acquisition</div>
  <div class="crosswalk__axis crosswalk__axis--col">Application</div>

  <div class="crosswalk__axis crosswalk__axis--row">Action</div>
  <div class="crosswalk__cell">
    <h3><a href="tutorials/">Tutorials</a></h3>
    <span class="crosswalk__coord">Action × Acquisition</span>
    <p>A guided build that teaches the concepts as you go. Start at the quickstart and keep going.</p>
  </div>
  <div class="crosswalk__cell">
    <h3><a href="cookbook/">Cookbook</a></h3>
    <span class="crosswalk__coord">Action × Application</span>
    <p>Recipes for one specific job, for someone who already knows the basics and wants the steps without the narration.</p>
  </div>

  <div class="crosswalk__axis crosswalk__axis--row">Cognition</div>
  <div class="crosswalk__cell">
    <h3><a href="devops/">DevOps Manual</a></h3>
    <span class="crosswalk__coord">Cognition × Acquisition</span>
    <p>How the system is deployed and operated, and why it is shaped that way. Read this before you run it in anger.</p>
  </div>
  <div class="crosswalk__cell">
    <h3><a href="reference/">Reference</a></h3>
    <span class="crosswalk__coord">Cognition × Application</span>
    <p>API surface, config, schemas, invariants. Built for search and lookup, not for reading start to finish.</p>
  </div>
</div>
