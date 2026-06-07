# Implementation Plan — TCK-20260607-MON-CAPTURE

## Summary
Add events[] accumulation and writeMonitoring() helper to implement-ticket.js. Call writeMonitoring at all 8 exit paths. Update CLAUDE.md with hard rule and DoD condition 12.

## Steps

### Step 1 — Add summary field to all 5 schema agents' schemas in implement-ticket.js
TICKET_SCHEMA, REVIEW_SCHEMA, IMPL_SCHEMA, TEST_SCHEMA, DONE_SCHEMA — add summary: {type: 'string'} and add to required[].

### Step 2 — Add events[] and helpers after Scope agent call
const events = [], pushEvent(), writeMonitoring() — initialized right after tid/tier are set.

### Step 3 — Push scope event and add writeMonitoring at CONFLICTS_DETECTED exit
Scope event status = 'failed' if conflicts found, else 'ok'.

### Step 4 — Add writeMonitoring at EPIC_SCOPED exit

### Step 5 — Push skipped events for hotfix tier (Investigate, Plan, Review)

### Step 6 — Push events after each standard-tier agent (Investigate, Plan, Review)
Including blocked/failed status for gate failure exits.

### Step 7 — Push events for Implement, Test, Parity, Verify, Finalize
Including writeMonitoring at all gate exits: TESTS_FAILED, DOD_BLOCKED, DONE.

### Step 8 — Update CLAUDE.md
Add monitoring hard rule to Hard Rules section. Add condition 12 to Definition of Done.

## Scope Guards
Do not change agent .md files (that's TCK-MON-AGENTS). Do not change Python tools (already done in MON-SCHEMA).

## Acceptance Criteria Map
| AC | Steps |
|---|---|
| All 8 exit paths call writeMonitoring | 3,4,6,7 |
| Hotfix produces events (3 skipped + impl/test/parity/verify/finalize) | 5,7 |
| CLAUDE.md updated | 8 |
