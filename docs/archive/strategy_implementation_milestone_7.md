Good. Milestone 7 is the point where all the previous work stops being architecture on paper and becomes a **real regression path**.

Up to Milestone 6, you can have a strong strategic engine and a canonical cognition export. That still is not enough. Until you can run a minimal production-like path, execute the real engine, produce artifacts, and assert invariants end to end, you are still testing components more than the system. Milestone 7 is where “run CLI -> engine execution -> result” becomes an actual proof harness rather than a vague hope. That is consistent with the implementation notes that frame the headless run plus export artifact as the right final-system validation path.

# Milestone 7 — Final-system CLI regression path

## What this milestone actually delivers

At the end of Milestone 7, you should be able to:

- run a deterministic, headless, production-like simulation path
- let the real engine execute through the real world loop
- produce stable artifacts such as replay plus cognition graph export
- assert structural invariants over those artifacts
- catch regressions in continuity, blockers, detours, cooperation, and reprioritization without manually inspecting the simulation every time

That is the first moment where the whole “thinking” system is not just implemented, but **testable as a system**.

What Milestone 7 does **not** need:

- visual dashboards
- human-in-the-loop inspection as the primary validation method
- giant scenario libraries on day one
- perfect behavioral scoring metrics

This milestone is about a trustworthy regression harness, not product polish.

---

## The real problem you are solving

The trap here is obvious: you already have unit tests, integration tests, replay, inspection, and export. So it is tempting to say “we already test the system.”

Not enough.

Why? Because scattered tests prove pieces. Milestone 7 must prove the **production-like path**:

- engine bootstraps correctly
- simulation executes deterministically
- authoritative updates accumulate correctly over time
- replay and exported cognition stay consistent
- major strategic behaviors remain visible after a real run

Without this, you can still pass many tests while the real headless run drifts, the CLI path diverges, or the artifacts stop reflecting the real engine state. The reference material is already pushing toward exactly this final-system path.

---

## What must exist by the end of this milestone

You need five things.

### 1. One trusted headless execution path

You need a single, explicit headless run path that is close enough to production to matter.

That means:

- real config
- real registries
- real world generation/bootstrap
- real `WorldLoop`
- real authoritative update flow
- real artifact writing

Do not build a fake “test runner” that bypasses the engine. That would undermine the whole milestone.

### 2. Stable artifact production

A run should produce deterministic artifacts that can be asserted.

At minimum:

- replay artifact
- one or more entity cognition graph exports

Optionally:

- summarized inspection output
- reduced strategic run report
- failure diffs

But replay plus graph export is the real baseline.

### 3. Selected tracked entities

You need a deterministic way to choose which entities matter for export/assertion.

That can be:

- explicit entity IDs when stable
- first hero / seeded hero / named actor chosen deterministically
- entities matching tracked roles or project conditions

Do not rely on ad hoc manual browsing after the run.

### 4. Cross-artifact invariants

The graph export and replay should agree where their semantics overlap.

Examples:

- current project/objective in replay summary matches graph continuity edges
- blocker presence in strategic summary matches blocker nodes in export
- contract/project continuity seen in replay is reflected in graph edges
- reprioritization events correspond to changed project state in the graph

If these artifacts can drift independently, you have created two partial truths.

### 5. Deterministic scenario tests

You need a small set of golden scenarios that predictably exercise the system.

Not dozens. Just enough to cover the important routes:

- continuity scenario
- blocker/detour scenario
- cooperation scenario
- event-driven reprioritization scenario

These are the scenarios that will keep the system honest.

---

## The correct implementation order

### Step 1 — Write end-to-end tests before polishing CLI features

Start with the behavior you want from the harness, not command-line sugar.

Write failing tests that prove:

- the headless run completes
- replay is written
- cognition export is written
- the same seed/config produces the same structural artifacts
- selected tracked entities appear in export
- replay and graph agree on basic continuity state
- targeted scenarios trigger expected structural features

If you do not start here, you will waste time on CLI flags and still not have a real regression harness.

### Step 2 — Unify or lock the headless bootstrap path

This matters more than it sounds.

You need to ensure the final-system run is using the same core execution path you actually trust. If the headless bootstrap drifts away from the canonical engine path, your regression harness becomes a side system, not the real system.

So:

- reuse the real engine bootstrap as much as possible
- eliminate unnecessary divergence between headless and production-like paths
- make world setup deterministic and explicit

This is one of the biggest architectural risks in systems like this.

### Step 3 — Add artifact writing as a first-class run outcome

Do not make export a separate manual step after the run.

The harness should finish by writing:

- replay file
- cognition graph file(s) for tracked entities

That makes the run self-contained and reproducible.

### Step 4 — Add tracked-entity selection rules

You need deterministic actor selection.

Good first-pass rules:

- explicit tracked entity IDs via config or CLI
- fallback deterministic selectors such as first hero or first entity matching role
- optionally export a small fixed count of tracked entities

Do not export every entity by default unless the system is tiny. That will produce noise and huge artifacts.

### Step 5 — Add artifact comparison helpers

You need machine-readable checks, not manual eyeballing.

Add helpers that can assert things like:

- graph contains current project node referenced by replay
- replay concern count is compatible with graph concern nodes
- active contract in graph matches replay summary or strategic state snapshot
- project interruption/resume state exists after event scenario

These helpers are the heart of regression value.

### Step 6 — Add scenario-specific golden tests

Now create a small set of deterministic end-to-end scenarios.

Examples:

- **continuity scenario**: same project persists across several ticks
- **blocker scenario**: current project hits blocker and spawns detour
- **cooperation scenario**: recruitment creates contract and resumes project
- **reprioritization scenario**: major event suspends or replaces project

These do not need to be giant worlds. They need to be controlled and repeatable.

### Step 7 — Add clear failure diffs

When a regression happens, you need useful output.

At minimum:

- missing node/edge details
- mismatched current project/objective
- unexpected blocker/concern/contract counts
- artifact path references for inspection

If failure output is vague, the harness will become annoying and people will ignore it.

---

## What the implementation should probably look like

## A. A dedicated headless regression runner

Create something like:

- `src/testing/headless_regression_runner.py`
  or equivalent harness logic near CLI support

Its job:

- prepare config
- run the world loop
- collect replay/export artifacts
- return structured result metadata for tests

This is better than making tests shell out blindly and parse random text.

## B. CLI integration as a thin surface

The CLI should expose the capability, but the real logic should live in a reusable runner/service.

That means:

- CLI flag parsing stays thin
- artifact production logic is shared
- tests can call the runner directly without subprocess overhead when appropriate

Do not bury core regression logic inside CLI string handling.

## C. Artifact manifest

Add a simple structured manifest describing what the run produced.

Example contents:

- seed
- ticks
- tracked entities
- replay path
- graph export paths
- maybe key summary hashes

This makes tests and debugging far cleaner.

## D. Structural assertion helpers

Create helpers for:

- loading replay
- loading cognition graphs
- comparing continuity state
- checking scenario-specific invariants

That keeps end-to-end tests readable and keeps you from reimplementing parsing in every test.

---

## TDD sequence for Milestone 7

Use this order.

### Test batch A — harness completes and writes artifacts

Write failing tests that prove:

- headless run completes without server dependencies
- replay is written
- cognition graph export is written
- artifact manifest is written or returned

Then implement the reusable regression runner and artifact writing.

### Test batch B — determinism

Write failing tests that prove:

- same seed/config produces same graph structure
- same seed/config produces same replay strategic summary
- tracked entity selection is deterministic

Then lock the bootstrap path and artifact ordering.

### Test batch C — cross-artifact consistency

Write failing tests that prove:

- replay current project/objective matches graph edges
- replay strategic summary and graph blocker/concern structure are compatible
- contract/project continuity is visible in both artifacts when relevant

Then implement assertion helpers and consistency checks.

### Test batch D — scenario coverage

Write failing tests that prove:

- continuity scenario preserves project across ticks
- blocker scenario produces detour artifacts
- cooperation scenario produces contract artifacts
- reprioritization scenario changes project continuity after major event

Then add deterministic scenario fixtures.

### Test batch E — failure diagnostics

Write failing tests that prove:

- mismatches surface clear structural diffs
- artifact file paths are available on failure
- missing export or missing replay fails loudly and specifically

Then improve diagnostics.

That is the right sequence because it locks the runner first, then determinism, then consistency, then behavioral coverage.

---

## Suggested file targets

Likely new or changed files:

- `src/testing/headless_regression_runner.py`
- CLI entrypoint or shared headless run module
- cognition graph export integration points
- replay writer/loader helpers
- artifact manifest module if you add one
- test utility/assertion helper modules

Suggested tests:

- `tests/e2e/test_headless_regression_runner.py`
- `tests/e2e/test_headless_regression_determinism.py`
- `tests/e2e/test_replay_graph_consistency.py`
- `tests/e2e/test_continuity_scenario.py`
- `tests/e2e/test_blocker_detour_scenario.py`
- `tests/e2e/test_cooperation_scenario.py`
- `tests/e2e/test_reprioritization_scenario.py`

---

## Definition of done for Milestone 7

Milestone 7 is done only when all of this is true:

- there is one trusted headless regression path
- it runs the real engine, not a fake simulation shortcut
- it writes replay and cognition graph artifacts deterministically
- tracked entities are selected deterministically
- cross-artifact consistency is asserted
- scenario-specific end-to-end tests exist for continuity, blockers, cooperation, and reprioritization
- failures produce useful structural diagnostics

If the headless path bypasses real engine behavior, you failed.
If the artifacts are non-deterministic, you failed.
If replay and graph can contradict each other unnoticed, you failed.
If end-to-end tests do not cover the core strategic behaviors, you failed.

---

## Milestone 7 checklist

- [x] Add failing tests that prove a headless production-like run completes successfully

- [x] Add failing tests that prove replay artifact is written

- [x] Add failing tests that prove cognition graph export artifact is written

- [x] Add failing tests that prove tracked entity selection is deterministic

- [x] Add failing tests that prove same seed/config yields same structural artifacts

- [x] Add failing tests that prove replay and graph agree on current project/objective continuity

- [x] Add failing tests that prove scenario-specific strategic behaviors appear in final artifacts

- [x] Add failing tests that prove artifact mismatch surfaces clear diagnostics

- [x] Create a reusable headless regression runner/service

- [x] Reuse the real engine bootstrap and world loop as much as possible

- [x] Avoid creating a fake test-only simulation path

- [x] Ensure configuration, seed, and tick count are explicit and reproducible

- [x] Return or write a structured artifact manifest

- [x] Add stable artifact writing for replay output

- [x] Add stable artifact writing for cognition graph export

- [x] Add deterministic file naming or manifest references

- [x] Keep artifact production part of the run outcome, not a manual afterthought

- [x] Add deterministic tracked-entity selection rules

- [x] Support explicit tracked entity IDs where useful

- [x] Support deterministic fallback selectors for actors of interest

- [x] Avoid defaulting to noisy export of every entity

- [x] Add helper utilities to load replay artifacts

- [x] Add helper utilities to load cognition graph artifacts

- [x] Add structural assertion helpers for continuity state

- [x] Add structural assertion helpers for blockers, concerns, contracts, and objectives

- [x] Add cross-artifact consistency checks where semantics overlap

- [x] Create deterministic continuity scenario fixture

- [x] Create deterministic blocker/detour scenario fixture

- [x] Create deterministic cooperation/recruitment scenario fixture

- [x] Create deterministic event-driven reprioritization scenario fixture

- [x] Keep scenarios small, controlled, and repeatable

- [x] Assert continuity scenario preserves project/objective structure across ticks

- [x] Assert blocker scenario shows blocker plus detour artifacts

- [x] Assert cooperation scenario shows contract-backed project continuation

- [x] Assert reprioritization scenario shows project suspension/replacement after major event

- [x] Add useful failure diagnostics for missing artifacts

- [x] Add useful failure diagnostics for replay/graph mismatches

- [x] Surface artifact paths or manifest details in failures

- [x] Keep diffs structural and concise enough to debug quickly

- [x] Confirm milestone definition of done with passing deterministic end-to-end tests

Priority Plan

What you must change in mindset or assumptions:
Stop thinking “the system runs” is evidence. The finish line is “the system runs, emits canonical artifacts, and those artifacts prove the strategic behavior survived a real engine run.”

What actions you must take immediately:
Write the headless artifact tests first, then build the reusable regression runner, then add cross-artifact assertion helpers, then add the four deterministic scenario tests.

What you must stop or eliminate:
Stop relying on manual inspection as the primary proof path. Stop allowing CLI/headless execution to drift from the real engine. Stop accepting replay or graph alone as sufficient when both can be checked together.

The consequences and opportunity cost if you fail to change:
You will have built a sophisticated strategic engine with weak final-system verification. That means regressions will slip through exactly where they matter most: not in isolated units, but in the real run path.
