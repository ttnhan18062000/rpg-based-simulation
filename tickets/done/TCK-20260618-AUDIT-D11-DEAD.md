---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260618-AUDIT-D11-DEAD
phase: done
date: 2026-06-18
tags: [audit, dead-code, orphaned-modules, v1-legacy, cleanup]
---

# TCK-20260618-AUDIT-D11-DEAD

## Title
D11 — Dead Code & Orphaned Modules Audit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Identify src/ modules that are never imported from the live pipeline or test suite.
Characterise whether orphans are V1 legacy, experimental, or accidentally isolated.

## Scope
- Import graph survey of all top-level src/ directories
- Characterise each orphan cluster by V1 pattern and V2 supersession
- Verify no hidden live path exists (systems/ duplicate check)

## Out of Scope
- Removing orphan code (separate cleanup ticket)
- Test suite reorganisation

## Acceptance Criteria
- docs/audits/D11_dead_code.md written with scoring rubric
- audit_dimensions.md D11 row updated to done
- Working log and monitoring entries written

## Related Tickets
- TCK-20260618-AUDIT-EPIC (parent)
- TCK-20260618-AUDIT-D12-PATTERNS (F3: design_patterns.md describes V1 patterns — ai/ confirms they exist as live files)

## Implementation Notes
9 top-level src/ directories confirmed zero importers from live pipeline and test suite.
36 files, ~109 KB of V1 code. Key clusters: ai/ (V1 GoalScorer), town/ (V1 building system),
entities/ (V1 archetype factory), progression/ (V1 leveling services), content_semantics/.
systems/quest_generator.py is a 2-line re-export facade only.
No src_legacy/ or tests_legacy/ directories found — legacy was restored in TCK-20260427
but these directories were never cleaned up.

## Test Summary
N/A

## Files Changed
- docs/audits/D11_dead_code.md (create)
- docs/audits/audit_dimensions.md (update)
- tickets/working_log.csv (append)
- agent-monitoring/ (append)

## Completion Summary
D11 audit complete. 9 orphan directories confirmed (36 files, ~109 KB). src/ai/ highest risk (12/15)
due to compliance ID debt and GoalScorer confusion with design_patterns.md. src/town/ + src/quests/
co-dependent orphan pair (11/15). Rest of src/ is clean — no commented code, no backup files.
