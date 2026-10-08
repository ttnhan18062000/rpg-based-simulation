---
status: historical
layer: combat
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC
phase: done
date: 2026-10-07
tags: [combat, regression]
---

# Test Plan — TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC (testing rescope)

- The rescoped test passes on the landing base, and two runs at one SHA give identical per-seed counts.
- The measured figures in the docstring match the test's own output (seeds 301-310: baseline 17, high 137).
- `data/content/social/species_relations.yaml` is byte-identical to main after the runs (the test restores it in `finally` and asserts so).
- After the species known-reds entry is removed, the known-reds lint stays clean and `tests/unit/tools/test_slow_regression_report.py` passes.

## Proof Plan
- **Level:** integration (the real ScenarioLabOrchestrator + MetamorphicRuleEngine path), slow, resource budget large.
- **Proof kind:** metamorphic relation (pooled high >= pooled baseline) plus a determinism repeat.
- **Oracle source:** rpg-planner's ruling of 2026-10-07 (the relation holds for pairs that meet), recorded verbatim in the ticket.
- **Expected effect:** pass with identical per-seed counts on two runs; the non-vacuity guard holds (>= 2 baseline seeds with contact; measured 4).
- **Selected commands:** `python -m pytest tests/integration/lab/test_species_relations_metamorphic_validation.py --resource-budget large -q -rP` (twice, one SHA); `python -m pytest tests/unit/tools/test_slow_regression_report.py -q`.
