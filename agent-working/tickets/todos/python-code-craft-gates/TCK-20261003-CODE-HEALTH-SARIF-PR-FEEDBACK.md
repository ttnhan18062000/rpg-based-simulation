---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
phase: open
date: 2026-10-03
tags: [delivery, security]
---

# TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK

## Title
M4b: Changed-line PR feedback through SARIF upload to GitHub code scanning (advisory)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision 2026-10-03: PRs get changed-line feedback through SARIF upload to GitHub code scanning, not reviewdog comments. ruff and complexipy emit SARIF; findings already held in the code-health registry must be filtered out so a PR shows only what it introduced. Advisory during the soak.

## Scope
- Produce SARIF for ruff and complexipy on the PR's changed `.py` files, filter out findings that match an existing registry row (same key the ratchet uses), and upload with `github/codeql-action/upload-sarif` pinned by version
- Grant `security-events: write` only on the job that uploads; no other permission change
- May be steps in the `code-health` job from TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB if wall time allows, else its own advisory job
- A small, tested filter in tools/code_health/ (SARIF in, SARIF out)
- Document where agents read results (job summary first, code-scanning tab second) in the environment guide

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check required or blocking (that is TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING, after the soak)
- reviewdog, diff-quality, PR comments
- jscpd and line-count SARIF (no native SARIF; report-only)

## Acceptance Criteria
- [ ] On a PR that adds one new ruff violation in a changed file, code scanning shows exactly that finding and none of the registry's existing rows (demonstrated on the real PR run or a recorded test PR)
- [ ] Unit tests for the SARIF filter cover: matching row filtered, new finding kept, worse-than-row finding kept, malformed SARIF reported not swallowed
- [ ] Only the uploading job has `security-events: write`; a static test asserts it
- [ ] The step cannot fail the PR during the soak
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB (depends on)

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tools/code_health/
- registries/code_health_exceptions.jsonl

## Assumptions / Open Questions
- Depends on the reseed ticket (the filter reads the reseeded registry)
- Security-tagged: workflow permissions change, so the Security-Review phase runs
- Code scanning on a public repo needs no licence; Investigate confirms the repository setting is enabled (owner action if not)
- complexipy SARIF output support and its symbol keys must be confirmed against complexipy 8.0.1

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
