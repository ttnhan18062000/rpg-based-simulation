---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260929-TOOLS-ORPHAN-FILE-CHECK
phase: open
date: 2026-09-29
tags: [process-improvement]
---

# TCK-20260929-TOOLS-ORPHAN-FILE-CHECK

## Title
Add an on-demand report-only orphan-file check over all of tools/

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The 8 orphaned tooling files handled by this epic were found by hand, and nothing stops new orphans from building up the same way. The author asked for a standing, repeatable check that flags tools/ files with no live cross-references. Once scripts/ is retired it covers all of tools/ recursively. Per the user decision it stays on-demand: a Makefile target only, not a CI gate, exit 0 report-only, with no ratchet, because checks over agent tooling should stay proportionate. It is a new tools/gate_checks/ module (named for what it does, e.g. tools_orphan_check.py) following the check_*() -> [{status, evidence}] and MARKER:+JSON shape. It sorts each tracked tools/ file into NO_REFERENCES / DOC_ONLY / TEST_ONLY / LIVE with the referencing files as evidence. DOC_ONLY and TEST_ONLY are kept separate from LIVE because the investigation measured that counting any doc mention hides every real orphan, and that DOC_ONLY does not mean dead (e.g. documented hand-run tools). This matters because it turns a one-off manual audit into a cheap, deterministic report that can be rerun.

## Scope
- Add a new tools/gate_checks/ module (e.g. tools_orphan_check.py) with a check_*() function returning List[{"status","evidence"}] and a __main__ that prints one "MARKER:"+json line and always exits 0. Model it on tools/gate_checks/working_log_duplicate_check.py and status_drift_check.py.
- Scan a deterministic, sorted, git-tracked file list, and build a one-pass token index (word-boundary identifier tokens, reusing the IDENT_RE approach from tools/audit_unreachable_code.py without importing it) instead of a per-tool regex scan.
- Classify each tracked tools/ file (skipping __init__.py and __pycache__) as exactly one of NO_REFERENCES, DOC_ONLY, TEST_ONLY or LIVE, listing the referencing files as evidence. Match on bare stems as well as paths, to cover sys.path sibling imports in hyphenated tools/agent-monitoring/, and exclude a file's own mentions of itself and its own package.
- Count Makefile and .claude/settings.json hook entrypoints (including .sh/.html references) as LIVE wiring. Ignore hits in tickets/done/, docs/archive/ and stored_artifacts/.
- Exclude the codex subtrees (tools/agent_codex_*, agent_orchestration_*, agent_replay_*) via a named constant that cites TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC, and report them in an explicit "excluded" bucket rather than skipping them silently.
- Disambiguate from tools/agent-monitoring/epic_scope_orphan_check.py (a different meaning of 'orphan') in the module docstring.
- Add a Makefile target `name: ## ... (on-demand only — not CI)` and list it in .PHONY.
- Add deterministic tests in tests/tools/ using a tmp_path mini-repo (or a minimal frozen fixture), plus a pure-text Makefile wiring test like test_makefile_wires_status_drift_check, and a real-corpus test that asserts structure only.

## Out of Scope
- Wiring the check into CI or any .github/workflows file.
- A ratchet, baseline or non-zero exit on findings (removed precedent: TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION).
- Deleting or moving any file the check flags; dispositions stay a separate human decision.
- Reusing tools/code_test_index.py (depends on untracked graphify-out/graph.json) or importing tools/audit_unreachable_code.py.
- Scanning the codex subtrees' contents beyond listing them as excluded.
- Regrouping flat top-level tools/ files.
- CLAUDE.md edits.

## Acceptance Criteria
- [ ] Running the module prints exactly one line starting with "MARKER:" followed by valid JSON, and exits 0 regardless of findings.
- [ ] Every tracked tools/ file except __init__.py and __pycache__ appears in exactly one of NO_REFERENCES, DOC_ONLY, TEST_ONLY or LIVE, each with its referencing files as evidence; codex subtree files appear only in an "excluded" bucket.
- [ ] tmp_path test (a): a tools/ file referenced only by a bare-stem `from foo import x` in another tools/ file is classified LIVE.
- [ ] tmp_path test (b): a tools/ file referenced only from tests/ is classified TEST_ONLY.
- [ ] tmp_path test (c): tools/test_docker.py is NOT matched by a file named test_docker_compose_dependency_hygiene (word-boundary tokens).
- [ ] tmp_path test (d): references located only in tickets/done/, docs/archive/ or stored_artifacts/ are ignored (the file is classified NO_REFERENCES).
- [ ] tmp_path test (e): a reference from the Makefile or from .claude/settings.json (including .sh/.html entrypoints) makes the file LIVE.
- [ ] Two consecutive runs produce byte-identical JSON, and the working tree is unmodified afterwards.
- [ ] The Makefile has a target whose help text contains `(on-demand only — not CI)`, the target is listed in .PHONY, and a pure-text test pins both. No .github/workflows file references the module.
- [ ] A real-corpus run completes within the test timeout, using the one-pass index rather than the per-tool regex scan that took over 300s.

## Related Tickets
- TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC
- TCK-20260929-RETIRE-SCRIPTS-DIR
- TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT
- TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION
- TCK-20260810-STATUS-DRIFT-CHECK-WIRING
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC

## Related Docs
- docs/plans/scripts_tools_governance_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/status_drift_check.py
- tools/gate_checks/working_log_duplicate_check.py
- tools/gate_checks/premise_staleness_check.py
- tools/audit_unreachable_code.py
- tools/code_test_index.py
- tools/agent-monitoring/epic_scope_orphan_check.py
- Makefile
- .claude/settings.json
- tests/tools/test_status_drift_check.py
- tests/tools/test_working_log_duplicate_check.py
- expected: tools/gate_checks/tools_orphan_check.py
- expected: tests/tools/test_tools_orphan_check.py

## Assumptions / Open Questions
- Depends on TCK-20260929-RETIRE-SCRIPTS-DIR. The first meaningful real-corpus run happens only after scripts/ is retired, and the real-corpus test asserts structure only, never specific counts.
- Generic file stems (e.g. utils, common) will collide with unrelated tokens and cause false negatives (files wrongly classed as referenced). This is accepted as the safer direction, and whether to add a stem denylist is left open.
- DOC_ONLY is weak evidence and does not mean dead (e.g. audit_unreachable_code.py is a documented hand-run tool). The report must present it as 'review', not 'delete'.
- Measured today: code/wiring-only counting yields about 7 no-reference files and 19 TEST_ONLY. These numbers will shift after the scripts/ retirement and are not acceptance targets.
- The exact module name (tools_orphan_check.py) and Makefile target name are recommendations.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
