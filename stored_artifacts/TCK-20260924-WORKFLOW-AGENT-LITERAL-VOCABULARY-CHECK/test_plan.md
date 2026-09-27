---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK
artifact_type: test_plan
tags: [agent-monitoring, workflows, data-quality]
---

# Test Plan: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK

New file: `tests/tools/test_workflow_vocabulary_check.py`, scoped run via
`pytest tests/tools/test_workflow_vocabulary_check.py -v` during Implement, folded into the
batch's full `pytest tests/tools/ -m "not slow"` regression at Verify.

## Normal flow
- A workflow file fully keyed with every literal registered contributes only `PASS` rows.
- The real, post-registration `.claude/workflows/` + real `vocabulary.py` -> zero FAIL rows
  (AC3, the ticket's own target end state).

## Edge cases
- A file with zero literals of either family (e.g. `simq-audit.js`, confirmed in investigation to
  have neither `writeSidecar` nor `agent:` call sites) is still checked for the keyed-file
  condition (AC1) even though it contributes no per-literal findings either way.
- A literal appearing in both a real call site and a comment on the same line is not a
  realistic case in this corpus (investigation confirmed 0 such lines) but the comment-stripping
  function is still unit-tested against a synthetic same-line case defensively.
- `writeSidecar` argument positions 2 and 3 read independently even when the two literal strings
  are easily confusable (e.g. differing only by case) — AC5's fixture uses visibly distinguishable
  strings specifically so a position swap fails loudly rather than passing by coincidence.

## Failure modes / regression-prone paths
- **The exact defect this ticket exists to prevent**: a check that silently skips an unkeyed
  workflow file (by delegating to `infer_workflow`'s "unknown -> None -> skip" contract) — AC1's
  fixture is built specifically to catch a future refactor that reintroduces this shortcut.
- **The exact defect that produced the wrong "1" finding during original scoping**: reading only
  one `writeSidecar` argument position — AC5's fixture pins both positions independently.
- **Registry regression**: a future edit accidentally removing or renaming an existing
  `WORKFLOW_AGENTS`/`WORKFLOW_PHASES` entry — guarded by the snapshot-subset assertion (AC9), plus
  a human diff read at Verify (a test alone cannot catch a same-shape rename with full confidence).
- **Comment false positives**: the corpus's own near-1:1 comment-to-real-callsite ratio for
  `writeSidecar` (21:22, per the ticket's own measurement) makes this the single most likely
  false-positive source — AC4 is a dedicated fixture, not inferred from the zero-findings AC3 test
  alone (a bug that produces exactly as many false positives as false negatives could pass AC3
  while still failing AC4).

## Existing tests checked for overlap
- `tests/tools/test_workflow_meta_conformance.py` — different question (run-keyed phase-vs-event
  conformance), no overlap; not modified.
- No existing test references `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` directly by literal snapshot
  (confirmed via grep during investigation), so the AC9 snapshot assertion in the new test file is
  not duplicating an existing guard.
