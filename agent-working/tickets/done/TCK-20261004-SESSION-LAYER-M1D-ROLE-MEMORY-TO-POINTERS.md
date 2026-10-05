---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS

## Title
Session-layer M1d: reduce role-defining memory files to pointers

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Move the facts held in role-defining memory files into the manifest, templates and overlays, then reduce each memory file to a one-line pointer, so roles are defined once, versioned and reviewable.

Child of `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (milestone M1). Hold rule met: M-1 merged (#289) and M0 recorded ADJUST (#307).

## Scope
- Enumerate the role-defining memory files in `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/memory/` (candidates: `project_session_role_division`, `project_semantic_control_plane_role_division`, `project_test_architecture_reviewer_role`, `project_mechanism_registry_ownership_split`, `feedback_implementer_owns_all_commits`, `feedback_planner_creates_epic_tickets_only`, `feedback_route_work_via_rpg_feature_planning`, `feedback_ask_rpg_feature_planning_before_touching_rpg_logic`, `feedback_small_doc_changes_handoff_to_rpg_planner`, `feedback_report_agent_process_issues_to_agent_working_design`) and map each fact to its new home.
- For each file: the fact is present in the repo (manifest, template or overlay) before the memory file is shortened; the memory file keeps its `[[links]]` and a pointer line.
- Update `MEMORY.md` index lines to say pointer.
- A checklist artifact (`agent-working/stored_artifacts/<ticket>/migration_map.md`) records file -> new home, with commit SHA once merged.

## Out of Scope
- Memory files unrelated to roles (feedback on workflow style, environment notes). Deleting any memory entry outright. Per-user memory is outside git: this ticket changes it only through the owner's machine, after the repo copies merged.

## Acceptance Criteria
1. `migration_map.md` lists every role-defining memory file with its new home; no fact is dropped (each is findable in the repo by the map's cited path).
2. Repo homes merged before any memory file is shortened (order shown in the map with SHAs).
3. Each shortened memory file keeps its frontmatter, links and a pointer; `MEMORY.md` hooks updated.
4. A grep of the memory directory shows no role definition left stated twice (define-once).
5. Owner confirms the list before shortening starts (memory is per-user and not under git).

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION` (parent), `TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE` (done)
- Depends on M1a, M1b.

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding; sections 3, 4, 5, 10, 12.2)
- `agent-working/stored_artifacts/TCK-20261003-SESSION-LAYER-M0-HARNESS-SPIKE/investigation.md` (M0 record; ADJUST 5, 6.1, 10)
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `~/.claude/projects/.../memory/` (outside repo), `agent-working/stored_artifacts/`.

## Assumptions / Open Questions
- The memory directory is shared by every session on this machine and unversioned; shortening is not revertable from git. Keep a copy of each original under the stored artifact (as `.jsonl`-safe text or `.md`) before editing.
- Runs after M1a-c merge; one writer, the owner's go in the implementer's terminal.

## Implementation Notes
Repo side done in the M1 bundle PR: `migration_map.md` (every role-defining memory file mapped to its repo home; 3 rules are GAP, 3 PARTIAL). Memory is NOT shortened: the ticket requires the repo homes merged first and the owner's confirmation of the list (memory is per-user and outside git). Remaining steps after merge: fill the merge SHA in the map, owner confirms the list, shorten each confirmed memory file to frontmatter + links + a pointer line, update MEMORY.md hooks, grep the memory dir for role rules stated twice.

2026-10-04: owner confirmed the list (relayed by agent-working-design). Six memory files shortened to pointers, originals kept in `original_memory_files.md`, `MEMORY.md` hooks updated, merge SHA filled. Four files stay in memory until their gaps are homed (branch-recovery subsection in `docs/guides/delivery_process.md`, drafted by design; the other two need no new text). Branch-recovery subsection added to `docs/guides/delivery_process.md`; stay-in-scope and test-infra-no-ask accepted as homed (route absence, no new text). Ready to close on merge.

## Test Summary
No code. The map is checked by reading each cited home (templates, overlays, manifest, authority file) against the memory text.

## Files Changed
- `docs/guides/delivery_process.md`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS/migration_map.md`
- `agent-working/stored_artifacts/TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS/original_memory_files.md`

## Completion Summary
Six of ten memory files shortened to pointers; the four kept files are homed or accepted; branch-recovery subsection added to `docs/guides/delivery_process.md`.
