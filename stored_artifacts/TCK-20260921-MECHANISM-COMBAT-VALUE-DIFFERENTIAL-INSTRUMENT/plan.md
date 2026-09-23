# Plan — TCK-20260921-MECHANISM-COMBAT-VALUE-DIFFERENTIAL-INSTRUMENT (re-scoped)

Original plan (8-mechanism sweep) superseded mid-investigation by explicit peer instruction — see
investigation.md's own re-scope note. This plan reflects the narrow, final scope only.

## Step 1 — combat_resolution direct differential (done)
`tests/mechanic_scenarios/test_combat_resolution_damage_value_differential.py` — vary
`combat.atk`/`combat.def_stat` directly, positive + negative control.

## Step 2 — the narrow question's own end-to-end answer (done)
`tests/mechanic_scenarios/test_combat_attributes_real_fight_outcome_value_differential.py` — chain
`LevelingService.recalculate_combat_stats()` (real, direct call) with a real Kernel-dispatched
fight, positive control (strength) + negative control (charisma).

## Step 3 — registry (done)
One dated additive note on `combat_resolution` only. No other mechanism entries touched.

## Step 4 — cross-reference the finding into the stats_dirty P0 ticket (done)
Answers that ticket's own open "does entity identity matter" question directly, in its own Request
Summary, not left implicit.

## Step 5 — report to peer, then stop
No further combat waves. No arbitration instrument. Ticket closes, #232 closes after this push.
