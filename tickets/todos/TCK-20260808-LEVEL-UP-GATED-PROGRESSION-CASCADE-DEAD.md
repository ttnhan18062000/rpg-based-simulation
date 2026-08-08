---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD
phase: open
date: 2026-08-08
tags: [progression, combat, simulation-quality]
---

# TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD

## Title
Skill unlocks, AP spending, non-HERO attribute growth, and species evolution are ALL gated behind
`levels_gained > 0` in `EvolutionSystem` — since `level_up` never fires in real gameplay, this is
a confirmed-shared-cause dead gameplay cascade, not just a dormant scoring signal

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**Scope narrowed 2026-08-08** (was originally bundled with 2 other, unconfirmed-to-share-this-cause
leads — split out into their own tickets after user review, see `## Related Tickets`): this ticket
covers only the events directly, confirmedly traced to one real shared root cause.
`item_equipped`'s own separate/independent producer investigation is now
`TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`; `trait_expressed`/`pillar_trait_unlocked`'s
entirely-untraced producer investigation is now
`TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`. Bundling those into this ticket was a
mistake — I had explicitly flagged them as *unconfirmed* to share this cause, and stacking
unconfirmed, independent leads into one ticket contradicts the very reasoning I used to justify
bundling the confirmed ones together in the first place.

Per the user's own explicit direction to prioritize the `GROWTH_PROGRESSION` zero-triggered events
found in `docs/audits/D21_entity_lifecycle_foundation_layers.md`, traced each event's real producer
code directly.

**Real, decisive, confirmed finding**: `src/engine/evolution.py`'s entire level-up reward block
(lines ~87-134) is gated behind a single condition, `if levels_gained > 0:`. Since real gameplay
confirms `level_up` essentially never fires (real kill rate ~13-21x too low relative to the
XP/stall-detection cadence, per `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`), **the
entire block never executes**, meaning in real gameplay:

- `learned_skills` never grows (`LevelingService.get_unlocked_skills(lvl)` never called) →
  `skill_unlocked` never fires — confirmed real producer, confirmed real gate.
- `unspent_ap_delta` never increases (nothing to spend) → `progression_conversion_applied` never
  fires (it fires on `unspent_ap` *decreasing*, but it can't decrease from zero).
- Non-HERO attribute growth (`vitality_delta`/`strength_delta`/`endurance_delta`, the `else`
  branch at line ~125-132) never applies — a real, confirmed contributing cause of
  `attribute_changed` never firing (`attribute_changed`'s own emitter is a general diff, so other
  real attribute-mutation sources should still be checked in Investigate — don't assume this is
  the *only* cause of `attribute_changed`'s dormancy, only a confirmed contributing one).
- Species evolution (`_get_evolved_kind`, the 10/25/50-level thresholds, and its own
  evolution-triggered gear upgrade at lines ~103-109) never triggers — real code for what would
  functionally be "class breakthrough"/"power up," dead in practice. This is one real, confirmed
  contributing cause of `item_equipped`'s dormancy too, but **not the only one** — see the split-out
  ticket for the other, independent equip-producing paths.

**Relationship to the existing, already-filed `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`**
(P3, standard, OPEN): that ticket frames the problem as a *scoring-detector cadence mismatch*
(`capability_growth_stalled` re-firing every 300 ticks vs. real kill rate) — a narrower framing
whose candidate fixes (lengthen the stall-detector window, or raise kill frequency) are about
making the **score** read correctly. This ticket's own finding is broader and more consequential:
even if the score were made to read correctly, the underlying **gameplay** — skills, AP, attribute
growth via leveling, and species evolution — genuinely never happens for real entities, independent
of how the score is computed. Raising real kill frequency (that sibling ticket's own "lever 1")
would likely fix both; lengthening the stall-detector's cadence (that ticket's "lever 2") would fix
the score reading without touching this ticket's own real gameplay-dead-code finding at all. **This
is exactly the kind of scoping decision to raise with the user before Plan, not decide
unilaterally** — see `## Assumptions / Open Questions`.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the real XP curve: how many levels a real entity would need to gain, and how much
     real XP that requires, versus real observed XP accumulation rates (cite
     `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own real numbers, extend if
     needed).
   - Confirm whether `attribute_changed` has any other real producer beyond `evolution.py`'s
     level-gated non-HERO branch (training system, item-stat-bonus system, etc.) — don't assume
     zero without checking.
   - Re-check `TCK-20260701-SIMQ-EMIT-PROGRESSION`'s own AC claim that a 200-tick `dungeon_crawl`
     run produced real `skill_unlocked` events at the time — confirm whether that was a
     narrow/synthetic test scenario (e.g. hand-crafted starting level) vs. a genuine regression
     since 2026-07-01.
2. **Plan**: coordinate explicitly with `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`
   once the user has decided the scoping question below — do not implement a kill-rate or XP-curve
   change in both tickets independently.
3. **Implement**: only after Plan, and only the real, minimal, user-approved fix.

## Out of Scope
- `item_equipped`'s own separate, non-level-gated producer paths — now
  `TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION`.
- `trait_expressed`/`pillar_trait_unlocked` — now
  `TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`.
- Any narrative/quest-reward XP source fix — `quest_completed` dormancy is already tracked
  separately (this session's own earlier findings).
- Re-litigating `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own already-rejected
  "just raise the per-kill XP multiplier" fix — that ticket's own real numbers already showed it
  can't flip the sign; any real fix here needs to be a structural rate change, not a magnitude
  tweak, unless new evidence says otherwise.

## Acceptance Criteria
- [ ] investigation.md confirms the real producer and real gating condition for each of
      `skill_unlocked`, `progression_conversion_applied`, and the leveling-driven contribution to
      `attribute_changed`/`item_equipped` dormancy (not assumed to be fully explained without
      checking for other real contributing producers)
- [ ] The scoping relationship to `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` is
      resolved with the user before Plan begins
- [ ] Any fix landed is re-verified against real 2000-tick corpus data showing the previously-zero
      events now firing at a real, honestly-reported rate (not assumed from a short synthetic run)
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ITEM-EQUIPPED-DORMANT-PATH-INVESTIGATION (split out — `item_equipped`'s own
  independent, non-level-gated producer paths)
- TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION (split out — `trait_expressed`/
  `pillar_trait_unlocked`'s entirely untraced producer)
- TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE (sibling, narrower scoring-cadence framing
  — see relationship note above)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (DONE — the real kill-rate/XP numbers
  this ticket's own evidence is grounded in)
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT (DONE — `docs/audits/D21_entity_lifecycle_foundation_layers.md`,
  the audit that surfaced this as the highest-priority open foundation gap)
- TCK-20260701-SIMQ-EMIT-PROGRESSION (DONE — the ticket that originally wired these event
  emitters)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`
- `docs/mechanics/01_entity_anatomy.md` (XP scaling)
- `docs/simulation_quality/event_type_coverage.md` §3.6

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/evolution.py` (`EvolutionSystem`, the real `levels_gained > 0` gate — lines ~80-149)
- `src/progression/leveling.py` (`LevelingService.get_unlocked_skills`, XP thresholds)
- `src/observability/event_extractor.py` (lines ~314-364, ~1086-1139 — the real event emitters,
  already correctly wired per `TCK-20260701-SIMQ-EMIT-PROGRESSION`)

## Assumptions / Open Questions
- **Needs a user decision before Plan**: should this ticket's own fix be unified with
  `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` (one combined kill-rate/XP-curve change
  addressing both the score-reading problem and the real gameplay-dead-code problem), or kept as
  2 separate tickets with 2 separate, more surgical fixes (e.g. lengthen the stall-detector window
  for the score, AND separately lower the level-1 XP threshold or add non-combat XP sources for
  the real gameplay cascade)? Not decided here.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
