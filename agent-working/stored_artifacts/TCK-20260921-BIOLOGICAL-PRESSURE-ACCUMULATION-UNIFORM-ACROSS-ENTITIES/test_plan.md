---
status: historical
layer: simulation
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260921-BIOLOGICAL-PRESSURE-ACCUMULATION-UNIFORM-ACROSS-ENTITIES
phase: done
date: 2026-10-07
tags: [simulation-quality, progression]
---

# Test Plan
`tests/unit/engine/test_biological_needs.py` (13 tests): legacy rate preserved for `medium`; person fallback; `none` kinds never hunger; profiles differ; explicit profile wins; undeclared kind reported with legacy rates; `ApplyPath` per kind; service reach orthogonal only; REST recovers sleep debt; inn serves a meal beside it; `EatScorer` targets the inn; advisory flags a hungry kind in an inn-less world. Scoped suites (world, resource, social, core, engine, tactical, strategic, kernel, systems; 1941 passed). Gates: `codebase.health check` 0 new / 0 worse; mypy baseline clean on changed files; package registry clean (local scratch venv; CI is the first real run).

## Proof Plan
- level: unit plus scenario
- proof kind: regression
- oracle source: SURV-05/SURV-06 catalog rules and the pre-change constants (medium = 0.1 / 0.05)
- expected effect: hungerless kinds never hunger; medium kinds unchanged; REST lowers sleep debt
- selected commands: `pytest tests/unit/engine/test_biological_needs.py`
