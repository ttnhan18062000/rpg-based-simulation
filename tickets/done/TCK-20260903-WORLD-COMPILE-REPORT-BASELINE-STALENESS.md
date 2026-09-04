---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
phase: done
date: 2026-09-03
tags: [content, determinism]
---

# TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Title
Committed compile/calibration baselines (world_compile_report.json, grade_anchors.json) drift stale with no process to prevent recurrence — world_compile_report.json side now fixed, grade_anchors.json still open

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found while implementing `TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT` (idea 66): every one of the 21
worlds' `data/worlds/*/world_compile_report.json` files was last committed in the **exact same single
commit** (`29d78798`, "Simulation quality (#20)", 2026-08-14) — confirmed directly via `git log --oneline
-1 -- data/worlds/<world>/world_compile_report.json` for `dungeon_crawl`, `wilderness_survival`,
`urban_political`, and `hero_guild_routing`, all pointing to the same commit. 83 commits have landed on
`main` since then (M2's 15-ticket batch, M3's Reproduction epic, numerous hardening/hotfix tickets), none
of which regenerated these fixtures.

Confirmed via direct recompile that at least 3 of the 21 worlds (`dungeon_crawl`, `wilderness_survival`,
`urban_political`) no longer reproduce their committed `state_hash` with the committed seed — likely all
21 are equally affected, since they share the same generation commit and the same 83-commit gap.

**Not a determinism bug**: independently verified the compiler itself is fully reproducible (recompiling
identical content twice in a row with the same seed produces identical hashes every time). The staleness
is purely a fixture-maintenance gap.

**Not currently causing any failures**: checked every test that reads `world_compile_report.json`
(`tests/tools/test_corpus_registry.py`, `tests/unit/worldassembly/test_corpus_diversity.py`,
`tests/certification/test_world_compile_determinism.py`) — none of them recompile and compare
`state_hash` against a fresh build; they only consume other fields (entity counts, faction diversity,
corpus registry metadata). This drift has been silent and consequence-free until idea 66's own
Recalibration ticket (`TCK-20260902-PLACE-MIGRATION-RECALIBRATION`) planned to rely on these baselines
being trustworthy comparison points — which surfaced the gap.

## Scope
- ~~Batch-regenerate all 21 worlds' `world_compile_report.json`/`resolved/` assets~~ **Done, as a side
  effect of `TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT`'s own batch resolve+compile pass** — all 21
  worlds now have fresh, current, reproducible `world_compile_report.json`/`resolved/` assets. This half
  of the original finding is resolved; no further action needed here.
- **New, still-open finding**: `tests/simulation_quality/fixtures/grade_anchors.json` has the identical
  staleness pattern, confirmed independently. Last committed `5993cac3` (2026-08-31), 21 commits ago (a
  smaller gap than `world_compile_report.json`'s 83, but still real — M3's Reproduction epic and other
  behavior-changing tickets landed since). Confirmed via a rigorous causal-isolation test during
  `TCK-20260902-PLACE-MIGRATION-RECALIBRATION`: reverted all of idea 66's content changes to their exact
  pre-migration state and re-ran a previously-drifted run_key (`unit_information_source_seed123_200t`)
  — it *still* drifted from its anchor (SOCIAL: anchor grade A/score 1.8 vs. fresh S/3.97), proving the
  drift is unrelated to idea 66's Place migration. A full 81-run_key sweep found 61/81 drifted from
  their anchors, 18/81 matched cleanly, 2/81 failed for an unrelated tooling reason (two "probe" run_keys
  with no matching `data/worlds/` directory, not resolvable via the standard `--name` invocation).
- Decide the fix direction for `grade_anchors.json` specifically:
  1. Batch-regenerate all 81 anchors against current `main` — a bigger decision than the
     `world_compile_report.json` case, since these are curated "acceptable" grade/score thresholds
     that gate the whole `test_grade_regression.py` suite, not just mechanical hash values; regenerating
     means deliberately accepting new baseline expectations going forward, not just refreshing a hash.
  2. Add a process/CI gate that flags (not silently auto-fixes) when live-recalibrated grades drift
     beyond the anchor's own tolerance bands, prompting a deliberate human review rather than silent
     staleness.
  3. Some combination.

## Out of Scope
- Idea 66's own migration work — all 5 child tickets landed independently of this ticket's fix (the
  `world_compile_report.json` half was resolved as a side effect of Stage B's own scope; the
  `grade_anchors.json` half was causally isolated and confirmed unrelated to idea 66, then left for this
  ticket rather than fixed inline).
- Root-causing *why* specific worlds' compiled state or grades changed field-by-field across the
  historical commit gaps (a real but much larger investigation, likely spanning M2/M3's own behavior
  changes) — this ticket is about regenerating stale fixtures and preventing recurrence, not auditing
  every historical diff.
- Fixing any of the 2 `RUN_FAILED` "probe" run_keys found during the sweep
  (`urban_political_selfmodel_execution_probe_seed42_200t`,
  `urban_political_selfmodel_probe_seed42_200t`) — these fail because they don't correspond to a real
  `data/worlds/` directory, a naming/invocation mismatch unrelated to staleness; needs its own
  investigation into what these run_keys are actually supposed to represent.

## Acceptance Criteria
- [x] All 21 worlds' `world_compile_report.json` confirmed current — done via Stage B's batch pass,
      21/21 succeeded, every world's fresh compile now matches its own (regenerated) committed value.
- [x] All 81 `grade_anchors.json` run_keys confirmed either stale or current — re-confirmed fresh
      (not the 2-day-old sweep numbers): 64/81 real anchor-based tests fail the full band+score-
      tolerance check against a real, live engine re-run of current `main` (44/61 fast-tier, 18/18
      slow-tier, both named isolated tests), 17/81 pass. The 2 `RUN_FAILED` probe keys remain
      confirmed out of scope (not covered by any parametrize list — a separate naming/invocation
      issue, unrelated to staleness). Per-key real-staleness-vs-non-determinism triage for all 64
      is not attempted (would require multiple repeat draws per anchor, per this ticket's own user-
      chosen scope: gate only, not a full regeneration decision this session).
- [x] A decision is recorded on the `grade_anchors.json` fix direction (regenerate, add a gate, or both).
      **Gate only**, per explicit user choice — batch regeneration deferred as a separate, human-
      reviewed follow-up (see investigation.md/plan.md).
- [ ] If regenerated: every anchor reproduces on a clean recalibration run with its committed seed,
      verified directly (not assumed) — **N/A, not regenerating in this ticket** (gate-only direction).
- [x] If a gate is added: it's wired into the same "After Work"/CI checklist pattern this repo already
      uses for `docs/REGISTRY.yaml` and the parity index, so it doesn't silently drift again. New
      informational `simq-grade-drift` CI job wired into `.github/workflows/test.yml`.

## Related Tickets
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (where the `world_compile_report.json` half was discovered)
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT (whose batch resolve+compile pass resolved the
  `world_compile_report.json` half as a side effect)
- TCK-20260902-PLACE-MIGRATION-RECALIBRATION (where the `grade_anchors.json` half was discovered and
  causally isolated from idea 66's own changes)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (Recalibration procedure
  section, whose "diff against committed baseline" premise this ticket's finding affects)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS/`

## Related Code Areas
- ~~`data/worlds/*/world_compile_report.json`, `data/worlds/*/resolved/*`~~ — resolved.
- `tests/simulation_quality/fixtures/grade_anchors.json` (81 run_keys, 64 confirmed drifted as of
  this ticket's fresh re-check — not mutated by this ticket)
- `tools/calibrate_simq.py` (the real regeneration path: `--name`/`--ticks`/`--seed`/`--output`)
- `tools/evaluate_simq.py` / `make evaluate-full` / `make simq-full-audit-full` (the already-built
  live-diff tooling this ticket wires into CI — no code changes needed)
- `tests/simulation_quality/test_grade_regression.py` (the regression test this fixture gates —
  docstring fix only)
- `.github/workflows/test.yml` (new `simq-grade-drift` informational job)

## Assumptions / Open Questions
- ~~Whether a full 21-world regeneration should happen as one batch ticket or be folded into idea 66's
  own Recalibration work~~ — resolved; it happened as a side effect of Stage B.
- Whether `grade_anchors.json`'s regeneration should be one big batch (all 81 run_keys) or staged/
  reviewed in smaller groups, given each anchor represents a curated "acceptable" threshold, not a
  mechanical hash — a human should plausibly eyeball at least the biggest swings (e.g. the SOCIAL
  A→S/1.8→3.97 case found during triage) before accepting them as the new baseline, not just batch-copy
  fresh numbers over old ones.
- What specifically changed across the 21 commits to cause the `grade_anchors.json` drift (M3's
  Reproduction epic is the most likely candidate, given its scale and the SOCIAL-pillar-heavy nature of
  the observed drift) — not required to answer before regenerating, but useful context for review.
- What specifically changed across the (now-historical) 83 commits that caused the
  `world_compile_report.json` drift, for anyone auditing the resolved side's individual field-level
  diffs later — not investigated, out of scope, but the fresh values are now committed and correct
  regardless of the "why."

## Implementation Notes
User was asked upfront to choose the `grade_anchors.json` fix direction, given two other resource-
heavy tickets this session already established a contention-avoidance discipline: **gate only**,
not batch regeneration.

Investigation found the real root cause is more precise than "no process to prevent recurrence"
implies: `test_grade_regression.py`'s anchor tests already exist with real band+score-tolerance
logic, but they compare against `data/calibration/<run_key>/quality_report.json` — a gitignored,
developer-machine-local file, never populated by any CI job (`grep -n "simq\|evaluate_simq\|calibrat"
.github/workflows/test.yml` found only the unrelated `simq-corpus-diversity-slow-isolated` job).
Confirmed empirically: `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"` in
a clean environment (matching real CI) produces 64 SKIPPED, 7 PASSED, 0 FAILED — every real anchor
comparison silently skips. The gate has never actually executed in this repo's CI history.

The real fix already existed as built tooling: `tools/evaluate_simq.py` / `make simq-full-audit-full`
(engine re-run + anchor diff + regression tests + coverage-gap scan), never wired into CI. Zero
production code changes needed. Added a new `simq-grade-drift` job to `.github/workflows/test.yml`,
mirroring the existing "Type check (informational)" job's `continue-on-error: true` pattern and the
existing "Slow regression" job's push-to-main-only trigger — deliberately non-blocking, since 64/81
anchors are already known-drifted and a hard-blocking gate would fail every push to main immediately
over already-known, already-accepted-for-now drift (the opposite of what "gate only, don't resolve
the backlog" means).

Separately confirmed and fixed a second, independent doc-drift bug found during investigation:
`test_grade_regression.py`'s own module docstring instructed `make calibrate` to regenerate
anchors — that Makefile target does not exist (confirmed via `grep -n "^calibrate" Makefile`, no
match). Corrected to the real `make evaluate-full`/`tools/calibrate_simq.py` invocations.

Also found and documented (not fixed — out of scope, `evaluate_simq.py` itself untouched): the
standalone `tools/evaluate_simq.py` only implements the letter-grade band-tolerance check
(`_within_band`), not the score-magnitude tolerance check `test_grade_regression.py`'s own pytest
suite also does — confirmed via direct source read (`grep -n "_within_band\|_within_score_tolerance"
tools/evaluate_simq.py`, only the former appears). This is why a first pass with
`evaluate_simq.py --dry-run` alone reported only 3/630 pillar regressions — it silently misses
within-band score-magnitude drift (the exact class the ticket's own investigation found, e.g. an
A→S grade transition that's still within the ±1 band but whose score more than doubled). The new
CI job runs the full pytest suite too (as part of `make simq-full-audit-full`'s own 3 steps), so
this gap doesn't blind the new gate — but it's worth knowing `evaluate_simq.py`'s own standalone
report undercounts real drift.

## Test Summary
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — valid YAML.
- Real, live `tools/evaluate_simq.py --include-slow` engine re-run against current `main`, on a
  confirmed-idle machine (load average 0.04/0.16/0.21 on 6 cores, all other Claude sessions'
  processes <4% CPU at start) — populated `data/calibration/` for all 81 real anchor run_keys
  (fast-tier took ~7m25s; slow-tier addition took longer given 1000t/2000t ticks, both completed
  without error).
- `pytest tests/simulation_quality/test_grade_regression.py -v` (full suite, fast + slow, against
  the now-populated `data/calibration/`) — **64 failed, 25 passed**. Of the 64 failures: 44/61
  fast-tier anchors, 18/18 slow-tier anchors, both named isolated tests (`test_urban_political_
  selfmodel_cognition_isolated_grade_anchor`, `..._execution_isolated_grade_anchor`) — 64/81 real
  anchor comparisons confirmed drifted, 17/81 confirmed current. Closely matches (grew slightly
  from) the ticket's own 2-day-old 61/81 estimate — consistent with "ongoing drift," not a one-time
  historical artifact.
- `pytest tests/simulation_quality/ -m "not slow and not extra_slow" -q` (broader domain sweep,
  before and after the docstring-only edit) — 47 failed, 487 passed both times, identical counts —
  confirms the docstring change introduced zero behavioral difference, and that the 47 (fast-tier
  subset of the 64) are pre-existing real drift, not caused by this ticket.
- No `grade_anchors.json` mutation at any point — confirmed via `git diff` showing zero changes to
  that file throughout this ticket's implementation.
- **Real CI failure caught and fixed** (PR #127, "Architecture / docs / static" job): reproduced
  locally with the exact CI command
  (`pytest tests/architecture tests/docs tests/integrity tests/static tests/refactor -m "not slow and not extra_slow"`)
  — `test_ci_step_summary_reporting.py::test_no_cross_job_aggregate_step_or_job_added` failed
  because it's a static, frozen-job-set guard that doesn't yet know about the new
  `simq-grade-drift` job. Investigated before touching it: the same file already documents a
  sanctioned precedent for this exact situation (`frontend`, added by
  `TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP` with a comment) — the guard's real invariant is "no
  *undocumented* job added," not "no job ever added." Extended `expected_job_names` with
  `simq-grade-drift` and a comment citing this ticket, matching the file's own established pattern
  — not a silently-routed-around gate. Re-ran the same command after the fix: 196 passed, 2
  skipped, 1 deselected, 2 xfailed (was 195/2/1/2/1-failed before).

## Files Changed
- `.github/workflows/test.yml` — new `simq-grade-drift` job (informational, push-to-main-only,
  runs `make simq-full-audit-full`).
- `tests/simulation_quality/test_grade_regression.py` — module docstring only: fixed the broken
  `make calibrate` reference and added a CI note explaining the new job's purpose.
- `tests/static/test_ci_step_summary_reporting.py` — CI caught this: PR #127's real
  "Architecture / docs / static" job failed with a reproduced local exit 1,
  `test_no_cross_job_aggregate_step_or_job_added` (a static frozen-job-set guard from
  `TCK-20260823-CI-STEP-SUMMARY-REPORTING`). This is the exact same pattern the test file's own
  `frontend` job entry already documents as sanctioned: the guard's real invariant is "no
  undocumented job added," not "no job ever added" — a prior ticket
  (`TCK-20260825-CI-FRONTEND-TEST-COVERAGE-GAP`) already extended it once, with a comment. Added
  `simq-grade-drift` to `expected_job_names` the same way, with a comment citing this ticket and
  its rationale — not a silent routed-around gate, following this repo's own established extension
  precedent for this exact guard.

## Completion Summary
Closed the `grade_anchors.json` half of this ticket via the user's chosen gate-only direction. The
real root cause was more precise than the ticket's own framing: the existing anchor-comparison
tests have real tolerance logic but have never once executed a real comparison in this repo's CI
history, since nothing populates the `data/calibration/` directory they depend on — confirmed
empirically (64/89 real anchor tests silently skip in a clean environment matching CI exactly).
The actual fix needed zero new Python code: `tools/evaluate_simq.py`/`make simq-full-audit-full`
already existed and does exactly what's needed, just was never wired into CI. Added a new,
deliberately non-blocking (`continue-on-error: true`) `simq-grade-drift` job on the same push-to-
main-only cadence as the existing "Slow regression" job, so new drift becomes visible for human
review without immediately failing every push over the 64 already-known-drifted anchors this
ticket does not resolve. Also fixed an unrelated, directly-adjacent doc-drift bug (a broken `make
calibrate` reference) found during investigation, and documented (without fixing, out of scope) a
real gap in `evaluate_simq.py`'s own standalone drift detection (missing the score-tolerance check
`test_grade_regression.py`'s pytest suite also does).

Satisfied AC #1 ("all 81 run_keys confirmed either stale or current") with a fresh, real, live
engine re-run on a confirmed-idle machine — not the ticket's own 2-day-old estimate: 64/81 real
anchor comparisons currently fail (44 fast + 18 slow + 2 named), 17/81 pass, 2 probe keys remain
out of scope. Per-key non-determinism-vs-real-staleness triage and the actual anchor regeneration
are both explicitly deferred as separate, human-reviewed follow-up work, per the user's own chosen
scope for this ticket.
