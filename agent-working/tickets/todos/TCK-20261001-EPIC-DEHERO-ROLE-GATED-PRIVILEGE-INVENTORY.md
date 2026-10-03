---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY
phase: open
date: 2026-10-01
tags: [architecture, lifecycle, combat, progression]
---

# TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY

## Title
Stop relying on `EntityRole.HERO` as a privileged status — inventory every HERO-gated behaviour first,
then re-ground real capabilities on real state

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P1

## Request Summary
**User direction, 2026-10-01:** *"we should not rely to the term 'hero' anymore."* Given while reviewing
the death batch, immediately after deciding to retire hero rebirth
(`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`).

**Interpretation, confirmed with the user:** no mechanic, rule or law may be gated on `EntityRole.HERO`
as a *privileged status*. Roles remain **classification** (ID-02: identity and its fate are not
determined by role). Any real capability a "hero" currently receives for free must come from **real
state** (CAUSE-04: capability gates must be real state, not narrative) — skills, equipment, reputation,
standing. **This is not a mass rename of every identifier.**

**Why it is an epic and not a sweep.** Retiring rebirth already exposed the pattern: a role label was
granting an exemption from death that no Rule ID authorised, it had never worked at runtime, and an
earlier ticket had *hardened its reachability* without anyone asking whether it should exist. The same
shape is likely to recur across rewards, content and events, and each instance needs a different answer —
remove, re-ground, or leave alone. Fixing them piecemeal would repeat the mistake.

**Sequencing, per the user: inventory first, after the current batch merges.** The user chose
"inventory first, after the batch" explicitly. No child ticket may be planned before the inventory
exists. This is the same discipline the user applied to the earlier altitude concern: inventory first, no
piecemeal fixes.

## Scope
- **Child 1 (the gate for everything else): the inventory.** Enumerate every place `EntityRole.HERO`
  (or the word "hero") grants or implies special behaviour, and classify each as:
  1. **a privilege to remove** — a benefit with no in-world basis;
  2. **a capability to re-ground on real state** — a benefit that should exist but must be earned through
     skills / equipment / reputation / standing;
  3. **harmless naming** — an identifier or content name with no behavioural consequence.
  Read-only investigation. Produces a classified table with a code citation per row. **No fixes.**
- Child tickets per cluster, planned only **after** the inventory and prioritised from it.

Known live instances, to be confirmed and classified by the inventory rather than treated as its
conclusion:
- `combat.py:136` — `is_lethal` forced `False` for HERO. **Already in scope of the rebirth retirement**,
  since leaving it would make a lethal hit on a former hero resolve as terminal `DEFEAT`. Not re-done
  here.
- `combat_rewards.py` — `HERO_KILL` reward category, `xp_multiplier=20`/`gold_multiplier=50` vs
  MONSTER's 10/5, plus the Bible 02 reward table that documents it.
- Hero routing / guild content — the `hero_guild_routing` world, the `hero_adventurers` module.
- `HERO_*` event names in the observability layer.

## Out of Scope
- **Any fix before the inventory exists.** That is the point of the epic's shape.
- `EntityRole` as a concept, and whether roles should exist at all. The user confirmed the narrower
  reading; roles stay as classification.
- The rebirth retirement itself — `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`, already
  decided and planned, including its `combat.py:136` and `combat_rewards` rebirth-eligibility changes.
- A mass rename of identifiers or content names for their own sake. Category 3 rows are recorded and
  **left alone** unless a later child ticket has an independent reason.
- Designing resurrection. The user chose retirement.

## Acceptance Criteria
1. The inventory exists as a stored artifact: every HERO-gated behaviour, with a code citation, assigned
   exactly one of the three categories, and a one-line justification per row.
2. Each category-2 row names the **real state** that should gate the capability instead, and cites the
   rule that requires it (CAUSE-04, ID-02).
3. Child tickets are filed from the inventory, prioritised, and traceable to its rows — **none filed
   before it**.
4. Any row that turns out to be a rule violation rather than a design preference is flagged to
   `world-rule-catalog-design` for a Rule-level ruling, as the rebirth case was.
5. A statement on whether `EntityRole.HERO` can ultimately be removed, or must remain as pure
   classification — answered from the inventory, not assumed up front.

## Related Tickets
- `TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION` — the first instance of this pattern, found
  and fixed before this epic was scoped. Its analysis is the template.
- `TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER` / `...-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE`
  — the death batch whose review surfaced the direction.

## Related Docs
- `docs/world_rules/foundations/causality.md` — CAUSE-04.
- `docs/world_rules/identity/` — ID-02, ID-06.
- `docs/world_rules/magic-supernatural/supernatural-transformation.md` — STR-02, the rule the rebirth
  case turned on.
- `docs/mechanics/02_combat_laws.md` — the reward table and the retired Hero's Journey law.

## Related Stored Artifacts
- `staging_artifacts/TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION/` — the worked example of
  the analysis this epic generalises.

## Related Code Areas
- `src/core/enums.py` — `EntityRole`
- `src/engine/combat_rewards.py`, `src/engine/combat.py`
- `src/observability/event_extractor.py` — `HERO_*` event names
- `data/worlds/` — `hero_guild_routing`; `src/worldmodules/` — `hero_adventurers`

## Assumptions / Open Questions
- Assumes the user's direction is about **privilege**, not naming. Confirmed with the user 2026-10-01,
  but the inventory should surface any row where that distinction is genuinely unclear rather than
  forcing it into a category.
- Whether `HERO_KILL`'s reward multipliers are a privilege (category 1) or a legitimate
  difficulty-scaling signal that happens to be keyed on role (category 2) is **genuinely open** and is
  the inventory's first interesting question. Do not pre-answer it.
- Unknown how much of the hero-guild/adventurer content is behavioural vs naming. The inventory decides.

## Implementation Notes
_Epic — tracks child tickets; no direct implementation._

## Test Summary
_Epic — no direct implementation._

## Files Changed
_Epic — no direct implementation._

## Completion Summary
_Epic — closes when its child tickets are done._
