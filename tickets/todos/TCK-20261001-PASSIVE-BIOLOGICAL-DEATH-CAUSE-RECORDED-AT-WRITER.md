---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER

## Title
Record the cause of a passive hunger/sleep-debt death at the writer, then classify it in `resolve_lifecycle`

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Passive starvation/sleep-debt HP-loss deaths are still silent: `apply.py:98-110` writes
`combat.alive=False` and `lifecycle.active=False` with no persisted cause, so `resolve_lifecycle` never
records a `death_reason` or dispatches lineage consequences. `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
shipped no classification. Its first design inferred the cause from `hunger >= 95` /
`sleep_debt >= 98`; that was rejected (see that ticket's Implementation Notes): being at a threshold is not
the cause (`docs/world_rules/foundations/capacity.md` LIMIT-04, ACCEPT), the cause would be fabricated
(CAUSE-01, HP-02, CAUSE-05), and a `DEFEAT` leftover (non-lethal, LIFE-02) would be mislabelled with
succession fired. `DEFEAT` also hits non-HERO entities via opportunity attacks, so a role gate fails.

## Scope
- Record the cause where it is known: in `apply.py`'s passive branch, when it takes HP from positive to
  zero (`comb.hp > 0 and new_hp == 0`). A `DEFEAT`/`REBIRTH` entity is already at `hp == 0`, so this
  excludes every combat-caused zero with no role or outcome inference.
- Add it as a typed durable field with a defined lifecycle, inspection/debug visibility and
  serialization tests (Durable State Rule). Do not change the `total_passive_dmg` computation or the
  `new_hp > 0` gate.
- `resolve_lifecycle` reads the typed field (it never infers) and records distinct `STARVATION` /
  `SLEEP_DEPRIVATION` reasons with `is_permadeath_set=True` and the existing succession dispatch.
- **Run `architecture-reviewer` on the plan before writing code** (user-approved), because this adds a
  typed field on the authoritative apply path.

## Out of Scope
- DEFEAT/REBIRTH handling (`TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`).
- The hazard route (done) and hazard-overwrites-KILL.

## Acceptance Criteria
1. A passive hunger or sleep-debt death records a distinct non-None `death_reason` and dispatches full lineage.
2. A `DEFEAT`/`REBIRTH` leftover, HERO or not, is never classified by this path.
3. The cause is a typed, serialized, inspectable field; `event_extractor.py` stays exact-match on COMBAT.
4. Architecture-reviewer verdict recorded before implementation; contract and parity docs updated.

## Related Tickets
- `TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP`
- `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`

## Related Docs
- `docs/simulation/lifecycle_systems_contract.md`
- `docs/world_rules/foundations/capacity.md` (LIMIT-04); `docs/world_rules/life-body/lifecycle.md` (LIFE-02)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/investigation.md`

## Related Code Areas
- `src/engine/apply.py:94-110`, `src/systems/lifecycle_systems/lifecycle.py`

## Assumptions / Open Questions
- Field name and home (on `LifecycleComponent` vs elsewhere) are for Plan and the architecture review.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary
_To be completed during implementation._
