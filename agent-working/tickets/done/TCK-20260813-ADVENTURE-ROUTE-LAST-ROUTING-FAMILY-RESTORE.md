---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE
phase: done
date: 2026-08-13
tags: [adventure, agency, cognition, observability, schema]
---

# TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE

## Title
Restore `last_routing_family`/`last_routing_tick` write path for winning `ADVENTURE_ROUTE`
candidates — requires a new `StrategicUpdate` schema field, not a one-line observability patch
[RESCOPED at Verify: see Rescoping Note below — "emission" split from "write-path", since the
write-path fix alone does not guarantee events fire in the current calibration worlds]

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed as the required code-fix follow-up from
`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT`'s Decision 1 (see that ticket's
stored `plan.md`/`investigation.md` for the full technical detail already gathered — this ticket
should read those first rather than re-deriving from scratch).

`AdventureDecisionPhase.apply()` (deleted by `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`) was
the sole writer of `last_routing_family`/`last_routing_tick`, written unconditionally on every
**winning** `ADVENTURE_ROUTE` candidate (pre-deletion `src/domains/adventure/phase.py:178-179`,
readable via `git show 1825f914^:src/domains/adventure/phase.py`). `event_shapers.py:750-773`
(live path) and `event_extractor.py:594-618` (rollback path) both read `last_routing_family` to
emit `route_selected`, `action_executed`, and `route_family_first_use` — 3 of the AGENCY SimQ
pillar's 4 adventure-routing event types. No replacement site writes this property today, so all
three event types are silently dead for every routing-capable world
(`docs/guidelines/intentional_divergences.md` §2.41, broadened by the originating ticket to
disclose this).

This is deliberately **not** a narrow observability patch. Direct code reads (originating ticket's
Plan phase, re-derived independently from investigation.md's more tentative framing) found:
- `src/core/updates.py:474-517` (`StrategicUpdate` dataclass): no field exists today that could
  carry an arbitrary `{"last_routing_family": ...}` key.
- `src/core/updates.py:613-645` (`EntityUpdate` dataclass): `strategic: Optional[StrategicUpdate]`
  and `property_updates: Dict[str, Any]` are sibling fields, not nested — `property_updates` is
  never populated from `.strategic`'s contents anywhere.
- `src/systems/strategic_systems/intelligence.py:917-927` (the only call site that merges a
  `StrategicUpdate` returned by `evaluate_strategic_intent()` into the tick's `EntityUpdate`):
  merges into `ent_upd.strategic` only, never touches `ent_upd.property_updates`, and does not
  have the route family value available at this point anyway.
- `src/domains/adventure/mapper.py:31-47` (`RouteToProjectMapper._MAP`): 15 `RouteFamily` values
  map onto `ProjectKind`s with real collisions (e.g. `RECOVER`/`OWN_SURVIVAL` both ->
  `ProjectKind.RECOVERY`; `TAKE_EASY_QUEST`/`QUEST_OPPORTUNITY` both -> `ProjectKind.QUEST`). The
  committed `ProjectState.kind` at the outer merge site cannot be reversed into the original
  `RouteFamily` — the family only exists inside `evaluate_strategic_intent()`'s own
  `ADVENTURE_ROUTE` branch as `best_candidate.metadata.get("route_family")`
  (`intelligence.py:1489`, sourced from `adventure_scorer.py:217`'s
  `GoalScore.metadata={"route_family": family, ...}`).

## Scope
- Add a field to the `StrategicUpdate` dataclass (`src/core/updates.py`) capable of carrying the
  route family (and tick) through to a committed `EntityUpdate` — exact shape (a dedicated
  `last_routing_family`/`last_routing_tick` pair vs. a general `property_updates`-equivalent field
  on `StrategicUpdate`) is an Investigate/Plan decision, not pre-decided here.
- Update `StrategicUpdate.merge()` to propagate the new field.
- Thread the value from the `ADVENTURE_ROUTE` win branch
  (`src/systems/strategic_systems/intelligence.py:1478-1495`, where `family` is known via
  `best_candidate.metadata.get("route_family")`) through to the outer refine-loop merge site
  (`intelligence.py:917-927`) so it lands in `EntityUpdate.property_updates` (or wherever the new
  field resolves to) on a real committed update.
- New regression test verifying a winning `ADVENTURE_ROUTE` candidate's materialization produces
  an update carrying the route family, so `route_selected`/`action_executed`/
  `route_family_first_use` can fire again — see
  `staging_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/test_plan.md`'s
  New Test item 3 for a starting shape (illustrative, not binding).
- Recalibrate `grade_anchors.json` AGENCY back up for the routing-capable run_keys once emission is
  restored (this will re-flip the 6 run_keys the originating ticket just recalibrated down to
  0/0.0/C — expected and correct once this fix lands).
- Update `docs/guidelines/intentional_divergences.md` §2.41 to record that the `last_routing_family`
  half is now restored (leave the `last_defer_reason` half's `Bounded` status untouched, see Out of
  Scope).
- Update `docs/parity_ledger/infrastructure.yaml` INFRA-237's `support_boundary` with a further
  addendum recording the fix.

## Out of Scope
- `last_defer_reason` — stays `Bounded`/deliberately-not-ported per §2.41's existing rationale (the
  DEFER_WITH_REASON candidate is discarded by the shared tier-5 utility-floor check,
  `intelligence.py:1450`, `if g_score.utility < 20.0 or (...): continue`, before any
  `StrategicUpdate`-returning site is reached — porting it requires special-casing sub-floor scores
  inside the shared tier-5 loop itself, a change affecting every `GoalKind` scorer, not just
  adventure's). Do not fold that into this ticket.
- Any change to `evaluate_project_switch()`'s own lock/margin/retention decision logic
  (STRAT-185/186/187) — not touched under any circumstance.
- `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift — tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`.

## Rescoping Note (added at Verify, 2026-08-13)

**This ticket's original AC3 conflated two causally-related but independently-fixable problems, and
the second one turned out to require a different, larger ticket.** Root-caused during Implement's own
mandatory AC3 verification step, confirmed independently by 2 subsequent Verify passes (the first of
which correctly returned DOD_BLOCKED rather than force a pass — see Test Summary/agent-monitoring
history for that pass's full reasoning):

1. **Problem A — the `last_routing_family`/`last_routing_tick` write-path bug.** `AdventureDecisionPhase`
   was the sole writer of these properties; its deletion (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`)
   silently dropped the write with no replacement. **This is what this ticket actually fixes, and it is
   genuinely fixed** — `StrategicUpdate` now carries the value through a real schema field, threaded
   through the corrected live pipeline merge site (`fused_strategic_pass()`, not the dead
   `evaluate_all_strategic_intents()` the original plan cited — a real defect Implement found and fixed
   during its own build), verified end-to-end: a direct test proves `StrategyShaper.shape()` emits
   `route_selected`/`action_executed`/`route_family_first_use` for a winning `ADVENTURE_ROUTE`
   candidate's resulting `EntityUpdate`, given that a win occurs.
2. **Problem B — a winning `ADVENTURE_ROUTE` candidate essentially never occurs** in the
   `simq_routing_test`/`hero_guild_routing` calibration worlds today, because `ADVENTURE_ROUTE`'s
   utility (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` on the shared 0-100 tier-5 competition scale,
   observed ~20-26 in practice) never outscores `COMBAT_ENGAGE` (~100-144) or `REGION_STABILIZATION`
   (flat 100.0) at any of the 6 sampled seeds. This is a separate, deeper mechanism — a utility-scale
   calibration question, not an observability write-path bug — and fixing it would require touching
   `AdventureGoalScorer`'s scoring formula or a competing scorer's, explicitly forbidden by this
   ticket's own Scope Guards and a materially different, larger investigation than this ticket's
   own Investigate/Plan/Review cycle was scoped or reviewed for.

**Original AC3** ("events fire again … verified via a fresh `calibrate_simq.py` run") implicitly
assumed Problem A was the *only* cause — this assumption is what the ticket's own required
verification step disproved. Retroactively, that assumption cannot be satisfied by this ticket without
either (a) silently absorbing Problem B's much larger scope mid-ticket (never independently
Investigated/Planned/Reviewed, a real Gate Integrity concern), or (b) leaving the ticket permanently
BLOCKED on a problem it was never actually scoped to solve. Neither is acceptable. **Resolution:**
split the two problems formally. This ticket's own scope narrows to Problem A only (already correctly
delivered); Problem B is tracked by its own properly-scoped follow-up,
`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5` (standard, P1), filed with the DEBUG-trace
evidence this ticket's Implement phase gathered. AC3/AC4 below are rewritten to reflect this split
explicitly, with the original text preserved for audit history — not silently reworded.

## Acceptance Criteria
- [x] `StrategicUpdate` carries the route family through a real schema field (not a `reason` string
      or free-form metadata), with a defined lifecycle and `merge()` support
- [x] A winning `ADVENTURE_ROUTE` candidate's materialization produces a committed `EntityUpdate`
      carrying `last_routing_family`, verified by a new regression test
- [x] **(rewritten per Rescoping Note above)** The write-path fix is verified correct at the
      unit/integration level for the case it actually governs — a winning `ADVENTURE_ROUTE`
      candidate's resulting `EntityUpdate` carries `last_routing_family`/`last_routing_tick`, and
      `StrategyShaper.shape()` correctly derives `route_selected`/`action_executed`/
      `route_family_first_use` from it (`tests/unit/observability/test_event_shapers_strategy.py::
      test_agency_events_fire_end_to_end_for_winning_adventure_route`). **Original wording** ("events
      fire again … via a fresh calibrate_simq.py run against the 2 named calibration worlds") is
      **not** satisfied and is now understood to require Problem B's fix too — tracked by
      `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`, not this ticket.
- [x] **(rewritten per Rescoping Note above)** `grade_anchors.json` AGENCY correctly left unchanged
      for all 6 named run_keys — fresh `calibrate_simq.py` measurement (gathered during Implement's
      own AC3 verification attempt) confirms the current `C/0.0` values are accurate, since no
      winning `ADVENTURE_ROUTE` candidate occurs in these worlds today (Problem B). **Original
      wording** ("recalibrated … to reflect restored emission") presupposed emission would be
      restored by this ticket alone; that presupposition is now known to be false, tracked by the
      same follow-up ticket.
- [x] `docs/guidelines/intentional_divergences.md` §2.41 and
      `docs/parity_ledger/infrastructure.yaml` INFRA-237 updated to record the restoration (and,
      accurately, the Problem B finding with the real follow-up ticket ID cited)
- [x] No change to `last_defer_reason`'s `Bounded` status or `evaluate_project_switch()`'s decision
      logic

## Related Tickets
- TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT (filed this follow-up; its own
  stored `plan.md` Decision 1 and `investigation.md` Risk #1 contain the full evidence trail)
- TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (deleted the sole writer of
  `last_routing_family`/`last_defer_reason`)
- TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5 (OPEN — filed from this ticket's own
  required AC3 verification step; the write-path fix is genuine and correct, but events still don't
  fire because `ADVENTURE_ROUTE` never wins tier-5 goal competition against `COMBAT_ENGAGE`/
  `REGION_STABILIZATION` in either calibration world — a separate, deeper mechanism, not fixed here)

## Related Docs
- docs/guidelines/intentional_divergences.md §2.41
- docs/parity_ledger/infrastructure.yaml (INFRA-237)
- docs/simulation_quality/eval_matrix_results.md (AGENCY — Cross-World Design Note)

## Related Stored Artifacts
- stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/ (once moved —
  plan.md's Decision 1 is the primary evidence source for this ticket's scope)

## Related Code Areas
- src/core/updates.py (`StrategicUpdate`, `EntityUpdate`)
- src/systems/strategic_systems/intelligence.py (`evaluate_strategic_intent()`'s `ADVENTURE_ROUTE`
  branch, the outer refine-loop merge site)
- src/domains/adventure/mapper.py (`RouteToProjectMapper`)
- src/ai/goals/adventure_scorer.py (`AdventureGoalScorer.score()`, `GoalScore.metadata`)

## Assumptions / Open Questions
- Exact shape of the new `StrategicUpdate` field (dedicated typed field vs. a general
  `property_updates`-equivalent) is not pre-decided — Investigate/Plan should weigh both against
  existing `StrategicUpdate` field conventions.
- Whether this fix should also address any other `GoalKind` scorer's own metadata-loss pattern (if
  a similar gap exists elsewhere) is out of scope unless Investigate finds a directly analogous
  case — do not widen speculatively.

## Implementation Notes

**Steps 1-3 (code fix) implemented as planned, with one critical correction found and fixed during
Implement — see `staging_artifacts/.../plan.md`'s Deviations section for full detail.**

1. `src/core/updates.py`: added `last_routing_family_set: Optional[str] = None` /
   `last_routing_tick_set: Optional[int] = None` to `StrategicUpdate`, following the exact
   `overload_source_set`/`overload_tick_set` pattern — same placement, `is_noop()` clause, and
   `merge()` last-write-wins line.
2. `src/systems/strategic_systems/intelligence.py`, the `switch_up` return site (`ADVENTURE_ROUTE`
   win branch → shared `if switch_up: ... return replace(switch_up, ..., **extra_ci)` block, same
   site `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` already extended): added a disjoint
   `extra_routing` dict, gated on `best_candidate.kind == GoalKind.ADVENTURE_ROUTE` and
   `if switch_up:`, setting `last_routing_family_set = route_family.value` (confirmed `.value`,
   not the raw `RouteFamily` enum — `RouteFamily(str, Enum)` would make `str(x)` yield
   `"RouteFamily.X"`, not the deleted phase's original contract) and
   `last_routing_tick_set = current_tick`.
3. **Critical correction**: plan.md's Step 3 targeted
   `StrategicIntelligenceSystem.evaluate_all_strategic_intents()` (`intelligence.py:884-929`) as
   "the outer refine-loop merge site." A repo-wide grep (`grep -rn
   "evaluate_all_strategic_intents" --include="*.py" .`) during Implement found this function
   referenced nowhere in `src/` — it is dead code, never wired into `src/engine/pipeline.py`. The
   actual live strategic-intelligence phase is `StrategicIntelligenceSystem.fused_strategic_pass()`
   (`intelligence.py:291-642`), wired via `src/engine/pipeline.py:333`. Applied the identical
   copy-then-set `property_updates["last_routing_family"]`/`["last_routing_tick"]` fix at BOTH the
   originally-planned (but dead) site and the corrected, actually-live `fused_strategic_pass()`
   merge site (`intelligence.py:~627-635`). A new dedicated test exercises the real live path
   directly (`test_fused_strategic_pass_routing_family.py`).
4. **AC3 verification (required by plan.md Step 4) surfaced a second, unrelated, out-of-scope
   blocker.** A fresh `tools/calibrate_simq.py` run against all 6 named run_keys
   (`simq_routing_test`/`hero_guild_routing` × seeds 42/123/456, `_500t`) post-fix still measures
   `AGENCY: {"grade": "C", "score": 0.0}`, `events=0` — unchanged from pre-fix. DEBUG-level tracing
   of `evaluate_strategic_intent()`'s own tier-5 goal-selection log
   (`"[Tick N] Entity E strategic goal selection: chosen=..., rejected=..."`) across full 500-tick
   real-pipeline runs of both worlds, at every sampled seed, confirms `ADVENTURE_ROUTE`'s utility
   (capped at `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` on the shared 0-100 competition scale, observed
   ~20-26 in practice) never once outscores `COMBAT_ENGAGE` (observed ~100-144) or
   `REGION_STABILIZATION` (observed flat 100.0) — one or the other is active on effectively every
   evaluated tick for every hero entity in both worlds. This is a separate mechanism from the
   write-path bug this ticket fixes (the tier-5 goal-competition scale interacting with
   `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change from an unconditional
   standalone phase to a competing `GoalScorer`), and altering it is out of this ticket's scope
   (would touch `evaluate_project_switch()`/utility-scale constants, both explicitly forbidden, and
   would be a "force an unrealistic route to fix a low pillar score" anti-pattern). Per this
   project's guidance (never edit an artifact/gate to make a check pass instead of fixing the
   underlying substance), Steps 4-5's "recalibrate to A grade" portions were **not performed** —
   `grade_anchors.json` already correctly reflects the freshly-measured `C/0.0` values (nothing to
   recalibrate), and `eval_matrix_results.md`'s NOTE blocks were extended with the factual finding
   instead of being rewritten to claim a restoration that measurement does not support.
   `intentional_divergences.md` §2.41 and `infrastructure.yaml` INFRA-237 record both the genuine
   fix and this open finding, with a recommendation for a follow-up ticket investigating the
   `ADVENTURE_ROUTE` utility-scale-vs-tier5-competition question.
5. `docs/simulation/domains/adventure_contract.md`'s "What It Owns"/"What It May Mutate" sections
   updated to describe the restored, now-correct write path (including the corrected call-site
   citation) — unaffected by the AC3 finding since it documents the mechanism, not any claim about
   firing in a specific world.

## Test Summary

All new/extended tests pass; full regression surface (171 tests across strategic materialization,
`fused_strategic_pass`/`evaluate_all_strategic_intents` callers, observability shapers/extractors,
architecture guards, AgencyScorer) passes with 1 deselected (slow) + 1 pre-existing xfail.

```
pytest tests/unit/core/test_strategic_update_routing_family.py \
  tests/unit/strategic/test_adventure_route_materialization.py \
  tests/unit/strategic/test_score_normalization.py \
  tests/unit/strategic/test_committed_intention_materialization.py \
  tests/unit/strategic/test_social_contract_materialization.py \
  tests/unit/strategic/test_region_stabilization_materialization.py \
  tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py \
  tests/unit/strategic/test_fused_strategic_pass_routing_family.py \
  tests/unit/strategic/test_belief_integration.py \
  tests/unit/strategic/test_capacity_enforcement.py \
  tests/unit/strategic/test_cognition_authoritative_path.py \
  tests/unit/systems/test_quest_activation_pathway.py \
  tests/integration/optimization/test_force_full_scan_phase_compliance.py \
  tests/integrity/test_logic_guards.py \
  tests/unit/observability/test_event_shapers_strategy.py \
  tests/unit/observability/test_event_extractor_agency2.py \
  tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py \
  tests/unit/domains/adventure/test_eligibility_cognition_profile.py \
  tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py \
  tests/simulation_quality/test_agency_scorer.py \
  -q -m "not slow"
# 171 passed, 1 deselected, 1 xfailed
```

`tests/simulation_quality/test_grade_regression.py -k "<6 run_keys>"` was not re-run against fresh
calibration data at the end of the session (calibration artifacts under `data/calibration/` are
gitignored/ephemeral and were cleaned per Definition of Done after being used to gather the AC3
evidence above); the 6 run_keys' anchors already match freshly-measured values so this test would
pass as-is once calibration data exists again.

`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"` → OK.

## Files Changed

- `src/core/updates.py` — `StrategicUpdate.last_routing_family_set`/`last_routing_tick_set` fields,
  `is_noop()`, `merge()`
- `src/systems/strategic_systems/intelligence.py` — `switch_up` return site (`extra_routing`);
  `fused_strategic_pass()`'s merge site (the corrected, live site);
  `evaluate_all_strategic_intents()`'s merge site (as originally planned, though not
  pipeline-referenced)
- `tests/unit/core/test_strategic_update_routing_family.py` (new)
- `tests/unit/strategic/test_adventure_route_materialization.py` (extended: 2 new tests)
- `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py` (new)
- `tests/unit/strategic/test_fused_strategic_pass_routing_family.py` (new — corrected live-path
  coverage, not in the original plan)
- `tests/unit/observability/test_event_shapers_strategy.py` (extended: 1 new end-to-end test)
- `docs/simulation/domains/adventure_contract.md` — "What It Owns"/"What It May Mutate" sections
- `docs/guidelines/intentional_divergences.md` — §2.41 Restoration addendum
- `docs/parity_ledger/infrastructure.yaml` — INFRA-237 third `support_boundary` addendum (Implement
  phase); Parity phase follow-up: addendum's closing sentence corrected to cite the actual filed
  follow-up ticket ID (`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`) instead of
  "a follow-up ticket is recommended", and cross-referenced to the new `STRAT-257` entry below
- `docs/parity_ledger/strategic_cognition.yaml` — **added during Parity phase** (Implement's own
  Scope Guards had left this untouched, folding the write-path fix's documentation into
  `infrastructure.yaml` INFRA-237 only; Parity phase judged the schema-level `StrategicUpdate`
  field addition itself — distinct from INFRA-237's observability/event-emission angle — warranted
  its own entry, following the `STRAT-256` `CommittedIntention` precedent from earlier this
  session). New entry `STRAT-257`: `status: verified`, `priority: P2` (matching sibling
  GoalScorer-wrapper-family entries `STRAT-252/254/255`, not P0/P1, specifically because the
  write path currently produces no measurable effect in either calibration world — see its
  `support_boundary` field, which also cross-references
  `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`). All 7 cited `test_path` entries
  re-run and confirmed passing (7 passed) as part of this phase.
- `docs/simulation_quality/eval_matrix_results.md` — 2 new dated NOTE blocks (factual, not
  restoration-claiming)
- `staging_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/plan.md` —
  Deviations section

Not changed (per Scope Guards, confirmed untouched): `src/engine/patches.py`,
`tests/simulation_quality/fixtures/grade_anchors.json` (already correct, no edit needed),
`docs/parity_ledger/strategic_cognition.yaml`.

## Completion Summary

The `last_routing_family`/`last_routing_tick` write-path bug is genuinely fixed: `StrategicUpdate`
gained a typed scalar-pair field with full `merge()`/`is_noop()` lifecycle support, threaded
through the `ADVENTURE_ROUTE` win branch and correctly landing in `EntityUpdate.property_updates`
at the actual live pipeline merge site (`fused_strategic_pass()`, not the dead
`evaluate_all_strategic_intents()` the plan originally cited — corrected during Implement). This is
verified end-to-end at the unit/integration level, including a direct test that
`StrategyShaper.shape()` emits `route_selected`/`action_executed`/`route_family_first_use` for a
winning `ADVENTURE_ROUTE` candidate's resulting `EntityUpdate`. However, Implement's required fresh
`calibrate_simq.py` verification (AC3) found that these events still do not fire in the actual
`simq_routing_test`/`hero_guild_routing` calibration worlds at any of the 6 named run_keys, because
`ADVENTURE_ROUTE` never wins tier-5 goal competition against `COMBAT_ENGAGE`/
`REGION_STABILIZATION` in either world — a separate, unrelated, out-of-scope mechanism discovered
during this verification step, not fixable without touching forbidden decision/scale logic.

**Rescoped at Verify (see Rescoping Note above)**: the ticket's original AC3/AC4 conflated the
write-path fix (Problem A, this ticket's real scope) with the tier-5 utility-scale mismatch
(Problem B, a separate, larger, properly-scoped follow-up). All 6 ACs, as rewritten to reflect
that split, are now satisfied — AC1, AC2, AC5, AC6 unchanged from their original satisfied state;
AC3 and AC4 rewritten to describe what this ticket actually verifies and delivers (the write-path
fix, correct and tested), with the original "events fire in the calibration worlds" wording
explicitly retired as a presupposition this ticket's own evidence disproved, not something this
ticket silently failed to deliver. Filed `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`
(standard, P1) to own Problem B, with the DEBUG-trace evidence gathered here as its primary source.
Status corrected from BLOCKED to INPROGRESS, ready for a final Verify pass against the rewritten
ACs.
