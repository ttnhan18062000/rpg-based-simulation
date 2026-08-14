# Test Plan: TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE

## Scope of Change Under Test

- `config/simulation_quality/profiles/simq_routing_test.yaml`: add
  `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}`.
- `tools/evaluate_simq.py`: remove `ROUTING_KEYS` (lines 34-38) and the `routing_flag`
  conditional branch in `_run_calibration()` (lines 65-86), and the
  `routing = run_key in ROUTING_KEYS` call-site line (line 158).
- Documentation: add a short note to `docs/simulation_quality/quality_scoring_contract.md` (or
  `docs/guides/content_authoring.md`) confirming `ENABLE_ADVENTURE_ROUTING` is now a normal
  per-world profile-YAML flag with no scenario-name special case remaining.

No production/engine logic changes. No `AgencyScorer`/`AdventureDecisionPhase` changes. This is a
harness + config mechanism refactor only.

## Normal Flow

1. **Unit — profile flag loading is generic.**
   `tools/calibrate_simq.py::_load_profile_feature_flags("simq_routing_test")` returns
   `{"ENABLE_ADVENTURE_ROUTING": "ON"}` after the YAML edit. Verify via direct call or via
   `python3 tools/calibrate_simq.py --name simq_routing_test --seed 42 --ticks 500` (no env var
   set) printing `[calibrate_simq] Profile feature flags: {'ENABLE_ADVENTURE_ROUTING': 'ON'}`.

2. **Integration — evaluate_simq.py no longer special-cases routing keys.**
   `python3 tools/evaluate_simq.py --scenario simq_routing_test_seed42_500t` (non-dry-run) drives
   the engine via the generalized profile-YAML path only (no `ROUTING_KEYS` lookup, no env var
   set/restore). Confirm the run completes and produces a `quality_report.json`.

3. **Regression — no anchor drift.**
   `make evaluate --dry-run` (reads cached `data/calibration/*/quality_report.json` against
   `tests/simulation_quality/fixtures/grade_anchors.json`) exits 0 with 0 regressions across all
   scenarios, including the 3 `simq_routing_test_seed{42,123,456}_500t` entries — this is the
   ticket's core acceptance criterion (no grade drift from a pure mechanism swap).

4. **Full re-run — no regressions end-to-end.**
   `make evaluate` (non-dry-run, full re-run) exits 0 with 0 regressions. This actually re-runs the
   3 routing-test scenarios through the new mechanism and re-diffs against anchors, giving a live
   (not cached) confirmation.

## Edge Cases

- **`--dry-run` with stale cached reports from the *old* env-var mechanism**: since `--dry-run`
  only reads existing `data/calibration/*/quality_report.json` files, it will pass even before the
  live re-run happens (as demonstrated in investigation: baseline dry-run today already shows 0
  regressions using pre-existing cached reports). This is expected and does not by itself prove
  the new mechanism works — criterion 4 (live full re-run) is required to prove that.
- **A profile YAML with no `feature_flags:` key at all** (e.g. `default.yaml`, `dungeon_crawl.yaml`)
  must continue to return `{}` from `_load_profile_feature_flags()` and must not error — unaffected
  by this change, but should be spot-checked since `_run_calibration()`'s signature changes (one
  fewer parameter).
- **`--scenario` filtering in `evaluate_simq.py`** (e.g.
  `--scenario simq_routing_test_seed42_500t`) must still work after removing `ROUTING_KEYS` — the
  scenario-key lookup against `grade_anchors.json` is unrelated to the routing special case and
  must not be accidentally deleted alongside it.

## Failure Modes

- **Grade drift on any `simq_routing_test_*` anchor**: would indicate the two mechanisms are not
  actually equivalent (e.g. flag-value string-casing mismatch, or a load-order bug where profile
  YAML flags get applied after state construction rather than before). Investigation's live A/B
  trial (see investigation.md §6) found no such drift for seed 42; re-verify for seed 123 and 456
  during implementation since only one seed was empirically trialed during investigation (chosen
  as representative; the mechanism has no seed-dependent branching, so this risk is low but not
  zero).
- **Any other existing world accidentally gaining `ENABLE_ADVENTURE_ROUTING=ON`**: must not happen
  — only `simq_routing_test.yaml` gets the new `feature_flags:` entry. `urban_political.yaml`,
  `dungeon_crawl.yaml`, and `default.yaml` must remain unchanged (out of scope: reversing the
  `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` ruling for any other world).
- **Dead/unreachable code left behind**: acceptance criteria explicitly require `ROUTING_KEYS` and
  the `routing_flag` branch to be removed or made unreachable, not left as misleading dead code —
  a partial removal (e.g. leaving `ROUTING_KEYS` defined but unused) would fail review even if
  tests pass.

## Regression-Prone Paths

- `tests/simulation_quality/test_evaluate_harness.py` — run to confirm `_within_band`, `_compare`,
  `_parse_run_key` (including `test_routing_test_key`, which parses the
  `simq_routing_test_seed456_500t` key shape) are untouched by the `_run_calibration`/`ROUTING_KEYS`
  removal. Expected: all pass unchanged (these functions are independent of the routing special
  case).
- Any test under `tests/simulation_quality/` or `tests/integration/` that imports
  `tools.evaluate_simq` or `tools.calibrate_simq` directly — repo-wide grep in investigation
  confirmed only `test_evaluate_harness.py` imports from `tools.evaluate_simq`, and no test imports
  `_run_calibration` or `ROUTING_KEYS` by name.
- `make evaluate` / `make evaluate-full` Makefile targets — confirm they still resolve and exit 0
  after the `_run_calibration()` signature change (one fewer positional arg internally; the CLI
  surface of `evaluate_simq.py` itself is unchanged).

## Commands To Run (implementation phase)

```
python3 -m pytest tests/simulation_quality/test_evaluate_harness.py -v
python3 tools/evaluate_simq.py --scenario simq_routing_test_seed42_500t
python3 tools/evaluate_simq.py --scenario simq_routing_test_seed123_500t
python3 tools/evaluate_simq.py --scenario simq_routing_test_seed456_500t
make evaluate            # full re-run, all scenarios, must exit 0
make evaluate --dry-run  # cached-data diff, must exit 0, 0 regressions
```
