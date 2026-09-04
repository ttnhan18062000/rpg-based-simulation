---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-CAPABILITY-ENVELOPE-BASELINE
phase: open
date: 2026-09-04
tags: [governance, ai, security]
---

# TCK-20260904-CAPABILITY-ENVELOPE-BASELINE

## Title
Capability-envelope baseline file and auditable diff check

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
Per the frozen proposal's configuration-precedence invariant ("effective local capability ⊆ approved capability envelope"), commit a version-controlled baseline file describing the approved capability envelope, kept separate from the git-ignored settings.local.json. Write a small auditable comparison script that diffs the live settings.local.json against that baseline and flags any entry outside it. This is explicitly auditable tooling only — there is no confirmed runtime-enforcement mechanism today, so the ticket must not claim to provide a proven runtime guarantee. Gated on nothing, runs in parallel with the tool-usage baseline audit ticket.

## Scope
- New version-controlled baseline file describing the approved capability envelope, following the tag_registry.py/layer_registry.py registry convention (documented lifecycle, stable location, script-enforced)
- Baseline covers all of settings.local.json's schema fields: permissions.allow plus the enableAllProjectMcpServers/enabledMcpjsonServers/disabledMcpjsonServers fields — not just permissions.allow
- New diff script comparing the live .claude/settings.local.json against the committed baseline and flagging any out-of-envelope entry
- Script/report output explicitly states its audit-only, no-runtime-enforcement nature in its own docstring or printed output

## Out of Scope
- Any change to settings.json's hooks mechanism
- Fixing settings.local.json's git-ignore coverage gap (only the user's personal global gitignore covers it today, not the repo's own tracked .gitignore) — flagged as a related risk, not fixed here
- Building or claiming any actual runtime-enforcement mechanism

## Acceptance Criteria
- [ ] Baseline file covers all settings.local.json schema fields observed in the live file (permissions.allow plus the 3 MCP server fields), not just permissions.allow
- [ ] Diff script run against the real settings.local.json (114 permissions.allow entries as of investigation) produces a real, non-stub report
- [ ] Diff script/report explicitly states audit-only / no-runtime-enforcement in its own output or docstring
- [ ] Positive and negative control cases both verified: a clean-baseline input produces an empty/clean result, and an out-of-envelope entry produces a flagged result

## Related Tickets
- No duplicate or overlapping ticket found

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/settings.local.json
- .claude/settings.json
- .gitignore
- docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md
- tools/tag_registry.py
- tools/layer_registry.py
- .claude/agents/concern-investigator.md
- tests/tools/test_tag_registry.py
- tests/tools/test_layer_registry.py

## Assumptions / Open Questions
- The frozen proposal's "~70 permissions" figure is stale — the real live count is 114 entries; baseline scoping must be derived from current live data, not the proposal's stale figure
- settings.local.json's git-ignore status is only enforced by the user's personal global ~/.config/git/ignore, not this repo's own tracked .gitignore — a real gap worth flagging even though fixing it is explicitly out of scope
- settings.local.json differs per machine/worktree (this worktree currently has none) — the diff script must define unambiguously which file/path it targets
- The live file has near-duplicate command variants and some very broad entries (e.g. Read(//tmp/**), Bash(find / -maxdepth 8 ...), Bash(gh api *), Bash(ps *)) — exact-string vs. normalized comparison design materially affects false-positive/negative rate and must be an explicit design decision

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
