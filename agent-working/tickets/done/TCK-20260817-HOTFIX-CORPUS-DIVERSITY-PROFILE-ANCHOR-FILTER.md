---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260817-HOTFIX-CORPUS-DIVERSITY-PROFILE-ANCHOR-FILTER
phase: done
date: 2026-08-17
tags: [testing, bug]
---

# TCK-20260817-HOTFIX-CORPUS-DIVERSITY-PROFILE-ANCHOR-FILTER

## Title
Fix `_anchored_world_ids()` to only include real `data/worlds/` directories, not calibration-profile
overlay anchors

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Part of a batch of 7 tickets fixing genuinely pre-existing CI failures found while investigating why
GitHub Actions was failing (user request). This one: `tests/unit/worldassembly/test_corpus_diversity.py::test_module_family_anchored`
fails on CI with `FileNotFoundError: ... data/worlds/urban_political_selfmodel_probe/world.yaml`.

Root cause (confirmed via investigation): `_anchored_world_ids()` (`test_corpus_diversity.py:178-188`)
derives a "world_id" from every `grade_anchors.json` key by stripping the `_seed{N}_{ticks}t`
suffix, assuming every resulting id maps 1:1 to a `data/worlds/{id}` directory. That assumption
broke when calibration **profile overlays** (not real worlds) were introduced —
`urban_political_selfmodel_probe` and `urban_political_selfmodel_execution_probe` are profile
configs (`config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`) applied on top
of the real world `urban_political`, not their own `data/worlds/` directories. `_world_modules()`
(line 160-170) then unconditionally reads `world.yaml` with no existence check, unlike sibling
loaders in the same test suite. This is not a missing/deleted fixture — `git log --diff-filter=A
--all -- '*urban_political_selfmodel_probe*'` confirms no `world.yaml` for this name was ever added.
`urban_political`'s own modules are already covered via its own direct `urban_political_seed*`
anchor entries, so excluding profile-only ids loses no real coverage.

## Scope
- Filter `_anchored_world_ids()` (or its caller) to only include ids where
  `(WORLDS_ROOT / candidate).is_dir()` is true, mirroring the existing directory-filter pattern
  already used by `ALL_CORPUS_WORLDS` (`ai for p in WORLDS_ROOT.iterdir() if p.is_dir()`).

## Out of Scope
- Any other of the 7 CI failures in this batch (each has its own ticket).
- Adding real `data/worlds/` directories for the profile-only anchor ids — they are intentionally
  profile overlays, not real worlds, per `config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml`'s
  own header comment.

## Acceptance Criteria
- [ ] `_anchored_world_ids()` (or the call site in `test_module_family_anchored`) excludes ids that
      don't correspond to a real `data/worlds/{id}` directory.
- [ ] `test_module_family_anchored` passes.
- [ ] No real world's module-family coverage is lost (i.e. `urban_political` itself is still
      checked via its own direct anchor entries).

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Implementation Notes
Added a directory-existence filter to `_anchored_world_ids()` (`(WORLDS_ROOT / base).is_dir()`),
mirroring the existing pattern already used by `ALL_CORPUS_WORLDS`. Documented in the function's own
docstring why profile-overlay anchor ids (like `urban_political_selfmodel_probe`) don't have their
own world directory. A follow-up full-file local run surfaced further, unrelated items in the same
file — cross-checked against the real, already-downloaded CI job log and disclosed precisely, not
folded together:
- 13-14 `grade_stability`/`extended_population_stability`-family failures, all confirmed
  `@pytest.mark.slow`-marked (varies slightly run-to-run — stochastic-band flakiness among these
  slow tests themselves, not a marker-classification issue), correctly deselected by the real CI
  job's own `-m "not slow"` filter.
- 1 separate `ERROR tests/unit/worldassembly/test_corpus_diversity.py::test_trading_company_hub_composed[swamp_border_world]`
  — confirmed via direct read of its definition (line 1926) that this test carries **no**
  `@pytest.mark.slow` marker at all (only `@pytest.mark.parametrize`). It passes when run in
  isolation and does not appear in the real, downloaded CI job log
  (`1 failed, 1372 passed, 1 skipped, 36 deselected` — only this ticket's own target failure is
  present). This is disclosed honestly as a non-slow, non-reproducible-in-isolation local-run
  anomaly, plausibly related to resource contention during a ~13-minute full-file run — not a
  `@pytest.mark.slow`-deselection case, and not something this ticket's own diff caused.

The real CI job's own scoped run (`1 failed, 1372 passed, 1 skipped, 36 deselected`) confirms this
ticket's target was the only real failure in that job's actual scope — both the slow-marked family
and the 1 isolated error are out of scope for this ticket, not absorbed.

## Test Summary
- `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_module_family_anchored -v`: 1
  passed.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -q` (full file, local, no `-m` filter):
  ~76 passed, 13-14 failed (varies run-to-run), 1 error. The 13-14 failures are all confirmed
  `@pytest.mark.slow`-marked `grade_stability`/`extended_population_stability` tests, deselected on
  real CI. The 1 error (`test_trading_company_hub_composed[swamp_border_world]`) carries no
  `@pytest.mark.slow` marker, passes in isolation, and does not appear in the real downloaded CI job
  log — disclosed as a separate, non-slow, local-run-only anomaly, not folded into the slow-marker
  claim. All of the above are pre-existing and unrelated to this ticket's own fix.

## Files Changed
- `tests/unit/worldassembly/test_corpus_diversity.py` — added `is_dir()` filter to
  `_anchored_world_ids()`.

## Completion Summary
Fixed the real CI failure: `_anchored_world_ids()` now correctly excludes calibration-profile-only
anchor ids that have no real `data/worlds/` directory, matching the existing directory-filter
pattern already used elsewhere in the same file. No real world's module-family coverage is lost.
Verified against the real, downloaded CI job log that this was the sole real failure in that job's
scope. The 14 unrelated `@pytest.mark.slow` failures found during local full-file verification are
disclosed, confirmed out of scope (deselected by the real CI job's own filter), and not addressed
by this ticket.
