---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME
artifact_type: test_plan
tags: [ai, agent-monitoring, determinism]
---

# Test Plan — TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME

## No test plan can be produced this cycle

The Investigate phase re-verified this ticket's explicit blocking condition — whether a real
`Workflow`/`tool_runner` execution surface exists in this harness — and confirmed it **CONFIRMED
STILL TRUE as of 2026-07-11T03:12:08Z**, and again, independently, **as of 2026-07-11T07:00:16Z**
(see `investigation.md`'s "Second Independent Confirmation" section for the second pass's evidence:
a fresh grep of `.claude/skills/*/SKILL.md`, byte-identical to the first pass's 5-line finding
across `implement-ticket`, `implement-epic` (x2), `create-tickets`, and `simq-audit`; plus a fresh
`ToolSearch` probe this pass, both a broad semantic query — which returned only `EnterWorktree`/
`Monitor`, neither relevant — and a direct exact-name lookup `"select:Workflow"`, which returned "No
matching deferred tools found"). This is the second independent confirmation within this session,
with zero drift in the answer between the two checks.

This ticket's only currently-actionable acceptance criterion (AC1) is the confirmation check
itself, not a code change. AC2 ("`.claude/workflows/implement-ticket.js` ported to real executable
code") is explicitly provisional and contingent on AC1 flipping true — it has not. The ticket's Out
of Scope section explicitly forbids "any speculative implementation against a hypothetical
execution surface before one is confirmed to exist."

There is therefore no implementation to test. Per this investigator's own instructions: no
hypothetical tests are invented here for unbuildable code. A real test_plan for AC2 (regression
surface for the ported `.js` files, new tests for runtime-executed phase sequencing/gate branching,
scoped pytest commands) can only be written once a genuine execution surface is confirmed to exist
and a `plan.md` exists describing what will actually be ported and how. Writing speculative test
cases now would itself be exactly the kind of scope-creep the ticket's Out of Scope section warns
against, and would go stale the moment a real surface's actual API shape became known.

## Regression Surface

Not applicable — no source changes are being made. For completeness, the tests that currently
cover the *narration* pattern (and that any eventual porting work would need to keep passing, or
deliberately supersede, once AC1 is unblocked) are noted here for the next Investigate pass to
re-check, not as something to run now:

- `tests/tools/test_workflow_meta_conformance.py` — covers `tools/gate_checks/workflow_meta_conformance.py`'s
  `meta.phases` vs. `events.jsonl` cross-reference (sibling ticket's mitigation; must keep passing
  if `.claude/workflows/*.js` source text is ever touched, since it does regex/AST-lite parsing of
  that source).
- `tests/tools/test_step0_ts_orchestrator.py` and `tests/tools/test_current_run_sidecar_orchestrator.py` —
  static, raw-source-text-parsing tests against `.claude/workflows/implement-ticket.js`,
  `implement-epic.js`, and `create-tickets.js` from the sub-agent bookkeeping-determinism epic; any
  future porting work touching those `.js` files' text would need to keep these passing or
  explicitly supersede them with equivalent coverage against the ported form.
- `tests/tools/test_tag_skill_mapping_check.py` — the established `Path.read_text()` pattern the
  two files above reuse; relevant precedent for whatever static-parsing tests a real port would
  eventually replace.

## New Tests Required

None. No acceptance criterion in this ticket that is actionable today requires a new test — AC1 is
a confirmation step (satisfied by this Investigate pass's findings, not by code), and AC2 is not
actionable.

## Scoped Pytest Commands

None to run for this ticket's own change, because there is no code change. If a future session
needs to re-verify that the currently-shipped narration-support tooling still passes (as a sanity
check before re-confirming the blocking condition, not as this ticket's regression surface), the
scoped command would be:

```
pytest tests/tools/test_workflow_meta_conformance.py tests/tools/test_step0_ts_orchestrator.py tests/tools/test_current_run_sidecar_orchestrator.py -q
```

This is offered only as a reference command for adjacent tooling sanity, not as verification of any
change made under this ticket.

## Anti-Drift Test Guards

- Any future Plan phase for this ticket must not treat the absence of a test plan here as a green
  light to skip TDD once AC1 flips true — the moment a real execution surface is confirmed, a fresh
  Investigate pass (and a real test_plan.md, replacing this file) is required before Plan/Implement,
  per this ticket's own Request Summary instruction.
- If a future session is tempted to write "placeholder" or "future-proofing" tests against a
  hypothetical `Workflow` tool API today, that is itself an anti-drift violation — the ticket's Out
  of Scope section forbids speculative implementation, and speculative tests are a form of
  speculative implementation (they encode assumptions about an API shape nobody has confirmed).
- If `workflow_meta_conformance.py` or the sidecar/timestamp orchestrator tests
  (`test_step0_ts_orchestrator.py`, `test_current_run_sidecar_orchestrator.py`) start failing on
  `main` independent of this ticket, that is a signal worth flagging to
  `TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC` (the parent), not silently absorbed into this
  blocked child's scope.
