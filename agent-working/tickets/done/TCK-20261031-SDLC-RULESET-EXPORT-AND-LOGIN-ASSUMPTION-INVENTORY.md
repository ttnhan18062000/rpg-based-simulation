---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY
phase: done
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY

## Title
The ruleset is exported as the rollback point, and the tools that assume the owner's login are listed.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Plan section 54 items 3-4, required before any credential change. Both are read-only.

## Scope
1. Export the production ruleset JSON, read-only, into a committed artifact, with SHA and date.
2. Inventory the tools and scripts that assume the owner login or need admin-only endpoints (`pr_render`, `pr_status`, GitHub MCP configuration, scripts calling `gh api`), recording what each would do under a write-role machine user.
3. Re-check that there are no repository-level Actions secrets, reporting names only.

## Out of Scope
- Host credential stores and E6a step 3: reported to the owner only, never in this ticket's artifacts.
- Changing any tool or setting.

## Acceptance Criteria
1. The export parses, and can be compared against a fresh read.
2. Each inventoried tool has a stated behaviour under the machine user, by trace or stated as unverified.
3. No credential value, store location or host detail in any artifact.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/delivery/pr_render.py, tools/delivery/pr_status.py
- agent-working/stored_artifacts/ (result record)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.

## Implementation Notes
Read-only: GET calls only, none denied. Result record `agent-working/stored_artifacts/sdlc-phase-0/ruleset_export_and_login_inventory.md`; export `ruleset_14220945_export.jsonl` beside it.
- The one ruleset (`protect_branches`, id 14220945) is exported with `current_user_can_bypass` removed (it describes the caller, so it would show a false change); a comparison against a fresh read ignores only that field.
- The export was read with an admin-level login. Whether a lower-role read returns `bypass_actors` is **unverified**, so a compare under a machine user may differ without a ruleset change.
- Repository-level Actions secrets: none. (Planner condition: nothing about credentials beyond that.)
- The inventory lists 12 tools/workflows/integrations with their `gh` verbs and API paths and the predicted behaviour under a write-role user, each marked unverified where not run. No tool uses an admin-only endpoint.
- Content was cleared for a public repository by agent-working-planner before commit: the ruleset id, name, admin always-bypass and required checks are already public in the audit; actor 5 is a role.

## Test Summary
Token-shape scan of the new files (ghp_/gho_/ghu_/ghs_/ghr_/github_pat_, AWS, sk-, Slack, PEM, JWT): clean on the new and changed files (positive control matched). `validate_frontmatter.py --content-type doc` passes on the result record. The export parses as JSON (13 keys).

## Files Changed
- `agent-working/stored_artifacts/sdlc-phase-0/ruleset_14220945_export.jsonl` (new)
- `agent-working/stored_artifacts/sdlc-phase-0/ruleset_export_and_login_inventory.md` (new)

## Completion Summary
Done. AC1: the export parses and has a stated comparison rule. AC2: every inventoried item has a stated behaviour, marked unverified where not run. AC3: no credential value, store location or host detail. Known gap: none stated beyond the unverified items marked in the record.
