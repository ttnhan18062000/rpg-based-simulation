# Implementation Sequence — ai-first-hardening-h0-governance-guardrail

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

Scope: Horizon-0 items from the Governance & Capability Policy and Guardrail Enforcement
epics (`docs/plans/agent_infrastructure/ai_first_hardening_epics/`).

## Order

1. TCK-20260904-AGENT-TOOL-USAGE-BASELINE  (no deps in this batch)
2. TCK-20260904-CAPABILITY-ENVELOPE-BASELINE  (no deps in this batch)
3. TCK-20260904-DOC-COVERAGE-REVERSE-CHECK  (no deps in this batch)
4. TCK-20260904-TEST-SCOPER-HANG-GUARD  (no deps in this batch)
5. TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE  (depends on: TCK-20260904-AGENT-TOOL-USAGE-BASELINE)

## Why This Order Matters

Running alphabetically would attempt TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE before its
dependency (TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table) is in place. Re-run
`/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.

**TCK-20260904-BASH-SECRET-SCAN-HOOK is NOT in this folder** (originally the Governance
epic's M4). It lives at `tickets/inprogress/TCK-20260904-BASH-SECRET-SCAN-HOOK.md`
(`## Status: BLOCKED`), following this repo's convention for a scope-only ticket that is
blocked before any implementation begins (matching `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`,
itself a never-implemented, scope-only `BLOCKED` epic in the same directory).
`implement-epic.js`'s folder-mode has no per-ticket `BLOCKED`-skip logic — see
`TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS` for that tracked gap — so a `BLOCKED` ticket must
stay out of any folder this workflow would run against, rather than living in this sequence.
Once the knowledge-gateway re-ratification and `scan_for_secrets()` extraction land, move it
back into a real batch (this one or a fresh one) and flip its `## Status` to `OPEN` first.
