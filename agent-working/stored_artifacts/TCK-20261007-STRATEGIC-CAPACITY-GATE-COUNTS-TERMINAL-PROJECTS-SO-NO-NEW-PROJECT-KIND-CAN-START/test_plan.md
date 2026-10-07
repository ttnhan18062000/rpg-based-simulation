---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START
artifact_type: test_plan
tags: [strategy, cognition, bug]
---

# Test plan

New: `tests/unit/strategic/test_project_capacity_counts_live_projects.py`. Existing, rerun: `tests/unit/strategic`, `tests/unit/ai`, `tests/unit/world`, the CI jobs' directory lists, `tests/integration/campaigns`. Gates: code-health ratchet, parity-ledger schema, mypy baseline, frontmatter and registry clean-export check.

## Proof Plan
- **Level**: unit (predicate, gate, trim, enforcement phase, guild scorer) and corpus (before and after).
- **Proof kind**: regression tests with a disabling control per site; before and after measurement with an identical repeat.
- **Oracle source**: the stated intent of `max_active_projects` (bounds the projects an entity is working on) and `LIMIT-01` (capacity bounds concurrent commitments); a finished project is not a concurrent commitment.
- **Expected effect**: an entity holding only finished projects starts a project of a new kind; the project mix changes (disclosed); survival is not expected to change.
- **Selected commands**: `pytest tests/unit/strategic/test_project_capacity_counts_live_projects.py tests/unit/strategic tests/unit/ai tests/unit/world`; the CI directory lists; `pytest tests/integration/campaigns`; `measure_cap.py` on `crowded_frontier` and `frontier_living_world` before and after.
