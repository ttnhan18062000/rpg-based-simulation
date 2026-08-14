---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260805-SYSTEMS-SKILL
phase: open
date: 2026-08-05
tags: [skills, economy]
---

# TCK-20260805-SYSTEMS-SKILL

## Title
Author a bespoke skill for working in src/systems/ (economy, crafting, quests, guild, market)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Domain-coverage sweep child ticket, from `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC`. The
largest confirmed gap in the sweep: `src/systems/` is 70 files / 6635 lines (economy.py,
crafting.py, harvest_system.py, market.py, quest_system.py, guild_system.py, town_service.py, plus
6 `*_systems/` subdirectories for economy/world/social/strategic/lifecycle). A real Mechanics
Bible chapter (`docs/mechanics/03_economic_laws.md`, atomic conservation/harvesting/trade/crafting
laws) governs authoritative domain law here, uncaptured by any skill. 32 tickets reference core
keywords (economy/crafting/harvest/market/quest_system/guild_system). Zero skill or agent
coverage.

## Scope
- Author `.claude/skills/systems-economy/SKILL.md` (or similar — Plan decides exact
  naming/boundary, and whether one skill covers the whole `src/systems/` surface or it needs
  splitting given its size), sourced from `docs/mechanics/03_economic_laws.md` and any other real
  contract docs for this subsystem.
- Must correctly reference the authoritative refinement pipeline (`docs/engine/authoritative_pipeline.md`)
  since several of this domain's operations execute as named phases inside that 32-phase pipeline
  (e.g. `resource_transactions`, `shop`, `blacksmith`, `quest_rewards`) — the skill cannot
  contradict or duplicate that pipeline's causal ordering.
- Cover: atomic conservation rules, the economy/crafting/harvest/market/quest/guild system
  boundaries, and how a change here interacts with the pipeline phases that consume its output.

## Out of Scope
- Building new economy/crafting code or fixing any real bug found while authoring the skill — file
  a separate ticket if one is found.
- Any change to `docs/engine/authoritative_pipeline.md` itself — read-only reference.

## Acceptance Criteria
- [x] New skill (`.claude/skills/systems-economy/SKILL.md`) authored, sourced from
      `03_economic_laws.md` + `docs/systems/buildings_and_economy.md` (a second real doc found
      during Investigate, not cited in the ticket's own Related Docs), correctly cross-referencing
      the pipeline's `blacksmith`/`quest_rewards`/`shop`/`resource_transactions` phases with their
      real Compliance IDs.
- [x] Explicit decision: one skill, scoped to documented laws (not a file-by-file tour of all 25
      files + 5 subdirs), with an explicit "What This Skill Does NOT Cover" disclosure rather than
      silently over-claiming coverage.
- [x] `docs/ai/skills.md` updated to list the new skill.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (parent epic)
- TCK-20260805-COMBAT-SKILL, TCK-20260805-COGNITION-STRATEGY-SKILL, TCK-20260805-PROGRESSION-ENTITIES-SKILL (sibling domain-gap tickets, all reference the same pipeline docs)

## Related Docs
- `docs/mechanics/03_economic_laws.md`
- `docs/engine/authoritative_pipeline.md` (the 32-phase pipeline this domain's logic executes inside)

## Related Stored Artifacts
None yet (standard tier, will be created).

## Related Code Areas
- `src/systems/` (all files and `*_systems/` subdirectories)
- `.claude/skills/` (new skill target)

## Assumptions / Open Questions
Exact skill naming/scope boundary (one skill vs. split, given the domain's real size) — Plan phase decides.

## Implementation Notes
Authored `.claude/skills/systems-economy/SKILL.md`, `source: project`. Found and used a second
real doc beyond the ticket's own citation: `docs/systems/buildings_and_economy.md` (blacksmith
recipes, Adventurer's Guild, Quest System) — gives genuine guild/quest coverage grounded in real
content rather than fabricating it or silently omitting it. Cites real formulas verbatim: the
reputation discount (`entity_rep = clamp(public_reputation, 0.0, 2.0) / 2.0`, up to 20% off),
`ECOLOGY_INTERVAL = 200`, `MAX_ACTIVE_QUESTS = 3`, real inventory limits (16 slots/50.0kg). Caught
and correctly stated a real, easy-to-conflate distinction: the quest *model* lives in
`src/core/quests.py`, the runtime *system* in `src/systems/quest_system.py` — two different files.
Also caught and honestly corrected a minor factual error in the ticket's own Request Summary
(cited "6 `*_systems/` subdirectories," real count confirmed via `ls` is 5) — noted in
investigation.md rather than silently perpetuated.

Applied the now-established mechanism directly: registered `systems-economy` in
`agent-orchestration/skills.yaml` before regenerating the `.agents/` Codex mirror.

Done entirely directly (no subagents — hard 200-agent spawn cap, per explicit user decision to
continue solo).

## Test Summary
New `tests/tools/test_systems_economy_skill_content.py` — 8 tests, all passing: valid frontmatter
with `source: project`; the real reputation-discount formula present verbatim; real inventory/
ecology/quest constants present; all 4 real pipeline phase names + their real Compliance IDs
present; the `src/core/quests.py`/`src/systems/quest_system.py` distinction stated; the explicit
out-of-scope disclosure present; `docs/ai/skills.md` lists it; `.agents/` mirror body matches.
Regression check: `pytest tests/agent_orchestration_codex_adapter/` — 27 passed.
`doc_staleness_check.py` → PASS. `clean_data_runs_early()` → PASS.
`expected_subsystems_for_files()` → `{}` — no parity entry needed.
`run_static_precheck('standard', ...)` — all 7 conditions PASS (first pass clean, correct
`layer: economy` used this time per the prior ticket's caught error).

## Files Changed
- `.claude/skills/systems-economy/SKILL.md` (new) — the skill.
- `.agents/skills/systems-economy/SKILL.md` (new) — Codex mirror.
- `agent-orchestration/skills.yaml` — registered the new skill in the contract.
- `docs/ai/skills.md` — added to the Project-Level Skill Files table.
- `tests/tools/test_systems_economy_skill_content.py` (new) — 8 tests.

## Parity
No `src/` files touched. `expected_subsystems_for_files()` → `{}`. No parity ledger entry needed.

## Completion Summary
Closed the largest confirmed domain gap in this repo's skill catalog with a skill scoped honestly
to what's genuinely documented — economic laws, market formulas, crafting, quests, guild-level
overview — rather than either fabricating deeper `guild_system.py` internals with no doc backing
them or attempting an unwieldy file-by-file split of a 25-file/5-subdirectory domain. Found and
incorporated a second real doc not cited by the ticket itself, and caught two small factual
corrections (the quests.py/quest_system.py file split, the real subdirectory count) along the way.
No known material gap.
