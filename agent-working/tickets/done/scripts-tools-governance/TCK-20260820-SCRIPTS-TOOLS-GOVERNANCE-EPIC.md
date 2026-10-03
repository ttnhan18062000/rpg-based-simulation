---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC
phase: done
date: 2026-08-20
tags: [ai, process-improvement]
---

# TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC

## Title
Establish a scripts/ vs tools/ governance rule, clean up confirmed-orphaned files, add a lasting orphan-check

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P2

## Request Summary
User question this session: "what is the different between scripts/ and tools/, are they contain
unused?" — investigated via direct cross-reference search (Makefile, CI, tests, other
scripts/tools files, docs), not assumption. Found: no documented rule distinguishes `scripts/`
from `tools/` anywhere in this repo; `tools/` (52 top-level files) is healthy (only 2 orphaned,
both from the earliest stretch of repo history); `scripts/` (28 files) is not (6 orphaned, only 2
even referenced in the Makefile); and no standing mechanism catches this drift going forward. This
is a real, multi-part initiative — a documented rule (with a real decision behind it, not just a
description of the status quo), cleanup of 8 confirmed-orphaned files, and new tooling to prevent
recurrence — not a single mechanical fix.

## Scope
- Scope-only epic: full findings and proposed remediation steps are in
  `docs/plans/scripts_tools_governance_epic.md`. Detailed, investigated child tickets are not
  created yet.
- When work begins: run `create-tickets` against a proposal document scoped to this epic's items
  (rule + retire-or-keep decision for `scripts/`, cleanup of the 6 orphaned `scripts/` + 2
  orphaned `tools/` files, a new lasting orphan-check mechanism), producing investigated child
  tickets in `tickets/todos/scripts-tools-governance/`.

## Out of Scope
- Auditing code quality *within* files that are still referenced — this epic is about orphaned
  files, not a broader code-quality review.
- `tools/agent_codex_*`/`agent_orchestration_*`/`agent_replay_*` — already tracked separately
  under `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC` (currently blocked), not folded in here.

## Acceptance Criteria
- [x] `docs/plans/scripts_tools_governance_epic.md` is reviewed and its scope confirmed accurate.
- [x] Child tickets are created via `create-tickets` once this epic is chosen for action.
- [x] This epic is not closed until its child tickets (once created) reach `tickets/done/`.
  Both `TCK-20260929-RETIRE-SCRIPTS-DIR` and `TCK-20260929-TOOLS-ORPHAN-FILE-CHECK` are in
  `tickets/done/` as of 2026-09-29 (confirmed via `tools/epic_folder_status.py`:
  `all_children_done: true`).

## Related Tickets
- TCK-20260929-RETIRE-SCRIPTS-DIR
- TCK-20260929-TOOLS-ORPHAN-FILE-CHECK

Child tickets created by create-tickets on 2026-09-29; order in SEQUENCE.md. Otherwise this epic originates from live session investigation, not the D23/D24 audit tree
(`TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC` and its sub-epics), so it stands independently.

## Related Docs
- docs/plans/scripts_tools_governance_epic.md

## Related Stored Artifacts
stored_artifacts/TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC/

## Related Code Areas
- scripts/
- tools/ (top-level files; not the agent_codex_*/agent_orchestration_*/agent_replay_* subdirs)
- Makefile

## Assumptions / Open Questions
- Whether `scripts/` should be retired/merged into `tools/` entirely (given its poor health vs.
  `tools/`'s demonstrated maintainability), or kept with a real, narrower, explicitly-documented
  purpose, is an open decision for whoever scopes the child tickets — not pre-decided here.
- Which of the 8 confirmed-orphaned files have reference value worth archiving (vs. outright
  deletion) is left to that same judgment call, per file.

## Implementation Notes
Scoped into 2 child tickets via `create-tickets` on 2026-09-29, both implemented and closed the
same day. See each child ticket's own Implementation Notes for the real work (scripts/
retirement into tools/perf, tools/release, tools/maintenance plus a 9th orphan found live and a
deeper turbo_run.py defect chain beyond what the investigation anticipated; the new on-demand
tools/gate_checks/tools_orphan_check.py orphan-check mechanism).

## Test Summary
No direct tests of its own (scope-only epic) — each child ticket carried its own, both green.

## Files Changed
None directly (scope-only epic) — see each child ticket's own Files Changed.

## Completion Summary
Both scoped child tickets closed 2026-09-29: `TCK-20260929-RETIRE-SCRIPTS-DIR` (scripts/
retired entirely, its live files moved into new tools/ subpackages, 13 dead/orphaned files
deleted) and `TCK-20260929-TOOLS-ORPHAN-FILE-CHECK` (new on-demand, report-only orphan-file
check covering all of tools/). All 3 acceptance criteria met. This epic's full remit —
documented rule, orphan cleanup, and a lasting prevention mechanism — is now delivered.
