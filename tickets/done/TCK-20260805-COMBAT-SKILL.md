---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-COMBAT-SKILL
phase: open
date: 2026-08-05
tags: [skills, combat]
---

# TCK-20260805-COMBAT-SKILL

## Title
Author a bespoke skill for working in src/domains/combat_engagement/

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Domain-coverage sweep child ticket, from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`.
`src/domains/combat_engagement/` (10 files) is governed by `docs/mechanics/02_combat_laws.md`
(Mechanics Bible ch.2 — deterministic, non-random combat resolution) plus a dedicated
`docs/simulation/domains/combat_engagement_contract.md` (10-file domain contract: "produces a
subjective pre-combat assessment... determines what CombatPosture the actor should adopt"). Zero
skill or agent coverage exists. Combat logic additionally executes as named phases
(`action_routing`, `combat_engagement`, `near_death_hardening`, `position_swaps`) inside the
32-phase `AuthoritativeApplyPipeline`, including a real, non-obvious causal rule ("Sliding State":
if Actor A kills Target T mid-tick, Actor B processed later sees T as already dead).

## Scope
- Author `.claude/skills/combat-mechanics/SKILL.md` (or similar — Plan decides exact naming),
  sourced from `docs/mechanics/02_combat_laws.md` and `docs/simulation/domains/combat_engagement_contract.md`.
- Must correctly reference `docs/engine/authoritative_pipeline.md`'s `action_routing` /
  `combat_engagement` / `near_death_hardening` / `position_swaps` phases and the Sliding State
  causal rule — a skill that doesn't account for this ordering would give actively wrong guidance
  about combat outcome sequencing.
- Cover: the deterministic damage formula, tactical modifiers, the pre-combat assessment vs.
  authoritative resolution distinction (the contract doc's own "NOT authoritative" framing for the
  engagement stage), and durability decay.

## Out of Scope
- Building new combat code or fixing any real bug found while authoring the skill — file a
  separate ticket if one is found.
- `docs/combat/` rulebooks (`combat_movement_overhaul_spec.md`, `observability_rulebook.md`,
  `rollout_hardening_rulebook.md`) — read as needed but not the primary source; the Mechanics
  Bible chapter and the domain contract are.

## Acceptance Criteria
- [x] New skill (`.claude/skills/combat-mechanics/SKILL.md`) authored, sourced from
      `02_combat_laws.md` + `combat_engagement_contract.md`, cross-referencing
      `action_routing`/`position_swaps`/`combat_engagement`/`near_death_hardening` and the
      Sliding State rule with its real phase name and Compliance ID.
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-SYSTEMS-SKILL, TCK-20260805-COGNITION-STRATEGY-SKILL, TCK-20260805-PROGRESSION-ENTITIES-SKILL (sibling domain-gap tickets)

## Related Docs
- `docs/mechanics/02_combat_laws.md`
- `docs/simulation/domains/combat_engagement_contract.md`
- `docs/engine/authoritative_pipeline.md` (action_routing/combat_engagement/near_death_hardening/position_swaps phases, Sliding State rule)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/domains/combat_engagement/`
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact skill naming — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/combat-mechanics/SKILL.md`, `source: project`. Grounded in exact real
values: the Fractional Armor Mitigation damage formula, all 7 tactical modifiers with their real
numeric values, durability decay rates, wound thresholds (`> 25% max HP`), kill reward formulas,
Hero's Journey generation rule, AoE splash percentages, all 10 real `CombatPosture` values, the
4-stage sub-service pipeline (confirmed 1:1 against real file names via `ls
src/domains/combat_engagement/`), and the 4 real pipeline phases with their real Compliance IDs.
Deliberately put the domain contract's "NOT authoritative" framing first, before the damage
formula — confirmed by test to appear earlier in the file — since it's the single easiest thing to
get backwards in this domain (per the ticket's own framing). The Sliding State causal rule is
stated with its real phase (`action_routing`), file (`src/engine/pipeline_phases/actions.py`), and
Compliance ID (`TOWN-149`), not paraphrased loosely.

Applied the now-established mechanism directly: registered `combat-mechanics` in
`agent-orchestration/skills.yaml`, used `layer: combat` (already registered) for staging
artifacts, regenerated the `.agents/` Codex mirror.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_combat_mechanics_skill_content.py` — 8 tests, all passing: valid frontmatter
with `source: project`; the real damage formula present verbatim; all 7 tactical modifiers
present; all 10 `CombatPosture` values present; "NOT authoritative" confirmed to appear before the
damage formula (ordering test, not just presence); the Sliding State rule + its real phase name +
Compliance ID + exact consequence text present; `docs/ai/skills.md` lists it; `.agents/` mirror
body matches. Regression check: `pytest tests/agent_orchestration_codex_adapter/` — 27 passed.
`doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` — no parity entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS, first pass clean.

## Files Changed
- `.claude/skills/combat-mechanics/SKILL.md` (new) — the skill.
- `.agents/skills/combat-mechanics/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/tools/test_combat_mechanics_skill_content.py` (new) — 8 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Authored a skill covering both layers of this domain — the subjective, non-authoritative
pre-combat assessment and the deterministic, authoritative resolution law — with the distinction
between them stated first and prominently, since conflating the two is the most likely real
mistake an agent working in this domain could make. Every numeric value and phase citation is
verified against real source docs, not approximated. No known material gap.
