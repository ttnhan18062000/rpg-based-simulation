---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-09-02
---

# Social Systems Contract

**Source:** `src/systems/social_systems/` (appraisal.py, contracts.py, relationships.py, guilds.py, party.py, party_composition.py, memory.py, group_service.py, reputation.py)
**Related docs:** [docs/simulation/domains/cooperation_contract.md](domains/cooperation_contract.md), [docs/simulation/domains/commitment_contract.md](domains/commitment_contract.md), [docs/simulation/domains/domain_ownership_map.md](domains/domain_ownership_map.md)

---

## Purpose

The social systems layer applies social outcomes to entity state. The cooperation and commitment domains make decisions about social posture; this layer implements those decisions as durable state changes — trust updates, bond formation, contract lifecycle, reputation shifts, and party management.

**Caller/callee direction:** The cooperation domain (`src/domains/cooperation/`) produces `ContractState` and `BlockerState`. Social systems receive those outputs and apply them. Social systems do NOT call the domain — the domain calls social systems to execute decisions.

---

## Appraisal — `appraisal.py`

Compliance IDs: SOC-001, SOC-002, SOC-004, SOC-008, STRAT-071, STRAT-073

`SocialAppraisalSystem` evaluates social contracts and offers before accepting or rejecting them.

### Trust evaluation pipeline

1. **Public reputation bias:** `source_entity.social.public_reputation / 2.0` → 0.0–1.0 baseline
2. **Private bond override:** if a SocialBond exists, `trust_score = (bond.sentiment + 1.0) / 2.0` (private sentiment overrides public)
3. **Blended fallback:** `trust_score = public_trust × 0.7 + history_trust × 0.3`
4. **Hard reject gates:** `trust_score < 0.2` → TOTAL_DISTRUST; `betrayal_count > 0 AND trust_score < 0.4` → BETRAYAL_HISTORY

### Contract kinds

| Kind | Special logic |
|---|---|
| RECRUITMENT | Social fatigue check; checks entity's current party commitment; employment cost evaluation |
| LOAN | Simple trust threshold; no counter-terms |
| POSITION_SWAP | Spatial proximity check; validates both parties can reach the target position |
| MERCHANT | `_appraise_trade`: utility = `price / item_value` (hard-cancel to `INSUFFICIENT_INCENTIVE` if `item_value <= 0` or utility `< 0.5`); score = `trust_score × 0.4 + min(1.0, utility) × 0.6`; `>= 0.6` → ACCEPTED (`FAIR_COMPENSATION`); `>= 0.4` and `negotiation_count < 2` → COUNTERED at `price = item_value` (`HAGGLING_FOR_PAY`); else CANCELLED |
| TEAM_UP | `_appraise_team_up`: pure trust gate, no utility/pay dimension — reuses `_appraise_recruitment`'s HIGH-risk/low-HP hard rejection (`FAILED, LOW_HP_RETREAT`); `trust_score >= 0.6` → ACCEPTED (`TEAM_UP_ACCEPTED`), else CANCELLED (`TEAM_UP_DECLINED`); no counter-terms |
| PAID_INFORMATION | `_appraise_paid_information`: always ACCEPTED (`INFORMATION_SALE_ACCEPTED`) once the shared trust/hard-cancel prelude passes — the prelude alone is the entire gate. `PaidInformationTransactionSystem.enforce()` synthesizes a transient (non-persisted) `ContractState(kind=PAID_INFORMATION)` per seeker/provider pair, mirroring `execute_recruit()`'s `temp_contract` pattern, purely to gate whether it emits a `ResourceTransferIntent` — see `docs/engine/authoritative_pipeline.md`'s Economy & Evolution phase |
| TEACH | `_appraise_teach`: always ACCEPTED (`TEACH_ACCEPTED`) once the shared trust/hard-cancel prelude passes — the prelude alone is the entire gate, no utility/risk model. `CoreActions.execute_train()` (`src/engine/domain/core_actions.py`) synthesizes a transient (non-persisted) `ContractState(kind=TEACH)` per teacher/student pair (`entity` = teacher, `target` = student), mirroring `execute_recruit()`'s `temp_contract` pattern — the **target (student) appraises the entity (teacher)**, same direction as RECRUITMENT/TEAM_UP/TRADE. On ACCEPTED, `IdentityUpdate(recipes_learned=[skill_id])` is set directly on the student's `EntityUpdate` (mirroring `execute_allocate_ap`'s direct-assignment pattern), not nested in a `ResourceTransferIntent`. No gold cost is charged — trust replaces the previously-present, never-enforced 50-gold `TRAIN_COST` entirely; see `docs/guidelines/intentional_divergences.md` DEV-007. `ContractService.get_project_mapping()` returns `None` for TEACH (not widened) — no tier-5 project is ever materialized from a teach offer. |
| MARRIAGE | `_appraise_marriage`: always ACCEPTED (`MARRIAGE_ACCEPTED`) once the shared trust/hard-cancel prelude passes — the prelude alone is the entire gate, no utility/risk model, no `eligibility_gate` field. `CoreActions.execute_propose_marriage()` (`src/engine/domain/core_actions.py`) synthesizes a transient (non-persisted) `ContractState(kind=MARRIAGE)` per proposer/target pair, mirroring `execute_train()`'s `temp_contract` pattern — the **target appraises the proposer**, same direction as RECRUITMENT/TEAM_UP/TRADE/TEACH. On ACCEPTED, a new typed durable `MarriageState` record (`src/core/strategic.py`; own `MarriageStatus` enum, distinct from `ContractStatus`) is written via `StrategicUpdate.marriages_add_or_update` on **both** parties' `EntityUpdate`, through the same authoritative `Patch.apply()` path `StrategicComponent.contracts` already uses. `ContractService.get_project_mapping()` returns `None` for MARRIAGE (not widened) — no tier-5 project is ever materialized. Bigamy prevention, household/family state, and aging/duration thresholds are deliberately out of scope — see `docs/mechanics/04_strategic_cognition.md` Sec 8. |

All three added kinds route through the same shared trust/hard-cancel prelude above (steps 1–4)
before kind dispatch — no behavior change to that prelude. `CoreActions.execute_team_up()` and
`execute_trade()` (`src/engine/domain/core_actions.py`) mirror `execute_recruit()`'s
temp-contract-then-appraise-then-branch shape; on ACCEPTED, both attach the resulting
`ContractState` via `EntityUpdate.strategic` with **no `ResourceTransferIntent`** — no gold changes
hands on TEAM_UP formation, and MERCHANT/Trade's `price` is recorded in the contract's `terms` but
not itself resolved as a transfer by these handlers. `TEAM_UP` is a distinct mechanism from
`party.py`'s COOPERATION/RECRUITMENT-only party-assembly condition (see Party section below) — an
ACTIVE `TEAM_UP` contract does not itself trigger `PartyRecord` formation. `ContractKind.MERCHANT`
was previously declared but unhandled (fell through to `CANCELLED, UNKNOWN`); it is now live via
`_appraise_trade`. Affection/liking continues to be represented entirely by the existing
`SocialBond.sentiment` field (see Relationships section) — no new field was added for any of the
three new kinds.

### Re-appraisal triggers

Re-appraisal occurs on: new contract offer received, betrayal event witnessed, entity's public_reputation changes significantly (±0.3), party dissolution.

---

## Relationships — `relationships.py`

Compliance IDs: SOC-193–SOC-196, SOC-217

`RelationshipService.process_update()` applies `SocialUpdate` deltas to `SocialComponent` fields.

### Relationship dimensions (all clamped per-field)

| Field | Range | What it tracks |
|---|---|---|
| trust_history | −1.0 to 1.0 | Per-entity trust accumulation |
| familiarity_history | 0.0 to 1.0 | Interaction frequency |
| debt_history | −1.0 to 1.0 | Social obligation balance |
| fear_history | 0.0 to 1.0 | Fear from combat/intimidation |
| grudge_history | 0.0 to 5.0 | Accumulated harm (5.0 cap) |
| salience_history | 0.0 to 1.0 | How "top of mind" an entity is |

### Social bonds

`SocialBond` is a richer directional relationship: `familiarity`, `sentiment` (−1.0 to 1.0), `last_interaction_tick`, `role` (`RelationshipRole`: `NEUTRAL` default / `FRIEND` / `RIVAL`, SOC-247). Bonds are formed for entities with high familiarity or strong sentiment. Bond sentiment takes priority over trust_history in appraisal. `role` is settable only through the authoritative `SocialBondUpdate.role_set` → `RelationshipService.process_update()` path, and `RIVAL` is independent of `nemesis_ids`/`grudge_history`-driven nemesis promotion below.

### Decay

Social history fields decay passively over time when there are no new interactions. Rate is configurable per-field in the social config.

---

## Social Memory — `memory.py`

`SocialMemoryService` handles two persistent social memory types:

**Place attachment:** Increments 0.001 per tick while entity is in a region. Long-term presence creates "home" attachment (`SocialUpdate(place_attachment_delta={region_id: 0.001})`).

**Nemesis promotion:** When `grudge_history[entity_id] >= 3.0`, the entity is promoted to `nemesis_ids`. Threshold: 3 kills or equivalent repeated harm. Nemesis relationship affects routing (the adventure domain avoids nemesis regions) and cooperation (never cooperates with a nemesis).

**Distinction from other memory types:**
- Social memory (this layer): place attachment + nemesis tracking
- Domain memory (`src/domains/memory/`): causal/spatial/temporal memory updated per tick
- Cognition knowledge model (`src/cognition/knowledge_model.py`): factual world knowledge with freshness

---

## Contracts — `contracts.py`

Social contracts are durable `ContractState` records. Each contract has: `kind`, `source_id`, `target_id`, `terms`, `status` (OFFERED/ACCEPTED/COUNTERED/CANCELLED/FULFILLED/BREACHED), `deadline_tick`.

### Breach conditions

| Contract kind | Breach triggers |
|---|---|
| RECRUITMENT | Source entity abandons party; party trust drops below threshold |
| ESCORT | Source entity dies before reaching destination |
| LOAN | Target entity fails to return gold by deadline_tick |
| POSITION_SWAP | Either party cannot reach the target position within agreed ticks |

Breach records `betrayal_count += 1` on the breaching entity and triggers reputation update via `ReputationUpdateService`.

---

## Guilds — `guilds.py`

Guild membership stores a `GuildMembership` record on the entity. Benefits and obligations:
- Members gain access to guild-affiliated service opportunities (guild halls, job boards)
- Members pay guild dues (ResourceTransferIntent at guild taxation cadence)
- Guild rank affects appraisal: higher-rank entities receive better contract terms from guild affiliates
- Routing: entities prefer regions where their guild has presence (guild presence is a positive route bias factor)

---

## Party — `party.py`

Party state is stored as a `PartyRecord` on a designated party leader entity. Assembly conditions:
- Requires a COOPERATION or RECRUITMENT contract between at least 2 entities
- Party forms when contract status transitions to ACCEPTED

Dissolution rules:
- Leader death → party dissolved; trust decreases by 0.25 for all members (cooperation domain handles this)
- All members reach destination → party fulfills and dissolves
- Explicit LEAVE action by any member → voluntary quit (commitment penalty applies)

Shared goal mechanics: party members share objective visibility. When the leader sets a project, members receive a `force_route_reevaluation` flag pointing them toward the same region.

---

## Party Composition — `party_composition.py`

Compliance ID: SOC-244 (trust/bonds-aware term only; the pre-existing role-diversity/OCEAN-compatibility
base score has no dedicated compliance id — see `docs/parity_ledger/social_narrative.yaml`'s SOC-244
divergence_note for the pre-existing SOC-231/SOC-232 docstring mis-citation, not fixed here)

`PartyCompositionScorer.score(entities, actor=None)` scores a candidate pool's party-formation
quality, 0.0–1.0: `0.6 × role_diversity + 0.4 × OCEAN_compatibility` (TANK/HEALER/DPS/SUPPORT role
coverage; bravery/sociability variance). When `actor` (the entity forming the party) is supplied,
an additional `0.15 ×` mean directed trust/bond term is added, plus a `0.10 ×` mean directed
`RelationshipRole` affinity term (`FRIEND` → +1.0, `RIVAL` → −1.0, `NEUTRAL`/no bond → 0.0, SOC-247),
and the result clamped to `[0.0, 1.0]` — see `docs/mechanics/04_strategic_cognition.md` §7. Bond
sentiment takes priority over `trust_history` when both exist for a candidate, matching the
Relationships section's rule above. Used by `AdventureRouteGenerator`'s FORM_PARTY route
(`src/domains/adventure/`) and by `GroupSystem`'s ally-cohesion group formation
(`src/systems/world_systems/groups.py`, which never passes `actor` and is unaffected by the
trust/bonds or role-affinity terms).

---

## Reputation — `reputation.py`

`ReputationUpdateService.process_witnessed_event()` updates `PublicReputationProfile.labels` for witnessed events:

| Event | Effect |
|---|---|
| escort completed | reputation +0.1; RELIABLE label added |
| betrayal witnessed | reputation −0.2; BETRAYER label added |
| camp cleared | reputation +0.05; COMBATANT label added |

Public reputation (0.0–1.0) is visible to all entities and used in trust appraisal.

---

## Engine phase

Social system updates run as part of the authoritative apply pipeline. There is no dedicated social phase — social updates are triggered by events (contract offers, betrayal events, death events) and processed within the relevant pipeline phase. `RelationshipService.process_update()` is called wherever a `SocialUpdate` is produced.

---

## Mutation rules

All social state changes go through `SocialUpdate` → `RelationshipService.process_update()` → authoritative apply. Direct mutation of `SocialComponent` fields outside this path is prohibited (SOC-217).

---

## Regression tests

- `tests/unit/social/test_groups.py` — trust pipeline, hard reject gates, bond formation
- `tests/unit/social/test_party_agency.py` — delta application, clamping, place attachment
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` — full contract lifecycle: offer → appraisal → accept/breach

---

## Extension rules

1. To add a new contract kind: add to `ContractKind` enum, implement an appraisal method in `SocialAppraisalSystem`, add breach conditions in `contracts.py`, add tests.
2. To add a new relationship dimension: extend `SocialComponent` and `SocialUpdate`, add clamping in `RelationshipService.process_update()`. Update consumers that read the new dimension.
3. To add a new guild benefit: extend `guilds.py` and update the service opportunity filtering in `providers/services.py`. Guild benefits must be readable by the adventure domain without importing social systems directly.
4. Never read social state in a domain service — domain services produce ContractState/SocialUpdate outputs; social systems apply them. Cross-imports between domains and social systems violate the architecture boundary.
