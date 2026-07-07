---
status: active
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING
phase: open
date: 2026-07-07
tags: [simulation-quality, documentation, process-improvement, corpus]
---

# TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING

## Title
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` is cited by 9+ tickets but does not exist anywhere in `staging_artifacts/` or `stored_artifacts/`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
First flagged as a non-blocking process-gap note (OQ-3) in
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`'s plan.md, and hit again independently during
`TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`'s investigation — this is the pre-ticket epic-scoping
investigation for the whole `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` (cited by its own epic ticket,
`SEQUENCE.md`, and at least 7 of its 10 child tickets, including `corpus_tier_taxonomy.md`'s own
citation). It is referenced as the evidentiary source for specific facts (per-world entity/region
counts, populated-faction lists, the `hero_guild` faction precedent, etc.) but the file itself is not
present in `staging_artifacts/` or `stored_artifacts/` today. Every specific fact attributed to it that
has been checked so far (by two independent investigator passes, in the AGENCY and E2E-CONTENT-EXPANSION
tickets) has cross-validated cleanly against ground truth (actual `world.yaml`/`world_compile_report.json`
contents, `test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) — so this is a traceability/
citation-hygiene gap, not evidence that the cited facts are wrong.

## Scope
1. Determine what happened to the file: was it ever actually written and committed (check git log
   across the full repo history, not just the current tree, for any commit that added a file at that
   path), was it written to a different path, or was it never committed at all (e.g. left in an
   uncommitted working-tree state during the original epic-scoping session and lost)?
2. If recoverable (via git history or another location), restore it to
   `stored_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` (or the correct
   canonical location per current `stored_artifacts/` conventions).
3. If not recoverable, correct the citation in every ticket/doc that references the missing path —
   either point to the specific ground-truth files that were used to independently re-verify each
   claim (per the AGENCY and E2E-CONTENT-EXPANSION tickets' own re-derivations), or add a note that
   the original source is lost but its claims have been independently re-verified, with pointers to
   where.
4. Audit whether any other `staging_artifacts/EPIC-SCOPE-*` or similar pre-ticket investigation
   artifacts referenced by this epic have the same problem, to close this out in one pass rather than
   rediscovering it ticket-by-ticket for the remaining 2 child tickets
   (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`, `TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS`,
   `TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL`).

## Out of Scope
- Re-deriving or re-validating any specific factual claim beyond what's needed to confirm the citation
  fix is accurate — the AGENCY and E2E-CONTENT-EXPANSION tickets already did that work for the claims
  they touched
- Any code or world-content change — this is a documentation/traceability ticket only

## Acceptance Criteria
- [ ] Root cause determined: recoverable via git history, or genuinely lost
- [ ] Either the file is restored to a canonical `stored_artifacts/` location, or every citing
      ticket/doc's reference is corrected to point at valid evidence
- [ ] Remaining epic child tickets checked for the same citation gap before they close

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (the epic this investigation doc was scoped for)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — first flagged this as OQ-3 (non-blocking)
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — hit it again independently, reconstructed facts
  from ground truth instead

## Related Docs
- `tickets/todos/simq-corpus-tiers/SEQUENCE.md` — cites the same missing path
- `docs/simulation_quality/corpus_tier_taxonomy.md` — cites the same missing path

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/plan.md` — OQ-3 process-gap note
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/investigation.md` — independent
  ground-truth reconstruction of the same facts

## Related Code Areas
None — documentation/traceability only.

## Assumptions / Open Questions
- Assumes the facts attributed to the missing doc remain correct (independently cross-validated
  twice already) — this ticket is about restoring/correcting the citation trail, not re-litigating
  the facts themselves.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
