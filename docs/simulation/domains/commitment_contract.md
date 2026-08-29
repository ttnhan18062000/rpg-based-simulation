---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-08-29
---

# Commitment Domain Contract

**Source:** `src/domains/commitment/` (pressure.py, abandonment.py, impact.py, reputation.py)  
**Pipeline phase:** no dedicated stage — runs inline as scoring utilities called by the Cooperation stage and the strategy system  
**Authoritative status:** Scoring utility domain. Computes pressure and bias values consumed by callers. `ReputationUpdateService` is the one path that produces a durable state change (`PublicReputationProfile`), returned as a new immutable instance.

---

## Purpose

The commitment domain computes **commitment pressure**, **abandonment classification**, **route and partner scoring biases**, and **public reputation updates**. It does not schedule actions or own strategic goals. It is a constraint and scoring layer: other domains call into it to get commitment-aware pressure values, route biases, and abandonment verdicts.

Commitment pressure gates whether an entity can abandon a cooperative obligation and at what reputational cost. Route bias ensures committed entities preferentially score routes that serve their active commitments.

---

## What It Owns

- Commitment pressure computation (`CommitmentPressureService`)
- Abandonment classification and reputation penalty assignment (`AbandonmentEvaluator`)
- Route score boosting from active commitments; partner fit penalty from reputation (`CommitmentReputationRouteImpact`)
- Public reputation label updates from witnessed events (`ReputationUpdateService`)

The domain does **not** own the commitment entries themselves (those live on `entity.cognition.commitment`), nor does it own strategic projects or party state.

---

## Engine Pipeline Phase

**Inline utility — no dedicated stage runner**

There is no `phase.py`. The four services are called inline by:

- **Cooperation phase** — calls `CommitmentPressureService.compute_pressure()` to gate help-request eligibility; calls `CommitmentReputationRouteImpact.apply_partner_fit_bias()` when scoring party candidates.
- **Adventure domain** — calls `CommitmentReputationRouteImpact.apply_route_bias()` during route scoring; calls `AbandonmentEvaluator.evaluate_abandonment()` when a route-exit event occurs.
- **`QuestResolutionSystem.enforce()`** (`src/engine/quests.py`, `quest_rewards` pipeline phase) — calls `ReputationUpdateService.process_witnessed_event()` with `event_kind="successful_escort"` when a `QuestKind.ESCORT` quest transitions ACTIVE→COMPLETED. `betrayal` and `clear_camp` remain unwired — no live production event source calls `process_witnessed_event()` with those event kinds today.

---

## Service Contracts

### CommitmentPressureService.compute_pressure(entry, current_tick, hp_ratio) → float

Returns a commitment pressure value in [0.0, 1.0] for a single `CommitmentEntry`.

```
pressure = entry.strength

if deadline_tick is not None:
    ticks_left = deadline_tick − current_tick
    if ticks_left <= 0:  pressure = 0.0    # expired
    elif ticks_left < 20: pressure += (20 − ticks_left) × 0.02   # urgency ramp

if hp_ratio < 0.2:
    pressure × = 0.1    # survival overrides commitment
```

- `entry.strength` is the base commitment weight (caller-set, typically 0.0–1.0).
- Deadline urgency adds up to +0.4 over the final 20 ticks before expiry.
- HP survival threshold (< 20%) reduces pressure by 90%, letting survival override obligation.
- Expired commitments (ticks_left ≤ 0) return 0.0 — caller should treat them as resolved.
- Result is clamped to [0.0, 1.0].

### AbandonmentEvaluator.evaluate_abandonment(hp, max_hp, is_party_in_combat, is_greed_driven) → dict

Classifies an abandonment event into one of three types and assigns a reputation penalty:

| Type | Conditions | is_betrayal | penalty |
|---|---|---|---|
| `survival` | `hp_ratio < 0.2` | False | 0.0 |
| `greedy_desertion` | party in combat AND `is_greed_driven` | True | 0.8 |
| `voluntary_quit` | all other cases | False | 0.2 |

- `hp_ratio = hp / max(1, max_hp)`.
- Survival abandonment produces **no reputation consequence** — it is classified as a valid biological response.
- Greedy desertion produces the maximum betrayal penalty (0.8) and sets `is_betrayal: True` — callers must route this through `ReputationUpdateService` with `event_kind="betrayal"`.
- The returned dict has keys: `is_betrayal` (bool), `penalty` (float), `reason` (str).

### CommitmentReputationRouteImpact

Two static methods for route and partner scoring:

**apply_route_bias(entity, tags, base_score) → float**

For each active `CommitmentEntry` in `entity.cognition.commitment.active_commitments`:

```
if entry.kind in tags OR str(entry.target_id) in tags:
    score += entry.strength × 0.5
```

Boosts route scores that match an active commitment's kind or target. Encourages commitment-aligned route selection without hard-gating alternatives.

**apply_partner_fit_bias(entity, candidate_reputation, base_fit) → float**

Adjusts a party candidate fit score based on their public reputation labels:

```
if "betrayer" in candidate_reputation:
    score −= candidate_reputation["betrayer"] × 2.0

if "reliable" in candidate_reputation:
    score += candidate_reputation["reliable"] × 0.2

return max(0.0, score)
```

Betrayal reputation carries a 2× weight penalty — known betrayers are strongly filtered from party formation. The result is clamped to a minimum of 0.0.

### ReputationUpdateService.process_witnessed_event(profile, event_kind) → PublicReputationProfile

Updates `PublicReputationProfile.labels` for a witnessed social event. Labels are floats in [0.0, 1.0].

| event_kind | Label changes |
|---|---|
| `successful_escort` | `reliable` +0.1 (capped at 1.0) |
| `betrayal` | `betrayer` +0.4 (capped at 1.0); `reliable` −0.3 (floored at 0.0) |
| `clear_camp` | `camp_clearer` +0.2; `heroic` +0.1 |

Returns a new `PublicReputationProfile` via `dataclasses.replace`. The input profile is never mutated. Unrecognised event kinds leave the profile unchanged.

---

## What It Reads

| Source | Field |
|---|---|
| Commitment state | `entity.cognition.commitment.active_commitments` (CommitmentEntry dict) |
| Commitment entry | `entry.strength`, `entry.deadline_tick`, `entry.kind`, `entry.target_id` |
| Entity vitals | `hp`, `max_hp` (or `hp_ratio`) for survival threshold |
| Combat context | `is_party_in_combat`, `is_greed_driven` (passed in by caller) |
| Entity reputation | `PublicReputationProfile.labels` |
| Candidate reputation | `candidate_reputation` dict (passed in by caller — sourced from partner's `PublicReputationProfile`) |

---

## What It Decides

- Whether commitment pressure is high enough to gate abandonment (caller interprets the returned float)
- How to classify an abandonment event and what reputation penalty to assign
- How much to boost a route score based on active commitment alignment
- How much to penalize or reward a party candidate based on reputation labels
- How to update a `PublicReputationProfile` for a witnessed social event

---

## What It May Mutate

`PublicReputationProfile.labels` — via `ReputationUpdateService.process_witnessed_event()`, which returns a new immutable instance. The caller is responsible for writing the updated profile back into the entity's cognition state.

All other services return computed scalars or classification dicts — they produce no durable state.

**Mutation path note:** `ReputationUpdateService` returns a new `PublicReputationProfile` directly (not via `EntityUpdate`). At the one live integration point (`QuestResolutionSystem.enforce()`, `src/engine/quests.py`, `successful_escort`), the caller routes the returned profile through the authoritative pipeline: it stages the updated `CognitionModel` via `EntityUpdate.cognition_bundle_set`, reading `entity_update.cognition_bundle_set` as the merge base (falling back to `entity.cognition` only if unset) rather than `entity.cognition` directly — the same merge-safe pattern `NearDeathHardeningPhase.apply()` uses (`src/engine/pipeline_phases/hardening.py:91-99`) — so it does not clobber `MemoryUpdatePhase`'s same-tick cognition writes. This is the one durable-state-adjacent output of the domain and should be treated with the same care as other cognition state replacements; any future caller wiring `betrayal`/`clear_camp` must follow the same pattern.

---

## What It Must NOT Mutate

| Target | Reason |
|---|---|
| `entity.cognition.commitment.active_commitments` | Commitment entries are owned by the commitment state, not modified by scoring utilities |
| Entity identity, class, attributes | Outside commitment scope |
| Inventory, gold, equipment | No economic ownership |
| Strategic projects | Commitment is a constraint on projects, not an owner |
| Other entities' state | Each entity's commitment pressure is computed independently |
| World state | The domain is entirely internal to entity cognition and social layer |

---

## Domain Interactions

| Domain / System | Direction | Detail |
|---|---|---|
| **Cooperation domain** | Calls into commitment | Commitment pressure gates help-request eligibility; partner fit bias applies during party candidate scoring |
| **Adventure domain** | Calls into commitment | Route bias from active commitments applied during route scoring; abandonment evaluator called on route-exit events |
| **Emotion domain** (event-driven, see emotion_contract.md) | Reads emotion outputs | Near-death emotion state (high fear/panic) contextually informs survival abandonment; `hp_ratio` is the formal signal, not direct emotion field reads |
| **`QuestResolutionSystem.enforce()`** (`src/engine/quests.py`) | Calls into commitment | `ReputationUpdateService.process_witnessed_event()` called with `event_kind="successful_escort"` when a `QuestKind.ESCORT` quest transitions ACTIVE→COMPLETED; `betrayal`/`clear_camp` remain unwired |

---

## Test Protection

| Test file | What it covers |
|---|---|
| `tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py` | All three abandonment types; hp boundary (< 0.2); greedy_desertion conditions; penalty values |
| `tests/unit/domains/commitment/test_phase15_reputation_update.py` | Label deltas per event_kind; clamping to [0.0, 1.0]; unrecognised event no-op; immutability |
| `tests/unit/domains/commitment/test_phase15_route_impact.py` | Route bias boost formula; partner fit penalty with betrayer/reliable labels; max(0.0) floor |
| `tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py` | Scenario-level: greedy desertion cascade → betrayal reputation → partner fit penalty; survival abandonment with no penalty; `QuestKind.ESCORT` completion → `successful_escort` reputation update via `QuestResolutionSystem.enforce()`; regression guard that this write preserves `MemoryUpdatePhase`'s same-tick `cognition_bundle_set` staging |
| `tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py` | End-to-end: commitment pressure gating cooperation decisions in full cognition hierarchy |

---

## Extension Rules

- **New abandonment type:** Add a classification branch in `AbandonmentEvaluator.evaluate_abandonment()`; assign an `is_betrayal` flag and a `penalty` float; add a corresponding delta rule in `ReputationUpdateService.process_witnessed_event()` if the new type should produce a reputation event; update tests for the new branch.
- **New commitment kind:** Extend the commitment state schema with the new kind string; `CommitmentReputationRouteImpact.apply_route_bias()` matches on `entry.kind in tags` dynamically — no code change needed in the impact service if the kind string is added to the route tag set.
- **New reputation label:** Add delta logic in `ReputationUpdateService.process_witnessed_event()` for the new `event_kind`; add a read branch in `apply_partner_fit_bias()` if the new label should affect partner scoring; document the weight rationale.
- **Pressure formula change:** Any change to `CommitmentPressureService.compute_pressure()` (new urgency ramp, different survival threshold) must update the formula documentation in this contract and add a regression test for the boundary condition.
- **No direct state mutation:** All services return new immutable instances or computed scalars. Do not add any service that mutates entity state in-place — route all durable changes through the caller-controlled replace pattern.
