---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-PARITY-UPDATER
phase: open
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-PARITY-UPDATER

## Title
Add a deterministic diff-cross-reference check backing parity-updater's ledger updates

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Second of 4 gate-determinism tickets (see `tickets/todos/gate-determinism-followups/SEQUENCE.md` for
shared design decisions and full context). Per `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
table: "Git-diff cross-reference: every `src/` file touched in the commit that maps to a
`docs/parity_ledger/*.yaml` subsystem must have a corresponding entry touched in the same commit." What
stays LLM-judged: whether the chosen `status` (`verified`/`divergent`) is the correct one.

## Scope
- Build a `src/` path → parity-ledger-subsystem mapping. Investigate whether one already exists
  implicitly (check `parity-updater.md`'s own prompt/instructions and `implement-ticket.js`'s Parity
  phase for how it currently decides which of the 8 canonical YAML files to touch) or must be derived
  fresh — likely from `docs/parity_ledger/*.yaml`'s own entries' `v2_evidence` path citations (reusing
  `TCK-20260705-WORKFLOW-PARITY-SKIP`'s `tools/parity_ledger_scan.py` module/pattern where sensible,
  without assuming its exact function signatures fit this different purpose without adaptation).
- `tools/gate_checks/parity_updater_static.py`: given `implementation.files_changed` (post-Implement,
  authoritative) and the set of parity-ledger files actually touched/modified in the same Implement
  pass, flag any `src/` file that maps to a subsystem YAML but whose corresponding YAML file was NOT
  touched — a static FAIL signal parity-updater's own LLM judgment must then explain or override with a
  citation.
- Add a `verified_by` field to whatever schema captures parity-updater's return (there is currently no
  formal schema for this call in `implement-ticket.js` — the Parity phase call uses only `{ label,
  agentType }` with no `schema:` property; Investigate should confirm this and decide whether adding a
  minimal schema is now warranted to carry `verified_by`, or whether the static check's result surfaces
  purely via `log(...)`/prose instead).
- Coordinate explicitly with the already-shipped `TCK-20260705-WORKFLOW-PARITY-SKIP` ticket's skip logic:
  this new static check only applies when the Parity phase's full `agent(...)` call actually runs (i.e.,
  it is not skip-eligible) — confirm during Investigate that the skip condition and this new check
  cannot conflict or double-count.
- At least one coverage-honesty test (a fixture `src/` change with a matching but untouched ledger
  subsystem must be flagged; a fixture where the ledger was correctly touched must not be).

## Out of Scope
- The other 3 gates' static verifiers — see SEQUENCE.md.
- Re-deciding `status: verified` vs `status: divergent` — remains LLM-judged.
- Modifying `TCK-20260705-WORKFLOW-PARITY-SKIP`'s skip condition itself.
- Token/cost telemetry.

## Acceptance Criteria
- [ ] `tools/gate_checks/parity_updater_static.py` exists with a documented `src/` → subsystem mapping
      derivation and a diff-cross-reference function.
- [ ] The Parity phase's prompt (when not skip-eligible) instructs parity-updater to run this check
      first and address any flagged file.
- [ ] Confirmed no conflict with the Parity-skip logic from `TCK-20260705-WORKFLOW-PARITY-SKIP`.
- [ ] At least one coverage-honesty test per check function.
- [ ] `docs/ai/agents.md`'s `parity-updater` section and the other 3 shared docs updated.

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER (sibling, first in sequence)
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR (sibling, should reuse this ticket's src/-to-subsystem mapping
  if built)
- TCK-20260705-WORKFLOW-PARITY-SKIP (the skip logic this check must coexist with)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- tickets/todos/gate-determinism-followups/SEQUENCE.md
- docs/ai/agents.md, docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/parity-updater.md
- .claude/workflows/implement-ticket.js (Parity phase)
- tools/parity_ledger_scan.py (reference — reuse pattern, do not assume signature fit without checking)
- docs/parity_ledger/*.yaml (read-only reference)

## Assumptions / Open Questions
- Whether a `src/`-to-subsystem mapping already exists implicitly somewhere, or must be derived fresh —
  left for Investigate.
- Whether the Parity phase call needs a formal `schema:` added for the first time to carry
  `verified_by` — left for Investigate/Plan.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
