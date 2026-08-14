---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
artifact_type: plan
tags: [social, cognition]
---

# Implementation Plan — TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Summary

Add `GoalKind.SOCIAL_CONTRACT` to `src/core/strategic.py`, a new `SocialContractGoalScorer` in a
new `src/ai/goals/social_contract_scorer.py` module that scans an entity's `ACTIVE` `RECRUITMENT`/
`LOAN` contracts, computes a raw score per contract from trust/urgency/economic-value/risk signals,
reduces multiple simultaneous candidates to one winner, and carries the raw score + a pre-resolved
`(ProjectKind, ObjectiveKind, obj_id_prefix)` mapping in `GoalScore.metadata`. Register it in
`src/ai/goals/__init__.py`. Add a new `elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:`
materialization branch in `StrategicIntelligenceSystem.evaluate_strategic_intent()`
(`src/systems/strategic_systems/intelligence.py`), mirroring the existing `ADVENTURE_ROUTE` branch's
shape exactly — never `best_candidate.utility` in `ProjectState.score`. Simplify
`ContractService.accept_contract()` (`src/systems/social_systems/contracts.py`) down to *only* the
status transition (`SocialContractSystem.transition_contract()`), removing its inline
`ProjectState`/`ObjectiveState` construction and `current_project_id_set` write entirely — not just
the `current_project_id_set` line — because leaving the rest of that construction in place while
routing materialization through the new arbiter path would create a second, orphaned `ProjectState`
per accepted contract competing for `max_active_projects` bandwidth against the arbiter-materialized
one (see Design Decision #7). The kind-conditional mapping logic
`accept_contract()` used to inline (`RECRUITMENT → ProjectKind.COMBAT`, `LOAN → ProjectKind.SOCIAL`,
both `ObjectiveKind.REACH_LOCATION`) is extracted into a new `ContractService.get_project_mapping()`
static helper, reused by the new scorer — satisfying the ticket's "delegating to `ContractService`'s
existing unchanged internal contract-acceptance logic" wording literally, while eliminating the
duplicate-project hazard.

This plan resolves all 6 open questions the investigation flagged as blocking, plus 5 additional
findings this plan's own fact-verification pass surfaced (not present in investigation.md — see
Design Decisions #7–#11 below), the most significant being: (a) a genuine duplicate-project/bandwidth
hazard if `accept_contract()` kept building its own `ProjectState` alongside the new arbiter path, and
(b) a **pre-existing, not newly introduced** "wins but stalls" defect in the *original*
`accept_contract()`'s own `ObjectiveState` construction (`target=str(source_id)` is never resolvable
by `TacticalDecisionSystem._resolve_target_position()`, which only looks up `state.resource_nodes`/
`state.buildings` for an int-castable target, never `state.entities`) — this plan fixes it as part of
the migration, mirroring the same class of fix the architecture-reviewer required for
`TCK-20260811-ADVENTURE-GOAL-SCORER`.

## Design Decisions (resolves investigation.md's 6 flagged open questions)

**#1 — Liveness scope (investigation.md Risk #4).** Chosen: this ticket does **not** wire
`accept_contract()` into a production call site — confirmed no such wiring ticket exists in this
epic's `SEQUENCE.md` (per investigation.md), and the ticket's own AC text is phrased entirely in
terms of `evaluate_project_switch()`'s comparison, not "in a live tick." **However — a materially
important refinement investigation.md did not surface**: `SocialContractGoalScorer.score()` does
**not** read through `accept_contract()` at all. It scans `entity.strategic.contracts.values()`
directly for `status == ContractStatus.ACTIVE`, regardless of which code path put the contract into
that state. `src/engine/domain/core_actions.py:96-105` (`CoreActions.execute_recruit`, read directly)
is a **real, live production path** that constructs a `ContractState` with `status=ContractStatus.ACTIVE`
directly (never calling `accept_contract()` or `SocialContractSystem.transition_contract()`) whenever
a recruitment offer is accepted via `appraise_contract()`. This means: **the new scorer itself is
reachable in live production once registered in `__init__.py`, even though `accept_contract()` remains
uncalled.** Previously, `execute_recruit()`-originated contracts spawned *no* strategic project at all
(a known, separate, out-of-scope gap per investigation.md). After this ticket, they become eligible to
compete for and potentially win tier-5 arbitration — a genuine, disclosed behavior change for a real
production path, not merely "landed but inert" the way `AdventureGoalScorer` was before its own
pipeline-wiring ticket. This must be stated explicitly in Docs Requiring Update and must not be
described as "no live production impact" anywhere in Implementation Notes — that framing would be
false for this ticket even though it is true for `accept_contract()` specifically.

**#2 — `_score_scale_max()` scale-sharing (investigation.md Risk #1).** Chosen: **(a) calibrate the
new raw-score formula to the existing `2.9` ceiling**, reusing `_ADVENTURE_ROUTE_SCORE_MAX` unchanged
(imported lazily, exactly as `AdventureGoalScorer` already does) — **not** (b) extending
`_score_scale_max()`/`ProjectState` with a new provenance-classification signal. Rationale: `(b)` would
require adding a durable-state field to `ProjectState` (`src/core/strategic.py:247-258`, confirmed
read directly — no such field exists today) purely to disambiguate "this `ProjectKind.SOCIAL` came
from a contract" from "this `ProjectKind.SOCIAL` came from adventure's `FORM_PARTY`," which is a
durable-state-model change the ticket's AC list never asks for, touches shared arbitration code both
`AdventureGoalScorer` and this scorer would then depend on, and directly risks the exact regression
the investigation's own Anti-Drift Hazards forbid ("Do not modify `_score_scale_max()`... without an
explicit Plan decision recorded... changing the shared constant/function affects `ADVENTURE_ROUTE`'s
own already-verified calibration too"). Option (a) is a pure-arithmetic calibration choice inside the
new scorer's own module, touches zero shared code, and keeps
`tests/unit/strategic/test_score_normalization.py`'s 5 existing tests provably unaffected (they never
import or reference anything this ticket edits).

**#3 — Raw-score formula (investigation.md Risk #2).** Chosen:
```
raw_score = clamp(trust*1.0 + urgency*1.0 + value*0.9 - risk_weight*0.3, 0.0, 2.9)
```
- `trust` (0.0–1.0): `(bond.sentiment + 1.0) / 2.0` if `entity.social.bonds.get(contract.source_id)`
  exists, else `entity.social.trust_history.get(contract.source_id, 0.5)` — the same two input
  fields `SocialAppraisalSystem.appraise_contract()` reads first
  (`src/systems/social_systems/appraisal.py:32,44`, read directly), deliberately **not** calling
  `appraise_contract()` itself (that function governs the OFFERED→ACCEPTED decision, a different,
  upstream purpose; this scorer runs on an already-`ACTIVE` contract's ongoing competitive standing).
- `urgency` (0.0–1.0): `1.0 - min(1.0, ticks_remaining / duration)` where
  `ticks_remaining = max(0, contract.expiry_tick - state.tick)`, using `contract.terms.get("duration", 0)`
  and `contract.expiry_tick` (confirmed fields, `src/core/strategic.py:191-195`, `contracts.py:35-38`
  sets `expiry_tick = tick + duration` on transition to `ACTIVE`); defaults to `0.5` when
  `expiry_tick <= 0` or `duration <= 0` (e.g. `execute_recruit()`-originated contracts, which never set
  either — see Design Decision #9).
- `value` (0.0–0.9 after weighting): kind-conditional economic magnitude, mirroring
  `_appraise_recruitment`'s own `expected_pay = 10 * entity.identity.evolution_level` baseline
  (`appraisal.py:97`, read directly) for `RECRUITMENT`
  (`min(1.0, terms.get("daily_pay", terms.get("payout", 0)) / max(1, 10 * entity.identity.evolution_level))`)
  and an analogous `50 * entity.identity.evolution_level` baseline for `LOAN`
  (`min(1.0, terms.get("amount", 0) / max(1, 50 * entity.identity.evolution_level))`).
- `risk_weight` (0.0–1.0): `1.0` if `risk_level == "HIGH"`, `0.5` if `"NORMAL"`, `0.1` otherwise —
  the identical ternary `_appraise_recruitment` already uses (`appraisal.py:100`, read directly,
  including its pre-existing quirk of folding `LOW`/`EXTREME` into the same `0.1` fallback — not this
  ticket's bug to fix); `0.0` for `LOAN` (no `risk_level` key exists in `LOAN` terms,
  `ContractService.create_loan_contract`, `contracts.py:94-104`, confirmed read directly).
- **Explicitly flagged, per the ticket's own Assumptions bullet ("Needs empirical validation of
  normalization constants, not assumable by formula alone")**: the weights (`1.0`/`1.0`/`0.9`/`0.3`)
  and baselines (`10`/`50`) are a reasoned initial calibration chosen so the formula's own maximum
  (`trust=1.0, urgency=1.0, value=1.0, risk=0.0` → `1.0+1.0+0.9-0.0 = 2.9`) exactly matches
  `_ADVENTURE_ROUTE_SCORE_MAX`, **not** a runtime-validated calibration. This is disclosed, not
  silently asserted as final — see Anti-Drift Notes.

**#4 — Multi-contract reduction (investigation.md Risk #3).** Chosen: among all `ACTIVE` contracts
whose `kind` has a `ContractService.get_project_mapping()` result (i.e. `RECRUITMENT`/`LOAN` only),
the **highest `raw_score` wins**; ties broken by **contract `id` ascending** (string comparison) for
determinism — `entity.strategic.contracts` is a `Dict[str, ContractState]`
(`src/core/strategic.py:346`, confirmed read directly) whose iteration order should not be relied on
for a determinism-sensitive tie-break, mirroring this codebase's own existing tie-break discipline
(`GoalRegistry.get_all_scores()`'s sorted-key iteration, `base.py:48-50`; `modified_scores.sort(key=
lambda x: (-x.utility, x.kind))`, `intelligence.py:1408`). No prior-art reduction exists elsewhere in
this codebase for this exact problem (confirmed by investigation.md and re-confirmed here); this is
new logic, not a delegation.

**#5 — Tie-break value (investigation.md Risk #5).** Chosen: `GoalKind.SOCIAL_CONTRACT =
"social_contract"` — **not** `"z_"`-prefixed. Confirmed (`src/core/strategic.py:121-133`, read
directly) the 11 current `GoalKind` values are the 10 originals (`harvesting` … `guild`, all starting
`c`–`t`) plus `ADVENTURE_ROUTE = "z_adventure_route"`. `"social_contract"` starts with `'s'`, so it:
(a) sorts among the original 10 the same ordinary way any new `GoalKind` would (no special collision
risk — none of the 10 originals' values collide with it); (b) is guaranteed to sort **before**
`"z_adventure_route"` (`'s' < 'z'`), so on an exact-utility tie, `SOCIAL_CONTRACT` wins the tie-break
over `ADVENTURE_ROUTE`. This is a deliberate semantic choice, not an accident: an accepted social
obligation (a promise already made to another entity) is treated as ranking above routine, non-urgent
adventuring (the design doc's own framing, `docs/architecture/2026-08-11-adventure-as-cognition-
strategy-subcomponent-design.md`) when the two are otherwise exactly tied. Confirmed no collision with
any `ProjectKind` value (`crafting, quest, exploration, combat, social, recovery, preparation,
training, harvesting, information, information_seeking, travel` — `src/core/strategic.py:139-152`,
read directly): `"social_contract"` is distinct from `"social"`, so the pre-existing
`existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)`
resume/dedup lookup (`intelligence.py:1429`) never accidentally matches for `SOCIAL_CONTRACT` winners
(same non-collision property `ADVENTURE_ROUTE` already relies on).

**#6 — `SOC-208` opportunistic closure.** Chosen: **yes, close it** as part of this ticket's Docs step.
`SOC-208`'s text, "Accepted contract creates explicit obligation/contract state" (`social_narrative.yaml:2176`,
read directly, `status: verified`, `test_path: null` today), is not force-fit — it is *exactly* what the
rewritten `test_accepted_contract_spawns_project_and_objective` (Step 9) now verifies end-to-end
(status transition + scorer output + real materialized `ProjectState`/`ObjectiveState`), more rigorously
than the pre-migration test did. Add `test_path` pointing at that rewritten test.

## New Findings (beyond investigation.md's 6 flagged questions, surfaced by this plan's own fact-verification)

**#7 — Duplicate-project hazard if `accept_contract()` merely dropped `current_project_id_set`.**
The ticket's Scope bullet 3 literally says only "no longer sets `current_project_id_set` directly." A
naive reading would leave `accept_contract()`'s `projects_add.append(proj)` /
`projects_add_or_update=[...]` write intact (lines 172-186 pre-edit, `contracts.py`, confirmed read
directly) while *also* routing materialization through the new arbiter path — producing **two**
distinct `ProjectState` entries for the same contract: one under `accept_contract()`'s original stable
id `proj_contract_{contract.id}` (committed immediately, unconditionally, never referenced by
`current_project_id`, effectively orphaned/dead weight), and one under the arbiter-materialized,
tick-suffixed id (committed only if/when it wins). The orphaned entry would sit in
`entity.strategic.projects` forever, consuming `max_active_projects` bandwidth
(`at_capacity = len(strat.projects) >= strat.profile.max_active_projects`, `intelligence.py:1488`,
read directly) without ever being useful — potentially starving the entity of any future project slot.
Resolved by Step 2: `accept_contract()` performs *only* the status transition; project/objective
construction is removed from it entirely, not merely its `current_project_id_set` line. See
`test_plan.md`'s own AC4 test note ("this test would fail if Implement accidentally changes either
mapping while extracting it into a reusable form") — this plan's reading is that the extraction is
into `ContractService.get_project_mapping()`, consumed only by the new scorer, not retained by
`accept_contract()`.

**#8 — Pre-existing "wins but stalls" defect in `accept_contract()`'s original `ObjectiveState`,
inherited (not introduced) by this migration.** `TacticalDecisionSystem._resolve_target_position()`
(`src/engine/tactical.py:702-753`, read directly) resolves an `int`-castable `obj.target` **only**
against `state.resource_nodes.get(candidate_id)` or `state.buildings.get(candidate_id)` — **never**
`state.entities`. `accept_contract()`'s original `ObjectiveState` set
`target=str(contract.source_id)` (an *entity* id, e.g. `"2"`) with no `target_position` — `int("2")`
succeeds, but `state.resource_nodes.get(2)`/`state.buildings.get(2)` will not resolve to the
counterparty entity except by numeric-id coincidence, and no `target_position` fallback exists to
recover if not. This means the **original**, pre-this-ticket `accept_contract()` code already produced
an unresolvable-by-`_resolve_target_position()` objective for every accepted contract, unconditionally
— a latent defect this ticket's migration is well-positioned to fix (mirroring the reviewer-required
fix in `TCK-20260811-ADVENTURE-GOAL-SCORER`), not introduce. Step 3 fixes it: `SocialContractGoalScorer
.score()` resolves `target_pos = state.entities.get(contract.source_id).navigation.position` (falling
back to `None` only if the counterparty entity is genuinely absent from `state.entities`) and threads
it into `GoalScore.target_pos`, which Step 5's materialization branch writes into
`ObjectiveState.target_position` — giving `_resolve_target_position()`'s `target_position` fallback
(`tactical.py:751-752`) real data to resolve, exactly as `TownScorer`/`RecoverScorer` already rely on
for their own non-int-resolvable targets.

**#9 — `terms` shape mismatch between `create_recruitment_contract()` and `execute_recruit()`.**
`ContractService.create_recruitment_contract()` sets `terms={"daily_pay":..., "duration":...,
"risk_level":...}` (`contracts.py:125-129`), but `CoreActions.execute_recruit()`
(`src/engine/domain/core_actions.py:104`, read directly) sets `terms={"payout": payout}` only — no
`daily_pay`, no `duration`, no `risk_level`. The raw-score formula (#3) defensively reads
`terms.get("daily_pay", terms.get("payout", 0))` so `execute_recruit()`-originated contracts still get
a non-zero `value` component instead of silently defaulting to `0.0` forever; `urgency` correctly
defaults to `0.5` for these (no `duration`/`expiry_tick`, confirmed `execute_recruit()` never sets
`expiry_tick`, defaults to `-1` per `ContractState`'s own dataclass default, `strategic.py:192`); `risk_weight`
defaults to `0.5` (no `risk_level` key — `terms.get("risk_level", RiskLevel.NORMAL)` falls through to
the `"NORMAL"` branch, matching `SocialAppraisalSystem._appraise_recruitment`'s identical
`terms.get("risk_level", "NORMAL")` default at `appraisal.py:93`; the `0.1` fallback only applies when
`risk_level` is present but holds `"LOW"`/`"EXTREME"`, never to a genuinely absent key). This is a
disclosed, accepted degradation (execute_recruit contracts score with weaker signal than
accept_contract-lineage ones) — **not** a schema unification, which is out of scope.

**#10 — Materialized project/objective id convention: tick-suffixed, deliberately diverging from
`accept_contract()`'s original stable id.** `accept_contract()`'s pre-edit id was the stable
`proj_contract_{contract.id}` (no tick suffix) — investigation.md flagged reusing this stable
convention as a "worth considering, not binding" option. This plan rejects it: if the *same* contract
keeps winning arbitration across multiple ticks under a stable id, `evaluate_project_switch()`'s
locked-branch would compare a freshly-recomputed `candidate_project` against the **same-id** `current`
project fetched from `entity.strategic.projects` (`intelligence.py:992`), and a subsequent win would
emit `projects_add_or_update=[replace(current, status=SUSPENDED), candidate_project]` with **both**
list entries sharing one id — the dict-keyed apply makes the `SUSPENDED` write a silent no-op
(last-write-wins), but the *lock itself* gets silently refreshed (`lock_until_tick=current_tick+50`)
every tick the contract's rising urgency lets it re-clear its own prior lock — an unanalyzed,
non-obvious edge case with no test coverage in test_plan.md. This plan instead mirrors
`RouteToProjectMapper.map_to_states()`'s own tick-suffixed convention exactly
(`src/domains/adventure/mapper.py:85-86`, read directly: `f"proj.{family.value}.ent{entity_id}.t{tick}"`)
— `proj_contract_{contract_id}_t{current_tick}` / `{obj_id_prefix}{contract_id}_t{current_tick}` —
so each winning tick produces a genuinely distinct id, avoiding the same-id lock-refresh ambiguity
entirely and staying consistent with the one precedent this codebase already has for this exact
mechanism. `lock_until_tick` itself is still set to `current_tick + 50` (not the generic branch's
`min(current_tick+10, current_tick+50) == current_tick+10`), preserving `accept_contract()`'s original
50-tick lock duration (`contracts.py:180` pre-edit, confirmed read directly) — a deliberate,
contract-specific lock length distinct from adventure's shorter one.

**#11 — Resume/dedup lookup inert for `SOCIAL_CONTRACT` too, inherited, not this ticket's job.** Same
structural non-match as `ADVENTURE_ROUTE` (Design Decision #5's non-collision property) — a suspended
contract-project is never resumed by `intelligence.py:1429`'s lookup, it is re-materialized fresh under
a new tick-suffixed id. This is the same accepted, shared gap investigation.md's Anti-Drift Hazards
explicitly forbid fixing here ("would require the same generalization for both kinds together, out of
scope").

## Steps

### Step 1 — Add `GoalKind.SOCIAL_CONTRACT` enum member

**Files:** `src/core/strategic.py`

**Change:** In the `GoalKind(str, Enum)` class body (confirmed exact current contents, read directly,
`strategic.py:121-136`: 10 original members plus `ADVENTURE_ROUTE = "z_adventure_route"`), add one new
member immediately after `ADVENTURE_ROUTE`'s definition:
```python
    SOCIAL_CONTRACT = "social_contract"  # deliberately NOT "z_"-prefixed (Design Decision #5):
    # sorts before "z_adventure_route" so an accepted social obligation wins an exact-utility tie
    # against routine adventuring; does not collide with any ProjectKind value or existing
    # GoalKind value (verified against strategic.py:121-152 directly).
```

**Do NOT touch:** The 10 original members or `ADVENTURE_ROUTE`'s value (`"z_adventure_route"`,
confirmed unchanged). Do not touch `ProjectKind`, `ContractKind`, `ContractStatus`, `RiskLevel` — read
only, no edits.

**Verify:** `test_goal_kind_social_contract_is_registered_member`,
`test_social_contract_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind` (new,
mirrors `test_adventure_route_kind_value_sorts_after_all_existing_goal_kinds`'s style — see Step 6).

---

### Step 2 — Extract `ContractService.get_project_mapping()`; simplify `accept_contract()`

**Files:** `src/systems/social_systems/contracts.py`

**Change (new helper):** Add a new static method, placed above `accept_contract()`:
```python
    @staticmethod
    def get_project_mapping(contract: ContractState):
        """
        Returns (ProjectKind, ObjectiveKind, objective_id_prefix) for the 2 of 5 ContractKind
        members that spawn a strategic project -- exactly preserving accept_contract()'s
        pre-existing 2-of-5 coverage (RECRUITMENT -> ProjectKind.COMBAT, LOAN -> ProjectKind.SOCIAL,
        both ObjectiveKind.REACH_LOCATION; contracts.py pre-edit lines 155-171, confirmed read
        directly). Returns None for PROTECTION/MERCHANT/POSITION_SWAP -- do not widen this
        coverage (see plan.md Scope Guards).
        """
        from src.core.strategic import ProjectKind, ObjectiveKind
        if contract.kind == ContractKind.RECRUITMENT:
            return ProjectKind.COMBAT, ObjectiveKind.REACH_LOCATION, "obj_recruit_"
        if contract.kind == ContractKind.LOAN:
            return ProjectKind.SOCIAL, ObjectiveKind.REACH_LOCATION, "obj_loan_"
        return None
```

**Change (simplify `accept_contract()`):** Replace the current body (lines 136-190, confirmed exact
read directly above) with:
```python
    @staticmethod
    def accept_contract(
        entity: EntityState,
        contract_id: str,
        tick: int
    ) -> StrategicUpdate:
        """
        Transition an OFFERED/COUNTERED contract to ACTIVE.

        Project/objective spawning is no longer performed here
        (TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER): SocialContractGoalScorer
        (src/ai/goals/social_contract_scorer.py) now scores every entity's ACTIVE
        RECRUITMENT/LOAN contracts each tick as a tier-5 GoalRegistry candidate, and the winning
        candidate is materialized into a real ProjectState/ObjectiveState by
        StrategicIntelligenceSystem.evaluate_strategic_intent()'s
        `elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:` branch, through
        evaluate_project_switch() -- not unconditionally. This function intentionally no longer
        builds any ProjectState/ObjectiveState or sets current_project_id_set: doing so here AND
        via the arbiter would create a second, orphaned project per accepted contract competing
        for max_active_projects bandwidth against the arbiter-materialized one (see plan.md
        Design Decision #7). The kind->(ProjectKind, ObjectiveKind) mapping this method used to
        inline now lives in ContractService.get_project_mapping(), reused by the scorer.
        """
        strat_up, _ = SocialContractSystem.transition_contract(
            entity, contract_id, ContractStatus.ACTIVE, tick
        )
        return strat_up
```

**Do NOT touch:** `SocialContractSystem.transition_contract()`/`_is_valid_transition()`
(`contracts.py:16-62`, unrelated to the bypass, confirmed unchanged); `resolve_contract_outcome()`,
`process_active_contracts()`, `reap_expired_offers()`, `check_expirations()` (all confirmed unrelated
to project-spawning, unaffected); `create_loan_contract()`/`create_recruitment_contract()` (contract
factories, unchanged). Do not touch `src/engine/domain/core_actions.py`'s `execute_recruit()` — its
contracts are now scored (Design Decision #1), but the function itself is not edited.

**Other writers to `entity.strategic.contracts` / `entity.strategic.projects` this step must not
collide with (Fact-Verification Requirement #2):**
- `SocialContractSystem.transition_contract()` — the only writer inside `accept_contract()`'s own call
  chain; unchanged, still the sole source of the `contracts_add_or_update` this step's simplified
  `accept_contract()` still returns.
- `ContractService.resolve_contract_outcome()`/`process_active_contracts()`/`reap_expired_offers()` —
  write `contracts_add_or_update`/`contracts_remove` for FULFILLED/FAILED/BETRAYED/EXPIRED
  transitions, unrelated to and unaffected by this step's edit (this step only touches the
  OFFERED/COUNTERED→ACTIVE path's project-spawning side effect, not the status-machine writes
  themselves).
- `src/domains/cooperation/services.py:170-181` and `src/engine/domain/core_actions.py:96-105`
  (`execute_recruit`) — both create/mutate contracts through paths that never call
  `accept_contract()`; unaffected by this step's edit to `accept_contract()` itself, but their
  resulting `ACTIVE` contracts are now visible to the new scorer (Design Decision #1) — a Step 3
  concern, not a Step 2 one.
- `src/systems/world_systems/events.py:98` (`stabilize_project`) — unconditional-overwrite bypass on
  `current_project_id`/`projects`, structurally independent, explicitly out of scope (ticket's own Out
  of Scope section), untouched by this step.
- `evaluate_project_switch()`'s own two unconditional-adopt branches (`intelligence.py:985-998`) and
  final raw-comparison branch (`intelligence.py:1039-1047`) — the *only* writers that will ever again
  set `current_project_id_set` for a contract-originated project after this step lands, reached solely
  via Step 5's new materialization branch, never via `accept_contract()` itself.

**Verify:** `test_accept_contract_no_longer_sets_current_project_id_directly`,
`test_contract_lifecycle_acceptance` (existing, `tests/unit/social/test_contract_lifecycle.py`, must
keep passing unmodified — asserts only on `contracts_add_or_update[0].status`/`.expiry_tick`, both
still produced identically by the unchanged `transition_contract()` call).

---

### Step 3 — Create `SocialContractGoalScorer` in a new module

**Files:** `src/ai/goals/social_contract_scorer.py` (new file)

**Change:** Create the file with the following structure (exact shape, not paraphrase):
```python
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from src.ai.goals.base import GoalScorer, GoalScore
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import GoalKind, ContractState, ContractStatus


class SocialContractGoalScorer(GoalScorer):
    """
    GoalScorer wrapper around ContractService.get_project_mapping() (src/systems/social_systems/
    contracts.py), registered under GoalKind.SOCIAL_CONTRACT as one candidate among many in tier 5
    of StrategicIntelligenceSystem.evaluate_strategic_intent()
    (src/systems/strategic_systems/intelligence.py). See plan.md
    TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER, Design Decision #1: this scorer reads
    entity.strategic.contracts directly and is therefore reachable in live production via
    src/engine/domain/core_actions.py's execute_recruit() (which constructs ACTIVE-status
    RECRUITMENT contracts directly), even though ContractService.accept_contract() itself has no
    production caller.
    """

    def score(self, entity: EntityState, state: AuthoritativeState) -> GoalScore:
        from src.systems.social_systems.contracts import ContractService

        candidates: List[Tuple[float, ContractState, Tuple[Any, Any, str]]] = []
        for contract in entity.strategic.contracts.values():
            if contract.status != ContractStatus.ACTIVE:
                continue
            mapping = ContractService.get_project_mapping(contract)
            if mapping is None:
                # PROTECTION/MERCHANT/POSITION_SWAP: preserve accept_contract()'s pre-existing
                # 2-of-5 coverage -- do not widen (plan.md Scope Guards).
                continue
            raw_score = SocialContractGoalScorer._raw_score(entity, contract, state.tick)
            candidates.append((raw_score, contract, mapping))

        if not candidates:
            return GoalScore(kind=GoalKind.SOCIAL_CONTRACT, utility=0.0, target_id=None)

        # Reduction (Design Decision #4): highest raw_score wins; ties broken by contract id
        # ascending for determinism (entity.strategic.contracts iteration order is not a
        # determinism-safe tie-break source).
        candidates.sort(key=lambda c: (-c[0], c[1].id))
        raw_score, contract, (proj_kind, obj_kind, obj_id_prefix) = candidates[0]

        # MUST be a lazy (function-local) import: mirrors AdventureGoalScorer's own documented
        # reason (src/ai/goals/adventure_scorer.py) -- intelligence.py:78's top-level
        # `from src.ai.goals import GoalRegistry` creates a transitive module-load-order
        # dependency once this module is registered in src/ai/goals/__init__.py.
        from src.systems.strategic_systems.intelligence import (
            _ADVENTURE_ROUTE_SCORE_MAX,
            _GOAL_UTILITY_SCORE_MAX,
        )

        # Design Decision #8: the counterparty's real position, so the materialized objective is
        # tactically resolvable (TacticalDecisionSystem._resolve_target_position() only resolves
        # int-castable targets against state.resource_nodes/state.buildings, never state.entities
        # -- a stringified entity id alone, as accept_contract()'s ORIGINAL ObjectiveState used,
        # was never resolvable). Falls back to None only if the counterparty is genuinely absent.
        source_entity = state.entities.get(contract.source_id)
        target_pos = source_entity.navigation.position if source_entity else None

        utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX

        return GoalScore(
            kind=GoalKind.SOCIAL_CONTRACT,
            utility=utility,
            target_id=str(contract.source_id),
            target_pos=target_pos,
            metadata={
                "contract_id": contract.id,
                "source_id": contract.source_id,
                "raw_score": raw_score,
                "proj_kind": proj_kind,
                "obj_kind": obj_kind,
                "obj_id_prefix": obj_id_prefix,
            },
        )

    @staticmethod
    def _raw_score(entity: EntityState, contract: ContractState, current_tick: int) -> float:
        """
        raw_score = clamp(trust*1.0 + urgency*1.0 + value*0.9 - risk_weight*0.3, 0.0, 2.9)
        Calibrated to the SAME 0-2.9 ceiling _ADVENTURE_ROUTE_SCORE_MAX already declares
        (Design Decision #2 -- reuse, do not extend, _score_scale_max()). See plan.md Design
        Decision #3 for the full per-term rationale and Anti-Drift Notes for the explicit
        disclosure that these weights/baselines are an initial, not empirically validated,
        calibration.
        """
        from src.core.strategic import ContractKind, RiskLevel

        bond = entity.social.bonds.get(contract.source_id)
        if bond:
            trust = (bond.sentiment + 1.0) / 2.0
        else:
            trust = entity.social.trust_history.get(contract.source_id, 0.5)

        duration = contract.terms.get("duration", 0)
        if contract.expiry_tick and contract.expiry_tick > 0 and duration > 0:
            ticks_remaining = max(0, contract.expiry_tick - current_tick)
            urgency = 1.0 - min(1.0, ticks_remaining / duration)
        else:
            urgency = 0.5

        if contract.kind == ContractKind.RECRUITMENT:
            # terms.get("payout", ...) fallback: execute_recruit()-originated contracts use
            # "payout", not "daily_pay" (Design Decision #9) -- disclosed degradation, not a
            # schema unification.
            pay = contract.terms.get("daily_pay", contract.terms.get("payout", 0))
            expected_pay = 10 * max(1, entity.identity.evolution_level)
            value = min(1.0, pay / expected_pay)
            risk = contract.terms.get("risk_level", RiskLevel.NORMAL)
            risk_weight = 1.0 if risk == "HIGH" else (0.5 if risk == "NORMAL" else 0.1)
        elif contract.kind == ContractKind.LOAN:
            amount = contract.terms.get("amount", 0)
            expected_amount = 50 * max(1, entity.identity.evolution_level)
            value = min(1.0, amount / expected_amount)
            risk_weight = 0.0  # LOAN terms carry no risk_level key (contracts.py, confirmed).
        else:
            # Defensively unreachable: score()'s caller already filters to RECRUITMENT/LOAN via
            # get_project_mapping() before calling this. Kept for safety, not exercised by tests.
            value = 0.0
            risk_weight = 0.0

        raw = (trust * 1.0) + (urgency * 1.0) + (value * 0.9) - (risk_weight * 0.3)
        return max(0.0, min(2.9, raw))
```

**Do NOT touch:** `src/systems/social_systems/appraisal.py` — read-only reference for the trust/risk
input pattern, not called or modified. Do not add this class's logic to `src/ai/goals/scorers.py` — it
lives in its own new file, mirroring `adventure_scorer.py`'s precedent (keeps the other 10+1 scorers'
import surface free of `src.systems.social_systems` — the same reasoning `AdventureGoalScorer`'s own
file placement already established for `src.domains.adventure`).

**Verify:** `test_social_contract_goal_scorer_implements_goal_scorer_protocol`,
`test_social_contract_goal_scorer_metadata_carries_raw_score_and_contract_identity`,
`test_social_contract_goal_scorer_no_active_contracts_returns_zero_utility_no_target`,
`test_social_contract_goal_scorer_reduces_multiple_active_contracts_to_one_candidate`,
`test_social_contract_protection_merchant_position_swap_never_spawn_a_project` (all in
`tests/unit/ai/goals/test_social_contract_goal_scorer.py`, Step 6).

---

### Step 4 — Register `SocialContractGoalScorer` in `src/ai/goals/__init__.py`

**Files:** `src/ai/goals/__init__.py`

**Change:** Confirmed current exact contents (read directly, 22 lines: `GoalKind`, `GoalRegistry`,
`AdventureGoalScorer` import, then 10 scorer imports from `scorers.py`, then 11
`GoalRegistry.register(...)` calls including `ADVENTURE_ROUTE`). Add:
```python
from src.ai.goals.social_contract_scorer import SocialContractGoalScorer
```
placed immediately after the existing `from src.ai.goals.adventure_scorer import AdventureGoalScorer`
line. Then add, after the existing `GoalRegistry.register(GoalKind.ADVENTURE_ROUTE,
AdventureGoalScorer())` line:
```python
GoalRegistry.register(GoalKind.SOCIAL_CONTRACT, SocialContractGoalScorer())
```

**Do NOT touch:** The 10 original scorer import/register lines, or `AdventureGoalScorer`'s own
import/register lines — order and content stay exactly as confirmed read.

**Verify:** `test_goal_kind_social_contract_is_registered_member` (registry-side half:
`GoalRegistry._scorers[GoalKind.SOCIAL_CONTRACT]` is a `SocialContractGoalScorer` instance),
`test_all_registered_scorers_are_canonical` (`tests/unit/strategic/test_enum_drift.py`, existing test,
must keep passing with a 12th member).

---

### Step 5 — Add the `SOCIAL_CONTRACT` materialization branch

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:** Confirmed current exact lines 1440-1486 (read directly): an
`if best_candidate.kind == GoalKind.ADVENTURE_ROUTE: ... else: ...` two-way branch. Insert a new
`elif` between them:
```python
            if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
                # ... UNCHANGED, not reproduced here ...
            elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:
                # AC3/AC4/AC5/AC6 (ticket items 2,3,4,5,6): materialize a contract win into a
                # real ProjectKind-typed project, using proj_kind/obj_kind/obj_id_prefix already
                # resolved by SocialContractGoalScorer via ContractService.get_project_mapping()
                # and carried in metadata -- intelligence.py needs no new import of
                # ContractKind/ContractService/ObjectiveKind to build this branch (all resolved
                # upstream in the scorer).
                contract_id = best_candidate.metadata.get("contract_id")
                proj_kind = best_candidate.metadata.get("proj_kind")
                obj_kind = best_candidate.metadata.get("obj_kind")
                obj_id_prefix = best_candidate.metadata.get("obj_id_prefix", "obj_contract_")
                obj = ObjectiveState(
                    id=f"{obj_id_prefix}{contract_id}_t{current_tick}",
                    kind=obj_kind,
                    target=best_candidate.target_id,
                    target_position=best_candidate.target_pos,
                    status=ObjectiveStatus.ACTIVE,
                )
                candidate_proj = ProjectState(
                    id=f"proj_contract_{contract_id}_t{current_tick}",
                    kind=proj_kind,
                    status=ProjectStatus.ACTIVE,
                    objectives=[obj],
                    active_objective_id=obj.id,
                    # Preserves accept_contract()'s original 50-tick lock (contracts.py pre-edit
                    # line 180, confirmed read directly) -- deliberately NOT the generic branch's
                    # min(current_tick+10, current_tick+50) == current_tick+10 (Design
                    # Decision #10).
                    lock_until_tick=current_tick + 50,
                    created_tick=current_tick,
                    # NEVER best_candidate.utility -- utility is normalized onto the 100-ceiling
                    # scale for tier-5 competition only; ProjectState.score is read back through
                    # _score_scale_max()'s 2.9-ceiling scale once kind is a real ProjectKind.
                    # Passing utility here reproduces the
                    # TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG defect class.
                    score=best_candidate.metadata.get("raw_score", 0.0),
                )
            else:
                # ... UNCHANGED, not reproduced here ...
```
Everything from the original line 1488 onward (`at_capacity = ...`, `evaluate_project_switch(entity,
candidate_proj, current_tick, state=state)`, etc.) stays **unchanged** and continues to reference
`candidate_proj`/`obj`/`existing` as before — all three branches of the now-three-way `if` produce
those same two names, so the rest of the function needs no further edits.

**Other writers to `intelligence.py`'s materialization logic and `current_project_id` this step must
not collide with (Fact-Verification Requirement #2):**
- `src/systems/world_systems/events.py:98` (`stabilize_project`) — unconditional-overwrite bypass,
  unaffected, explicitly out of scope (ticket's Out of Scope section names this as a separate ticket's
  job).
- `if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:` branch (immediately above the new `elif`) —
  same function, same `if/elif/else`, mutually exclusive per call since `best_candidate` is a single
  winner per tick; no collision.
- The `else:` generic branch (all 10 original `GoalKind`s) — same mutual-exclusivity property; no
  collision.
- `ContractService.accept_contract()` (Step 2) — no longer writes `current_project_id_set` or
  `projects_add_or_update` at all after this ticket; the arbiter-materialized path (this step) becomes
  the *only* writer of a contract-originated `ProjectState`/`current_project_id`.
- `existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)`
  (`intelligence.py:1429`, unchanged) — confirmed (Design Decision #5) `best_candidate.kind` (always
  `GoalKind.SOCIAL_CONTRACT`, value `"social_contract"`) never string-equals any real `ProjectKind`
  value, so this lookup never matches for a `SOCIAL_CONTRACT` winner — the resume/dedup short-circuit
  never fires (inherited, shared gap with `ADVENTURE_ROUTE`, explicitly out of scope per
  investigation.md's Anti-Drift Hazards).

**Do NOT touch:** `evaluate_project_switch()`'s signature or internal lock logic
(`intelligence.py:955-1049`, confirmed unchanged) — this step only supplies a new `candidate_project`
into the existing, unmodified call at line 1494. Do not touch the `existing`/resume-suspended-project
lookup at line 1429 (see above — its inertness for `SOCIAL_CONTRACT` is accepted, not fixed here). Do
not add a new top-level import to `intelligence.py` — none is needed (confirmed: `ProjectState`,
`ProjectStatus`, `ObjectiveState`, `ObjectiveStatus`, `GoalKind` are all already imported,
`intelligence.py:64-68`).

**Verify:** `test_social_contract_winner_materializes_with_raw_score_not_utility`,
`test_social_contract_recruitment_maps_to_combat_project_loan_maps_to_social_project`,
`test_active_contract_wins_arbitration_with_no_current_project`,
`test_high_lock_current_project_retains_against_low_urgency_contract`,
`test_high_urgency_contract_interrupts_locked_current_project` (all in
`tests/unit/strategic/test_social_contract_materialization.py`, Step 7).

---

### Step 6 — Unit tests for `SocialContractGoalScorer`

**Files:** `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (new file, same directory as
`test_adventure_goal_scorer.py`)

**Change:** Implement, per test_plan.md's exact specifications:
- `test_goal_kind_social_contract_is_registered_member`
- `test_social_contract_kind_value_does_not_collide_with_project_kind_or_existing_goal_kind` (new,
  checks `GoalKind.SOCIAL_CONTRACT.value` against all `ProjectKind` values and all other `GoalKind`
  values for equality — asserts none match)
- `test_social_contract_goal_scorer_implements_goal_scorer_protocol`
- `test_social_contract_goal_scorer_metadata_carries_raw_score_and_contract_identity` — assert
  `set(score.metadata.keys()) == {"contract_id", "source_id", "raw_score", "proj_kind", "obj_kind",
  "obj_id_prefix"}` exactly (shape-exactness, mirroring `test_adventure_goal_scorer_metadata_carries_
  route_family_and_raw_score`'s style)
- `test_social_contract_goal_scorer_no_active_contracts_returns_zero_utility_no_target`
- `test_social_contract_goal_scorer_reduces_multiple_active_contracts_to_one_candidate` — entity with
  one LOAN, one RECRUITMENT contract, both `ACTIVE`; assert exactly one `GoalScore` returned and that
  `metadata["contract_id"]` matches whichever contract this plan's raw-score formula (Design
  Decision #3) computes as higher for the fixture's chosen terms — compute the expected winner by
  hand in the test docstring, not by assertion-after-the-fact
- `test_social_contract_protection_merchant_position_swap_never_spawn_a_project` — `ACTIVE`
  `PROTECTION`/`MERCHANT`/`POSITION_SWAP` contracts produce `GoalScore(utility=0.0, target_id=None)`
- `test_social_contract_goal_scorer_raw_score_clamped_to_2_9_ceiling` (new, direct regression guard
  for Design Decision #3's clamp) — construct a contract/entity combination that would otherwise
  exceed the formula's natural max (not reachable given the weights chosen, but assert the clamp
  function itself behaves correctly at the boundary via a direct `_raw_score()` call)
- `test_social_contract_target_pos_resolves_to_counterparty_entity_position` (new, direct regression
  guard for Design Decision #8) — entity + a `state.entities` counterparty at a known position; assert
  `score.target_pos == that counterparty's navigation.position`, and a second case with the
  counterparty absent from `state.entities` asserting `score.target_pos is None` (defensive fallback,
  not a crash)

**Do NOT touch:** `tests/unit/ai/goals/test_adventure_goal_scorer.py` — must keep passing unmodified,
confirming `AdventureGoalScorer` is undisturbed by adding a sibling scorer in the same package.

**Verify:** `pytest tests/unit/ai/goals/ -v` passes; all tests listed above pass.

---

### Step 7 — Integration tests for the materialization branch

**Files:** `tests/unit/strategic/test_social_contract_materialization.py` (new file)

**Change:** Implement, per test_plan.md's exact specification (AC3/AC4/AC5/AC6 tests):
- `test_social_contract_winner_materializes_with_raw_score_not_utility` — force a known raw score via
  a controlled `ACTIVE` `RECRUITMENT` contract fixture (not monkeypatching `_raw_score` — construct
  `terms`/`social.bonds`/tick values by hand so the formula in Design Decision #3 yields a known,
  documented raw score), run `evaluate_strategic_intent(state, entity, force=True)` end-to-end, assert
  `ProjectState.score == <the hand-computed raw score>` (not the normalized utility), plus a negative
  check (`project.score != <utility value>`).
- `test_social_contract_recruitment_maps_to_combat_project_loan_maps_to_social_project` — both
  `ContractService.get_project_mapping()` outcomes preserved exactly through the full pipeline:
  `RECRUITMENT` → `ProjectKind.COMBAT`, `LOAN` → `ProjectKind.SOCIAL`, both
  `ObjectiveKind.REACH_LOCATION`, `target=str(source_id)`.
- `test_active_contract_wins_arbitration_with_no_current_project` — entity has no current project, one
  `ACTIVE` `RECRUITMENT`/`LOAN` contract; assert `current_project_id` becomes the materialized
  contract project's id via `evaluate_project_switch()`'s unconditional-adopt path
  (`intelligence.py:985-998`).
- `test_high_lock_current_project_retains_against_low_urgency_contract` — entity has a locked
  (`lock_until_tick > current_tick`), high-score current project plus a newly-`ACTIVE`, deliberately
  low-raw-score contract (e.g. low trust, low urgency, low value); assert `current_project_id`
  unchanged. Worked arithmetic in the docstring, mirroring `test_locked_system_a_current_still_blocks_
  low_urgency_system_b_candidate`'s existing style.
- `test_high_urgency_contract_interrupts_locked_current_project` — locked current project + a
  deliberately high-raw-score contract (near the 2.9 ceiling: high trust, near-expiry urgency, high
  value, low risk) clears both `candidate_pct > normalized_effective_current_pct` and the `0.8` floor;
  assert `current_project_id` switches to the materialized contract project.
- `test_social_contract_target_position_is_tactically_resolvable_not_a_stall` (new, mirrors
  `test_form_party_materialized_objective_is_tactically_resolvable_not_a_stall`'s style, direct proof
  of Design Decision #8's fix) — after materialization, call
  `TacticalDecisionSystem._resolve_target_position(state, materialized_obj)` directly and assert it
  returns a non-`None` position equal to the counterparty entity's `navigation.position` — via the
  `target_position` fallback (`tactical.py:751-752`), confirmed by also asserting `int(obj.target)`
  does NOT resolve via `state.resource_nodes`/`state.buildings` in the fixture (i.e. the fallback path,
  not an accidental resource-node/building id collision, is what resolves it).
- `test_social_contract_and_adventure_route_share_score_scale_as_designed` — asserts
  `_score_scale_max(ProjectKind.COMBAT) == _ADVENTURE_ROUTE_SCORE_MAX` regardless of whether the
  `ProjectKind.COMBAT` instance originated from a contract or from adventure's own `HUNT_WEAK_ENEMY`
  route — explicit, in-code assertion of Design Decision #2's resolution (mirrors the adventure
  ticket's own Risk #1 placeholder-test discipline).
- `test_social_contract_winner_preserves_dedup_lookup_inert_behavior` (new, direct regression guard for
  Design Decision #11) — confirms the pre-existing `existing = next(...)` lookup does not fire for a
  `SOCIAL_CONTRACT` winner (i.e. a suspended contract-project is re-materialized fresh, not resumed) —
  documents the accepted, shared, unfixed gap rather than leaving it silently unasserted.

**Do NOT touch:** `tests/unit/strategic/test_adventure_route_materialization.py` — must keep passing
unmodified, proving the new `elif GoalKind.SOCIAL_CONTRACT:` branch is additive, not a restructure of
the existing `ADVENTURE_ROUTE` branch.

**Verify:** `pytest tests/unit/strategic/test_social_contract_materialization.py -v` passes.

---

### Step 8 — Rewrite `test_accepted_contract_spawns_project_and_objective`

**Files:** `tests/unit/strategic/test_strategic_social_contracts.py`

**Change:** Per the ticket's own Scope ("rewritten as a scorer-output assertion, not just extended")
and test_plan.md's own prescribed shape, replace the current test body (lines 8-36, confirmed exact
read directly above) with three assertions in sequence:
1. `ContractService.accept_contract(ent, "c1", tick=100)` returns a `StrategicUpdate` with
   `current_project_id_set is None` and `contracts_add_or_update[0].status == ContractStatus.ACTIVE`
   (the part of the old test that remains true, now via the simplified Step 2 `accept_contract()`).
2. Apply that `StrategicUpdate` to the entity (or otherwise construct an entity with the `ACTIVE`
   contract present in `entity.strategic.contracts`), then call
   `SocialContractGoalScorer().score(ent_with_active_contract, state)` and assert
   `score.metadata["raw_score"]` is populated and `score.metadata["contract_id"] == "c1"`.
3. Run `StrategicIntelligenceSystem.evaluate_strategic_intent(state, ent_with_active_contract,
   force=True)` end-to-end and assert the resulting `ProjectState.kind == ProjectKind.COMBAT` (the
   **enum member**, not the string `"combat"` — the old test's `proj.kind == "combat"` assertion is
   explicitly upgraded here per AC "uses a real `ProjectKind` enum member", not just ported verbatim)
   and `proj.objectives[0].target == "2"` (preserved from the old test, unchanged mapping).

**Do NOT touch:** `test_contract_failure_degrades_trust`, `test_betrayal_history_blocks_contracts` —
the other two tests in this file, unrelated to the bypass, must keep passing unmodified. Do not create
a duplicate file — the ticket's own Scope names this exact file/test.

**Verify:** `pytest tests/unit/strategic/test_strategic_social_contracts.py -v` passes, all 3 tests in
the file green.

---

### Step 9 — Docs and parity ledger updates

**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`,
`docs/parity_ledger/social_narrative.yaml`,
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`

**Change (`04_strategic_cognition.md` §6.6):** Confirmed current exact text (read directly, lines
247-272): the section already documents a "second consumer" paragraph for `_ADVENTURE_ROUTE_SCORE_MAX`
(added by `TCK-20260811-ADVENTURE-GOAL-SCORER`). Add a third paragraph immediately after it:
```
The same constant has a third consumer as of TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER:
`SocialContractGoalScorer` normalizes its own raw contract score (trust/urgency/value/risk-derived,
independently calibrated to the same 0-2.9 ceiling -- see the parity ledger entry below for the exact
formula) onto the same `GoalScore.utility` 0-100 scale via the same
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` formula. This constant
is therefore now shared by two structurally unrelated raw-score domains (adventure routing, social
contracts) purely because `_score_scale_max()` classifies by Python enum class (`isinstance(kind,
ProjectKind)`), not by provenance -- a deliberate, disclosed design choice (not an oversight), recorded
in `docs/parity_ledger/strategic_cognition.yaml`.
```
**Change (§2, "Generalized Bypass" paragraph):** Confirmed current text names "System A/
`AdventureRouteScorer`" as the sole example of a `ProjectKind`-ceiling candidate. Add a one-sentence
clarifying footnote after the existing paragraph: "As of `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`,
`SocialContractGoalScorer`-materialized projects also land on System A's `~2.9` ceiling once
materialized (any real `ProjectKind`-typed candidate does, by `_score_scale_max()`'s `isinstance`
check) — 'System A' here means 'any `ProjectKind`-typed candidate,' not specifically adventure."

**Change (`strategic_cognition.yaml`):** Add a new entry `STRAT-254` (confirmed next available id —
highest existing is `STRAT-253`), mirroring `STRAT-252`'s structure exactly: `text` describing
`SocialContractGoalScorer`'s landing, the `GoalKind.SOCIAL_CONTRACT = "social_contract"` value and its
deliberate tie-break ordering vs. `ADVENTURE_ROUTE`, the `accept_contract()` simplification, and the
explicit disclosure that the scorer (not `accept_contract()`) is live-reachable via `execute_recruit()`
(Design Decision #1) — `status: verified`, `priority: P2`, `v2_evidence` citing
`src/ai/goals/social_contract_scorer.py`, `src/core/strategic.py` (the enum line),
`src/ai/goals/__init__.py` (the register line), `src/systems/strategic_systems/intelligence.py` (the
elif branch line range), `test_path` pointing at
`tests/unit/strategic/test_social_contract_materialization.py`.

**Change (`social_narrative.yaml`):** Update `SOC-208` (`social_narrative.yaml:2175-2184`, confirmed
read directly, currently `test_path: null`) — set `test_path:
tests/unit/strategic/test_strategic_social_contracts.py::test_accepted_contract_spawns_project_and_objective`
per Design Decision #6's opportunistic-closure choice. Do not change `status` (already `verified`) or
`text`.

**Change (design doc):** Confirmed (per investigation.md) the design doc's "Future Extension Patterns"
section names `contracts.py:187` as this exact still-open future item, and its `BYPASS` subgraph lists
`CON["social_systems/contracts.py:187"]` as a "Still-unguarded bypass writer." Update both to reflect
this migration as done, mirroring how the doc's own `STRAT-252`/`253` addendum pattern tracked
adventure's landing (move `CON` out of the `BYPASS` subgraph, add a landed-migration addendum note
citing this ticket).

**Do NOT touch:** Any other section of `04_strategic_cognition.md` (§1, §3, §4, §5, §6.1-6.5, §6.7-6.10
are unrelated). Do not touch `docs/parity_ledger/town_resource.yaml`, `progression.yaml`, or any other
ledger file — only `strategic_cognition.yaml` and `social_narrative.yaml` are in scope.

**Verify:** No test verifies doc content directly; verified by inspection against the Authoritative
Mechanics Rule (CLAUDE.md) and by `docs-registry`/`frontmatter_valid` checks at Finalize.

---

### Step 10 — Run the full scoped regression suite

**Files:** none (verification-only step)

**Change:** Run exactly the command test_plan.md specifies:
```
pytest tests/unit/ai/goals/ tests/unit/strategic/test_expanded_goals.py tests/unit/strategic/test_score_normalization.py tests/unit/strategic/test_enum_drift.py tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_social_contract_materialization.py tests/unit/strategic/test_strategic_social_contracts.py tests/unit/strategic/test_interruption_resistance.py tests/unit/social/ -v
```
All tests must pass, including the full pre-existing regression surface
(`test_contract_lifecycle.py`'s 4 tests, `test_contracts.py`, `test_social_contracts.py`,
`test_contract_lifecycle_phase7.py`) proving `SocialContractSystem`/`SocialAppraisalSystem` were not
disturbed.

**Do NOT touch:** Never run `pytest tests/` (full suite) per project testing rules.

**Verify:** All listed suites green; no test in the regression surface required an edit to pass (if one
did, that is itself a signal of unintended scope creep and must be investigated before Finalize, not
silently patched).

## Scope Guards

- **Do not wire `ContractService.accept_contract()` into any production call site.** No such wiring
  ticket exists in this epic's `SEQUENCE.md` (confirmed by investigation.md); this ticket's job ends at
  making the arbitration path correct and unit-testable. **This is not the same as claiming the whole
  feature is inert** — see Design Decision #1: the scorer itself is live-reachable via
  `execute_recruit()`'s directly-`ACTIVE` contracts. State this distinction explicitly wherever
  liveness is discussed; do not let "not wired" bleed into "no production impact."
- **Do not widen contract-kind coverage beyond `RECRUITMENT`/`LOAN`.**
  `ContractService.get_project_mapping()` returns `None` for `PROTECTION`/`MERCHANT`/`POSITION_SWAP`,
  exactly matching `accept_contract()`'s original `if obj:` guard behavior — do not make these 3 kinds
  start spawning projects.
- **Do not touch `src/engine/domain/core_actions.py`'s `execute_recruit()`.** It builds contracts as
  already-`ACTIVE` through a structurally different path than `accept_contract()`; this ticket does not
  edit it, only discloses that its output is now visible to the new scorer.
- **Do not touch `src/systems/world_systems/events.py`** (`RegionStabilizationGoalScorer`'s target,
  `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`'s job) or `src/domains/adventure/`,
  `src/ai/goals/adventure_scorer.py`, `src/domains/adventure/mapper.py` (`AdventureGoalScorer`'s own
  materialization path, a separate ticket's job per the ticket's own Out of Scope section).
- **Do not modify `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`, or `_GOAL_UTILITY_SCORE_MAX`.**
  Design Decision #2 explicitly chose to reuse these unchanged; changing them affects
  `ADVENTURE_ROUTE`'s own already-verified calibration too.
  `tests/unit/strategic/test_score_normalization.py`'s 5 existing tests must keep passing unmodified.
- **Do not use `best_candidate.utility` anywhere in Step 5's `ProjectState(score=...)` argument** — the
  single highest-value regression this ticket must not introduce (identical class to the adventure
  ticket's own top Anti-Drift Hazard).
- **Do not leave `accept_contract()` still building its own `ProjectState`/`ObjectiveState`** even if
  only `current_project_id_set` is removed — Design Decision #7's duplicate-project/bandwidth hazard is
  real and must be avoided by removing the construction entirely, not partially.
- **Do not modify `SocialContractSystem.transition_contract()`/`_is_valid_transition()`** — unrelated
  to the bypass, only the post-transition project-spawn block (now entirely removed from
  `accept_contract()`, replaced by the arbiter path) is in scope.
- **Do not modify `TacticalDecisionSystem._resolve_target_position()` or any other code in
  `src/engine/tactical.py`.** Design Decision #8's fix supplies real data
  (`GoalScore.target_pos`/`ObjectiveState.target_position`) to this function's existing, unmodified
  `target_position` fallback — it does not add a new resolution path or change existing ones.
- **Do not attempt to fix the resume/dedup lookup's inertness for `SOCIAL_CONTRACT`** (Design
  Decision #11) — shared, inherited gap with `ADVENTURE_ROUTE`, explicitly out of scope per
  investigation.md's own Anti-Drift Hazards.
- **Do not unify the `terms` schema between `create_recruitment_contract()` and `execute_recruit()`**
  (Design Decision #9) — the defensive `terms.get("daily_pay", terms.get("payout", 0))` fallback in
  the raw-score formula is the full extent of this ticket's response to that mismatch.
- **Do not treat the raw-score formula's weights/baselines as empirically final.** Design Decision #3
  explicitly discloses these as an initial, reasoned calibration, not a validated one, per the ticket's
  own Assumptions bullet.

## Dependency Map

- Step 1 (enum member) has no dependencies. Must land before Steps 2-5 (all reference
  `GoalKind.SOCIAL_CONTRACT`).
- Step 2 (`get_project_mapping()` + simplified `accept_contract()`) has no dependency on Step 1 (does
  not reference `GoalKind` at all), but must land before Step 3 (the scorer imports
  `ContractService.get_project_mapping()`).
- Step 3 (scorer) depends on Steps 1 and 2.
- Step 4 (registration) depends on Step 3.
- Step 5 (materialization branch) depends on Step 1 and Step 3's `metadata` key names (`"contract_id"`,
  `"proj_kind"`, `"obj_kind"`, `"obj_id_prefix"`, `"raw_score"`) — not on Step 4 (reachable via direct
  `evaluate_strategic_intent()` calls in tests even before registration, though Step 7's integration
  tests are more naturally written after Step 4 lands so `GoalRegistry` picks up the scorer
  automatically).
- Step 6 (unit tests) depends on Steps 1-4.
- Step 7 (integration tests) depends on Steps 1-5.
- Step 8 (test rewrite) depends on Steps 2, 3, 5.
- Step 9 (docs/parity) depends on Steps 1-8 having landed (cites concrete line numbers/behavior that
  must already be true).
- Step 10 (regression run) depends on Steps 1-9 all landing.

No step depends on any ticket explicitly marked Out of Scope (region stabilization, adventure's own
materialization path).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| 1 — `ContractService.accept_contract()` no longer sets `current_project_id_set` directly | Step 2 | `test_accept_contract_no_longer_sets_current_project_id_directly` |
| 2 — Accepting a contract produces a `GoalScore` (via `SocialContractGoalScorer`) that clears `evaluate_project_switch()`'s comparison to become `current_project_id` | Step 3, Step 5 | `test_social_contract_goal_scorer_implements_goal_scorer_protocol`, `test_active_contract_wins_arbitration_with_no_current_project` |
| 3 — Entity with a high-lock current project + newly-accepted low-urgency contract keeps its current project | Step 5 (unchanged `evaluate_project_switch()` lock-bypass gate) | `test_high_lock_current_project_retains_against_low_urgency_contract` |
| 4 — Entity with no current project, or a contract that legitimately outscores the lock, does switch | Step 5 | `test_active_contract_wins_arbitration_with_no_current_project`, `test_high_urgency_contract_interrupts_locked_current_project` |
| 5 — Materialized `ProjectState.kind` uses a real `ProjectKind` enum member | Step 3 (`ContractService.get_project_mapping()`), Step 5 | `test_social_contract_recruitment_maps_to_combat_project_loan_maps_to_social_project` |
| 6 — Raw-score/normalized-utility separation: `metadata["raw_score"]`, never utility, goes into `ProjectState.score` | Step 3, Step 5 | `test_social_contract_winner_materializes_with_raw_score_not_utility` |
| 7 — `docs/mechanics` and the relevant parity ledger entry updated in the same session | Step 9 | Inspection at Finalize; `frontmatter_valid` / registry checks |

**AC5/AC6 cross-check (Fact-Verification Requirement #3, confirmed against Steps):** AC5 says
"Materialized `ProjectState.kind` uses a real `ProjectKind` enum member" — Step 5's branch sets
`kind=proj_kind` where `proj_kind` is one of `ProjectKind.COMBAT`/`ProjectKind.SOCIAL` (real enum
members, sourced from `ContractService.get_project_mapping()`, Step 2), never `GoalKind.SOCIAL_CONTRACT`
itself and never a bare string — matches. AC6 says "`metadata["raw_score"]`, never utility, goes into
`ProjectState.score`" — Step 5's branch sets `score=best_candidate.metadata.get("raw_score", 0.0)`
verbatim, and Step 3's scorer always populates `metadata["raw_score"]` (never omits it on the winning
path) — matches, no contradiction found between the ticket's stated field names and this plan's Steps.

## Anti-Drift Notes

- **The single highest-value regression to guard**: Step 5's `ProjectState(score=...)` argument must be
  `best_candidate.metadata.get("raw_score", 0.0)`, never `best_candidate.utility`. A regression here
  silently reproduces the `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect class —
  the entity still "works," it just becomes permanently un-interruptible or trivially interruptible
  depending on which direction the scale mismatch goes.
- **Design Decision #7's duplicate-project hazard is the second highest-value regression to guard.** A
  future edit that re-adds any `ProjectState`/`ObjectiveState` construction to `accept_contract()`
  (even without `current_project_id_set`) would silently reintroduce an orphaned project consuming
  `max_active_projects` bandwidth. No test directly asserts `entity.strategic.projects` stays free of
  extra entries after a bare `accept_contract()` call without a full-arbitration follow-up — Step 2's
  `test_accept_contract_no_longer_sets_current_project_id_directly` should additionally assert
  `strat_up.projects_add_or_update == []` (not just `current_project_id_set is None`) to close this
  gap; Implement must add this assertion even though test_plan.md's own wording only mentions the
  `current_project_id_set` check.
- **Design Decision #8's "wins but stalls" fix is inherited-bug remediation, not new-feature
  gold-plating — do not skip it as "out of scope."** Without `target_pos` resolution, a contract
  project that wins tier-5 arbitration would lock the project slot but never let the entity navigate
  toward the counterparty, silently reproducing the exact defect class the architecture-reviewer
  required a fix for in `TCK-20260811-ADVENTURE-GOAL-SCORER`. This was **not** flagged in
  investigation.md — it is a new finding from this plan's own fact-verification pass — but is squarely
  within this ticket's scope (it lives entirely inside the new scorer's own `target_pos` construction,
  the same sanctioned fix location the adventure ticket's plan used).
- **Raw-score formula weights/baselines (Design Decision #3) are disclosed as unvalidated.** Do not
  present them in `docs/parity_ledger/strategic_cognition.yaml`'s new entry as empirically proven — the
  entry's `v2_evidence` should describe them as "unit-verified for the documented worked examples," not
  "calibrated against live gameplay data," since no such data exists at ticket-authoring time.
  Empirical re-tuning (e.g. once this scorer's execute_recruit-reachable behavior is observed in a real
  run) is a natural future ticket, not required by this ticket's ACs.
- **Materialized project/objective ids are tick-suffixed (Design Decision #10), not stable.** Do not
  "simplify" this back to `accept_contract()`'s original stable `proj_contract_{contract.id}` form
  during Implement even though it looks simpler — that reintroduces the same-id lock-refresh ambiguity
  analyzed in Design Decision #10, which has no test coverage designed against it.
- **`lock_until_tick=current_tick+50` in Step 5 is deliberately NOT the generic branch's
  `min(current_tick+10, current_tick+50)` (== `current_tick+10`).** Do not "unify" these two branches'
  lock durations during Implement — the 50-tick value is a deliberate preservation of
  `accept_contract()`'s original contract-specific lock semantics, not an oversight or inconsistency to
  clean up.
- **`ContractService.get_project_mapping()` is the single source of truth for kind→(`ProjectKind`,
  `ObjectiveKind`, id-prefix) mapping** — both the scorer's eligibility filter and (indirectly, via
  metadata) the materialization branch must derive from it. Do not let a future edit hardcode this
  mapping a second time anywhere else (e.g. directly inside `social_contract_scorer.py` or
  `intelligence.py`) — that would reintroduce the exact "two sources of truth can drift" risk this
  extraction was designed to prevent.
- **Docs**: `docs/mechanics/04_strategic_cognition.md` §2/§6.6,
  `docs/parity_ledger/strategic_cognition.yaml` (new `STRAT-254`), `docs/parity_ledger/
  social_narrative.yaml` (`SOC-208`'s `test_path`), and the design doc's "Future Extension Patterns"/
  `BYPASS` subgraph (Step 9) must not be silently skipped — this ticket's own AC 7 depends on all four
  landing in the same session.

---

## Deviations (recorded during Implement)

Steps 1-8 were implemented exactly as specified, with the following additions/clarifications not
literally spelled out in plan.md/test_plan.md's prose (Steps 9-10 are explicitly out of scope for
this Implement pass — deferred to a separate Document-Update/Parity phase per the task's own
instructions; the Step 10 scoped regression command was still run and is reported in the ticket's
Test Summary):

1. **Standalone `test_accept_contract_no_longer_sets_current_project_id_directly`.** Added to
   `tests/unit/social/test_contract_lifecycle.py` (co-located with the existing
   `test_contract_lifecycle_acceptance`), asserting `current_project_id_set is None` AND
   `projects_add_or_update == []`. This is not a deviation from Design Decision content — it is
   exactly what this plan's own Anti-Drift Notes section required ("Implement must add this
   assertion even though test_plan.md's own wording only mentions the `current_project_id_set`
   check") — recorded here because test_plan.md's own AC1 section left the exact location
   ambiguous ("co-located... or ... if Plan decides the rewritten test... covers this directly").
   Both landed: the standalone test (this file) plus the rewritten
   `test_accepted_contract_spawns_project_and_objective`'s own first step (a different
   fixture/entity, not an exact duplicate).

2. **AC5/AC6 integration test arithmetic required two hand-derived adjustments beyond
   test_plan.md's worked-arithmetic sketches**, both disclosed in the tests' own docstrings in
   `tests/unit/strategic/test_social_contract_materialization.py`:
   - The retention test (`test_high_lock_current_project_retains_against_low_urgency_contract`)
     needed the entity's HP set below the 80% threshold used by `_threat_resolved()`
     (STRAT-236's early lock-release check). A full-HP, no-hostile-nearby entity causes
     `evaluate_project_switch()`'s locked-branch gate to be unconditionally bypassed regardless
     of score, which would have made the test pass vacuously (via the final raw check alone,
     not the normalized lock-bypass gate this AC is actually about). Not a bug — a
     previously-undocumented interaction between the new `SOCIAL_CONTRACT` branch and an
     existing, unmodified STRAT-236 mechanism.
   - The interruption test (`test_high_urgency_contract_interrupts_locked_current_project`)
     needed a low `interruption_resistance` (0.01, mirroring
     `test_score_normalization.py::test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`'s
     own pattern for `ProjectKind`-typed candidates). With the DEFAULT profile
     (`interruption_resistance=0.3`, `resistance_multiplier=30.0` → `retention_margin=9.0`), a
     contract-originated candidate's raw score (capped at 2.9 per Design Decision #2's shared
     scale) can never clear `evaluate_project_switch()`'s final raw
     `candidate.score > effective_current_score` check against ANY locked current, regardless of
     urgency — a structural consequence of reusing the 2.9 ceiling, not something in scope to fix
     here, but it meant the natural reading of test_plan.md's own AC6 worked-arithmetic sketch
     (reusing the retention test's locked-current values wholesale) would never actually switch.
     Both gates (lock-bypass AND the final raw check) now genuinely clear in the implemented
     test.
