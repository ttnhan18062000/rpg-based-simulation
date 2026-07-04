---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation_quality, world-content, faction, information, end-to-end-tier, calibration]
---

# TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION

## Title
Author bespoke, archetype-matched FACTION and INFORMATION content into existing end-to-end worlds

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 found FACTION
tension seeding and INFORMATION source profiles populated in exactly 1 of 10 worlds
(`urban_political`) — the direct answer to "why does only urban_political have this content" is
that no one has authored it elsewhere yet, not an architectural constraint (investigation.md §3:
"pure content, additive, no code risk" for both mechanics). Per the hybrid content-authoring
decision, this ticket authors **bespoke, archetype-matched** content (not templated/copy-pasted
from `urban_political`) into the 8 remaining end-to-end-tier worlds: `dungeon_crawl`,
`sandbox_world`, `wilderness_survival`, `highland_traverse`, `swamp_border_world`,
`frontier_living_world`, `frontier_extended`, `generated_frontier_3_42`.

Per investigation.md §4 open question 2, this must respect each world's actual archetype — e.g.
`wilderness_survival`'s "no settlement" framing may make an `urban_political`-style
`town_notice_board` information source archetypally wrong there. This is per-world judgment work,
not a mechanical stamp-and-repeat.

## Scope
1. For each of the 8 worlds, read its existing `world.yaml` description/archetype framing and
   populated-faction list (investigation.md §2 table) before authoring anything.
2. For **FACTION tension seeding**: for each world, judge which of its actually-populated factions
   (per investigation.md §2's per-world faction list) have an archetypally plausible tension
   relationship, and seed `faction_tension_overrides` accordingly (e.g. `dungeon_crawl`'s
   `bandit_company`/`goblin_warband`/`undead_remnants`/`wild_beast_pack` populate a hostile-dungeon
   archetype very differently from `swamp_border_world`'s `merchant_league`/`swamp_tribe`/
   `town_council`/`wild_beast_pack`). Do not copy `urban_political`'s exact faction/value pairs into
   worlds where those factions are not even populated.
3. For **INFORMATION source profiles**: for each world, judge whether an information-source
   archetype fits at all (a `town_notice_board`-style guide profile presumes a settlement;
   `wilderness_survival`'s "no settlement" framing may call for a different profile shape entirely,
   or may justify explicitly skipping this world for INFORMATION content if no archetype-honest fit
   exists — document that judgment call rather than forcing content in). Where a fit exists, author
   `information_source_profiles` and `pending_information_responses` content matched to that
   world's own population and archetype.
4. Where `information_source_profiles` content is seeded, also add
   `ENABLE_BELIEF_ASSIMILATION: "ON"` to that world's profile YAML `feature_flags:` block (per
   investigation.md §3: seeding profiles without the flag produces zero signal).
5. Recompile every touched world and verify 0 warnings.
6. **Re-verify existing calibration anchors with the same discipline
   `TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS` Step 4a used**: for every world touched, diff its full
   existing `grade_anchors.json` entries against a fresh calibration run and update any drifted
   entries in place, with the drift attributed and documented (do not silently assume `make
   evaluate`'s dry-run diff alone catches content-driven grade drift — it only compares against
   already-committed anchors, so a stale anchor combined with a changed world will show as a
   "regression" unless the anchor itself is refreshed first).
7. Update `docs/simulation_quality/eval_matrix_results.md` with the new FACTION/INFORMATION grades
   for all 8 worlds and any anchor updates from step 6.
8. Run `make evaluate --dry-run` after anchors are refreshed (0 regressions) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Authoring new worlds (that is tickets 4-6, 8 in this batch) — this ticket only extends the 8
  existing end-to-end worlds' content
- Self-model/Branch B or AGENCY content in these 8 worlds — explicitly not part of this ticket's
  scope (self-model has its own dedicated pilot ticket; AGENCY stays OFF in all 9 non-routing
  worlds per the DA ruling)
- Fixing any pillar scoring/emission bug discovered during this pass — file a follow-up ticket
- Expanding `data/content/social/faction_relationships.yaml`'s global density (that is
  `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`, though its results will make more of this
  ticket's new tension pairs meaningfully differentiated once it lands)

## Acceptance Criteria
- [ ] Each of the 8 worlds has a documented per-world judgment call recorded (in this ticket's
      Implementation Notes) for both FACTION and INFORMATION content — including any world where the
      judgment was "no archetype-honest fit, skip this mechanic for this world"
- [ ] `faction_tension_overrides` content authored only uses factions actually populated in that
      world (per investigation.md §2's faction list per world) — no non-populated-faction entries
- [ ] Where `information_source_profiles` is seeded, `ENABLE_BELIEF_ASSIMILATION: "ON"` is also set
      in that world's profile YAML
- [ ] All touched worlds recompile with 0 warnings
- [ ] Every existing `grade_anchors.json` entry for a touched world is re-verified against a fresh
      calibration run; any drift is documented and the anchor updated (not silently left stale or
      silently assumed unaffected)
- [ ] `docs/simulation_quality/eval_matrix_results.md` updated with new FACTION/INFORMATION grades
      for all 8 worlds
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions after anchor refresh

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines end-to-end-tier's bespoke-content requirement
- TCK-20260702-SIMQ-UPLIFT2-FACTION — original single-world (`urban_political`) FACTION activation;
  reference for the mechanism, explicitly not for the exact content values
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — established the drift-check-and-update discipline this
  ticket must reuse (Step 4a pattern)
- TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS — global relationship-density work that makes this
  ticket's new tension pairs more meaningfully differentiated once it lands

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §1 (mechanic
  inventory), §2 (per-world faction/scale table), §3 (blast radius), §4 open question 2
  (bespoke-vs-template authoring tradeoff)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — drift-check discipline reference
  (Step 4a)
- `stored_artifacts/TCK-20260702-SIMQ-UPLIFT2-FACTION/` — original FACTION mechanism reference

## Related Code Areas
- `data/worlds/{dungeon_crawl,sandbox_world,wilderness_survival,highland_traverse,
  swamp_border_world,frontier_living_world,frontier_extended,generated_frontier_3_42}/world.yaml`
- `config/simulation_quality/profiles/` — new/edited per-world profile YAMLs
- `src/worldbuilding/schema.py:52,226,227`
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: For worlds where no archetype-honest INFORMATION fit exists (e.g. potentially
  `wilderness_survival`), is "skip this mechanic for this world, document why" an acceptable
  outcome, or must every world get some INFORMATION content regardless? Default to "skip and
  document" — per investigation.md §4 open question 2's own framing, forcing content everywhere
  risks the "generic content stamped everywhere" outcome the SimQ Uplift batches originally avoided.
- UQ-2: Order of authoring across the 8 worlds is left to the implementer; no cross-world
  dependency exists (each world's content is independent), but the drift-check step (Scope item 6)
  should be done per-world immediately after that world's content lands, not batched at the end,
  to keep attribution clear.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
