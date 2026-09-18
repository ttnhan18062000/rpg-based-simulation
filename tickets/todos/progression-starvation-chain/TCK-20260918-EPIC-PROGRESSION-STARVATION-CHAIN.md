---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN
phase: open
date: 2026-09-18
tags: [combat, faction, progression, investigation]
---

# TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN

## Title
Group the five tickets that together measured one causal chain — combat is incidental, not
decisional; few kills; XP never accumulates; no level-ups; `stats_dirty` never fires; agility never
reaches `readiness_speed` — so whoever picks up any one of them can see the other four

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P1

## Request Summary
Five tickets, filed across three separate sessions between 2026-09-15 and 2026-09-17 for five
different immediate reasons, each independently measured one link of the same real causal chain.
Nothing connects them today — whoever opens one has no way to know the other four exist, which is
the same failure this whole registry/ticket-discipline effort exists to prevent, one layer up at
the ticket level.

**The chain, every link measured, every measurement already sitting in one of these five tickets —
not asserted here, only assembled:**

1. Real combat is **incidental, not decisional**. `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`
   found most sampled corpus worlds show zero cross-faction hostile interaction, and its own
   2026-09-17 addendum traced this to a sharper fact: almost all real combat resolution runs through
   `CombatResolutionSystem.resolve_multi_attack()` (movement's incidental opportunity-attack
   mechanic — 181-2177 calls per 1000-2000 ticks), not through the decision-driven
   `resolve_attack()` path reached via `TacticalDecisionSystem` (0-2 calls). Investigation paused,
   not closed, at this finding.
2. **Why** the decision-driven path essentially never fires is `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s
   own question (P0) — four candidate causes (sticky tasks, the `hostiles` gate, task
   emission-vs-dispatch divergence, objectives never reaching `DEFEAT_ENEMY`), each to be confirmed
   or ruled out by measurement, not reasoning. This is the same underlying fact `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`
   independently sighted in August for an unrelated reason — three separate investigations, the
   same fact, never connected until this ticket's own path-split measurement named it directly.
3. A newly-built posture-veto gate (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`,
   closed) cuts real decision-driven attack volume ~58% in the one world class where that path
   fires (`metropolis`) — raising the question of whether it further starves two already-thin
   downstream systems. `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`
   checked both: the faction-chain half is resolved (the gate has no measurable effect on the
   corpus worlds' cross-faction volume, because those worlds' real combat never routes through the
   gated path in the first place — link 1 and link 2's own finding, restated from a different
   angle); the boss-gate half (does the gate further starve the world-boss maturity trigger) is
   still open.
4. Few kills mean **XP never accumulates past a fraction of a single level-up threshold**.
   `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (closed, root-caused) found
   the combat-XP-to-level-up chain itself is correctly wired and confirmed via a real Kernel-tick
   positive control — the code is not broken. The tested corpus worlds simply never generate enough
   real kills (0-10 per 1000 ticks) to reach the ~100 XP a level-2 threshold requires.
5. No level-ups mean **`stats_dirty` never sets**, so no derived combat stat (`max_hp`, `atk`,
   `def_stat`, `evasion`, `move_cost`, `range`, `tactical_role`, `readiness_speed`) is ever
   recalculated for any entity in any tested world — the same ticket's own original finding, now
   fully explained rather than merely observed.
6. The tuning question this all points toward —
   `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — is **explicitly blocked** on link
   1 landing, per that ticket's own Status field: retuning the XP threshold or per-kill values to
   fit today's starved combat volume would silence the signal (entities barely fight) rather than
   fix what the signal is reporting on, the same failure shape as lowering an attribution ratchet to
   fit a low score.

## Scope
This epic **groups and sequences existing tickets — it does not itself investigate or fix
anything.** Each child ticket keeps its own scope, acceptance criteria, and disposition; this epic's
only job is making the chain visible and stating two constraints that already exist inside
individual tickets but weren't visible from outside them.

### Order (see `SEQUENCE.md`)
1. `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (P0, open)
2. `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (P1, paused — resume with (1)'s findings)
3. `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (P2, open — boss-gate half
   only; faction-chain half already resolved)
4. `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (done — referenced for
   context, not reopened; stays in `tickets/done/` root per this repo's own epic-folder precedent)
5. `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (P1, blocked — must run last)

## Out of Scope
- **Any investigation or fix work itself.** That belongs to the individual child tickets, which keep
  their own scopes unchanged by this epic.
- **Re-litigating any already-closed finding** (the posture-veto gate's own correctness, the
  combat-XP-to-level-up chain's own correctness) — both are confirmed-correct code, not reopened
  here or by any child.
- **Retuning the XP threshold or combat volume before the chain's root (item 1 above) is resolved.**
  Already encoded in `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`'s own Status
  field; restated here so it's visible from the epic level too, not just from inside that one
  ticket.

## Acceptance Criteria
1. All five tickets cross-reference this epic and each other (already true for most pairs
   individually; this epic is the single place that names all five together).
2. `SEQUENCE.md` records the two sequencing constraints that already exist inside individual
   tickets: the XP threshold ticket runs last, and the ATTACK-path investigation's own priority is
   independent of `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`'s re-derived ranking (see
   Related Tickets).
3. No child ticket's own scope, acceptance criteria, or status is altered by this epic — grouping
   only.

## Related Tickets
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` — child, P0, open
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — child, P1, paused (not closed — the
  investigation that started this chain and produced the path-split measurement child 1 continues)
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` — child, P2, open
  (boss-gate half only)
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` — child, done
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — child, P1, blocked (runs last)
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — **not a child, cited for context only.**
  Its own re-derivation of `registries/mechanisms.yaml`'s priority ranking dropped `tactical_decision`
  (the mechanism `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` investigates) from
  the top-priority unverified target to zero transitive dependents. **That investigation's own real
  corpus measurement (181-2177 incidental calls vs. 0-2 decisional calls per 1000-2000 ticks) does
  not depend on why the mechanism was selected for investigation, and stands independent of the
  ranking that originally surfaced it — recorded here explicitly so it does not read as retracted.**
- `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION` — 2026-08, closed; the third,
  independent, unrelated-reason sighting of the same `resolve_attack(): 0 real calls` fact this
  chain's own investigations converged on from three different directions

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy, interruption resistance, the posture
  gate's own spec
- `docs/engine/kernel.md` — the Sticky-Task Law, one of the four candidates in child 1
- `docs/mechanics/attribute_progression_contract.md` — the XP/level-up formula confirmed correct by
  child 4's own positive control
- `docs/plans/world_composition_precondition_gap_finding.md` — the `camp`-family pattern child 4 and
  child 5 both match (correct, wired code defeated by real-world data/volume, not a code defect)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS/` — child
  4's own full trace

## Related Code Areas
- `src/engine/tactical.py` — child 1's own primary investigation surface
- `src/engine/movement.py` — `resolve_multi_attack()`, the dominant real combat path
- `src/engine/domain/action_router.py` — the posture-veto gate
- `src/engine/evolution.py`, `src/progression/leveling.py` — the confirmed-correct XP/level-up chain
- `registries/mechanisms.yaml` — `tactical_decision`, `combat_resolution`, `movement`, `xp_leveling`,
  `evolution`

## Assumptions / Open Questions
- Whether `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s own findings will let
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` close outright, or whether that older
  investigation's own remaining unverified lead (the static `merchant_league` region-overlap
  comparison between `crowded_frontier` and `frontier_living_world`) still needs a live check
  independent of the ATTACK-path question — not yet known; `SEQUENCE.md` records the order without
  assuming the answer.
- Whether the world-boss maturity gate's real trigger rate (the still-open half of child 3) shares
  the same root cause as the rest of this chain, or is an independent thinness — not yet checked.

## Implementation Notes
Epic tier — grouping only. Children carry their own plans, investigations, and dispositions.

## Test Summary
Per child. This epic itself changes no code.

## Files Changed
None (epic — grouping only; individual child tickets are not modified by this filing beyond adding
a cross-reference to this epic where a child's own `Related Tickets` section is updated).

## Completion Summary
Open.
