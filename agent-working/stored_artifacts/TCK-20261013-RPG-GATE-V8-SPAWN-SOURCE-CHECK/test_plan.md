---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK
artifact_type: test_plan
date: 2026-10-19
tags: [testing]
---

# Test plan — TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK

| AC | proof |
|---|---|
| AC4 | `tests/simulation_quality/rpg_gate/test_v8_fires.py::test_a..test_g`: real apply path, real recorders, real `compute`; never skipped |
| AC5 | `tests/architecture/test_spawn_sites_declare_source.py`: real tree passes; synthetic unsourced site, stale entry, tagged-now entry, wrong count, flipped flag default, missing flag, gate world enabling a flag each fail |
| AC6 | no change under `src/`, `config.yaml` or the oracle; (e) proves silence is no-data |
| AC7 | `SEQUENCE.md` already lists item 7; epic notes updated; one testing PR |

Commands: `pytest tests/simulation_quality/rpg_gate tests/architecture/test_spawn_sites_declare_source.py tests/unit/observability/test_rpg_gate_metrics.py tests/unit/observability/test_run_ledger.py tests/unit/tools/test_rpg_gate_*.py`.
