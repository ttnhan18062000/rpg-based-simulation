---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
phase: open
date: 2026-09-03
tags: [content, determinism]
---

# TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Title
Committed compile/calibration baselines (world_compile_report.json, grade_anchors.json) drift stale with no process to prevent recurrence — world_compile_report.json side now fixed, grade_anchors.json still open

## Status
OPEN

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
- [ ] All 81 `grade_anchors.json` run_keys confirmed either stale or current (61/81 confirmed drifted via
      the sweep in this ticket's Related Stored Artifacts; not yet triaged one-by-one for whether each
      is real staleness vs. a run-to-run non-determinism artifact — the causal-isolation test only
      directly proved this for one run_key).
- [ ] A decision is recorded on the `grade_anchors.json` fix direction (regenerate, add a gate, or both).
- [ ] If regenerated: every anchor reproduces on a clean recalibration run with its committed seed,
      verified directly (not assumed) — same discipline as the `world_compile_report.json` fix.
- [ ] If a gate is added: it's wired into the same "After Work"/CI checklist pattern this repo already
      uses for `docs/REGISTRY.yaml` and the parity index, so it doesn't silently drift again.

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
None yet.

## Related Code Areas
- ~~`data/worlds/*/world_compile_report.json`, `data/worlds/*/resolved/*`~~ — resolved.
- `tests/simulation_quality/fixtures/grade_anchors.json` (81 run_keys, 61 confirmed drifted)
- `tools/calibrate_simq.py` (the real regeneration path: `--name`/`--ticks`/`--seed`/`--output`)
- `tests/simulation_quality/test_grade_regression.py` (the regression test this fixture gates)

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

## Test Summary

## Files Changed

## Completion Summary
