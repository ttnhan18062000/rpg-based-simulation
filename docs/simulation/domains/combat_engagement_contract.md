---
status: authoritative
layer: ai
authority: P1
audience: agent
last_verified: 2026-06-12
tags: [domains, combat, engagement, contract]
---

# Combat Engagement Domain Contract

**Source:** `src/domains/combat_engagement/` (10 files)  
**Pipeline phase:** Phase 4 — Pre-Combat Assessment  
**Authoritative status:** NOT authoritative — reads state, returns typed decision record.

---

## Purpose

The combat engagement domain produces a **subjective pre-combat assessment** for an actor encountering a potential target. It determines what `CombatPosture` the actor should adopt before any combat resolution occurs. It does not resolve combat outcomes — that is the combat system's responsibility.

---

## CombatPosture Enum

Ten posture values in escalating engagement level:

| Posture | Meaning |
|---|---|
| `IGNORE` | Target is beneath notice |
| `WATCH` | Observe without acting |
| `AVOID` | Actively route around target |
| `PROBE` | Test target without full engagement |
| `THREATEN` | Assert dominance / warn off |
| `ENGAGE` | Commit to combat |
| `SKIRMISH` | Hit-and-run tactics |
| `CALL_HELP` | Seek reinforcement before engaging |
| `RETREAT` | Disengage from ongoing encounter |
| `PANIC_FLEE` | Uncontrolled flight |

---

## Service Contract

**Entry point:** `CombatEngagementDecisionService.evaluate(actor, target, state)`

```
Input:
  actor: EntityState      — the entity making the assessment
  target: EntityState     — the entity being assessed
  state: AuthoritativeState — read-only world state

Output:
  CombatEngagementDecisionResult — typed, frozen; contains chosen CombatPosture and OpponentModel
```

`evaluate()` is **stateless and deterministic** — same inputs produce the same output.

---

## Sub-Service Pipeline

`CombatEngagementDecisionService.evaluate()` orchestrates four sub-services in order:

1. **OpponentPerceptionService** — builds `OpponentModel` from target's observable properties
2. **SelfCombatEstimateService** — estimates actor's own combat capability
3. **EngagementRiskEvaluator** — computes risk ratio from OpponentModel vs. self-estimate
4. **CombatPostureSelector** — selects `CombatPosture` from risk ratio and actor personality

None of these sub-services mutate state. Each receives `EntityState` or derived records and returns a typed result.

---

## Authoritative Pipeline Integration

Phase 4 of the authoritative pipeline calls combat engagement assessment for entities that encounter other entities. The output `CombatPosture` is passed to downstream phases for tactical goal selection. The domain does not write back to `AuthoritativeState` — the pipeline applies the posture.

---

## Reassessment and Learning

- **reassessment.py** — re-evaluates posture mid-encounter when conditions change (e.g. health drops, reinforcements arrive). Same stateless contract as initial evaluation.
- **learning.py** — produces updated reputation/learning records after encounter resolution. These records are passed to the pipeline for application — not applied directly.

---

## Constraints

- Must not import from other domain packages.
- Must not call the Kernel or other pipeline phases directly.
- `OpponentModel` and `CombatEngagementDecisionResult` are frozen dataclasses — never mutate after construction.
