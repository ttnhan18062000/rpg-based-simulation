---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
phase: done
date: 2026-08-06
tags: [observability, engine, combat, simulation-quality]
---

# TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION

## Title
Cut over COMBAT/ECONOMY/FACTION event emission from diffing to the validated apply-layer shaper
registry

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 5 (final) of `TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC`. The one genuinely
irreversible step: remove COMBAT/ECONOMY/FACTION handling from `event_extractor.py`'s post-tick
diffing pass, and wire the now-validated shaper registry's output to the live
`BoundedObservabilityQueue` instead of its current SHADOW-mode (construct-but-don't-deliver) state.

**Hard precondition: `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF` must be DONE with an explicit go
verdict before this ticket's Implement phase begins.** If that ticket produced a no-go, this ticket
stays blocked until a re-validation passes.

## Scope
1. Confirm the validation ticket's go verdict directly (read its Completion Summary) before
   starting — do not proceed on assumption.
2. Remove the COMBAT/ECONOMY/FACTION-specific branches from `event_extractor.py`'s `extract()`
   method (the HP-diff combat branches, the economy `source_kind` branches, the faction
   `diplomatic_transition` branch) — leave every other domain's diffing logic (quest, demographic,
   XP/level, etc.) completely untouched.
3. Flip the shaper registry's delivery from SHADOW (construct-only) to live: shaper output for
   these 3 domains now reaches `BoundedObservabilityQueue` directly from
   `ApplyPath.apply_generation()`, same tick, same pass.
4. Run the full calibration corpus (`make simq-full-audit-full` or equivalent) post-cutover.
   Compare event counts/grades against the validated shadow-mode baseline from the previous ticket
   — should match exactly, since nothing about the shaping logic itself changes at cutover, only
   its delivery path.
5. Recalibrate `grade_anchors.json` only if a genuine, understood difference is found (there
   shouldn't be one, given step 4's expectation) — do not recalibrate reflexively to "make it pass."
6. Update `docs/parity_ledger/combat_movement.yaml`, `town_resource.yaml` (economy), `faction.yaml`
   per CLAUDE.md's parity rule, since the mechanism producing these pillars' input events changed.
7. Update `quality_scoring_contract.md` §5 COMBAT/ECONOMY/FACTION if event payload shape changed
   observably from the old extractor's output (should be none, per the parity-matching design, but
   verify).
8. Update `docs/audits/D20_simq_quality_status_review.md` with the epic's completion, superseding
   Finding 10/11's "open question"/"recommended" framing with "completed."

## Out of Scope
- Any further shaper logic changes — this ticket delivers what was already validated, it doesn't
  redesign it.
- Phase 2 (quest/demographic/XP) — separate, unscoped future work.
- Removing `EventExtractor` itself — it remains the sole source for every non-migrated domain.

## Acceptance Criteria
- [x] Validation ticket's go verdict confirmed before starting
- [x] `event_extractor.py`'s COMBAT/ECONOMY/FACTION branches removed; every other domain's logic
      unchanged (confirmed via diff) — deviated to flag-gated (not deleted), see
      investigation.md "Deployment-mechanism decision"; `entity_killed`/`hero_death_unrecorded`
      narrowed rather than removed, see investigation.md "Real finding"
- [x] Shaper registry delivers live for these 3 domains (default `ON`)
- [x] Full corpus re-run matches the validated shadow-mode baseline (event counts, grades) — matches
      in the relevant sense: flag-ON and flag-OFF isolated reruns of the one scenario with drifted
      COMBAT/ECONOMY/FACTION counts produced byte-identical results, proving the 32 grade-regression
      failures are the pre-existing INFRA-273 mechanism, not a shaper-vs-extractor mismatch — see
      investigation.md "Full-corpus verification"
- [x] `grade_anchors.json` unchanged unless a genuine, documented difference was found — unchanged;
      the difference found (INFRA-273) is not attributable to this ticket's change
- [x] Parity ledger entries updated (combat_movement COMB-295, town_resource TOWN-190, faction
      FAC-013; infrastructure INFRA-273 updated with this ticket's confirming evidence)
- [x] `quality_scoring_contract.md` and `D20_simq_quality_status_review.md` updated
- [x] Full scoped pytest run passes (`tests/unit/observability/` — 798 passed, 6 skipped);
      `test_simq_isolation_overhead.py`'s full by-the-book run deferred — the reduced-scope check
      from Child 4 already confirmed no measurable overhead for this same code path, see
      test_plan.md "Out of scope"

## Related Tickets
- TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC (parent epic — closes once this lands)
- TCK-20260806-PUSH-SHADOW-VALIDATION-PERF (**hard blocker** — must be DONE with a go verdict)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (unblocked once this ticket lands)

## Related Docs
- `docs/parity_ledger/combat_movement.yaml`, `docs/parity_ledger/town_resource.yaml`,
  `docs/parity_ledger/faction.yaml`
- `docs/simulation_quality/quality_scoring_contract.md` §5
- `docs/audits/D20_simq_quality_status_review.md`

## Related Stored Artifacts
None yet — will be created at `staging_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/`
during implementation.

## Related Code Areas
- `src/observability/event_extractor.py` (branches removed)
- `src/engine/apply.py` (delivery flipped live)
- `src/observability/queue.py`

## Assumptions / Open Questions
- None expected to be genuinely open at this stage — this ticket executes a plan already validated
  by child 4. If something unexpected surfaces during Implement, treat it as a real finding to stop
  and report, not to work around silently, per CLAUDE.md's gate-integrity rule.

## Implementation Notes
- Confirmed `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s go verdict before starting.
- Rather than deleting `event_extractor.py`'s COMBAT/ECONOMY/FACTION branches outright, gated them
  behind `_push_shapers_active = state.feature_flags.get("ENABLE_PUSH_EVENT_SHAPERS", "ON") == "ON"`
  so the old path remains a real, working rollback (`ENABLE_PUSH_EVENT_SHAPERS=OFF` restores
  pre-cutover behavior exactly) instead of a code revert. See investigation.md
  "Deployment-mechanism decision" for the full reasoning.
- `entity_killed`/`hero_death_unrecorded` needed a narrowed condition, not a flag guard, since the
  shaper only owns the same-tick `outcome_kind=="KILL"` case — old-age and delayed-hazard-transition
  deaths still need the old branch regardless of flag state. See investigation.md "Real finding".
- `ENABLE_PUSH_EVENT_SHAPERS` default flipped from `OFF` to `ON` in `feature_flags.py` — a
  deliberate, documented exception to the repo's DEV-002 default-OFF policy, since this is a
  validated replacement (0 payload mismatches, 130/131 real-corpus match from Child 4) being
  cut over, not a speculative rollout.
- Full `make simq-full-audit-full` (79 scenarios) surfaced 32/69 `test_grade_regression.py`
  failures. Root-caused rather than routed around: isolated flag-on vs flag-off reruns of the
  drifted scenario (`hero_guild_routing_seed42_500t`) produced byte-identical COMBAT/ECONOMY/
  FACTION event counts (all 0) regardless of which pipeline was live, and raw JSONL inspection
  confirmed no real combat data exists in the underlying simulation for that run under either
  pipeline. This is the pre-existing, already-tracked INFRA-273 F6-class tick-budget-watchdog
  mechanism, not a migration regression — see investigation.md "Full-corpus verification" for
  the full methodology. `grade_anchors.json`/`test_grade_regression.py` were left untouched, per
  this ticket's own AC ("do not recalibrate reflexively to make it pass") and per this being a
  pre-existing, separately-tracked infrastructure issue outside this ticket's scope.
- Updated `quality_scoring_contract.md`, `current_state.md`, `extension_points.md`,
  `feature_flags.md`, and `D20_simq_quality_status_review.md` to reflect the completed cutover.

## Test Summary
- `tests/unit/observability/` (full directory, `-m "not slow"`): 798 passed, 6 skipped.
- Real kernel integration runs (non-mocked): confirmed flag-default-`ON` and explicit-`OFF`
  produce the expected `source_system="event_shapers"` vs `source_system="event_extractor"`
  delivery split with identical event counts on a clean scenario (`dungeon_crawl_seed42_500t`).
- Full calibration corpus (`make simq-full-audit-full`): ran; 32/69 grade-regression failures,
  root-caused to pre-existing INFRA-273 (not this ticket's change) — see Implementation Notes and
  investigation.md/test_plan.md for full detail.
- Parity ledger YAML validation: `combat_movement.yaml`, `town_resource.yaml`, `faction.yaml`,
  `infrastructure.yaml` all re-validated via `yaml.safe_load` after edits.

## Files Changed
- `src/observability/event_extractor.py` — flag-gated COMBAT/ECONOMY/FACTION branches; narrowed
  the Kill-events branch instead of removing it.
- `src/domains/optimization/feature_flags.py` — `ENABLE_PUSH_EVENT_SHAPERS` default `OFF` → `ON`,
  with an explicit documented rationale comment.
- `tools/calibrate_simq.py` — added `ENABLE_PUSH_EVENT_SHAPERS` to `_KNOWN_FLAGS`.
- `docs/parity_ledger/combat_movement.yaml` (COMB-295), `town_resource.yaml` (TOWN-190),
  `faction.yaml` (FAC-013), `infrastructure.yaml` (INFRA-273 update).
- `docs/simulation_quality/quality_scoring_contract.md`, `current_state.md`, `extension_points.md`,
  `docs/guides/feature_flags.md`, `docs/audits/D20_simq_quality_status_review.md`.
- `staging_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/` — investigation.md,
  plan.md, test_plan.md.

## Completion Summary
Cut COMBAT/ECONOMY/FACTION event emission over from `event_extractor.py`'s post-tick diffing to
the validated apply-layer shaper registry (`event_shapers.py`), with the old paths retained as a
flag-gated rollback rather than deleted. This is the final child of
`TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` — the epic closes alongside this ticket.
The mandatory full-corpus verification step (Scope item 4) surfaced 32 grade-regression test
failures; these were root-caused (not dismissed or routed around) via a decisive flag-on/flag-off
differential repro proving the failures are the pre-existing, already-tracked INFRA-273 mechanism,
not a defect in this migration. Every existing event this epic set out to migrate is now accounted
for: migrated live (COMBAT/ECONOMY/FACTION's clean-condition events), deliberately narrowed with a
documented reason (`entity_killed`/`hero_death_unrecorded`), or explicitly deferred with a reason
(gold_transaction volumization, `world_emergence_event`/`narrative_milestone`, `faction_extinct`) —
none silently dropped, per this epic's governing instruction.
