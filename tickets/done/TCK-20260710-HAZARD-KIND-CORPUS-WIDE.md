---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260710-HAZARD-KIND-CORPUS-WIDE
phase: done
date: 2026-07-10
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260710-HAZARD-KIND-CORPUS-WIDE

## Title
Make `hazard_kind`/`hazard_immunities` match coverage corpus-wide, not allowlist-based

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`test_hazard_kind_matches_populating_faction_immunity` in
`tests/unit/worldassembly/test_corpus_diversity.py` currently only runs against an explicit
3-world allowlist (`HAZARD_KIND_MATCH_WORLDS = ["dungeon_crawl", "urban_political",
"generated_frontier_3_42"]`). Extend it (or add a sibling test) to run unconditionally against
every world in the calibration corpus (`data/worlds/*`, 17 worlds as of this scoping), asserting
that every populated region with `hazard_level > 0` declares a `hazard_kind` matching at least
one of its populating faction(s)' `hazard_immunities` — or is an explicitly documented accepted
exception. This is Phase 1.1 of `docs/plans/simq_development_roadmap.md`, resolving P2-O in
`docs/plans/audit_fix_plan.md`. The missing-`hazard_kind` defect class (unconditional lethal
drain because `src/worldassembly/resolver.py`'s `"PHYSICAL"` default matches no faction's
immunities) has recurred three separate times across independent sweeps (2026-06-30, 2026-07-04,
2026-07-09) precisely because coverage was reactive/allowlist-based. Test-only change.

## Scope
- Extend `test_hazard_kind_matches_populating_faction_immunity` (or add a sibling test in the
  same file) to iterate every world in the calibration corpus (`data/worlds/*` directories,
  cross-checked against `tests/simulation_quality/fixtures/grade_anchors.json`'s world-id set —
  both currently enumerate the same 17 worlds) rather than the `HAZARD_KIND_MATCH_WORLDS`
  allowlist.
- Reuse the existing helper pattern (`_load_resolved_spec`, `_faction_hazard_immunities`,
  `pytest.skip` when a world has no resolved spec on disk) already established in this file —
  do not introduce a parallel loading mechanism.
- Handle the one already-known accepted case (`town_council` at `bandit_road`, found
  independently in both `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` and
  `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`'s investigations) with an
  explicit, narrow, commented test-level exception that cites the tracking ticket for the formal
  DA ruling (P2-Q / Phase 1.2 — **not yet its own ticket as of this scoping**, see Assumptions).
  Do not add a broad or wildcard exception mechanism — one named region/faction pair only.
- If running corpus-wide surfaces a genuine new (4th+) recurrence in a currently-unlisted
  world/module, treat that as real new information: document it explicitly (e.g. reference a
  follow-up ticket in Completion Summary) rather than silently fixing it out-of-band without
  investigation, per the request's explicit instruction.
- Remove or repurpose the now-superseded `HAZARD_KIND_MATCH_WORLDS` constant once the test is
  corpus-wide (avoid leaving a dead, misleading allowlist in the file).
- Update the module docstring (lines 12-15) and any comments referencing the old allowlist scope
  to reflect corpus-wide coverage.

## Out of Scope
- Any change to `src/worldassembly/resolver.py`'s `"PHYSICAL"` hazard_kind default (working as
  designed).
- Any change to `src/world/environment.py::calculate_hazard_drain` (working as designed).
- Formally recording the permanent P2-Q DA ruling in `docs/guidelines/intentional_divergences.md`
  — that is Phase 1.2's own ticket. This ticket may add a temporary, narrow, explicitly-commented
  test-level carve-out for the one known case, but must not itself author the permanent doc
  entry.
- Redesigning `test_hazard_kind_completeness`'s broader presence-only coverage semantics (already
  ruled out of scope per this file's own comments, lines 36-38, citing investigation.md Risk 5).
- Folding any newly-covered worlds into `ANCHORED_WORLD_BANDS`, `EXPECTED_DISTINCT_POPULATED_FACTIONS`,
  or the entity-count-band tests — unrelated concerns per this file's existing comments.
- Fixing any genuinely new (previously-unknown) `hazard_kind` gap discovered by the corpus-wide
  run beyond documenting/flagging it — unless the fix is self-evidently the same narrow
  content-authoring pattern already used three times, in which case it may be included with full
  documentation of why it was in-ticket rather than deferred. Default assumption is
  surface-and-reference, not silent expansion of scope.

## Acceptance Criteria
- [ ] `test_hazard_kind_matches_populating_faction_immunity` (or its sibling) is parametrized
      over every world in `data/worlds/*` (17 worlds as of this scoping), not
      `HAZARD_KIND_MATCH_WORLDS`, and passes for all of them except the one documented exception.
- [ ] `HAZARD_KIND_MATCH_WORLDS` no longer exists as a coverage-limiting allowlist (removed or
      repurposed with a comment explaining its new role, if any).
- [ ] The `town_council`/`bandit_road` case is neither a silent pass nor a silent failure — it is
      either (a) excluded via a narrow, named, commented exception citing the P2-Q tracking
      reference, or (b) resolved because P2-Q landed first and the mechanism now matches.
- [ ] `git diff` for this ticket touches only test files (and, if applicable, a documented content
      fix for a newly-discovered defect) — no changes to `src/worldassembly/resolver.py` or
      `src/world/environment.py::calculate_hazard_drain`.
- [ ] `test_hazard_kind_completeness` (the presence-only sibling test) is unmodified in behavior.
- [ ] `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind` passes locally.
- [ ] If a genuine new recurrence is found in a previously-unlisted world, it is documented in
      Completion Summary (either as an in-ticket fix with justification, or a referenced
      follow-up ticket) — not silently absorbed.

## Related Tickets
- TCK-20260701-HAZARD-NATIVE-IMMUNITY (origin of the `hazard_kind`/`hazard_immunities` mechanism)
- TCK-20260701-HAZARD-KIND-RESOLVER-GAP
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (first corpus-wide `hazard_kind` authoring pass, 7 modules)
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP
- TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
- TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE (2nd recurrence fix; added `dungeon_crawl`/`urban_political` to the allowlist this ticket removes; also surfaced the `town_council`/`bandit_road` question as Risk #2)
- TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE (3rd recurrence fix; added `generated_frontier_3_42`; re-surfaced the same `town_council`/`bandit_road` question as Root cause 2)
- P2-Q / Phase 1.2 (`docs/plans/audit_fix_plan.md`, `docs/plans/simq_development_roadmap.md`) — not yet its own ticket as of this scoping; the formal DA ruling this ticket's test-level exception stands in for

## Related Docs
- `docs/mechanics/05_world_evolution.md` §3 "Hazard Impacts" / "Native Endurance to a Region's
  Hazard Kind" — authoritative mechanism description (unaffected by this test-only change).
- `docs/plans/audit_fix_plan.md` P2-O (this ticket's source finding) and P2-Q (the related,
  not-yet-ticketed DA ruling).
- `docs/plans/simq_development_roadmap.md` Phase 1.1 (this ticket) and Phase 1.2.
- `docs/parity_ledger/world_dynamics.yaml` WORLD-029, WORLD-060 (hazard-drain/native-endurance
  parity entries — no update expected unless a genuine new content defect is fixed in-ticket).
- `docs/guidelines/design_patterns.md` (compile-time content pattern references, if applicable).
- `docs/simulation_quality/corpus_tier_taxonomy.md` (corpus tier structure context).
- `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md` — scope added during Plan
  phase (architecture-review NEEDS_CHANGES remediation, 2026-07-11): the folder's own ordering
  rationale ("running 1.1 before 1.2 hits town_council/bandit_road as a live failure") is
  empirically disproven by this ticket's corpus-wide dry run (zero mismatches, including
  bandit_road) and is corrected here via an append-only note alongside the same correction
  already in scope for `docs/plans/simq_development_roadmap.md`'s Phase 1 section — left
  uncorrected, it would contradict the roadmap doc's own corrected text describing the same two
  tickets.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260701-HAZARD-NATIVE-IMMUNITY/investigation.md`
- `stored_artifacts/TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE/investigation.md` (Risk #2 —
  `town_council`/`bandit_road`)
- `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md`
  (Root cause 2 — same question re-surfaced)

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py` (primary edit target)
- `data/content/social/factions.yaml` (read-only reference; `_faction_hazard_immunities()` source)
- `data/worlds/*/resolved/world.resolved.yaml` (read-only; per-world resolved specs the test loads)
- `tests/simulation_quality/fixtures/grade_anchors.json` (read-only; corpus world-id cross-check)
- `src/worldassembly/resolver.py` (read-only reference only — not to be modified)
- `src/world/environment.py::calculate_hazard_drain` (read-only reference only — not to be modified)

## Assumptions / Open Questions
- "Every world in the calibration corpus" is assumed to mean the 17 world directories under
  `data/worlds/*` (excluding `world_index.json`), which as of this scoping are identical to the
  17 distinct world_ids present in `tests/simulation_quality/fixtures/grade_anchors.json`. If
  these two sources diverge by implementation time, re-verify against the live `data/worlds/`
  listing (the more authoritative of the two, since it is the actual content corpus).
- P2-Q (the `town_council`/`bandit_road` DA ruling) is confirmed **not yet its own ticket** —
  no match in `tickets/inprogress/` or `tickets/done/`, and no `town_council` entry exists yet in
  `docs/guidelines/intentional_divergences.md`. This ticket's test-level exception is therefore a
  temporary stand-in, not a formal ruling — if P2-Q lands before this ticket implements, prefer
  letting the test pass unaided (no exception needed) over adding a now-redundant carve-out.
- Some corpus worlds (`unit_faction_tension`, `unit_information_source`, `unit_selfmodel_pilot`,
  `hero_guild_routing`, `simq_routing_test`, `sandbox_world`, `crowded_frontier`,
  `resource_dense_basin`, `frontier_marches`) were never in `HAZARD_KIND_MATCH_WORLDS` and have
  unverified hazard/population content shape at scoping time — the corpus-wide test must degrade
  gracefully (0 hazardous populated regions = trivial pass; no resolved spec on disk =
  `pytest.skip`, matching the existing `_load_resolved_spec` pattern) rather than assume every
  world has relevant content.
- If a genuine new (4th+) recurrence is found, whether to fix it in-ticket (self-evident, narrow,
  same pattern) or defer to a follow-up ticket is an implementer judgment call within the Out of
  Scope guardrail above — this ticket does not pre-decide which.

## Implementation Notes

Followed the plan's 7 steps exactly, no code-level deviations.

1. **Parametrization (Step 1):** Replaced `HAZARD_KIND_MATCH_WORLDS` (3-world list) with
   `ALL_CORPUS_WORLDS = sorted(p.name for p in WORLDS_ROOT.iterdir() if p.is_dir())` in
   `tests/unit/worldassembly/test_corpus_diversity.py` — approach (a) from the plan (glob-based,
   self-updating), since filtering to directories cleanly excludes `world_index.json` with no
   added complexity. `test_hazard_kind_matches_populating_faction_immunity`'s
   `@pytest.mark.parametrize` now references `ALL_CORPUS_WORLDS`; the function body (matching
   logic, `_load_resolved_spec`, `_faction_hazard_immunities`) is untouched.
2. **Cleanup (Step 2):** Removed `HAZARD_KIND_MATCH_WORLDS` entirely (confirmed via grep — zero
   remaining references anywhere in the repo). Updated the module docstring to add item 3b
   describing corpus-wide coverage, and replaced the stale allowlist-provenance comment above the
   old constant with one describing the new glob-based, self-updating approach.
3. **Explanatory comment (Step 3):** Added a documentation-only paragraph to
   `test_hazard_kind_matches_populating_faction_immunity`'s docstring explaining the region-level
   "any populating faction" matching semantics and why `town_council`/`bandit_road` passes today
   (not a content fix), citing `docs/guidelines/intentional_divergences.md` §2.30 and
   `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`. No xfail/skip/conditional logic was added — the test
   executes identically for all 17 worlds.
4. **`audit_fix_plan.md` (Step 4):** P2-O's table row and detail-section heading marked
   `RESOLVED (2026-07-11)`; a Resolution paragraph appended to the detail section citing this
   ticket, matching the P2-M/P2-P closeout convention.
5. **`simq_development_roadmap.md` (Step 5):** Appended a "Result (landed 2026-07-11)" note under
   Phase 1.1 stating the corpus-wide test passed with 0 mismatches and no exception was needed,
   independent of Phase 1.2's ordering. Appended a "Correction (2026-07-11, post-implementation)"
   note to the existing 2026-07-10 callout box, stating the original 1.1-before-1.2 coupling claim
   is empirically disproven — the original text was preserved, not rewritten.
6. **`SEQUENCE.md` (Step 6):** Appended a correction note below the ordering table citing this
   ticket's investigation.md as the source, stating Row 1's "why this order" claim does not hold —
   the corpus-wide test's region-level "any" semantics already covered `bandit_road` independent
   of ordering. Table content preserved as historical record, per the plan's append-only
   instruction.
7. **Regression verification (Step 7):** all commands run; see Test Summary.

**Corpus-wide dry-run outcome (implementation-time, not just investigation-time):** re-running
the actual (now corpus-wide) pytest parametrization reproduced the investigation's dry run exactly
— **17/17 worlds, 45 hazardous-populated-region checks, 0 mismatches**, including all 6
`bandit_road`-containing worlds (`crowded_frontier`, `frontier_extended`,
`frontier_living_world`, `frontier_marches`, `generated_frontier_3_42`, `urban_political`). This
confirms the investigation's central finding: **no runtime exception/xfail/skip was needed** for
`town_council`/`bandit_road` — the test's pre-existing region-level "any populating faction"
matching semantics already pass that case via `bandit_company`/`merchant_league`'s immunities,
independent of the Phase 1.2 DA ruling or of implementation ordering. AC #7's contingency (document
a genuine new 4th+ recurrence) did not apply — none was found.

## Test Summary

- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k test_hazard_kind_matches_populating_faction_immunity -v`
  — 17 passed (all corpus worlds), 0 failed, 0 skipped.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind -v` — 29 passed (12
  `test_hazard_kind_completeness` + 17 `test_hazard_kind_matches_populating_faction_immunity`), 0
  failed.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k test_hazard_kind_completeness -v`
  (isolated) — 12 passed, identical case set/behavior to pre-change baseline (list and logic
  untouched).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -v -m "not slow"` — 51 passed, 17
  deselected (slow-marked population-stability tests, out of scope per Testing Rule), 0 failed —
  full-file regression confidence given shared module-level fixtures/constants.
- `pytest tests/unit/world/test_regional_consequences.py -v` — 11 passed (adjacent-file
  confirmation, byte-identical to baseline; no `src/` changes made).
- `pytest tests/unit/worldbuilding/test_world_compiler.py -k bandit_road -v` — 1 passed (adjacent
  reference test, byte-identical to baseline).
- `grep -rn "HAZARD_KIND_MATCH_WORLDS"` (whole repo) — empty, confirms full removal.
- `git diff --stat` scoped to this ticket's 4 touched files
  (`tests/unit/worldassembly/test_corpus_diversity.py`, `docs/plans/audit_fix_plan.md`,
  `docs/plans/simq_development_roadmap.md`,
  `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md`) — no `src/`, no
  `data/content/social/factions.yaml`, no `docs/parity_ledger/world_dynamics.yaml`.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py` — corpus-wide parametrization,
  docstring/comment updates, explanatory comment.
- `docs/plans/audit_fix_plan.md` — P2-O closed out to RESOLVED.
- `docs/plans/simq_development_roadmap.md` — Phase 1.1 marked done; ordering-coupling claim
  corrected (append-only).
- `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md` — ordering-rationale
  correction note appended (append-only).

## Completion Summary
`test_hazard_kind_matches_populating_faction_immunity` now runs unconditionally across the full
17-world calibration corpus (`ALL_CORPUS_WORLDS`, globbed from `data/worlds/*`) instead of the
3-world `HAZARD_KIND_MATCH_WORLDS` allowlist, which has been fully removed. The corpus-wide run
found **zero mismatches across 45 hazardous-populated-region checks**, including every
`town_council`/`bandit_road` occurrence (6 of 17 worlds) — confirming the investigation's dry-run
finding that the test's region-level "any populating faction" matching semantics already pass that
known case via `bandit_company`/`merchant_league`'s pre-existing immunities, so **no
xfail/skip/exception was added or needed** (AC #3 satisfied by outcome (b): resolved because the
mechanism already matches, not via a named carve-out). A documentation-only comment was added to
the test citing `docs/guidelines/intentional_divergences.md` §2.30 and
`TCK-20260710-TOWN-COUNCIL-HAZARD-DA` so a future reader understands why `bandit_road` passes
without mistaking it for an oversight. No genuine new (4th+) `hazard_kind` recurrence was found
(AC #7 contingency does not apply). This is a test-file-only change plus three append-only doc
closeouts (`audit_fix_plan.md` P2-O → RESOLVED, `simq_development_roadmap.md` Phase 1.1 → done
with the now-disproven 1.1-before-1.2 coupling claim corrected, and `SEQUENCE.md`'s ordering
rationale corrected) — `git diff --stat` confirms zero changes to `src/worldassembly/resolver.py`,
`src/world/environment.py`, `data/content/social/factions.yaml`, or
`docs/parity_ledger/world_dynamics.yaml`. All acceptance criteria are met; no follow-up ticket is
required.
