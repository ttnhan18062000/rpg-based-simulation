---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER
artifact_type: investigation
tags: [social, cognition]
---

# Investigation — TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER

## Current Behavior

### `src/systems/social_systems/contracts.py` — `ContractService.accept_contract()` (exact bypass site confirmed)

Full method at lines 136-190. Exact sequence:

```python
135: @staticmethod
136: def accept_contract(entity, contract_id, tick) -> StrategicUpdate:
144:     strat_up, _ = SocialContractSystem.transition_contract(entity, contract_id, ContractStatus.ACTIVE, tick)
148:     contract = entity.strategic.contracts.get(contract_id)
149:     if contract and strat_up.contracts_add_or_update:
153:         proj_kind = ProjectKind.SOCIAL   # default
155:         if contract.kind == ContractKind.RECRUITMENT:
156:             proj_kind = ProjectKind.COMBAT
157:             obj = ObjectiveState(id=f"obj_recruit_{contract.id}", kind=ObjectiveKind.REACH_LOCATION,
                                      target=str(contract.source_id), status=ObjectiveStatus.ACTIVE)
163:         elif contract.kind == ContractKind.LOAN:
164:             proj_kind = ProjectKind.SOCIAL
165:             obj = ObjectiveState(id=f"obj_loan_{contract.id}", kind=ObjectiveKind.REACH_LOCATION,
                                      target=str(contract.source_id), status=ObjectiveStatus.ACTIVE)
172:         if obj:
173:             proj = ProjectState(id=f"proj_contract_{contract.id}", kind=proj_kind, status=ProjectStatus.ACTIVE,
                                     objectives=[obj], active_objective_id=obj.id, created_tick=tick, lock_until_tick=tick+50)
184:         if projects_add:
185:             strat_up = replace(strat_up,
186:                 projects_add_or_update=list(strat_up.projects_add_or_update) + projects_add,
187:                 current_project_id_set=projects_add[0].id)   # <-- THE BYPASS: unconditional, no evaluate_project_switch() call
190:     return strat_up
```

**The ticket's cited line 187 is exactly this `current_project_id_set=projects_add[0].id` assignment** — confirmed, not approximate. This runs *unconditionally* whenever a RECRUITMENT or LOAN contract transitions OFFERED/COUNTERED → ACTIVE, regardless of what the entity's current locked project is or how urgent it is. No `evaluate_project_switch()` call anywhere in this method.

**Contract-kind coverage gap (pre-existing, not introduced by this ticket, must be preserved or explicitly widened by Plan)**: only `ContractKind.RECRUITMENT` and `ContractKind.LOAN` ever set `obj` (lines 155-171); for `PROTECTION`, `MERCHANT`, and `POSITION_SWAP` contracts, `obj` stays `None`, the `if obj:` guard at line 172 never fires, `projects_add` stays empty, and **no project is spawned at all** for those three contract kinds today, accepted-or-not. `ContractKind` has 5 members total (`RECRUITMENT, LOAN, PROTECTION, MERCHANT, POSITION_SWAP`, `strategic.py:73-83`) — only 2 of 5 produce a project. Any new `SocialContractGoalScorer` that "delegates to `ContractService`'s existing unchanged internal contract-acceptance logic" per the ticket's own Scope wording should preserve exactly this same 2-of-5 coverage unless Plan explicitly decides to widen it (a scope expansion, not implied by the ticket text).

### `ContractService.accept_contract()` has **no production caller anywhere in `src/`** (confirmed, not assumed)

```
grep -rn "accept_contract" src/ tests/ --include=*.py
  src/systems/social_systems/contracts.py:136:    def accept_contract(
  tests/unit/social/test_contract_lifecycle.py:75:    update = ContractService.accept_contract(entity, contract.id, tick=100)
  tests/unit/strategic/test_strategic_social_contracts.py:26:    strat_up = ContractService.accept_contract(ent, "c1", tick=100)
```

Only 2 test files call it directly. `src/engine/pipeline.py:344-346` wires `ContractService.process_active_contracts` and `ContractService.reap_expired_offers` as pipeline phases, but **not** `accept_contract`. There is no `ContractLifecyclePhase` call to it either (`src/engine/pipeline_phases/contracts.py` only calls `SocialContractSystem.transition_contract`/`resolve_contract_outcome`-adjacent expiry logic, not `ContractService.accept_contract`).

Two real production contract-creation paths exist, **neither of which calls `accept_contract()`**:
1. `src/domains/cooperation/services.py:170-181` — `CooperationDecisionResult` posture `REQUEST_HELP`/`HIRE_SUPPORT` creates a **RECRUITMENT contract as OFFERED** (via `ContractService.create_recruitment_contract`), added to `strategic.contracts_add_or_update`. No acceptance, no project.
2. `src/engine/domain/core_actions.py:56-144` (`CoreActions.execute_recruit`) — appraises via `SocialAppraisalSystem.appraise_contract`, and on `ContractStatus.ACCEPTED` constructs a contract **already `status=ContractStatus.ACTIVE`** directly (lines 96-105), delivered via `ResourceTransferIntent.strategic_upd`, entirely bypassing both `SocialContractSystem.transition_contract` and `ContractService.accept_contract`. **This path never spawns a project or touches `current_project_id_set` at all** — a contract accepted through `execute_recruit` today produces no strategic project, a different (lesser) gap than the one this ticket targets, out of scope here (this ticket's Scope is specifically `accept_contract()`'s direct overwrite, not `execute_recruit`'s missing-project gap).

**Implication for this ticket, flagged as an open question, not resolved here (see Risks)**: the exact chain "accept a contract → compete for the project slot via the arbiter → possibly win" has **no live production trigger today**. It is unit-testable (as the existing tests already exercise `accept_contract()` directly) but not exercised end-to-end in a real simulation tick, unlike `AdventureGoalScorer`, which its own module docstring confirms is "the live, sole adventure-decision path today... reached unconditionally, every tick." The epic's `SEQUENCE.md` has no follow-on ticket that wires `accept_contract()` (or `execute_recruit`) into a production call site — confirmed by reading `tickets/todos/adventure-cognition-merge/SEQUENCE.md` in full.

### `src/ai/goals/base.py`, `src/ai/goals/adventure_scorer.py`, `src/ai/goals/__init__.py` — confirmed precedent, already generalized once

`GoalScore` (`base.py:8-14`): `kind`, `utility`, `target_id`, `target_pos`, `metadata: Dict[str, Any]`. `GoalRegistry.register()` validates `kind` via `GoalKind(kind)`. `GoalRegistry.get_all_scores()` calls exactly one `score(entity, state)` per registered kind, in sorted-key order — **one `GoalScore` per scorer per entity per tick**, which matters directly for the reduction problem noted below (an entity can hold multiple simultaneous `ACTIVE` contracts in `entity.strategic.contracts`, but `SocialContractGoalScorer.score()` may return only one `GoalScore`).

`AdventureGoalScorer` (`adventure_scorer.py`, 281 lines) is already fully landed (this session, prior ticket in this epic) and is the concrete structural precedent:
- Eligibility short-circuit before any expensive work (`_supports_adventure_routing`) → `GoalScore(utility=0.0, target_id=None)` early return.
- Metadata carries `route_family` and `raw_score` (the pre-normalization value) — the two keys the materialization branch consumes.
- Normalization formula: `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX`.
- A `_resolve_placeholder_target_pos()` static helper was needed for 3 of 15 route families that don't naturally carry a `target_pos`, to avoid a "wins but stalls" defect at the tactical layer — flagged here as a precedent pattern to watch for, not as directly applicable to contracts (contracts always have a real `target_id`/`target_pos`-able counterpart entity, see below).

`GoalKind` registration in `__init__.py` (21 lines): one `GoalRegistry.register(GoalKind.X, XScorer())` line per scorer, `AdventureGoalScorer` is the 11th, imported from its own new file `adventure_scorer.py` (not `scorers.py`) to keep adventure-domain imports out of the shared scorers module — the same reasoning applies to a new `SocialContractGoalScorer`, which needs `src.systems.social_systems.contracts` imports; **recommend a new file `src/ai/goals/social_contract_scorer.py`**, not adding to `scorers.py`, mirroring the adventure precedent exactly.

### `src/core/strategic.py` — enum state (confirmed exact, post ticket-1)

```python
121: class GoalKind(str, Enum):
    HARVESTING = "harvesting"; FATIGUE = "fatigue"; HUNGER = "hunger"; SOCIAL = "social";
    TOWN_RETURN = "town_return"; COMBAT_ENGAGE = "combat_engage"; COMBAT_RETREAT = "combat_retreat";
    RECOVER = "recover"; RESOLVE_BLOCKER = "resolve_blocker"; GUILD = "guild";
    ADVENTURE_ROUTE = "z_adventure_route"  # deliberately sorts after all 10 originals (Risk #5 in prior ticket)
```
11 members today (10 original + `ADVENTURE_ROUTE`, already landed with a `"z_"`-prefixed value specifically so it never wins a tie-break sort against any of the 10 originals). `SOCIAL_CONTRACT` will be the **12th** member. **New finding, not covered by the prior ticket**: since `ADVENTURE_ROUTE` already claims the `"z_"` prefix, a naive `"z_social_contract"` value creates a **second** tie-break question the prior ticket never had to answer — `"z_adventure_route"` vs `"z_social_contract"` sort *against each other* (`'z_a' < 'z_s'` lexicographically, so `ADVENTURE_ROUTE` would win any exact-utility tie against `SOCIAL_CONTRACT` under the unchanged `modified_scores.sort(key=lambda x: (-x.utility, x.kind))`, `intelligence.py:1408`). Whether that ordering is the *deliberately correct* one (adventure is "routine, non-urgent" per the design doc §2, so should social-contract urgency also lose ties to it, or should an accepted obligation rank above routine adventuring?) is a genuine semantic question, not a mechanical one — flagged in Risks, must not be picked arbitrarily (mirrors the ticket's own AC framing for `ADVENTURE_ROUTE`'s value in the prior ticket).

```python
139: class ProjectKind(str, Enum):
    CRAFTING, QUEST, EXPLORATION, COMBAT, SOCIAL, RECOVERY, PREPARATION, TRAINING,
    HARVESTING, INFORMATION, INFORMATION_SEEKING, TRAVEL = ...
```
No dedicated "obligation"/"contract" `ProjectKind` member exists. `accept_contract()` already reuses `ProjectKind.COMBAT` (RECRUITMENT) and `ProjectKind.SOCIAL` (LOAN) today — the materialization branch should reuse these same two mappings (contract-kind-conditional), consistent with AC "Materialized `ProjectState.kind` uses a real `ProjectKind` enum member" and with "delegating to `ContractService`'s existing unchanged internal contract-acceptance logic."

`ContractKind` (`:73-83`): `RECRUITMENT, LOAN, PROTECTION, MERCHANT, POSITION_SWAP` (5 members). `ContractState` (`:182-195`): `id, kind, source_id, target_id, terms: Dict[str, Any], expiry_tick, status, created_tick, negotiation_count`. `terms` observed shapes: LOAN → `amount, interest_rate, total_due, duration`; RECRUITMENT → `daily_pay, duration, risk_level`. `RiskLevel` (`:173-178`): `LOW, NORMAL, HIGH, EXTREME`.

### `_score_scale_max()` (`intelligence.py:91-109`) — critical, non-obvious constraint confirmed by direct read

```python
def _score_scale_max(kind) -> float:
    if isinstance(kind, ProjectKind):
        return _ADVENTURE_ROUTE_SCORE_MAX   # 2.9
    return _GOAL_UTILITY_SCORE_MAX          # 100.0
```

Dispatch is **purely by Python enum class identity** (`isinstance(kind, ProjectKind)`), not by provenance. `ProjectState` (`strategic.py:247-258`) has **no provenance field** — just `id, kind, status, score, lock_until_tick, objectives, active_objective_id, created_tick, failure_count`. Nothing on it records "this came from `RouteToProjectMapper`" vs. "this came from a future contract mapper."

**This means: once this ticket's materialization branch emits a real `ProjectKind` member (as AC requires), `_score_scale_max()` will classify it onto the *exact same* 2.9-ceiling constant currently named `_ADVENTURE_ROUTE_SCORE_MAX` and calibrated solely against `AdventureRouteScorer`'s own 0-2.9 output range** (`docs/mechanics/04_strategic_cognition.md` §6.6). There is no third scale. Consequences:
- The new raw-score formula's natural ceiling must itself be designed/calibrated to plausibly top out near 2.9 for the lock-bypass percentage math (`evaluate_project_switch()`, see below) to behave sanely relative to adventure-routed and any other future `ProjectKind`-typed candidates — **or** `_score_scale_max()` must be extended with a genuinely new, more specific classification (a third constant, dispatched on something other than bare `isinstance(kind, ProjectKind)`, since that alone cannot distinguish "this `ProjectKind.SOCIAL` came from a contract" from "this `ProjectKind.SOCIAL` came from adventure's `FORM_PARTY` route").
- This is **not** speculative — it is a direct, mechanical consequence of the existing dispatch function's documented behavior ("Anything else... defaults to the GoalRegistry/universal-baseline scale... isinstance(kind, ProjectKind)... Does not unify or alter the ProjectKind/GoalKind vocabulary split — out of scope, tracked under D22"), read verbatim from its own docstring at `intelligence.py:100-105`.
- **Flagged as the single highest-priority open question for Plan** (see Risks) — analogous to, but structurally distinct from, `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`'s fix: that bug was about which denominator to use; this is about whether a *shared* denominator constant, literally named for a different system, is even the right one to reuse for a second, unrelated raw-score domain.

### `evaluate_project_switch()` (`intelligence.py:955-1049`) — confirmed mechanically achievable for both ACs, with one caveat

- **No current project, or current not `ACTIVE`** (`985-998`): unconditional immediate adopt, `current_project_id_set=candidate_project.id`. Satisfies AC "An entity with no current project... does switch" **exactly as-is**, no changes needed here — same mechanism ticket 1 already exercised for adventure.
- **Current locked** (`current.lock_until_tick > current_tick`, `1005-1037`): bypass requires `candidate_project.kind == "detour"` (unconditional, not our case) **or** `candidate_pct > normalized_effective_current_pct AND candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT (0.8)`, where `candidate_pct = candidate_project.score / _score_scale_max(candidate_project.kind)`. Given the `_score_scale_max` finding above, if the contract raw-score formula is *not* calibrated sensibly against the 2.9 ceiling, a "low-urgency" contract could accidentally clear 0.8 of 2.9 (i.e. raw score > 2.32) far too easily, or a "high-urgency, should-win" contract could fail to reach it — **the AC's own qualitative framing ("high-lock ... low-urgency ... keeps its project", "legitimately outscores ... does switch") is only mechanically true once the raw-score formula and its ceiling are jointly calibrated; the arbitration mechanism itself is already correct and unchanged.**
- **Current unlocked** (`1039-1047`): `candidate_project.score > effective_current_score` — a **raw**, unnormalized comparison, pre-existing and unrelated to the lock-bypass gate above; also directly exposed to whatever scale the contract raw score lands on.

### Materialization branch (`intelligence.py:1428-1486`) — confirmed exact shape, new branch required

```python
1428: if best_candidate:
1429:     existing = next((p for p in strat.projects.values() if p.kind == best_candidate.kind), None)
1431-1438:  # resume-if-suspended (see caveat below)
1440:     if best_candidate.kind == GoalKind.ADVENTURE_ROUTE:
1441-1467:      # RouteToProjectMapper.map_to_states(family=..., score=metadata["raw_score"], ...)
1468:     else:
1469-1486:      # generic: ProjectState(kind=best_candidate.kind, score=best_candidate.utility)
```

A **new** `elif best_candidate.kind == GoalKind.SOCIAL_CONTRACT:` branch is required, mirroring the `ADVENTURE_ROUTE` branch's shape: build `ProjectState`/`ObjectiveState` from data carried in `best_candidate.metadata` (must include, at minimum, enough to reconstruct the same `(ProjectKind, ObjectiveState)` pair `accept_contract()` used to build inline — i.e. the contract's `id`, `kind`, `source_id`/`target_id`), with `score=best_candidate.metadata.get("raw_score", 0.0)` — **never `best_candidate.utility`**, identical Anti-Drift rule to the adventure ticket, for the identical reason (`_score_scale_max` reads `ProjectState.score` against the 2.9 ceiling once `kind` is a real `ProjectKind`).

**Confirmed structural finding, not present in the adventure ticket's own investigation**: the `existing = next(... p.kind == best_candidate.kind ...)` dedup/resume lookup at line 1429 runs **before** the kind-dispatch, and compares `p.kind` (a real `ProjectKind` for any already-materialized adventure/contract project, or a raw `GoalKind` for any of the 10 generic-branch projects) against `best_candidate.kind` (always the *scorer's* `GoalKind`, e.g. `GoalKind.SOCIAL_CONTRACT` — never the materialized `ProjectKind`). Because `GoalKind`/`ProjectKind` are both `str, Enum` mixins, `==` compares by **string value**, not class identity (unlike `_score_scale_max`'s deliberate `isinstance` check) — so this lookup will only ever match if `GoalKind.SOCIAL_CONTRACT`'s chosen string value happens to collide with a real `ProjectKind` value (it must not — avoid `"social"`/`"combat"`, which are live `ProjectKind` values already reused by `accept_contract()`). Given a safely-chosen distinct value, this resume/dedup check **never fires** for a materialized `SOCIAL_CONTRACT` project, mirroring the identical, already-accepted gap for `ADVENTURE_ROUTE` (a suspended contract-obligation project is never found by this lookup and would be re-materialized fresh, not resumed, on a later tick) — **inherited, not newly introduced by this ticket, not something this ticket needs to fix** (would require the same generalization for both kinds together, out of scope here).

**Concrete, actionable recommendation for Plan** (not binding, a design option worth recording): unlike `RouteToProjectMapper.map_to_states()`'s project id (`f"proj.{family.value}.ent{entity_id}.t{tick}"`, tick-suffixed, changes every tick), `accept_contract()`'s **existing** id format is `f"proj_contract_{contract.id}"` — **not** tick-suffixed, already stable/idempotent across ticks for the same contract. If the new materialization branch reuses this same id-construction convention (contract-id-keyed, not tick-keyed), repeated re-materialization of the same still-losing, still-`ACTIVE` contract across ticks naturally converges on the same project id instead of spawning a fresh one every tick it's evaluated but doesn't win — a cheap partial mitigation for the resume gap above, worth Plan's consideration, not a requirement.

### `StrategicUpdate.merge()` / `EntityUpdate.merge()` (`src/core/updates.py:530-560`) — confirmed last-writer-wins

```python
549: current_project_id_set=other.current_project_id_set if other.current_project_id_set is not None else self.current_project_id_set,
```
Confirms the orchestrator's framing: last non-`None` writer wins on merge. Not directly exercised by this ticket's own new code (the arbiter's single write path is unaffected), but relevant context for why `accept_contract()`'s direct write was a real bypass — nothing about `merge()` itself would have caught or arbitrated a second unconditional write.

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §2 ("Generalized Bypass")**: governs `evaluate_project_switch()`'s lock-bypass gate — unchanged by this ticket, only fed a new kind of raw-scored candidate. Same law adventure now competes under.
- **`docs/mechanics/04_strategic_cognition.md` §6.6 ("Score Range Summary")**: currently documents only `AdventureRouteScorer`'s ~0-2.9 range as the normalization anchor for `_ADVENTURE_ROUTE_SCORE_MAX`. Once a second, structurally unrelated raw-score domain (contracts) is classified onto the *same* constant (per the `_score_scale_max` finding above), this section either needs a note disclosing the shared-scale reuse, or the constant needs splitting — Plan must decide which, and either way the doc goes stale the moment this ticket lands without an update.
- **Durable State Rule (CLAUDE.md)**: `GoalScore.metadata` is intra-tick only (consumed and discarded within the same `evaluate_strategic_intent()` call), same reasoning as the adventure ticket's investigation already established — carrying contract identity/raw score there is consistent with the rule. What's committed into `ProjectState`/`ObjectiveState` via the arbiter is the durable surface that must stay on the correct scale.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml`: no existing entry documents the `contracts.py:187` bypass or its fix (confirmed by direct grep — no `contract`/`bypass`/`current_project_id_set=projects_add` hits anywhere in this file). A new entry is required describing the `SocialContractGoalScorer` wrapper and its materialization branch, mirroring the `STRAT-252`/`STRAT-253` pattern already used for `AdventureGoalScorer`'s own landing.
- `docs/parity_ledger/social_narrative.yaml`: `SOC-208` ("Accepted contract creates explicit obligation/contract state", P0, `status: verified`, `test_path: null` today) is directly exercised by this ticket's rewritten test — an opportunistic-closure candidate (add a real `test_path`) once the rewritten `test_accepted_contract_spawns_project_and_objective` (or its replacement) lands, per the same "close it if a natural test lands, don't force one" discipline the adventure ticket applied to `STRAT-185`.
- `docs/mechanics/04_strategic_cognition.md`: §2/§6.6 both need the disclosure described above (new tier-5 candidate kind exists; scale-sharing decision recorded once Plan resolves the `_score_scale_max` question).
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: its own "Future Extension Patterns" section (lines 365-378) names this *exact* migration as a still-open future item (`src/systems/social_systems/contracts.py:187 → a SocialContractGoalScorer`), and its component diagram's `BYPASS` subgraph (lines 472-487) lists `CON["social_systems/contracts.py:187"]` as a "Still-unguarded bypass writer." Both go stale the moment this ticket lands and should be updated to reflect the migration as done (mirroring how the doc's own STRAT-252/253 addendum pattern tracked adventure's landing).

## Parity Ledger Overlap

- **SOC-208** (P0, `social_narrative.yaml`, `status: verified`, `test_path: null`): "Accepted contract creates explicit obligation/contract state." Directly overlaps this ticket's scope — the rewritten test is a natural close-candidate for its `test_path` gap (per the same non-forcing discipline as the adventure ticket's STRAT-185 treatment).
- **STRAT-185/186/187** (P0, `strategic_cognition.yaml:1987-2035`): general interruption-resistance/retention-priority laws. Not contract-specific, but this ticket's correctness (raw-score threading into `evaluate_project_switch()`) is a precondition for these continuing to hold once a second `ProjectKind`-typed candidate system exists — same relationship the adventure ticket's investigation already recorded for itself, now doubled since two independent systems share the 2.9-ceiling classification.
- **No existing entry documents the `contracts.py:187` bypass itself** — this ticket's fix has no ledger entry to update; it must add one (see Docs Requiring Update).

## Prior Work

- **`TCK-20260811-ADVENTURE-GOAL-SCORER`** (done, `stored_artifacts/TCK-20260811-ADVENTURE-GOAL-SCORER/`): the wrapper pattern's origin and this ticket's direct structural precedent — file layout (new co-located scorer module, not `scorers.py`), metadata-carries-raw-score convention, tie-break-value discipline (`"z_"`-prefix pattern, now needing a *second* decision relative to `ADVENTURE_ROUTE` itself, see Risks), and the "never `best_candidate.utility` in materialization" anti-drift rule all carry over directly.
- **`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`**: landed `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX`, and the normalized-percentage lock-bypass gate this ticket's contract candidates will flow through unchanged — but also the source of the shared-scale constraint flagged above as this ticket's top risk (that ticket generalized the *mechanism*, not the *scale vocabulary*, and `_score_scale_max` was written assuming only one non-`GoalKind` system would ever exist).
- **`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`**: fixed the `retention_margin` normalization-denominator bug (`intelligence.py:1034`, divides by `_GOAL_UTILITY_SCORE_MAX`, not `current_max`) — already fixed generically, applies automatically to contract-originated locked projects too, no further action needed here.
- **`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`**: names this exact ticket's target (`contracts.py:187`) explicitly in its own "Future Extension Patterns" and diagram sections (see Docs Requiring Update) — confirms this ticket is executing a specifically-anticipated, not speculative, follow-on.
- **`tests/unit/strategic/test_strategic_social_contracts.py`** (full file read, 1 test: `test_accepted_contract_spawns_project_and_objective`) and **`tests/unit/social/test_contract_lifecycle.py`** (full file read, `test_contract_lifecycle_acceptance` also calls `accept_contract()` but only asserts on `contracts_add_or_update`/status/`expiry_tick`, not on `current_project_id_set` or `projects_add_or_update` — **will not need rewriting**, only `test_strategic_social_contracts.py`'s test is in scope per the ticket's own AC).

## Risks and Open Questions

1. **`_score_scale_max()` scale-sharing question (top priority, blocking for Plan, not assumable by formula alone)**: once this ticket's materialized `ProjectState.kind` is a real `ProjectKind`, it is classified by `_score_scale_max()` onto the *same* `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` constant currently calibrated solely against `AdventureRouteScorer`'s own range, because that function only checks `isinstance(kind, ProjectKind)` with no further provenance signal, and `ProjectState` carries none. Plan must explicitly choose one of: (a) calibrate the new raw-score formula to plausibly top out near 2.9 too (simplest, but couples two unrelated domains' scales together, possibly non-obviously to future readers), or (b) extend `_score_scale_max()`/the constant set with a genuinely new classification signal (larger change, touches shared arbitration code both adventure and contracts now depend on). **This is not the same question as the adventure ticket's own §4 raw-score-vs-utility bug — that was about which value to pass; this is about whether the shared denominator itself is structurally correct for a second, independent raw-score system.**

2. **No raw-score formula is prescribed by the ticket, and none should be assumed here.** Available real inputs at the scorer's disposal, confirmed by direct read: `contract.terms` (LOAN: `amount, interest_rate, total_due, duration`; RECRUITMENT: `daily_pay, duration, risk_level`), `contract.expiry_tick` (urgency-by-proximity-to-deadline), `entity.social.bonds`/`trust_history` (same trust inputs `SocialAppraisalSystem.appraise_contract` already reads), `RiskLevel` weighting (mirrors `_appraise_recruitment`'s own `risk_weight` pattern, `appraisal.py`). The ticket's own Assumptions section explicitly flags "Needs empirical validation of normalization constants (not assumable by formula alone)" — Plan must design and justify this formula, not treat it as mechanical.

3. **One scorer, one `GoalScore`, but an entity can hold multiple simultaneous `ACTIVE` contracts** (`entity.strategic.contracts: Dict[str, ContractState]`, unbounded). `GoalRegistry.get_all_scores()` calls `SocialContractGoalScorer.score()` exactly once per entity per tick and expects exactly one `GoalScore` back. Unlike `AdventureDecisionService.decide()`, which already internally reduces up to 25 candidates to one winner, **no existing service reduces multiple contracts to one**. `score()` itself must implement this reduction (e.g., highest-computed-raw-score-among-`ACTIVE`-contracts-without-an-existing-materialized-project wins the single candidate slot this tick) — a genuinely new piece of logic, not a delegation to something that already exists, despite the ticket's "delegating to `ContractService`'s existing unchanged internal contract-acceptance logic" phrasing (that phrasing covers the *kind→(ProjectKind, ObjectiveState)* mapping sub-logic at lines 153-171, not a multi-contract reduction, which has no prior-art anywhere in this codebase).

4. **`accept_contract()` has no live production caller, and neither does the entity-decision that would call it.** This ticket can make the internal architecture correct and fully unit-testable (matching the wrapper pattern's own "land alongside, not wired" staging precedent from the adventure ticket's own migration §7), but the AC's behavioral claims ("An entity with a high-lock current project... keeps its project", "...does switch") are only exercisable via direct test-harness calls (as the existing and rewritten tests already do), not via a live simulation tick — since nothing in `src/` ever calls `accept_contract()` today, and no ticket in this epic's `SEQUENCE.md` wires it in. **Flagging as an open scope question for Plan, not resolved here**: does "done" for this ticket require confirming/documenting this non-liveness explicitly (e.g. in Docs Requiring Update or a code comment, mirroring `AdventureGoalScorer`'s own explicit disclosure of its wiring status), or is unit-test-level correctness alone sufficient per the ticket's literal Scope/AC text (which never mentions wiring)?

5. **Second tie-break value question, not present in the prior ticket**: `GoalKind.ADVENTURE_ROUTE` already claims the `"z_"`-prefixed tie-break-safe range. `SOCIAL_CONTRACT` needs its own value that (a) does not collide with any of the 11 existing `GoalKind` values, and (b) has a *deliberately chosen*, not accidental, ordering relative to `ADVENTURE_ROUTE` specifically (not just the original 10) — e.g. does an accepted social obligation deserve to out-rank routine adventuring on an exact-utility tie, or not? This is a real semantic call, not a mechanical placement.

## Anti-Drift Hazards

- **Do not use `best_candidate.utility` anywhere in the new materialization branch's `score=` argument** — identical, highest-value regression class to the adventure ticket's own Anti-Drift Hazard, doubly important here given the shared-scale finding above (Risk #1) makes an accidental scale mismatch even easier to introduce unnoticed.
- **Do not widen contract-kind coverage beyond `RECRUITMENT`/`LOAN`** (i.e. do not make `PROTECTION`/`MERCHANT`/`POSITION_SWAP` start spawning projects) unless Plan explicitly decides to — the ticket's "delegating to `ContractService`'s existing unchanged internal contract-acceptance logic" wording implies preserving the existing 2-of-5 coverage, not expanding it.
- **Do not touch `src/engine/domain/core_actions.py`'s `execute_recruit`** — it builds contracts as already-`ACTIVE` through a structurally different path (`ResourceTransferIntent.strategic_upd`) that never called `accept_contract()` and never spawned a project; a different, out-of-scope gap.
- **Do not modify `_score_scale_max()`, `_ADVENTURE_ROUTE_SCORE_MAX`, or `_GOAL_UTILITY_SCORE_MAX` without an explicit Plan decision recorded** — Risk #1 above is a real open design fork, not a default-safe edit; changing the shared constant/function affects `ADVENTURE_ROUTE`'s own already-verified calibration too (`test_score_normalization.py`'s existing 5 tests would need re-verification if this constant's meaning changes).
- **Do not assume `SocialContractSystem.transition_contract()`'s status-machine logic (`contracts.py:17-45`, `_is_valid_transition`) needs any change** — it is unrelated to the bypass; only the post-transition project-spawn block (lines 148-190) is in scope.
- **Do not silently drop the resume-suspended-project gap fix (see Current Behavior)** into this ticket's scope — it is an inherited, shared structural gap with `ADVENTURE_ROUTE`, not contract-specific, and fixing it for one kind without the other would be an inconsistent half-fix; leave it for a dedicated follow-on if ever addressed.
