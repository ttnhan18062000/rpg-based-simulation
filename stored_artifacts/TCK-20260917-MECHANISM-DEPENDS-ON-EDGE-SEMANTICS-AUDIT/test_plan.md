---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT
artifact_type: test_plan
tags: [architecture, schema]
---

# Test Plan — TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT

## What is under test
This ticket edits `registries/mechanisms.yaml`'s `depends_on` edges (removals only, no additions).
The relevant behavior to verify: the registry remains schema-valid and acyclic after any removal, and
the derived-priority view continues to run against the corrected edge set.

## Normal flow
- `registries/mechanisms.yaml` validates against its own schema after edits
  (`python3 tools/mechanism_registry/validate.py` or repo-equivalent validator — confirm exact
  entrypoint during implementation).
- `tools/mechanism_registry/generate_mechanism_priority_view.py` runs without error before and after
  the edit set.

## Edge cases
- An edge removal that would orphan a mechanism (leave it with zero remaining `depends_on` and zero
  dependents) is not itself an error — record it, don't treat it as a regression to fix.
- A mechanism whose only declared edge is removed still validates as long as the schema doesn't
  require at least one edge (confirm this during implementation by checking the schema/validator).

## Failure modes
- Removing an edge that breaks acyclicity validation elsewhere (should not happen — removals only
  shrink the graph — but confirm the validator still passes).
- A REMOVE verdict recorded without the same evidence rigor as the `combat_resolution` correction —
  guarded by this ticket's own Acceptance Criteria #2, checked manually during Completion Summary
  write-up, not by an automated test.

## Regression-prone paths
- `tools/mechanism_registry/generate_mechanism_priority_view.py`'s own priority computation, since it
  is the direct consumer of `depends_on` and the ticket's own motivation (AC #3: measure the
  priority-ranking shift).

## Existing tests to run
Located via `grep -rl "mechanisms.yaml" tests/`:
- `tests/unit/tools/test_mechanism_registry.py` — schema/structural validation of the registry itself.
- `tests/unit/tools/test_mechanism_priority_derivation.py` — directly covers the priority computation
  this ticket's AC #3 requires re-measuring.
- `tests/unit/tools/test_mechanism_registry_completeness_check.py` — completeness/consistency checks
  that must still pass after edge removals.
- `tests/unit/tools/test_mechanism_state_caller_check.py` — likely relevant given this audit's own
  subject is caller-vs-dependency conflation; run to confirm no regression.
- `tests/unit/tools/test_mechanism_artifact_convergence.py`,
  `tests/unit/tools/test_mechanism_registry_graphify_check.py` — broader registry-consistency
  coverage, run as part of the scoped suite rather than the full suite.

Scoped command: `pytest tests/unit/tools/test_mechanism_registry.py
tests/unit/tools/test_mechanism_priority_derivation.py
tests/unit/tools/test_mechanism_registry_completeness_check.py
tests/unit/tools/test_mechanism_state_caller_check.py
tests/unit/tools/test_mechanism_artifact_convergence.py
tests/unit/tools/test_mechanism_registry_graphify_check.py -v`
