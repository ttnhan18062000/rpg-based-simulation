---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-PLAN-DOCUMENTS-LAND
phase: done
date: 2026-10-31
tags: [ai, governance, delivery, planning]
---

# TCK-20261031-SDLC-PLAN-DOCUMENTS-LAND

## Title
The AI-first SDLC plan, audit, decision summary and handover are committed under docs/plans/agent_infrastructure/.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
First PR of the epic, docs only. The four files are uncommitted in agent-working-designer's worktree, `.claude/worktrees/agent-working-designer/docs/plans/agent_infrastructure/`, and those copies are final (designer, 2026-10-31). sha256 prefixes: AUDIT d5c28b79a9ed, PLAN c989755ffffe, SUMMARY 30459a2f4cdc, HANDOVER 4f9f77c32193. Take all four from that worktree; do not fold u24's branch `agent-working-designer-u24-sdlc-plan-handover` (62f963067) over them: AUDIT and HANDOVER are no longer byte-identical to it. If a hash differs, ask the designer.

## Scope
1. Copy the four files from the designer's worktree onto a fresh branch from origin/main, and check their hashes: `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, `AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md`, `AI_FIRST_SDLC_DECISION_SUMMARY.md`, `HANDOVER_SDLC_EVOLUTION_TO_UBUNTU.md`.
2. Before committing, read the plan's section 27a and check the files against owner condition #715 6528807751. The owner has ruled on AUDIT section 26 (generalised, with an errata note); its remaining `.env` mentions, the host path at :473 and the allow-rule list at :564 stay.
3. Run `make docs-registry`; run `make knowledge-index-update` per the docs rule.
4. PR body Review notes name sections 28a-32a, 42 and Part IX of the plan as unreviewed by lead-planner (it reviewed the summary, Resolution Matrix, 27a and 28).
5. After the PR merges, ask the owner, through lead-planner, to delete `agent-working-designer-u24-sdlc-plan-handover`. Its history stays public until then.

## Out of Scope
- Any edit to plan substance; that is the designer's.
- Pushing to u24's branch, or deleting it (the owner's).
- Committing anything from `tmp/`, including `AI_WORKING_ISSUE1.md`. Part IX cites it by name; the citation stays.
- Running anything the plan proposes.

## Acceptance Criteria
1. Exactly the four documents, plus ticket, registry and monitoring files, are in the PR diff; no `src/`, `tools/` or `tests/` change.
2. The four files match the sha256 prefixes above.
3. `validate_frontmatter.py` and `generate_registry --check` pass.
4. A token-shape scan of the four files, with a positive control, finds nothing; record the result.
5. OD-4 to OD-9, OD-11 to OD-13 and OD-16 to OD-21 read as undecided in the summary and plan.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- docs/plans/agent_infrastructure/
- docs/REGISTRY.yaml

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- Owner ruling, given in the designer's terminal, lead-planner logging it on #715: AUDIT generalised on main; u24's branch deleted after the PR, on the owner's command.

## Implementation Notes
Copied the four documents from the designer's worktree to `docs/plans/agent_infrastructure/` with no edit. sha256 prefixes match the ticket: AUDIT d5c28b79a9ed, PLAN c989755ffffe, SUMMARY 30459a2f4cdc, HANDOVER 4f9f77c32193. Read plan section 27a before committing: it keeps host-level credential details out, as owner condition #715 6528807751 asks. u24's branch 62f963067 was not folded or pushed to; `tmp/` and AI_WORKING_ISSUE1.md were not committed.

## Test Summary
Token-shape scan of the four files (GitHub ghp_/gho_/ghu_/ghs_/ghr_ and github_pat_ shapes, AWS, sk-, Slack, PEM private key, JWT): no matches; positive control (a synthetic ghp_ line) matched 1. `validate_frontmatter.py --content-type doc` passes on all four. OD-4 to OD-9, OD-11 to OD-13 and OD-16 to OD-21 read as open in the summary's `Still open` table. `generate_registry --check`: in sync (3821 entries). `tests/tools/test_agent_working_paths_guard*.py`: 11 passed. `tests/docs/test_doc_integrity.py`, `test_doc_path_existence.py`, `test_contributor_guardrails.py`: 13 passed, 1 skipped, 1 xfailed. `make knowledge-index-update` run. No full tests/tools run (docs only).

## Files Changed
docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md; AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md; AI_FIRST_SDLC_DECISION_SUMMARY.md; HANDOVER_SDLC_EVOLUTION_TO_UBUNTU.md (all new); this ticket moved to done/; docs/REGISTRY.yaml; monitoring shards.

## Completion Summary
The AI-first SDLC plan, audit, decision summary and handover are committed under docs/plans/agent_infrastructure/ unedited, with matching hashes. Docs only; no src/, tools/ or tests/ change.
