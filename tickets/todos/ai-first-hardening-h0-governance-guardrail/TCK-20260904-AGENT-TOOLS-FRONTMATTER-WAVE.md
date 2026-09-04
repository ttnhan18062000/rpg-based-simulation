---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE
phase: open
date: 2026-09-04
tags: [governance, ai]
---

# TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE

## Title
Per-agent tools: frontmatter wave-based rollout, gated on usage-audit baseline

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
GATED ON the tool-usage baseline audit ticket (TCK-20260904-AGENT-TOOL-USAGE-BASELINE), which was created in this same batch. Step 0, blocking, before any wave begins: empirically verify on concern-investigator (the only agent with a tools: field today) whether tools: is actually enforced at the harness level and whether disallowedTools is recognized — observed directly, not assumed from docs. Then run an offline candidate-policy replay per agent using the usage-audit ticket's usage table, classifying every historical 'would deny' call under a 5-way taxonomy (legitimate-but-rare / obsolete / inappropriate-legacy / accidental / unclear-needs-review). Sizing rule is smallest confident scope, not theoretical minimum. Rollout is wave-based, each wave gated on the prior wave's clean observation window: Wave 1 (11 read-oriented roles), Wave 2 (architecture-reviewer, security-reviewer, planner), Wave 3 (implementer, parity-updater — highest blast radius, last). Rollback per wave is a documented single-file frontmatter revert, written before that wave starts.

## Scope
- Step 0 (blocking, before Wave 1): empirically observe and document real harness behavior for both tools: and disallowedTools on concern-investigator by directly attempting a tool call outside its declared scope
- Offline candidate-policy replay per agent against the usage-audit ticket's usage table, with every historical 'would deny' call classified under the 5-way taxonomy
- Wave-based rollout: Wave 1 (11 read-oriented roles) -> Wave 2 (architecture-reviewer, security-reviewer, planner) -> Wave 3 (implementer, parity-updater), each gated on the prior wave's clean observation window
- A documented, trivial single-file frontmatter revert command written before each wave lands
- Parametrized extension of test_concern_investigator_agent_definition.py's pattern to verify each landed agent's tools: field

## Out of Scope
- Beginning implementation before TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table is committed
- Any change to agent files beyond tools:/disallowedTools frontmatter scoping
- Resolving the Guardrail Enforcement epic's test-scoper-hang-guard ticket's three-way file-overlap on .claude/agents/-adjacent files beyond coordinating to avoid clobbering concurrent edits

## Acceptance Criteria
- [ ] Step 0 empirical verification performed before Wave 1: an actual attempt to invoke a tool not in concern-investigator's tools: field is made and the real harness behavior (hard-denied vs. silently-allowed vs. merely-absent-from-list) is directly observed and documented — the prior TCK-20260709 smoke test does not satisfy this; disallowedTools checked the same way
- [ ] Rollout does not begin until TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table exists and is linked as this ticket's input dependency
- [ ] For every Wave 1 agent, a candidate tools: scope is proposed with every historical 'would deny' call classified per the 5-way taxonomy — no capability silently dropped without that classification
- [ ] After a wave lands, each of that wave's agent files carries an explicit tools: field verified by a parametrized extension of test_concern_investigator_agent_definition.py's pattern, plus a documented single-file revert command written before the change lands

## Related Tickets
- Depends on TCK-20260904-AGENT-TOOL-USAGE-BASELINE — do not begin implementation until that ticket's usage table is committed
- TCK-20260709-CONCERN-INVESTIGATOR-AGENT (added the repo's only tools: field; its runtime-verification evidence is weaker than Step 0 requires)
- TCK-20260707-SUBAGENT-FRONTMATTER (explicitly deferred tools:/model: scoping as a follow-up — this ticket is that deferred follow-up)

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/concern-investigator.md
- .claude/agents/*.md
- .claude/settings.json
- tests/tools/test_concern_investigator_agent_definition.py

## Assumptions / Open Questions
- The only existing 'runtime verification' evidence (TCK-20260709) is weaker than Step 0 requires — it only showed the agent chose not to call Edit/Write, not that an attempted call would be blocked
- disallowedTools has zero local precedent in this repo, only third-party docs
- The harness does not hot-reload .claude/agents/ mid-session (requires session restart) — wave observation windows must account for this
- TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table does not exist yet at ticket-creation time — this ticket must not be scheduled for implementation ahead of that one landing
- Wave 3 (implementer, parity-updater) carries the highest blast radius and must land last
- Roadmap flags a three-way file-overlap point with Guardrail Enforcement's M3 (TCK-20260904-TEST-SCOPER-HANG-GUARD, this same batch) around .claude/agents/-adjacent files — coordinate, don't let concurrent edits clobber each other

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
