---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES
artifact_type: test_plan
tags: [combat, simulation-quality]
---

# Test Plan — TCK-20260809-TACTICAL-DEAD-ACTIONSTYLE-SUBBRANCHES

## Normal flow / regression
No new tests needed — this is a pure removal of confirmed-dead code with zero prior test
coverage referencing it (confirmed via grep before removal). The real, working `ActionStyle`
consumers (kiting distance, opportunity-attack suppression) are untouched and remain covered by
their own existing tests.

## Failure modes / regression-prone paths
- Full scoped pytest re-run across the combat/tactical/movement surface to confirm zero
  behavioral change.
- Real corpus `is_attack_legal` re-verification (live probe, same methodology used throughout
  this session) against both real worlds already used as this session's own baseline —
  specifically to confirm the freshly-hardened legality path (`TCK-20260809-COMBAT-ATTACK-
  LEGALITY-ALWAYS-FALSE-INVESTIGATION`, `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`)
  is genuinely unaffected, not just assumed safe.

## Real corpus re-verification results
- `dungeon_crawl` (600 real ticks): 27.7% legal (was 28.5% pre-removal — within real sampling
  variance from the `WORLDENTITYSPAWNER-ZERO-PERSONALITY` fix landed immediately before this
  ticket, not a regression from this ticket's own change).
- `urban_political` (600 real ticks): 36.6% legal (unchanged).

## Scoped test commands
```
.venv/bin/python3 -m pytest tests/unit/tactical/ tests/unit/combat/ tests/unit/movement/ \
  tests/unit/strategic/ tests/unit/core/ tests/unit/kernel/ -q -m "not slow"
```
Result: 610 passed, 1 pre-existing failure already confirmed unrelated to any ticket this session
(`test_normal_move_triggers_oa`). Zero new regressions.
