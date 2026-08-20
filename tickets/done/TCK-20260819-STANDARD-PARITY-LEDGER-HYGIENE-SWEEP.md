---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
phase: done
date: 2026-08-19
tags: [ai, documentation]
---

# TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP

## Title
Parity ledger hygiene: fix 2 malformed entries, triage stale file citations, archive orphaned predecessor checklist

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
High-level health investigation of `docs/parity_ledger/*.yaml` (2,047 entries, 9 subsystems),
using the existing `tools/parity_index.py` SQLite query tooling rather than raw YAML reads.
Overall health is good — 98.8% verified/legacy_verified, no duplicate IDs. Four concrete,
independently-actionable findings surfaced, each population-level (not anecdotal):
1. Exactly 2 of 2,047 entries (`TOWN-040`, `TOWN-041`) are malformed — every evidence field empty,
   degenerate fixture-name-leak text. Isolated anomaly, not a pattern (the `` `test_name`:
   description `` format itself is a real, widespread, correct convention elsewhere).
2. 173 `absent_file` health findings (paths cited in the ledger that don't resolve on disk) — a
   mix of checker imprecision (frontend paths missing a `dashboard-frontend/` root, prose mentions
   of intentionally-deleted files) and likely-genuine drift, concentrated in 120 `test_refs` hits
   that plausibly reflect real test-file moves.
3. 1,552 of 2,047 entries (76%) lack machine-parseable structured references
   (`legacy_unstructured`) — can't power the tooling's own `impact` blast-radius query. Real, but
   large — flagged out of scope for this ticket.
4. `docs/logic_checklist_exhaustive.md` (3,197 lines) is the confirmed historical predecessor of
   the parity ledger itself — its own already-archived design spec describes the exact migration
   into today's ID scheme. Last touched 2026-07-02, 5 support scripts wired into neither `Makefile`
   nor CI, one dangling internal reference to a nonexistent filename variant. Never archived.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- Fix (or remove, if unrecoverable) the 2 malformed entries.
- Triage the 173 `absent_file` findings — fix genuine drift, fix or flag the checker's own
  frontend-root resolution gap, distinguish narrative mentions from live citations. Do this
  **after** `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` lands (it's actively moving 61 test
  files as of this investigation — triaging against a moving target wastes effort).
- Archive `docs/logic_checklist_exhaustive.md` and its 5 orphaned support scripts; fix the
  dangling filename reference in `src/engine/rpg_depth.py`.

## Out of Scope
- Retrofitting the 1,552 `legacy_unstructured` entries with structured references — large,
  speculative, separate effort; not broken, just less automatable.
- Any change to `docs/parity_ledger/schema.json`.

## Acceptance Criteria
- [x] No entry in the ledger has every evidence field empty (down from 2). TOWN-040/TOWN-041
      removed (no real `test_rng`/`test_entity` functions exist repo-wide); full-table bare-entry
      SQL scan returns 0 rows.
- [x] `absent_file` count meaningfully drops from the 173 baseline, with each remaining/fixed hit
      triaged (not blindly suppressed). Final count: 26 (down from a rebuilt-post-domain-nesting
      baseline of 174; 85% reduction), every remaining hit individually triaged as a legitimate
      historical/narrative mention (each carries an explicit "relocated from X (deleted)" or
      "confirmed deleted" note in the entry's own v2_evidence/text).
- [x] The orphaned checklist system (`docs/logic_checklist_exhaustive.md` + 5 scripts) is
      archived, not just noted as orphaned. Doc moved to `docs/archive/` with corrected
      frontmatter; all 5 scripts moved to `scripts/archive/`; all live cross-references fixed
      (see Implementation Notes).

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line this
  session's investigations belong to)
- TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING (its in-flight test-file moves are directly
  relevant to finding 2's `test_refs` triage — implement after this one lands)
- TCK-20260817-DEAD-INFRA-REMOVAL-EPIC (source of the correctly-`unsupported` broker entries noted
  as context, not a finding, in this ticket's investigation)

## Related Docs
- tools/parity_index.py
- docs/archive/specs/2026-05-03-checklist-governance-design.md
- docs/logic_checklist_exhaustive.md
- docs/parity_ledger/*.yaml

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP/

## Related Code Areas
- docs/parity_ledger/town_resource.yaml
- tools/parity_index.py (`_populate_entry_health`)
- docs/logic_checklist_exhaustive.md
- scripts/validate_checklist.py, scripts/ledger_validator.py, scripts/remediate_checklist.py,
  scripts/report_coverage.py, scripts/apply_traceability.py
- src/engine/rpg_depth.py (dangling filename reference)

## Assumptions / Open Questions
- Whether any of the 5 orphaned scripts contain logic worth preserving as reference (vs. pure
  duplication of what `tools/parity_ledger_scan.py`/`writer.py`/`index.py` now do) is left to the
  implementer's judgment.
- Exact count of genuinely-fixable `absent_file` hits (vs. checker false positives) wasn't
  determined here by design — population-level counts only, per this investigation's explicit
  high-level scope; per-item triage is the implementer's job.

## Implementation Notes

**Step 1 — malformed entries.** Confirmed via repo-wide grep that no real `test_rng`/`test_entity`
functions exist anywhere — the fixture-name-leak theory was correct. Removed `TOWN-040`/
`TOWN-041` from `docs/parity_ledger/town_resource.yaml` (default-removal outcome per plan.md).
Rebuilt the index; the full-table bare-entry SQL scan returns 0 rows. Ran
`tools/parity_ledger_writer.py::validate_entry()` directly against `town_resource.yaml`'s full
189-entry list: confirms TOWN-040/041 no longer appear (trivially compliant); the 150 pre-existing
`test_path`-missing validation errors on *other* entries in that shard are the known, pre-existing
`missing_test_path` debt (1336 ledger-wide) explicitly out of scope for this ticket.

**Step 2 — absent_file triage.** `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` had already
landed (found in `tickets/done/`), so the precondition was satisfied. Rebuilt the index post-TOWN-
040/041 removal: baseline was 174 (not 173 — the domain-nesting ticket's test moves shifted the
count by 1 since the original investigation snapshot). Found and fixed **three separate systemic
checker bugs** in `tools/parity_index.py::_populate_entry_health()` (all three verified against
real, currently-passing tests before and after, with new regression tests added to
`tests/tools/test_parity_index.py::TestEntryHealth`):
  1. Frontend paths cited as bare `src/...` when the real file lives under
     `dashboard-frontend/src/...` (confirmed: `dashboard-frontend/src/App.tsx` is real, cited in
     the ledger as `src/App.tsx`). Added `_path_resolves()` checking a second root for
     `.ts`/`.tsx`/`.js`/`.jsx` paths. Fixed 25 findings (174 → 149).
  2. **New finding, not anticipated by the plan**: a declared `test_path` with a
     `::test_function` pytest node-id suffix was checked as a literal filesystem path including
     the `::` suffix, so it was always "absent" even when the underlying `.py` file is completely
     real (`Path("x.py::fn").exists()` is always `False`). This explained 117 of the 149 remaining
     findings — the large majority of what the plan called the "highest-confidence real drift"
     `test_refs` bucket was actually this checker bug, not real drift. Fixed by stripping the
     `::symbol` suffix before the existence check (consistent with the module's own pre-existing,
     stated non-goal of symbol-level verification). Fixed 117 findings (149 → 32).
  3. **New finding**: `legacy_evidence`-sourced `code_refs` were checked for existence, but
     `legacy_evidence` exists specifically to document the pre-V2 (often since-deleted)
     implementation location — checking it for existence is a category error. All 3
     `legacy_evidence`-sourced `code_refs` rows repo-wide were false positives (SUB-007, SUB-073,
     STRAT-257). Fixed by excluding `source_field == "legacy_evidence"` from the check. Fixed 3
     findings (32 → 29).
  After the three systemic fixes, manually triaged all remaining findings individually:
  fixed real citation drift in 15 ledger entries (SOC-001/002/003/004/006/008/051,
  STRAT-006/007/008/009/225/243, SUBSTRATE-NEW-003, TOWN-186, INFRA-202, INFRA-275) — updated
  `v2_evidence`/`test_path` to the real current file/function locations, each verified against a
  real, currently-passing test before committing the citation. Left the remaining hits unchanged
  where they are legitimate historical narrative (each carries an explicit in-place "relocated
  from X (deleted)" / "confirmed deleted" marker, matching this ledger's own pre-existing
  convention: STRAT-236/246/252/253, INFRA-211/225/279/287/277/303 already used this pattern
  before this ticket started). Final count: 26 absent_file findings, all individually triaged.

**Step 3 — archive.** Grep sweep found all references plan.md anticipated, exactly matching
its live-reference list. Moved `docs/logic_checklist_exhaustive.md` to
`docs/archive/logic_checklist_exhaustive.md` with frontmatter corrected to
`status: archive` / `authority: P2` / `audience: historical` / `layer: guidelines` /
`original_date: 2026-05-04` (confirmed via `git log --follow --diff-filter=A`). Moved all 5
scripts to `scripts/archive/` (none contained logic worth preserving outside the
now-archived-and-correctly-repointed reference use — each is a small, single-purpose parser tied
1:1 to the retired checklist's own text format, fully superseded by
`tools/parity_ledger_scan.py`/`writer.py`/`index.py`); updated each moved script's own hardcoded
`CHECKLIST` path to point at the new archived location (safe since these scripts are dead code by
design now, kept for reference — unlike the certification-reporter case below). Found and fixed a
real functional dependency the grep sweep surfaced: `scripts/release_gate.py:93` calls
`scripts/ledger_validator.py` via `subprocess` — updated the call site to
`scripts/archive/ledger_validator.py` (release_gate.py is itself confirmed unwired from
Makefile/CI, so this was already unreachable in practice, but leaving a fresh dangling reference
while fixing old ones would be self-defeating). Fixed `tools/add_frontmatter_live.py`'s
`LOOSE_FILES["docs/logic_checklist_exhaustive.md"]` entry by **removing** it (not updating to
archived frontmatter) — the tool's own docstring says it "excludes archive," so a `LOOSE_FILES`
entry for a now-archived file is definitionally out of that tool's scope; updated the paired
`tests/tools/test_add_frontmatter_live.py::test_loose_logic_checklist` by removing it to match.
Updated `docs/plans/engine_future_epics_roadmap.md:43`'s roadmap row to record the resolution
rather than restate the now-stale "could mislead future agents" framing.

Fixed all 3 (not 1 — investigation.md's original count was incomplete, corrected during Review)
dangling `logic_checklist_exhaustive_v2.md` references. **Deviation from plan.md's literal
suggestion**: for `scripts/certification_long_run.py:154` and
`tests/integration/kernel/test_certification_scenarios.py:112`, chose "remove the stale
cross-reference" over "point at the real archived path" — repointing would have changed
observable behavior, since both pass the string as a functional `checklist_path` argument into
`CertificationReporter.generate_report()`, whose `_analyze_checklist()` would then actually parse
the archived doc's `[x] VERIFIED v2` markers and compute a real `coverage["percent"]`, which
directly feeds the report's `"CERTIFIED"` vs `"PROVISIONAL"` status — silently reactivating a
retired coverage-scoring mechanism this exact ticket exists to retire. Replaced both with a
deliberately-still-unresolvable sentinel path (`"logic_checklist_exhaustive.md.retired"`) plus an
inline comment explaining why, preserving today's existing no-op behavior byte-for-byte while
removing the dangling/wrong filename. For `src/engine/rpg_depth.py:8` (a pure docstring, no
functional path argument), repointed to the real archived path since there is no behavior-change
risk there. This deviation is recorded in `staging_artifacts/.../plan.md`'s new Deviations
section.

Added a `docs/parity_ledger/README.md` one-line-note doc (plan.md offered this as the alternative
to editing `schema.json`, which is explicitly out of scope) stating the parity ledger is the sole
authoritative parity-tracking mechanism.

**investigation.md corrections** (per Review, documentation-accuracy only, no code implication):
finding 4's "last touched 2026-07-02" corrected to note the 2026-08-19 touch (commit `280639aa`,
unrelated test-path-comment sync from the domain-nesting ticket); "one dangling internal
reference" corrected to the real count of 3.

## Test Summary
Ran the full parity-ledger tool suite (`tests/tools/test_parity_index.py`,
`test_parity_index_baseline.py`, `test_parity_ledger_scan.py`, `test_parity_ledger_schema.py`,
`test_parity_ledger_writer.py`, `test_parity_updater_static.py`): 83 passed (78 pre-existing + 5
new regression tests covering the three systemic checker fixes: frontend second-root resolution,
pytest node-id suffix stripping, legacy_evidence exclusion — each with both a
should-not-flag and a still-flags-real-absence case). Ran every real test file cited by a fixed
ledger citation before committing that citation (590 tests total across
`tests/unit/social/`, `tests/unit/strategic/test_detour_suggestion.py`,
`tests/unit/worldbuilding/test_world_compiler.py`, `tests/unit/engine/test_content_hotpath_guard.py`,
`tests/unit/worldmodules/`, `tests/unit/worldassembly/test_resolver.py`,
`tests/integration/worldassembly/`, `tests/perf/test_phase3_adventure_decision_budget.py`,
`tests/integration/kernel/test_certification_scenarios.py`, `tests/tools/test_add_frontmatter_live.py`,
`tests/tools/test_validate_frontmatter.py`) — all pass. Ran `python3 -m py_compile` on all 5
archived scripts plus every edited `.py` file — all parse cleanly. Ran
`tools/validate_frontmatter.py` on both the moved doc and the new README — both pass (the
352 pre-existing violations found by a full `docs/` sweep are unrelated pre-existing debt, none
touching this ticket's files).

## Files Changed
- `docs/parity_ledger/town_resource.yaml` — removed TOWN-040/TOWN-041; fixed TOWN-186 test_path
- `docs/parity_ledger/social_narrative.yaml` — fixed v2_evidence/test_path citations on SOC-001/
  002/003/004/006/008/051
- `docs/parity_ledger/strategic_cognition.yaml` — fixed citations on STRAT-006/007/008/009/225/243
- `docs/parity_ledger/substrate.yaml` — fixed SUBSTRATE-NEW-003's worldmodules/resolver.py citation
- `docs/parity_ledger/infrastructure.yaml` — fixed INFRA-202 test_path, INFRA-275 multi-path
  formatting
- `docs/parity_ledger/README.md` — new: one-line authoritative-mechanism note
- `tools/parity_index.py` — 3 systemic `_populate_entry_health()` fixes (frontend second root,
  node-id suffix stripping, legacy_evidence exclusion)
- `tests/tools/test_parity_index.py` — 5 new regression tests for the above
- `docs/logic_checklist_exhaustive.md` → `docs/archive/logic_checklist_exhaustive.md` (moved,
  frontmatter corrected)
- `scripts/validate_checklist.py` → `scripts/archive/validate_checklist.py` (moved, path fixed)
- `scripts/ledger_validator.py` → `scripts/archive/ledger_validator.py` (moved, path fixed)
- `scripts/remediate_checklist.py` → `scripts/archive/remediate_checklist.py` (moved, path fixed)
- `scripts/report_coverage.py` → `scripts/archive/report_coverage.py` (moved, path fixed)
- `scripts/apply_traceability.py` → `scripts/archive/apply_traceability.py` (moved, path fixed)
- `scripts/release_gate.py` — fixed subprocess call site to the new archived script path
- `tools/add_frontmatter_live.py` — removed the now-archived LOOSE_FILES entry
- `tests/tools/test_add_frontmatter_live.py` — removed the paired test
- `docs/plans/engine_future_epics_roadmap.md` — updated stale roadmap row to record resolution
- `src/engine/rpg_depth.py` — fixed dangling `logic_checklist_exhaustive_v2.md` docstring reference
- `scripts/certification_long_run.py` — fixed dangling reference (retired sentinel, not repointed)
- `tests/integration/kernel/test_certification_scenarios.py` — fixed dangling reference (same)
- `tickets/todos/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP.md` → `tickets/inprogress/...`
  (ticket file itself)
- `staging_artifacts/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP/investigation.md` — fixed
  finding 4's stale date claim and reference-count claim
- `staging_artifacts/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP/plan.md` — Deviations
  section added (see Implementation Notes); this file's pre-implementer content (2 rounds of
  architecture review) was already in place when implementation started
- `staging_artifacts/TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP/test_plan.md` — already in
  place when implementation started, listed here per this run's own Investigate/Plan-phase
  changeset

## Completion Summary
Implemented all 3 steps of the approved plan. Step 1 removed the 2 malformed TOWN-040/TOWN-041
entries (confirmed no real underlying test exists) and verified schema compliance directly via
`validate_entry()`, not just the build/bare-entries scan. Step 2 rebuilt the `absent_file` health
check, found and fixed 3 systemic checker bugs in `tools/parity_index.py` (frontend second-root
resolution, pytest node-id-suffix stripping, legacy_evidence exclusion — 145 of 174 findings were
checker imprecision, not ledger content problems) with regression test coverage, then manually
triaged and fixed 15 ledger entries' genuine citation drift, landing at 26 remaining findings
(85% reduction from baseline), each individually documented as legitimate historical narrative.
Step 3 archived the orphaned predecessor checklist doc and its 5 dead support scripts, fixed all
discovered live cross-references (including one real functional dependency the grep sweep
surfaced in `scripts/release_gate.py`), and added a short authoritative-mechanism note to
`docs/parity_ledger/`. All touched tests pass (590+ across the affected subsystems); no
observable simulation/engine behavior changed — this is a documentation/tooling/dead-code hygiene
ticket only, with one deliberate exception (a systemic bug fix in the parity-index health
checker's own logic, which is test/tooling infrastructure, not simulation behavior).
