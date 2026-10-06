---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO
phase: open
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO

## Title
A report-only gate precision reading, and a Gates section in the weekly retro

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER`. Turn the ledger into a weekly reading per gate without
claiming more than the adjudicated rows support (`agent_evaluation_foundation_experiment.md:92`).

## Scope
- **`gate_ledger.py report [--week YYYY-Www]`**, per `gate_id`:
  - verdict counts, broken down by `execution_mode`;
  - blocking count;
  - outcome mix, with derived and recorded outcomes counted separately;
  - unresolved blocks;
  - adjudicated count;
  - false-block share and false-pass count, over adjudicated rows only. With n < 5 adjudicated it prints the
    counts and the label "too few adjudicated", never a percentage.
- **A "Gates" section in `generate_retro.py`.** It follows the existing pattern for sections with no data: a dark
  instrument says "Instrument not running", and zero rows says "no gate verdicts this week".
- **Direction doc.** The row moves to `shipped (code)`. The pending decision is struck through. An idea row is
  added for "CI and code-health gate ingest".

## Out of Scope
- Alerts, thresholds, or any gate behaviour driven by the reading. It is report-only, per the direction doc.

## Acceptance Criteria
1. The fixture ledger contains:
   - 3 gates;
   - one gate with 6 adjudicated rows (2 false blocks);
   - one gate with 2 adjudicated rows;
   - one gate with none.

   The report gives 2/6 for the first, "too few adjudicated" for the second, and "not adjudicated" for the third.
2. The retro on a week with no `gate_verdicts` shards renders the Gates section with the dark/zero wording. With
   the fixture, it renders the per-gate table.
3. `--force` is not needed to regenerate a retro that has Notes. The existing preservation still holds; add a test
   on the new section.
4. The direction doc is updated. Scoped retro and gate_ledger tests are green.

## Related Tickets
- `TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION` (depends on it)
- `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER` (parent; AC2 of the parent is read from this report)

## Related Docs
- `docs/plans/agent_infrastructure/agent_working_direction.md`
- `docs/plans/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`, `retro_provenance.py`, `gate_ledger.py`

## Assumptions / Open Questions
- n < 5 is the cut-off for "too few adjudicated". It is a starting value; change it at a retro if needed.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

## Test Summary

## Files Changed

## Completion Summary
