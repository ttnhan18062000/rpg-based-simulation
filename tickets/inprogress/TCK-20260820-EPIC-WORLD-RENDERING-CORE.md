---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260820-EPIC-WORLD-RENDERING-CORE
phase: open
date: 2026-08-20
tags: [rendering, visualization, world, simulation-quality, architecture, determinism]
---

# TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Title
Epic: Server-Owned World Rendering Core, with Visual/Geometric Quality Validation as First Consumer

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Build a server-owned, deterministic world-rendering core — one canonical renderer, thin consumption modes on top — with batch/QA PNG generation as the buildable-first mode (live-streaming/multi-device deferred in full). Its first prioritized consumer is a SimQ-sibling visual/geometric quality validation system (not an 11th SimQ pillar) that scores generated worlds on Shape, Density, Variants, and Connectivity, feeding a tiered agent-review pipeline. This epic is scope-only: it tracks a breakdown of child tickets, each independently scoped/investigated when picked up. The investigation itself is already complete — see Related Docs — this ticket does not re-investigate.

## Scope
This epic tracks the following prospective child tickets (not created in this pass — epic tier is scope-only):

1. **Core batch/QA renderer** (prerequisite for all others) — deterministic PNG generation from `AuthoritativeState` (terrain, `blocked_tiles`, `building_tiles`, `town_tiles`, entity positions), reusing `DirtySet` (`src/core/dirty.py`) for incremental re-render caching, storing output under the existing `data/runs/{run_id}/` convention via the already-live `RetentionPolicy`/`RetentionManager` (`src/observability/reporting/retention.py`). Must reproduce the proven bit-identical SHA256 determinism as a golden-hash regression test. Zero new pip dependency required at minimum; numpy adoption (already present, not yet a committed dependency) is a decision this child ticket makes, not this epic.
2. **Four validation metric families** — Shape (connected-component-aware bounding-box fill-ratio; repetition/rotation detection), Density (entity nearest-neighbor coefficient of variation; terrain-type histogram), Variants (trail-activity liveliness; cross-*spec* diversity via total-variation-distance), Connectivity (whole-map walkable-region reachability) — as real, tested implementations promoted from the `experiments/spatial_rendering/prototype/` scripts, not new designs.
3. **Sibling scoring/grade-band system** — reuses SimQ's exact S/A/B/C/D/F numeric thresholds (`docs/simulation_quality/quality_scoring_contract.md` §4.5) but is an architecturally independent implementation (computes directly from `AuthoritativeState` geometry, no event to hang off `ObservabilityEventEnvelope`) — explicitly not a new SimQ pillar.
4. **Multi-seed / multi-world threshold calibration** — mirrors `tools/calibrate_simq.py`'s real precedent; none of the four metric families have multi-seed-calibrated healthy-band thresholds yet (fill-ratio has single-seed, full-corpus evidence; the other three are tested on only 1–3 worlds).
5. **Agent-review pipeline** — Tier 0 (pure data, zero image) → Tier 1 (compact JSON digest) → Tier 2 (actual image, fetched only on escalation) design; the coordinate-gridded/annotated render variant is the default Tier-2 output. Includes the open question of whether a new `.claude/agents/world-render-reviewer.md` subagent gets built or this folds into an existing agent's scope (closest structural template: `.claude/agents/simulation-analyst.md`).

Each child ticket is independently scoped and investigated (standard tier expected for most, pending its own scoping pass) when picked up; this epic does not commit to child ticket IDs, ordering beyond (1) being a prerequisite for (2)-(5), or exact sequencing beyond that dependency.

## Out of Scope
- **Live-streaming/multi-device rendering mode** — deferred in full per the parent vision doc's own "Option C" architecture (one renderer, two modes); no implementation plan exists for it and none is being scoped here.
- **Player-facing frontend reconnection** — fixing the 5 missing backend routes (`/map`, `/static`, `/stats`, `/speed`, `/clear_events`) that `frontend/src/hooks/useSimulation.ts` calls but `src/api/server.py`/`src/api/routes/*.py` do not serve (confirmed still broken today via direct route-decorator grep; `src/api/routes/state.py` is still a 0-line empty file) is explicitly deferred. Per direct user instruction ("I prefer the second first"), validation/measurement rendering is priority; UI rendering is not.
- **Any decision on replacing vs. reconnecting the existing React/Canvas frontend** (`GameCanvas.tsx` et al.) — an open product/architecture question per the parent vision doc, not decided or scoped by this epic.
- **Placement-legality checks** (routed to `HardLawMonitor`) and **biome-resource content correctness** (routed to an extension of the existing `CatalogValidator`) — both explicitly out of scope for the validation consumer; any check reducing to "does field X belong to allowed-set Y" is a data-lookup check, not a visualization/geometry check, no matter how spatial it sounds.
- **Elevation-based metrics** — ruled inapplicable; this engine's terrain is a flat categorical classification with no continuous elevation field.

## Acceptance Criteria
- [ ] A documented, ordered breakdown of child tickets exists in this epic's Scope section (done in this pass) that a later ticket-creation pass can use directly to open the 5 child tickets listed above.
- [ ] Each child ticket, when opened, references this epic in its `Related Tickets` section.
- [ ] No implementation work happens directly on this epic ticket — epic tier tracks children only (per CLAUDE.md Tier Routing table: epic tier is "Scope only — tracks child tickets").
- [ ] The two new tags (`rendering`, `visualization`) are registered in `registries/tag_registry.jsonl` before this ticket is created (done in this pass — verified below).

## Related Tickets
None. Verified directly: no ticket in `tickets/inprogress/`, `tickets/done/`, or `tickets/backlogs/` covers world-geometry rendering or visual/geometric quality validation. `TCK-20260619-E51D-RENDERER` (done) is the Chronicle.md/chronicle.json text renderer — a different domain (narrative markdown generation), not spatial/PNG rendering. `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`, the one ticket both idea docs flagged as "currently in-progress, unrelated," is now confirmed DONE in `tickets/done/` — the idea docs' "no ticket dependency" claim still holds.

## Related Docs
- `docs/plans/world_rendering/idea_world_rendering_core.md` — parent vision doc: architecture options (Option C — shared core, two modes — chosen), benchmarked performance, architecture constraints.
- `docs/plans/world_rendering/idea_world_render_validation.md` — validation consumer: four metric families, real corpus findings, scoring design, tiered agent-review pipeline.
- `docs/engine/contracts/regression_and_verification.md` — Absolute Determinism law (confirmed present, §"Absolute Determinism and Observable AI"), the constraint the renderer must preserve.
- `docs/simulation_quality/quality_scoring_contract.md` §4.5 — the S/A/B/C/D/F grade-band vocabulary and thresholds this epic's scoring system reuses (confirmed present, `config/simulation_quality/grade_thresholds.yaml` is the live source of the thresholds).
- `docs/testing/test_taxonomy.md` — performance work fits `tests/perf/` + `perf_budget`; metric-correctness tests are ordinary `tests/unit/`; render-determinism golden-hash test is a `regression`-marker candidate.

## Related Stored Artifacts
None found. `stored_artifacts/` has no prior investigation in this area (searched directly for `*world_render*` / `*spatial_render*`) — consistent with the idea docs' own claim that nothing has been promoted from this investigation yet.

## Related Code Areas
- `src/core/state.py` — `AuthoritativeState` (terrain, `blocked_tiles`, `building_tiles`, `town_tiles`, entity `position`/`last_position`/`home_position`) — the sole data source the renderer reads.
- `src/core/dirty.py` — `DirtySet` (`PERF-006`), already computed every tick, must be reused for incremental rendering, not reimplemented.
- `src/engine/legality.py` — `LegalityServiceV2.verify_occupancy()`, the walkability rule the Connectivity metric and any occupancy-aware rendering must follow.
- `src/observability/reporting/retention.py` — `RetentionPolicy`/`RetentionManager`, to be reused for `renders/` artifact storage under `data/runs/{run_id}/`.
- `src/simulation_quality/pillars.py` — the 10 existing SimQ pillars, confirmed to have zero spatial/geometric coverage; the new scoring system is a sibling, not an addition here.
- `experiments/spatial_rendering/prototype/` — 7 already-committed, already-executed prototype scripts (`png_writer.py`, `render_world.py`, `render_trail.py`, `render_annotated.py`, `benchmark.py`, `render_incremental.py`, `render_numpy.py`) and rendered PNG evidence in `prototype/output/` — the primary evidence base for child tickets to promote from, not re-derive.
- `frontend/src/constants/colors.ts` — existing visual design system (tile/entity/behavior/resource colors, `hpColor()`), worth porting (not verbatim — keyed by numeric IDs, backend terrain is string-keyed) rather than reinventing.
- `.claude/agents/simulation-analyst.md` — closest existing structural template for a future `world-render-reviewer` agent role.

## Assumptions / Open Questions
Carried forward verbatim from the two idea docs — genuinely still open, to be resolved by whichever child ticket picks up the relevant piece, not decided in this epic:
- Exact digest JSON schema and the Tier 0→2 escalation threshold (e.g. what fill-ratio value triggers fetching the real image) — not calibrated.
- Exact healthy-band threshold numbers for all four metric families, and whether `FOREST` needs its own, separate threshold band from other biome types given its structurally different (composite-stamp) generation pattern. Fill-ratio has real corpus-wide (15-world) single-seed evidence; the other three families are tested on only 1–3 worlds; none have multi-seed calibration yet.
- Whether `FOREST`'s distinct multi-rectangle-composite generation pattern (vs. every other biome type's clean single rectangle) points to a specific, fixable difference in `src/worldgeneration/generator.py`'s placement logic — not investigated, a sharper follow-up lead than "biome placement in general looks stamped."
- Whether this becomes a real new `.claude/agents/world-render-reviewer.md` file, or folds into an existing agent's scope.
- Historical-tick checkpoint interval (every tick vs. every N) — cheap to tune, not calibrated.
- Exact terrain-string vocabulary is not exhaustively enumerated across every world (only sampled, not walked systematically against `src/worldgeneration/generator.py`'s full output space) — needed before a complete, non-`DEFAULT`-fallback color table can be built.
- Whether a rectangle-decomposition check should pair with the fill-ratio metric — a composite of several rectangles unioned together scores artificially low (more "organic-looking") on fill-ratio alone.
- Whether the existing React/Canvas frontend gets reconnected or replaced by a new client of this rendering core — explicitly out of scope for this epic (see Out of Scope), listed here only because it is the one open question this epic deliberately does not answer.
- `layer: world` was chosen over registering a new `rendering` layer because the two idea docs' own frontmatter already used `layer: world` and the work is squarely world-geometry/worldbuilding-adjacent; `rendering`/`visualization` were registered as tags (subsystem-topic category) instead, which is sufficient granularity without a new layer.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
