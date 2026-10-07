---
status: historical
layer: simulation
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES
phase: done
date: 2026-10-07
tags: [simulation-quality, progression]
---

# Plan
1. `src/engine/biological_needs.py::need_rates` (cached by profile id, species id, role); `apply.py` reads it in place of the constants (no line growth: code-health ratchet).
2. `EatScorer` -> `inn`; `src/engine/service_reach.py` resolves the service building from the building map with orthogonal reach; `town_resolution` uses it and serves EAT at an inn.
3. `CoreActions` REST recovers sleep debt (10).
4. Advisory `src/engine/need_paths.py` + `tools/need_path_report.py`.
5. Docs: divergence 2.80, parity PROG-128, `attributes_biology` binding, SURV-05 evidence line.
Out: shop/blacksmith, decision/arbitration, profile assignment.
