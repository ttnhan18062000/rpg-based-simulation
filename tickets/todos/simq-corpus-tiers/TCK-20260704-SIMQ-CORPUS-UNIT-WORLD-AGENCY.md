---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, agency, adventure, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY

## Title
Author 1 new real-scale unit-tier world with ENABLE_ADVENTURE_ROUTING ON by design

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that
`simq_routing_test` — the only world with AGENCY-active behavior today — is explicitly authored as
a "minimal calibration/test world," not a world representing a shipped gameplay archetype
(investigation.md §2, "A routing-capable (AGENCY-active) world that is also a 'real' gameplay
archetype" gap). Per the user's AGENCY decision, this ticket authors 1 new world at a "real"
scale/archetype (not calibration-minimal) with `ENABLE_ADVENTURE_ROUTING` ON from inception, using
the generalized `feature_flags:` profile mechanism `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`
introduces. **This ticket does NOT reverse `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing
world** — the 9 non-routing worlds keep AGENCY=C, permanently, per that ruling. This is a new
archetype category ("routing-capable, real-scale") added alongside "routing-inactive" and
"routing-test-only," not a reinterpretation of any existing world's archetype-correctness.

## Scope
1. Confirm `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` has landed (hard dependency — this
   ticket needs the generalized `feature_flags:` mechanism, not a new hardcoded scenario-name
   special case in `evaluate_simq.py`).
2. Author a new world composition at a scale comparable to the existing mid-size real archetypes
   (investigation.md §2: `urban_political` 30 entities/3 regions, `dungeon_crawl` 32/4 — not
   `simq_routing_test`-minimal, and not as large as `frontier_extended`'s 56/10). Per
   investigation.md §3, `urban_political` already has a `hero_guild` faction population (4 entities)
   framed around adventuring, so a `hero_guild`-centric archetype is not architecturally foreign —
   this new world should have an explicit adventuring/route-selection framing in its description
   (unlike `dungeon_crawl`'s "pure dungeon exploration" or `urban_political`'s "settlement-heavy...
   trade pressure," neither of which mentions adventuring/routing per investigation.md §3).
3. Set `ENABLE_ADVENTURE_ROUTING: "ON"` in this world's own
   `config/simulation_quality/profiles/<world>.yaml` `feature_flags:` block (using ticket 3's
   generalized mechanism) — this world carries the flag ON by design from its first compile, not
   toggled on after the fact.
4. Compile the world, verify 0 warnings, verify population stability (>=60% alive floor) through
   200-500 ticks (matching `simq_routing_test`'s 500-tick calibration length as a reasonable
   default for an AGENCY-focused world, since route/goal-selection dynamics may need more ticks
   than the 200-tick default to show signal).
5. Run a 3-seed calibration matrix and add grade-anchor entries. Document the resulting AGENCY grade
   (expect B/A given `simq_routing_test`'s precedent of B/A with the same flag, but do not assume —
   verify and report the actual grade).
6. Update `docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design Note
   (added by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) to add this new world as a second
   routing-capable archetype, explicitly distinguishing it from both the "9 non-routing worlds stay
   AGENCY=C" ruling and from `simq_routing_test`'s calibration-only purpose.
7. Run `make evaluate --dry-run` (0 regressions on pre-existing corpus, including
   `simq_routing_test`'s own anchors which ticket 3 already protected) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Reversing `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for `urban_political`, `dungeon_crawl`, or any of
  the other 7 existing non-routing worlds — none of them change AGENCY grade as a result of this
  ticket
- Building the generalized flag mechanism itself (that is
  `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`, a hard dependency of this ticket)
- Seeding FACTION/INFORMATION/self-model content into this world (keep this world isolated to the
  AGENCY mechanic per unit-tier philosophy, unless investigation finds a compelling archetype
  reason a `hero_guild`-framed world also needs e.g. faction tension — default to isolation unless
  justified)

## Acceptance Criteria
- [ ] `TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE` confirmed landed before this ticket's
      implementation begins
- [ ] New world exists at real-archetype scale (comparable to `urban_political`/`dungeon_crawl`,
      not `simq_routing_test`-minimal), with an explicit adventuring/route-selection archetype
      framing in its description
- [ ] `ENABLE_ADVENTURE_ROUTING: "ON"` set via this world's own profile YAML `feature_flags:` block
      (not a harness-level special case)
- [ ] World compiles with 0 warnings, verified population-stable (>=60% alive floor) through
      200-500 ticks
- [ ] 3-seed grade-anchor entries added; actual AGENCY grade documented honestly (not assumed)
- [ ] `eval_matrix_results.md`'s AGENCY Cross-World Design Note updated to reflect this new
      routing-capable archetype without altering its existing "9 non-routing worlds stay C" language
- [ ] None of the 9 existing non-routing worlds' AGENCY grades change
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE — **hard dependency**; this ticket cannot start
  implementation until that mechanism exists
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — the ruling this ticket explicitly does NOT reverse for any
  existing world
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines unit-tier criteria this world should meet

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 ("A
  routing-capable (AGENCY-active) world that is also a 'real' gameplay archetype" gap) and §3
  ("`ENABLE_ADVENTURE_ROUTING` / AGENCY broadly" — middle-ground option analysis)
- `docs/simulation_quality/eval_matrix_results.md` — existing AGENCY Cross-World Design Note

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA/` — the DA ruling this ticket must remain
  consistent with

## Related Code Areas
- `config/simulation_quality/profiles/<new-world>.yaml` — new profile file, `feature_flags:` block
- `src/domains/optimization/feature_flags.py:16` — `ENABLE_ADVENTURE_ROUTING`
- `src/domains/adventure/phase.py` — `AdventureDecisionPhase` (not modified, only exercised)
- `data/content/social/factions.yaml` — `hero_guild` faction, if reused for this world's population
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: Exact tick count for this world's calibration matrix — default to 500 (matching
  `simq_routing_test`'s existing calibration length) unless investigation finds a stronger reason
  to use the corpus's more common 200-tick default.
- UQ-2: World name — should be self-descriptive of its routing-capable archetype (e.g.
  `hero_guild_routing`, `adventurers_crossing`) and should not collide with `simq_routing_test`'s
  existing "test world" framing, since this world is explicitly meant to read as a real archetype,
  not a calibration harness fixture.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
