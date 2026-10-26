---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE
date: 2026-10-24
tags: [performance, documentation, certification]
---

# Test plan: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

- `tests/unit/perf/`: every `_check_*` outcome carries its `check`; PASS has none; `compare()` end to end per check; old record JSON without `check` still loads; round trip keeps `check`; known-debt entry matches on state + check and a different check or state does not; a source guard that `tools/perf/known_debt.py` never reads `.reason`.
- `tests/docs/test_gate_conformance_map.py`: the real map covers every call site with no stale entry and no unknown clause; synthetic tmp_path trees show an unmapped site, a stale entry and an unknown clause failing, naming file and function.
- `tests/docs/test_certification_contract_names.py`: the three legacy names appear only inside the documented earlier-name notes.
- Scoped runs: `tests/unit/perf`, `tests/docs`, `tests/tools/test_perf_baseline_tool.py`, `python3 -m codebase.health check`, paths-guard, REGISTRY regenerated.
- The `performance_contract.md` edit: a text test that no sentence still says "The threshold is not yet set" and that the decided value is stated; added with that commit.
