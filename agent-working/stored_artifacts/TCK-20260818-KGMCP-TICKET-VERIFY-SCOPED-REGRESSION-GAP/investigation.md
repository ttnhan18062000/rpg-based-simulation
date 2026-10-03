---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP
artifact_type: investigation
tags: [testing, process-improvement, mcp]
---

# Investigation: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP

## Root Cause

The Test phase's `test-scoper` sub-agent is defined by `.claude/agents/test-scoper.md`. Its
entire "Test Directory Map" (the reference table it uses to map a changed file to the test
directory that must run) only ever documented `src/` → `tests/unit/<subsystem>/`. It had **no
entry at all** for `tools/` — a second, equally real, independently-tested source tree in this
repo:

```
$ ls tools/*.py | wc -l
52
$ ls tests/tools/*.py | wc -l
128
```

`tools/retrieval_cache.py` and `tools/knowledge_gateway_redaction.py` — the two modules
`TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` legitimately changed —
both live under `tools/`, not `src/`. Because the agent's own mapping instructions never mention
`tools/` at all, there was no rule that would have told it to scope in `tests/tools/` for that
ticket's diff. The agent instead scoped its own new test files individually
(`tests/tools/test_agent_ops_dashboard_stats.py`, etc.) plus a `src/api/` subsystem directory —
a reasonable-looking command that happened to never include the two pre-existing tests
(`test_knowledge_gateway_cache.py`, `test_knowledge_gateway_redaction.py`) that broke.

This is confirmed structural, not a one-off agent mistake: the Test Directory Map is the agent's
only source of truth for what to scope, and it was silently incomplete for an entire source tree.

## Wiring Confirmation

`implement-ticket.js`'s Test phase (`.claude/workflows/implement-ticket.js:1008-1047`) really
does dispatch to `agentType: 'test-scoper'` and is the actual gate this project relies on before
Finalize — confirmed via direct grep, not assumed.

## Design Decision

Per the ticket's own stated preference (Assumptions/Open Questions) for a structural guard over
agent-prompt discipline alone when feasible: implemented **both**, since `testResult.pytest_command`
(the actual command the agent reports having run) is already captured in the Test phase's schema
(`TEST_SCHEMA.properties.pytest_command`) — a deterministic post-hoc verification against it is
genuinely feasible, mirroring the existing `Architecture-Verify` phase's own
`architecture_reviewer_static.py` pattern (a `tools/gate_checks/*_static.py` module invoked via
`bash()` + `python3 -c "..."`, consumed by the orchestrator directly, not another agent's
judgment).

1. **Documentation fix** — `.claude/agents/test-scoper.md`'s Test Directory Map and Scoping Rules
   extended to cover `tools/` (flat files → `tests/tools/`, named subdirs → same-name `tests/`
   mirror), so the agent's own future judgment is correctly informed.
2. **Structural fix** — new `tools/gate_checks/test_scope_coverage_static.py`, wired into
   `implement-ticket.js`'s Test phase immediately after `testResult` returns, run regardless of
   `testResult.passed` (a reported PASS with an uncovered directory is a false PASS). Returns a
   new blocking status `TEST_SCOPE_COVERAGE_FAILED` if any changed file's required test directory
   isn't referenced as a bare, whole-directory token in the real `pytest_command`.

## Real-Incident Reproduction Nuance Found

An initial substring-based implementation (`"tests/tools/" in pytest_command`) would have
**failed to catch the real incident** — the real ticket's actual reported command DID contain the
substring `tests/tools/` (as a path prefix of the individually-named new test files it wrote),
which a naive substring check would wrongly count as "covered." Caught this while writing the
reproduction test (`test_reproduces_the_real_incident_flat_tools_change_uncovered` initially
failed against the first implementation), and fixed the check to require the **bare directory as
a standalone token** (`tests/tools/` followed by whitespace/end-of-string, not by a filename) —
this is what actually distinguishes "the whole directory ran" from "only some files inside it
were named," which is the real distinction that mattered in the incident.

## Documentation Sync

`docs/ai/ticket-lifecycle.md`'s `### Test` section documented only the `src/`→`tests/unit/`
mapping and gate; updated in the same pass to describe the `tools/` mapping and the new
`TEST_SCOPE_COVERAGE_FAILED` gate, keeping code and docs in parity per this project's general
documentation-sync discipline.
