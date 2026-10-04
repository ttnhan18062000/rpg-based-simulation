---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M1D-ROLE-MEMORY-TO-POINTERS
artifact_type: report
tags: [ai, process-improvement, governance]
---

# Role memory -> repo homes (migration map)

Memory directory: `~/.claude/projects/-home-u24desktop-Working-rpg-based-simulation/memory/` (per-user, outside git).
**Six files shortened 2026-10-04 (see Owner confirmation); four kept.** Order required by the ticket: repo homes merged first (M1a to M1c,
this PR), the owner confirms this list, then each memory file is reduced to a pointer. Status below is
about the repo side only. `GAP` means the rule has no repo home yet; that memory file keeps the rule until one exists.

Home paths: `R` = `registries/session_roles.yaml`, `A` = `registries/session_authority.yaml`,
`F/<f>` = `docs/guidelines/session_roles/functions/<f>.md`, `D/<d>` = `docs/guidelines/session_roles/domains/<d>.md`.
Repo homes merged: PR #314, squash commit `242d8920e89bff578a83ab31d2366a215af3d2dc` (M1a/b/c).

| Memory file | Role rule it holds | Repo home | Status |
|---|---|---|---|
| `project_session_role_division` | a planning/design session never implements; hands off at Plan | `F/designer`, `F/planner` ("never implement"), `A` (`forbidden` for designer and planner) | HOME EXISTS |
| same | stop at Plan, commit nothing, message the implementer with branch and review focus | `F/designer` (drafts handed over by message), `F/planner` (dispatch) | PARTIAL: "name the branch and what review should scrutinise" has no home |
| same | shared memory note applied to the wrong session (scope ambiguity) | removed by design: the card is per seat (M2 injects it) | OBSOLETE once M2 lands; keep until then |
| same | `rpg-planner` owns the semantic-control-plane epic end to end; the catalog designer is advisory | `D/rpg` | HOME EXISTS |
| same | stay in scope: do not propose repo-wide housekeeping outside the owned track | none | GAP |
| `project_semantic_control_plane_role_division` | the design session does not scope M1 to M4 of that epic; advisory only; relayed "user said" claims are confirmed directly when high stakes | `D/rpg` covers the owner; the relay caution is `docs/plans/agent_infrastructure/session_layer_working_process.md` 9.3 ("verify before acting on a relayed claim") | HOME EXISTS |
| `project_test_architecture_reviewer_role` | `testing-planner` reviews batch PRs against roadmap and epic criteria, blocking vs non-blocking; keeps `HOLD` items held; does not implement or create child tickets unasked | `D/testing` | HOME EXISTS |
| same | binding plan and tickets locations; D-x pending list | `D/testing` names the roadmap; the pending decisions are roadmap content | PARTIAL: the current D-x list is state, not role, and stays in the roadmap |
| `project_mechanism_registry_ownership_split` | `registries/mechanisms.yaml` content is rpg; only the tooling around it is agent-working; route by commit subject or routing ticket, not authorship | `R` (`owns_not` for agent-working, `owns` for rpg, route `registries/mechanisms.yaml -> rpg-planner`), `D/agent-working`, plan 9.4 (authorship not used) | HOME EXISTS |
| `feedback_implementer_owns_all_commits` | one writer per branch; design does not commit or push on an implementer's branch | `F/implementer` ("only role that writes to the worktree"), `A` (`forbidden: commit, push` for designer/planner), `R` `worktrees:` writer | HOME EXISTS |
| same | the implementer owns CI polling and triage; design hands leads and reviews the conclusion | `F/implementer`, `D/agent-working` | HOME EXISTS |
| same | recovery when a commit lands on a branch an implementer holds (park, reset, verify SHAs) | none | GAP (a procedure, not a role rule: candidate home `docs/guides/delivery_process.md`) |
| `feedback_planner_creates_epic_tickets_only` | a roadmap-level session files epic tickets only; child tickets belong to the detail planner and implementer | `F/designer` ("File epic tickets only"), `F/planner` (detail child tickets) | HOME EXISTS |
| `feedback_route_work_via_rpg_feature_planning` | the catalog designer hands briefs only to the rpg planner, never to an implementer | `D/rpg`; plan 9.0 and 9.3 | HOME EXISTS |
| `feedback_ask_rpg_feature_planning_before_touching_rpg_logic` | testing roles ask the rpg planner before RPG logic, expected behaviour, Bible or parity semantics | `D/testing`, `D/rpg`, `R` routes | HOME EXISTS |
| same | test-infra-only changes need no ask | none | GAP (small; candidate `D/testing`, but the card is at budget) |
| `feedback_small_doc_changes_handoff_to_rpg_planner` | the rpg designer hands small corrections to its own docs to the rpg planner with exact before/after text | `F/designer` ("send the owner exact before/after text") | HOME EXISTS |
| `feedback_report_agent_process_issues_to_agent_working_design` | process problems go to `agent-working-designer` with symptom, evidence, impact | `D/agent-working`, `R` routes (`agent-working/**`, `tools/**`) | HOME EXISTS |

## Open items for the owner

1. Confirm which memory files above are reduced to pointers (all ten, or only those with every rule at HOME EXISTS).
2. Gaps (3 rules, plus the PARTIAL rows): give each a home or accept that it stays in memory. The role cards are at
   the 400-token budget, so a new card sentence needs one removed or a rule placed in a guide instead of a card.
3. The shortened files keep their frontmatter, `[[links]]` and one pointer line; `MEMORY.md` hooks change to say "pointer".

## Owner confirmation (2026-10-04)

The owner confirmed the M1d list ("confirm the memory list", agent-working-design session), relayed to the implementer by message.

- **Shortened to pointers** (every rule HOME EXISTS): `project_semantic_control_plane_role_division`, `project_mechanism_registry_ownership_split`, `feedback_planner_creates_epic_tickets_only`, `feedback_route_work_via_rpg_feature_planning`, `feedback_small_doc_changes_handoff_to_rpg_planner`, `feedback_report_agent_process_issues_to_agent_working_design`. Originals: `original_memory_files.md` in this folder.
- **Kept as is until their gaps close**: `project_session_role_division` (GAP stay-in-scope, PARTIAL; obsolete only after M2), `feedback_implementer_owns_all_commits` (GAP branch-recovery), `feedback_ask_rpg_feature_planning_before_touching_rpg_logic` (GAP test-infra-no-ask), `project_test_architecture_reviewer_role` (PARTIAL).
- **Gap homes accepted**: stay-in-scope = `owns_not`/routes plus plan section 10 advisory boundaries (no new text); branch-recovery = a short subsection in `docs/guides/delivery_process.md` (design drafts the text); test-infra-no-ask = testing `owns` in the registry (no card text).
- M1d closes once the four kept files' gaps are homed or the owner accepts them staying in memory.

## Not done yet

The four kept files and their gap homes (above). The ticket stays `INPROGRESS` until then.
