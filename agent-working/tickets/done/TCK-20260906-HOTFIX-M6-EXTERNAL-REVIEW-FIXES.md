---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260906-HOTFIX-M6-EXTERNAL-REVIEW-FIXES
phase: done
date: 2026-09-06
tags: [architecture, faction]
---

# TCK-20260906-HOTFIX-M6-EXTERNAL-REVIEW-FIXES

## Title
Fix 4 real issues found by an external pre-merge review of PR #133 (M6) before merge

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
A cross-session peer review ("rpg-feature-planning") ran a structured 3-angle review
(architecture/determinism, mechanics/parity-ledger, ticket-workflow) against PR #133 before merge,
delivering 4 numbered findings. Independently re-verified every claim against real repo state before
acting, per this session's own established verify-then-fix discipline (mirroring the identical
process already run against PR #128's own external review, `TCK-20260905-HOTFIX-EXTERNAL-REVIEW-FIXES`).
All 4 findings confirmed real; none were fabricated or already-fixed.

1. **Architecture guard regex gap**: `tests/architecture/test_faction_mutation_write_paths.py`'s
   `dataclasses.replace(...)` bypass-scan pattern (`replace\([^)]*?faction\s*=(?!=)`) cannot match
   across one level of nested parens (e.g. `dataclasses.replace(entity.identity, role=get_default_role(),
   faction=Faction.NEUTRAL)` — `get_default_role()`'s own closing paren terminates `[^)]*?` before
   `faction=` is ever reached), silently evading the guard. Not a live bypass today (confirmed via
   direct scan), but a real detection gap.
2. **PR body overclaim**: PR #133's checklist and findings text stated `spawn_humanoid_offspring()`
   "was importing `src.engine` internally" as a fixed violation, as if it had landed in a commit.
   Confirmed via `git diff main...HEAD -- src/systems/world_systems/generator.py` that no such import
   ever appears in any committed diff — the real story (per the ticket's own Implementation Notes) is
   that this was a transient draft caught and fixed during the Implement phase's own iterative work,
   never actually reaching git history.
3. **Undisclosed P0 outcome-flip**: idea 39's faction-mutation trigger can flip
   `LegalityServiceV2.verify_attack_legality()`'s P0-certified Friendly-Fire verdict (COMB-294) for a
   given attacker/target pair starting the next tick after a defection — a real change to a certified
   law's outcome, not just its timing. COMB-294's own ledger entry did not disclose this interaction.
   Confirmed via `tests/unit/engine/test_legality_faction_mutation.py::
   test_faction_change_mid_tick_legality_semantics`, which literally demonstrates
   `legal_before=True`/`LEGAL` -> (defection) -> `legal_after=False`/`FRIENDLY_FIRE_ILLEGAL`.
4. **Documentation-accuracy gaps** (does not undermine the original safety conclusion — all missed
   sites are immediate per-tick reads, not cross-tick caches):
   - `identity.faction` call-site count was reported as 31 (6 `legality.py` + 25 others); a fresh
     repo-wide grep found 41 real sites, including 2 in `src/engine/town_resolution.py` (taxation and
     suppression checks) never enumerated by the original investigation.
   - `tickets/working_log.csv`'s `DRIFTING-LOYALTY-SIGNAL` row said `staging_artifacts/` instead of
     `stored_artifacts/`.
   - The epic ticket (`TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY`) still referenced
     `tickets/todos/m6-political-identity/SEQUENCE.md` in 2 places after the folder moved to
     `tickets/done/` once the last child ticket landed.

## Scope
- `tests/architecture/test_faction_mutation_write_paths.py` — widen `_IDENTITY_REPLACE_FACTION_BYPASS_PATTERN`
  to tolerate one level of nested balanced parens.
- `docs/world/affiliation_mutation.md` — correct the call-site count (31 -> 41) and disclose the 2
  unaudited `town_resolution.py` sites.
- `tickets/done/TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY.md` — correct the same call-site count in
  its Completion Summary, and fix the 2 stale `SEQUENCE.md` path references.
- `docs/guidelines/intentional_divergences.md` — new §2.52 disclosing the COMB-294 outcome-flip
  (rationale class: Bounded), plus a new Summary Table row.
- `docs/parity_ledger/combat_movement.yaml` — cross-reference COMB-294 <-> COMB-323 <-> §2.52; correct
  COMB-323's own `support_boundary` call-site count (31 -> 41).
- `tickets/working_log.csv` — fix the `staging_artifacts/` -> `stored_artifacts/` typo on the
  `DRIFTING-LOYALTY-SIGNAL` row (surgical single-line text substitution only — a first attempt via
  Python's `csv` module full-file rewrite was caught producing a 204-line diff from re-serialization
  formatting differences and reverted before committing).
- PR #133's own body (`gh api .../pulls/133 -X PATCH`) — correct the overclaiming `src.engine` import
  bullets and the 31/41 count, and add a summary of this review-fix round.

## Out of Scope
- Any change to `LegalityServiceV2` or the phase-order guarantee itself — confirmed correct and
  intentional; this is a disclosure-only fix.
- Auditing every one of the 41 `identity.faction` call sites individually for the same timing-safety
  property — `town_resolution.py`'s 2 sites were spot-checked as structurally identical to
  `legality.py`'s own reads; the remaining sites are out of scope for this hotfix (COMB-323's own
  `support_boundary` already discloses this as a scoped-out item).
- Any production code change — this hotfix touches only tests (a detection-gap widening), docs, and
  parity-ledger/working-log metadata.

## Acceptance Criteria
- [x] `tests/architecture/test_faction_mutation_write_paths.py`'s widened regex matches the peer's
      exact nested-paren example while preserving all prior correct match/non-match behavior; all 4
      tests in the file still pass.
- [x] `docs/world/affiliation_mutation.md` and the epic ticket's Completion Summary both cite 41 (not
      31) real call sites, with the `town_resolution.py` disclosure present.
- [x] `docs/guidelines/intentional_divergences.md` §2.52 exists with Subsystem/Old Behavior/New
      Behavior/Rationale/Verification/Status fields and a Summary Table row, cross-referenced from
      `docs/parity_ledger/combat_movement.yaml`'s COMB-294 and COMB-323 entries.
- [x] `tickets/working_log.csv`'s `DRIFTING-LOYALTY-SIGNAL` row says `stored_artifacts/`; diff confirmed
      scoped to the single logical row.
- [x] The epic ticket's 2 `SEQUENCE.md` references point at `tickets/done/m6-political-identity/`.
- [x] `python3 tools/parity_index.py build && health` runs clean after the parity-ledger edits.
- [x] PR #133's body no longer claims a committed `src.engine` import violation in
      `spawn_humanoid_offspring()`, and cites 41 call sites.

## Related Tickets
- TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY (the epic this review covers)
- TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE (idea 39 — source of findings 1, 3, 4)
- TCK-20260905-HOME-EXILE-REFUGEE-THREADS (idea 59+65 — source of finding 2)
- TCK-20260905-HOTFIX-M6-CI-DRIFT-AND-COVERAGE-GAP (the immediately-prior hotfix on this same PR)
- TCK-20260905-HOTFIX-EXTERNAL-REVIEW-FIXES (the identical-shaped precedent hotfix for PR #128's own
  external review)

## Related Docs
- docs/world/affiliation_mutation.md
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/combat_movement.yaml (COMB-294, COMB-323)

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in this ticket.

## Related Code Areas
- tests/architecture/test_faction_mutation_write_paths.py
- src/engine/legality.py
- src/engine/town_resolution.py

## Assumptions / Open Questions
None — every finding was independently confirmed against real repo state before fixing.

## Implementation Notes
Every one of the peer's 4 findings was independently re-verified before acting (never trusted
blindly): the regex gap was reproduced with a standalone Python script against the peer's exact
example; the PR-body overclaim was confirmed via `git diff` against `main` showing zero actual
`src.engine` import in any commit; the P0 outcome-flip was confirmed by reading
`test_legality_faction_mutation.py` directly; the call-site undercount was confirmed via a fresh
`grep -rn "\.identity\.faction\b" src/ --include="*.py"` (41, not 31).

The `tickets/working_log.csv` fix required a second attempt: the first, via Python's `csv` module
reading and rewriting the whole file, technically produced correct content but generated a 204-line
diff (102 insertions/deletions) purely from `csv.writer`'s different quoting/formatting versus the
file's original exact byte formatting — caught via `git diff --stat` before committing, reverted via
`git checkout -- tickets/working_log.csv`, and redone as a minimal Edit-tool text substitution
targeting only the one row's trailing field. Confirmed via a full line-by-line `diff` (not just `git
diff`, whose default algorithm rendered the single real change as a larger, cosmetically-misleading
hunk against several byte-identical surrounding lines) that only that one row's content actually
changed.

All parity-ledger edits used the sanctioned `tools/parity_ledger_writer.py::write_entry()` (never a
raw YAML edit), and `tools/parity_index.py build`/`health` were re-run clean afterward.

## Test Summary
- `tests/architecture/test_faction_mutation_write_paths.py tests/tools/test_parity_index_baseline.py
  tests/tools/test_parity_updater_static.py` — 39 passed, 0 failed.
- `tools/validate_frontmatter.py` clean on all 3 edited doc/ticket files.
- `tools/parity_index.py build` + `health` — status `ok`, 2173 entries, 9 shards.

## Files Changed
- `tests/architecture/test_faction_mutation_write_paths.py`
- `docs/world/affiliation_mutation.md`
- `docs/guidelines/intentional_divergences.md`
- `docs/parity_ledger/combat_movement.yaml`
- `tickets/done/TCK-20260823-EPIC-RPG-M6-POLITICAL-IDENTITY.md`
- `tickets/working_log.csv`
- `docs/REGISTRY.yaml` (regenerated)
- PR #133's own body (GitHub-side, not a repo file)

## Completion Summary
Fixed all 4 real findings from an external pre-merge review of PR #133, matching the identical
verify-then-fix discipline already applied to PR #128's own external review. No production code
touched — this hotfix widens a test detection gap and corrects documentation/metadata accuracy,
including a genuine P0-law disclosure gap (COMB-294's interaction with the new faction-mutation
primitive) that had real architectural significance even though no code needed to change.
