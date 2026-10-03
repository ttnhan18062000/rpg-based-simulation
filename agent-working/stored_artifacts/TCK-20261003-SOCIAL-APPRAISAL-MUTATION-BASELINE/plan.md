---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE

Reviewed as the ticket text by test-architecture-reviewer on 2026-10-03, with these decisions: file name
`tests/mutation/baselines/src_systems_social_appraisal_v1.json`; selection rule `import-based-one-hop`
with `target_module src.systems.social_systems.appraisal`, excluding `tests/mutation/`; record the
resolved file list and confirm it green before mutation; a FRESH positive control; v3's `stale_after`
fields plus the RELATIONSHIP-VECTOR landing as a further trigger; reputation-read mutants listed
separately as "current behaviour, catalog-CONFLICTING".

1. Resolve the selection with `tools/test_architecture/mutation_selection.py`; record files, one-hop modules and the files hash.
2. Run the selection unchanged and confirm it green (test count, time).
3. G3: probe whether the kernel runs in the selection (a read-only pytest plugin kept outside the repo) and with what `audit_mode` and tick budget. If it runs, force `audit_mode=True` and a relaxed `max_tick_budget_ms` through the scratch-run plugin only, and confirm the selection is still green.
4. Make a scratch copy of the tree with `git archive` at the measured `origin/main` SHA, outside the repo. Install `mutmut==2.5.1` with `pip --target`. Run detached with `setsid`.
5. Fresh positive control: a hand-made mutant of `appraisal.py` that a selected test must catch; it must be killed by the same runner, or the run is not trusted.
6. Run `mutmut run --paths-to-mutate src/systems/social_systems/appraisal.py`; collect results and survivor diffs.
7. Write the baseline JSON in v3's shape; section 4 of `docs/testing/social_test_report_2026-10-03.md` summarises and points at it.

Scope guards: no test or source file edited in the repo; no survivor is called a defect; party, `memory.py`, perception excluded.
