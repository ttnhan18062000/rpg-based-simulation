---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
phase: open
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT

## Title
M5.1: Structure audit of src/ top-level packages (decisions only)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
One decision record with a row per tracked top-level src/ package: purpose, size, outside importers, architectural layer, decision. Extends D14's layer model (8 of 36 packages) to all 36. No code moves.

## Scope
- Write docs/plans/codebase_health/src_package_structure_audit.md: one row per tracked top-level package (36 on main 2026-10-04): one-line purpose, files and lines, outside importers, layer (record both D14 and the real import graph where they disagree), decision keep | merge-candidate into <pkg> | retire-candidate | investigate
- Focus: actions, logging, views, runtime, replay, the world* family (world, worldassembly, worldbuilding, worldgeneration, worldmodules), content / content_semantics, plus economy, platform, testing, strategy, quests. Show overlap with evidence (shared responsibilities, import edges), not assumption
- Every non-keep decision names the owning domain (normally rpg-planner) and goes to that planner as a note in .claude/handover/codebase-planner-outbox.md
- Record src/social/ and src/graphify-out/ as untracked local clutter for the owner to delete (no ticket action)

## Out of Scope
- Subpackages of domains/, observability/, engine/ (registry rows are top-level only)
- Renaming anything
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [ ] Audit doc has exactly one row per tracked top-level src/ package, count verified against git ls-files
- [ ] Every non-keep decision has an owning domain and a note written to .claude/handover/codebase-planner-outbox.md with status: pending
- [ ] Layer column covers all packages and records D14 disagreements
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-IMPORT-LINTER-EVALUATION

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/audits/D14_coupling_depth.md
- registries/system_registry.jsonl

## Related Stored Artifacts
None.

## Related Code Areas
- src/ (read only)
- docs/plans/codebase_health/

## Assumptions / Open Questions
- Nothing moves in M5 or before the owner reopens src/ (M7)
- Importer counts in the brief are grep counts; derive a real import graph (grimp or ast) for this audit
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes


## Test Summary

## Files Changed

## Completion Summary
