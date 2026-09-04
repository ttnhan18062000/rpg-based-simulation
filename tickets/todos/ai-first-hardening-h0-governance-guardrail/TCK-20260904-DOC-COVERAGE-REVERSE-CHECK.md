---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-DOC-COVERAGE-REVERSE-CHECK
phase: open
date: 2026-09-04
tags: [testing, ai, documentation, process-improvement]
---

# TCK-20260904-DOC-COVERAGE-REVERSE-CHECK

## Title
Doc-update self-report gap: Verify-time reverse-direction hardening

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
A doc-updater-added doc file recurringly fails to get reflected into the ticket's own Files Changed/Related Docs sections — caught by done-checker/Verify's check_docs_to_update_coverage each time, and patched by hand. RETRO-2026-W36 confirms 3 more recurrences (ITEM-INSTANCE-HISTORY, RACE-RELATIONS-MATRIX, READINESS-SPEED-FORMULA) after RETRO-2026-W33 already flagged the pattern. This ticket has two parts, not equally weighted: (1) Verify-time hardening, the primary fix — extend check_docs_to_update_coverage to also check the reverse direction (a file doc-updater touched but that never made it into the ticket body); (2) generation-time defense-in-depth, not primary — bake an explicit self-check step into doc-updater.md's base prompt. Per the epic's own invariant, deterministic enforcement is required; prompt reinforcement alone does not satisfy the milestone.

## Scope
- Extend check_docs_to_update_coverage (tools/gate_checks/done_checker_static.py, lines 482-558) to additionally check the reverse direction: does git status show a docs/ path touched during the ticket's diff that does not appear (with the existing directory-collapse tolerance) in the ticket's resolved Files Changed or Related Docs section text
- Reuse check_tag_drift's existing pattern (lines 769-810) for resolving the ticket path and reading section text via _extract_section_text
- Wire the new/extended check into run_static_precheck (or its own DoD condition) so it actually blocks Verify, not just advises
- Add an explicit self-check instruction to doc-updater.md's base prompt: cross-reference actual touched paths against what will land in Files Changed/Related Docs, flag mismatch same-turn
- Reword docs/architecture/doc_updater_agent.md's 'fully decoupled from doc-updater's own output' language precisely, preserving its meaning (ground truth is git status, not docs_updated self-report) while reflecting that a new reverse check now exists

## Out of Scope
- Modifying check_docs_to_update_coverage's existing forward-direction bullet-format contract for investigation.md (TCK-20260802-DOC-COVERAGE-CHECK) — that stays as-is; the reverse check is additive
- Silently deciding supersede-vs-coexist between the new Python check and the prior JS/awk-based non-blocking warning without recording the decision explicitly
- Silently inheriting the forward check's unconditional hotfix-tier NA exemption for the new reverse check without an explicit stated decision

## Acceptance Criteria
- [ ] New/extended done-checker static check FAILs when git status shows a docs/ path touched during the ticket's diff that does not appear (matching the existing directory-collapse tolerance) in the ticket's resolved Files Changed or Related Docs section text
- [ ] Same check PASSes when every git-touched docs/ path appears in one of those sections, and is wired into run_static_precheck (or its own DoD condition) so it actually blocks Verify, not just advises
- [ ] At least one of the three named real historical incidents (ITEM-INSTANCE-HISTORY, RACE-RELATIONS-MATRIX, or READINESS-SPEED-FORMULA) is reproduced as a regression-test fixture proving the new check would have FAILed before the hand-patch
- [ ] doc-updater.md's base prompt gains an explicit self-check instruction (cross-reference actual touched paths against what will land in Files Changed/Related Docs, flag mismatch same-turn) — agent-interpreted, matching this file's existing test-surface limitation

## Related Tickets
- TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING (prior non-blocking JS warning, proven insufficient by this concern's own retro evidence — decide explicitly whether the new Verify-time Python check supersedes or coexists with it)
- TCK-20260802-DOC-COVERAGE-CHECK
- TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED
- TCK-20260803-DOC-UPDATER-CORE-WIRING
- TCK-20260803-DOC-UPDATER-EPIC

## Related Docs
- docs/architecture/doc_updater_agent.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- .claude/agents/doc-updater.md
- .claude/workflows/implement-ticket.js
- docs/architecture/doc_updater_agent.md
- tests/tools/test_done_checker_static.py
- tests/tools/test_document_update_phase_wiring.py
- tests/tools/test_doc_staleness_gate_wiring.py

## Assumptions / Open Questions
- Risk of two parallel diverging implementations (JS awk-based non-blocking vs. new Python check_docs_to_update_coverage-based blocking) — must explicitly decide supersede-vs-coexist, not leave both live by default
- docs/architecture/doc_updater_agent.md needs precise rewording in the same session — must preserve the spirit that ground truth stays git-status-derived, not docs_updated-self-report-derived, even as the decoupling language changes
- Scope ambiguity on whether the reverse check covers docs/ paths only (matching the forward check and all 3 historical incidents) or all touched paths generally — needs an explicit stated decision, not silent inheritance
- check_docs_to_update_coverage currently returns NA unconditionally for hotfix tier (no investigation.md) — hotfix tickets have Files Changed/Related Docs too and could exhibit the identical gap; needs a stated decision, not silent inheritance of the forward check's hotfix exemption

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
