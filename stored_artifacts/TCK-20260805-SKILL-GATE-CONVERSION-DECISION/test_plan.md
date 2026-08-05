---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-GATE-CONVERSION-DECISION
artifact_type: test_plan
tags: [skills, workflows]
---

# Test Plan — TCK-20260805-SKILL-GATE-CONVERSION-DECISION

## Normal Flow
- A `performance`-tagged ticket's Test-phase prompt includes the `tests/unit/perf/`/`tests/perf/`
  reminder text, citing the real regression-gate policy doc.
- `test-scoper.md`'s own Scoping Rules section documents the identical rule.

## Edge Cases
- A ticket WITHOUT the `performance` tag gets the empty-string branch of the conditional — zero
  added prompt text (verified structurally: the conditional expression evaluates to `''` when the
  tag is absent, mirroring `Security-Review`'s own "zero added latency for untagged tickets"
  property, though this is a prompt-content change rather than a phase, so there is no
  execution-latency dimension to measure — only prompt-length/content).

## Failure Modes
N/A — this is a prompt-content change to an existing gate (Test/`TESTS_FAILED`), not new
executable logic with its own failure modes. The only thing to verify is that the *wiring* is
correct (tag check present, reminder present, no new blocking status introduced) — covered by
`tests/tools/test_perf_tag_test_scoper_wiring.py`'s static source-text assertions.

## Regression-Prone Paths
- Confirm no new `return { status: ... }` block was introduced keyed on the `performance` tag
  (would silently turn this into an undocumented second gate).
- Confirm existing Test-phase / Document-Update / doc-staleness-gate wiring tests
  (`test_document_update_phase_wiring.py`, `test_doc_staleness_gate_wiring.py`,
  `test_shadow_packet_call_site.py`, `test_step0_ts_orchestrator.py`,
  `test_workflow_meta_conformance.py`) still pass unchanged after this edit — confirms the new
  conditional block was inserted without disturbing surrounding phase structure.
