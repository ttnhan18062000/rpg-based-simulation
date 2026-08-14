---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY
artifact_type: test_plan
tags: [simulation-quality, world, corpus]
---

# Test Plan — TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY

## New tests

1. `test_corpus_registry_covers_every_anchored_run_key` — every `grade_anchors.json` key has a
   corresponding registry entry (no anchored scenario silently missing from the registry).
2. `test_corpus_registry_world_names_resolve_to_real_directories` — every entry's `world_name`
   field is a real `data/worlds/{name}/` directory (guards against the registry drifting from
   `_resolve_world_name`'s own real resolution as worlds are added/renamed).
3. `test_corpus_registry_scale_fields_match_compile_report` — spot-check a handful of entries'
   scale fields against their real `world_compile_report.json`, catching silent staleness if the
   registry generator is ever run against outdated compile reports.

## Regression surface

`tests/simulation_quality/test_grade_regression.py` (unaffected, but run as a sanity check — this
ticket touches no anchor values).

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/tools/test_corpus_registry.py -q` (new file)
