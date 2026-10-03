---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE

## Proof Plan
- level: mutation measurement over existing tests (no test added or changed)
- proof kind: a mutmut run in a scratch copy of the tree at a stated SHA; a fresh positive control
- oracle source: the existing selected tests; the record states what they do and do not catch
- expected effect: a baseline JSON with counts, survivors, selection identity and staleness fields; the baseline-record shape tests accept it
- selected commands:

| Check | Command | Expected |
|---|---|---|
| Selection green | `pytest -q -p no:cacheprovider <resolved 46 files>` | 313 passed |
| Selection green under G3 forcing | same, with the scratch probe plugin forcing `audit_mode=True` and a relaxed budget | 313 passed |
| Positive control | same runner against a scratch copy with `(public_trust * 0.7)` changed to `0.6` | fails (killed), target restored with the original sha256 |
| Mutation run | `mutmut run --paths-to-mutate src/systems/social_systems/appraisal.py --runner "python -m pytest -x -q -p no:cacheprovider -p kprobe <files>" --no-progress` | counts total = killed + survived + timeout + suspicious |
| Record shape | `pytest tests/unit/tools/test_mutation_baseline_records.py -q` | all baselines pass, including the new one |
| Diff gate | `git diff --name-only origin/main` | the only test files are `test_scenario_lane_paths.py` (C1) and the new baseline JSON |
