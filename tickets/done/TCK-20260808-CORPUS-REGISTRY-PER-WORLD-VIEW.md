---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW
phase: open
date: 2026-08-08
tags: [simulation-quality, world, corpus]
---

# TCK-20260808-CORPUS-REGISTRY-PER-WORLD-VIEW

## Title
Add a per-world `worlds:` section to `corpus_registry.yaml` — scale/tier data exists but is only
reachable through up to 10 duplicate per-run_key entries, sorted alphabetically among 80 total

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
User reported being unable to find world size/tier in `config/simulation_quality/corpus_registry.yaml`
(built by `TCK-20260808-SIMQ-CORPUS-WORLD-METADATA-REGISTRY`). The data exists (`scale`/`tier`
fields on every entry) but the registry is keyed by `run_key`, not `world_name` — a world with
multiple seeds/tick-lengths (e.g. `dungeon_crawl`, 10 run_keys) has its identical scale/tier data
duplicated 10x, scattered alphabetically among 80 total entries, with no single per-world lookup
point. A real usability gap in already-delivered work, not missing data.

## Implementation Notes
Added a `worlds:` top-level section to `tools/generate_corpus_registry.py`'s output, one entry per
unique `world_name` (20, vs. 80 run_key entries) — `tier`, `scale` (deduplicated; asserted
identical across all of that world's own run_keys, since scale is a world-compile fact, not a
per-seed one — a real assertion, not an assumption, verified for all 20 worlds during Implement),
and `run_keys` (the list of run_keys backing it, for cross-reference into the existing per-run_key
section). The per-run_key section is unchanged — additive, not a breaking restructure, since the
3 sibling tickets from the same batch (ceiling, perf-baseline, large-scale-world) already consume
the per-run_key shape.

## Test Summary
`tests/tools/test_corpus_registry.py` extended with `test_corpus_registry_worlds_section_dedupes_correctly`
(worlds section has exactly one entry per unique world_name, and each world's scale is
bit-identical across all its own run_keys — the assertion that made deduplication safe) and
`test_corpus_registry_worlds_run_keys_cross_reference_real_entries` (every `run_keys` list entry
is a real key in the per-run_key section). All 5 tests in the file pass (3 pre-existing + 2 new).

## Files Changed
- `tools/generate_corpus_registry.py` (`worlds:` section added, dedup-safety assertion)
- `config/simulation_quality/corpus_registry.yaml` (regenerated, +20-entry `worlds:` section)
- `tests/tools/test_corpus_registry.py` (2 new tests)

## Completion Summary
Verified the dedup assumption (scale identical across a world's own run_keys) is actually true for
all 20 worlds before relying on it, rather than assuming. Additive change — the existing
per-run_key section and its 3 downstream consumers (ceiling, perf-baseline, large-scale-world
tickets) are unaffected.
