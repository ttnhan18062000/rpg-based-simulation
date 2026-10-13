---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HARNESS-LLM-SECURITY-MAPPING
phase: open
date: 2026-10-13
tags: [ai, security, mcp, documentation]
---

# TCK-20261013-HARNESS-LLM-SECURITY-MAPPING

## Title
Map the agent harness against the OWASP LLM Top 10 (2025), with a threat model and a search MCP hardening checklist (docs only)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The owner accepted lead-planner-u24's recommendation on 2026-10-13 and confirmed it in the agent-working-planner
terminal. The recommendation comes from career-prepare's job-market input, which lead-planner-u24 checked against the
repo. This is docs only and needs no ADR. The aim is an honest record of which LLM-application security controls the
agent harness has, which it lacks, and where the evidence lives.

## Scope
New doc `docs/plans/agent_infrastructure/llm_security_mapping.md`, with valid frontmatter and three sections:
1. **OWASP LLM Top 10 (2025) mapping.** One row per risk (LLM01 Prompt Injection ... LLM10 Unbounded Consumption).
   Columns: what applies to this harness, controls present, controls missing, evidence (file:line or test path).
   Candidate controls to verify: pre/post tool hooks (`tools/agent-monitoring/pre_tool_hook.py`,
   `post_tool_hook.py`), the gate ledger (`tools/agent-monitoring/gate_ledger.py`), `tools/write_path_guard.py`,
   redaction in `tools/retrieval_cache.py` and `tools/agent_codex_posttool_adapter/`, `tools/sessions/boundary.py`, and
   the search MCP's token in `tools/search_shared.py`.
   **List a control as present only after reading its code and naming the line or test that shows it works.** Say
   "advisory" where it only warns; `boundary.py` is advisory, for example.
2. **Threat model: an agent with tool access.** Prompt injection through tool output (web, files, peer messages,
   artifacts), excess permissions, secret leakage (logs, monitoring shards, the public repo, the handover-transit
   bundle), log tampering (the JSONL monitoring shards are plain files in git). For each: entry point, impact, current
   mitigation, gap.
3. **Hardening checklist for the search MCP server** (`tools/search_mcp.py`, `search_server.py`, `search_shared.py`,
   `start_search_mcp.sh`): pinned dependency versions, scoped tokens and the socket and file permissions, tool
   allow-list, an append-only query log, idle exit. Mark each item done, partial or open, with evidence.
Link the doc from `docs/plans/agent_infrastructure/` index if one lists docs. Run `make knowledge-index-update`.

## Out of Scope
- Any code change. Gaps found become separate tickets proposed in the doc's last section, not fixed here.
- The gitleaks/Semgrep CI lane (platform domain).
- Claims about Claude Code's own internal sandboxing beyond what this repo configures (`.claude/settings.json`, hooks).

## Acceptance Criteria
- AC1: all 10 OWASP rows are present. Every "present" control cites code or a test that was read. No control is
  listed as present without evidence.
- AC2: the threat model covers the four named threats, with entry point, impact, mitigation and gap for each.
- AC3: the checklist covers the five named items for the search MCP, each marked done, partial or open, with evidence.
- AC4: the frontmatter validates, and the knowledge index is updated.
- AC5: a "Proposed follow-ups" list names the gaps. Nothing is filed without the planner.

## Related Tickets
- TCK-20260705-WORKFLOW-SECURITY-GATE; TCK-20261013-SEARCH-MCP-FILES-OWNED (same batch); #527.

## Related Docs
- docs/plans/agent_infrastructure/; docs/agent-monitoring/; docs/guides/delivery_process.md (handover-transit rule, public repo).

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261013-HARNESS-LLM-SECURITY-MAPPING/ (created at close)

## Related Code Areas
- tools/agent-monitoring/{pre_tool_hook,post_tool_hook,gate_ledger}.py, tools/write_path_guard.py, tools/retrieval_cache.py,
  tools/agent_codex_posttool_adapter/, tools/sessions/boundary.py, tools/search_*.py, .claude/settings.json

## Assumptions / Open Questions
- The OWASP LLM Top 10 2025 list is cited by its published IDs and titles. The implementer confirms the titles from the
  source and records the URL and access date.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
