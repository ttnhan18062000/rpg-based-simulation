# Phase 40-44: Cleanup, Authoring, Behavior Consumers, Second Pack, Fallback Retirement

## Overview

15 tickets across 5 phases. Implement in sequence — later phases depend on earlier ones.

---

## Phase 40 — Gradual cleanup of old enum assumptions

| Order | Ticket ID | Title | Notes |
|---|---|---|---|
| 1 | TCK-20260610-ENUM-REWARD-INFLUENCE | Replace enum checks in reward attribution and faction influence update | Companion to Phase 35-39 enum cleanup (combat/quest/region already done) |
| 2 | TCK-20260610-ENUM-USAGE-LINTER | Add enum usage linter with allowlist | Gate: prevents new enum coupling from spreading |
| 3 | TCK-20260610-ENUM-MIGRATION-REPORT | Add enum migration backlog report | Visibility: categorises remaining enum usage for migration tracking |

---

## Phase 41 — Broaden scenario authoring from clean data

| Order | Ticket ID | Title | Notes |
|---|---|---|---|
| 4 | TCK-20260610-SCENARIO-TEMPLATES | Add scenario authoring templates with structural schema | Prerequisite for 41.2 and 41.3 |
| 5 | TCK-20260610-SCENARIO-WORLD-VALIDATION | Add scenario-to-world-composition feature validator | Requires templates schema |
| 6 | TCK-20260610-SCENARIO-CATALOG-MATRIX | Add scenario catalog matrix integration test (8 scenarios) | Requires both template and validator |

---

## Phase 42 — Add deeper behavior consumers for drives, needs, and senses

| Order | Ticket ID | Title | Notes |
|---|---|---|---|
| 7 | TCK-20260610-MOTIVATION-PRESSURE-RESOLVER | Add MotivationPressureResolver from need/drive profiles | May require minimal catalog fixtures for profiles |
| 8 | TCK-20260610-SENSE-PERCEPTION-GATE | Add PerceptionGate from sense profiles | May share catalog fixtures with 42.1 |
| 9 | TCK-20260610-PRESSURE-PERCEPTION-CONSUMERS | Connect pressure and perception to decision points | Requires 42.1 and 42.2 |

---

## Phase 43 — Introduce second content pack after first pack proves stable

| Order | Ticket ID | Title | Notes |
|---|---|---|---|
| 10 | TCK-20260610-SECOND-PACK-THEME | Select and document second content pack theme | Gate: verify Phase 43 entry criteria first |
| 11 | TCK-20260610-SWAMP-BORDER-PACK | Implement swamp_border_pack content pack | Requires theme selection |
| 12 | TCK-20260610-MULTI-PACK-INTERACTION | Add multi-pack composition integration test | Requires both packs to exist |

---

## Phase 44 — Final legacy fallback retirement plan

| Order | Ticket ID | Title | Notes |
|---|---|---|---|
| 13 | TCK-20260610-FALLBACK-RETIREMENT-CRITERIA | Document and gate explicit fallback retirement criteria | Defines the gate; no code deleted here |
| 14 | TCK-20260610-FALLBACK-RESTRICT-MODES | Restrict fallback to test_manual and debug modes | Requires criteria definition |
| 15 | TCK-20260610-FALLBACK-RECORDS-REMOVAL | Graduated removal of fallback records by family | Requires restriction in place; may spawn sub-tickets per family |

---

## Cross-phase dependency summary

```
40.1 → 40.2 → 40.3
41.1 → 41.2 → 41.3
42.1 → 42.3
42.2 → 42.3
43.1 → 43.2 → 43.3
44.1 → 44.2 → 44.3
```

Phases 40/41/42/43 are independent of each other.
Phase 44 is a capstone — ideally starts after Phase 43 is stable.
