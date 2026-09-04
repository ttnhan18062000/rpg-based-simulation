# Implementation Sequence — ai-first-hardening-governance-guardrail-batch

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260904-AGENT-TOOL-USAGE-BASELINE  (no deps in this batch)
2. TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION  (no deps in this batch)
3. TCK-20260904-CAPABILITY-ENVELOPE-BASELINE  (no deps in this batch)
4. TCK-20260904-COST-PROXY-EPIC-TICKETS  (no deps in this batch)
5. TCK-20260904-DOC-COVERAGE-REVERSE-CHECK  (no deps in this batch)
6. TCK-20260904-OWNERSHIP-LIFECYCLE-DOC  (no deps in this batch)
7. TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST  (no deps in this batch)
8. TCK-20260904-SHADOW-REVIEWER-LOGGING  (no deps in this batch)
9. TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE  (no deps in this batch)
10. TCK-20260904-TEST-SCOPER-HANG-GUARD  (no deps in this batch)
11. TCK-20260904-WORKING-LOG-CSV-PARSER  (no deps in this batch)
12. TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE  (depends on: TCK-20260904-AGENT-TOOL-USAGE-BASELINE)

## Why This Order Matters

Running alphabetically would attempt TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE before its
dependency (TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table) is in place. Re-run
`/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.

**TCK-20260904-BASH-SECRET-SCAN-HOOK is NOT in this folder.** It was moved to
`tickets/inprogress/TCK-20260904-BASH-SECRET-SCAN-HOOK.md` (frontmatter `phase: blocked`,
`## Status: BLOCKED` in the body), matching this repo's established convention for blocked work
(see `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`, `TCK-20260730-CODEX-CONTROLLED-PILOT`).
This was deliberate, not an oversight: `implement-epic.js`'s folder-mode has no mechanism to skip
an individual `BLOCKED` ticket — its only skip signal is whether the ticket ID already exists in
`tickets/done/` (see `discover_candidate_epics()`/Step 2's `ls tickets/done/` check). Leaving a
`BLOCKED` ticket inside this todos folder would have caused `/implement-epic` to attempt it in
normal sequence and fail or produce unusable work. A real ticket
(`TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS`) has been filed for this workflow gap — closing it
would let a future `BLOCKED` ticket safely stay in its batch folder instead of requiring this
manual move. Once the knowledge-gateway re-ratification and `scan_for_secrets()` extraction land,
move `TCK-20260904-BASH-SECRET-SCAN-HOOK.md` back to `tickets/todos/` (or a fresh batch) and flip
its `## Status` to `OPEN` before running `/implement-epic` or `/implement-ticket` against it.
