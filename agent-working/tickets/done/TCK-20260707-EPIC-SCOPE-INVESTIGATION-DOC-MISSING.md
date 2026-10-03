---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING
phase: done
date: 2026-07-07
tags: [simulation-quality, documentation, process-improvement, corpus]
---

# TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING

## Title
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` is cited by 9+ tickets but does not exist anywhere in `staging_artifacts/` or `stored_artifacts/`

## Status
DONE

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
- [x] Root cause determined: recoverable via git history, or genuinely lost
- [x] Either the file is restored to a canonical `stored_artifacts/` location, or every citing
      ticket/doc's reference is corrected to point at valid evidence
- [x] Remaining epic child tickets checked for the same citation gap before they close

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (the epic this investigation doc was scoped for)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — first flagged this as OQ-3 (non-blocking)
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — hit it again independently, reconstructed facts
  from ground truth instead
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/` as a documentation/traceability-only child with zero
  code/content overlap with the rest of the epic — can run fully independently and in parallel per
  that folder's `SEQUENCE.md`. Note: this new epic's own investigation doc
  (`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md`) was written and preserved
  precisely to avoid repeating the citation-rot pattern this ticket exists to fix

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

**Root cause (Scope item 1):** Confirmed via `git log --all --full-history --diff-filter=A` (and a
`-S` pickaxe search) that no commit, on any branch, ever added a file at either
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` or
`stored_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`. `.gitignore:242` shows
`staging_artifacts/` is entirely gitignored by repo policy ("In-progress staging artifacts... never
commit"), so this was never a candidate for git recovery. `tickets/done/TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC.md`'s
own Implementation Notes record that the folder was renamed from
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` to
`staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/` once the epic ticket ID existed — but that
renamed path is *also* absent from both `staging_artifacts/` and `stored_artifacts/` today. Cause:
`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` is tier=`epic` ("Scope only — tracks child tickets; no direct
implementation" per the Tier Routing table), so it never ran a Finalize phase of its own — the step
that migrates `staging_artifacts/{ticket_id}/` to `stored_artifacts/{ticket_id}/` on ticket
completion only fires for tickets that go through Implement/Finalize, not scope-only epics. The
local working-tree copy was subsequently lost (gitignored, so no safety net) before anyone ran that
migration by hand. Net: written, renamed once, never committed (by design), never migrated to
`stored_artifacts/` (process gap specific to epic-tier tickets), and now genuinely gone — not a
misplacement, a real loss.

**Scope item 2 (restore):** Not possible — confirmed unrecoverable by the git-history check above;
neither candidate path exists anywhere in the working tree either.

**Scope item 3 (correct citations):** Found 24 distinct files citing either the original
`EPIC-SCOPE-full-feature-world-coverage` path or its `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` rename
(both equally dead): 11 `tickets/done/` files (10 SimQ-corpus-tiers child tickets +
`simq-corpus-tiers/SEQUENCE.md`), 11 `stored_artifacts/*/investigation.md` or `plan.md` files, and 2
active docs (`docs/simulation_quality/corpus_tier_taxonomy.md`,
`docs/simulation_quality/eval_matrix_results.md`). Rather than re-deriving each individual factual
claim per file (explicitly out of scope — the AGENCY and E2E-CONTENT-EXPANSION tickets already did
that re-derivation work), added one standardized "Citation Correction" note per file: explains the
path is dead, why (gitignored + un-migrated epic-tier staging artifact), and points to the two
tickets that already independently cross-validated the underlying facts against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`), plus this ticket for the full
root-cause writeup. For the two active docs, the note was placed inline at/near the citation instead
of appended, since those are living reference docs read in context rather than closed historical
records.

**Scope item 4 (audit remaining epic scope):** All 10 `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` child
tickets are already in `tickets/done/simq-corpus-tiers/` (epic closed per
`git log --oneline -S "EPIC-SCOPE-full-feature-world-coverage"`, which shows all 10 child-ticket
commits plus the guardrail ticket's "close epic" commit) — so the "remaining 2 child tickets" language
in this ticket's own Scope section is stale; all were already covered in the item-3 sweep. Searched
repo-wide for other `staging_artifacts/<non-TCK-prefixed>` citation patterns
(`grep -rohE "staging_artifacts/[A-Za-z0-9_.-]+"`) to check for siblings of this same problem: the
only other non-ticket-ID-prefixed hit was `staging_artifacts/phase_2/`, which is a stale-folder
deletion checklist item in `stored_artifacts/TCK-20260410-PHASE-2-ALIGNMENT/plan.md`, not a
broken evidentiary citation — no action needed. No other dangling pre-ticket epic-scoping docs
found.

Did not touch `tickets/todos/simq-deep-coverage/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md`
(the identical parked copy of this ticket) or run the ticket-close/working-log/folder-move steps —
those are Finalize-phase responsibilities outside this Implement pass.

## Test Summary
Documentation/traceability-only change; no code paths affected, so no automated tests apply. Verified
by: (1) `git log --all --full-history --diff-filter=A` and `git log --all -S` pickaxe search across
all branches confirming zero commits ever added either candidate path; (2) `git status --short`
scoped to `tickets/`, `docs/`, `stored_artifacts/` confirming the edited file set matches exactly the
24 files identified as citing the dead path (no unrelated files touched); (3) grep-verified each of
the 24 edited files now contains exactly one "Citation Correction" note, correctly placed relative to
each file's existing section structure (before `## Test Summary` for ticket files, appended at file
end for `stored_artifacts/`/`SEQUENCE.md`, inline near the citation for the two active docs).

## Files Changed
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/simulation_quality/eval_matrix_results.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO/investigation.md`
- `stored_artifacts/TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/plan.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-SCALE-METRIC/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-SCALE-METRIC/plan.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/investigation.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION/plan.md`
- `stored_artifacts/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS/investigation.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-SCALE-METRIC.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS.md`
- `tickets/done/TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC.md`
- `tickets/done/simq-corpus-tiers/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC.md`
- `tickets/done/simq-corpus-tiers/SEQUENCE.md`

## Completion Summary
Root cause determined: the epic-scoping investigation doc was a pre-ticket working file, deliberately
gitignored per repo policy, renamed once (to a `TCK-`-prefixed staging folder) but never migrated to
`stored_artifacts/` because its owning ticket was epic-tier (scope-only, no Finalize phase) — then
lost from the working tree with no git-history recovery path. Not recoverable, so all 24 citing
files were corrected in place with a standardized note explaining the loss and pointing to the two
tickets (`UNIT-WORLD-AGENCY`, `E2E-CONTENT-EXPANSION`) that already independently re-verified the
underlying facts against ground truth. All `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` child tickets were
already closed and covered in this same pass, so no further ticket-by-ticket rediscovery is needed.
`make knowledge-index-update` was run after these docs/ edits landed (Verify-phase gap caught by
done-checker and closed before Finalize) so the agent search index reflects the corrected citations.
