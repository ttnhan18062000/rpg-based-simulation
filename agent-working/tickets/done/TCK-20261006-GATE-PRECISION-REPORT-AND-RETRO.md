---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO
phase: done
date: 2026-10-06
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO

## Title
A report-only gate precision reading, and a Gates section in the weekly retro

## Status
DONE

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
- `agent-working/stored_artifacts/TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO/` (plan, investigation, test_plan)

## Related Code Areas
- `tools/agent-monitoring/generate_retro.py`, `retro_provenance.py`, `gate_ledger.py`

## Assumptions / Open Questions
- n < 5 is the cut-off for "too few adjudicated". It is a starting value; change it at a retro if needed.

## Implementation Notes
Drafted by `agent-working-design` on 2026-10-06.

`gate_ledger.py` gained `report(rows, week)` (one reading per `gate_id`: verdicts by `execution_mode`, blocking, outcomes recorded and derived counted separately, unresolved blocks, adjudicated count, adjudication mix), `render_section(rows, week, total_rows)` and a `report [--week]` subcommand. `generate_retro.py` gained `_gates_section()` and a `gates` argument to `generate()`; the section follows the session-layer section and is built the same fail-soft way (a read failure omits it, never fails the retro).

Decisions:
- A false-block share is printed only from 5 adjudicated verdicts (`MIN_ADJUDICATED`); below that the cell reads `too few adjudicated (n=2, false blocks 0)`, and with none it reads `not adjudicated`. The cut-off is a starting value.
- An `unknown` ruling is not a judgement and does not count as adjudicated.
- The week of a verdict is its own `ts`; outcomes and adjudications count whenever they were recorded.
- Dark instrument (no verdict row in any week) prints "Instrument not running"; rows only outside the period print "No gate verdicts this period".
- A `--days` or `--all` retro reads every week for the Gates section.
- The direction doc row is `shipped (code)`; the pending-decision line was struck earlier in this batch; an idea row for CI and code-health gate ingest was added.

## Test Summary
`tests/tools/test_gate_ledger.py` (24 pass in total, 10 of them new here): the three-gate fixture gives `2/6 (33%)` for the gate with 6 adjudicated rows, `too few adjudicated` for the gate with 2 and `not adjudicated` for the gate with none; mode, outcome and unresolved counts; `unknown` not counted; week filter; the `report` CLI; dark and zero wording; the retro with no gate shards and with the fixture; regenerating with hand-written Notes keeps them without `--force` and the Gates section lands before them; a failing ledger read yields None. `tests/tools/test_generate_retro.py` and `test_retro_provenance.py` stay green (212 pass with the new file).

## Files Changed
- `tools/agent-monitoring/gate_ledger.py`, `tools/agent-monitoring/generate_retro.py`
- `tests/tools/test_gate_ledger.py`
- `docs/plans/agent_infrastructure/agent_working_direction.md`

## Completion Summary
Closed 2026-10-06. All four acceptance criteria met: the fixture ledger reads 2/6, "too few adjudicated" and "not adjudicated" (AC1); the retro renders the Gates section with the dark wording on a week with no `gate_verdicts` shards and the per-gate table with the fixture (AC2); regeneration preserves Notes without `--force` and the new section sits before them (AC3); the direction doc row is `shipped (code)` and scoped tests are green (AC4). The real W41 retro was not regenerated: it has no gate rows yet, and the epic's AC2 is read from the first full ISO week after this merges.
