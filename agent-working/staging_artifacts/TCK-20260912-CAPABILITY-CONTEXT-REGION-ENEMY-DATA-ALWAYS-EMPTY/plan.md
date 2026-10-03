# Plan — TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY

## Steps taken
1. Re-verified the empty-fields claim and `travel_regions`'s own zero-construction-site finding.
2. Searched for a real, live belief source (never world truth) before writing any code.
3. Found and traced both real candidates to their current blockers (see investigation.md).
4. Declined to wire either — would produce unreachable code, the exact pattern this ticket exists
   to close.
5. Ticket stays `BLOCKED`, both chains named explicitly, `travel_regions` finding kept visible.

## Scope guard
No implementation. No documentation of the fields as "speculative/remove" either — that would
misdescribe a genuinely blocked-not-abandoned disposition.

## Acceptance-criteria map
See the ticket body's own Acceptance Criteria — marked directly with inline notes on why the
unmet ones stay unmet pending the two named blocking chains.
