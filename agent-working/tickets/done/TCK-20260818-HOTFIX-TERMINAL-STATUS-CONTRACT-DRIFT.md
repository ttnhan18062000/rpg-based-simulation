---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT
phase: done
date: 2026-08-18
tags: [ai, testing, mcp]
---

# TCK-20260818-HOTFIX-TERMINAL-STATUS-CONTRACT-DRIFT

## Title
Register TEST_SCOPE_COVERAGE_FAILED in the terminal-status contract; fix line-number/count drift it caused

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI "Agent orchestration / codex / replay" job failed after
`TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP`'s push: that ticket added a new terminal
status (`TEST_SCOPE_COVERAGE_FAILED`) to `.claude/workflows/implement-ticket.js`'s Test phase, but
never touched `agent-orchestration/terminal-statuses.yaml` — the authoritative contract file a
whole conformance-test system (`tests/agent_orchestration_claude_adapter/`,
`tests/agent_orchestration/`) cross-checks the live workflow file against. This job runs tests
outside `tests/tools/`, so my own earlier local verification (scoped to `tests/tools/` for that
ticket) never exercised it — a real instance of exactly the class of gap that ticket was fixing,
now surfaced one layer up.

## Scope
- Register `TEST_SCOPE_COVERAGE_FAILED` in `agent-orchestration/terminal-statuses.yaml` (kind:
  literal, phase: Test) — this is the authoritative fix; not a divergence-log entry, since this is
  a genuine, permanent, intentional new terminal status, not a temporary contract/live mismatch.
- Fix the resulting count/line-number drift in `tests/agent_orchestration_claude_adapter/
  test_terminal_status_extractor.py`, `test_terminal_status_conformance.py`,
  `test_terminal_status_schema.py`, `test_generator_containment.py`, and
  `tests/agent_orchestration/test_contract_structure.py` — all hardcode exact counts (13→14
  literal call sites, 15→16 distinct values) and the shifted `FINALIZE_INCOMPLETE` call-site line
  numbers (1457,1469 → 1498,1510) that my insertion pushed down.
- Reproduce the real CI failure fully locally first (fresh venv on PATH, `CI=true`, the job's
  exact command) before touching anything, per this session's established discipline.

## Out of Scope
- Extending `tools/gate_checks/test_scope_coverage_static.py` to also map
  `.claude/workflows/*.js` changes to `tests/agent_orchestration*` — this is a real, disclosed
  residual gap (see Implementation Notes) left for a follow-up ticket to scope deliberately,
  not patched in as an afterthought here.
- Any other terminal-status contract changes beyond registering the one new value.

## Acceptance Criteria
- [x] `TEST_SCOPE_COVERAGE_FAILED` registered in `agent-orchestration/terminal-statuses.yaml`.
- [x] All stale count/line-number assertions across the 5 affected test files updated to the real,
      current values — reproduced and verified locally before pushing.
- [x] Full "Agent orchestration / codex / replay" job command passes clean locally
      (`CI=true`, exact job command) before pushing.
- [x] The residual scope gap (this class of drift for `.claude/workflows/*.js` changes) is
      disclosed, not silently left implicit.

## Related Tickets
- TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP (introduced the new terminal status this
  hotfix registers)
- TCK-20260818-KGMCP-EFFICIENCY-REMEDIATION-EPIC (parent epic)

## Related Docs
None — no behavior/mechanics change beyond the contract registration itself.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `agent-orchestration/terminal-statuses.yaml`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py`
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py`
- `tests/agent_orchestration/test_contract_structure.py`

## Assumptions / Open Questions
None.

## Implementation Notes
Real CI log successfully fetched via `gh api repos/.../actions/jobs/<id>/logs` (Fortinet block
intermittently doesn't trigger — worth retrying this call before falling back to blind local
reproduction, same lesson as earlier today's websocket-race hotfix). Confirmed
`terminal_status_schema_version` correctly stays `1` — per `agent-orchestration/README.md`'s
versioning note, a non-breaking content addition (new entry) never bumps a file's schema-version
counter, only a structural/breaking change does.

**Disclosed residual gap**: this incident is structurally the same class as
`TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP` fixed for `tools/`/`src/` changes — a
change to a file outside the scope that ticket's new `test_scope_coverage_static.py` check
covers (`.claude/workflows/*.js`) broke tests in a directory
(`tests/agent_orchestration_claude_adapter/`, `tests/agent_orchestration/`) that check never
considers, because those tests aren't reached by the `src/`/`tools/` file-to-test-directory
mapping at all — they're static-source-text-parsing tests keyed on `.claude/workflows/
implement-ticket.js` itself. Extending the coverage check to also require `tests/
agent_orchestration*` whenever `.claude/workflows/*.js` or `.claude/agents/*.md` changes is a real
follow-up worth scoping deliberately (own investigation/plan, own test-plan for a second file-tree
mapping), not patched into this already-closed ticket's own gate reactively.

## Test Summary
Reproduced the real failure locally first: `CI=true pytest tests/agent_codex_live_transport
tests/agent_codex_pilot_executor tests/agent_codex_pilot_guardrails
tests/agent_codex_pilot_orchestration tests/agent_codex_posttool_adapter
tests/agent_codex_realrepo_pilot_harness tests/agent_codex_runtime_shadow
tests/agent_orchestration tests/agent_orchestration_claude_adapter
tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow
and not extra_slow" --tb=short -q` — 4 failed initially (contract registration + 2 stale test
files), then 3 failed after the first fix round (3 more stale-count assertions in
sibling/downstream test files), then **385 passed, 5 skipped, 0 failed** after all fixes.

## Files Changed
- `agent-orchestration/terminal-statuses.yaml`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py`
- `tests/agent_orchestration_claude_adapter/test_terminal_status_schema.py`
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py`
- `tests/agent_orchestration/test_contract_structure.py`

## Completion Summary
Registered the new `TEST_SCOPE_COVERAGE_FAILED` terminal status in the authoritative
`agent-orchestration/terminal-statuses.yaml` contract and fixed the resulting cascade of
hardcoded count/line-number assertions across 5 test files, verified via full local reproduction
of the real CI job before pushing. Notably, this incident is itself a live instance of the exact
class of test-scoping gap the ticket that caused it was built to fix — just one layer removed
(a `.claude/workflows/*.js` change, not a `tools/`/`src/` change) — disclosed honestly as a real
residual gap rather than silently patched over.
