---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
phase: done
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT

## Title
M5.1: Structure audit of src/ top-level packages (decisions only)

## Status
DONE

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
- [x] Audit doc has exactly one row per tracked top-level src/ package, count verified against git ls-files
- [x] Every non-keep decision has an owning domain and a note written to .claude/handover/codebase-planner-outbox.md with status: pending
- [x] Layer column covers all packages and records D14 disagreements
- [x] `git diff --stat <base>...HEAD` lists no path under src/

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
- Own `ast` import scan instead of grimp: `src/` has namespace packages (no `__init__.py` in core, api, perf, certification, content_semantics), so grimp sees 215 of 744 files. Importer counts are file counts across src, tests, tools, codebase, agent-working, experiments and visual_assets.
- Outbox messages 7 (rpg-planner) and 8 (testing-planner) written to `.claude/handover/codebase-planner-outbox.md` with status: pending (the file is git-ignored).
- Deviation: `plan.md` was written after the audit, not sent to the planner first (docs-only ticket); the planner reviews the commit.
- Findings the owner should see: `core` imports engine/domains/systems (D14 says nothing); five import cycles; four packages with only test importers.


- **Correction (2026-10-04, found during ticket 4):** the scan mapped the bare stdlib `import logging` / `import platform` onto `src/logging` and `src/platform`. `logging` has 3 src importing files, not 112; `platform` 27 src / 139 outside (not 28 / 157); `worldmodules` 33 outside (not 42, a brief figure); `content` 67 outside. `logging` moved from keep to investigate; no other decision changed. The package registry row and outbox Message 7 were updated.
- Also corrected: 20 of 36 top-level packages have no `__init__.py`, not five (the five were the first lines of a truncated listing).

## Test Summary
No code. Checked: 36 audit rows against `git ls-files src` (none missing), frontmatter validator on the doc, ticket and artifacts, empty `git diff --stat origin/main -- src`.

## Files Changed
- docs/plans/codebase_health/src_package_structure_audit.md (new)
- agent-working/tickets, stored artifacts, monitoring shards

## Completion Summary
Audit of the 36 tracked top-level `src/` packages written with layer, evidence and a decision per package: 7 non-keep decisions routed to rpg-planner and 1 to the testing planner by pending outbox notes. No `src/` change.
