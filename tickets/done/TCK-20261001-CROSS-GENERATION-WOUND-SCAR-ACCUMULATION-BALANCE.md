---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261001-CROSS-GENERATION-WOUND-SCAR-ACCUMULATION-BALANCE
phase: done
date: 2026-10-01
tags: [lifecycle, combat, progression, simulation-quality]
---

# TCK-20261001-CROSS-GENERATION-WOUND-SCAR-ACCUMULATION-BALANCE

## Title
Measure whether wound/scar penalties accumulating across all four hero generations is a balance problem,
once SimQ is trustworthy enough to measure it

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE` makes `REBIRTH` restore
`combat.hp = max_hp` and `alive = True`, and deliberately **does not** clear accumulated
`CombatComponent.wounds` / `.scars`.

That no-reset choice is **rule-compliant and was the correct default** — BODY-06 permits persistent
injury after the harmful event ends, HP-01/ID-05 ("history survives") and LIFE-01's "identity continues"
both lean toward carrying rather than resetting, and CAUSE-01/CAUSE-05 require a declared cause for any
durable-record deletion. `world-rule-catalog-design` confirmed this on 2026-10-01 and was explicit that
**a reset would be legitimate only as a declared part of the rebirth law, which is a gameplay/balance
decision for the user, not a rule requirement**.

**This ticket exists because the consequence is unmeasured, not because it is known to be wrong.** With
no-reset, a hero's `atk_penalty` / `def_penalty` / `speed_penalty` / `max_hp_penalty` stack carries
across all four generations, so a Gen-4 hero can be meaningfully weaker than a Gen-1 hero even at
`max_hp`. Whether that is good design (rebirth is costly, decline is dramatic) or a balance defect
(late generations are unplayably crippled) is a question for evidence.

**It is filed as KEEP rather than worked now** because the instrument needed to answer it is
untrustworthy: 13 of 15 SimQ grade anchors are red on untouched `main`
(`TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`), of which ~10 are class (c)
non-deterministic. Any balance claim made against SimQ today would be unreadable, and the death batch
explicitly excluded SimQ as a verification signal for that reason. Do not open this until the SimQ
reporting-path work lands and the anchors can distinguish a real shift from noise.

## Scope
- Measure the actual penalty accumulation across generations 1→4 with a focused, deterministic scenario
  (not the SimQ corpus): the total `atk`/`def`/`speed`/`max_hp` penalty a hero carries at each
  generation, and its effect on combat outcome rates.
- State whether the accumulation is intended decline or a defect, with evidence.
- If a reset or partial reset is wanted, it must be **declared in `docs/mechanics/02_combat_laws.md`'s
  rebirth law** as part of that law — not added as a side effect of the rebirth branch, and not as a
  general `heal` helper (BODY-05 binds general recovery separately).

## Out of Scope
- Changing the no-reset behaviour without evidence. The default is rule-compliant; this ticket gathers
  the balance evidence that would justify revisiting it.
- Building a general HP/injury recovery mechanism. BODY-05 records that none exists and binds any future
  one; rebirth's restore is a declared lifecycle-transition consequence, not a recovery system.
- Fixing the SimQ anchors — that is `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`.

## Acceptance Criteria
1. Penalty accumulation per generation is measured with a deterministic scenario and recorded.
2. A stated verdict on whether it is intended decline or a balance defect, with evidence, not assumption.
3. If a reset is adopted, it is declared in the rebirth law with a parity entry and an
   `intentional_divergences.md` entry if it departs from the Bible.
4. The measurement does not rely on any SimQ grade anchor currently classified (c).

## Related Tickets
- `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE` — the batch that established
  no-reset and whose rule review requested this follow-up.
- `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED` — the blocker; this ticket waits on it.

## Related Docs
- `docs/mechanics/02_combat_laws.md` — "The Hero's Journey (Generations)", the rebirth law.
- `docs/world_rules/life-body/body-condition.md` — BODY-03, BODY-05, BODY-06.
- `docs/world_rules/life-body/lifecycle.md` — LIFE-01.
- `docs/world_rules/foundations/causality.md` — CAUSE-01, CAUSE-05.

## Related Stored Artifacts
- `stored_artifacts/TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE/`

## Related Code Areas
- `src/core/state.py` — `CombatComponent.wounds`, `.scars`, and the `*_penalty` fields on
  `WoundState`/`ScarState`.
- `src/engine/combat.py:182-187` — the rebirth branch.

## Assumptions / Open Questions
- Assumes the death batch lands with no-reset as planned. If the user changes decision 4 during
  implementation, this ticket's premise changes and it should be re-scoped or closed.
- Whether a *partial* reset (e.g. wounds clear, scars persist) is the better design is open; `WoundState`
  and `ScarState` are already distinct types with different durability semantics, so the split exists.

## Implementation Notes
_To be completed during implementation._

## Test Summary
_To be completed during implementation._

## Files Changed
_To be completed during implementation._

## Completion Summary

**WITHDRAWN, not implemented — 2026-10-01, same day it was filed. Its premise ceased to exist.**

This ticket existed to measure wound/scar penalty accumulation across a hero's four rebirth
generations. Later the same day, `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION` retired
hero rebirth entirely (an undeclared resurrection failing STR-02/ID-02/CAUSE-04/ID-06, per
`world-rule-catalog-design` and a user decision). **With no rebirth there are no cross-generation
penalties to accumulate**, so there is nothing left to measure.

Closed on the explicit instruction of the rule owner that filed it: "close it rather than re-scope. Its
premise (cross-generation accumulation) no longer exists. If injury persistence ever matters for
balance, that's a fresh question."

No code, tests or docs were changed by this ticket. The durable finding it was built on — that
wounds/scars persist rather than being cleared, which is rule-compliant per BODY-06/HP-01/CAUSE-01 —
survives in `TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE` and is unaffected.
