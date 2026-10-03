---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN
phase: done
date: 2026-09-08
tags: [world, architecture]
---

# TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN

## Title
Decide whether a world should be compilable at a non-zero starting world maturity

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Found during `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE`'s follow-up pass. The Lair-occupant gate
(`state.maturity >= 50.0`, world-level) has no compile-time content-seed path in the schema, and
natural accrual is genuinely slow: `CalamityService.apply()` (`src/world/calamity.py:30-32`)
increments `state.maturity` by 1 on a plain, unconditional periodic schedule
(`state.tick % MATURITY_INTERVAL == 0`, `MATURITY_INTERVAL = 1000` — not tied to whether a calamity
actually fires), so reaching `state.maturity >= 50` needs ~50,000 ticks — far beyond any practical
calibration run (this repo's own runs are 200-5,000 ticks).

Unlike the camp-maturity gate `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` fixed via content
authoring (`CampState.maturity` is a real, per-camp, content-authorable field), `state.maturity` is
a single global counter — there is no per-lair or per-region equivalent. "Seeding" it isn't a
lair-content change at all; it's a global world-age override that would simultaneously
fast-forward every other maturity-gated mechanism in the simulation (not just Lair occupants),
a materially wider blast radius than the schema gap suggests.

## Scope
- Confirm during Investigate whether `world.maturity >= 50` genuinely gates only the Lair-occupant
  spawn, or whether other real mechanisms also key off `state.maturity` at various thresholds
  (re-grep for `state.maturity` comparisons across `src/`) — the real blast radius of any change
  here needs to be understood before deciding.
- **Decision already made (user, 2026-09-08): accept the gate as long-horizon-only and record the
  divergence. Do NOT add a schema field, and do NOT recalibrate the gate value.** Both alternatives
  were considered and rejected: adding `starting_world_maturity` has the widest blast radius (it
  fast-forwards every maturity-gated mechanism at once, not just Lair occupants), and lowering the
  `state.maturity >= 50` threshold would change when lairs appear in every existing world. Neither
  is justified without demonstrated demand, and there is none today.
- The remaining work is therefore the blast-radius survey plus the disclosure, not a design
  decision: re-grep `state.maturity` comparisons across `src/` to identify every mechanism gated on
  it, so the recorded divergence states accurately what else is long-horizon-gated rather than
  claiming Lair occupants are the only one.
- Record the accepted gap in `docs/guidelines/intentional_divergences.md` with a rationale class
  and a verification path, per the Authoritative Mechanics Rule. A ticket-body note is explicitly
  not sufficient.
- If the survey turns up a maturity-gated mechanism that someone actually depends on reaching in a
  practical run, **file a ticket** for it — do not reopen the schema question inside this one.

## Out of Scope
- Redesigning `CalamityService`'s own maturity-accrual formula or interval — confirmed correct as a
  design choice, not a bug; this ticket only asks whether a *starting* value should be
  content-authorable.
- The Lair-occupant mechanism itself (`region.trauma_score >= 20.0`, `BossService`) — already
  confirmed correct and tested; this ticket only concerns the world-maturity half of its gate.
- Any other maturity-gated mechanism's own disposition — scope this ticket to the schema/design
  question only, not a survey of every consumer (though Investigate should identify them for real
  blast-radius awareness, per Scope above).

## Acceptance Criteria
- [x] A complete list of `state.maturity`-gated mechanisms exists, produced by a real survey of
      `src/`, so the disclosure describes the true scope of what is long-horizon-gated. Found
      `check_for_boss_spawn()` (world_boss/ancient_sentinel, region-scoped) shares the exact same
      gate as `check_for_lair_spawn()` — not mentioned by this ticket's own original framing.
      Also found `spawn_stronghold()`'s own maturity-based stat scaling (real, reachable) and
      `spawn_calamity()`'s own identical scaling pattern (confirmed dead — zero callers anywhere).
- [x] The accepted gap is recorded in `docs/guidelines/intentional_divergences.md` §2.56 with a
      rationale class (Bounded) and a verification path — not left as only a ticket-body note.
- [x] No schema change and no gate-value change are made. The survey did not turn up evidence that
      overturns the decision — confirmed genuinely long-horizon (no other consumer depends on
      reaching the threshold sooner).

## Related Tickets
- `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` (`tickets/done/` — found this gap during its own
  follow-up pass)
- `TCK-20260904-LAIR-ENTITY-ANCHOR` (the ticket that originally built the Lair-occupant mechanism)
- `TCK-20260908-HOTFIX-STATE-PLACES-APPLY-CARRYFORWARD-GAP` — **second, independent blocker on
  Lair-occupant/boss spawning, found and fixed after this ticket's own decision was made.**
  `BossService.check_for_lair_spawn()` (`src/world/boss.py:206`) iterates `state.places.items()`
  filtering `kind == PlaceKind.LAIR` — but `state.places` was never carried forward tick-to-tick in
  `apply.py` (a separate bug from `CAMPAIGN-REGION-PLACE-CARRY`'s initial-construction fix), so this
  loop found zero LAIR places past the first tick, in every simulation mode, **independent of the
  `state.maturity >= 50` gate this ticket investigated**. That carry-forward gap is now fixed. This
  does not change this ticket's own accept-and-disclose decision (the `state.maturity` gate itself
  is still real and still long-horizon-only) — it means the disposition/divergence-entry this ticket
  produces must record BOTH blockers (the maturity gate AND the — now-fixed —
  places-carry-forward gap that was silently compounding it), not just the one originally
  investigated, so a future reader understands the full history rather than a partial one.

## Related Docs
None yet.

## Related Stored Artifacts
`stored_artifacts/TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN/` (investigation.md, plan.md,
test_plan.md)

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.apply()`, `MATURITY_INTERVAL`)
- `src/world/boss.py` (Lair-occupant gate consumer)
- `src/worldbuilding/schema.py`, `src/worldbuilding/compiler.py` (if a new compile-time field is
  added)

## Assumptions / Open Questions
- Whether to add a new schema field or accept the gap as-is is the central real design question
  this ticket must resolve — deliberately not decided here.

## Implementation Notes

Decision was already made (user, 2026-09-08: accept as long-horizon-only, no schema field, no
gate recalibration). Remaining work was the blast-radius survey and the disclosure entry.

**Survey** (`grep -rn "state\.maturity\b" src/`, excluding tests): found 6 real reference sites,
classified into gates, scalers, and non-consumers — see `intentional_divergences.md` §2.56 for the
full breakdown. Two findings beyond the ticket's own original framing:
1. `BossService.check_for_boss_spawn()` (region-scoped `world_boss`/`ancient_sentinel`) shares the
   exact same `state.maturity>=50` gate as `check_for_lair_spawn()` — the ticket named only the
   Lair-occupant case; both mechanisms have been equally unreachable, all along, for the same
   reason.
2. `EntityGenerator.spawn_calamity()` (`generator.py:238-251`) has the same `state.maturity`-scaled
   stat pattern as `spawn_stronghold()`, but a repo-wide grep (including tests) confirms **zero
   callers anywhere** — dead code, unrelated to the maturity threshold itself. Noted in the
   disclosure for survey completeness; not filed as its own cleanup ticket since it has zero
   runtime impact (a judgment call, not escalated — happy to file it separately if reviewed and
   disagreed with).

**Doc correction**: `docs/world/raid_boss_camp_contract.md`'s own "Boss — Spawn conditions"
section read `camp.maturity >= 50`, inconsistent with that same doc's own correct
`state.maturity >= 50` phrasing two paragraphs later (the Lair-generalization note). Corrected —
a real doc/code parity fix directly adjacent to this ticket's own investigation area, per the
Authoritative Mechanics Rule.

**`intentional_divergences.md` §2.56** records the full survey, the accept-and-disclose decision
and its rationale (Bounded — rejecting a global `starting_world_maturity` field because its blast
radius covers every consumer above at once, unlike the scoped `CampState.maturity` content-
authoring fix `TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE` already shipped for camps/nests), and
the two beyond-scope findings above.

No production code changed beyond the doc correction (a comment/prose fix, not a behavior change).

## Test Summary
`pytest tests/unit/world/ -m "not slow and not extra_slow"` → 332 passed, 0 failed (confirms the
doc-only change introduced no regression — expected, since no `src/` behavior changed).

## Files Changed
- `docs/guidelines/intentional_divergences.md` — new §2.56.
- `docs/world/raid_boss_camp_contract.md` — corrected `camp.maturity` → `state.maturity` typo in
  the Boss spawn-conditions section.

## Completion Summary
Confirmed via a real survey (not assumed) that `state.maturity`'s long-horizon (~50,000-tick) gate
affects both the world_boss/ancient_sentinel and Lair-occupant spawn mechanisms identically, plus
stronghold elite-stat scaling — a wider blast radius than this ticket's own original Lair-occupant
framing named. Recorded the already-decided accept-and-disclose disposition in
`docs/guidelines/intentional_divergences.md` §2.56 with the full survey, per the Authoritative
Mechanics Rule. Corrected a real, directly-adjacent doc/code inconsistency
(`docs/world/raid_boss_camp_contract.md`'s own internal contradiction on which value the boss
spawn gate reads) found while investigating. No schema change, no gate-value change, no other
production code changed — exactly as the standing decision specified.
