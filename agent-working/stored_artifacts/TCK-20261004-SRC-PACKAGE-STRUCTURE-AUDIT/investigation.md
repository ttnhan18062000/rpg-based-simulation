---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT

- 36 tracked top-level packages; `src/social/` and `src/graphify-out/` untracked clutter.
- A grimp build over `src` finds 215 modules (namespace packages without `__init__.py`): unusable for this audit; own `ast` scan used. Mixed `src.x` and bare `x` import forms exist.
- D14 disagreements: `core` imports content, domains, engine, logging, replay, systems; `content` imports engine, worldassembly, worldmodules.
- 0 src importers: actions, runtime, testing, views (plus entry points cli, lab, rendering).
- Overlaps with evidence: QuestGenerator/QuestTemplate (quests vs systems/world_systems), CapacityService x2 in strategy, SkillScalingService (progression vs engine/rpg_depth), ValidationIssue (content vs worldbuilding).
- Import cycles: content<->content_semantics, core<->replay, worldbuilding<->worldmodules, worldbuilding<->worldassembly, worldbuilding<->worldgeneration.
- Deviation noted: `plan.md` was written after the audit and was not sent to the planner first (docs-only ticket); the planner reviews the commit.
