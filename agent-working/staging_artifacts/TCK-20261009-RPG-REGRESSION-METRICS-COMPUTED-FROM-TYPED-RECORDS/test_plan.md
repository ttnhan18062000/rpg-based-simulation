---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS
artifact_type: test_plan
tags: []
---

# Test plan
Per metric V1-V7: a constructed ledger/event stream that violates it (expects violations>0 and an example) and a clean one (0). O1-O7: values on a constructed stream equal hand-computed numbers. pool(): two docs -> pooled rows incl. O2.seeds_with_survivors. Determinism: compute twice on the same artifacts -> identical JSON. Liveness: a run without the ledger header -> no-data, never zero. Architecture: rpg_gate_metrics imports no engine decision module and reads no live state. One real pinned run (small world, few ticks) through tools/test_architecture/rpg_gate_run.py end to end. Always also run tests/unit/tools/test_mechanism_registry_completeness_check.py for any change that adds or moves a src file.
