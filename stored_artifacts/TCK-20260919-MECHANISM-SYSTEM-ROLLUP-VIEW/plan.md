---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW

## Goal
Build child 3 of `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP`, deferred until the membership
foundation existed. A per-system rollup view showing what each system actually contains, holding to
two known constraints: counts never a badge, rates against a live baseline never in isolation.

## Design
1. `build_system_rollup(data)` in `registry.py` — a pure, read-only aggregation over
   `mechanisms_by_system()`'s own output, sharing one `_rollup_stats()` counting helper across
   per-system, `unassigned`, and whole-registry-baseline computations (same counting path for all
   three, so a comparison between them is meaningful).
2. Per group: mechanism count, `implemented_by`-bound count/rate, verified count/rate (split
   runtime vs static per `mechanism_verification_view.md`'s own convention), full 6-state
   breakdown.
3. `generate_mechanism_system_rollup_view.py` — CLI mirroring `generate_mechanism_verification_
   view.py` exactly (`--output`/`--registry`/`--check`), rendering a markdown table plus a baseline
   summary line.
4. `make mechanism-system-rollup-view` target, no separate `--check` target (matching the plain-view
   convention — only atlas/capabilities regenerators, which mutate a second artifact, pair with one).
5. Tests mirroring `test_mechanism_registry_view.py`'s structure: fixture-based correctness tests
   for the two hard constraints (counts-not-badge, baseline-not-isolated) plus the generator-CLI
   trio (check-mode staleness, Make target, real-file-up-to-date regression guard).

## Non-goals
- No wiring into atlas/capabilities — a new, separate rendered view.
- No derived ranking/verdict from system membership at any point.
- No revisiting the foundation's own many-to-many multi-membership decision.
