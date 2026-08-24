---
title: "Tau"
kind: "project"
version: "v0.9.3"
repo: "jmccardle/tau"
---

# Tau

Tau is a hackable coding agent harness for CLI, TUI, or RPC. Extensions are Python. A session is a tree you can branch; context is a walk of it.

<figure class="dia"><svg viewBox="0 0 680 362" role="img" aria-labelledby="dia-tau-t dia-tau-d"><title id="dia-tau-t">Everything reaches Tau through one method</title><desc id="dia-tau-d">Tau sits at the centre as a rounded pill labelled AgentSession. Five inputs converge on it from the left — a Tectum agent node named agent dot persona underscore reflection, the tau TUI, tau dash p, the SDK's create underscore agent underscore session, and an extension's api dot submit — and every one lands on the same red bar marked submit before a single arrow enters the session. Above, a Tectum subject rail feeds the agent node, and a second rail carries the session's speak tool back out onto the bus. To the right the spine continues past the pill, forks at a filled dot, and splits into a solid branch that extends the active leaf and a dashed one left behind as an abandoned sibling. Below, two hatched slabs are the two places a session can be stored: a plain slab for a JSONL file under tilde slash dot tau slash sessions, and a doubled JMFTS slab where each entry becomes a document alongside the rest of the corpus.</desc><defs><pattern id="dia-hatch-tau" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="4" y1="0" x2="4" y2="8" class="hatch"/></pattern></defs><text x="0" y="36" class="label-soft">events.sensation.audio.filtered</text><line x1="0" y1="48" x2="300" y2="48" class="stroke"/><path d="M300 48 L291 44 L291 52 Z" class="fill-ink"/><text x="380" y="36" class="label-soft">events.workspace.persona_reflection.out.speak</text><line x1="380" y1="48" x2="668" y2="48" class="stroke"/><path d="M668 48 L659 44 L659 52 Z" class="fill-ink"/><line x1="100" y1="48" x2="100" y2="90" class="stroke"/><path d="M100 98 L96 89 L104 89 Z" class="fill-ink"/><rect x="0" y="98" width="200" height="28" class="fill-ground stroke"/><text x="100" y="117" text-anchor="middle" class="label">agent.persona_reflection</text><rect x="0" y="140" width="200" height="28" class="fill-ground stroke-hair"/><text x="100" y="159" text-anchor="middle" class="label">tau</text><rect x="0" y="182" width="200" height="28" class="fill-ground stroke-hair"/><text x="100" y="201" text-anchor="middle" class="label">tau -p</text><rect x="0" y="224" width="200" height="28" class="fill-ground stroke-hair"/><text x="100" y="243" text-anchor="middle" class="label">create_agent_session</text><rect x="0" y="266" width="200" height="28" class="fill-ground stroke-hair"/><text x="100" y="285" text-anchor="middle" class="label">api.submit()</text><path d="M200 112 H236 V180 H244" class="stroke-hair fill-none"/><path d="M252 180 L244 176.5 L244 183.5 Z" class="fill-ink"/><path d="M200 154 H224 V188 H244" class="stroke-hair fill-none"/><path d="M252 188 L244 184.5 L244 191.5 Z" class="fill-ink"/><path d="M200 196 H244" class="stroke-hair fill-none"/><path d="M252 196 L244 192.5 L244 199.5 Z" class="fill-ink"/><path d="M200 238 H224 V204 H244" class="stroke-hair fill-none"/><path d="M252 204 L244 200.5 L244 207.5 Z" class="fill-ink"/><path d="M200 280 H236 V212 H244" class="stroke-hair fill-none"/><path d="M252 212 L244 208.5 L244 215.5 Z" class="fill-ink"/><rect x="252" y="172" width="8" height="48" class="fill-red"/><path d="M256 220 V234 H266" class="stroke-red fill-none"/><text x="270" y="238" class="label">submit()</text><text x="270" y="256" class="label-mark">one door</text><line x1="260" y1="196" x2="275" y2="196" class="stroke"/><path d="M284 196 L275 192 L275 200 Z" class="fill-ink"/><rect x="284" y="176" width="180" height="40" rx="20" class="fill-ground stroke"/><text x="374" y="201" text-anchor="middle" class="label">AgentSession</text><line x1="464" y1="196" x2="540" y2="196" class="stroke"/><circle cx="540" cy="196" r="4" class="fill-ink"/><path d="M540 196 V166 H660" class="stroke-hair fill-none"/><text x="548" y="158" class="label-soft">extends the leaf</text><path d="M540 196 V226 H660" class="stroke-hair stroke-dashed fill-none"/><text x="548" y="242" class="label-soft">abandoned sibling</text><path d="M430 176 V56" class="stroke-hair fill-none"/><path d="M430 48 L426 57 L434 57 Z" class="fill-ink"/><text x="438" y="118" class="label-soft">tool: speak</text><path d="M345 216 V290" class="stroke-soft fill-none"/><path d="M345 298 L341 289 L349 289 Z" class="fill-ash"/><text x="351" y="288" class="label-soft">--store file</text><path d="M400 216 V254 H575 V268" class="stroke-soft fill-none"/><path d="M575 276 L571 267 L579 267 Z" class="fill-ash"/><text x="408" y="248" class="label-soft">--store jmfts</text><rect x="250" y="298" width="190" height="32" fill="url(#dia-hatch-tau)" class="stroke"/><rect x="287" y="304" width="116" height="18" class="fill-ground"/><text x="345" y="318" text-anchor="middle" class="label">~/.tau/sessions</text><text x="0" y="318" class="label-soft">every input source</text><text x="250" y="348" class="label-soft">a JSONL file per session</text><rect x="470" y="276" width="190" height="22" class="fill-ground stroke-hair"/><text x="565" y="291" text-anchor="middle" class="label-soft">documents</text><rect x="470" y="298" width="190" height="32" fill="url(#dia-hatch-tau)" class="stroke"/><rect x="474" y="302" width="182" height="24" class="fill-none stroke-soft"/><rect x="503" y="304" width="124" height="18" class="fill-ground"/><text x="565" y="318" text-anchor="middle" class="label">tau:conversation</text><text x="470" y="348" class="label-soft">an entry is a document</text></svg><figcaption>Everything that can drive Tau — a Tectum agent node holding the session open over RPC, the TUI, a headless run, the SDK, an extension — arrives at the same method. What comes back out is a tree rather than a log: the spine forks, and a rollback leaves the abandoned branch on disk instead of deleting it. The substrate above hears the turn's result as an ordinary event. The store below is a flag, and pointing it at JMFTS files every entry as a document beside the rest of the corpus.</figcaption></figure>

## Install

```bash
pip install ffwf-tau
```

Then run `tau`. The meta package pulls in the TUI; the bare
`ffwf-tau-coding-agent` package is CLI and RPC only. The `ffwf-` prefix is
required — `tau-ai` and `tau-llm` on PyPI are unrelated projects. The
[DevOps Manual](devops.md#install) covers the extras and the second command
name.

Out of the box τ talks to any OpenAI-compatible endpoint, local or hosted.
Anthropic and Google are two more extras — `ffwf-tau-llm[anthropic]` and
`ffwf-tau-llm[google]` — and both import only when a model actually names
them.

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
    <p>Guided builds. Concepts as you go, quickstart first.</p>
  </div>
  <div class="crosswalk__cell">
    <h3><a href="cookbook/">Cookbook</a></h3>
    <span class="crosswalk__coord">Action × Application</span>
    <p>Recipes for one job. Step by step.</p>
  </div>

  <div class="crosswalk__axis crosswalk__axis--row">Cognition</div>
  <div class="crosswalk__cell">
    <h3><a href="devops/">DevOps Manual</a></h3>
    <span class="crosswalk__coord">Cognition × Acquisition</span>
    <p>Deployment, operation, and why it's like that.</p>
  </div>
  <div class="crosswalk__cell">
    <h3><a href="reference/">Reference</a></h3>
    <span class="crosswalk__coord">Cognition × Application</span>
    <p>API, config, schemas. Unfiltered lookup by module or endpoint.</p>
  </div>
</div>
