---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, faction, information, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO

## Title
Author 2 new unit-tier worlds isolating FACTION tension seeding and INFORMATION source profiles

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 found that
`faction_tension_overrides` (`FACTION` pillar) and `information_source_profiles` /
`pending_information_responses` (`INFORMATION` pillar) are populated in exactly one world today
(`urban_political`) and are both "pure content, additive, no code risk" (investigation.md §3) —
zero schema/compiler/resolver changes required, only new `world.yaml` entries plus a recompile and
recalibration run. Per the hybrid content-authoring decision (template/synthetic content OK at
unit tier), this ticket authors 2 new small unit-tier worlds, each isolating exactly ONE of these
two mechanics with everything else at baseline — the controlled-experiment counterpart to the
richer, bespoke content `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION` authors for the existing
end-to-end worlds.

## Scope
1. Author **world A** (FACTION-isolation unit world): a new small world composition (comparable in
   scale to `wilderness_survival`/`sandbox_world` per investigation.md §2's smallest-world rows,
   11-18 entities) with non-zero `faction_tension_overrides` entries on at least 2 catalog-registered
   factions actually populated in this world (mirroring `urban_political`'s
   `bandit_company: 0.5, town_council: 0.5` pattern in shape, not necessarily the same values or
   factions). Every other Pattern-6 field (`information_source_profiles`,
   `pending_information_responses`, `pending_self_model_information_events`) stays empty/default,
   and `ENABLE_BELIEF_ASSIMILATION`/`ENABLE_SELF_MODEL_COGNITION`/`ENABLE_ADVENTURE_ROUTING` stay
   OFF in its profile YAML (baseline) — this must isolate FACTION alone.
2. Author **world B** (INFORMATION-isolation unit world): a second new small world composition with
   at least 1 `information_source_profiles` entry and 1 `pending_information_responses` entry
   (mirroring `urban_political`'s `town_notice_board` guide-profile / `pop_0`/`bandit_road_danger`
   pattern in shape), plus `ENABLE_BELIEF_ASSIMILATION: "ON"` in its profile YAML (per
   investigation.md §3: "seeding profiles without turning the flag on produces zero signal" — both
   must be seeded together for the mechanic to be observable). Every other Pattern-6 field stays
   empty/default and `faction_tension_overrides` stays at catalog default (0.0 for all factions) —
   this must isolate INFORMATION alone.
3. Template/synthetic content is acceptable for both worlds per the hybrid decision — narrative
   coherence is not a goal here, isolating the mechanic is.
4. Compile both worlds (`python -m src.worldbuilding.cli resolve <world>` +
   `compile --seed <seed> --from-resolved`), verify `world_compile_report.json` shows 0 warnings,
   and verify population stability (>=60% alive floor through at least 200-300 ticks, following the
   verification pattern `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` established).
5. Run a 3-seed calibration matrix (seeds 42/123/456, following the existing corpus pattern) for
   each world and add grade-anchor entries to `tests/simulation_quality/fixtures/grade_anchors.json`
   / `FAST_ANCHOR_KEYS` in `test_grade_regression.py`, mirroring
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`'s Step 4 anchoring pattern.
6. Confirm world A's FACTION pillar grade shows genuine non-C signal (or document honestly if it
   does not — this is real diagnostic data) and world B's INFORMATION pillar likewise.
7. Update `docs/simulation_quality/eval_matrix_results.md` with both worlds' grade tables, tagged as
   unit-tier per `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s taxonomy.
8. Run `make evaluate --dry-run` (0 regressions on existing corpus) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Authoring self-model/Branch B content (that is
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`)
- Authoring an AGENCY-isolation world (that is `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`)
- Adding bespoke FACTION/INFORMATION content to any existing end-to-end-tier world (that is
  `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`)
- Expanding `data/content/social/faction_relationships.yaml`'s global density (that is
  `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`)
- Fixing any pillar scoring/emission bug discovered while authoring these worlds — file a follow-up
  ticket instead, per the pattern established in `TCK-20260703-SIMQ-UPLIFT3-PLAYBOOK-DOC`

## Acceptance Criteria
- [ ] World A exists, compiles with 0 warnings, has >=2 non-zero `faction_tension_overrides`
      entries, and has every other Pattern-6 field empty/default
- [ ] World B exists, compiles with 0 warnings, has >=1 `information_source_profiles` entry, >=1
      `pending_information_responses` entry, `ENABLE_BELIEF_ASSIMILATION: "ON"` in its profile YAML,
      and every other Pattern-6 field empty/default
- [ ] Both worlds verified population-stable (>=60% alive floor) through at least 200-300 ticks at
      seed 42
- [ ] Both worlds have 3-seed grade-anchor entries in `grade_anchors.json` and
      `FAST_ANCHOR_KEYS`
- [ ] World A's FACTION grade and world B's INFORMATION grade are documented honestly in
      `eval_matrix_results.md`, whatever they turn out to be
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions on the pre-existing corpus
- [ ] `make knowledge-index-update` run if `docs/` files changed

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines the unit-tier criteria these worlds must meet
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — should be recompiled with the new
  `distinct_populated_factions` field once that ticket lands, if sequenced after
- TCK-20260702-SIMQ-UPLIFT2-FACTION — prior single-world FACTION activation this ticket's world A
  generalizes the pattern from
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — precedent for compile/verify/anchor workflow this ticket
  follows

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory, FACTION/INFORMATION rows) and §3 (blast-radius: "pure content, additive, no code risk")
- `docs/guidelines/design_patterns.md` — Pattern 6
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — reference for how
  `faction_tension_overrides` was first seeded in `urban_political`
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — compile/verify/anchor workflow
  reference

## Related Code Areas
- `src/worldbuilding/schema.py:52` (`FactionSpec.initial_tension_level`), `:226-227`
  (`information_source_profiles`, `pending_information_responses`)
- `src/worldassembly/schema.py:40,44,48,168,172,176` — composition-level mirrors
- `data/worlds/urban_political/world.yaml` — reference pattern for both fields
- `config/simulation_quality/profiles/urban_political.yaml` — reference `feature_flags:` pattern
- `tests/simulation_quality/fixtures/grade_anchors.json`,
  `tests/simulation_quality/test_grade_regression.py`

## Assumptions / Open Questions
- UQ-1: Should the two new worlds reuse existing catalog factions/module content (faster, lower
  risk) or introduce any new content? Default to reusing existing catalog content exclusively —
  matches the "template/synthetic content OK" unit-tier philosophy and avoids new catalog-ID
  registration risk.
- UQ-2: Exact naming for the two new world directories under `data/worlds/` is left to the
  implementer — should be self-descriptive (e.g. `unit_faction_tension`, `unit_information_source`)
  and consistent with the taxonomy doc's naming guidance if
  `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` establishes one.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
