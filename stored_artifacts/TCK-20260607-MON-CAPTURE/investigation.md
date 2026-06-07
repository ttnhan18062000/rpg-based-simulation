# Investigation — TCK-20260607-MON-CAPTURE

## Current Behavior
`implement-ticket.js` had no monitoring integration. Each workflow run was invisible — no machine-readable record of which agents ran, what they returned, or how they exited.

## Mechanics / Engine Constraints
None — tooling only.

## Parity Ledger Overlap
No parity entries affected.

## Prior Work
TCK-20260607-MON-SCHEMA (dependency): created the JSONL files, record_run.py, record_events.py.

## Risks and Open Questions
- `Date.now()` and `new Date()` are unavailable in workflow scripts (they break replay). Solution: monitoring-write agent gets the timestamp via `date -u +%Y-%m-%dT%H:%M:%SZ` bash command.
- Monitoring agent failure must not fail the workflow. Solution: agent() returns null on terminal error; check null and log WARNING.
- All 8 exit paths in implement-ticket.js must call writeMonitoring. Solution: centralized `writeMonitoring()` async helper called at each return.

## Anti-Drift Hazards
- New exit paths added to implement-ticket.js in the future must also call writeMonitoring.
- The events array must be initialized BEFORE the conflict check, so even CONFLICTS_DETECTED exits have a scope event recorded.
