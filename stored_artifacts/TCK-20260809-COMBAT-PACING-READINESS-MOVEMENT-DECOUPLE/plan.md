---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE

## Chosen fix: remove movement's readiness cost, keep its stamina cost
Confirmed via direct source read that stamina already, independently serves as the real
movement-fatigue resource (its own regen, its own exhaustion mechanic). Readiness's own documented
contract is purely an attack-eligibility gate. Removing the redundant readiness cost from
movement is the minimal, architecturally-correct fix — not a magnitude tweak (which the sibling
ticket's own `readiness_speed` parameter sweep already showed doesn't work) and not a new design
(readiness's own intended role never included movement cost in the first place).

## Rejected alternatives
- **Raise `readiness_speed` further**: already tried and rejected in the sibling ticket's own
  parameter sweep (10/20/30/50) — no value fixed the structural double-cost, since regen can't
  outpace continuous movement drain regardless of magnitude while the drain itself is real.
- **Give movement a separate, new "movement readiness" resource distinct from both stamina and
  attack-readiness**: rejected as unnecessary new-mechanic scope — stamina already exists and
  already fills exactly this role; inventing a third resource would be solving an already-solved
  problem.
- **Remove the readiness pre-check in `verify_movement_legality()` entirely**: rejected — that
  check still serves a real, small, correct purpose (a brief post-attack movement lockout), not
  part of the double-cost bug.

## Verification plan
Same `is_attack_legal` live-probe methodology used throughout this whole session's combat
investigation chain, run against both real corpus worlds already used as this investigation's own
baseline (`dungeon_crawl`, `urban_political`), before and after the fix.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms the real double-cost root cause | Done — direct source read |
| Fix re-verified against real corpus data, not assumed | Done — 1.3% → 28.5%/36.6% |
| No regressions | Done — 1071+ scoped tests, only pre-existing unrelated failures remain |
| Scoped pytest passes | Done |
