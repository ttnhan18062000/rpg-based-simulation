---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-DOC-COVERAGE-REVERSE-CHECK
phase: done
date: 2026-09-04
tags: [testing, ai, documentation, process-improvement]
---

# TCK-20260904-DOC-COVERAGE-REVERSE-CHECK

## Title
Doc-update self-report gap: Verify-time reverse-direction hardening

## Status
DONE

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
- [x] New/extended done-checker static check FAILs when git status shows a docs/ path touched during the ticket's diff that does not appear (matching the existing directory-collapse tolerance) in the ticket's resolved Files Changed or Related Docs section text
- [x] Same check PASSes when every git-touched docs/ path appears in one of those sections, and is wired into run_static_precheck (or its own DoD condition) so it actually blocks Verify, not just advises
- [x] At least one of the three named real historical incidents (ITEM-INSTANCE-HISTORY, RACE-RELATIONS-MATRIX, or READINESS-SPEED-FORMULA) is reproduced as a regression-test fixture proving the new check would have FAILed before the hand-patch
- [x] doc-updater.md's base prompt gains an explicit self-check instruction (cross-reference actual touched paths against what will land in Files Changed/Related Docs, flag mismatch same-turn) — agent-interpreted, matching this file's existing test-surface limitation

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

Implemented all 8 plan steps in `staging_artifacts/TCK-20260904-DOC-COVERAGE-REVERSE-CHECK/plan.md`:

1. **`tools/gate_checks/done_checker_static.py`**: added `_DOCS_PROSE_TOKEN_RE`, `_prose_docs_paths`,
   `_touched_docs_paths_uncovered`, and `_resolve_ticket_body_path` (a new private helper — did not
   touch `check_tag_drift`). Restructured `check_docs_to_update_coverage` so the `tier == "hotfix"`
   bare early-`NA`-return is gone; the forward half still skips (no `investigation.md` dependency)
   under hotfix, but the reverse half now always runs afterward, tier-agnostically, scoped to
   `docs/` paths only. `_git_touched_paths()` is called exactly once and its result reused by both
   halves (plan's explicit "do not call it twice" instruction).
2. Added `test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident`, mocking
   `_git_touched_paths` via `monkeypatch.setattr("gate_checks.done_checker_static._git_touched_paths", ...)`
   (no prior test in this file mocked git — this is a new, idiomatic pattern, not literally
   "mirroring existing tests" as the plan phrased it).
3. Added `test_run_static_precheck_wires_reverse_check_blocking` — confirms no `run_static_precheck`
   code change was needed; a reverse FAIL surfaces through the existing aggregation.
4. Reworded the Verify-prompt sentence in `.claude/workflows/implement-ticket.js` (lines ~1444-1449)
   to describe the bidirectional check, citing this ticket's ID.
5. Added a numbered self-check step (item 6) to `.claude/agents/doc-updater.md`'s "What to Do"
   section, using the existing `blocker` output field.
6. Reworded `docs/architecture/doc_updater_agent.md`'s "Error handling" section: (A) the
   decoupling paragraph no longer claims "No new coupling is added" verbatim; (B) the hotfix-gap
   paragraph now states the accepted/closed split precisely (omission case still open,
   touched-but-undeclared case now closed on hotfix). (C) `docs/ai/workflows.md:88`'s
   Document-Update cell no longer claims the backstop is "for standard/epic tier" only.
7. Updated `guardrail_enforcement_epic.md`'s M2 acceptance-signal bullet to mark it satisfied,
   naming this ticket and the RACE-RELATIONS-MATRIX incident, and explicitly disclosing the
   `docs/`-only scope's ITEM-INSTANCE-HISTORY limitation.
8. Corrected `docs/ai/ticket-lifecycle.md`'s hotfix-backstop-gap passage (~line 360) to state the
   same accepted/closed split as (B) above.

**Deviation from the plan (see `plan.md`'s Deviations section for full detail):** the plan's Step 1
Verify list claimed all pre-existing `test_docs_coverage_*` tests would remain "unmodified" except
`test_docs_coverage_hotfix_is_na`. Running the suite after implementing the reverse check surfaced
two real, evidence-based conflicts this claim did not anticipate:
- Three existing fixtures (`test_docs_coverage_all_flagged_paths_touched_passes`,
  `test_docs_coverage_line_suffix_bullet_matches_bare_git_path`,
  `test_docs_coverage_resolved_conditional_bullet_touched_anyway_still_passes`) `git init` a fresh
  repo and touch a real `docs/` file but never create a resolvable ticket file — the reverse
  check's own designed behavior (a missing ticket file at Verify time is a real `FAIL`, per plan
  Step 1 item 6) then broke them. Fixed by adding a minimal resolvable ticket file declaring the
  same path to each fixture — this models real Verify-time state accurately (a ticket file always
  exists then); it does not weaken what these tests were built to verify (forward-direction bullet
  parsing).
- Three other existing fixtures (`test_docs_coverage_no_section_heading_passes`,
  `test_docs_coverage_explicit_none_passes`, `test_docs_coverage_none_with_trailing_rationale_passes`)
  never called `monkeypatch.chdir(tmp_path)` — previously harmless because the old forward-only
  logic never invoked `_git_touched_paths()` for an empty-required-docs fixture, but the new
  reverse half always does, so these tests were unknowingly reading the *real* repo's own
  uncommitted `docs/` changes (confirmed via `git status --porcelain` at implementation time: real
  modifications to `docs/REGISTRY.yaml`, `docs/agent-monitoring/README.md`, etc., from concurrent
  work in this shared worktree). Fixed by adding the missing `monkeypatch.chdir(tmp_path)` — a
  pre-existing test-isolation gap, not a new fixture-construction choice.

Full suite run: `tests/tools/test_done_checker_static.py` (112 tests, all pass),
`tests/tools/test_doc_updater_agent_file.py` (3 tests, all pass — including the new
`test_doc_updater_prompt_includes_self_check_instruction`), `tests/tools/test_document_update_phase_wiring.py`
and `tests/tools/test_doc_staleness_gate_wiring.py` (unaffected, all pass).

## Test Summary

`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest
tests/tools/test_done_checker_static.py tests/tools/test_doc_updater_agent_file.py
tests/tools/test_document_update_phase_wiring.py tests/tools/test_doc_staleness_gate_wiring.py -q`
→ 129 passed. New tests added: `test_docs_coverage_hotfix_forward_half_still_skips` (rewrite of
the old `test_docs_coverage_hotfix_is_na`), `test_reverse_docs_coverage_fails_when_touched_doc_not_in_files_changed_or_related_docs`,
`test_reverse_docs_coverage_passes_when_touched_doc_appears_in_files_changed`,
`test_reverse_docs_coverage_passes_when_touched_doc_appears_in_related_docs_only`,
`test_reverse_docs_coverage_directory_collapse_tolerance`,
`test_reverse_docs_coverage_ITEM_INSTANCE_HISTORY_style_non_docs_path_is_out_of_scope`,
`test_reverse_docs_coverage_hotfix_tier_behavior`,
`test_reverse_docs_coverage_reproduces_RACE_RELATIONS_MATRIX_incident`,
`test_run_static_precheck_wires_reverse_check_blocking`,
`test_verify_prompt_mentions_reverse_check_or_updated_condition_language`,
`test_doc_updater_prompt_includes_self_check_instruction`. Broader `tests/tools/` run in progress
at time of writing this section (background); no failures observed in the scoped runs above.

## Files Changed
- `tools/gate_checks/done_checker_static.py`
- `tests/tools/test_done_checker_static.py`
- `.claude/workflows/implement-ticket.js`
- `.claude/agents/doc-updater.md`
- `tests/tools/test_doc_updater_agent_file.py`
- `docs/architecture/doc_updater_agent.md`
- `docs/ai/workflows.md`
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`
- `docs/ai/ticket-lifecycle.md`
- `staging_artifacts/TCK-20260904-DOC-COVERAGE-REVERSE-CHECK/plan.md` (Deviations section added)
- `docs/parity_ledger/infrastructure.yaml` (modified, by this ticket's own Parity phase, adding
  `INFRA-404` for the reverse-check extension)

Not touched by this run (pre-existing, unrelated changes from sibling tickets
`TCK-20260904-AGENT-TOOL-USAGE-BASELINE` and `TCK-20260904-CAPABILITY-ENVELOPE-BASELINE`, both
already Finalized but not yet committed in this shared worktree at the time this ticket's own
Verify phase ran): `docs/REGISTRY.yaml`, `docs/agent-monitoring/README.md`, `docs/ai/README.md`,
`docs/ai/capability_envelope_baseline.md`.

## Completion Summary

Extended `check_docs_to_update_coverage` in-place with a tier-agnostic reverse-direction check: it
now independently confirms every `docs/` path real `git status` shows touched during a ticket's
diff is reflected in that ticket's own `## Files Changed`/`## Related Docs` text, reusing
`check_tag_drift`'s path-resolution/`_extract_section_text` mechanics and `_path_touched`'s
directory-collapse tolerance while keeping the existing `PASS`/`FAIL` vocabulary and
`run_static_precheck` wiring unchanged (no new tuple entry). Reproduced the real
`TCK-20260831-RACE-RELATIONS-MATRIX` historical incident as a regression fixture, added a
self-check instruction to `doc-updater.md`'s prompt as defense-in-depth, and corrected four stale
doc passages (`doc_updater_agent.md` x2, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md`)
that previously claimed hotfix tier had "no equivalent backstop" — now stated precisely as a split:
the omission case (doc-updater never touching a needed doc) remains an open, accepted gap on
hotfix tier, while the touched-but-undeclared case is now closed tier-agnostically. The scope is
deliberately `docs/`-only (Decision 2), so this check structurally cannot catch the
`ITEM-INSTANCE-HISTORY` incident's actual `src/core/state.py` gap — disclosed explicitly, not
implied as covered.
