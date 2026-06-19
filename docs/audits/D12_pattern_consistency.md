---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, patterns, consistency, typed-updates, determinism, domain-phases, architecture]
---

# D12 — Pattern Consistency

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | B — Codebase / Architecture |
| **State** | `done` |
| **Impact** | 3 / 5 |
| **Interest** | 3 / 5 |
| **Priority** | 6 |
| **Method** | code-read |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Are the established V2 architecture patterns applied
uniformly across all domains, or are there pockets of inconsistency that create
maintenance traps?

**Related dimensions:** D10 (Test Coverage) — F3 bare random usage is the most serious
determinism pattern violation; D14 (Coupling Depth) — pattern violations often coincide
with coupling violations; D17 (Documentation Currency) — `design_patterns.md` describes
V1 patterns, creating a guidance gap.

---

## Review Method

Seven pattern categories are checked by automated scan and manual review. Each finding
is scored on three dimensions to produce a Pattern Enforcement Priority. Higher score =
higher priority to standardize.

### Pattern Enforcement Priority Scoring

3 dimensions, each 1–5. Maximum: 15.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Adoption Gap** | Violation is isolated (1–2 sites) | Several sites; inconsistent adoption | Pattern widely violated or guidance document wrong |
| **Risk if Violated** | Cosmetic inconsistency | Caller must check fragile dict keys or strings | Breaks determinism, replay, or type-checking across the codebase |
| **Detection Ease** | Visible in IDE immediately | Requires running a scanner | Only detected in production by comparing replay outputs |

---

## Pattern Inventory

The authoritative pattern reference is `docs/engine/architecture_reference.md`.
Key established patterns:

1. **Typed records** — every durable concept must be a typed dataclass/Pydantic model, not a dict or `reason` string
2. **Decision/mutation separation** — domains read state and return typed updates; only the authoritative pipeline applies mutations
3. **Deterministic ordering** — all entity/candidate sorting must use a stable tiebreaker (entity ID) to ensure replay reproducibility
4. **Domain Phase class** — domain logic lives in a `XPhase` class with an `execute()` method and typed return
5. **Presenter layer** — API shapes are produced by presenters/DTOs, not inline dict construction in route handlers
6. **`reason` as explanation only** — `reason` fields carry prose for debugging; categorical decisions must be enums or typed fields

---

## Key Findings

### F1 — Unstable sorts on simulation path — Priority: 10 / 15

| Dimension | Score | Reason |
|---|---|---|
| Adoption Gap | 3 | 8 sites in non-test code; 3 on potential simulation paths |
| Risk if Violated | 4 | Score ties produce non-deterministic ordering — breaks replay; D10 F3 already detected a determinism breach |
| Detection Ease | 3 | Only visible when comparing replays of the same seed; tests rarely check ordering stability |
| **Total** | **10** | |

8 `sorted()` calls in non-test production code use a single criterion with no `entity_id`
or stable tiebreaker:

| File | Line | Sorts by | Risk |
|---|---|---|---|
| `generator.py:94` | `sorted(options, key=lambda o: o.score, reverse=True)` | score only | ⚠️ simulation path |
| `selector.py:69` | `sorted(scored_options, key=lambda pair: pair[1], reverse=True)` | score only | ⚠️ simulation path |
| `patterns.py:49` | `sorted(alive_entities_with_combat, key=lambda e: kill_counts[e])` | kill count only | ⚠️ simulation path |
| `modifier_applicator.py:73` | `sorted(modifiers, key=lambda m: m.modifier_type)` | type only | moderate |
| `gaps.py:117` | `sorted(gaps, key=lambda g: g.severity)` | severity only | low (analysis only) |
| others | various | various | low (reporting only) |

`generator.py` and `selector.py` are the highest-risk sites — they operate during tick
execution where ties in candidate scoring could resolve differently across replays.

**Architecture reference §4.1:** "If two outcomes can be tied, define a stable tie-breaker."

---

### F2 — `commitment/abandonment.py` returns untyped dict with mechanical fields — Priority: 9 / 15

| Dimension | Score | Reason |
|---|---|---|
| Adoption Gap | 2 | Isolated to `commitment/abandonment.py` (3 return sites) |
| Risk if Violated | 4 | `is_betrayal` (bool) and `penalty` (float) are mechanical — callers branch on `result["is_betrayal"]`; key rename silently breaks callers with no type error |
| Detection Ease | 3 | Not caught by type checker because return type is `dict`; only obvious on code review |
| **Total** | **9** | |

`classify_abandonment()` in `src/domains/commitment/abandonment.py` returns plain dicts:
```python
return {"is_betrayal": False, "penalty": 0.0, "reason": "survival"}
return {"is_betrayal": True,  "penalty": 0.8, "reason": "greedy_desertion"}
return {"is_betrayal": False, "penalty": 0.2, "reason": "voluntary_quit"}
```

Two violations of established patterns:
1. Mechanical fields (`is_betrayal`, `penalty`) belong in a typed dataclass per §1.2 of `architecture_reference.md`: "If a concept matters strategically or mechanically, it should exist as a typed record."
2. The `reason` string carries categorical meaning (`"greedy_desertion"`, `"survival"`) — this is an informal enum encoded as a string, violating §3.3: "`reason` is for explanation. It is not state."

**Fix:** Replace the return type with `@dataclass class AbandonmentClassification: is_betrayal: bool; penalty: float; category: AbandonmentCategory` where `AbandonmentCategory` is an enum.

---

### F3 — `design_patterns.md` describes V1 patterns, not V2 — Priority: 8 / 15

| Dimension | Score | Reason |
|---|---|---|
| Adoption Gap | 5 | Entire document describes V1 (GoalScorer, StateHandler, EntityBuilder, AIBrain) — none of these are the current extension points |
| Risk if Violated | 2 | Developers following this doc add wrong abstractions but don't break the engine immediately |
| Detection Ease | 1 | Only discovered by reading both the doc and current code side-by-side |
| **Total** | **8** | |

`docs/guidelines/design_patterns.md` documents 5 patterns: Goal Plugin (GoalScorer),
Damage Strategy (DamageCalculator), Entity Builder, Trait Aggregation, AI State Machine.

The current V2 engine uses: Domain Phase classes, authoritative pipeline, typed update records,
cognition domain orchestration. The V1 patterns (`GoalEvaluator`, `STATE_HANDLERS`, `EntityBuilder`)
may still exist in legacy paths but are not the extension points for new features.

A developer extending the simulation using this doc would:
- Add a `GoalScorer` subclass (V1 goal system) instead of extending the adventure/motivation domain
- Add a new `StateHandler` (V1 state machine) instead of adding a domain phase
- Use `EntityBuilder` fluent API (V1) instead of the catalog-driven `WorldAssemblyResolver`

**Note:** This is a joint D12/D17 finding. The doc is stale (D17) AND it actively misleads
about which patterns to follow (D12).

---

### F4 — 3 of 8 domain phases missing typed return annotations — Priority: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Adoption Gap | 3 | 3/8 domain phases (world_emergence, perception, memory) lack typed `-> ReturnType` annotation on execute() |
| Risk if Violated | 2 | No runtime behavior change; callers still receive the correct return type |
| Detection Ease | 2 | Immediately visible in IDE type checker output |
| **Total** | **7** | |

5 of 8 domain phases annotate their `execute()` return type:

| Phase | Typed return? |
|---|---|
| progression | ✅ `-> Optional[ProgressionConversionResult]` |
| cooperation | ✅ `-> Optional[CooperationResult]` |
| combat_engagement | ✅ `-> CombatEngagementDecisionResult` |
| information | ✅ `-> Optional[InformationResult]` |
| adventure | ✅ `-> Optional[AdventureDecisionResult]` |
| world_emergence | ❌ missing |
| perception | ❌ missing |
| memory | ❌ missing |

Missing annotations make it harder to verify that callers handle the return correctly
and reduces IDE support for domain phase integration. This is a consistency gap, not
a behavioral one.

---

### F5 — `kernel.py:770` direct `entity.timeline.append()` mutation — Priority: 6 / 15

| Dimension | Score | Reason |
|---|---|---|
| Adoption Gap | 1 | Single site |
| Risk if Violated | 2 | `entity.timeline` is a list, not durable structured state; append is bounded and predictable |
| Detection Ease | 3 | Pattern mismatch visible in code review; not immediately obvious to a new reader |
| **Total** | **6** | |

`kernel.py:770` calls `entity.timeline.append(event)` directly outside the authoritative
pipeline. This is a minor violation — `entity.timeline` is an in-memory event log, not
a durable state record — but it is inconsistent with the convention that state changes
go through typed updates. If timeline management grows, this becomes a coupling risk.

---

### Pattern Enforcement Priority Summary

| Finding | Description | Priority Score |
|---|---|---|
| F1 | Unstable sorts on simulation path | **10 / 15** |
| F2 | Untyped dict return in commitment/abandonment | **9 / 15** |
| F3 | design_patterns.md describes V1 patterns | **8 / 15** |
| F4 | 3 domain phases missing typed return annotations | **7 / 15** |
| F5 | kernel.py direct timeline append | **6 / 15** |

---

## Pattern Strengths

These V2 patterns are consistently applied across the codebase:

| Pattern | Coverage | Evidence |
|---|---|---|
| Domain Phase class structure | 8 / 8 phases | All domain `phase.py` files define `XPhase` with `execute()` |
| Decision/mutation separation | All 14 domains | No domain directly mutates `AuthoritativeState` (D14 confirmed) |
| Presenter layer | API routes | All entity/state endpoints go through read_cache DTOs or `StatePresenter` (D14 confirmed) |
| Metadata blobs | Near-clean | Only 1 `metadata={}` with data found in src/ (scenarios.py) |
| Authoritative pipeline | Engine core | `pipeline.py` is the single domain integration point; phases return typed records |

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| **P1** | Add stable `entity_id` tiebreaker to `generator.py:94` and `selector.py:69` sort keys | F1 — determinism on tick path |
| **P1** | Replace `classify_abandonment()` dict return with `AbandonmentClassification` typed dataclass; replace reason strings with `AbandonmentCategory` enum | F2 |
| **P1** | Update `docs/guidelines/design_patterns.md` to describe V2 extension points (domain Phase class, typed updates, WorldAssemblyResolver) — archive V1 patterns | F3 |
| P2 | Add typed return annotations to `world_emergence`, `perception`, `memory` phase `execute()` methods | F4 |
| P2 | Add import boundary CI test to catch cross-domain imports automatically (noted in D14) | F1 (prevention) |
| P2 | Move `entity.timeline.append()` in `kernel.py` into the event emission layer | F5 |

---

## Related Dimensions

- **D10 (Test Coverage)** — F3 bare random usage (the most serious determinism violation) is a test finding confirming the determinism pattern is breached. F1 here (unstable sorts) is the next tier.
- **D14 (Coupling Depth)** — pattern violations often co-locate with coupling violations; the `memory→time` import found in D14 is also a pattern violation (domain reaching outside its boundary).
- **D17 (Documentation Currency)** — F3 is a joint D12/D17 finding: `design_patterns.md` is stale and actively misleads. The D17 audit should include this file.
- **D13 (Type Safety)** — F4 (missing return annotations) is the border of D12 and D13; the D13 audit will assess annotation coverage more broadly.
