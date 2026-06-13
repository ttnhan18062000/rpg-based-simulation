---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Cooperation Domain Contract

**Source:** `src/domains/cooperation/` (phase.py, contract_service.py, group_evaluator.py, partner_scoring.py, posture.py)  
**Pipeline phase:** Phase 7 — CooperationPhase  
**Authoritative status:** Cooperative posture decision domain — selects help-seeking posture and cooperation contracts. Does not execute resource transfers or social contracts directly.

---

## Purpose

The cooperation domain implements **cooperative posture selection** for entities each tick. It detects conditions under which an entity needs assistance, identifies eligible partner candidates in spatial range, scores their fit using a weighted formula, and selects the appropriate cooperative posture. The selected posture produces typed intent outputs (ContractState, ResourceTransferIntent, StrategicUpdate, or BlockerState) consumed by downstream social and economic systems. The domain does not own entity identity, inventory, or world state.

---

## Engine Phase

**Phase 7 — `CooperationPhase.execute(state, context)`**

Runs every tick for all entities that have an active cooperation evaluation trigger. There is no hard entity filter by role — the phase evaluates all living, active entities.

---

## What It Owns

- The entity's **cooperative posture decision**: which of the 12 posture options the entity adopts this tick
- **Help-need trigger detection**: whether any of the 4 recognized conditions are active for the entity
- **Partner candidate selection**: which entities in spatial range are eligible cooperation candidates
- **Party cohesion evaluation**: ongoing assessment of active groups and trust decay on abandonment or leader loss

The cooperation domain does not own entity identity, strategic project content, inventory balances, or world state.

---

## What It Reads

From the entity under evaluation:

| Field | Purpose |
|---|---|
| `entity.position` | Spatial anchor for partner candidate radius search |
| `entity.combat.hp` / `entity.combat.combat_risk` | Near-death and combat-risk trigger conditions |
| `entity.timeline` | Recent events used for help-need detection |
| `entity.gold` | Gold-surplus trigger detection (`> 1000`) |
| `entity.cognition.spatial_memory` | Unknown-region detection (no spatial memory for current region) |

From other entities in spatial range (radius = 15.0, max 5 candidates):

| Field | Purpose |
|---|---|
| `other.position` | Spatial distance check |
| `other.capability` | Partner scoring — capability dimension |
| `other.identity.faction` | Partner scoring — alignment dimension |
| `other.trust` (relationship score) | Partner scoring — trust dimension |
| `other.combat_risk` | Partner scoring — risk dimension |

From domain outputs read as inputs:

| Source | Field | Purpose |
|---|---|---|
| Commitment domain | Commitment pressure | Gates help-request eligibility — entities under high commitment pressure are excluded from REQUEST_HELP posture |
| Emotion domain | Fear level | Adjusts near-death trigger threshold — high fear lowers the HP threshold for help-need detection |
| Motivation domain | `cooperation_bias` from entity doctrine | Modulates posture scoring — doctrine-flagged cooperative entities favour COOPERATE over DEFER |

---

## Help-Need Trigger Detection

Four conditions are evaluated each tick. Any single condition that resolves to True marks the entity as needing assistance and initiates partner candidate search:

| Trigger | Condition |
|---|---|
| `combat_risk` | Entity's `combat_risk` flag is True (entity is engaged in a dangerous combat encounter) |
| `near_death` | Entity HP falls below the critical threshold (exact value is entity-class-dependent; adjusted by fear level from emotion domain) |
| `unknown_region` | Entity is in a region with no entry in `entity.cognition.spatial_memory` (unexplored territory) |
| `gold_surplus` | `entity.gold > 1000` (potential hire trigger — entity can afford to hire support) |

If no trigger is active, the entity skips posture selection entirely and no intent is emitted.

---

## Partner Scoring Formula

When a trigger is detected, up to 5 candidates within radius 15.0 are gathered and scored:

```
partner_score = trust × 0.35 + capability × 0.3 + alignment × 0.2 + (1 − risk) × 0.15
```

| Term | Source | Weight |
|---|---|---|
| `trust` | Relationship trust score between entity and candidate (0.0–1.0) | 0.35 |
| `capability` | Candidate's combat/skill capability rating (0.0–1.0) | 0.30 |
| `alignment` | Faction alignment compatibility (0.0–1.0) | 0.20 |
| `(1 − risk)` | Inverse of candidate's current combat risk (0.0–1.0) | 0.15 |

Weights sum to 1.0. If adjusting weights, all four must be adjusted proportionally so the sum remains 1.0.

The highest-scoring candidate above any minimum eligibility threshold is selected as the cooperation partner. If no candidate meets the threshold, posture selection falls back to DEFER_NO_PARTNER.

---

## Posture Selection

The domain selects one posture from an enum of 12 options. The four primary postures with documented output semantics are:

| Posture | Trigger context | Output produced |
|---|---|---|
| `DEFER_NO_PARTNER` | Help-need trigger active but no eligible partner found | `BlockerState` — records that cooperation was blocked and logs the reason |
| `REQUEST_HELP` | Partner found; entity is in combat-risk or near-death; commitment pressure allows | `ContractState` via `ContractService` |
| `HIRE_SUPPORT` | Partner found; `gold_surplus` trigger active; entity has sufficient gold | `ResourceTransferIntent` (gold transfer amount) + `ContractState` |
| `COOPERATE` | Partner found; `unknown_region` trigger active or doctrine cooperation_bias is high | `StrategicUpdate` aligning entity's active project with partner's active project |

The remaining 8 postures handle graduated cooperation responses (e.g., partial support, observe-only, standby, follow). Their output semantics follow the same pattern: typed intent emitted, never direct mutation.

---

## Party Cohesion Evaluation

`GroupEvaluator` runs as a secondary pass within `CooperationPhase.execute()`, evaluating all active groups in the world state:

- If a group's leader entity is no longer active (dead, departed, or unreachable): trust for all remaining group members decreases by 0.25 for that group's trust record.
- If an entity abandonment event appears in the group's recent event log: trust decreases by 0.25.
- Trust decay is applied to the group's cohesion record, not to individual entity bilateral trust scores.

---

## What It May Mutate (Via Intent)

All primary mutations are emitted as typed intents — never applied directly inside `CooperationPhase`.

| Output type | Fields written | Notes |
|---|---|---|
| `ContractState` | cooperation contract record (parties, terms, duration) | Consumed by social systems layer |
| `ResourceTransferIntent` | gold transfer amount (source entity, target entity, amount) | Consumed by economic resolution |
| `StrategicUpdate` | `current_project_id_set` aligned to partner's project | Consumed by strategy system |
| `BlockerState` | blocker reason, blocking entity or condition | Consumed by adventure domain for route re-evaluation |
| `entity.timeline` | Direct `entity.timeline.append()` call | Known direct-write pattern — see architecture note below |

### Architecture Note: entity.timeline Direct Write

`entity.timeline.append()` is called directly inside `CooperationPhase.execute()`. This is a known and accepted pattern in the codebase — the timeline is a bounded, append-only log used for diagnostic and causal attribution purposes. It is not a primary durable state field. This direct write is **not** the recommended extension pattern; new cooperation side-effects should be expressed as typed intents. Do not model new durable state by extending this pattern to other entity fields.

---

## What It Must NOT Mutate

- Entity identity fields (`entity.identity.*`)
- Entity inventory or gold balance (use `ResourceTransferIntent` — the economic system applies it)
- World state: regions, resource nodes, ecology records
- Other entities' strategic projects or objective assignments (the `StrategicUpdate` for COOPERATE aligns the requesting entity to the partner's project — it does not rewrite the partner's project)
- Entity combat state (`alive`, HP, durability)

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Commitment domain** | Cooperation reads commitment pressure as an eligibility gate. High commitment pressure blocks REQUEST_HELP posture — the entity is already locked into obligations. |
| **Emotion domain** | Fear level from the emotion domain adjusts the near-death trigger threshold. A frightened entity will detect near-death at a higher HP value than a calm entity. |
| **Motivation domain** | `cooperation_bias` from entity doctrine modulates posture scoring. Doctrine-flagged cooperative entities weight COOPERATE higher than DEFER when a partner is available. |
| **Social systems layer** | `ContractState` output is consumed by the social systems layer to register the active cooperation agreement and update bilateral trust over time. |
| **Adventure domain** | `BlockerState` from DEFER_NO_PARTNER is read by the adventure domain on the next tick to inject a blocker penalty on FORM_PARTY routes, preventing repeated fruitless cooperation attempts. Cooperative commitments that produce project locks (`lock_until_tick`) are respected by AdventureDecisionPhase. |
| **Economic system** | `ResourceTransferIntent` from HIRE_SUPPORT is applied by the economic resolution system — gold is not deducted inside this domain. |

---

## Test Protection

Primary test targets:

```
grep -r "CooperationPhase\|partner_scoring\|ContractService\|BlockerState\|GroupEvaluator" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| No trigger active → no posture selected, no intent emitted | Yes |
| Trigger active, no eligible candidates → DEFER_NO_PARTNER + BlockerState | Yes |
| Partner scoring formula: trust × 0.35 + capability × 0.3 + alignment × 0.2 + (1 − risk) × 0.15 | Yes |
| REQUEST_HELP → ContractState produced via ContractService | Yes |
| HIRE_SUPPORT → ResourceTransferIntent + ContractState both emitted | Yes |
| COOPERATE → StrategicUpdate aligns entity to partner project | Yes |
| Commitment pressure gate: high pressure blocks REQUEST_HELP | Yes |
| Trust decay: 0.25 reduction on leader loss or abandonment event | Yes |
| gold_surplus trigger: entity.gold exactly 1000 does NOT trigger; > 1000 does | Recommended |
| entity.timeline append does not corrupt other state | Recommended |

---

## Extension Rules

**Adding a new posture:**
1. Add the value to the posture enum in `src/domains/cooperation/postures.py`.
2. Add a case in `CooperationPhase.execute()` that maps the new posture to a typed intent output.
3. Define clearly what trigger conditions activate the new posture and at what priority relative to existing postures.
4. Add tests: trigger detection, intent output type, downstream consumption.

**Adding a new help-need trigger:**
1. Add the detection condition in the trigger-detection pass of `CooperationPhase.execute()`.
2. Wire the new trigger to a posture outcome — specify which posture or postures the new trigger can activate.
3. If the trigger interacts with another domain's outputs (e.g., emotion, commitment), declare the read dependency explicitly.
4. Add tests: trigger fires when expected, does not fire below threshold.

**Adjusting partner scoring weights:**
All four weights (trust 0.35, capability 0.3, alignment 0.2, risk 0.15) must sum to 1.0. Adjust proportionally. Do not add new scoring terms without removing or reducing existing weights to maintain the sum invariant.

**Adding new durable side-effects:**
Use typed intents — do not extend the `entity.timeline.append()` direct-write pattern to new entity fields.
