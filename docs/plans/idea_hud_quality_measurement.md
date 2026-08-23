---
status: active
layer: frontend
authority: P2
audience: developer
maturity: idea
date: 2026-08-23
tags: [idea, hud, design-system, testing]
---

# Idea: HUD Quality Measurement — A Third Sibling to SimQ and Visual-Quality Validation

> **Maturity: IDEA** — Not scheduled. This doc formalizes metric-model research done alongside
> `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION` (M1 of `docs/plans/hud_delivery_roadmap.md`) and its
> child ticket `TCK-20260822-HUD-BASELINE-MEASUREMENT`, plus new research into simulated-interaction
> testing that goes beyond what any current ticket scopes. It exists so M1's baseline ticket and M4
> (`TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT`) have a concrete metric model and a real,
> internally-precedented shape to draw from when they're eventually broken into child tickets — it does
> not itself create or modify any ticket, and M4 stays gated exactly as the roadmap already states.

---

## Problem

`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s own scope item 5 (`TCK-20260822-HUD-BASELINE-MEASUREMENT`)
requires "a baseline measurement result... recorded and dated" but leaves the actual metric model
unspecified — deliberately, since the epic ticket itself only commits to *recording* a baseline, not to a
full scoring system. M4 (`TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT`) needs to "run M1's own metrics
rubric... producing a real scored result" but was written before any concrete rubric existed.

This project has already solved an almost structurally identical problem twice — for simulation-behavior
quality (SimQ, `docs/simulation_quality/quality_scoring_contract.md`) and for world-rendering visual/
geometric quality (`docs/plans/world_rendering/idea_world_render_validation.md`, shipped as
`TCK-20260821-VISUAL-CONNECTIVITY-METRIC` and `TCK-20260821-VISUAL-DENSITY-METRIC`, both DONE) — but
neither precedent has been explicitly adapted for HUD/observer-usability quality. Checked directly: no
existing doc under `docs/plans/`, `docs/testing/`, or `docs/architecture/` has previously considered
simulating a player's *physical* interaction with the frontend (cursor movement, click accuracy, screen
size, gaze/attention) — this is genuinely new ground for this repo, not a rediscovery of an existing plan.

## Idea, Part A — Reuse the proven "sibling scoring system" pattern

### Precedent, read directly

`idea_world_render_validation.md` §"Scoring: a sibling system to SimQ, not an 11th pillar" states the exact
reasoning to reuse: SimQ is architecturally event-stream-driven (`ObservabilityEventEnvelope` → scorer);
visual-quality metrics compute directly from `AuthoritativeState` geometry with no natural event to hang
them on, so forcing them into SimQ's shape would "repeat a scope-violation this project's own SimQ
investigation already identified and avoided." **HUD usability metrics are in the identical position** —
they measure a human observer's interaction with a rendered frontend, not simulation-tick events. The same
reasoning applies without modification: HUD quality should be a third sibling scoring system, reusing
SimQ's exact grade vocabulary (`S`/`A`/`B`/`C`/`D`/`F`, `docs/simulation_quality/quality_scoring_contract.md`
§4.5) for consistency, implemented independently.

### Signal shape — explicit, not assumed, per metric

`idea_world_render_validation.md` explicitly separates monotonic signals (SimQ's classic "more activity is
healthier") from **healthy-band** signals (fill-ratio, clustering-CV — both a near-perfect rectangle and
scattered noise are penalized). HUD metrics need the same explicit classification per family, not a
blanket assumption:

| Family | Metric | Signal shape |
|---|---|---|
| **Findability** | Time-to-locate a named entity/event; completion rate (HEART framework's Task Success decomposition — completion rate, error rate, time-on-task) | Monotonic — lower time / higher completion is better |
| **Detection** | Time from an event occurring to the observer noticing it | Monotonic |
| **Context Preservation** | Binary per-workflow: does switching panels/modes lose prior selection, scroll position, or active tab? | Monotonic — directly measures whether `TCK-20260822-EPIC-HUD-CORE-PANEL-WIRING`'s child ticket `TCK-20260822-DURABLE-SELECTION-STATE` actually fixed the confirmed `Sidebar.tsx:43-49` bug |
| **Density Legibility** | Fraction of glance-critical info (HP, alert status) readable without drill-down; canvas-vs-chrome screen-space ratio | **Healthy-band** — too sparse wastes space, too dense overwhelms |

**Verification note (2026-08-23):** an earlier draft of this doc cited a "~200ms glance-budget" figure and
presented the 80/20 gameplay-vs-chrome attention split as established research. Both were checked directly
against their claimed sources before this doc was finalized. The 200ms figure does not appear in any of the
three game-HUD design articles it was sourced from — it does not check out, and is dropped from this doc
rather than kept with a caveat. The 80/20 split does appear in one article, but that article itself states
it as `"research shows..."` with **no actual citation** — it is repeated design-blog folklore, not verified
research. The underlying design principle (glance-critical info should be readable without drilling in;
chrome shouldn't crowd out the canvas) is kept as a qualitative goal for the Density Legibility family, but
without a specific numeric threshold attached until this project runs its own real measurement (which is
exactly what `TCK-20260822-HUD-BASELINE-MEASUREMENT` and any later calibration ticket are for).

### Calibration and decomposition discipline

`idea_world_render_validation.md`'s own four metric families shipped as **separate tickets** —
`TCK-20260821-VISUAL-CONNECTIVITY-METRIC` and `TCK-20260821-VISUAL-DENSITY-METRIC` (both DONE), with
`TCK-20260821-VISUAL-QUALITY-CALIBRATION` (multi-seed threshold calibration) and
`TCK-20260821-VISUAL-GRADE-SCORER` (grade-combination logic) as further siblings, not folded into one
ticket. Thresholds are never hardcoded — SimQ's `tools/calibrate_simq.py` established the discipline of
calibrating against real corpus data across multiple seeds before a threshold is trusted
(`docs/simulation_quality/quality_scoring_contract.md` §4.5's own re-calibration history). **When M4
eventually gets its own child-ticket breakdown, this same split is the template**: metric-computation
ticket(s) → a calibration ticket (measured across representative workload bands — small/medium/target
~10,000-entity scale, mirroring both SimQ's multi-seed and the earlier external design review's
workload-band suggestion) → a grade-scorer ticket. Not proposed as tickets now — M4 stays gated on M3 per
`docs/plans/hud_delivery_roadmap.md`'s own sequencing rules; this is the shape to draw from once it isn't.

### The grade-scorer engine already has a real, shipped reference implementation to draw from

`TCK-20260821-VISUAL-GRADE-SCORER` is now DONE (`src/rendering/grading.py`, merged after this doc's first
draft) — not just a sibling ticket to point at anymore, a real, tested engine whose actual shape maps almost
exactly onto this doc's own monotonic-vs-healthy-band distinction (§ above), read directly from the real
code rather than inferred:

- **Hard rules** (`evaluate_hard_rule`) are a binary pass/fail delta from a config-sourced
  `HardRuleConfig(pass_delta, fail_delta)` — the exact shape for this doc's monotonic families (Findability,
  Detection, Context Preservation): either the observer succeeded or didn't, no gradient needed.
- **Soft rules** (`evaluate_soft_rule` / `_trapezoidal_delta`) implement the healthy-band shape precisely:
  a `SoftRuleConfig(low, healthy_low, healthy_high, high, peak_delta, min_delta)` — flat at `peak_delta`
  inside `[healthy_low, healthy_high]`, ramping linearly down to `min_delta` outside `[low, high]`, with
  linear interpolation in between. This is the exact real-code shape Density Legibility's "too sparse wastes
  space, too dense overwhelms" healthy-band description above was gesturing at conceptually — the real
  implementation already exists, just needs the right threshold values for HUD metrics instead of geometric
  ones.
- **Config-driven, never hardcoded**: thresholds load from `config/rendering/grade_thresholds.toml` via a
  fail-loud loader (missing/wrong-typed keys raise immediately, not silently default) — the same discipline
  this doc's own Calibration section already calls for.
- **Deliberately architecture-independent, same pattern as this doc's own Part A precedent**: `grading.py`
  does not import `src.simulation_quality`, does not subclass its `PillarScorer`, and does not register a
  `PillarId` — it copies SimQ's exact grade-threshold *values* by value, not by import, specifically to stay
  structurally independent while staying numerically consistent. If a HUD grade-scorer gets built, this is
  the concrete precedent for doing the same thing a second time, not reinventing the "how do we stay
  consistent without coupling" question from scratch.

Not proposed as an implementation plan here — `grading.py` operates on `AuthoritativeState` geometry in
Python; a HUD scorer would run against DOM/canvas measurements in TypeScript, a different runtime with no
direct code-sharing path. What transfers is the *engine shape* (hard-rule/soft-rule/config-driven/
architecture-independent), not the code itself.

## Idea, Part B — Simulated player interaction: a genuinely new direction for this project

Beyond adapting the two existing precedents, there is real, current, external research for going further
than manual/human-recorded baseline measurement (which is all `TCK-20260822-HUD-BASELINE-MEASUREMENT`
currently scopes) — simulating the *physical act* of a player using the HUD, not just the workflow steps.

### Cursor movement and click accuracy — two distinct techniques, not one

**Verification note (2026-08-23):** an earlier draft of this section conflated two separate things as if
they were the same research direction. They are related but distinct, and are kept separate here after
directly checking the actual CHI 2026 paper's abstract (the first WebFetch attempt hit an ACM 403; the
abstract itself was confirmed via a follow-up search that surfaced its real text, not assumed from the
title alone):

- **Fitts's Law** (`MT = a + b · log2(A/W + 1)`, movement time as a function of the ratio between distance
  to a target and target width) is the standard, decades-old human-computer-interaction model for
  *unconstrained* point-to-point pointing-device movement time and accuracy — in continuous use since 1954.
  This is the right fit for simple click targets (an entity row in `EntityList`, an inspector tab, a map
  pin): simulate a cursor moving from an arbitrary starting point to the target at a parameterized screen
  size/resolution and pointing-device speed, compute predicted movement time and miss probability against
  the target's actual rendered hit-area size, and flag any HUD element whose hit-area is small enough
  relative to its Fitts's-Law-predicted accuracy to be a real usability risk — catchable before any human
  ever clicks it.
- **"Simulating Human Cursor Trajectories for Path-Sensitive GUI Evaluation"** (Extended Abstracts of the
  2026 CHI Conference, not a full peer-reviewed paper) does **not** use Fitts's Law — its actual method,
  confirmed from the real abstract, is a *"parametrizable generative user simulation model... formulating
  constrained movement as a receding-horizon optimization problem using Model Predictive Contouring
  Control"* (MPCC), built specifically for interactions where the *path* the cursor takes matters, not just
  the start/end points — cascading menus and lasso selection are the paper's own worked examples. This is
  the right fit for this project's more constrained interactions (if any exist or get added — e.g. a
  drag-select on the map, a multi-step menu), not for simple single-target clicks. The paper's own claim
  (evaluated against real human data, trajectories "closely match human behavior") supports using
  simulated-trajectory testing as "a robust, in-silico alternative to human trials" specifically for
  *path-constrained* interactions — Fitts's Law remains the right tool for simple point-and-click targets.

### Screen size / resolution parameterization

Real automated-UI-testing research explicitly treats screen resolution and layout as a first-class
parameter affecting both what's visible and testing resilience (see References). Combined with Fitts's
Law's target-width term, this gives a concrete, parameterized simulated-user model: run the same simulated
click-path across a small matrix of representative screen sizes (this project doesn't yet have declared
target device classes — an open question, see below) and see whether hit-area sizes or glance-budget
legibility hold up at the smaller end, the same way `idea_world_render_validation.md`'s Tier-0/1/2 escalation
pipeline avoided assuming one config represents all real usage.

### Attention / gaze simulation — reusing this project's own agent-first pattern

Real saliency-prediction research (UEyes, and newer zero-shot vision-language-model gaze prediction) shows
a model can take a UI screenshot and predict where a human's attention would land, without training data
specific to that UI. This maps directly onto a mechanism this project has *already built and shipped* for
a different domain: `idea_world_render_validation.md`'s "Agent-first review pipeline" — an agent reviewing
a rendered image via the existing `.claude/agents/simulation-analyst.md`-shaped Data Sources → Analysis
Dimensions → Severity Classification → structured Output template. The same agent-vision mechanism that
already reviews rendered world-map images for geometric quality could review a HUD screenshot and predict
which elements draw attention first — directly testable against the Density Legibility family's glance-budget
metric above, using a capability this project has already proven works, not a new integration.

### What this is *not* proposing

Mirroring `idea_world_render_validation.md`'s own explicit scope discipline ("a fact you can look up in
data should never be approximated by looking at pixels"): simulated-interaction metrics are a **predictive,
pre-human-testing signal**, not a replacement for `TCK-20260822-HUD-BASELINE-MEASUREMENT`'s real, human-recorded
baseline. Fitts's-Law throughput and predicted click-miss probability tell you where friction is *likely*;
they do not replace an actual dated, human-observed baseline result. The two are complementary — simulated
metrics can run cheaply and often (every change), the real baseline is the ground truth they're checked
against.

## Architecture Constraints

- Must not become a fourth scoring system competing with SimQ or visual-quality validation for the same
  numeric vocabulary — reuse the grade-band math exactly, as both existing siblings already do.
- Any simulated-interaction metric (Fitts's Law throughput, predicted miss probability, agent-predicted
  gaze) is advisory/predictive only — it must never substitute for `TCK-20260822-HUD-BASELINE-MEASUREMENT`'s
  real, human-recorded baseline result, per the "not proposing" section above.
- Reuses the existing agent-vision capability already proven for `idea_world_render_validation.md`'s Tier-2
  image review — this idea adds no new agent-image-review mechanism of its own.
- Frontend-only concern (`frontend/src/**`) — no backend/`AuthoritativeState` changes implied by anything in
  this doc.

## Relationship to Planned Tickets

- `TCK-20260822-HUD-BASELINE-MEASUREMENT` — this doc's Part A metric families are a candidate source for
  that ticket's own Investigate phase when picked up; not binding, since that ticket's own AC already
  allows it to choose its own representative tasks.
- `TCK-20260822-EPIC-HUD-CONTENT-POLISH-MEASUREMENT` (M4) — this doc's full model (Part A + Part B) is the
  candidate source for M4's eventual child-ticket breakdown, once M4's hard gate (M3 done) clears. No
  ticket created or modified by this doc.
- `docs/plans/world_rendering/idea_world_render_validation.md` — the direct structural precedent this doc
  is deliberately modeled on; no scope overlap (that doc is server-side world-geometry, this is
  frontend-side HUD usability).

## Open Questions

- Exact healthy-band threshold numbers for the Density Legibility family, including whatever "glance
  budget" figure this project ends up using — no external source checked so far actually supports a
  specific number (see the verification note above), so this needs to be established from this project's
  own real measurement, via the same real-corpus-calibration discipline SimQ and visual-quality validation
  both used, not borrowed from an unverified external claim.
- This project has no declared target device/screen-size classes today (unlike, say, a mobile-first
  product) — the screen-size matrix for simulated-interaction testing needs that decided first, likely
  during `TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`'s own scope or later.
- Whether a Fitts's-Law cursor-trajectory simulator gets built as new frontend tooling, a Python
  script against rendered layout metadata, or folded into an existing test harness — not investigated here,
  a real follow-up question once this idea is picked up.
- Whether the agent-vision gaze-prediction mechanism should be a genuinely new
  `.claude/agents/hud-review.md`-shaped agent or reuse/extend the world-render-reviewer agent
  `idea_world_render_validation.md` itself leaves as an open question — likely resolved together, since
  both are "review a rendered image" agents.
- Whether representative screen sizes, cursor speeds, and click-accuracy baselines should themselves be
  drawn from real player telemetry once any exists, versus reasonable assumed defaults for now — this
  project currently has no player-input telemetry collection at all, worth flagging as a real gap if
  simulated-interaction testing is picked up before telemetry exists to validate the simulation against.

---

## References

- `docs/simulation_quality/quality_scoring_contract.md` §4.5 — SimQ's grade-band math and real
  multi-seed calibration history, the scoring-mechanics precedent this doc's Part A reuses.
- `docs/plans/world_rendering/idea_world_render_validation.md` — the direct structural precedent for
  "sibling scoring system, not a forced pillar," signal-shape classification, agent-first tiered review,
  and metric/calibration/scorer ticket decomposition.
- `TCK-20260821-VISUAL-CONNECTIVITY-METRIC`, `TCK-20260821-VISUAL-DENSITY-METRIC` — shipped, DONE examples
  of the metric-ticket decomposition pattern in practice.
- Fitts's Law (`MT = a + b · log2(A/W + 1)`) — the standard HCI model for pointing-device movement time and
  accuracy, in continuous use since 1954. Well-established; not independently re-verified beyond the
  formula itself, which is textbook-level settled.
- "Simulating Human Cursor Trajectories for Path-Sensitive GUI Evaluation," Extended Abstracts of the 2026
  CHI Conference — **verified directly** (abstract text confirmed via search after an ACM 403 blocked
  direct fetch, not assumed from the title). Real precedent for path-constrained cursor-trajectory
  simulation via Model Predictive Contouring Control, evaluated against real human data — distinct from
  Fitts's Law, see the corrected section above. Note this is an Extended Abstract, a lighter publication
  tier than a full peer-reviewed CHI paper.
- UEyes (CHI 2023) and current zero-shot vision-language-model gaze prediction research — precedent for
  predicting UI attention/gaze from a screenshot without UI-specific training data. Not independently
  re-verified beyond the search-summary level (unlike the two items above, this one wasn't WebFetch-checked
  against a primary source) — treat as a plausible-but-unconfirmed lead, worth a real check before relying
  on it further.
- HEART framework (Google) — Task Success dimension's real breakdown (error rate, time-to-completion,
  success rate) **verified directly** against statsig.com's summary, used to shape the Findability family
  above. The specific researcher attribution (Rodden/Hutchinson/Fu) is a well-known fact from the original
  Google publication but was not itself confirmed by the source checked here.
- ~~Current game-HUD design research — the ~200ms glance-budget and 80%/20% gameplay-vs-chrome attention
  split figures~~ — **checked directly and downgraded/removed**, see the verification note under Density
  Legibility above. The 200ms figure did not appear in any of three checked source articles; the 80/20
  split appears in one article but is itself presented there as an uncited "research shows" claim.

*Raised: 2026-08-23, following the external design-review-driven revision of
`docs/plans/hud_delivery_roadmap.md` and direct research into this repo's own existing quality-scoring
precedents (SimQ, visual-quality validation) plus current external HCI/UX-measurement research.
Fact-checked 2026-08-23: three of the doc's external claims were directly re-verified against their
primary sources after an initial pass relied only on search-engine summaries — one number (200ms) was
found unsupported and removed, one (80/20 split) was downgraded from "citable finding" to "uncited
folklore," and one technical claim (the CHI paper's method) was corrected from Fitts's Law to Model
Predictive Contouring Control.*
