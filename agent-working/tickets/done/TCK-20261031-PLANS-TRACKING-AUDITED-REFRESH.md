---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261031-PLANS-TRACKING-AUDITED-REFRESH
phase: done
date: 2026-10-31
tags: [planning, tracking, documentation]
---

# TCK-20261031-PLANS-TRACKING-AUDITED-REFRESH

## Title
Move plans_tracking.md to docs/plans/agent_infrastructure/ and refresh it with an audited count of the plans on main

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
`docs/plans/plans_tracking.md` is dated 2026-10-02 and omits the AI-first SDLC plan and everything since. The designer asked for a refresh under the owner's go on stale tickets and plans (#715 6543261623). It folds into the next agent-working PR after #796 merges, and is not a plan-only PR. Pushes and merges stay separate asks.

The file has no holder. Lead-planner's route is to move it under `docs/plans/agent_infrastructure/`, which the agent-working glob already covers, so no registry or card budget changes (designer's go, with the draft at main-checkout `.claude/handover/drafts/plans_tracking_holder.md`). Lead-planner owns this choice of route.

## Scope
Move the file: `git mv docs/plans/plans_tracking.md docs/plans/agent_infrastructure/plans_tracking.md`. Re-base all its relative links to the new location, and add a line saying the inventory still covers all of `docs/plans/` because the location is about ownership, not subject matter. A link that was already broken before the move is a finding to fix or report, not to guess at.

Then follow the file's own rules, working from the origin/main commit the branch is based on:
- Rebuild the inventory table against `docs/plans/`. Status and authority come from each plan's frontmatter. Do not infer completion from tickets.
- Exclude `docs/plans/archive/`. Collapse multi-file packages into one row, and exclude the file itself.
- Re-count files and records from the tree and record the totals in `## Scope`. Say this count is audited. Earlier counts were incremented, not audited: the file says 99 Markdown files, and `git ls-tree` at 6fdfdf555 finds 199 outside the archive including the file itself.
- Keep the brainstorm column to sources a plan explicitly references in `docs/brainstorm/`.
- Add any status value found in frontmatter to the status key, so that the key covers every value the table shows.
- Update the Date line.
- Check the paths named in the file's maintenance notes. Correct or remove a note only where its path has moved or been archived, and say so in the PR body. Do not re-judge a plan's accuracy or authority in those notes.

## Out of Scope
- Editing any plan or its frontmatter. If a plan's frontmatter is missing or looks wrong, the row shows what the file declares ("none" when it declares nothing), and the plan is listed in the PR body.
- Changing `registries/session_roles.yaml` or any card budget.
- Editing frozen references: `registries/tag_registry.jsonl` notes, `agent-working/tickets/working_log.csv`, done tickets and stored artifacts. `live_map_rendering_and_surface_integration_milestone_plan.md:73` names only the bare filename and stays.
- Validating any plan's feasibility or implementation progress.
- A count check, test or other new tooling for this file.

## Acceptance Criteria
1. Every non-archive Markdown file under `docs/plans/`, except the file itself, is covered by exactly one table row. A scripted check from the tree shows this, and its output is in Test Summary.
2. The Scope totals match that check, with the commit it ran at, and are described as audited.
3. A sample of at least 10 rows, including every row for a multi-file package changed by this ticket, is checked against frontmatter by script or by reading: status and authority match.
4. Every relative link in the file resolves at that commit.
5. The Date line is updated. The AI-first SDLC plan has a row.
6. `route` on the new path gives domain agent-working. No file under `docs/plans/` changes other than the moved file and the two references listed in Implementation Notes.
7. `tests/docs`, `tests/tools/test_planning_doc_staleness_check.py` and `tests/tools/test_session_cards.py` pass. If anything needs the old path, stop and tell the planner, because that choice goes to the owner through lead-planner.
8. `docs/REGISTRY.yaml` is regenerated with the new path and staged.
9. Plans with missing or doubtful frontmatter are listed in the PR body, or the PR body says there are none.

## Related Tickets
TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
docs/plans/plans_tracking.md

## Related Stored Artifacts
None.

## Related Code Areas
`tools/gate_checks/planning_doc_staleness_check.py` scans `docs/plans/` with `rglob`, so it still sees the file. No file under `tools/`, `tests/`, `docs/guides/` or `docs/guidelines/` names this file at 6fdfdf555.

## Assumptions / Open Questions
- Count at the base commit, not earlier. Other domains' plans can land before this ticket runs, so the 199 above is only a reference point.

## Implementation Notes
Two live references outside agent-working's files name the old path, at lines 45 and 411 of origin/main (match on text). `route` results:
- `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md` has no holder. Change `docs/plans/plans_tracking.md` to `docs/plans/agent_infrastructure/plans_tracking.md` in this PR and say so in the PR body.
- `docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md` is held by codebase-planner, whose seat is not running. Lead-planner's word (citing #715 6543261623): change the path on line 45 in this PR, and nothing else in that file. Name the line in the PR body so that codebase-planner sees it at its next start.

## Test Summary
Audit script outputs, run at origin/main `96f623a62` (`docs/plans/` is byte-identical at the branch base `6445ea7b8`):

```
relative links: 83 broken: 0
rows: 59 files in Files-collapsed column: 200 markdown files outside archive excluding the file: 200
single-file rows checked against frontmatter: 42 matching: 42
```

- Coverage (AC1): a spec grouping every non-archive Markdown file under `docs/plans/` into one row was checked by script from the tree: 200 files outside the archive excluding the tracking file (201 including it), each matched by exactly one row, 59 rows. The Files-collapsed column sums to 200.
- Frontmatter (AC3): all 42 single-file rows match their file's `status` and `authority` by script. Every multi-file row (11 packages) was compared by script against the computed status and authority of its files; the table now shows counts where a package is mixed. Three rows differed from the old text and were corrected or kept deliberately: the AI-first hardening row (3 files are P0, not only the roadmap), the Live Map rendering row (one file is P2), and the world rendering core row (kept as the existing `active program; idea/historical support`).
- Links (AC4): all 83 relative links resolve. Before the move, 53 links were checked at `docs/plans/` and none was already broken.
- `route` on the new path: domain agent-working, owned, matched by `docs/plans/agent_infrastructure/**`.
- No plan has missing frontmatter status or authority. No plan frontmatter was edited.
- Tests (scoped, slot OK from lead-planner, `-n 1`, CPUs 4-5): `tests/docs`, `tests/tools/test_planning_doc_staleness_check.py`, `tests/tools/test_session_cards.py`: 185 passed, 2 skipped, 1 xfailed in 4.05s. Nothing needed the old path.

## Files Changed
- `docs/plans/plans_tracking.md` -> `docs/plans/agent_infrastructure/plans_tracking.md` (moved, links re-based, table rebuilt, Date and Scope updated, one archived path corrected in the maintenance notes)
- `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md` (line 411, path only)
- `docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md` (line 45, path only)
- `docs/REGISTRY.yaml` (regenerated)
- this ticket, moved to done; agent-monitoring shards

## Completion Summary
Moved `plans_tracking.md` under `docs/plans/agent_infrastructure/` (agent-working owns it), re-based its links, rebuilt the table from the tree (59 rows covering 200 files, audited), and updated the Date and Scope text. Two path-only reference fixes outside agent-working's files: line 411 of the Live Map rendering plan (no holder) and line 45 of the Python Code Craft foundation brief (codebase-planner's file, lead's word citing #715 6543261623; its seat sees it at next start).

Maintenance-note path check: the roadmap-authority note named `docs/plans/architecture_resilience_remediation_roadmap.md`, which is archived; it now names `docs/plans/archive/architecture_resilience_remediation_roadmap.md`. No other note path had moved. No plan's accuracy or authority was re-judged.

Known gap: no plan has missing status or authority. Six `idea_*` files declare a status other than `idea` and are left as declared: `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`, `docs/plans/idea_frontend_canvas_render_tiers.md`, `docs/plans/idea_hud_color_asset_system.md`, `docs/plans/idea_hud_motion_transition_system.md` and `docs/plans/idea_hud_quality_measurement.md` declare `active`, and `docs/plans/world_rendering/idea_world_render_validation.md` declares `historical`.

Two reference lines outside agent-working's files changed, path only: `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md` line 411 and `docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md` line 45 (codebase-planner's file, changed on lead-planner's word citing #715 6543261623).
