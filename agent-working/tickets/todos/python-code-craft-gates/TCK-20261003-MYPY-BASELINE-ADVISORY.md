---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-MYPY-BASELINE-ADVISORY
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-MYPY-BASELINE-ADVISORY

## Title
M4c: mypy baseline with mypy-baseline, advisory until the soak ends

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The CI typecheck job runs `mypy src/ ... || true` with continue-on-error, so nothing is gated. Roadmap 6.2 chose mypy + mypy-baseline to make it blocking without src/ edits; owner decision 2026-10-03: it soaks two weeks with the ratchet and flips in the same follow-up ticket. Measured 2026-10-03: 1,569 errors in 236 files.

## Scope
- Add `mypy-baseline` pinned exactly to a dependency group the typecheck job syncs; regenerate uv.lock and the requirements.txt export
- Generate the baseline from main at a stable path (e.g. registries/mypy_baseline.txt) and record its path and entry count in the code-health registry or snapshot per roadmap 6.3
- CI typecheck step: `mypy src/ --config-file pyproject.toml | mypy-baseline filter`, still advisory (keep `continue-on-error`; `|| true` removal is the flip ticket's job); job summary states new-error count
- `make typecheck-py` uses the same filter; document regenerating the baseline (`mypy-baseline sync`) and when it is allowed
- Update INFRA-TYPE-001 (docs/parity_ledger/infrastructure.yaml) evidence and tests/static/test_typecheck_gate_configured.py, listing each edit with its reason

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- Changing [tool.mypy] strictness, python_version or excludes
- Fixing any type error (the 104 name-defined errors are routed to the rpg domain separately)

## Acceptance Criteria
- [ ] Baseline committed; `mypy src/ ... | mypy-baseline filter` reports 0 new errors on main
- [ ] Investigate shows how mypy-baseline normalises line numbers, and a test or recorded demo proves an unrelated edit above an existing error does not resurface it, while a genuinely new error is reported
- [ ] CI typecheck step uses the filter, remains advisory, and its summary shows the new-error count
- [ ] `pytest tests/static/test_typecheck_gate_configured.py` passes; INFRA-TYPE-001 updated with v2_evidence
- [ ] `uv lock --check` passes and the export reproduces requirements.txt
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20260623-TYPE-CHECKER
- TCK-20261002-UV-REMAINING-CI-JOBS

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-001)
- docs/audits/D13_type_safety.md
- docs/archive/plans/open_audit_findings_backlog.md (Section 1G, cited by the CI comment)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260623-TYPE-CHECKER/

## Related Code Areas
- .github/workflows/test.yml (typecheck job)
- pyproject.toml, uv.lock, requirements.txt
- Makefile (typecheck-py)
- tests/static/test_typecheck_gate_configured.py
- docs/parity_ledger/infrastructure.yaml

## Assumptions / Open Questions
- Baseline churn: other domains edit src/ daily; the soak measures how often the baseline needs a sync. Record that rate for the flip decision
- Which dependency group: `dev` (typecheck job already syncs it) unless Investigate finds a reason for its own group

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
