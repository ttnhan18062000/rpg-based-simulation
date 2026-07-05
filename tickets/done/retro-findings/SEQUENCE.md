# Retro Findings — Implementation Sequence

Three tickets filed 2026-07-05, all from the same investigation: the first-ever real run of
`agent-monitoring/retro/` tooling (`make agent-monitoring-retro`, `validate.py`) surfaced several
warnings, and digging into root causes (rather than treating each warning at face value) found
three distinct, independent bugs — not one problem with three symptoms.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP | Smallest, most mechanical fix (hotfix tier) — do first as a quick win, and because it closes the validator's own blind spot before the next retro run, so future retros get a more complete picture from the start |
| 2 | TCK-20260705-RETRO-METRIC-ACCURACY | Independent of ticket 1, but shares the "detect legacy vs. current schema" concern raised in its own Open Questions — worth deciding a shared predicate before or alongside ticket 1's fix, even though neither technically blocks the other |
| 3 | TCK-20260705-MONITORING-RUNID-JOIN | Standard tier, requires the most investigation (confirming whether the timestamp-race pattern is live in current code or purely historical debris) before any fix can be scoped — do last |

## Dependency Notes

- No hard blocking dependency between any of these three — they touch different files
  (`validate.py`, `generate_retro.py`, `record_run.py`/`record_events.py`/the workflow JS files
  respectively) and can be done in any order or in parallel.
- Tickets 1 and 2 both need a definition of "is this record legacy-schema or current-schema" —
  each ticket's own text flags this and suggests a shared helper might be worth factoring out
  rather than reimplementing the check twice. This is a design nicety to consider during
  Plan, not a hard requirement — the ticket that lands second can simply reuse whatever the
  first one establishes, if it's in a natural, shared location.
- Ticket 3 is the only one where the fix itself is genuinely undetermined until Investigate
  confirms root cause — treat its Acceptance Criteria as "understand and appropriately harden,"
  not "apply a specific pre-decided change."
