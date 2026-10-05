---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
artifact_type: investigation
tags: [ai, process-improvement, governance]
---

# Investigation (retroactive)

**Written after the fact**, from `migration_map.md` and the ticket's Implementation Notes. Nothing here was re-derived from the memory files.

## Role-defining memory files and where each fact lives

| Memory file | Fact now lives in | Outcome |
|---|---|---|
| `project_semantic_control_plane_role_division` | `domains/rpg.md`; relayed-claim caution in plan 9.3 | shortened |
| `project_mechanism_registry_ownership_split` | `registries/session_roles.yaml` (`owns`/`owns_not`, route `registries/mechanisms.yaml -> rpg-planner`), `domains/agent-working.md`, plan 9.4 | shortened |
| `feedback_planner_creates_epic_tickets_only` | `functions/designer.md` ("File epic tickets only"), `functions/planner.md` | shortened |
| `feedback_route_work_via_rpg_feature_planning` | `domains/rpg.md`, plan 9.0 and 9.3 | shortened |
| `feedback_small_doc_changes_handoff_to_rpg_planner` | `functions/designer.md` ("send the owner exact before/after text") | shortened |
| `feedback_report_agent_process_issues_to_agent_working_design` | `domains/agent-working.md`, `session_roles.yaml` routes (`agent-working/**`, `tools/**`) | shortened |
| `project_session_role_division` | `functions/designer.md`, `functions/planner.md`, `session_authority.yaml`, `domains/rpg.md` | kept: stay-in-scope GAP (accepted as homed by `owns_not`/routes and plan section 10), "name the branch" PARTIAL, and the scope-ambiguity row is obsolete only once M2 lands |
| `feedback_implementer_owns_all_commits` | `functions/implementer.md`, `session_authority.yaml`, `session_roles.yaml` worktrees | kept: branch-recovery GAP, then homed by the new `delivery_process.md` subsection |
| `feedback_ask_rpg_feature_planning_before_touching_rpg_logic` | `domains/testing.md`, `domains/rpg.md`, routes | kept: test-infra-no-ask has no explicit text, accepted as homed by route absence |
| `project_test_architecture_reviewer_role` | `domains/testing.md` | kept: the current D-x list is state, not role, and stays in the roadmap (PARTIAL) |

## Why four were kept

As the ticket records: each had a GAP or PARTIAL row, so the memory file keeps the rule until a home exists or the owner accepts it staying. The owner confirmed this split on 2026-10-04. The ticket's Implementation Notes record the gaps as homed or accepted; shortening the four is a follow-up if the owner wants it.
