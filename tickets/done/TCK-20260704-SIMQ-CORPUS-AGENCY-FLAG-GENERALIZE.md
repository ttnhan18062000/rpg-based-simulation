---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, agency, feature-flags, calibration]
---

# TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE

## Title
Generalize ENABLE_ADVENTURE_ROUTING activation into the per-world feature_flags profile mechanism

## Status
DONE

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
Followed plan.md's 10-step ordered plan exactly (2nd-pass architecture-approved), no deviations:

1. Added `feature_flags:\n  ENABLE_ADVENTURE_ROUTING: "ON"` to
   `config/simulation_quality/profiles/simq_routing_test.yaml`, matching `urban_political.yaml`'s
   existing `feature_flags:` block style (blank line, then block) exactly.
2. Removed `ROUTING_KEYS` (module-level set) from `tools/evaluate_simq.py` entirely. Simplified
   `_run_calibration()` by dropping the `routing_flag` parameter and the
   `os.environ["ENABLE_ADVENTURE_ROUTING"]` set/restore branch — the function is kept (not
   inlined/removed) because it still centralizes the `sys.argv` monkey-patch/restore around the
   in-process `cal_mod.main()` call, which is an independent concern from the routing special case
   (confirmed by re-reading the function post-simplification: `import os` at module scope remains
   needed for `os.path.join(os.path.dirname(__file__), "..")` on line 27, so no now-unused import
   was left behind). Removed the `routing = run_key in ROUTING_KEYS` line and the routing arg at
   the `_run_calibration(name, seed, ticks)` call site in `main()`.
3. Live re-ran all 3 `simq_routing_test_seed{42,123,456}_500t` scenarios individually
   (`python3 tools/evaluate_simq.py --scenario <run_key>`) under the new profile-YAML-only
   mechanism (no env var set anywhere in this session) — all 3 produced 10/10 PASS against
   `grade_anchors.json`, matching the plan's pre-implementation dry-run findings exactly, now
   confirmed live post-code-change. (Seed 456's anchor has a pre-existing, out-of-scope
   COGNITION/NARRATIVE one-grade-step disagreement with the actual report — documented in
   investigation.md/plan.md §3 as predating this ticket; both anchor grades still pass the
   existing ±1 tolerance band, so this is not a regression introduced here.)
4. `tests/simulation_quality/test_evaluate_harness.py` — 17/17 passed unchanged (only imports
   `_within_band`/`_compare`/`_parse_run_key`, none of which were touched).
5. `make evaluate-full` (full corpus re-run, all 14 fast anchor scenarios including the 3 routing
   ones) — exit 0, 400 pillars checked, 0 regressions, 0 missing.
6. `make evaluate` (dry-run against the regenerated `data/calibration/` reports) — exit 0, 400
   pillars checked, 0 regressions, 0 missing — identical to step 5's live numbers.
7. `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` returns only
   `simq_routing_test.yaml` — no leakage to `urban_political.yaml`, `dungeon_crawl.yaml`,
   `default.yaml`, or any other archetype world's profile. `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`
   is not reversed.
8. Added the plan's exact drafted documentation paragraph to
   `docs/simulation_quality/quality_scoring_contract.md` §11.6 "Standing Evaluation Harness",
   immediately after the "Anchor update workflow" 5-step list and before the `---` separator
   preceding "## 12. Acceptance Criteria".
9. No test files were modified (only `tools/evaluate_simq.py`, one config YAML, and one doc were
   changed) — confirmed via `git status --porcelain` before concluding — so `graphify update .`
   was correctly skipped per the plan's stated trigger scope (`src/`/`tests/` only).

No deviations from plan.md were needed; no Deviations entry was required in plan.md.

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This ticket's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
(later renamed to `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`) point to a
pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact this
ticket drew from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by this ticket and/or
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` / `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.

## Test Summary
- `python3 tools/evaluate_simq.py --scenario simq_routing_test_seed42_500t` — 10/10 PASS
- `python3 tools/evaluate_simq.py --scenario simq_routing_test_seed123_500t` — 10/10 PASS
- `python3 tools/evaluate_simq.py --scenario simq_routing_test_seed456_500t` — 10/10 PASS
  (pre-existing anchor/report grade-step gap on COGNITION/NARRATIVE, both within ±1 tolerance,
  documented pre-existing in investigation.md/plan.md §3, not introduced by this ticket)
- `python3 -m pytest tests/simulation_quality/test_evaluate_harness.py -v` — 17 passed, 0 failed
- `make evaluate-full` — exit 0, 400 pillars checked, 0 regressions, 0 missing
- `make evaluate` (dry-run) — exit 0, 400 pillars checked, 0 regressions, 0 missing
- `grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` — only
  `simq_routing_test.yaml` (no leakage to any other archetype world)

## Files Changed
- `config/simulation_quality/profiles/simq_routing_test.yaml` — added `feature_flags:
  {ENABLE_ADVENTURE_ROUTING: "ON"}` block
- `tools/evaluate_simq.py` — removed `ROUTING_KEYS` module-level set; simplified
  `_run_calibration()` (dropped `routing_flag` param + env-var set/restore branch); removed the
  `routing = run_key in ROUTING_KEYS` call-site line and routing arg
- `docs/simulation_quality/quality_scoring_contract.md` — added a documentation paragraph to
  §11.6 "Standing Evaluation Harness" describing the profile-driven (not harness-driven)
  feature-flag activation mechanism
- `data/calibration/simq_routing_test_seed{42,123,456}_500t/quality_report.json` — regenerated
  under the new mechanism (content is byte/grade-identical to the previously committed reports;
  not part of this ticket's durable Files Changed list beyond noting they were regenerated as
  part of step 3/5 verification)

## Completion Summary
Migrated `ENABLE_ADVENTURE_ROUTING` activation for `simq_routing_test` off `tools/evaluate_simq.py`'s
hardcoded `ROUTING_KEYS`/env-var special case and onto the already-generic `feature_flags:`
profile-YAML mechanism `urban_political.yaml` already uses for `ENABLE_BELIEF_ASSIMILATION`/
`ENABLE_SOCIAL_COOPERATION` — `calibrate_simq.py::_load_profile_feature_flags()` required zero
changes, confirmed genuinely generic across any flag name. `simq_routing_test.yaml`'s profile now
carries `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}` directly; `ROUTING_KEYS` and the
env-var set/restore branch in `_run_calibration()` are fully removed (the function itself is
retained, simplified, since its `sys.argv` monkey-patch/restore purpose is independent of routing).

Behavior preservation was verified three times independently, not just once: empirically during
investigation (seed42 A/B test), again during planning (all 3 seeds live-tested pre-implementation),
and again during implementation (all 3 seeds re-run post-code-change) — all three passes produced
identical grades/normalized-scores to the pre-existing anchors. `make evaluate-full` (full corpus
re-run) and `make evaluate` (dry-run diff) both independently confirmed 0 regressions across all
400 pillars. A `grep` confirms no other world's profile YAML picked up the flag. One pre-existing,
unrelated discrepancy was found and explicitly not touched: `simq_routing_test_seed456_500t`'s
committed anchor has COGNITION/NARRATIVE reversed against the actual report (COGNITION=A vs
anchor=S, NARRATIVE=S vs anchor=A) — both directions pass only via the ±1-grade tolerance band, and
this predates and is unrelated to this ticket's mechanism migration.

Architecture review caught one real defect during planning (before any code was written): the
plan's own verification steps had the `make evaluate`/`make evaluate-full` Makefile targets swapped,
with one command (`make evaluate --dry-run`) being a silent no-op since `--dry-run` is GNU Make's
own flag, not passed through to the underlying script. Fixed and re-verified before implementation
began.
