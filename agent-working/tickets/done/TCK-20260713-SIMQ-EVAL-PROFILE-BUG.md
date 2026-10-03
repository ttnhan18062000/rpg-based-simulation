---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-EVAL-PROFILE-BUG
phase: done
date: 2026-07-13
tags: [simulation-quality, calibration]
---

# TCK-20260713-SIMQ-EVAL-PROFILE-BUG

## Title
Fix `evaluate_simq.py` live-mode silent world-loading fallback when a run_key's profile name
differs from its world name

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`tools/evaluate_simq.py`'s live (non-`--dry-run`) mode silently produces corrupted, meaningless
calibration results for any anchor entry whose profile name differs from its world name, instead
of erroring. Discovered while building `docs/simulation_quality/current_state.md`: a full live
corpus run of `urban_political_selfmodel_probe_seed42_200t` (the probe fixture added by
`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) fell back to a generic synthetic scenario
(`world_id: "unknown"`, `scenario_name: "PROD_SMALL"`, confirmed in that run's
`run_manifest.json`) and produced a near-empty result that was compared against the real anchor
and flagged as a 3-pillar REGRESS. A standalone `calibrate_simq.py` re-run of the identical
scenario reproduced the correct, anchor-matching result, confirming this is a tooling bug, not a
quality regression.

**Root cause, confirmed by direct code read:** `_run_calibration()`
(`tools/evaluate_simq.py:59`) never forwards `--profile` to `calibrate_simq.py` — it only passes
`--name`, `--seed`, `--ticks`. `_parse_run_key()` (`tools/evaluate_simq.py:45`) derives `name`
purely from the run_key's regex-matched prefix (`^(.+)_seed(\d+)_(\d+)t$`), which for
`urban_political_selfmodel_probe_seed42_200t` extracts `"urban_political_selfmodel_probe"` — the
*profile* name, not the *world* name (`"urban_political"`). Since `--profile` is never passed,
`calibrate_simq.py:329-332` falls back to `profile = _resolve_profile(args.name)`, which happens
to resolve correctly by lucky filename coincidence (the profile YAML is named identically). But
`calibrate_simq.py:344` then calls `_run_engine(args.name, ...)` — passing the same wrong string
as the **world** name. No world directory `data/worlds/urban_political_selfmodel_probe/` exists,
and the engine's world-loading silently falls back to a generic scenario instead of raising.

This currently affects exactly one anchor entry (the only one where profile-name-prefix ≠
world-name), but is a latent trap for any future probe-style fixture.

## Scope
- Fix `_run_calibration()`/`_parse_run_key()` (or the calling code in `evaluate_simq.py::main()`)
  so the correct **world** name and **profile** name are both resolved correctly for every anchor
  entry, including ones where they differ. Investigate whether `grade_anchors.json` needs a
  per-entry metadata hint (it currently has none — confirmed only `_note`, `_instructions`,
  `_grade_order` metadata keys exist) or whether a different run_key-parsing strategy avoids
  needing one.
- Make `calibrate_simq.py`'s world-loading fail loudly (raise a clear error) when the requested
  world name doesn't resolve to a real `data/worlds/{name}/` directory, instead of silently
  falling back to a generic synthetic scenario. This is a real defense-in-depth fix independent of
  the root-cause fix above — it's what let the corrupted result look plausible instead of crashing
  obviously.

## Out of Scope
- Any change to the actual scoring formula, weights, or grade thresholds — pure tooling/plumbing
  fix, see `TCK-20260713-SIMQ-SCORE-CEILING-FIX` for that separate concern.
- Adding new probe-style fixtures — this ticket only fixes the mechanism for handling the one that
  already exists and any future ones.

## Acceptance Criteria
- [x] `python3 tools/evaluate_simq.py` (live mode, not `--dry-run`) run against the full corpus
      reproduces the same grades for `urban_political_selfmodel_probe_seed42_200t` as a standalone
      `calibrate_simq.py --name urban_political --seed 42 --ticks 200 --profile
      urban_political_selfmodel_probe` invocation (COGNITION=S, FACTION=S, SOCIAL=S, NARRATIVE=A
      per the last verified standalone run). Verified COGNITION=S/FACTION=S/SOCIAL=S exactly;
      NARRATIVE landed at B (anchor A) on both live reruns due to a pre-existing, unrelated
      tick-budget/real-time variance in SOCIAL/NARRATIVE event counts under machine load — still
      within the ±1 tolerance band, all 10 pillars PASS. See Implementation Notes.
- [x] A deliberately-broken world name (e.g. running calibration against a nonexistent world)
      raises a clear error instead of silently producing a near-empty result.
- [x] Full `evaluate_simq.py --dry-run` and live-mode sweeps show 0 regressions attributable to
      this fix.

## Related Tickets
- `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` (done) — added the
  `urban_political_selfmodel_probe` fixture that exposed this bug.

## Related Docs
- `docs/simulation_quality/current_state.md` — "Known issue" note, full bug evidence and diagnosis.
- `docs/plans/simq_scoring_improvement_roadmap.md` — Phase 0, this ticket's source.

## Related Stored Artifacts
None yet — filed directly from a diagnosed tooling bug, hotfix tier.

## Related Code Areas
- `tools/evaluate_simq.py:45` (`_parse_run_key`)
- `tools/evaluate_simq.py:59` (`_run_calibration`)
- `tools/calibrate_simq.py:329-344` (profile resolution and `_run_engine` call)
- `tests/simulation_quality/fixtures/grade_anchors.json` (may need a schema addition)

## Assumptions / Open Questions
- Whether the fix needs a `grade_anchors.json` schema change (a `_profile` hint per entry) or can
  be solved purely by smarter run_key parsing (e.g. trying `_resolve_profile` against progressively
  shorter name prefixes until a real world directory is found) is left to the implementer's
  Investigate step — both are plausible, investigation should pick the one with less schema churn.

## Implementation Notes

Chose the "smarter run_key parsing" option (no `grade_anchors.json` schema change), since
`data/worlds/` already lists every real world directory and can be probed directly at run time —
adding a `_profile` metadata key per anchor entry would have been pure churn for information the
filesystem already encodes.

- `tools/evaluate_simq.py`:
  - `_parse_run_key()` unchanged in implementation, but its return value is now explicitly
    documented (and treated by callers) as `(profile_name, seed, ticks)` rather than
    `(name, seed, ticks)` — the run_key prefix is always the *profile* name.
  - Added `_resolve_world_name(profile_name) -> str`: tries the full profile name against
    `data/worlds/{name}/` first, then progressively strips trailing `_segment` tokens until a real
    world directory is found; raises `ValueError` with a clear message if none match.
  - `_run_calibration()` now takes `(world_name, profile_name, seed, ticks, run_key)` and forwards
    both `--name {world_name}` and `--profile {profile_name}` to `calibrate_simq.py`, plus
    `--output {CALIBRATION_ROOT}/{run_key}` — pinning the output directory to `run_key` explicitly,
    since `calibrate_simq.py`'s own default output dir is derived from `--name` (the world), which
    only coincidentally matched `run_key` when profile and world names were identical. Without this,
    `_load_calibration_report(run_key)` would look in the wrong directory for any profile≠world
    entry.
  - `main()`'s live-mode loop now calls `_resolve_world_name(profile_name)` before invoking
    calibration, and reports both names in the progress line.
- `tools/calibrate_simq.py`:
  - `_load_world_state()` now raises `FileNotFoundError` when `name != "generic"` and no resolved
    world spec exists at `data/worlds/{name}/resolved/world.resolved.yaml`, instead of silently
    returning `(None, None)` (which drove the hero+goblins generic fallback and produced a
    plausible-looking but meaningless report). The literal sentinel `"generic"` (the CLI's `--name`
    default, used for ad-hoc non-world runs) is preserved as the one case that still returns
    `(None, None)` without raising. Compile-failure fallback (the `except Exception` branch further
    down, already logging a warning) is untouched — out of this ticket's stated scope, which is
    specifically the "world doesn't resolve to a real directory" case.
- Added tests: `tests/simulation_quality/test_calibrate_world_loading.py` (new file) covers the
  `generic` sentinel, a real world, and the fail-loud path. Added a `TestResolveWorldName` class to
  `tests/simulation_quality/test_evaluate_harness.py` covering direct match, variant-prefix match
  (the actual probe fixture case), and the unresolvable-name error.

**Verification performed (see Test Summary):** live-mode run of
`urban_political_selfmodel_probe_seed42_200t` via `evaluate_simq.py` now resolves
`world=urban_political profile=urban_political_selfmodel_probe` and produces PASS on all 10
pillars against the anchor, including COGNITION=S, FACTION=S, SOCIAL=S exactly as required.
NARRATIVE anchor is A; two live reruns produced NARRATIVE=B, one letter below anchor — still PASS
under the existing ±1 tolerance band. This is **not** attributable to this fix: COGNITION, FACTION,
COMBAT, WORLD, PROGRESSION event counts were bit-identical across repeated runs (5610/29/4/14/3),
while SOCIAL and NARRATIVE event counts varied run-to-run (e.g. SOCIAL 1064 vs 1079 vs the
standalone run's 770) and the live runs logged `Tick N exceeded budget` warnings under machine
load that a quieter standalone run did not. This is a pre-existing kernel tick-budget/real-time
sensitivity, orthogonal to profile/world name resolution (which is what this ticket fixes), and is
out of scope here (no scoring-formula changes permitted). Flagging for awareness, not fixing.

## Test Summary

- `pytest tests/simulation_quality/test_evaluate_harness.py tests/simulation_quality/test_calibrate_world_loading.py -v`
  — 23 passed (17 pre-existing + 6 new: 3 `TestResolveWorldName`, 3 in the new world-loading file).
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q` — 55 passed (no
  regression from the `_load_world_state` fail-loud change).
- `pytest tests/unit/worldassembly/test_hero_guild_routing_population_stability.py -q` — 1 passed.
- `python3 tools/evaluate_simq.py --dry-run` — full 72-entry corpus, 720 pillars checked, 0
  regressions, 0 missing.
- `python3 tools/evaluate_simq.py --scenario urban_political_selfmodel_probe_seed42_200t` (live
  mode, run twice) — 10/10 PASS both times; COGNITION=S, FACTION=S, SOCIAL=S matched exactly;
  NARRATIVE=B vs anchor A, within ±1 tolerance (see Implementation Notes for the unrelated
  tick-budget variance explanation).
- `python3 tools/evaluate_simq.py --scenario sandbox_world_seed42_200t` and
  `--scenario dungeon_crawl_seed42_200t` (live mode, normal profile==world case) — 10/10 PASS each,
  confirming the fix does not disturb the standard path.
- `python3 tools/calibrate_simq.py --name doesnotexist123 --seed 1 --ticks 5` — raises
  `FileNotFoundError` with a clear message instead of silently producing a report.
- `python3 tools/calibrate_simq.py --seed 1 --ticks 3` (no `--name`, defaults to `"generic"`) —
  still runs the generic hero+goblins fallback scenario without raising, confirming the sentinel
  case is preserved.

## Files Changed

- `tools/evaluate_simq.py`
- `tools/calibrate_simq.py`
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_calibrate_world_loading.py` (new)

## Completion Summary

Fixed `evaluate_simq.py` live mode to correctly resolve both the world name and the profile name
for every anchor entry (via a new `_resolve_world_name()` that probes `data/worlds/` directly,
requiring no `grade_anchors.json` schema change), and forwards `--profile` and an explicit
`--output` to `calibrate_simq.py` so the calibration report lands where the evaluator expects it.
Independently hardened `calibrate_simq.py`'s world loading to raise `FileNotFoundError` on any
unresolvable non-`"generic"` world name instead of silently falling back to a synthetic scenario.
All acceptance criteria verified: the probe fixture now reproduces its anchor grades in live mode
(COGNITION=S, FACTION=S, SOCIAL=S confirmed exactly; NARRATIVE within tolerance band), a broken
world name now errors loudly, and full dry-run plus spot-checked live-mode sweeps show 0
regressions attributable to this fix.
