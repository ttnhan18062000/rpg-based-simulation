---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Title
`tactical.py`'s `AGGRESSIVE` effective-range bonus and `EVASIVE` "reposition instead of
attacking" stub are confirmed dead code — a local variable mutated but never read by the
function's own downstream branches — **confirmed to currently have zero effect on combat
outcome, scoring, or metrics, since the code path is structurally unreachable regardless of
`ActionStyle`**

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found during `TCK-20260809-COMBAT-ACTIONSTYLE-WIRING` (same session) while tracing
`ActionStyle`'s own real consumption in `src/engine/tactical.py`, to confirm which of its
consumers actually matter before claiming that ticket's own fix "activates" them.

`tactical.py` (lines ~596-603) computes an `attack_range` local variable, biased for
`ActionStyle.AGGRESSIVE` (+1) and with an `EVASIVE` branch that is a bare `pass` (a no-op stub —
the comment says "Evasive skirmishers might choose to reposition instead of attacking if too
close" but no such repositioning logic exists). **Neither has any real effect**: `is_attack_legal`
(the value an `attack_range` bonus would need to influence) is computed earlier in the same
function (line ~401), *before* this block runs; the local `attack_range` variable itself is never
read again by anything after this block (confirmed via direct read of the function's own
remaining ~65 lines — the `SKILL`/`ATTACK`/pursuit branches that follow reference `dist_to_target`
and `skill.range`, never this local variable). This is genuinely dead code, not a design decision
— the comments describing intended behavior ("Aggressive entities ignore range buffers", "Evasive
skirmishers might choose to reposition") do not match what the code actually does.

**Real impact**: none currently. Wiring `ActionStyle` from bravery
(`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`) does not activate either of these two sub-branches —
only the real, separately-verified kiting-distance and opportunity-attack-suppression consumers
are affected by that fix. This dead code was dead before `ActionStyle` had any real assignments
and remains equally dead now that it does.

## Scope
1. **Investigate**: confirm the dead-code finding still holds (re-read `tactical.py`'s current
   state in case it's changed since this ticket was filed); decide the real, minimal fix — either
   (a) remove the dead branches entirely (if the "reposition"/"range bonus" behavior isn't
   actually wanted), or (b) implement them for real (if it is) by making `attack_range`'s
   post-bias value actually feed into a legality/behavior decision, which likely means moving
   the `ActionStyle` bias earlier, before `is_attack_legal` is computed, and building the real
   `EVASIVE` reposition logic that currently doesn't exist at all.
2. **Plan**: given this affects `is_attack_legal`'s own computation (a determinism/combat-legality
   critical path already the subject of 2 other tickets this session), any real fix here should be
   re-verified with the same real corpus `is_attack_legal` probe methodology used throughout this
   session's combat investigation chain — not just unit-tested.
3. **Implement**: only after the real Investigate/Plan decision on (a) vs (b) above.

## Out of Scope
- Any other `ActionStyle` consumer — the real, working kiting-distance and opportunity-attack
  consumers are unaffected and already correct.
- Re-litigating `TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`'s own scope (which entity gets which
  `ActionStyle`) — this ticket is purely about what `tactical.py` itself does once an entity has
  a given `ActionStyle`.

## Acceptance Criteria
- [ ] investigation.md re-confirms the dead-code finding (or reports if it's changed) and makes a
      real (a) remove vs (b) implement decision, resolved with the user if both are equally valid
- [ ] If (b): real fix re-verified via a live `is_attack_legal` corpus probe, not unit-tests alone
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (DONE, same session — found and disclosed this while
  verifying that ticket's own real scope)
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — the real
  `is_attack_legal` combat-legality work this ticket's own option (b) would need to be
  re-verified against, since it touches the same decision point)

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/tactical.py` (lines ~596-603, the dead `AGGRESSIVE`/`EVASIVE` sub-branches; line
  ~401, where `is_attack_legal` is actually computed)

## Assumptions / Open Questions
- Whether the real intended design is (a) remove or (b) implement — not decided here; a real
  design/priority call, not a technical one.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
