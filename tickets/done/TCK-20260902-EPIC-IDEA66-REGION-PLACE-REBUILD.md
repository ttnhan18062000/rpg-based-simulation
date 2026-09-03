---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
phase: done
date: 2026-09-02
tags: [content, determinism]
---

# TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

## Title
Region/Place foundational rebuild (idea 66) — epic, promoted from plan doc

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Promotes `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (already a complete,
field-level plan) into a tracked epic. Today `RegionState.bounds` is a single rectangular box and
world-module content contributes flat sibling regions with zero containment — a City *is* one Region
rather than a Place *inside* a Region. This epic replaces that model: `Place` becomes the atomic
point-of-interest object, positioned within a Region's (larger) bounds, and a Region can hold zero or
many Places. This subsumes ideas 45 (Camp), 46 (Nest), and 47 (Lair) as `Place` kinds, and fixes the
previously-unassigned Ruins/Mines/Battlefields content gap (`RUIN`/`DUNGEON` kind). It directly informs
idea 35's sovereignty wiring (territory-level default, per-Place override).

This is the clearest concrete implementation gate remaining from this session's design/architecture
investigation — no open architectural question blocks it (the plan doc's own membership-index question
is the one thing that must be resolved before child tickets are cut, see Acceptance Signal below).

## Scope
Full detail lives in the plan doc — not duplicated here. Six work areas, expected to become separable
child tickets:
1. Schema migration (`PlaceState`/`PlaceKind`, `RegionState.places: List[str]`).
2. Resolve the membership-index open question (List-only vs. per-entity `place_id` back-reference) —
   **must be decided before any child ticket starts**, per the plan doc's own Acceptance Signal.
3. `WorldCompiler` wiring (`src/worldbuilding/compiler.py` — confirmed sole production construction site).
4. Two-stage pilot: Stage A (`unit_information_source`, 1 region/1 Place, byte-identical `state_hash`
   expected) → Stage B (`hero_guild_routing`, 4 non-uniform regions) → remaining 19 worlds.
5. `state_hash`-first recalibration across all 21 worlds/84 `run_keys`, with per-world triage notes for
   any hash that changes.
6. Downstream unblocking record for ideas 35, 45, 46, 47, 48 (each keeps its own ticket).

## Out of Scope
- Actually implementing ideas 35, 45, 46, 47, 48, or 61 — each gets its own ticket once this rebuild
  lands and unblocks it.
- A `Country`-tier entity (confirmed out of scope by M8's own investigation — sovereignty is
  region-level/faction-based, not a new entity kind).
- Authoring new gameplay content inside the new Place kinds.
- Idea 48's place-type transition *mechanic* (reuses `TransformationService`'s existing threshold table;
  only `Place.kind` becoming a real migrated field is in scope here).
- Coordination with the concurrent M3 core-RPG implementation session — this epic's scope is narrowly
  gated (per the plan doc's own Gate note) to M2's ideas 35/48 and M4's place-shaped branch (44-47, 61);
  it does not block or overlap M3's scope, and child tickets should confirm no live M3 conflict on
  `src/worldbuilding/compiler.py` or `src/worldbuilding/schema.py` before starting.

## Acceptance Criteria
- [x] Membership-index open question is decided and recorded — dual-sided membership (`RegionState.places`
      list + cached `place_id` back-reference), see plan doc "Membership-index decision" section.
- [x] Child tickets created (5, sequenced) — see Related Tickets above.
- [x] Stage A pilot lands with a byte-identical `state_hash` to its committed baseline (or an explained,
      accepted hash change) before Stage B starts. **Explained hash change**: `state_hash`
      (`StateFingerprinter`) was found blind to Place data entirely; `canonical_state_hash`
      (`CanonicalStateHasher`, added to the compile report specifically for this purpose) changed as
      expected for real new Place data, verified isolated to `regions`/`places` only via direct
      canonical-dict diffs.
- [x] All 21 worlds pass through the recalibration procedure with recorded triage notes. Done in
      `TCK-20260902-PLACE-MIGRATION-RECALIBRATION`: all 21 worlds' `canonical_state_hash` triaged as
      compile-shape (not a regression); separately, a full 81-run_key `grade_anchors.json` sweep found
      61/81 drifted, causally isolated via a revert-and-rerun control test and confirmed unrelated to
      this epic's changes (pre-existing fixture staleness, tracked in
      `TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`).
- [x] Downstream idea 35/48 (M2) and 44-47/61 (M4) tickets can cite this epic's landed state as their
      unblocking dependency. All 21 worlds now carry real `Place` data (`CITY`/`CAMP`/`RUIN`, plus
      deliberate empty-wilderness cases where no real anchor exists) with full canonical-hash coverage —
      the schema and content foundation these downstream ideas depend on is landed.

## Related Tickets
Child tickets (created 2026-09-02, sequenced 1→5):
1. TCK-20260902-PLACE-SCHEMA-MIGRATION
2. TCK-20260902-WORLDCOMPILER-PLACE-WIRING
3. TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT
4. TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT
5. TCK-20260902-PLACE-MIGRATION-RECALIBRATION (runs alongside/after child 4, per-world)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (full plan — this ticket's
  primary source, not duplicated)
- `docs/brainstorm/rpg_feature_atlas.html` idea 66
- `docs/brainstorm/rpg_expected_schemas.html#schema-66`
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` item 9
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` item 2

## Related Stored Artifacts
(none — the plan doc itself serves as this epic's investigation/plan artifact; per-child-ticket staging
artifacts to be created when each child ticket is scoped)

## Related Code Areas
- `src/worldbuilding/schema.py` (`RegionSpec`, new `PlaceState`/`PlaceKind`)
- `src/worldbuilding/compiler.py` (`WorldCompiler.compile()`)
- `data/content/world_modules/*.yaml`
- `docs/brainstorm/rpg_expected_schemas.html#schema-66`

## Assumptions / Open Questions
- Membership-index shape (List-only vs. per-entity `place_id` back-reference) — the plan doc points to
  `ClanState` membership as prior art to check before re-deriving.
- Whether the `grade_anchors.json` tolerance band re-run across all 84 `run_keys` should be budgeted as
  part of this epic's own scope or split into a dedicated follow-up ticket once the scale of triage work
  is known after Stage B.

## Implementation Notes
All 5 child tickets landed across two PRs: child 1 (`TCK-20260902-PLACE-SCHEMA-MIGRATION`) merged
separately via #113; children 2-5 (`TCK-20260902-WORLDCOMPILER-PLACE-WIRING`,
`TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT`, `TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT`,
`TCK-20260902-PLACE-MIGRATION-RECALIBRATION`) landed together on branch `worldcompiler-place-wiring`
(PR #117, all CI checks green). `Place` is now a real, atomic point-of-interest object positioned within
a Region's bounds, wired through both the Direct and Composition compilation paths, with dual-sided
membership (`RegionState.places` + cached `place_id` back-reference), full canonical-hash coverage, and
real content across all 21 worlds (`CITY`/`CAMP`/`RUIN` kinds, plus deliberate empty-wilderness cases
where no real anchor exists in the source content). Two real findings surfaced and handled during
implementation rather than deferred: `state_hash`'s blindness to Place data (fixed by adding
`canonical_state_hash`/`place_count` to the compile report) and two independent stale-fixture gaps
(`world_compile_report.json`, resolved as a side effect of Stage B's batch pass; `grade_anchors.json`,
still open, causally proven unrelated to this epic and tracked in
`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS` for future human-reviewed regeneration).

## Test Summary
Aggregate across all 5 child tickets: 11 new unit/regression tests
(`tests/unit/worldbuilding/test_place_wiring.py`, `tests/unit/worldassembly/test_resolver.py`,
`tests/unit/worldbuilding/test_world_compiler.py`), 1 existing certification test's exact-key-set
assertion updated, a full ~895-test regression sweep across worldbuilding/worldassembly/worldmodules/
core/engine/kernel/certification (0 failed), a 21/21-world batch resolve+compile pass, and a full
81-run_key `grade_anchors.json` sweep with a causal-isolation control test proving no regression from
this epic. PR #117's CI (all lanes, including Simulation quality) is green.

## Files Changed
See each child ticket's own Files Changed section for the full per-file breakdown. Summary: schema
(`src/core/state.py`, `src/worldbuilding/schema.py`, `src/worldbuilding/recipe.py`), wiring
(`src/worldassembly/resolver.py`, `src/worldbuilding/compiler.py`), content (6 shared
`data/content/world_modules/*.yaml` files), all 21 worlds' `world_compile_report.json`/`resolved/`
assets, plus tests, docs (`docs/world/compiler_contract.md`), and parity ledger entries
(`SUB-389`-`SUB-392`).

## Completion Summary
Idea 66's Region/Place foundational rebuild is fully landed: all 5 child tickets complete, zero real
regressions found across the entire migration. This directly unblocks ideas 35 (sovereignty wiring),
45/46/47 (Camp/Nest/Lair as `Place` kinds), and 48 (place-type transitions) — each retains its own
ticket for implementation, but the schema/content/compiler foundation they depend on now exists and is
verified. One follow-up ticket remains open from this work
(`TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS`, `grade_anchors.json` half), tracked separately
since it is a pre-existing fixture-maintenance gap unrelated to this epic's own changes, not a blocker
to closing this epic.
