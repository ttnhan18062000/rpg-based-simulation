---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65
phase: done
date: 2026-10-11
tags: []
---

# TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65

## Title
Every living kind heals naturally everywhere, twice as fast asleep or resting, with no healing at the starving line and half speed while weakened (owner-ruled 2026-10-11, memo row 65).

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Lane C found (divergence 2.114 disclosure) that HP recovers only on a town tile, by a paid inn rest, on a level-up, or through one core action. Wounded wild creatures, camp monsters and travellers never heal, which distorts the gate's deaths. Owner ruling: natural healing for every living kind (D42).

## Scope
- Rate, in the same shape as staged starvation's hp_loss (D36):
  - 1 HP every round(9600 / max_hp) ticks awake;
  - 1 HP every round(4800 / max_hp) ticks while in a held SLEEP/REST, including a collapse.
  
  That is full health in about 4 days awake or 2 days resting, whatever the body size. Named D33 placeholder constants; per-kind rates come in M1's body properties.
- Need stages (same scale as D36/D41): no healing at or past the starving line, half speed while weakened. The worse of hunger and sleep decides. Derived from existing state, with NO new state field.
- Applied through the authoritative path as a typed HP delta. It never exceeds max_hp and is deterministic (tick-modulo, staggered by entity id like the need wake if that is the existing pattern).
- Unchanged: the inn's paid rest heals at once; town-tile and level-up healing stay as they are.
- Docs: divergence (next free id), parity entry, Bible 01 paragraph (it states only stamina regen today), mechanisms.yaml note.
- Tests:
  - an awake heal at the rate;
  - a resting heal at twice the rate;
  - no heal at the starving line;
  - half speed while weakened;
  - a cap at max_hp;
  - two body sizes reach full HP in the same time;
  - determinism.
- Measure with the paired protocol: deaths by cause and kind, the mean HP of wounded subjects, combat engagements (healed subjects fight again).

## Out of Scope
- Town-tile free healing (disclosed for M3's healing item; the designer will bring it to the owner then).
- Per-kind rates (M1).

## Acceptance Criteria
- Rates and stage interaction as ruled, tested, deterministic; measured before the baseline v1; divergence and parity recorded.

## Related Tickets
TCK-20261011-A-PANIC-RETREAT-TO-ITS-OWN-TILE-IS-HELD-WITH-NO-THREAT-IN-SIGHT (where the gap was found); D36 staged starvation; D41 sleep collapse.

## Related Docs
SURV-02 / LB amendments (memo row 65); docs/mechanics/01_entity_anatomy.md.

## Related Stored Artifacts
None.

## Related Code Areas
The staged-starvation hp_loss path; sleep_debt.py; town_resolution.py (unchanged).

## Assumptions / Open Questions
None.

## Implementation Notes
`src/engine/natural_healing.py` (table, `heal_period`, `hp_gain`) and one call in `apply.py`'s life-due branch. A starvation-loss tick heals nothing. Docs: Bible 01 'Natural Healing', divergence 2.116, parity PROG-131, mechanisms note on `attributes_biology`.

## Test Summary
12 new tests pass; engine and mechanic_scenarios 698 passed, 2 stale expectations loosened to 'none is lost'. Measured 5 seeds x 2 worlds x 5000 ticks: effects within noise except urban deaths -1.2 (SE 0.5).

## Files Changed
src/engine/natural_healing.py, src/engine/apply.py, tests/unit/engine/test_natural_healing.py, two mechanic_scenarios tests, docs (Bible 01, divergence 2.116, PROG-131), registries/mechanisms.yaml.

## Completion Summary
Shipped as ruled. Rate is slow against a 5000-tick run, so the measured effect is small; disclosed in 2.116.
