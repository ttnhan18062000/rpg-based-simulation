---
status: active
layer: world
authority: P1
audience: agent
tags: [rendering, visualization, world, simulation-quality, architecture, determinism]
---

# Epic Plan — Server-Owned World Rendering Core, with Visual/Geometric Quality Validation as First Consumer

**Tracking ticket:** `TCK-20260820-EPIC-WORLD-RENDERING-CORE`
**Source:** `docs/plans/world_rendering/idea_world_rendering_core.md`, `docs/plans/world_rendering/idea_world_render_validation.md`, `experiments/spatial_rendering/PROPOSAL.md` (full 530-line investigation trail, 7 committed prototype scripts)
**Priority:** P1 — user-prioritized; validation/measurement rendering explicitly before player-facing UI rendering.

## Problem

No canonical way exists for this project's backend to render a world to an image, for any purpose. Two converging gaps: the live frontend calls 5 backend routes that don't exist at all (confirmed dead, still true as of 2026-08-20); and no mechanism exists to answer "does this generated world look geometrically reasonable" — SimQ's 10 pillars are exclusively event-stream-driven with zero spatial/geometric coverage. A real corpus sweep already found a live, non-hypothetical defect this gap hides: 78.8% of measured biome components across all 18 worlds score ≥0.95 bounding-box fill-ratio (near-perfectly rectangular, not organic), including one exact case of a biome component being another one rotated 90°.

## Scope for the eventual `create-tickets` pass

Child tickets, in dependency order (not created yet — this epic is scope-only):

1. **Core batch/QA renderer** (prerequisite for everything below). Deterministic PNG generation from `AuthoritativeState`, `DirtySet`-incremental caching, `data/runs/{run_id}/renders/` storage reusing the existing `RetentionPolicy`. Golden-hash regression test (render determinism already proven bit-identical via SHA256, three independent runs).
2. **Four validation metric families**, promoted from `experiments/spatial_rendering/prototype/`'s already-tested code, not redesigned: Shape (connected-component-aware fill-ratio + rotation/repetition detection), Density (entity nearest-neighbor CV + terrain histogram), Variants (trail-activity liveliness + cross-*spec* diversity via total-variation-distance), Connectivity (whole-map walkable-region reachability).
3. **Sibling scoring/grade-band system** — reuses SimQ's exact S/A/B/C/D/F thresholds, architecturally independent (computes from `AuthoritativeState` geometry directly, no event to hang off). Structured as **hard rules** (binary geometric facts), **soft rules** (gradient quality signals with a healthy band, not monotonic — unlike most of SimQ's signals), and **scoring rules** (how hard+soft combine into a grade) — mirrors the deterministic, non-visual-model-first measurement philosophy SimQ itself uses for its own event-driven signals. Actual image-based agent review (Tier 2, see item 5) is the escalation path, never the default measurement mechanism.
   - **Multi-seed averaging is a core part of this system's design**, not an add-on: a world spec's score is the average across multiple seeds' renders of that spec, anticipating that world generation will eventually produce seed-varied maps. **Known current limitation, verified not assumed**: terrain/biome layout is presently deterministically *fixed* per world spec — byte-identical across seeds 42/137/999 (only entity placement/behavior currently varies by seed). Multi-seed averaging will be correct but a no-op (averaging identical values) until world generation itself becomes seed-varied — that capability is explicitly **out of scope for this epic** (see Out of Scope), a world-generation-side concern, not a rendering-validation one. Build the averaging mechanism now regardless, so it activates correctly the moment that dependency lands.
4. **Multi-seed / multi-world threshold calibration** — mirrors `tools/calibrate_simq.py`'s real precedent. None of the four metric families have multi-seed-calibrated healthy-band thresholds yet.
5. **Agent-review pipeline** — Tier 0 (pure data, zero image, the deterministic hard/soft/scoring-rule path from item 3 — primary and default) → Tier 1 (compact JSON digest) → Tier 2 (actual image, fetched only on escalation, annotated/gridlined by default for citable coordinates). Includes the open question of a new `.claude/agents/world-render-reviewer.md` subagent vs. folding into an existing one.
6. **Documentation deliverables**, explicitly requested, structured to mirror SimQ's own precedent exactly:
   - A new `docs/visual_quality/` subfolder (naming TBD at implementation time — mirrors `docs/simulation_quality/`'s shape: a scoring contract doc equivalent to `quality_scoring_contract.md`, a current-state doc, a calibration/audit-workflow doc equivalent to `audit_workflow.md`) — the living reference for this system's hard/soft/scoring rules and calibration state.
   - A new periodic audit dimension entry under `docs/audits/` — **next available number is D26** (confirmed 2026-08-20: D25 was claimed same-day by an unrelated concurrent ticket, `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`) — mirroring the relationship `docs/audits/D20_simq_integration.md` already has to `docs/simulation_quality/`: a periodic audit *of* the visual-quality system's own health/coverage, distinct from the live scorer's own on-demand output.

This epic tracks the breakdown above; it does not commit to exact child-ticket IDs or create them.

## Out of Scope

- **Live-streaming/multi-device rendering mode** — deferred in full per the parent vision doc's own "Option C" architecture.
- **Player-facing frontend reconnection** — fixing the 5 missing backend routes `useSimulation.ts` calls. Per direct user priority: validation/measurement rendering first, UI rendering not now.
- **Any decision on replacing vs. reconnecting the existing React/Canvas frontend.**
- **Placement-legality checks** (routed to `HardLawMonitor`, already shipped) and **biome-resource content correctness** (routed to an extension of the existing `CatalogValidator`) — any check reducing to "does field X belong to allowed-set Y" is a data-lookup check, not a geometry check, no matter how spatial it sounds.
- **Making this a blocking gate or a wired pytest/CI check.** Explicitly report-only per direct user instruction — same posture as SimQ's own scores today, not tied to an actual test.
- **Automatic/scheduled triggering.** On-demand tooling only, run when needed — not hooked into world-compile or simulation-run completion.
- **Seed-varied procedural world generation itself** (i.e., making world generation actually produce different terrain per seed). This is the real dependency multi-seed averaging (item 3) is designed for, but it is a `src/worldgeneration/`-side capability, not part of this rendering-validation epic. **Flagged, not filed**: no separate ticket/backlog entry exists yet for this world-generation capability — worth a deliberate decision on whether to open one, not assumed here.

## Acceptance Signal for This Epic (not yet broken into child tickets)

- A documented, ordered child-ticket breakdown exists (done, above) that a later ticket-creation pass can use directly.
- Each child ticket, when opened, references this epic and this plan doc.
- No implementation happens directly on the epic ticket or this plan doc — both are scope/planning artifacts only.

## References

- `docs/plans/world_rendering/idea_world_rendering_core.md` — full architecture, benchmarked performance, drawing-tool options.
- `docs/plans/world_rendering/idea_world_render_validation.md` — full metric-family detail, corpus findings, scoring design, agent-review pipeline.
- `experiments/spatial_rendering/PROPOSAL.md` + `experiments/spatial_rendering/prototype/` — the complete investigation trail and 7 already-executed, already-committed prototype scripts this epic's child tickets promote from.
- `docs/simulation_quality/` (`quality_scoring_contract.md`, `audit_workflow.md`, `current_state.md`, ...) — the structural precedent item 6's new `docs/visual_quality/` subfolder mirrors.
- `docs/audits/D20_simq_integration.md` — the structural precedent for item 6's new periodic audit-of-the-system entry (next number: D26).
- `tools/calibrate_simq.py` — the real multi-seed/multi-world calibration precedent item 4 mirrors.
