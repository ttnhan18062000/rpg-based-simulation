---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
artifact_type: plan
tags: [ai, process-improvement, governance]
---

# Plan (retroactive)

**Written after the fact**, from the ticket's Scope, Implementation Notes and Completion Summary, `migration_map.md`, `original_memory_files.md` and the commits that landed in PR #316 (squash `54e46f439`). It records the plan as executed, not a prior document.

## Order as executed

1. **Repo homes first.** The role facts were put into `registries/session_roles.yaml`, `registries/session_authority.yaml`, the function templates (`docs/guidelines/session_roles/functions/`) and the domain overlays (`domains/`) by M1a/b/c, merged as PR #314, squash commit `242d8920e89bff578a83ab31d2366a215af3d2dc` (SHA from `migration_map.md`).
2. **Map.** `migration_map.md` lists each of the ten candidate memory files, the rule it holds, its repo home and a status (HOME EXISTS, PARTIAL, GAP, OBSOLETE). Three rules were GAP and three PARTIAL.
3. **Owner confirmation, 2026-10-04.** The owner confirmed the list ("confirm the memory list", relayed to the implementer by `agent-working-design`). Commit `9d84dfa15` records it and fills the merge SHA.
4. **Shorten six files.** The six whose every rule is HOME EXISTS were reduced to frontmatter, `[[links]]` and a pointer line: `project_semantic_control_plane_role_division`, `project_mechanism_registry_ownership_split`, `feedback_planner_creates_epic_tickets_only`, `feedback_route_work_via_rpg_feature_planning`, `feedback_small_doc_changes_handoff_to_rpg_planner`, `feedback_report_agent_process_issues_to_agent_working_design`. Originals kept in `original_memory_files.md` (commit `9d84dfa15`) before editing, as the ticket's assumptions require. `MEMORY.md` hooks updated to "POINTER".
5. **Gaps.** Commit `f6dc5f540` added the subsection "Recovering when a commit lands on a branch an implementer holds" to `docs/guides/delivery_process.md` (the branch-recovery gap) and recorded the accepted homes for stay-in-scope and test-infra-no-ask (no new text).
6. **Four files kept** in memory: `project_session_role_division`, `feedback_implementer_owns_all_commits`, `feedback_ask_rpg_feature_planning_before_touching_rpg_logic`, `project_test_architecture_reviewer_role`.

## Not in the record

Per-step timestamps for the memory edits (memory is outside git); the order of steps 3 and 4 rests on the ticket's Implementation Notes dated 2026-10-04.
