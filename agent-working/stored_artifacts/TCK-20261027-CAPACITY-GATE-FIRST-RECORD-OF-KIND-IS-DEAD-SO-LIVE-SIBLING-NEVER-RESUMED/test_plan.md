---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED
phase: open
date: 2026-10-28
tags: []
---

# test_plan

- Dead-first-in-dict with a SUSPENDED sibling and a matching target: resumes the sibling; no new project; `CapacityEnforcementPhase` evicts nothing.
- Dead-first, live sibling, different target: sibling ended with the typed reason, new project created, live count unchanged, gate not consulted.
- No live record, full cap: refused; escalated need (2.137) still admitted.
- Current project of the kind with a matching target: continues, no switch.
- Newest-live rule and tie-break; ACTIVE before SUSPENDED.
- Target match: entity-targeted kinds on target_entity_id; others on target_id; both None matches.
- Typed field round-trips through to_canonical_dict / from dict; unchanged hash when None.
- Determinism: dict order independent (shuffle insertion order, same result).
