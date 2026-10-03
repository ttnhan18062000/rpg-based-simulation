---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE
phase: done
date: 2026-09-09
tags: [testing, architecture]
---

# TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE

## Title
`test_phase18_import_boundaries.py`'s `_DOMAINS_OBSERVABILITY_PINNED` keys grandfathered exceptions by line number — brittle, and its failure mode is diff-indistinguishable from a prohibited gate-weakening edit

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`tests/architecture/test_phase18_import_boundaries.py`'s `_DOMAINS_OBSERVABILITY_PINNED` dict keys
each grandfathered `domains -> observability` import exception by `(file_path, line_number)`. Any
unrelated code addition above a pinned import shifts its line number, breaking the pin and failing
CI for a reason that has nothing to do with the actual change — the import itself is unchanged and
still legitimate.

**This has now happened three times, per the dict's own comments**:
1. `TCK-20260905-FAME-DERIVER-LEGEND-FACT` — adding `FameExporter.export()` shifted
   `orchestrator.py`'s pinned import from line 437 to 440.
2. `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` — adding `CatalogRepository`/
   `WorldModuleRepository`/`CatalogScenarioStateBuilder` construction shifted the same file's
   pinned import from line 447 to 487.
3. Commit `3e4154ba` (hotfix, RPG Batch B/C follow-ups on `batch-c-campaign-followups`, not yet
   merged) — deleting `_scatter_catalog_entities()`, adding docstrings, and threading
   `information_source_profiles` shifted the same pinned import again, from 487 to 498. Import
   content (`src.observability.events`, `SimulationEvent`) confirmed unchanged. This ticket's
   content-keyed design supersedes that re-pin regardless of which branch lands second — a line
   shift no longer matters once the key is content, not line number.

**Why this is worse than ordinary test fragility**: the correct fix (re-pin the line number to
match reality) is diff-indistinguishable from the exact edit the Gate Integrity rule prohibits
(silently editing a gate/check to make it pass instead of fixing the underlying issue) — both are
a one-line change to `_DOMAINS_OBSERVABILITY_PINNED`. A reviewer (human or peer-review agent)
cannot tell "the import is unchanged and this is legitimate maintenance" from "the gate was
weakened to pass" without independently re-deriving the actual current line number and confirming
the import content is identical — real scrutiny cost on every occurrence, not just an inconvenience.

## Scope
- Change `_DOMAINS_OBSERVABILITY_PINNED`'s keying scheme to something stable across unrelated
  line-shifting edits — candidates: key by `(file_path, module_being_imported, tuple_of_imported_names)`
  and match any `ImportFrom` node in that file with that module/names combination (regardless of
  line), or key by a nearby stable anchor (e.g. the enclosing function name) instead of a raw line
  number.
- Preserve the existing guard: expanding the exception set (adding a NEW file/import pair) must
  still require updating this test AND `docs/audits/D14_coupling_depth.md` together — only the
  keying mechanism for existing entries changes, not the review discipline around adding new ones.
- Confirm the new scheme still correctly REJECTS an import that isn't pinned (the test's own
  negative-case behavior must be unchanged).

## Out of Scope
- Any other line-keyed pinning mechanism elsewhere in the test suite, if one exists — not surveyed
  here; file separately if found.
- The Gate Integrity rule itself — this ticket makes gate maintenance safer to distinguish from
  gate weakening, it does not change the rule.

### Scope amendment (Investigate, 2026-09-11)
- **Widened to both line-keyed dicts.** `_SYSTEMS_ENGINE_PINNED` (13 entries,
  across 5 files — corrected from 10 after Review) is also keyed by `(rel_path, lineno)` and has already
  drifted once (`TCK-20260829-HOTFIX-INTELLIGENCE-CADENCE-PIN-LINENO-DRIFT`). The Out of Scope
  survey is done: no other line-keyed pin exists anywhere in `tests/`.
- **Key is `(rel_path, module, names)` → expected count.** The count is required, because
  `intelligence.py:832` and `:904` are identical imports. It keeps the file, unlike the in-file content-keyed
  precedent `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS`, whose loop covers only three fixed files.
- **Every D14 pinned-entry citation becomes a content reference** — both the domains→observability
  rows and the 13-import systems→engine table (corrected after Review). `D14_coupling_depth.md`
  still cites `orchestrator.py:418` (the real line is 487) — the doc-coupling the ticket wants to
  preserve has already drifted silently.
- **Priority: recommend P2.** The fix is small; the risk it removes is that a reviewer cannot tell a
  legitimate re-pin from a gate-weakening edit. Three occurrences confirmed.

## Acceptance Criteria
- [x] `_DOMAINS_OBSERVABILITY_PINNED` **and `_SYSTEMS_ENGINE_PINNED`** are keyed on
      `(rel_path, module, names)` with an exact expected count, so a new duplicate or a removed
      import both fail. The key survives an unrelated line-shifting edit above them (verified
      with a real test per dict: add dummy lines above a pinned import in a `tmp_path` copy and
      confirm the pin still matches).
- [x] The test still correctly fails for a genuinely new, unpinned `domains -> observability`
      import.
- [x] A pinned `(module, names)` copied verbatim into a different file is rejected.
- [x] `TYPE_CHECKING`-guarded imports are still skipped.
- [x] Both pinned-entry sections of `docs/audits/D14_coupling_depth.md` use content references, with no
      line numbers for pinned imports and no "`(file, lineno)`-exact" wording left;
      `orchestrator.py:418` is gone.
- [x] No regression in `tests/architecture/`.

## Related Tickets
- `TCK-20260905-FAME-DERIVER-LEGEND-FACT` (first occurrence)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (second occurrence; origin of this ticket)

## Related Docs
- `docs/audits/D14_coupling_depth.md` (must stay in sync with any NEW exception added, per the
  existing convention this ticket preserves)

## Related Code Areas
- `tests/architecture/test_phase18_import_boundaries.py` (`_DOMAINS_OBSERVABILITY_PINNED`,
  `test_domains_do_not_import_observability_outside_pinned_exceptions`)

## Assumptions / Open Questions
- Whether a symbol/import-content key alone is sufficiently unambiguous (e.g. if a file somehow
  imported `SimulationEvent` from `src.observability.events` twice) is worth checking during
  Investigate — likely a non-issue in practice, but worth confirming rather than assuming.

## Implementation Notes
Investigate and Plan are complete; see
`staging_artifacts/TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE/`
(`investigation.md`, `plan.md`, `test_plan.md`). Multiplicity question answered: one real duplicate
exists (`intelligence.py:832`/`:904`). The plan keys on an exact count rather than a set. Revised after
Review NEEDS_CHANGES (13 entries, not 10; D14 systems→engine table in scope) — see investigation.md §6.

**Implemented in `tests/architecture/test_phase18_import_boundaries.py`:**
- Added a `PinnedKey = tuple[str, str, tuple[str, ...]]` alias and two shared helpers:
  `_count_boundary_imports(root_dir, module_prefix)` (walks a package and returns a `Counter` of
  `(rel_path, module, names)` for boundary-crossing, non-`TYPE_CHECKING` imports) and
  `_assert_pinned_exactly(seen, pinned, boundary_label)` (asserts every observed key is pinned at
  its exact expected count, and every pinned key was observed its exact expected count — so an
  unpinned key, an over-count new duplicate, and an under-count stale pin all fail). These are
  shared by both production tests and by the new synthetic `tmp_path` tests, which is why they
  were factored out rather than left inline per test (needed for testability of the line-shift
  claim, not a speculative abstraction).
- `_DOMAINS_OBSERVABILITY_PINNED` and `_SYSTEMS_ENGINE_PINNED` converted from
  `{(rel_path, lineno): (module, names)}` to `{(rel_path, module, names): expected_count}`.
  `test_domains_do_not_import_observability_outside_pinned_exceptions` and
  `test_systems_do_not_import_engine_outside_pinned_exceptions` now just call the two helpers.
- Re-pin history comments retired per Step 5; both dict header comments now cite this ticket and
  name any count-2 (duplicate) key so a future reader doesn't "fix" it back to 1.
- Added 9 new tests: 2 line-shift-survival tests (one per dict, synthetic `tmp_path` copy, never
  touching `src/`), 3 negative-path tests (new unpinned import, changed import content, same
  `(module, names)` copied into a different file), 3 count tests (duplicate beyond expected_count
  fails, a removed duplicate copy fails as a stale pin, a second copy of a count-1 pin fails), and
  1 `TYPE_CHECKING`-still-skipped test.
- **Deviation from the dispatched conversion (disclosed, not silent):** `_SYSTEMS_ENGINE_PINNED`
  ships with 11 unique keys (not 12) — a second real duplicate exists at `intelligence.py:84`/`:828`
  (`from src.engine.domain_logic import SimulationDomainLogic`, byte-identical at both sites,
  verified by direct read before writing the dict), on top of the `:832`/`:904` cadence duplicate
  the dispatch named. Both are `expected_count: 2`; the count sum is still 13. See
  `staging_artifacts/.../plan.md`'s new Deviations section for the full account and why the
  as-dispatched "12 keys" would have broken the test against unmodified `src/` on day one.

**`docs/audits/D14_coupling_depth.md`:** both pinned-entry sections (domains→observability,
systems→engine) converted from line-citation tables to content-reference tables (imported symbol
+ enclosing function for domains→observability; imported names + occurrence count for
systems→engine). `orchestrator.py:418` (stale since the import moved to line 487) is gone. Both
sections' "`(file, lineno)`-exact grandfather list" sentence now describes the content-keyed,
exact-count scheme and cites this ticket. Line citations outside these two sections were not
touched (out of scope per plan.md).

Ran `graphify update .` after the test-file edit (project rule: any `tests/` change); no topology
changes reported, as expected for a pure test-content change.

## Test Summary
`pytest tests/architecture/ -q` (full directory, per test_plan.md and Step 7 — not just the one
file, since other architecture tests share `_iter_py_files`/`_parse`): **109 passed**, 0 failed.
This includes both real production boundary tests running against unmodified `src/` (proving every
currently-pinned import — all 13 systems→engine + both domains→observability entries — still
matches after the key conversion) and all 9 new synthetic tests covering line-shift survival,
negative paths, duplicate counts, and the `TYPE_CHECKING` skip.

## Files Changed
- `tests/architecture/test_phase18_import_boundaries.py`
- `docs/audits/D14_coupling_depth.md`
- `staging_artifacts/TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE/plan.md` (added
  Deviations section)
- `tickets/inprogress/TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE.md` (this file)

## Completion Summary
Both line-keyed pinned-exception dicts in `test_phase18_import_boundaries.py`
(`_DOMAINS_OBSERVABILITY_PINNED`, `_SYSTEMS_ENGINE_PINNED`) are now keyed by
`(rel_path, module, names)` with an exact expected occurrence count instead of `(rel_path,
lineno)`, so a pin survives unrelated line-shifting edits while still failing on a new unpinned
import, a new duplicate of a pinned import, or a stale/removed pin. Both pinned-entry sections of
`docs/audits/D14_coupling_depth.md` were converted to matching content references, fixing a
line citation (`orchestrator.py:418`) that had already drifted stale. 9 new tests were added
covering line-shift survival, negative paths, and count edge cases; the full
`tests/architecture/` suite (109 tests) passes. Implementation deviated from the dispatch on one
point, disclosed in both this file and the plan's Deviations section: a second genuine duplicate
import was found and given `expected_count: 2`, making the final dict 11 unique keys rather than
the dispatched 12 (counts still sum to 13).
