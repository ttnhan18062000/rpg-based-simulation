---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-PROGRESSION-ENTITIES-SKILL
phase: open
date: 2026-08-05
tags: [skills, progression]
---

# TCK-20260805-PROGRESSION-ENTITIES-SKILL

## Title
Author a bespoke skill for working in src/entities/ and src/progression/

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
`src/entities/` and `src/progression/` are governed by `docs/mechanics/01_entity_anatomy.md`
(Mechanics Bible ch.1 — core attributes, derived stats, biological pressures, XP scaling) plus a
dedicated companion sub-contract, `docs/mechanics/attribute_progression_contract.md` ("exact XP
threshold formulas"). Zero skill or agent coverage exists.

## Scope
- Author `.claude/skills/progression-entities/SKILL.md` (or similar — Plan decides exact naming),
  sourced from `docs/mechanics/01_entity_anatomy.md` and `docs/mechanics/attribute_progression_contract.md`.
- Must correctly reference the authoritative pipeline's `evolution` and `progression_conversion`
  phases (`docs/engine/authoritative_pipeline.md`) — "Applies entity evolution and stat boosts"
  and "converts progression points to levels/skills" respectively.
- Cover: core attributes (STR/DEX/INT/END/CHA), derived stats, biological pressures, and the exact
  XP threshold formulas from the companion contract doc.

## Out of Scope
- Building new entity/progression code or fixing any real bug found while authoring the skill —
  file a separate ticket if one is found.

## Acceptance Criteria
- [x] New skill (`.claude/skills/progression-entities/SKILL.md`) authored, sourced from
      `01_entity_anatomy.md` + `attribute_progression_contract.md`, cross-referencing the
      authoritative pipeline's `evolution` (23) and `progression_conversion` (24) phases.
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMBAT-SKILL, TCK-20260805-COGNITION-STRATEGY-SKILL, TCK-20260805-SYSTEMS-SKILL (sibling domain-gap tickets)

## Related Docs
- `docs/mechanics/01_entity_anatomy.md`
- `docs/mechanics/attribute_progression_contract.md`
- `docs/engine/authoritative_pipeline.md` (evolution/progression_conversion phases)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/entities/`
- `src/progression/`
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact skill naming — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/progression-entities/SKILL.md`, `source: project`. Grounded in exact
values: 9 core attributes, real derived-stat formulas, the real class registry, real biological
decay rates/thresholds, the real XP threshold table (100/283/520/1,118/3,162/8,944/35,355/~969,440),
the exact 5-step `_execute_level_up` algorithm, all 4 real `PROG-06x` AP-allocation gates, and the
exact 6-step `LevelingService.recalculate_combat_stats()` order — verified in correct relative
order by a structural test, not just presence, since applying these steps out of order would
silently produce wrong derived stats.

Applied the now-established mechanism directly: registered `progression-entities` in
`agent-orchestration/skills.yaml`, regenerated the `.agents/` Codex mirror.

**Real gate catch during Verify**: first `run_static_precheck` pass failed `frontmatter_valid` —
reused `layer: progression` in all 3 staging artifacts, conflating the `progression` **tag**
(registered earlier this session in `tag_registry.jsonl` for this exact ticket) with a `layer`
value (a separate registry, `layer_registry.jsonl`, which has no `progression` entry). Fixed to
`layer: mechanics` (the genuinely-fitting registered value, since both source docs are Mechanics
Bible content), re-ran, clean pass. Same error class this session already caught once on
`SIMQ-DEV-SKILL` — worth noting as a recurring trap (tag registry and layer registry share no
values, easy to conflate when a ticket's own tag happens to look like a plausible layer name).

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_progression_entities_skill_content.py` — 9 tests, all passing: valid
frontmatter with `source: project`; all 9 core attributes present; real derived-stat formulas
present verbatim; real XP threshold values present; all 4 `PROG-06x` compliance IDs present; the
6-step recalculation order verified in correct relative sequence (not just presence); both real
pipeline phases present; `docs/ai/skills.md` lists it; `.agents/` mirror body matches. Regression
check: `pytest tests/agent_orchestration_codex_adapter/` — 27 passed. `doc_staleness_check.py` →
PASS. `clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity
entry needed. `run_static_precheck('standard', ...)` — all 7 conditions PASS (second pass, after
the layer fix above).

## Files Changed
- `.claude/skills/progression-entities/SKILL.md` (new) — the skill.
- `.agents/skills/progression-entities/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/tools/test_progression_entities_skill_content.py` (new) — 9 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Closed the last of the epic's 6 confirmed domain-coverage gaps. Every formula, threshold, and gate
ID is verified against real docs, with the 6-step recalculation order specifically tested for
correct sequence rather than mere presence, since an out-of-order recalculation would silently
produce wrong stats. Caught and fixed a real, recurring frontmatter error class (tag-registry vs.
layer-registry conflation) already seen once earlier this session. No known material gap. This
was the final child ticket in the domain-coverage-sweep group of `SKILL-CATALOG-MODERNIZATION-EPIC`.
