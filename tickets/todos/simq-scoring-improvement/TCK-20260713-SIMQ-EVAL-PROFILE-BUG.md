---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-EVAL-PROFILE-BUG
phase: open
date: 2026-07-13
tags: [simulation-quality, calibration]
---

# TCK-20260713-SIMQ-EVAL-PROFILE-BUG

## Title
Fix `evaluate_simq.py` live-mode silent world-loading fallback when a run_key's profile name
differs from its world name

## Status
OPEN

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
- [ ] `python3 tools/evaluate_simq.py` (live mode, not `--dry-run`) run against the full corpus
      reproduces the same grades for `urban_political_selfmodel_probe_seed42_200t` as a standalone
      `calibrate_simq.py --name urban_political --seed 42 --ticks 200 --profile
      urban_political_selfmodel_probe` invocation (COGNITION=S, FACTION=S, SOCIAL=S, NARRATIVE=A
      per the last verified standalone run).
- [ ] A deliberately-broken world name (e.g. running calibration against a nonexistent world)
      raises a clear error instead of silently producing a near-empty result.
- [ ] Full `evaluate_simq.py --dry-run` and live-mode sweeps show 0 regressions attributable to
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

## Test Summary

## Files Changed

## Completion Summary
