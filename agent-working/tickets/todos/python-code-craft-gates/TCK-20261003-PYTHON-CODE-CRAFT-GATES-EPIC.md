---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
phase: open
date: 2026-10-03
tags: [delivery, planning]
---

# TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC

## Title
M4: Python Code Craft gates — advisory CI ratchet, SARIF feedback, mypy baseline, prek, type-checker trial

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
Roadmap milestone M4 (python_code_craft_roadmap.md Section 7). M1 to M3 closed under TCK-20261002-PYTHON-CODE-CRAFT-EPIC (PRs #288, #297, #298). The owner approved the toolchain (decision 8.8), a two-week advisory soak before any gate blocks (8.10), and on 2026-10-03: mypy soaks with the ratchet, changed-line feedback via SARIF code scanning, prek installed opt-in only, jscpd report-only. Scope-only epic; children listed in SEQUENCE.md.

## Scope
- Track the six child tickets in SEQUENCE.md order
- Record the soak start date (merge of the advisory CI job) and end date (start + 14 days) here and in the roadmap
- Soak start: date of batch PR merge (the PR that carries TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB; the closure commit writes the real date). Soak end: start + 14 days.

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Roadmap M5, M6, M7

## Acceptance Criteria
- [ ] Children 1 to 5 in agent-working/tickets/done/
- [ ] Child 6 (flip) is filed with the soak end date and either done or explicitly carried forward by the owner
- [ ] Roadmap Section 7 marks M4 done or names what carries forward

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- the six children in SEQUENCE.md

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tools/code_health/
- registries/code_health_exceptions.jsonl
- pyproject.toml, uv.lock, Makefile

## Assumptions / Open Questions
- Measured 2026-10-03 on main b90c3aa9: mypy 2.1.0 reports 1,569 errors in 236 of 710 files under src/ (48 s, ~400 MB); registry holds 3,617 rows, all reviewed: false
- Hand-written by codebase-planner from the approved brief (not a create-tickets run); each child's Investigate phase must confirm its facts

## Implementation Notes
- **Monitoring-shard repair at closure (owner decision, relayed and confirmed through two blocking questions):** after the unexpected session close, line 674 of `agent-working/agent-monitoring/data/2026-W40/python-code-craft-gates.tools.jsonl` held 717 NUL bytes followed by one valid JSON row (perf-planner session `cef84786`, Bash tool, ts `2026-10-03T15:53:17.951560Z`); the NULs were in the uncommitted tail (the committed and pushed copies had none) and made `record_hand_orchestrated_closure.py` crash in `compute_tool_stats` with `JSONDecodeError`. My first description called the whole line NULs and proposed deleting it; that was wrong and was corrected before anything was edited (a safety assertion stopped the edit). The owner chose "strip only the leading NUL bytes". Done with a backup first: line 674 went from 1,073 to 356 bytes (717 NUL bytes removed), the file had 793 lines before and after, 0 NUL bytes remain, every line parses as JSON, a byte-for-byte comparison with the backup shows only line 674 differs, and the committed content is an exact prefix of the repaired file. The perf-planner row is intact. No other shard line was edited.
- **Progress (PR #305, CI run 37134889219 green):** children 1 to 5 are done (`CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB`, `MYPY-BASELINE-ADVISORY`, `CODE-HEALTH-SARIF-PR-FEEDBACK`, `PREK-GIT-HOOKS-OPT-IN`, `TYPE-CHECKER-TRIAL`). Child 6 (`CODE-HEALTH-GATES-FLIP-BLOCKING`) stays BLOCKED until the soak ends; this epic closes after it. Open follow-up: write the real soak start (the PR #305 merge date) and end (+14 days) into this epic, roadmap Section 7 and the flip ticket in the first commit of the next codebase batch.

## Test Summary

## Files Changed

## Completion Summary
