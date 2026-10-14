---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE
date: 2026-10-10
tags: [performance, observability, testing]
---

# Investigation: TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE

`docs/observability/baselines/latest.json` is a perf matrix keyed by profile, not a `BaselineConfig`; `src gate` rejects it with a ValidationError (exit 1), so it does not pass vacuously. The vacuous pass is reachable with a sweep-generated baseline_v1 file predating DEV-017. `baseline_generator.py` does not stamp the version, so generated baselines are INCONCLUSIVE until it does (outside this lift).
