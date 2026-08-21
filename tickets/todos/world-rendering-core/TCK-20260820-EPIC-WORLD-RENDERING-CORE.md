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

**Refined 2026-08-20, per direct user clarification (not in the original investigation docs):**
- **On-demand tooling, not automatic, not blocking.** Runs when invoked, not hooked into world-compile/simulation-run completion or CI. Grades are reported only — never wired to a pass/fail test, same posture SimQ's own scores have today.
- **Scoring is averaged across multiple seeds per world spec**, anticipating that world generation will eventually produce seed-varied maps (it currently does not — see Scope item 3 and Out of Scope).
- **Deterministic, rule-based measurement is the default and primary mechanism** — hard rules (binary geometric facts), soft rules (gradient signals), and scoring rules (how they combine) — not routinely feeding rendered images into a model. Image-based agent review is the escalation path (Tier 2), not the default.
- **Two new documentation deliverables requested explicitly**: a `docs/visual_quality/`-style subfolder mirroring `docs/simulation_quality/`'s shape, and a new periodic `docs/audits/` dimension entry (next number: D26) auditing this system's own health, mirroring `docs/audits/D20_simq_integration.md`'s relationship to SimQ.

See `docs/plans/world_rendering_core_epic.md` for the full epic plan doc consolidating all of this.

## Scope
This epic tracks the following prospective child tickets (not created in this pass — epic tier is scope-only):

1. **Core batch/QA renderer** (prerequisite for all others) — deterministic PNG generation from `AuthoritativeState` (terrain, `blocked_tiles`, `building_tiles`, `town_tiles`, entity positions), reusing `DirtySet` (`src/core/dirty.py`) for incremental re-render caching, storing output under the existing `data/runs/{run_id}/` convention via the already-live `RetentionPolicy`/`RetentionManager` (`src/observability/reporting/retention.py`). Must reproduce the proven bit-identical SHA256 determinism as a golden-hash regression test. Zero new pip dependency required at minimum; numpy adoption (already present, not yet a committed dependency) is a decision this child ticket makes, not this epic.
2. **Four validation metric families** — Shape (connected-component-aware bounding-box fill-ratio; repetition/rotation detection), Density (entity nearest-neighbor coefficient of variation; terrain-type histogram), Variants (trail-activity liveliness; cross-*spec* diversity via total-variation-distance), Connectivity (whole-map walkable-region reachability) — as real, tested implementations promoted from the `experiments/spatial_rendering/prototype/` scripts, not new designs.
3. **Sibling scoring/grade-band system** — reuses SimQ's exact S/A/B/C/D/F numeric thresholds (`docs/simulation_quality/quality_scoring_contract.md` §4.5) but is an architecturally independent implementation (computes directly from `AuthoritativeState` geometry, no event to hang off `ObservabilityEventEnvelope`) — explicitly not a new SimQ pillar. Structured as **hard rules** (binary geometric facts), **soft rules** (gradient signals with a healthy band), and **scoring rules** (combination into a grade) — deterministic and rule-based by default, matching SimQ's own non-visual-model measurement philosophy. **Multi-seed averaging is core to this system's design**: a world spec's score averages across multiple seeds' renders of it. **Verified current limitation**: terrain/biome layout is presently deterministically *fixed* per world spec (byte-identical across seeds 42/137/999 — only entity placement/behavior varies by seed today) — averaging will be correct but a no-op until world generation itself becomes seed-varied, which is a `src/worldgeneration/`-side capability explicitly out of scope for this epic (see Out of Scope). Build the averaging mechanism now regardless.
4. **Multi-seed / multi-world threshold calibration** — mirrors `tools/calibrate_simq.py`'s real precedent; none of the four metric families have multi-seed-calibrated healthy-band thresholds yet (fill-ratio has single-seed, full-corpus evidence; the other three are tested on only 1–3 worlds).
5. **Agent-review pipeline** — Tier 0 (pure data, zero image — the deterministic hard/soft/scoring-rule path from item 3, primary and default) → Tier 1 (compact JSON digest) → Tier 2 (actual image, fetched only on escalation) design; the coordinate-gridded/annotated render variant is the default Tier-2 output. Includes the open question of whether a new `.claude/agents/world-render-reviewer.md` subagent gets built or this folds into an existing agent's scope (closest structural template: `.claude/agents/simulation-analyst.md`).
6. **Documentation deliverables**, explicitly requested: a new `docs/visual_quality/` subfolder (naming TBD at implementation time) mirroring `docs/simulation_quality/`'s shape (scoring contract, current-state doc, calibration/audit-workflow doc) — the living reference for this system's hard/soft/scoring rules and calibration state; and a new periodic audit dimension entry under `docs/audits/` — **confirmed next available number: D26** (D25 was claimed same-day, 2026-08-20, by an unrelated concurrent ticket, `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`) — mirroring `docs/audits/D20_simq_integration.md`'s relationship to SimQ: a periodic audit *of* this system's own health, distinct from its own on-demand scoring output.

Each child ticket is independently scoped and investigated (standard tier expected for most, pending its own scoping pass) when picked up; this epic does not commit to child ticket IDs, ordering beyond (1) being a prerequisite for (2)-(6), or exact sequencing beyond that dependency.

## Out of Scope
- **Live-streaming/multi-device rendering mode** — deferred in full per the parent vision doc's own "Option C" architecture (one renderer, two modes); no implementation plan exists for it and none is being scoped here.
- **Player-facing frontend reconnection** — fixing the 5 missing backend routes (`/map`, `/static`, `/stats`, `/speed`, `/clear_events`) that `frontend/src/hooks/useSimulation.ts` calls but `src/api/server.py`/`src/api/routes/*.py` do not serve (confirmed still broken today via direct route-decorator grep; `src/api/routes/state.py` is still a 0-line empty file) is explicitly deferred. Per direct user instruction ("I prefer the second first"), validation/measurement rendering is priority; UI rendering is not.
- **Any decision on replacing vs. reconnecting the existing React/Canvas frontend** (`GameCanvas.tsx` et al.) — an open product/architecture question per the parent vision doc, not decided or scoped by this epic.
- **Placement-legality checks** (routed to `HardLawMonitor`) and **biome-resource content correctness** (routed to an extension of the existing `CatalogValidator`) — both explicitly out of scope for the validation consumer; any check reducing to "does field X belong to allowed-set Y" is a data-lookup check, not a visualization/geometry check, no matter how spatial it sounds.
- **Elevation-based metrics** — ruled inapplicable; this engine's terrain is a flat categorical classification with no continuous elevation field.
- **Making this a blocking gate or wiring it into a pytest/CI check.** Report-only, per direct user instruction — never tied to an actual test.
- **Automatic/scheduled triggering** — on-demand tooling only; not hooked into world-compile or simulation-run completion.
- **Seed-varied procedural world generation itself** (making world generation actually produce different terrain per seed) — this is the real dependency Scope item 3's multi-seed averaging is designed for, but it is a world-generation-side capability, not part of this rendering-validation epic. **Filed as a separate, independent epic 2026-08-21**: `TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN` — not a dependency of this epic in either direction (see Related Tickets).

## Acceptance Criteria
- [x] A documented, ordered breakdown of child tickets exists in this epic's Scope section that a later ticket-creation pass can use directly to open the child tickets listed above. **Done 2026-08-21**: `/create-tickets` investigated all 6 scope items (splitting item 2's four metric families into their own tickets) and wrote 9 real, individually-scoped tickets to `tickets/todos/world-rendering-core/`, plus a dependency-ordered `SEQUENCE.md`.
- [x] Each child ticket, when opened, references this epic in its `Related Tickets` section. Verified directly: all 9 written tickets cite `TCK-20260820-EPIC-WORLD-RENDERING-CORE`.
- [x] No implementation work happens directly on this epic ticket — epic tier tracks children only (per CLAUDE.md Tier Routing table: epic tier is "Scope only — tracks child tickets"). No code was written; this ticket and its 9 children are scope/planning artifacts only.
- [x] The two new tags (`rendering`, `visualization`) are registered in `registries/tag_registry.jsonl` before this ticket is created (done 2026-08-20 — verified below).

## Related Tickets
No pre-existing overlap was found when this epic was scoped (2026-08-20): no ticket in
`tickets/inprogress/`, `tickets/done/`, or `tickets/backlogs/` covered world-geometry rendering or
visual/geometric quality validation. `TCK-20260619-E51D-RENDERER` (done) is the
Chronicle.md/chronicle.json text renderer — a different domain (narrative markdown generation),
not spatial/PNG rendering. `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`, the one ticket
both idea docs flagged as "currently in-progress, unrelated," is confirmed DONE in `tickets/done/`
— the idea docs' "no ticket dependency" claim still holds.

**Child tickets (2026-08-21, via `/create-tickets`, `tickets/todos/world-rendering-core/`):**
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260821-VISUAL-SHAPE-METRIC
- TCK-20260821-VISUAL-DENSITY-METRIC
- TCK-20260821-VISUAL-VARIANTS-METRIC
- TCK-20260821-VISUAL-CONNECTIVITY-METRIC
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260821-VISUAL-QUALITY-CALIBRATION
- TCK-20260821-VISUAL-AGENT-REVIEW
- TCK-20260821-VISUAL-QUALITY-DOCS

**Related, independent sibling epic (2026-08-21):**
- TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN — root-causes the rectangular-biome finding this
  epic's `VISUAL-SHAPE-METRIC` child ticket measures; explicitly cross-referenced, not a
  dependency in either direction (see below).

C10 (seed-varied world generation) was investigated but deliberately NOT converted into a child
ticket of this epic — instead, per direct user instruction ("treat it as a separate epic"), it
became its own independent epic: **`TCK-20260821-EPIC-WORLDGEN-ORGANIC-TERRAIN`**
(`tickets/inprogress/`, plan doc `docs/plans/world_generation_organic_terrain_epic.md`).

**2026-08-21 follow-up investigation corrected and sharpened C10's original finding.** The C10
investigation above examined `WorldProceduralGenerator` and found zero RNG calls in its
terrain-carving code — accurate, but that class is now confirmed **dead code**: zero real call
sites anywhere in `src/`/`tools/`, only referenced by its own unit test. The actually-live
generator is `ProceduralCompositionGenerator` (`src/worldbuilding/cli.py:421`, the sole real call
site), and the real root cause traces further downstream than C10 found: real terrain content is
hand-authored as fixed-rectangle `RegionRecipeSpec` entries in `data/content/world_modules/*.yaml`
(single `terrain: str` field, no shape/noise mechanism in the schema at all), which
`WorldCompiler.compile()` (`src/worldbuilding/compiler.py:211-221`) then mechanically flat-fills
into a perfect rectangle — directly and unavoidably producing the fill-ratio finding this epic's
own `VISUAL-SHAPE-METRIC` child ticket measures. External research into Dwarf Fortress/RimWorld/
Terraria/Caves of Qud (full findings in the new epic's plan doc) confirms this project's current
fixed-geography approach is a legitimate, precedented design point (Caves of Qud does the same,
deliberately), and that Terraria's "structured randomness" pattern (fixed macro-layout + seed-varied
noise-fill within it) is a proven, additive-not-rewrite path if the new epic chooses to pursue it.

## Related Docs
- `docs/plans/world_rendering_core_epic.md` — this epic's own consolidated plan doc (Problem/Scope/Out of Scope/References), created 2026-08-20 alongside this ticket refinement.
- `docs/plans/world_generation_organic_terrain_epic.md` — the sibling epic's plan doc (2026-08-21), tracing the real root cause of the rectangular-biome finding through `RegionRecipeSpec`/`WorldCompiler`, plus external research into comparable games' world-generation approaches.
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
- **Whether seed-varied procedural world generation gets its own ticket/backlog entry** (2026-08-20) — real, wanted, future work per direct user statement, and the dependency Scope item 3's multi-seed averaging is designed for, but explicitly not decided or filed here (see Out of Scope).
- **Exact naming for the new `docs/visual_quality/`-style subfolder** (2026-08-20) — not decided; "mirrors `docs/simulation_quality/`'s shape" is the only constraint stated so far.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
