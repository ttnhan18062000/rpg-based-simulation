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
Skill unlocks, AP spending, attribute growth, species evolution, and evolution-driven gear
upgrades are ALL gated behind `levels_gained > 0` in `EvolutionSystem` — since `level_up` never
fires in real gameplay, this is a dead gameplay cascade, not just a dormant scoring signal

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Per the user's own explicit direction to prioritize the `GROWTH_PROGRESSION` zero-triggered
events found in `docs/audits/D21_entity_lifecycle_foundation_layers.md`
(`skill_unlocked`, `item_equipped`, `attribute_changed`, `trait_expressed`, `progression_conversion_applied`
all confirmed to never fire in real 2000-tick corpus runs, alongside the already-known-dormant
`level_up`), traced each event's real producer code directly rather than assuming independent
causes.

**Real, decisive finding**: `src/engine/evolution.py`'s entire level-up reward block
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
  `attribute_changed` never firing (though `attribute_changed`'s own emitter is a general diff, so
  other real attribute-mutation sources should be separately checked, not assumed to be zero, in
  Investigate).
- Species evolution (`_get_evolved_kind`, the 10/25/50-level thresholds) never triggers — real
  code for what would functionally be "class breakthrough"/"power up," dead in practice.
- The species-evolution-triggered gear upgrade (`new_slots[EquipSlot.MAIN_HAND] = "iron_sword"`
  etc., lines ~103-109) never fires — one real contributing cause of `item_equipped` never firing,
  **but not the only one**: `src/domains/progression/resolver.py:43-44` and
  `src/core/equipment.py:239-265` are separate, real, non-level-gated equip-producing code paths
  that were NOT traced in this initial finding — their own real gating conditions are an open
  question for Investigate, not assumed to share this same root cause.
- `trait_expressed`/`pillar_trait_unlocked` (diffing `entity.identity.traits`/
  `active_breakthroughs`) were **not** found to be touched anywhere in `evolution.py`'s own
  level-up block — their real producer(s) are a genuinely open question, not yet traced, and may
  have an entirely different (or entirely absent) real cause.

**Relationship to the existing, already-filed `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`**
(P3, standard, OPEN): that ticket frames the problem as a *scoring-detector cadence mismatch*
(`capability_growth_stalled` re-firing every 300 ticks vs. real kill rate) — a narrower framing
whose candidate fixes (lengthen the stall-detector window, or raise kill frequency) are about
making the **score** read correctly. This ticket's own finding is broader and more consequential:
even if the score were made to read correctly, the underlying **gameplay** — skills, AP, attribute
growth, evolution, and some equipment — genuinely never happens for real entities, independent of
how the score is computed. Raising real kill frequency (that sibling ticket's own "lever 1") would
likely fix both; lengthening the stall-detector's cadence (that ticket's "lever 2") would fix the
score reading without touching this ticket's own real gameplay-dead-code finding at all. **This
is exactly the kind of scoping decision to raise with the user before Plan, not decide
unilaterally** — see `## Assumptions / Open Questions`.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the real XP curve: how many levels a real entity would need to gain, and how much
     real XP that requires, versus real observed XP accumulation rates (cite
     `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own real numbers, extend if
     needed).
   - Trace `trait_expressed`/`pillar_trait_unlocked`'s real producer(s) — not found in
     `evolution.py`; check personality/self-model systems or any other real writer of
     `entity.identity.traits`/`active_breakthroughs`.
   - Trace `src/domains/progression/resolver.py`'s and `src/core/equipment.py`'s own real gating
     conditions for `item_equipped` — confirm whether they share the level-up root cause, a
     different pacing-style root cause, or something else entirely (e.g. a feature flag, a
     quest-reward dependency already known to be dormant).
   - Confirm whether `attribute_changed` has any other real producer beyond `evolution.py`'s
     level-gated non-HERO branch (training system, item-stat-bonus system, etc.) — don't assume
     zero without checking.
2. **Plan**: coordinate explicitly with `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE`
   once the user has decided the scoping question below — do not implement a kill-rate or XP-curve
   change in both tickets independently.
3. **Implement**: only after Plan, and only the real, minimal, user-approved fix.

## Out of Scope
- Any narrative/quest-reward XP source fix — `quest_completed` dormancy is already tracked
  separately (this session's own earlier findings).
- Re-litigating `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`'s own already-rejected
  "just raise the per-kill XP multiplier" fix — that ticket's own real numbers already showed it
  can't flip the sign; any real fix here needs to be a structural rate change, not a magnitude
  tweak, unless new evidence says otherwise.

## Acceptance Criteria
- [ ] investigation.md traces every one of the 5 zero-triggered events to a confirmed real
      producer and real gating condition (not assumed to share one cause without checking each)
- [ ] The scoping relationship to `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` is
      resolved with the user before Plan begins
- [ ] Any fix landed is re-verified against real 2000-tick corpus data showing the previously-zero
      events now firing at a real, honestly-reported rate (not assumed from a short synthetic run)
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE (sibling, narrower scoring-cadence framing
  — see relationship note above)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (DONE — the real kill-rate/XP numbers
  this ticket's own evidence is grounded in)
- TCK-20260808-LOWER-LAYER-FOUNDATION-AUDIT (DONE — `docs/audits/D21_entity_lifecycle_foundation_layers.md`,
  the audit that surfaced this as the highest-priority open foundation gap)
- TCK-20260701-SIMQ-EMIT-PROGRESSION (DONE — the ticket that originally wired these 5 event
  emitters; its own AC claimed a 200-tick `dungeon_crawl` run produced real `skill_unlocked`
  events, worth re-checking during Investigate whether that was a narrow/synthetic scenario vs. a
  genuine regression since 2026-07-01)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md`
- `docs/mechanics/01_entity_anatomy.md` (XP scaling)
- `docs/simulation_quality/event_type_coverage.md` §3.6

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/evolution.py` (`EvolutionSystem`, the real `levels_gained > 0` gate — lines ~80-149)
- `src/progression/leveling.py` (`LevelingService.get_unlocked_skills`, XP thresholds)
- `src/domains/progression/resolver.py` (a separate, real, non-level-gated equip-producing path —
  not yet traced)
- `src/core/equipment.py` (another separate, real equip-resolution path — not yet traced)
- `src/observability/event_extractor.py` (lines ~314-364, ~1086-1139 — the real event emitters,
  already correctly wired per `TCK-20260701-SIMQ-EMIT-PROGRESSION`)

## Assumptions / Open Questions
- **Needs a user decision before Plan**: should this ticket's own fix be unified with
  `TCK-20260808-GROWTH-PACING-STALL-DETECTOR-IMBALANCE` (one combined kill-rate/XP-curve change
  addressing both the score-reading problem and the real gameplay-dead-code problem), or kept as
  2 separate tickets with 2 separate, more surgical fixes (e.g. lengthen the stall-detector window
  for the score, AND separately lower the level-1 XP threshold or add non-combat XP sources for
  the real gameplay cascade)? Not decided here.
- Whether `trait_expressed`/`pillar_trait_unlocked` share the level-up root cause at all is
  genuinely unknown — not assumed.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
