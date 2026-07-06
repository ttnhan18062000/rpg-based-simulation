---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260706-SCOPE-TAG-REGISTRY-CHECK
artifact_type: test_plan
tags: [tagging, workflows, agent-monitoring]
---

# Test Plan — TCK-20260706-SCOPE-TAG-REGISTRY-CHECK

## Unit tests — `tests/tools/test_tag_registry.py` (new test functions)

- `test_check_tags_registered_all_registered_returns_empty`
- `test_check_tags_registered_returns_only_unregistered_subset`
- `test_check_tags_registered_phase_tags_never_flagged`
- `test_check_tags_registered_empty_input_returns_empty`

## Regression suites

```bash
pytest tests/tools/test_tag_registry.py -v
pytest tests/tools/ -q --ignore=tests/tools/test_knowledge_search.py
```
Zero new failures beyond the 2 pre-existing, unrelated `test_search_mcp.py` failures already
disclosed earlier this session.

## Non-pytest verification

- `node --check .claude/workflows/implement-ticket.js` — syntax valid.
- Manual read-through of the new gate block and updated `pushEvent` call, confirming it mirrors the
  `CONFLICTS_DETECTED` shape exactly (return fields, `writeMonitoring` call, log guidance).
- Manual bracket-balance check on the updated `docs/ai/ticket-lifecycle.md` Mermaid diagram (same
  method used in `TCK-20260706-DIAGRAM-COVERAGE`).
- `validate_frontmatter.py` on all touched docs.
- Cannot exercise the new gate via a live `implement-ticket` run on this ticket itself (same
  bootstrapping limitation as `TCK-20260706-MONITORING-REASON-CODE` and
  `TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER`) — verified via code read-through and the pure
  Python unit tests instead.

## Acceptance-criteria-to-check mapping

- "check_tags_registered exists, tested" → the 4 unit tests.
- "caught at Scope for both branches" → code read-through confirms the check runs on
  `ticketInfo.tags` regardless of which prompt branch produced it (orchestrator-run, not
  branch-specific).
- "reason_code correct for both Scope causes" → manual trace of the updated `pushEvent` call logic
  (no live run possible, per the bootstrapping limitation above).
- "docs accurate" → manual review of all 3 doc files.
