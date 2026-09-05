---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-BASH-SECRET-SCAN-HOOK
phase: blocked
date: 2026-09-04
tags: [governance, ai, hooks, security]
---

# TCK-20260904-BASH-SECRET-SCAN-HOOK

## Title
Bash secret-exposure advisory hook (BLOCKED pending re-ratification and extraction)

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
This ticket is BLOCKED. It was originally gated on a cross-epic hard prerequisite: scan_for_secrets() must first be extracted out of tools/knowledge_gateway_redaction.py into a location independent of the knowledge-gateway module, as milestone 1 of a separate "Remove/archive knowledge-gateway" standalone item. That knowledge-gateway-removal work was explicitly skipped this pass, because it conflicts with the already-ratified TCK-20260824-KGMCP-KEEP-OR-DEPRECATE decision ("keep as-is, no further investment... No changes to tools/knowledge_gateway_mcp.py or any related module are authorized by this decision"). That means this ticket's hard prerequisite (the scan_for_secrets() extraction) is now also blocked, pending a fresh re-ratification decision that has not happened. (Live confirmation during ticket creation: the knowledge-gateway MCP tools are still fully functional and callable today — this is not dead/disabled infrastructure, just underused — so there is no urgency pressure to route around the ratification.) Once unblocked and extracted, the plan is to reuse scan_for_secrets(text: str) -> str | None as-is, wired as a NEW advisory-only PreToolUse hook matching Bash in .claude/settings.json, following the exact shell-wrapper pattern already used by every other hook there — scanning the outgoing command string itself, never denying, and scoped strictly to secret-shaped values (not a dangerous-command policy, not command-injection detection).

## Scope
- Once unblocked: wire scan_for_secrets() (reused unmodified, post-extraction) as a new hooks.PreToolUse entry matching Bash in .claude/settings.json, following the exact existing shell-wrapper pattern (python3 -c one-liner parsing tool_input.command from stdin JSON, emitting hookSpecificOutput.additionalContext)
- Scan the outgoing Bash command string itself, advisory-only — warning via additionalContext, never permissionDecision/deny
- New test file (e.g. tests/tools/test_bash_secret_scan_hook.py) asserting both positive-fire (synthetic secret-shaped command) and negative-no-fire (ordinary command) cases, closing the currently-zero settings.json-embedded-hook test coverage gap

## Out of Scope
- The scan_for_secrets() extraction step itself — that belongs to the separate knowledge-gateway removal/archive item, which is out of scope this pass and currently skipped pending re-ratification
- Any dangerous-command or command-injection detection policy
- Any modification to scan_for_secrets()'s own logic or its 10-pattern _SECRET_SCAN_PATTERNS list
- Catching commands that merely read a secret (e.g. cat ~/.aws/credentials) — accepted named limitation, not a gap to close

## Acceptance Criteria
- [ ] New hooks.PreToolUse entry with matcher: Bash whose embedded python3 -c one-liner parses tool_input.command and, on match, emits valid {"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"..."}} JSON — never permissionDecision/deny
- [ ] A synthetic secret-shaped command (matching any of the 10 existing patterns) produces non-empty additionalContext naming the pattern; an ordinary command (git status, pytest tests/) produces no output
- [ ] Hook calls scan_for_secrets() unmodified — verified by a diff showing the (post-extraction) module is unchanged by this ticket except for the extraction landing separately
- [ ] New test file (e.g. tests/tools/test_bash_secret_scan_hook.py) asserts both positive-fire and negative-no-fire cases via subprocess/thin wrapper, closing the settings.json-hook coverage gap

## Related Tickets
- Depends on a future knowledge-gateway re-ratification and scan_for_secrets() extraction ticket — neither exists yet; this ticket is BLOCKED until both land
- TCK-20260824-KGMCP-KEEP-OR-DEPRECATE (ratified 2026-08-24: "keep as-is, no further investment... no changes authorized" — this is the ruling blocking the hard prerequisite)
- TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH (done — added scan_for_secrets() originally, no hook wiring)
- TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY (done — ratified the reject-outright policy scan_for_secrets() implements)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (done — closest prior-art for adding a new advisory PreToolUse hook)

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_gateway_redaction.py
- .claude/settings.json
- tests/tools/test_knowledge_gateway_redaction.py

## Assumptions / Open Questions
- BLOCKED: this milestone cannot proceed until (a) a repository-owner re-ratification supersedes TCK-20260824-KGMCP-KEEP-OR-DEPRECATE's "no changes authorized" ruling for the knowledge-gateway module, and (b) scan_for_secrets() is actually extracted to a gateway-independent location (to be tracked as a separate not-yet-created ticket once re-ratification happens)
- This ticket must not be scoped to include the extraction step itself — that belongs to the knowledge-gateway item, explicitly out of scope this pass
- Shared-file coordination note (not a real sequencing dependency): .claude/settings.json's hooks block is also touched by this batch's TCK-20260904-TEST-SCOPER-HANG-GUARD and by a separate, not-in-this-batch Workflow Reliability ticket — coordinate at merge time via rebase, don't let this block scheduling
- Every hook in settings.json is wrapped 2>/dev/null || true so a malformed entry fails silently — no CI currently validates settings.json's embedded shell snippets; this ticket may end up owning a small smoke-test addition for its own entry
- Named/accepted limitation must be documented, not silently dropped: this hook catches embedded secret literals only, not commands that merely read a secret
- Confirmed live during ticket creation (2026-09-04): the knowledge-gateway MCP tools (mcp__knowledge-gateway__knowledge_status, knowledge_context) are still fully registered and functional, not disabled — the underlying infra is underused, not broken, which removes any technical urgency to bypass the pending re-ratification

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
