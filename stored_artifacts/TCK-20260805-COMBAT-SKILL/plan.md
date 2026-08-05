---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260805-COMBAT-SKILL
artifact_type: plan
tags: [skills, combat]
---

# Plan — TCK-20260805-COMBAT-SKILL

## New skill: `.claude/skills/combat-mechanics/SKILL.md`
`source: project` frontmatter. Sections:
1. **When to use** — editing `src/domains/combat_engagement/`, damage/tactical-modifier logic,
   wound/durability logic, or debugging combat sequencing/ordering issues.
2. **Pre-combat assessment vs. authoritative resolution** — the contract doc's "NOT authoritative"
   framing stated first and prominently, since it's the single easiest thing to get backwards.
3. **`CombatPosture` and the sub-service pipeline** — 10 values, 4 stages, stateless/deterministic
   entry point, the domain-isolation constraints.
4. **The deterministic damage formula + tactical modifiers** — exact formula and all 7 modifier
   values.
5. **Durability decay, wounds, kill rewards, Hero's Journey**.
6. **AoE logic**.
7. **The authoritative pipeline phases + the Sliding State rule** — stated with its real
   Compliance IDs and the exact causal-ordering consequence, since this is the ticket's own
   explicit highest-priority citation.
8. **Real test paths for debugging**.

## `docs/ai/skills.md` + contract registration + `.agents/` mirror
Same mechanism as the prior 3 domain-skill tickets.

## Tests
New `tests/tools/test_combat_mechanics_skill_content.py`:
- Real damage formula string present verbatim.
- All 7 tactical modifier names + values present.
- All 10 `CombatPosture` values present.
- The Sliding State rule text present, plus its real phase name/Compliance ID.
- The "NOT authoritative" framing present (a real, easy-to-get-backwards distinction).
- `docs/ai/skills.md` lists it; `.agents/` mirror matches.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Acceptance-Criteria Map
- AC1 (sourced from real Mechanics Bible + domain contract, cross-references pipeline + Sliding
  State) → sections 2-7, each cited to a real doc section/phase.
- AC2 (`docs/ai/skills.md` updated) → Document-Update step.
