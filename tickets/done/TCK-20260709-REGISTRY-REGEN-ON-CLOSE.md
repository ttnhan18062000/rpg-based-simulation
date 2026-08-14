---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260709-REGISTRY-REGEN-ON-CLOSE
phase: done
date: 2026-07-09
tags: []
---

# TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Title
Trigger docs/REGISTRY.yaml regeneration on every ticket close

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
The `make docs-registry` command exists but nothing in `.claude/workflows/implement-ticket.js` or CLAUDE.md's 'After Work' section triggers it when a ticket moves to `tickets/done/`, which is the root cause of drift — the checked-in `docs/REGISTRY.yaml` currently has 13 stale `tickets/done/` entries. This matters because CLAUDE.md's Hard Rules already establish precedent for a mandatory, non-fatal, every-tier auto-write step (the agent-monitoring write rule), and registry regen should follow the same shape rather than remain conditional on docs/ changes only.

## Scope
- Add a step to implement-ticket.js's Finalize phase (or a Post-Finalize orchestrator bash() checkpoint, mirroring existing Post-Test/finalize-selfcheck patterns) that invokes `python3 tools/generate_registry.py` unconditionally on every ticket close, all tiers including hotfix
- Handle a nonzero exit as a non-blocking warning, mirroring the 'write-never-fails' semantics used for agent-monitoring
- Add an orchestrator-run self-check that confirms the regenerated docs/REGISTRY.yaml contains an entry for the closing ticket_id before Finalize completes
- Update CLAUDE.md's 'After Work' section to document the new unconditional trigger and the `git add docs/REGISTRY.yaml` staging step, analogous to the existing 'Always stage agent-monitoring/' instruction

## Out of Scope
- Adding the --check/CI drift-detection gate (see TCK-20260709-REGISTRY-DRIFT-CHECK-GATE)
- Backfilling frontmatter on any currently frontmatterless tickets (see TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL)
- Modifying _SKIP_DOC_SUBDIRS or any other generate_registry.py internals unrelated to the Finalize-phase trigger

## Acceptance Criteria
- [ ] implement-ticket.js's Finalize phase (or a Post-Finalize orchestrator bash() checkpoint, mirroring existing Post-Test/finalize-selfcheck patterns) invokes `python3 tools/generate_registry.py` on every ticket close, all tiers including hotfix, unconditional on whether docs/ changed this run
- [ ] A nonzero exit (doc frontmatter errors anywhere in the repo) logs a warning and does not block ticket close, mirroring the 'write-never-fails' wording used for agent-monitoring
- [ ] An orchestrator-run self-check confirms the regenerated docs/REGISTRY.yaml actually contains an entry for the closing ticket_id before Finalize completes
- [ ] CLAUDE.md's 'After Work' section is updated to state registry regen now runs unconditionally on every ticket close, and the regenerated docs/REGISTRY.yaml is staged (`git add docs/REGISTRY.yaml`) as part of ticket close

## Related Tickets
- TCK-20260606-DOCSITE-REGISTRY
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER
- TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS
- TCK-20260627-P1E-DOMAIN-INVENTORY
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Related Docs
- `CLAUDE.md`
- `docs/ai/README.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `Makefile`
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`

## Assumptions / Open Questions
- Hotfix-tier ticket closes are assumed to also trigger regen, per the concern's stated intent ('every implement-ticket workflow run... including hotfix') — this was an open AC decision in investigation, not explicitly confirmed
- Non-fatal handling must tolerate a pre-existing, unrelated frontmatter gap elsewhere in the repo without becoming a recurring false FINALIZE_INCOMPLETE signal
- The new step should follow the existing orchestrator-verified self-check pattern (finalizeCheckOutput/monitoringCheckOutput) rather than an agent-prompt-only bullet

## Implementation Notes

Followed staging_artifacts/TCK-20260709-REGISTRY-REGEN-ON-CLOSE/plan.md exactly, with the
deviations documented in that file's own "Deviations" section.

- Added `check_registry_entry_regenerated(ticket_id, root=Path("."), registry_output=Path("docs/REGISTRY.yaml"))`
  to `tools/gate_checks/done_checker_static.py`, placed between `check_monitoring_write_recorded`
  and `run_finalize_selfcheck`. It calls `generate_registry(resolved_root, output_path)` (imported
  directly from `tools/generate_registry.py`, which is already on `sys.path` via `_TOOLS_DIR`)
  inside a `try/except Exception`, captures a nonzero return or a raised exception purely as
  informational `regen_note` text, then parses the freshly-written `docs/REGISTRY.yaml` with
  `yaml.safe_load` and checks whether any entry has `ticket_id == ticket_id`. Only entry
  presence/absence drives PASS/FAIL — a nonzero tool exit never causes FAIL, satisfying AC #2.
  No `tier` parameter, matching `check_monitoring_write_recorded`'s precedent (AC #1: applies to
  every tier including hotfix).
- Wired it in as `run_finalize_selfcheck`'s 4th tuple entry (`registry_entry_regenerated`).
  Because Python evaluates tuple-literal elements eagerly, the regen always runs whenever
  `run_finalize_selfcheck` runs — no separate invocation site needed. Updated the function's and
  module's docstrings from "3" to "4" conditions.
- Updated only the comment above the existing `finalizeCheckOutput` `bash()` call in
  `.claude/workflows/implement-ticket.js` (around line 1069) to document that this call now also
  regenerates `docs/REGISTRY.yaml` and checks the closing ticket's entry as a side effect. No new
  `bash()` call, no change to the JSON-marker parsing or the generic `finalizeFailures` handling —
  both already treat any number of conditions/any FAIL uniformly.
- Added one bullet to CLAUDE.md's "After Work" section (next to the "Always stage
  agent-monitoring/" bullet) documenting the unconditional regen and the `git add
  docs/REGISTRY.yaml` staging instruction. Also lightly reworded the pre-existing "Run `make
  docs-registry` to regenerate after new docs are added" line in the Graphify Integration section,
  which had gone stale/contradictory now that regen is automatic on every ticket close — it now
  clarifies `make docs-registry` is for a manual mid-session preview only.
- Tests (`tests/tools/test_done_checker_static.py`): imported `check_registry_entry_regenerated`;
  bumped `test_run_finalize_selfcheck_all_pass` to `len(results) == 4`; added
  `test_run_finalize_selfcheck_surfaces_missing_registry_entry`; added five direct unit tests for
  `check_registry_entry_regenerated` covering entry-present (PASS), entry-absent (FAIL),
  nonzero-tool-exit-with-entry-present (still PASS, proving AC #2), no-tier-parameter behavior, and
  an ordering-guard test proving a ticket still in `tickets/inprogress/` produces FAIL (guards
  against the call site ever being moved to run before Finalize's move-to-done step); added
  `test_claude_md_documents_registry_regen_trigger` asserting the new CLAUDE.md prose is present.
  `tests/tools/test_generate_registry.py` untouched and still passes unmodified, confirming
  `generate_registry.py` internals were not touched.
- Parity ledger: at Implement time, `INFRA-183` was reviewed and deliberately left unedited — it
  describes `generate_registry.py`'s *output shape*, not invocation timing, and this ticket
  doesn't touch that file. That "left unedited" note was written before the Parity phase ran.
  The Parity phase (parity-updater agent, after Implement) subsequently added a **new** entry,
  `INFRA-263`, to `docs/parity_ledger/infrastructure.yaml` — documenting the ticket-close
  registry-regeneration gate itself as a distinct infrastructure guarantee, as a companion to
  (not an edit of) `INFRA-183`, following the existing precedent of other dev-tooling entries in
  that file (`INFRA-180`–`INFRA-182`, `INFRA-188`). `INFRA-183` itself remains untouched.

Verification: `python3 -m pytest tests/tools/test_done_checker_static.py
tests/tools/test_generate_registry.py -v --tb=short` — 93 passed.

## Test Summary

`tests/tools/test_done_checker_static.py` (52 tests) and `tests/tools/test_generate_registry.py`
(41 tests) — all 93 pass. New tests specifically added: `test_run_finalize_selfcheck_all_pass`
(updated to 4 conditions), `test_run_finalize_selfcheck_surfaces_missing_registry_entry`,
`test_check_registry_entry_regenerated_passes_when_entry_present`,
`test_check_registry_entry_regenerated_fails_when_entry_absent`,
`test_check_registry_entry_regenerated_nonzero_tool_exit_does_not_fail`,
`test_check_registry_entry_regenerated_applies_under_hotfix_tier`,
`test_registry_entry_check_ordering_guard_fails_if_ticket_still_inprogress`,
`test_claude_md_documents_registry_regen_trigger`.

## Files Changed

- `tools/gate_checks/done_checker_static.py`
- `.claude/workflows/implement-ticket.js`
- `CLAUDE.md`
- `tests/tools/test_done_checker_static.py`
- `docs/parity_ledger/infrastructure.yaml` (new `INFRA-263` entry, added by the Parity phase)

## Completion Summary

docs/REGISTRY.yaml regeneration is now an unconditional, non-blocking side effect of
`run_finalize_selfcheck` (Part B, post-Finalize), invoked from the existing `finalizeCheckOutput`
`bash()` call site in `implement-ticket.js` for every ticket close, all tiers including hotfix.
A new blocking 4th condition, `registry_entry_regenerated`, confirms the closing ticket's own
entry landed in the regenerated file before Finalize completes; a nonzero exit from
`generate_registry()` itself (e.g. an unrelated repo-wide frontmatter gap) is captured only as
non-blocking evidence text and never causes FAIL. CLAUDE.md's "After Work" section documents the
new unconditional trigger and the `git add docs/REGISTRY.yaml` staging instruction. The Parity
phase added `docs/parity_ledger/infrastructure.yaml`'s `INFRA-263` entry to track this new
guarantee as a companion to `INFRA-183` (which remains unedited, describing a different property).
