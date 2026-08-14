---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION
artifact_type: test_plan
tags: [simulation-quality, world, corpus, calibration]
---

# Test Plan — TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION

## Real-kernel verification (already performed, not a mock)

- `world resolve simq_scale_stress_seed42` — real composition resolution, succeeded after 2
  real collisions were found and fixed by removing colliding modules.
- `world compile simq_scale_stress_seed42` — real `WorldCompiler.compile()`, 68 entities/13
  regions/18 resource nodes/7 buildings/27 quests/11 factions confirmed.
- `tools/calibrate_simq.py --name simq_scale_stress_seed42 --profile simq_scale_stress_seed42 --seed 42 --ticks 200`
  — real engine run, real `QualityHub` scoring, real quality_report.json.

## Regression coverage

- `simq_scale_stress_seed42_seed42_200t` added to `FAST_ANCHOR_KEYS` in
  `test_grade_regression.py` — the new anchor is exercised by the fast-tier gate going forward,
  same as every other corpus world's own anchor.
- `tests/tools/test_corpus_registry.py` (from ticket 1) — re-run to confirm the new world's
  registry entry doesn't break existing coverage/consistency checks (full corpus regeneration).

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`
`.venv/bin/python3 -m pytest tests/tools/test_corpus_registry.py -q`
