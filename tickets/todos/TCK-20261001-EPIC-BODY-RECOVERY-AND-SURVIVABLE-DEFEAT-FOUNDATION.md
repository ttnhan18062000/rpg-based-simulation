---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261001-EPIC-BODY-RECOVERY-AND-SURVIVABLE-DEFEAT-FOUNDATION
phase: open
date: 2026-10-01
tags: [architecture, lifecycle, combat, world]
---

# TCK-20261001-EPIC-BODY-RECOVERY-AND-SURVIVABLE-DEFEAT-FOUNDATION

## Title
The world has no recovery and no survivable defeat — a foundational gap nobody chose, made visible by
PR #276. Design recovery first, then survivable defeat; resurrection stays out.

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
**User decision 2026-10-01, on `world-rule-catalog-design`'s approach review of PR #276, which the user
asked for after observing the PR had directional effects.**

The simulation currently has: **no HP recovery, no healing, no survivable defeat, no resurrection, and
every zero-HP event terminal.** Each of those is separately recorded and separately justified. Together
they describe a world property **nobody designed**.

**Crucial correction to the framing — this property PRE-DATES PR #276 and that PR did not create it.**
The planner initially reported the opposite and was wrong. Verified this week:
- `DEFEAT` and `REBIRTH` outcomes already ended in permanent deactivation one tick late, via
  `apply.py`'s passive HP gate — the LIFE-02 application-layer contradiction observed in C1's run.
- Passive starvation/sleep-debt deaths were already deactivated by the same gate.
- Hazard deaths were already deactivated the same way.
- `REBIRTH` never restored anyone (no runtime writer ever set `alive` back to `True`).
- No healing exists anywhere (BODY-05).

Measured on base: of 34 HP-0 entities in a 400-tick `frontier_marches` run, **all 34 were already
inactive** with no `death_reason`. So in runtime terms nothing that reached zero HP ever came back. **The
property was already total; it was merely silent.** What PR #276 changed is that those deaths now carry
a `death_reason` and fire their consequences — succession, heirlooms, feud and dying-wish seeding,
economic vacancy.

So this is **not** altitude drift from PR #276: each of its fixes repaired a recording defect. But the
harsh-world property was never a decision, and it was invisible until the deaths became recorded. **This
epic exists to make it a decision.**

## Scope

**Ordering is load-bearing and comes from the rule owner. Bottom-up: recovery is a *body* concern,
lower than perception (a cognition input), so this epic is ranked AHEAD of a perception-foundation
epic.** Within it:

- **Child 1 — body recovery (the foundational gap).** BODY-05 records that no HP-recovery process
  exists, declared or otherwise, and that `src/cognition/need_interpretation.py` lets entities *perceive*
  a healing need **that nothing fulfils** — which BODY-05 itself calls worse than an inert field. It is
  **rule-ready**: BODY-05 already states what a valid recovery process must be (declared semantics, no
  spontaneous healing). Design and spec before code.
- **Child 2 — survivable defeat, which DEPENDS on child 1.** LIFE-02 permits a route from defeat to
  continued existence and does not require one. **It must never land before recovery:** a downed or
  incapacitated state with no recovery path is permanent limbo — a fact claiming recoverability the world
  can never deliver, which is the shape the rule owner explicitly ruled out when rejecting a downed state
  for terminal `DEFEAT`.
- **Child 3 (conditional) — population-collapse check.** With no healing and every defeat lethal,
  turnover may outrun reproduction and leave no living parents for succession to work through. Measure
  the population trajectory over a long run. **If it collapses, the fix is this epic's recovery
  foundation or reproduction rates — never a revival of defeat-survival hacks.**

## Out of Scope
- **Resurrection / death reversal.** STR-02 permits it but does not require it; it is optional content
  and the rule owner was explicit: do not bundle it. Any future resurrection is its own epic built to
  STR-02 (declared supernatural process gated on real state, each death recorded as history first,
  declared identity semantics).
- **Restoring hero `REBIRTH` in any form.** It was an undeclared resurrection that never worked at
  runtime; retiring it was correct regardless of what the recovery story becomes. If the answer here is
  "the world needs recovery", that is **new designed content**, not a restoration of what was removed.
- **Any implementation before the specs exist.** Spec-before-code, as with the de-hero epic.
- The PR #276 work itself, which is correct on every local question.

## Acceptance Criteria
1. A recovery design spec that satisfies BODY-05: a **declared** process with declared semantics, no
   spontaneous healing, and a stated relationship to `WoundState`/`ScarState` (which persist today and
   whose persistence is rule-compliant per BODY-06).
2. The `need_interpretation.py` perceive-but-cannot-fulfil gap is closed or explicitly deferred with a
   reason — an entity perceiving a need the world cannot satisfy is the specific defect BODY-05 names.
3. A survivable-defeat design that **cannot** be implemented before recovery exists, with that dependency
   stated as a hard sequencing constraint, not a preference.
4. A statement on whether LIFE-01's "may lose active-participant status without that being permanent"
   and LIFE-02's defeat-to-continued-existence route move from *permitted, not currently realised* back
   to *realised* — and if so, by which declared mechanism.
5. Population trajectory measured over a long run; a verdict on whether turnover outruns reproduction.
6. Child tickets traceable to these criteria, none filed before the specs.

## Related Tickets
- `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER`,
  `...-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`,
  `...-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND`,
  `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION` — PR #276, which made the property visible.
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — C1, the evidence that the property pre-existed.
- `TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY` — its inventory must treat former-HERO
  durability as **a capability to re-ground** (on equipment, skills, and eventually recovery), **not a
  privilege to restore**. With no recovery and no HERO protection, formerly-protected entities are the
  most exposed population; the inventory should check that rather than assume it away.

## Related Docs
- `docs/world_rules/life-body/body-condition.md` — **BODY-05** (the governing rule), BODY-03, BODY-06.
- `docs/world_rules/life-body/lifecycle.md` — LIFE-01, LIFE-02 (both now *permitted, not currently
  realised* for their non-permanence halves).
- `docs/world_rules/magic-supernatural/supernatural-transformation.md` — STR-02 (bounds any reversal).
- `docs/plans/systemic_world/roadmap.md` — owned by `world-rule-catalog-design`; it is drafting the
  sequencing additions for user approval and will not edit the roadmap unilaterally.

## Related Stored Artifacts
- `staging_artifacts/TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION/`
- `stored_artifacts/TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK/`

## Related Code Areas
- `src/cognition/need_interpretation.py` — perceives a healing need nothing fulfils.
- `src/core/state.py` — `CombatComponent.hp`/`max_hp`, `WoundState`, `ScarState`.
- `src/systems/lifecycle_systems/lifecycle.py` — the sole declared authority for HP-death deactivation.
- `src/engine/apply.py` — the passive branch; no longer decides `active`.

## Assumptions / Open Questions
- Assumes the harsh-world property is **not** what the user wants permanently. If it is — permanent
  stakes, continuity purely through descendants — then this epic closes as a recorded, deliberate design
  decision, which is a perfectly good outcome and still better than leaving it undesigned.
- Whether recovery should be time-based, treatment-based, rest-based, or several, is open; BODY-05
  constrains the *shape* (declared, non-spontaneous) but not the mechanism.
- The rule owner's own hypothesis, still to be confirmed by the PR #276 before/after measurement:
  deactivation counts should be roughly unchanged while the consequence layer moves. If deactivations
  moved materially, that reading is wrong and the mortality change needs disclosure and re-baselining.

## Implementation Notes
_Epic — tracks child tickets; no direct implementation._

## Test Summary
_Epic — no direct implementation._

## Files Changed
_Epic — no direct implementation._

## Completion Summary
_Epic — closes when its child tickets are done, or when the user records the harsh-world property as a
deliberate design decision._
