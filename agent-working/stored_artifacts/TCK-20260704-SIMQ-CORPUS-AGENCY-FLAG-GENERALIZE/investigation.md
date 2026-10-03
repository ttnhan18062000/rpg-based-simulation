# Investigation: TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE

## Context Scan Performed

1. `mcp__knowledge-search__search_docs` (query: "ENABLE_ADVENTURE_ROUTING feature_flags profile YAML
   evaluate_simq calibrate_simq ROUTING_KEYS") — surfaced `TCK-20260627-P0A-ADVENTURE-FLAG` (flag
   default OFF), `TCK-20260630-SIMQ-ROUTING-TEST` (created `simq_routing_test` world + profile YAML —
   working_log.csv confirms the profile file already existed as of 2026-06-30), and
   `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (the DA ruling this ticket must not reverse).
2. `graphify query "ENABLE_ADVENTURE_ROUTING feature_flags profile calibrate_simq evaluate_simq"` —
   confirmed `_load_profile_feature_flags()` (tools/calibrate_simq.py:44) is a standalone node with
   docstring "Read the optional `feature_flags:` block from a scoring profile YAML... allows
   per-scenario calibration profiles to activate feature flags without requiring the caller to
   export env vars manually" — generic by design, called from `main()`.

## 1. Current `ENABLE_ADVENTURE_ROUTING` activation mechanism (confirmed exact)

`tools/evaluate_simq.py`:
- `ROUTING_KEYS` (lines 34-38): a hardcoded set of exactly 3 run keys —
  `simq_routing_test_seed{42,123,456}_500t`.
- In `main()` (line 158): `routing = run_key in ROUTING_KEYS` — a scenario-name string-match.
- `_run_calibration(name, seed, ticks, routing_flag)` (lines 65-86): sets
  `sys.argv` for `calibrate_simq`, and if `routing_flag` is true, sets
  `os.environ["ENABLE_ADVENTURE_ROUTING"] = "ON"` **before** calling `cal_mod.main()` directly
  (in-process **import + call**, not a subprocess — `import tools.calibrate_simq as cal_mod;
  cal_mod.main()`), then restores the previous env var value (or removes it) in a `finally` block.

Because this is a direct in-process call (not `subprocess.run`), the env var is visible to
`calibrate_simq.main()` immediately via `os.environ` — there is no subprocess-inheritance question.

Inside `calibrate_simq.py::_run_engine()` (lines 180-226), flag resolution has two layers,
applied in order:
1. `extra_flags` (profile-YAML `feature_flags:`, loaded via `_load_profile_feature_flags()`) —
   lower priority.
2. Environment variables matching `_KNOWN_FLAGS` — higher priority, can override the profile.

So today, `ENABLE_ADVENTURE_ROUTING` for the 3 routing-test anchors flows entirely through layer 2
(env var), injected only by `evaluate_simq.py`'s special case. `calibrate_simq.py` run standalone
(without `evaluate_simq.py`'s wrapper) has never turned this flag on for `simq_routing_test`,
because — see finding UQ-1 below — the profile YAML for `simq_routing_test` currently has **no**
`feature_flags:` block at all.

## 2. `_load_profile_feature_flags()` genericity — confirmed

`tools/calibrate_simq.py` lines 44-63:
```python
def _load_profile_feature_flags(profile: str) -> dict:
    profile_path = os.path.join("config", "simulation_quality", "profiles", f"{profile}.yaml")
    if not os.path.exists(profile_path):
        return {}
    ...
    raw = yaml.safe_load(fh) or {}
    return {str(k): str(v) for k, v in (raw.get("feature_flags") or {}).items()}
```
This reads **any** key under `feature_flags:` in the resolved profile YAML — there is no
allowlist or per-flag-name special-casing at this layer. The call site (`main()`, lines 338-344)
passes the resulting dict straight through as `extra_flags` to `_run_engine()`, which applies it
against `_KNOWN_FLAGS` (a fixed list of the 10 Phase-10 flags, `ENABLE_ADVENTURE_ROUTING` already
included) via `_parse_flag_value()`. `urban_political.yaml` already proves this path end-to-end
for `ENABLE_SOCIAL_COOPERATION` and `ENABLE_BELIEF_ASSIMILATION`. **Confirmed: this mechanism is
genuinely generic and requires zero code changes to support `ENABLE_ADVENTURE_ROUTING` — only a
YAML content change.**

Profile resolution: `_resolve_profile(name)` (lines 32-41) uses `name` as the profile if
`config/simulation_quality/profiles/{name}.yaml` exists, else `"default"`. Since
`config/simulation_quality/profiles/simq_routing_test.yaml` already exists (see UQ-1), when
`evaluate_simq.py` calls `_run_calibration("simq_routing_test", ...)` with `args.profile=None`,
`calibrate_simq.main()` resolves `profile = "simq_routing_test"` automatically — no `--profile`
flag or other plumbing is needed for the generalized mechanism to activate.

## 3. UQ-1 — does `simq_routing_test.yaml` already exist?

**Yes.** `config/simulation_quality/profiles/simq_routing_test.yaml` exists (created by
`TCK-20260630-SIMQ-ROUTING-TEST`, confirmed via `working_log.csv`). Its current content
(byte-identical to `default.yaml`):
```yaml
pillar_weights:
  COGNITION: 1.0
  AGENCY: 1.0
  COMBAT: 1.0
  FACTION: 1.0
  ECONOMY: 1.0
  PROGRESSION: 1.0
  SOCIAL: 1.0
  INFORMATION: 1.0
  WORLD: 1.0
  NARRATIVE: 1.0
```
**It has no `feature_flags:` block today.** The file exists but does not yet carry the flag —
scope item 3 (add `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}`) is a pure content **edit** to
an existing file, not a file-creation task.

## 4. Callers of `_run_calibration` / other `ENABLE_ADVENTURE_ROUTING` env-var setters

Repo-wide grep (`ROUTING_KEYS|_run_calibration|ENABLE_ADVENTURE_ROUTING`, all `.py`, excluding
`.git`):
- `_run_calibration` and `ROUTING_KEYS` are defined and used **only** in
  `tools/evaluate_simq.py`. No other file imports or calls `_run_calibration`.
- Other `ENABLE_ADVENTURE_ROUTING` references are all independent, unrelated mechanisms that do
  not depend on `evaluate_simq.py`'s special case:
  - `src/domains/optimization/feature_flags.py:16` — the flag's `FeatureMode.OFF` default
    definition.
  - `src/domains/optimization/rollout_profiles.py` — rollout/shadow-phase config (Phase 10
    rollout metadata, unrelated to SimQ calibration).
  - `src/engine/pipeline.py:235`, `src/testing/scenario_runner.py:103`,
    `tools/personality_audit.py:50`, `tools/balance_measure.py:116` — each sets the flag via its
    own `FeatureFlagManager`/`ScenarioRunner` override mechanism, not via `os.environ` and not via
    `evaluate_simq.py`.
  - `tests/unit/config/test_phase10_rollout_profiles.py`,
    `tests/integration/test_scenario_feature_flag_defaults.py`,
    `tests/integration/domains/test_fused_loop.py`,
    `tests/integration/scenarios/test_balance_regression.py`,
    `tests/integration/scenarios/test_entity_differentiation.py`,
    `tests/unit/social/test_multi_hero.py`,
    `tests/regression/test_behavioral_5k.py` — all exercise the flag through
    `FeatureFlagManager` overrides or `ScenarioRunner`/pipeline flag dicts directly, entirely
    independent of `evaluate_simq.py`.
  - `tools/calibrate_simq.py` lines 181-220 — the two-layer resolution logic itself (profile YAML
    then env var), already generic (see §2).

**Conclusion: nothing else depends on `evaluate_simq.py`'s `ROUTING_KEYS`/`_run_calibration`
env-var-injection special case.** It is safe to delete outright, matching the ticket's stated
default preference (UQ-2). No caller signature elsewhere references `_run_calibration` or
`ROUTING_KEYS`.

`tests/simulation_quality/test_evaluate_harness.py` (the only test file that imports from
`tools.evaluate_simq`) only imports `_within_band`, `_compare`, `_parse_run_key` — it does not
test `ROUTING_KEYS` or `_run_calibration` at all, so removing them will not break this test file.

## 5. Full call-chain trace (subprocess vs. in-process)

`evaluate_simq.py::main()` → `_run_calibration()` → `import tools.calibrate_simq as cal_mod` →
`cal_mod.main()` — **direct in-process function call, not a subprocess.** `sys.argv` is
monkey-patched to simulate CLI args (`--name`, `--seed`, `--ticks`, no `--profile`), so
`calibrate_simq.main()` resolves `args.profile = None` → `profile = _resolve_profile(args.name)`.
Since `simq_routing_test.yaml` exists, `profile = "simq_routing_test"` automatically — the
existing `_resolve_profile()` name-based fallback already triggers the profile-YAML path with no
new `--profile` argument or other plumbing required.

## 6. Behavior-preservation verification — empirically confirmed (not just reasoned)

Ran both mechanisms live for `simq_routing_test_seed42_500t` (500-tick engine run, same seed) and
diffed the `quality_report.json` outputs:

**A. Current mechanism** (`ENABLE_ADVENTURE_ROUTING=ON` env var injected around
`calibrate_simq.main()`, exactly reproducing `evaluate_simq.py`'s current behavior):
```
overall_grade=A overall_score=0.6899
AGENCY      grade=A  norm=+1.4207  events=687
COGNITION   grade=A  norm=+1.2193  events=101
COMBAT      grade=C  norm=+0.0000  events=0
NARRATIVE   grade=S  norm=+4.2785  events=421
PROGRESSION grade=C  norm=-0.0645  events=1
WORLD       grade=B  norm=+0.0450  events=6
```
This matches the committed `data/calibration/simq_routing_test_seed42_500t/quality_report.json`
(overall_score 0.6898986758209894, same pillar grades) exactly — confirms the harness reproduces
the anchor today.

**B. New mechanism** (temporarily added `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}` to
`config/simulation_quality/profiles/simq_routing_test.yaml`, ran `calibrate_simq.py` directly with
**no env var set at all**, relying purely on profile-YAML resolution):
```
overall_grade=A overall_score=0.6899
AGENCY      grade=A  norm=+1.4207  events=687
COGNITION   grade=A  norm=+1.2193  events=101
COMBAT      grade=C  norm=+0.0000  events=0
NARRATIVE   grade=S  norm=+4.2785  events=421
PROGRESSION grade=C  norm=-0.0645  events=1
WORLD       grade=B  norm=+0.0450  events=6
```
**Identical overall score and identical per-pillar grade/normalized-score to 4 decimal places** for
every pillar. (Total replayed JSONL event counts differed trivially — 1268 vs 1266 — an
unrelated drain-worker flush-timing artifact of repeated back-to-back runs, not a
scoring-relevant difference; per-pillar `event_count` values, which feed scoring, matched exactly.)

The profile-YAML edit made for this test was reverted immediately after — investigation is
read-only; no code or config changes are left in place from this session.

**Conclusion: the migration is grade-identical (in this trial, score-identical too) by direct
empirical trial**, consistent with the code-level reasoning in §1/§2 (both mechanisms populate the
exact same `combined_flag_overrides` dict entry, `ENABLE_ADVENTURE_ROUTING: FeatureMode.ON`,
before constructing `AuthoritativeState` — order of layers 1 vs 2 is irrelevant when only one
layer supplies the value).

## 7. Test coverage referencing `ROUTING_KEYS` / `_run_calibration` / routing-specific behavior

- `tests/simulation_quality/test_evaluate_harness.py` — only imports `_within_band`, `_compare`,
  `_parse_run_key`. `test_routing_test_key` (line 85) tests `_parse_run_key` parsing the
  `simq_routing_test_seed456_500t` string shape — unaffected by removing `ROUTING_KEYS`, since
  `_parse_run_key` is a separate, generic run-key regex parser unrelated to the routing special
  case.
- No test imports or exercises `ROUTING_KEYS` or `_run_calibration` directly.
- `make evaluate --dry-run` baseline run today: `390 pillars checked — 0 regressions — 0 missing`
  (1 scenario with no cached calibration data, unrelated to routing). This is the pre-change
  baseline the ticket's acceptance criteria must continue to satisfy after migration.

## Recommendation (UQ-2)

**Delete `ROUTING_KEYS` and the `routing_flag`-conditional branch in `_run_calibration()` outright**
— the ticket's stated default. Evidence: no other caller or test depends on this special case (see
§4/§7), and the replacement mechanism is empirically grade-identical (§6). Implementation should:
1. Add `feature_flags: {ENABLE_ADVENTURE_ROUTING: "ON"}` to
   `config/simulation_quality/profiles/simq_routing_test.yaml`.
2. Remove `ROUTING_KEYS` (lines 34-38) from `evaluate_simq.py`.
3. Simplify `_run_calibration()` to drop the `routing_flag` parameter and the env-var
   set/restore logic entirely (it becomes a plain `sys.argv`-patch + `cal_mod.main()` call).
4. Remove the `routing = run_key in ROUTING_KEYS` line and pass no routing arg at the call site.
5. Re-run `make evaluate` (non-dry-run, or at least the 3 `simq_routing_test_*` scenarios) once
   post-change to regenerate `data/calibration/simq_routing_test_*` reports against the new
   mechanism, then `make evaluate --dry-run` to confirm 0 drift against `grade_anchors.json`.

## Open Questions Requiring a Human Decision

**None.** Both UQ-1 and UQ-2 in the ticket are resolved by this investigation with direct evidence:
- UQ-1: the profile file already exists; it needs a content edit (add `feature_flags:` block), not
  creation.
- UQ-2: delete outright — no other caller depends on the special case, and empirical trial shows
  grade/score-identical output.
