---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES
phase: open
date: 2026-07-20
tags: [documentation, claude-md]
---

# TCK-20260720-CLAUDE-MD-CONSISTENCY-FIXES

## Title
Fix CLAUDE.md self-consistency errors found by the 2026-07-20 agent-orchestration audit

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
The same audit that produced TCK-20260720-MONITORING-PIPELINE-BUGFIXES found several places
where `CLAUDE.md` — the one file every agent (including Claude Code itself) reads as ground
truth — is factually wrong about its own project, either about numeric facts (phase counts) or
about file paths that no longer exist. Fixing all of these together per user direction (minimize
distinct tickets, hotfix tier for small, self-evident, mechanical corrections).

## Scope
- Engine Contracts table: `authoritative_pipeline.md` was described as "17-phase" — the actual
  doc is titled "The 32 Phases of Refinement" and says so explicitly. Corrected to 32-phase.
- Tier Routing table: `standard` tier was described as "Full 9-phase pipeline" — the actual
  `implement-ticket.js` phase list has 10 standing phases plus 1 conditional (Security-Review),
  confirmed directly against the workflow file's own `meta.phases` array. Corrected to
  "Full 10-phase pipeline (+1 conditional: Security-Review)".
- Definition of Done list: added a bullet for frontmatter validity, matching the real
  script-checked `frontmatter_valid` condition in `done-checker`'s 6-check static pre-check — the
  prior 12-bullet list had no corresponding entry at all.
- 3 stale doc-path references in "Other Active Doc Areas": `docs/architecture/`'s description
  named nonexistent `adr-004`/`adr-005` files (real files: `simulation_watchdog.md`,
  `performance_optimization.md`); `docs/combat/`'s description named nonexistent `m1`–`m7`
  milestone files (real files: `combat_movement_overhaul_spec.md`, `observability_rulebook.md`,
  `rollout_hardening_rulebook.md`); `docs/testing/v2_test_taxonomy.md` was referenced but the
  `v2_` prefix was dropped repo-wide by a prior ticket and this one reference was missed —
  corrected to `docs/testing/test_taxonomy.md`. All corrected paths verified to exist on disk.

## Out of Scope
- The `docs/ai/*.md` and `docs/agent-monitoring/schema.md` accuracy findings from the same
  audit (wrong subagent counts, false claims, stale phase/workflow enums, static pre-check count
  drift in those files) — tracked separately as this batch's own ticket, since those are a
  different set of files with a different kind of drift (docs *about* the system, not the
  system's own master instruction file).
- Any change to the actual pipeline phase count, DoD enforcement, or doc structure — this ticket
  only corrects CLAUDE.md's prose description to match what already exists; no behavior changed.

## Acceptance Criteria
- [x] CLAUDE.md's Engine Contracts table describes `authoritative_pipeline.md` as 32-phase,
      matching that doc's own stated title and text.
- [x] CLAUDE.md's Tier Routing table describes `standard` tier as 10-phase +1 conditional,
      matching `implement-ticket.js`'s actual `meta.phases` array (verified directly).
- [x] CLAUDE.md's Definition of Done list includes a bullet for frontmatter validity.
- [x] All 3 corrected doc-path references (`docs/architecture/`, `docs/combat/`,
      `docs/testing/`) point at files confirmed to exist on disk.
- [x] No test in the repo asserts the old stale text (confirmed via repo-wide grep; the only
      hits were unrelated synthetic test-fixture path strings in
      `tests/tools/test_add_frontmatter_live.py`, testing a path-based heuristic function, not
      CLAUDE.md's own content).

## Related Tickets
- TCK-20260720-MONITORING-PIPELINE-BUGFIXES (same audit, sibling hotfix batch)
- TCK-20260617-DOCS-DEVERSION (originally dropped the `v2_` prefix repo-wide; this ticket closes
  the one reference it missed)
- TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER (added the `Architecture-Verify` phase that made
  the "9-phase" count stale)

## Related Docs
- CLAUDE.md (this ticket's only changed file)
- docs/engine/authoritative_pipeline.md (verified: "The 32 Phases of Refinement")
- docs/architecture/simulation_watchdog.md, docs/architecture/performance_optimization.md
- docs/combat/combat_movement_overhaul_spec.md, docs/combat/observability_rulebook.md,
  docs/combat/rollout_hardening_rulebook.md
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
None (hotfix — self-evident intent captured in this ticket).

## Related Code Areas
- CLAUDE.md

## Assumptions / Open Questions
- The static pre-check count drift (5→6 conditions) and Finalize self-check drift (3→4 checks)
  found by the same audit live in `docs/ai/workflows.md`, `docs/ai/agents.md`,
  `docs/ai/ticket-lifecycle.md` — not in CLAUDE.md itself — so that fix is deliberately routed to
  the sibling `docs/ai/*.md` + `schema.md` accuracy ticket rather than duplicated here.

## Implementation Notes
All 5 corrections are mechanical — verified against direct evidence (reading the target doc's own
text, reading the workflow file's real phase array, confirming file existence on disk) with no
design ambiguity. No behavior changed; CLAUDE.md's prose now matches what already exists.

## Test Summary
No code tests apply (pure documentation correction). Verified via direct evidence: read
`docs/engine/authoritative_pipeline.md` to confirm "32 Phases"; read `implement-ticket.js`'s
`meta.phases` array to confirm 10+1 conditional; ran `ls` against all 7 corrected/verified doc
paths to confirm they exist; grepped the full `tests/` tree for the old stale strings to confirm
no test depends on them.

## Files Changed
- CLAUDE.md

## Completion Summary
Corrected 5 self-consistency errors in CLAUDE.md found by the 2026-07-20 agent-orchestration
audit: 2 wrong phase counts (17→32, 9→10+1 conditional), 1 missing Definition-of-Done bullet
(frontmatter validity), and 3 stale/broken doc-path references. All corrections verified against
direct evidence before applying; no test depends on the old text.
