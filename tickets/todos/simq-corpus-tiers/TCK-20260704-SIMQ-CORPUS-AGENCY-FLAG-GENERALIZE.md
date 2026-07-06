---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, agency, feature-flags, calibration]
---

# TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE

## Title
Generalize ENABLE_ADVENTURE_ROUTING activation into the per-world feature_flags profile mechanism

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 and §3 found an
architectural asymmetry: FACTION/INFORMATION content and `ENABLE_BELIEF_ASSIMILATION` all activate
through generalizable, already-existing mechanisms (world.yaml content fields, or a per-world
`config/simulation_quality/profiles/<world>.yaml` `feature_flags:` block, read by
`tools/calibrate_simq.py::_load_profile_feature_flags()`, lines 44-63). `ENABLE_ADVENTURE_ROUTING`,
by contrast, is activated **only** via a hardcoded special case in `tools/evaluate_simq.py`: a
`ROUTING_KEYS` set (lines 34-38) listing the exact 3 `simq_routing_test_seed*_500t` run keys, and a
`_run_calibration()` helper (lines 65-86) that sets/restores the `ENABLE_ADVENTURE_ROUTING`
environment variable directly around only those runs — bypassing the profile-YAML mechanism
entirely.

This ticket generalizes that mechanism: any world's `config/simulation_quality/profiles/<world>.yaml`
should be able to set `ENABLE_ADVENTURE_ROUTING: "ON"` in its `feature_flags:` block exactly the
way `urban_political.yaml` already does for `ENABLE_BELIEF_ASSIMILATION` and
`ENABLE_SOCIAL_COOPERATION` — with no scenario-name special-casing in `evaluate_simq.py` required.
This is a **prerequisite for ticket `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`**, which needs a
non-hardcoded way to turn routing on for a new world.

**This ticket does NOT change the existing DA ruling or any existing world's AGENCY grade** — it is
purely mechanism work. `simq_routing_test`'s existing behavior must be preserved exactly (same
env-var injection outcome), whether achieved by migrating it onto the new mechanism or by leaving
its current special case in place alongside the new generalized path — investigation and
implementation should determine which is cleaner, but either way its 3 existing anchor entries in
`grade_anchors.json` must not drift.

## Scope
1. Confirm `tools/calibrate_simq.py::_load_profile_feature_flags()` (lines 44-63) and its call site
   in `main()` (lines 338-344, `_run_engine(..., extra_flags=profile_feature_flags)`) already
   generically apply any `feature_flags:` key from a world's profile YAML to the engine run,
   with no special-casing per flag name — verify `ENABLE_ADVENTURE_ROUTING` would flow through this
   path identically to `ENABLE_BELIEF_ASSIMILATION` today (per investigation.md, this plumbing
   "already exists and works" for a sibling flag).
2. Remove or bypass `tools/evaluate_simq.py`'s `ROUTING_KEYS` hardcoded special case (lines 34-38,
   65-86) in favor of driving `ENABLE_ADVENTURE_ROUTING` activation purely through each scenario's
   profile YAML `feature_flags:` block — i.e. `evaluate_simq.py` should no longer need to know which
   run keys are "routing keys"; the profile YAML for that world/scenario should carry the flag.
3. Add a `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}` block to
   `config/simulation_quality/profiles/simq_routing_test.yaml` (create this profile file if it does
   not yet exist — confirm during investigation) so `simq_routing_test`'s existing routing-ON
   behavior is now expressed via the generalized mechanism instead of the hardcoded harness
   special case.
4. Confirm `simq_routing_test`'s 3 existing `grade_anchors.json` entries
   (`simq_routing_test_seed{42,123,456}_500t`) produce byte-identical or grade-identical results
   after the migration — no anchor drift permitted from this ticket (it is a mechanism refactor,
   not a content change).
5. Run `make evaluate --dry-run` and confirm 0 regressions.
6. Document the generalized mechanism (a short note, likely in
   `docs/simulation_quality/quality_scoring_contract.md` or `docs/guides/content_authoring.md`)
   confirming `ENABLE_ADVENTURE_ROUTING` is now a normal per-world profile-YAML flag like any other,
   with no remaining scenario-name special case.

## Out of Scope
- Turning `ENABLE_ADVENTURE_ROUTING` ON for any existing archetype world (`urban_political`,
  `dungeon_crawl`, etc.) — that would reverse `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` and is
  explicitly not part of this ticket or this epic for any existing world
  the DA ruling covers
- Authoring the new AGENCY unit-tier world itself (that is
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`, which depends on this ticket)
- Changing `AdventureDecisionPhase`, `AgencyScorer`, or any AGENCY-pillar scoring logic — this
  ticket only changes how the flag gets turned on for a given world/scenario, not what happens once
  it is on

## Acceptance Criteria
- [ ] `ENABLE_ADVENTURE_ROUTING` can be turned on for any world purely via that world's
      `config/simulation_quality/profiles/<world>.yaml` `feature_flags:` block, with zero
      scenario-name string-matching in `tools/evaluate_simq.py`
- [ ] `tools/evaluate_simq.py`'s `ROUTING_KEYS` hardcoded set and the `routing_flag` special-case
      branch in `_run_calibration()` are removed or made redundant/unreachable (not left as dead,
      misleading code)
- [ ] `simq_routing_test`'s 3 existing `grade_anchors.json` entries show 0 grade drift after the
      migration (`make evaluate --dry-run` confirms)
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions across the full existing corpus
- [ ] No existing world's AGENCY grade changes as a result of this ticket
- [ ] Mechanism documented in an appropriate doc (quality_scoring_contract.md or
      content_authoring.md)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — depends on this ticket; cannot turn
  `ENABLE_ADVENTURE_ROUTING` on for its new world without this mechanism existing
- TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL — its per-scenario flag-state test matrix must
  cover the generalized mechanism this ticket introduces
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — the ruling this ticket explicitly does NOT reverse

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory table, AGENCY row) and §3 ("`ENABLE_ADVENTURE_ROUTING` / AGENCY broadly" — mechanism
  cost asymmetry finding)
- `docs/simulation_quality/quality_scoring_contract.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA/` (if present) — the DA ruling's own
  investigation/plan

## Related Code Areas
- `tools/evaluate_simq.py` — lines 34-38 (`ROUTING_KEYS`), lines 65-86 (`_run_calibration`)
- `tools/calibrate_simq.py` — lines 44-63 (`_load_profile_feature_flags`), lines 338-344 (call site)
- `config/simulation_quality/profiles/simq_routing_test.yaml` (create if absent)
- `config/simulation_quality/profiles/urban_political.yaml` — reference pattern for
  `feature_flags:` block usage
- `src/domains/optimization/feature_flags.py:16` — `ENABLE_ADVENTURE_ROUTING` definition
- `tests/simulation_quality/fixtures/grade_anchors.json` — `simq_routing_test_*` anchor entries

## Assumptions / Open Questions
- UQ-1: Does `config/simulation_quality/profiles/simq_routing_test.yaml` already exist with other
  content, or does it need to be created fresh? Confirm during investigation before assuming
  file-creation vs. file-edit.
- UQ-2: Should `evaluate_simq.py`'s `ROUTING_KEYS`/`_run_calibration` routing-flag branch be deleted
  outright, or kept as a deprecated fallback for one release? Default to deletion (cleanest, matches
  "no special-casing" goal) unless investigation finds another caller depends on the current
  signature.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
