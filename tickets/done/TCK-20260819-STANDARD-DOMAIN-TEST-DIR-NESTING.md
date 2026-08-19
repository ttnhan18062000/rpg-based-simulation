---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING
phase: done
date: 2026-08-19
tags: [testing]
---

# TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING

## Title
Nest 6 stray domain-subpackage test directories under tests/unit/domains/ to match the other 13

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
`src/domains/` has 19 subpackages. Only 13 have their tests nested under
`tests/unit/domains/<name>/`; the other 6 — `campaigns`, `chronicle`, `culture`, `faction`,
`feature_packs`, `optimization` (61 files total) — sit as flat siblings directly under
`tests/unit/`. This is item 3 of `TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC`, previously
flagged but left unverified ("coverage exists... just inconsistently located" — asserted, not
confirmed). This ticket supplies the exact verified split and pulls the item out as a standalone,
directly-actionable ticket, matching the pattern already used for that epic's siblings
(A/B/D/E/F/G/H/I). Root cause: `docs/testing/content_migration_test_ownership.md`'s "New Suite
Creation Rules" never stated a domain-nesting convention to begin with — there was no rule to
follow, so nothing was violated so much as never specified.

## Scope
Full investigation and step-by-step plan are in `staging_artifacts/` for this ticket. Concrete
scope:
- `git mv` the 6 directories into `tests/unit/domains/<name>/`.
- Remove the 6 now-redundant explicit CI path entries in `.github/workflows/test.yml`
  (`unit-core-world` and `unit-gameplay` jobs) — the moved content is automatically covered by
  `unit-infra`'s existing `tests/unit/domains` path entry.
- Update `.claude/agents/test-scoper.md`'s Test Directory Map to reflect the real, corrected
  nesting (only once the move actually happens, not before).
- Add a domain-nesting convention rule to `docs/testing/content_migration_test_ownership.md`'s
  "New Suite Creation Rules" so this doesn't recur for new domain subpackages.

## Out of Scope
- `demographics` (no test directory under either layout today) — a coverage gap, not a placement
  question; not created by this ticket.
- Any change to test content/behavior — pure directory relocation.
- Splitting `unit-infra` into an additional CI job, even if its runtime grows — a follow-up
  decision only if the growth proves to be a real problem in practice.

## Acceptance Criteria
- [x] All 19 `src/domains/` subpackages' tests (18 that currently have any) live under
      `tests/unit/domains/<name>/` — none remain as flat `tests/unit/<name>/` siblings.
- [x] Pre-move and post-move `pytest --collect-only` counts for the moved content match exactly.
- [x] `.github/workflows/test.yml` still runs every moved test (from its new location) and
      remains valid YAML.
- [x] `.claude/agents/test-scoper.md` and `docs/testing/content_migration_test_ownership.md` both
      reflect the corrected structure/convention.

## Related Tickets
- TCK-20260817-CODEBASE-NAVIGABILITY-HYGIENE-EPIC (item 3 extracted from here; epic remains open
  for its other 3 items)
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic of the wider audit line)
- TCK-20260819-HOTFIX-CI-TEST-DIR-COVERAGE-CHECK (sibling ticket — its completeness check guards
  against a *future* recurrence of this same class of drift; this ticket only fixes the current
  instance)

## Related Docs
- docs/audits/D24_codebase_health_observatory.md (§D, §F — original source finding)
- docs/plans/codebase_navigability_hygiene_epic.md
- docs/testing/content_migration_test_ownership.md
- .claude/agents/test-scoper.md

## Related Stored Artifacts
staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/

## Related Code Areas
- tests/unit/campaigns/, tests/unit/chronicle/, tests/unit/culture/, tests/unit/faction/,
  tests/unit/feature_packs/, tests/unit/optimization/, tests/unit/domains/
- .github/workflows/test.yml

## Assumptions / Open Questions
- Whether `unit-infra`'s CI runtime growth (absorbing ~61 files' worth of tests previously split
  across two other jobs) is meaningful enough to warrant its own job split — not pre-judged;
  measure at implementation time.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/plan.md`
(APPROVED, 2 review rounds). No deviations from the plan — all 8 steps completed as written.

1. `git mv`'d each of the 6 directories individually into `tests/unit/domains/`
   (`campaigns`, `chronicle`, `culture`, `faction`, `feature_packs`, `optimization`).
2. Fixed the one confirmed regression: `tests/unit/domains/campaigns/test_campaign_state.py:290`
   (`test_campaign_state_module_has_no_engine_imports`) — added a 5th `.parent` hop to the
   `Path(__file__)` chain (was 4, now 5) so it still resolves to `src/domains/campaigns/state.py`
   from the new, one-level-deeper location. Verified this was the *only*
   `Path(__file__)`/`sys.path` hit across all 6 moved directories (grep confirmed zero others).
   Also updated the 4 cosmetic old-path header-comment references (`test_campaign_state.py`,
   `test_campaign_orchestrator.py`, `test_narrative_ledger.py`, `test_chronicle_compiler.py`) —
   docstring text only, no executable-code risk.
3. Repo-wide grep sweep for the 6 old bare path strings. Updated all in-scope live references:
   8 parity ledger shard files (~45 `test_path`/text citations, including the 2 P0 entries
   SUB-383 and COMB-310, both spot-checked to now point at the real, existing
   `tests/unit/domains/optimization/test_movement_candidate_selector.py`), plus
   `docs/optimization_audit_ledger.md`, `docs/logic_checklist_exhaustive.md`,
   `docs/simulation/domains/chronicle_contract.md`, `docs/guidelines/design_patterns.md`,
   `docs/guidelines/intentional_divergences.md`, `docs/performance/optimization_invariants.md`,
   `docs/engine/candidate_selection.md`, `docs/engine/authoritative_apply_contract.md`,
   `docs/plans/codebase_navigability_hygiene_epic.md`. Confirmed zero remaining live hits outside
   the explicitly out-of-scope dirs (`tickets/done/`, `stored_artifacts/`, `docs/audits/`,
   `docs/archive/**`) via a final repo-wide sweep. `docs/REGISTRY.yaml` left untouched (auto-
   regenerated at Finalize, per plan).
4. Removed the 6 redundant explicit CI path lines from `.github/workflows/test.yml`
   (`tests/unit/feature_packs`/`tests/unit/culture` from `unit-core-world`;
   `tests/unit/faction`/`tests/unit/campaigns` from `unit-gameplay`;
   `tests/unit/optimization`/`tests/unit/chronicle` from `unit-infra`) — `unit-infra`'s existing
   `tests/unit/domains` entry now covers all 6 via pytest recursion. Confirmed valid YAML.
5. Updated `.claude/agents/test-scoper.md`'s Test Directory Map: removed the "Known
   inconsistency, pending fix" callout (now resolved), removed `campaigns`/`optimization` as flat
   top-level entries, and added an explicit `tests/unit/domains/` sub-map listing all 18
   nested-with-tests subpackages.
6. Verified `docs/testing/content_migration_test_ownership.md`'s existing New Suite Creation
   Rules #6 and #7 (added by prior commit `92b6f02e`) are accurate as-is now that the move has
   landed — did not add a duplicate rule. Added the missing Ownership Table row for
   `tests/unit/domains/` (marker `unit`; Owns: all 18 domain-subpackage suites with tests, the 6
   newly-nested plus the 12 already-nested; `demographics` has no test dir, out of scope).
7. Ran `graphify update .` (32880 nodes, 98748 edges, 1210 communities — succeeded) and
   `make knowledge-index-update` (incremental: 10 files changed/new, 7827 chunks total —
   succeeded).
8. Full verification per `test_plan.md` — see Test Summary below.

**Concurrent-session note (not a deviation, informational):** partway through this run, a
different concurrent agent session (working `TCK-20260819-STANDARD-LAB-WORKFLOWS-FILE-SPLIT` in
the same shared working tree) committed (`85189803`) while this ticket's `git mv` renames were
already staged in the shared index; its commit swept in the pure-rename portion of this ticket's
work as a side effect (0 line changes for those paths — a true no-op rename, confirmed via
`git show --stat`), even though its own commit message states it intentionally left this ticket's
work "completely untouched." Net effect on the working tree is identical to the plan's intended
end state; this session's own remaining edits (Steps 2-6) landed as normal uncommitted working-tree
changes on top, verified consistent via a full post-hoc directory listing and a full test run.
Flagging for Finalize/commit-review visibility, not treated as a blocker.

**Unresolved Question (`unit-infra` CI runtime growth):** measured locally, not from real CI.
The subset of tests that moved from `unit-core-world`/`unit-gameplay` into `unit-infra`'s scope
(`campaigns` + `faction` + `culture` + `feature_packs`, 306 tests) ran in ~0.77s of local pytest
execution time (~1.7s wall including startup). `unit-infra`'s full new job command ran 2207
passed + 1 skipped in ~38s locally. This suggests the added execution-time load is small relative
to `unit-infra`'s existing runtime, but local timing does not capture real CI overhead (checkout,
pip install, runner variance), so this remains an estimate, not a definitive answer — deferred to
real CI observation as the plan specifies. No action taken (a job split is explicitly out of
scope for this ticket).

## Test Summary
- Pre-move baseline (`pytest --collect-only` across the 6 old flat dirs + existing
  `tests/unit/domains`): 713 tests collected.
- Post-move `pytest tests/unit/domains --collect-only -q`: 713 tests collected — exact match.
- Post-move full run, `pytest tests/unit/domains -m "not slow and not extra_slow" --tb=short -q`:
  **713 passed, 0 failed** (2.35s). This is the run that would have caught the
  `Path(__file__)` regression had Step 2's fix been wrong or incomplete; it did not fail.
- Spot-checked `test_campaign_state_module_has_no_engine_imports` in isolation: PASSED.
- Ran the actual post-edit CI job commands locally:
  - `unit-core-world`: 1305 passed, 1 skipped (72.9s).
  - `unit-gameplay`: 954 passed (4.5s).
  - `unit-infra` (now includes `tests/unit/domains`, absorbing the 6 moved dirs): 2207 passed,
    1 skipped, 1 pre-existing unrelated warning (`recipe_learned` flakiness note, not caused by
    this change) (38.1s).
- `.venv/bin/python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"`: valid.
- Repo-wide grep sweep for the 6 old bare path strings: zero live hits outside the explicitly
  out-of-scope dirs (`tickets/done/`, `stored_artifacts/`, `docs/audits/`, `docs/archive/**`) and
  this ticket's own staging_artifacts (which intentionally narrate the pre-move state as part of
  the ticket's own history).
- Spot-checked parity ledger P0 entries SUB-383 and COMB-310: both `test_path` fields now read
  `tests/unit/domains/optimization/test_movement_candidate_selector.py`, and that file genuinely
  exists at that path.
- `graphify query "domains test directory"` ran successfully post-`graphify update .` (sanity
  check only, not a hard gate per test_plan.md).

## Files Changed
- `tests/unit/domains/campaigns/` (moved from `tests/unit/campaigns/`, 18 files, `git mv`)
- `tests/unit/domains/chronicle/` (moved from `tests/unit/chronicle/`, 6 files, `git mv`)
- `tests/unit/domains/culture/` (moved from `tests/unit/culture/`, 6 files, `git mv`)
- `tests/unit/domains/faction/` (moved from `tests/unit/faction/`, 13 files, `git mv`)
- `tests/unit/domains/feature_packs/` (moved from `tests/unit/feature_packs/`, 6 files, `git mv`)
- `tests/unit/domains/optimization/` (moved from `tests/unit/optimization/`, 18 files, `git mv`)
- `tests/unit/domains/campaigns/test_campaign_state.py` (Path regression fix + docstring path)
- `tests/unit/domains/campaigns/test_campaign_orchestrator.py` (docstring path)
- `tests/unit/domains/campaigns/test_narrative_ledger.py` (docstring path)
- `tests/unit/domains/chronicle/test_chronicle_compiler.py` (docstring path)
- `.github/workflows/test.yml` (removed 6 redundant explicit path lines)
- `.claude/agents/test-scoper.md` (Test Directory Map updated)
- `docs/testing/content_migration_test_ownership.md` (added `tests/unit/domains/` Ownership row)
- `docs/parity_ledger/combat_movement.yaml` (path citations updated, incl. COMB-310 P0)
- `docs/parity_ledger/faction.yaml` (path citations updated)
- `docs/parity_ledger/infrastructure.yaml` (path citations updated)
- `docs/parity_ledger/progression.yaml` (path citations updated)
- `docs/parity_ledger/social_narrative.yaml` (path citations updated)
- `docs/parity_ledger/strategic_cognition.yaml` (path citations updated)
- `docs/parity_ledger/substrate.yaml` (path citations updated, incl. SUB-383 P0)
- `docs/parity_ledger/world_dynamics.yaml` (path citations updated)
- `docs/optimization_audit_ledger.md` (path citations updated)
- `docs/logic_checklist_exhaustive.md` (path citations updated)
- `docs/simulation/domains/chronicle_contract.md` (path citation updated)
- `docs/guidelines/design_patterns.md` (path citation updated)
- `docs/guidelines/intentional_divergences.md` (path citations updated)
- `docs/performance/optimization_invariants.md` (path citations updated)
- `docs/engine/candidate_selection.md` (path citation updated)
- `docs/engine/authoritative_apply_contract.md` (path citation updated)
- `docs/plans/codebase_navigability_hygiene_epic.md` (path citations updated)
- `graphify-out/` (regenerated via `graphify update .`)
- (knowledge-search index cache, regenerated via `make knowledge-index-update`, not tracked
  in git as a source file)
- `staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/investigation.md` (edited
  during this ticket's Review-fix cycle, pre-dating this implement run)
- `staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/plan.md` (edited during this
  ticket's Review-fix cycle, pre-dating this implement run)
- `staging_artifacts/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING/test_plan.md` (present, read
  for verification approach; no content edit needed during this run)
- `tickets/inprogress/TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING.md` (this file — Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)

## Completion Summary
Nested all 6 stray domain-subpackage test directories (`campaigns`, `chronicle`, `culture`,
`faction`, `feature_packs`, `optimization` — 61 files) under `tests/unit/domains/` via individual
`git mv` operations, fixed the one confirmed `Path(__file__)` regression this exposed in
`test_campaign_state.py`, updated all live downstream references (CI workflow, parity ledger
P0/P1 entries, agent-facing test map, test ownership doc, and ~9 other docs), and verified with a
full test execution (not just collection) showing 713/713 passing with an exact pre/post
collection-count match. All 4 acceptance criteria are satisfied. Ready for Test/Parity/Verify
phases.
