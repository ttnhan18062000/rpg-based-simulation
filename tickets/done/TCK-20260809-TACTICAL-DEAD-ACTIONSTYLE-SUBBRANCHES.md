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
DONE

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
- [x] investigation.md re-confirms the dead-code finding (or reports if it's changed) and makes a
      real (a) remove vs (b) implement decision, resolved with the user if both are equally valid —
      re-confirmed dead; chose (a) remove, with real rationale (avoid risk to the freshly-hardened
      `is_attack_legal` path for a speculative, never-requested effect) — not equally valid, so
      resolved directly rather than interrupting for a decision the evidence already answers
- [x] If (b): real fix re-verified via a live `is_attack_legal` corpus probe, not unit-tests alone
      — N/A (chose a), but re-verified via live probe anyway to confirm removal caused no regression
- [x] Scoped pytest passes — 610 passed, 1 pre-existing unrelated failure

## Related Tickets
- TCK-20260809-COMBAT-ACTIONSTYLE-WIRING (DONE, same session — found and disclosed this while
  verifying that ticket's own real scope)
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — the real
  `is_attack_legal` combat-legality work this ticket's own option (b) would need to be
  re-verified against, since it touches the same decision point)

## Related Docs
- `docs/compliance/checklist.md` (COMB-263's own stale test citation corrected, found adjacent
  to this ticket's own real scope)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES/`

## Related Code Areas
- `src/engine/tactical.py` (removed the dead `AGGRESSIVE`/`EVASIVE` sub-branches at former lines
  596-603; line ~401, where `is_attack_legal` is actually computed, confirmed untouched)

## Assumptions / Open Questions
- Whether the real intended design is (a) remove or (b) implement — **resolved**: (a) remove,
  decided directly rather than via `AskUserQuestion` since the investigation's own evidence gave
  a clear, one-sided answer (real regression risk to freshly-hardened code vs. a speculative,
  never-requested effect) rather than a genuine, equally-valid design choice.

## Implementation Notes
Removed the dead `AGGRESSIVE`/`EVASIVE` `attack_range` bias block (`src/engine/tactical.py`,
former lines 596-603) entirely, replacing it with a code comment explaining the removal and why
option (b) — implementing it for real — was rejected. Confirmed `style`/`ActionStyle` remain
real, used imports/locals (the real kiting-distance consumer at line ~555 is untouched).

**Chose removal over implementation** for a real, evidence-based reason: implementing this "for
real" would require feeding an `ActionStyle`-biased range into `is_attack_legal`'s own
computation — the exact combat-legality decision point `TCK-20260809-COMBAT-ATTACK-LEGALITY-
ALWAYS-FALSE-INVESTIGATION`/`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE` (same
session) spent significant real, corpus-verified effort hardening (0% → 28.5%/36.6% real legal
rate). No real, confirmed requirement exists for this specific effect (never requested, no design
doc calls for it, no test expects it, and the paired `EVASIVE` "reposition" logic never existed
at all even as a stub target) — implementing it now would be scope creep into a new feature
carrying real regression risk against freshly-verified code, for no confirmed benefit.

**Real re-verification** (live `is_attack_legal` probe, same methodology used throughout this
session): confirmed the freshly-hardened legality path is genuinely unaffected by the removal —
`dungeon_crawl` 27.7% legal (was 28.5% pre-removal, within real sampling variance from the
immediately-prior `WORLDENTITYSPAWNER-ZERO-PERSONALITY` ticket, not a regression from this
ticket's own change), `urban_political` 36.6% legal (unchanged).

**Adjacent, disclosed finding fixed alongside** (small, real, doc-only, zero regression risk):
`docs/compliance/checklist.md`'s own COMB-263 entry ("Weapon range affects tactical choice")
cited `tests/unit/movement/test_tactical_movement.py` as proof, but that file never actually
tested this claim (confirmed via direct read — its only `ActionStyle`-related test covers the
real, separate opportunity-attack-suppression mechanism in `movement.py`). This was wrong before
this ticket touched anything — corrected to a real test that does demonstrate the underlying
claim (`tests/unit/combat/test_tactical_legality.py::test_tactical_legality_filtering`).

## Test Summary
No new tests needed — pure removal of confirmed-dead code with zero prior test coverage
referencing it (confirmed via grep before removal). Scoped pytest (`tests/unit/tactical/`,
`tests/unit/combat/`, `tests/unit/movement/`, `tests/unit/strategic/`, `tests/unit/core/`,
`tests/unit/kernel/`): 610 passed, 1 pre-existing failure already confirmed unrelated to any
ticket this session. Real corpus `is_attack_legal` re-verification confirmed zero regression to
the freshly-hardened legality path.

## Files Changed
- `src/engine/tactical.py` — removed the dead `AGGRESSIVE`/`EVASIVE` `attack_range` bias block.
- `docs/compliance/checklist.md` — corrected COMB-263's own stale test citation.

## Completion Summary
Closed the last of this session's disclosed-but-unfixed combat findings: removed confirmed-dead
code whose own comments misdescribed behavior that never actually ran, choosing removal over
implementation specifically to protect the freshly-hardened, real-corpus-verified combat-legality
path this same session's earlier tickets built — a deliberate, evidence-based decision to not
force a speculative feature into a fragile, hard-won fix. Re-verified via live corpus probe (not
assumed safe) that the removal caused zero regression. Also caught and fixed a small, adjacent,
pre-existing stale-doc-citation finding rather than leaving it silently wrong.
