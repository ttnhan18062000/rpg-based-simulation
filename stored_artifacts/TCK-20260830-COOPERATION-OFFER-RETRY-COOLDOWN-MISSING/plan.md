---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING
artifact_type: plan
tags: [social, simulation-quality]
---

# Implementation Plan — TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING

## Summary

Add a per-entity, tick-based retry cooldown that stops a cooperation offer from being
re-proposed on the tick immediately after a prior offer expired. The cooldown reuses the
existing, live `IdentityComponent.cooldowns: Dict[str, int]` field (a proven skill-cooldown
mechanism, not a new dataclass field) under a new fixed key `"cooperation_offer_retry"`. The
cooldown is **set** in `ContractService.reap_expired_offers()` (`src/systems/social_systems/contracts.py:304-331`)
only when the reaped `OFFERED` contract's `kind == ContractKind.RECRUITMENT`, and **checked** in
`CooperationDecisionService.select()` (`src/domains/cooperation/services.py:26-133`) to gate the
existing "good partner exists" branch, falling through unchanged to the existing SOLO/
DEFER_NO_PARTNER logic while on cooldown. No changes to `CooperationIntentBridge.map_decision()`
or `phase.py`. After the code fix lands, a real `tools/evaluate_simq.py` corpus trial against
`highland_traverse_seed42_200t` confirms the fix actually reduces `contract_expired_offer`
density, and only then is that one run_key's `SOCIAL` block in `grade_anchors.json` updated to
the fresh real score.

**Correction to investigation.md**: the set-point method is owned by class `ContractService`, not
`SocialContractSystem`, in `src/systems/social_systems/contracts.py`. `SocialContractSystem` is a
distinct class defined in the same file (line 11, with `check_expirations()` at line 65) that
handles the separate status-transition expiry path; `src/systems/social_contract.py` is a
compat re-export shim (`from src.systems.social_systems.contracts import SocialContractSystem`)
which is why the two names look interchangeable in older test imports. `reap_expired_offers()` is
confirmed at `src/systems/social_systems/contracts.py:305`, called as
`ContractService.reap_expired_offers(state, u)` from `src/engine/pipeline.py:368`. All step
references below use the correct class name.

## Steps

### Step 1 — Set the retry cooldown when a RECRUITMENT offer is reaped

**Files:** `src/systems/social_systems/contracts.py`

**Change:**
- Add a module-level constant near the top of the file (after imports, before class
  `SocialContractSystem`): `COOPERATION_OFFER_COOLDOWN_TICKS = 15`.
- Add `IdentityUpdate` to the existing `from src.core.updates import ...` line
  (`src/systems/social_systems/contracts.py:6`, currently
  `StrategicUpdate, SocialBondUpdate, EntityUpdate, StateUpdate, SocialUpdate`) — confirmed
  `IdentityUpdate` is defined in `src/core/updates.py:221-267` with field
  `cooldown_updates: Dict[str, int]` at `updates.py:237`.
- In `ContractService.reap_expired_offers()` (`src/systems/social_systems/contracts.py:304-331`),
  inside the existing `for e_id, entity in state.entities.items():` loop, after the existing
  `expired_ids` collection loop (`contracts.py:316-319`) and inside the existing
  `if expired_ids:` block (`contracts.py:321-329`): check whether any of the contracts named in
  `expired_ids` has `contract.kind == ContractKind.RECRUITMENT` (the same `contract` objects
  already being iterated at `contracts.py:317`, from `entity.strategic.contracts.items()`;
  `ContractState.kind: ContractKind` confirmed at `src/core/strategic.py:221`). If so, also set
  `identity=IdentityUpdate(cooldown_updates={"cooperation_offer_retry": current_tick + COOPERATION_OFFER_COOLDOWN_TICKS})`
  on that entity's `EntityUpdate`, merged alongside the existing
  `strategic=replace(strat_up, contracts_remove=...)` write (`contracts.py:325-329`) in the same
  `replace(ent_upd, ...)` call — i.e. `refined_entity_updates[e_id] = replace(ent_upd, strategic=..., identity=IdentityUpdate(...))`.
  `current_tick = state.tick` is already bound at `contracts.py:313`.
- **Other writers of `cooldown_updates` (shared resource — must be checked, not assumed
  non-conflicting):** the only production writer of `IdentityUpdate.cooldown_updates` today is
  `src/engine/domain/skill_actions.py:113` (`identity=IdentityUpdate(cooldown_updates={skill_id: next_ready_tick})`).
  Confirmed via `grep -rn "cooldown_updates" src/` — only two production sites: that one and this
  new one. Merge behavior at two layers: (a) `IdentityUpdate.merge()`
  (`src/core/updates.py:266`, `{**self.cooldown_updates, **other.cooldown_updates}`) is used if
  two `IdentityUpdate`s for the same entity in the same tick get merged before apply — a plain
  dict union, later value wins per key; (b) the authoritative apply path
  (`src/engine/patches.py:188` `cds = dict(new_id.cooldowns)`, `patches.py:208`
  `cds.update(u_id.cooldown_updates)`) additively updates the entity's persisted `cooldowns` dict
  — existing keys (including any real skill_id cooldowns) are preserved, only the specific keys
  present in this tick's `cooldown_updates` are overwritten. Since `"cooperation_offer_retry"` is
  a literal string that can never collide with a real `skill_id` (skill ids come from
  `SKILL_REGISTRY`, all real skill names), there is no collision risk with the skill-cooldown
  writer. `reap_expired_offers()` itself has exactly one call site
  (`src/engine/pipeline.py:368`, once per tick, phase `expired_offers`) so there is no intra-tick
  double-write of this same key from this same function.
- Confirm the proposer's own `EntityState` is the one whose `contracts` dict holds the reaped
  offer (needed to confirm the cooldown lands on the correct entity, the proposer, not the
  target): `CooperationIntentBridge.map_decision()` (`src/domains/cooperation/services.py:168-176`)
  creates the contract via `ContractService.create_recruitment_contract(source_id=entity.id,
  target_id=partner_id, ...)` and returns `EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(contracts_add_or_update=[contract]), ...)`
  — i.e. the contract is applied into the *proposer's own* `entity.strategic.contracts`, not the
  target's. `reap_expired_offers()`'s existing loop (`contracts.py:315`, `for e_id, entity in
  state.entities.items(): for c_id, contract in entity.strategic.contracts.items()`) therefore
  already iterates `e_id` = the proposer for each reaped record, so setting the cooldown on that
  same `e_id` is correct with no extra lookup needed.

**Do NOT touch:** `SocialContractSystem.check_expirations()` (`contracts.py:11-77`, the separate
status-transition expiry path covered by SOC-240) — leave it untouched; `LOAN` or any other
`ContractKind` branch — the cooldown write must be conditioned on `ContractKind.RECRUITMENT`
only, never applied unconditionally to every reaped `OFFERED` contract regardless of kind; the
existing `contracts_remove` write itself (`contracts.py:327`) — do not change removal behavior,
only add the new identity write alongside it.

**Verify:** `test_reap_expired_recruitment_offer_sets_retry_cooldown` (new, Step 3),
`test_reap_expired_loan_offer_does_not_set_cooperation_cooldown` (new, Step 3).

---

### Step 2 — Gate the cooperation decision on the retry cooldown

**Files:** `src/domains/cooperation/services.py`

**Change:**
- In `CooperationDecisionService.select()` (`src/domains/cooperation/services.py:26-133`), after
  the existing early-return `if not help_needs:` block (`services.py:39-47`) and before the
  personality-effects block (`services.py:49-53`), add:
  `on_offer_cooldown = state.tick < entity.identity.cooldowns.get("cooperation_offer_retry", 0)`.
  `entity: EntityState` and `state: AuthoritativeState` are both existing parameters of `select()`
  (`services.py:29,33`); `entity.identity.cooldowns` is `IdentityComponent.cooldowns: Dict[str,
  int]`, confirmed at `src/core/state.py:486`.
- Change the existing `if best_report:` branch (`services.py:90`) to
  `if best_report and not on_offer_cooldown:`. No other line inside that branch
  (`services.py:91-112`) changes. When the condition is `False` because `on_offer_cooldown` is
  `True`, execution falls through unchanged to the existing "No suitable partner or solo
  preferred" logic (`services.py:114-133`, the `solo_score >= 0.5` / `DEFER_NO_PARTNER` branches)
  — confirmed by direct read that these lines require no modification since they are reached
  purely by falling out of the `if` block.
- No import changes needed — `state` and `entity` are already in scope.

**Do NOT touch:** `CooperationIntentBridge.map_decision()` (`services.py:136-196`) — it receives
whatever `CooperationDecisionResult` `select()` returns and needs no cooldown-awareness of its
own, since `select()` will never return `REQUEST_HELP`/`HIRE_SUPPORT` while on cooldown; the
`rejected_partners`/`trace` dict construction inside the `for rep in fit_reports:` loop
(`services.py:70-87`) — partner rejection reasons (low trust, poor fit, cost) are unrelated to the
cooldown gate and must keep working exactly as today; the `solo_score >= 0.5` /
`DEFER_NO_PARTNER` fallback logic itself (`services.py:114-133`) — do not add new
cooldown-specific branches there, the existing fallback must be reused as-is; `phase.py` — no
changes required per investigation.md's Recommendation §4 (gating in `map_decision()` instead
would produce a misleading `CooperationDecisionSelectedEvent`/`PartnerSelectedEvent` trace).

**Verify:** `test_cooperation_offer_retry_blocked_within_cooldown_window` (new, this step),
`test_cooperation_offer_retry_allowed_after_cooldown_expires` (new, this step), plus the full
existing `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py` suite must
still pass byte-identical (every existing fixture there constructs entities via `V2EntityBuilder`
with no `cooldowns` argument, defaulting `entity.identity.cooldowns == {}`, so
`state.tick < {}.get("cooperation_offer_retry", 0)` i.e. `state.tick < 0` is `False` for every
existing test's positive `tick` values — confirmed by reading
`tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py:16-53`, all of which
use `tick=1`).

---

### Step 3 — New unit tests for the set point and check point

**Files:**
- `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`
- `tests/unit/social/test_contract_lifecycle_phase7.py`

**Change:**
1. `test_cooperation_offer_retry_blocked_within_cooldown_window` — added to
   `tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py`, adjacent to the
   existing `test_risky_objective_selects_request_help_when_good_partner_exists()`
   (`test_phase7_cooperation_decision_service.py:25-51`, read in full — confirmed exact fixture
   shape: `V2EntityBuilder(1)...build()` for the requester, a `PartnerCandidate`/`PartnerFitReport`
   pair for entity 2 with `trust_score=0.8`, `fit_score=0.8`, and `HelpNeed("combat_support_needed",
   0.8, "Risky target")`). Copy that fixture, but construct the requester entity with
   `entity.identity.cooldowns["cooperation_offer_retry"]` set ahead of `state.tick` — since
   `V2EntityBuilder.identity(...)` accepts a `cooldowns: Optional[Dict[str, int]]` keyword-only
   argument (confirmed at `src/core/builder.py:164-180,202` — it is a kwarg of the `.identity(...)`
   chain method, not a standalone `.cooldowns(...)` method), use `V2EntityBuilder(1).kind("HERO").location(0.0,
   0.0).identity(cooldowns={"cooperation_offer_retry": 6}).build()` with `state =
   AuthoritativeState(..., tick=1, seed=123)` (i.e. cooldown ready_tick 6 > current tick 1). Assert
   `decision.selected_posture in (CooperationPosture.SOLO, CooperationPosture.DEFER_NO_PARTNER)`
   — never `REQUEST_HELP`/`HIRE_SUPPORT` — matching the existing fallback branches
   (`services.py:114-133`), not a new bespoke posture.
2. `test_cooperation_offer_retry_allowed_after_cooldown_expires` — same file, same fixture, but
   `.identity(cooldowns={"cooperation_offer_retry": 1})` with `state.tick=1` (i.e. `state.tick <
   ready_tick` is `False`, cooldown already elapsed). Assert `decision.selected_posture ==
   CooperationPosture.REQUEST_HELP` and `decision.selected_partner_id == 2`, identical to the
   existing unmodified test's assertions — confirms the comparison direction (`<`, not `<=` or
   inverted).
3. `test_reap_expired_recruitment_offer_sets_retry_cooldown` — added to
   `tests/unit/social/test_contract_lifecycle_phase7.py`. **No existing test in this repo directly
   exercises `ContractService.reap_expired_offers()`** — confirmed via
   `grep -rln "reap_expired_offers" tests/` returning only an unrelated working-log fixture JSON,
   not a real test file. The nearest pattern to adapt from is
   `test_offer_expiration_logic()` (`test_contract_lifecycle_phase7.py:56-105`, read in full),
   which exercises the *sibling* `SocialContractSystem.check_expirations()` path with the same
   `create_mock_entity()` helper (`test_contract_lifecycle_phase7.py:10-20`) and
   `ContractService.create_recruitment_contract("c_expired", source_id=99, target_id=1, tick=100)`
   (confirmed `expiry_tick == tick+10`, i.e. `110`). For this new test: build an entity via
   `create_mock_entity(1)`, attach a `RECRUITMENT` contract created the same way with
   `expiry_tick <= current_tick`, place it into `entity.strategic.contracts` via `dataclasses.replace`
   exactly as `test_offer_expiration_logic` does (`test_contract_lifecycle_phase7.py:86-94`), then
   call `ContractService.reap_expired_offers(state, StateUpdate())` (import `StateUpdate` from
   `src.core.updates`, confirmed at `src/core/updates.py:888`) with
   `AuthoritativeState(entities={1: entity}, tick=<expiry_tick+1>, seed=42)`. Assert the returned
   `StateUpdate.entity_updates[1].identity.cooldown_updates["cooperation_offer_retry"] ==
   current_tick + COOPERATION_OFFER_COOLDOWN_TICKS` **and** that the existing
   `strategic.contracts_remove` still contains the reaped contract id (do not regress the existing
   removal behavior).
4. `test_reap_expired_loan_offer_does_not_set_cooperation_cooldown` — same file, anti-drift guard.
   Identical setup but use `ContractService.create_loan_contract(...)`
   (confirmed at `src/systems/social_systems/contracts.py:85-110`, `kind=ContractKind.LOAN`)
   instead of a recruitment contract. Assert the returned `EntityUpdate.identity` for that entity
   is `None` (or has an empty `cooldown_updates`) — i.e. no `"cooperation_offer_retry"` key is
   ever written for a reaped `LOAN` offer — while `strategic.contracts_remove` still correctly
   contains the reaped `LOAN` contract id (removal behavior for non-RECRUITMENT kinds must be
   unaffected).

**Do NOT touch:** any existing test function in either file; `SocialAppraisalSystem`-related
tests (`test_appraisal_betrayal_rejection`, `test_appraisal_risk_vs_hp`,
`test_contract_lifecycle_phase7.py:22-54`) — unrelated to this fix, do not modify.

**Verify:** running these 4 new tests plus the full existing files
(`pytest tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py
tests/unit/social/test_contract_lifecycle_phase7.py -v`) — all pass.

---

### Step 4 — Integration test: no immediate re-offer on the tick after expiry

**Files:** `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`

**Change:** Add `test_cooperation_phase_no_immediate_reoffer_after_expiry_tick`, following
whichever established fixture pattern this file already uses to drive `CooperationPhase.execute()`
across two consecutive ticks (confirm the exact harness — direct pipeline call vs.
`AuthoritativeApplyPipeline` — by reading this file's existing tests before writing the new one,
since test_plan.md explicitly leaves this open pending implementation-time confirmation). Drive:
tick T — an entity has a `RECRUITMENT` offer with `expiry_tick <= T` reaped (via
`ContractService.reap_expired_offers()`, Step 1's new cooldown-set logic fires); tick T+1 —
re-run `CooperationPhase.execute()` (which internally calls `CooperationDecisionService.select()`,
Step 2's new gate) for the same entity with the same eligible partner still available in
range/candidate pool. Assert no new `RECRUITMENT` contract appears in that entity's
`strategic.contracts_add_or_update` for tick T+1.

**Do NOT touch:** any other test in this file exercising flag-on/flag-off or inactive-entity
paths — this is purely an additive new test.

**Verify:** `test_cooperation_phase_no_immediate_reoffer_after_expiry_tick` passes; existing file
tests remain green.

---

### Step 5 — Full scoped regression pass

**Files:** none changed — verification only.

**Change:** Run every command listed in test_plan.md's "Scoped Pytest Commands" section:
```
pytest tests/unit/domains/cooperation/ tests/integration/domains/cooperation/ tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py -v
pytest tests/unit/social/ tests/unit/strategic/test_strategic_social_contracts.py -v
pytest tests/unit/progression/test_rpg_advancement.py tests/integration/pipeline/test_combat_legality_matrix.py tests/unit/observability/test_event_extractor_identity.py -v
pytest tests/unit/observability/test_event_extractor_social_faction.py tests/unit/observability/test_event_shapers_social.py -v
pytest tests/perf/test_phase7_social_cooperation_budget.py -v
```
All must pass with zero regressions before proceeding to Step 6. The skill-cooldown regression
surface (`test_rpg_advancement.py`, `test_combat_legality_matrix.py`,
`test_event_extractor_identity.py`) and the `contract_expired_offer` observability tests
(`test_event_extractor_social_faction.py`, `test_event_shapers_social.py`) are the concrete
guards for the two "other writer" risks named in Step 1 — key-collision on `identity.cooldowns`
and unintended change to contract-expiry event semantics, respectively.

**Do NOT touch:** do not modify any test in this regression surface to make it pass — a failure
here means Step 1 or Step 2's change has a real regression that must be fixed in those steps, not
routed around.

**Verify:** all listed pytest commands exit 0.

---

### Step 6 — Post-fix corpus trial (depends on Steps 1–5 being merged into the working tree)

**Files:** none changed — produces evidence for Step 7.

**Change:** Run the real corpus trial against the fixed code:
```
python3 tools/evaluate_simq.py --scenario highland_traverse_seed42_200t
```
Read the fresh `data/calibration/highland_traverse_seed42_200t/quality_report.json` output (not
`quality_scores.jsonl`, which is append-only and was already found to double-count per the filing
ticket's own investigation). Confirm `contract_expired_offer` event density for this run_key has
measurably decreased relative to the pre-fix baseline (the 20-23-consecutive-tick streaks cited in
the ticket's Request Summary). If `COOPERATION_OFFER_COOLDOWN_TICKS = 15` (Step 1) is insufficient
— i.e. a rapid-retry streak is still visible, merely shorter — increase the constant in
`src/systems/social_systems/contracts.py` and re-run this trial. Do not proceed to Step 7 until a
trial run shows the streak genuinely broken.

**Do NOT touch:** `tests/simulation_quality/fixtures/grade_anchors.json` in this step — that is
Step 7 only, and only after this step's trial output is in hand. Do not hand-compute or guess
what the new score would be.

**Verify:** the fresh `quality_report.json`'s `contract_expired_offer` density for
`highland_traverse_seed42_200t` is visibly reduced from the pre-fix baseline; this step's own
output is the evidence Step 7 consumes.

**Dependency:** requires Steps 1 and 2 (the actual fix) to be implemented and present in the
working tree first. Cannot be run against unmodified code — would only reproduce the known-bad
baseline.

---

### Step 7 — Update the `highland_traverse_seed42_200t` SOCIAL anchor only (depends on Step 6)

**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`

**Change:** Update only the `"highland_traverse_seed42_200t"` top-level key's `"SOCIAL"` block
(confirmed current value at `tests/simulation_quality/fixtures/grade_anchors.json:1440-1466`:
`"SOCIAL": {"grade": "S", "score": 6.875}` sits among nine other pillar blocks —
`COGNITION`, `AGENCY`, `COMBAT`, `FACTION`, `ECONOMY`, `PROGRESSION`, `INFORMATION`, `WORLD`,
`NARRATIVE` — none of which this ticket touches) to the fresh `grade`/`score` values read directly
from Step 6's `data/calibration/highland_traverse_seed42_200t/quality_report.json` output. Do not
touch any other pillar block within this run_key's entry, and do not touch any other run_key's
entry anywhere else in the file.

**Do NOT touch:** any other pillar (`COGNITION`, `AGENCY`, `COMBAT`, `FACTION`, `ECONOMY`,
`PROGRESSION`, `INFORMATION`, `WORLD`, `NARRATIVE`) within `highland_traverse_seed42_200t`'s own
entry; any other run_key's entry anywhere in `grade_anchors.json`, in particular
`urban_political_selfmodel*_probe` entries (owned by
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`, explicitly deferred there) and
`urban_political_seed42_200t` / `lifecycle_full_coverage_world_seed42_200t` (explicitly confirmed
by the filing ticket's investigation to remain within the 20% score-tolerance band, not touched by
any anchor update).

**Verify:**
```
pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[highland_traverse_seed42_200t]" -v -m "not slow"
```
passes. Never run `pytest tests/simulation_quality/` unscoped (would re-run all 61
`FAST_ANCHOR_KEYS`, most already-known-failing/out-of-scope per the filing ticket).

---

## Scope Guards

- No changes to `ContractKind.LOAN` (or any non-`RECRUITMENT` kind) offer/retry cadence — the
  cooldown-set write in Step 1 must stay conditioned on `contract.kind == ContractKind.RECRUITMENT`.
- No changes to `CooperationIntentBridge.map_decision()` (`src/domains/cooperation/services.py:136-196`)
  or `src/domains/cooperation/phase.py` — per investigation.md's Recommendation §4, the gate stays
  entirely inside `select()`.
- No changes to any other run_key's entry in `tests/simulation_quality/fixtures/grade_anchors.json`
  — only `highland_traverse_seed42_200t`'s `SOCIAL` block, and only after a real post-fix corpus
  trial (Step 6 before Step 7, never reordered or skipped).
- No changes to `PartnerCandidateProvider`/`PartnerFitEvaluator` scoring or weighting logic
  (`src/domains/cooperation/providers.py`, `src/domains/cooperation/evaluators.py`) — this fix is
  strictly additive (a new gate before offer creation), never a rebalancing of trust/fit/severity
  weights.
- No changes to `contract_expired_offer` event emission logic in
  `src/observability/event_extractor.py:1000-1035` or `src/observability/event_shapers.py:1400-1630`
  — both are read-only, derived from contract state diffs; this fix changes offer-creation
  *frequency*, never contract-expiry event *semantics*.
- No changes to `SocialContractSystem.check_expirations()` (`src/systems/social_systems/contracts.py:11-77`)
  — the separate status-transition expiry path (SOC-240), untouched by this fix.
- No fix to `IdentityComponent.to_canonical_dict()`'s pre-existing omission of `cooldowns` from the
  canonical hash (`src/core/state.py:494-511`) — this is a pre-existing gap inherited, not
  introduced, by reusing `identity.cooldowns`; if it's judged worth fixing, that's a separate
  ticket, not part of this one.
- No changes to `docs/mechanics/04_strategic_cognition.md`, `docs/engine/authoritative_pipeline.md`,
  or `docs/parity_ledger/social_narrative.yaml` as part of the Implement phase — those are the
  Document-Update phase's responsibility, sequenced after Implement per the standard-tier pipeline,
  not this plan's steps.

## Dependency Map

- Steps 1 and 2 are independent of each other (different files, different functions) and can be
  implemented and verified in either order, but both must land before Step 3's tests can pass
  (Step 3's tests exercise both the set point and the check point).
- Step 3 depends on Steps 1 and 2 (tests exercise the code those steps add).
- Step 4 depends on Steps 1, 2, and 3 (integration test exercises the full tick-to-tick path;
  should be written and run after the unit-level set/check points are individually verified).
- Step 5 depends on Steps 1-4 all being complete (full regression pass over the finished change).
- Step 6 depends on Steps 1-5 (the code fix, including all new tests, must be merged into the
  working tree — the trial is meaningless against unmodified code).
- Step 7 depends on Step 6's fresh trial output (never computed independently, never run out of
  order relative to Step 6).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "Cooperation offers have a real cooldown/backoff after expiry" | Steps 1, 2 | `test_cooperation_offer_retry_blocked_within_cooldown_window`, `test_cooperation_offer_retry_allowed_after_cooldown_expires`, `test_reap_expired_recruitment_offer_sets_retry_cooldown` |
| "`test_grade_within_anchor_band[highland_traverse_seed42_200t]` passes after the anchor is updated to reflect the fixed behavior" | Steps 6, 7 | `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band[highland_traverse_seed42_200t]` |
| "A regression test confirms an entity does not re-propose a cooperation offer on the tick immediately following a prior expiry" | Step 4 | `test_cooperation_phase_no_immediate_reoffer_after_expiry_tick` |
| (Scope) "Confirm the fix actually reduces `contract_expired_offer` event density ... re-run the real corpus trial, don't assume" | Step 6 | manual verification of `data/calibration/highland_traverse_seed42_200t/quality_report.json`, not a pytest assertion |
| (Out of Scope guard) "Any other SOCIAL/cooperation scoring or weighting change ... out of scope" | Step 1's `ContractKind.RECRUITMENT` conditioning | `test_reap_expired_loan_offer_does_not_set_cooperation_cooldown` |
| (Out of Scope guard) "Re-litigating any other run_key's anchor value ... only `highland_traverse_seed42_200t` is in scope" | Step 7's scoped edit | manual diff review of `grade_anchors.json` before commit (confirm only one run_key's `SOCIAL` block changed) |

## Anti-Drift Notes

- **`ContractService` vs. `SocialContractSystem` naming**: investigation.md calls the set point
  `SocialContractSystem.reap_expired_offers()` throughout; the actual owning class, confirmed by
  direct read, is `ContractService` (`src/systems/social_systems/contracts.py:78-331`).
  `SocialContractSystem` (same file, line 11) is the distinct class holding
  `check_expirations()` — do not confuse the two or edit the wrong class.
- **Per-entity blanket cooldown is the baseline design, not per-(entity, partner) pair** — matches
  the ticket's own "(or any) target" wording. If Step 6's trial shows the blanket cooldown
  over-suppresses legitimate cooperation (SOCIAL score moves the wrong direction because a
  different, viable partner also gets blocked for 15 ticks), per-`{entity_id}_{partner_id}` keys
  are the documented fallback per investigation.md's Risks section — but do not switch designs
  preemptively; only after real trial evidence says the blanket design failed.
- **`COOPERATION_OFFER_COOLDOWN_TICKS = 15` is a starting point, not a fixed requirement** — Step 6
  explicitly allows increasing it and re-running the trial if the streak is only shortened, not
  broken. Never hand-tune `grade_anchors.json` to mask a still-present rapid-retry pattern instead
  of increasing this constant.
- **The reaped contract lives on the proposer's own `entity.strategic.contracts`, not the
  target's** — confirmed via `CooperationIntentBridge.map_decision()` returning
  `EntityUpdate(entity_id=entity.id, ...)` with `source_id=entity.id` on the created contract
  (`services.py:168-176`). `reap_expired_offers()`'s existing per-entity loop
  (`contracts.py:315`) already iterates the correct `e_id` (the proposer) for the cooldown write —
  no extra source/target disambiguation logic is needed in Step 1.
- **No existing test in the repo directly exercises `ContractService.reap_expired_offers()`** —
  confirmed by `grep -rln "reap_expired_offers" tests/` returning only an unrelated fixture JSON.
  Step 3's tests 3 and 4 are genuinely new coverage for this function, adapted from the sibling
  `test_offer_expiration_logic()` pattern (which covers `check_expirations()`, not
  `reap_expired_offers()`) — do not assume a closer precedent exists that wasn't found.
- **Determinism/replay gap is pre-existing, not introduced here**: `identity.cooldowns` (all keys,
  including the new `"cooperation_offer_retry"`) is absent from
  `IdentityComponent.to_canonical_dict()` (`src/core/state.py:494-511`), confirmed by direct read —
  the same gap already applies to skill cooldowns today. Do not silently fix this as part of this
  ticket.

## Deviations

None. Steps 1-5 were implemented exactly as specified in this plan:

- Step 1: `COOPERATION_OFFER_COOLDOWN_TICKS = 15` constant, `IdentityUpdate` import, and the
  RECRUITMENT-conditioned cooldown write in `ContractService.reap_expired_offers()`, merged
  alongside the existing `contracts_remove` write in the same `replace(ent_upd, ...)` call.
- Step 2: `on_offer_cooldown` check added after the `if not help_needs:` early return;
  `if best_report:` changed to `if best_report and not on_offer_cooldown:`; no other line changed.
- Step 3: all 4 new unit tests added exactly as specified, adjacent to the named sibling tests.
- Step 4: the integration test builds tick T+1's entity state via `dataclasses.replace` applying
  the reap update's own returned effects (contract removal, cooldown set) directly, rather than
  invoking a full `AuthoritativeApplyPipeline`/`ApplyPath` — the plan explicitly left the exact
  harness open pending implementation-time confirmation, and this repo's existing
  `test_phase7_cooperation_phase.py`/`test_phase7_social_cooperation_scenarios.py` tests all
  construct entity state directly via `V2EntityBuilder` + `dataclasses.replace`/`object.__setattr__`
  rather than driving a full kernel/apply pipeline, so this follows the file's own established
  pattern rather than introducing a new one.
- Step 5: all 5 regression pytest commands run and passed with zero regressions (373 tests total).
  Later re-scoped by the orchestrator to include the whole `tests/unit/domains/` directory (not
  just the `cooperation/` subdirectory) to satisfy the structural test-scope-coverage backstop
  (`tools/gate_checks/test_scope_coverage_static.py`), re-run as 1091 passed, 0 failed.
- Step 6 (real post-fix corpus trial, run once Steps 1-5 were merged into the working tree, per the
  Dependency Map): `python3 tools/evaluate_simq.py --scenario highland_traverse_seed42_200t`.
  SOCIAL `normalized_score` improved from 5.045 (pre-fix) to 5.636363636363637 (post-fix, grade
  `S`). Confirmed via `simulation_events.jsonl` trace that no entity creates a new `RECRUITMENT`
  offer on any tick following an expiry once its cooldown is active — the observed
  same-window `contract_expired_offer` runs are the pre-cooldown backlog draining on its own
  pre-set schedule, not new re-proposals. `COOPERATION_OFFER_COOLDOWN_TICKS = 15` was sufficient;
  no increase/re-run needed.
- Step 7 (anchor update, depends on Step 6): `tests/simulation_quality/fixtures/grade_anchors.json`'s
  `highland_traverse_seed42_200t` entry's `SOCIAL` block updated to `score: 5.636363636363637`
  (grade unchanged, `S`) — the exact value read from Step 6's fresh
  `data/calibration/highland_traverse_seed42_200t/quality_report.json`, no other pillar or run_key
  touched. `test_grade_within_anchor_band[highland_traverse_seed42_200t]` re-run and confirmed
  PASSING.

No deviations from the plan's design. One finding disclosed but explicitly not fixed, out of this
ticket's scope: an entity can still create multiple simultaneous un-expired offers to a target
before the first one ever expires (offer creation is not itself gated on an already-pending offer —
only post-expiry retry is), which is why the post-fix trial still shows an initial multi-tick burst
before the cooldown activates. This is a separate, pre-existing characteristic of
`CooperationDecisionService.select()`/`CooperationIntentBridge.map_decision()` (creating a new offer
every tick a decision persists), not something this ticket's Scope asked to change — a candidate
follow-up ticket if desired.
