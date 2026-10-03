# Plan: TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE

## Summary

Migrate `simq_routing_test`'s `ENABLE_ADVENTURE_ROUTING` activation off the hardcoded
`ROUTING_KEYS` special case in `tools/evaluate_simq.py` and onto the already-generic
`feature_flags:` profile-YAML mechanism (`tools/calibrate_simq.py::_load_profile_feature_flags()`)
that `urban_political.yaml` already uses for `ENABLE_SOCIAL_COOPERATION` /
`ENABLE_BELIEF_ASSIMILATION`. This is a pure harness/config mechanism refactor — no engine,
scorer, or `AdventureDecisionPhase`/`AgencyScorer` logic changes, and no existing archetype
world's flags change.

Both open questions in the ticket (UQ-1, UQ-2) are resolved by investigation with direct
evidence; this plan adds a second live empirical confirmation (seeds 123 and 456, on top of
investigation's seed 42 trial) — see §3 below. **No open question remains for a human decision.**

## Ordered Implementation Steps

1. Edit `config/simulation_quality/profiles/simq_routing_test.yaml`: append a `feature_flags:`
   block with `ENABLE_ADVENTURE_ROUTING: "ON"`, matching `urban_political.yaml`'s existing
   block style exactly (see exact diff §1 below).
2. Edit `tools/evaluate_simq.py`: delete the `ROUTING_KEYS` set (module-level constant), delete
   the `routing_flag` parameter and its env-var set/restore branch inside `_run_calibration()`,
   and delete the `routing = run_key in ROUTING_KEYS` call-site line — `_run_calibration()` keeps
   its remaining purpose (sys.argv patch + in-process `cal_mod.main()` call + restore) and is
   simplified in place, not removed (see exact diff §2 below — it is not a pointless wrapper once
   simplified, since it still centralizes the sys.argv monkey-patch/restore around the in-process
   call).
3. Re-run the 3 `simq_routing_test_seed{42,123,456}_500t` scenarios live (non-dry-run) through
   the new code path (`python3 tools/evaluate_simq.py --scenario simq_routing_test_seed<N>_500t`)
   to regenerate `data/calibration/simq_routing_test_seed<N>_500t/quality_report.json` under the
   new mechanism, replacing the stale reports that were generated under the old env-var mechanism.
4. Run `python3 -m pytest tests/simulation_quality/test_evaluate_harness.py -v` — confirm all
   pass unchanged (this file only imports `_within_band`, `_compare`, `_parse_run_key`, none of
   which are touched).
5. Run `make evaluate-full` (full re-run, all scenarios) — confirm exit 0, 0 regressions across
   the whole corpus, not just the 3 routing scenarios. This is a broader corpus-wide safety net
   on top of step 3's targeted live re-run, since this ticket touches `evaluate_simq.py` itself
   (shared infrastructure, not just `simq_routing_test`-specific content).
6. Run `make evaluate` — confirm exit 0, 0 regressions (dry-run: reads the regenerated
   `data/calibration/` reports from step 3 against `grade_anchors.json`, no engine re-run).
7. Confirm no other world's profile YAML gained `ENABLE_ADVENTURE_ROUTING` — `grep -rl
   ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` must return only
   `simq_routing_test.yaml`.
8. Add a short documentation note to `docs/simulation_quality/quality_scoring_contract.md`
   §11.6 "Standing Evaluation Harness" (see exact text §6 below) stating the harness no longer
   special-cases routing scenarios by name; `ENABLE_ADVENTURE_ROUTING` activation is a normal
   per-world profile-YAML `feature_flags:` entry like any other.
9. Update the ticket's `Implementation Notes` / `Test Summary` / `Files Changed` sections, run
   `working_log.csv` append, move ticket to `tickets/done/`, delete
   `tickets/todos/simq-corpus-tiers/TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE.md` (already
   absent from that folder as of this session — the ticket file is already staged directly under
   `tickets/inprogress/`; only `tickets/todos/simq-corpus-tiers/` folder-completion bookkeeping
   remains if other tickets in that folder are still open), move staging artifacts to
   `stored_artifacts/`, clean `data/runs/*` (calibration runs in steps 3/5/6 write raw run JSONL
   under `data/runs/<run_id>/` regardless of `--output`; these are transient and must be purged
   per the finalize checklist — but only `data/calibration/simq_routing_test_seed*` +
   `grade_anchors.json`-relevant artifacts should be *kept/committed*, not `data/runs/`).
10. No `graphify update .` needed — no `src/` or `tests/` code paths changed outside
    `tools/evaluate_simq.py` (a `tools/` script, not `src/`/`tests/`); confirm this is consistent
    with the project's stated trigger ("after modifying files under `src/` or `tests/`") before
    skipping — `tools/` is out of that trigger's stated scope.

## 1. Exact content edit — `config/simulation_quality/profiles/simq_routing_test.yaml`

Current (byte-identical to `default.yaml`):
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

New (append, matching `urban_political.yaml`'s blank-line-then-`feature_flags:` style exactly):
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

feature_flags:
  ENABLE_ADVENTURE_ROUTING: "ON"
```

Diff:
```diff
   WORLD: 1.0
   NARRATIVE: 1.0
+
+feature_flags:
+  ENABLE_ADVENTURE_ROUTING: "ON"
```

## 2. Exact diff — `tools/evaluate_simq.py`

Remove `ROUTING_KEYS` (module scope, currently lines 34-38):
```diff
 DEFAULT_ANCHORS = Path("tests/simulation_quality/fixtures/grade_anchors.json")
 CALIBRATION_ROOT = Path("data/calibration")

-ROUTING_KEYS = {
-    "simq_routing_test_seed42_500t",
-    "simq_routing_test_seed123_500t",
-    "simq_routing_test_seed456_500t",
-}
-
-
 def _within_band(actual: str, anchor: str, tolerance: int = 1) -> bool:
```

Simplify `_run_calibration()` (currently lines 65-86) — drop the `routing_flag` parameter and
the env-var set/restore branch; keep the sys.argv patch/restore, which is still its purpose:
```diff
-def _run_calibration(name: str, seed: int, ticks: int, routing_flag: bool) -> None:
+def _run_calibration(name: str, seed: int, ticks: int) -> None:
     import tools.calibrate_simq as cal_mod

     old_argv = sys.argv[:]
-    old_routing = os.environ.get("ENABLE_ADVENTURE_ROUTING")
     try:
         sys.argv = [
             "calibrate_simq",
             "--name", name,
             "--seed", str(seed),
             "--ticks", str(ticks),
         ]
-        if routing_flag:
-            os.environ["ENABLE_ADVENTURE_ROUTING"] = "ON"
         cal_mod.main()
     finally:
         sys.argv = old_argv
-        if routing_flag:
-            if old_routing is None:
-                os.environ.pop("ENABLE_ADVENTURE_ROUTING", None)
-            else:
-                os.environ["ENABLE_ADVENTURE_ROUTING"] = old_routing
```

Call site in `main()` (currently line 158, `routing = run_key in ROUTING_KEYS`, and line 161,
`_run_calibration(name, seed, ticks, routing)`):
```diff
             try:
                 name, seed, ticks = _parse_run_key(run_key)
             except ValueError as exc:
                 print(f"ERROR: {exc}", file=sys.stderr)
                 error_count += 1
                 continue
-            routing = run_key in ROUTING_KEYS
             print(f"[evaluate] Running engine: {run_key} ...", flush=True)
             try:
-                _run_calibration(name, seed, ticks, routing)
+                _run_calibration(name, seed, ticks)
             except SystemExit:
                 pass
```

**Decision on `_run_calibration()`'s continued existence:** it is NOT removed. Its remaining job
— monkey-patching `sys.argv` to simulate CLI args for the in-process `cal_mod.main()` call, and
restoring `sys.argv` afterward — is independent of the routing special case and still has a
real purpose (isolating `evaluate_simq.py`'s loop from `calibrate_simq.py`'s `argparse` CLI
surface). It is simplified (one fewer parameter, no env-var logic), not inlined/deleted, because
inlining would duplicate the `try/finally sys.argv` pattern at the call site for no benefit. This
resolves the ticket's open question about whether `_run_calibration()` "becomes a trivial
passthrough with no remaining purpose" — re-reading the function confirms it does not; the
env-var injection was only ever one of two things it did.

The `import os` at the top of `evaluate_simq.py` remains needed for other uses in the file
(`os.path.join`, `os.environ` is otherwise unused now — confirm at implementation time whether
`import os` becomes partially redundant; it is not, since `os.path.join(os.path.dirname(__file__),
"..")` at line 27 still needs it).

## 3. Live re-verification — seeds 123 and 456 (executed during planning, not deferred)

Investigation (§6) already empirically confirmed seed 42 is grade/score-identical between the
old env-var mechanism and the new profile-YAML-only mechanism. Per the ticket's own flagged
residual item (test_plan.md "Failure Modes"), seeds 123 and 456 needed the same live check. This
plan session ran that check directly (temporarily adding the `feature_flags:` block to
`simq_routing_test.yaml`, running `calibrate_simq.py --name simq_routing_test --seed <N> --ticks
500` with **no env var set**, to an isolated `--output` scratch directory so committed
`data/calibration/` reports were not touched), then reverted the YAML edit immediately after —
consistent with investigation's read-only discipline; no code/config change is left in place
from this planning session.

**Seed 123** — new mechanism vs. existing cached `data/calibration/simq_routing_test_seed123_500t/quality_report.json` (generated under the old env-var mechanism):
```
overall_score: 0.5801969405774996  ==  0.5801969405774996   (exact match)
AGENCY      A  +0.6415  events=303   (identical)
COGNITION   S  +2.8072  events=233   (identical)
COMBAT      C   0.0000  events=0     (identical)
ECONOMY     C   0.0000  events=0     (identical)
FACTION     C   0.0000  events=0     (identical)
INFORMATION C   0.0000  events=0     (identical)
NARRATIVE   S  +2.3727  events=233   (identical)
PROGRESSION C  -0.0645  events=1     (identical)
SOCIAL      C   0.0000  events=0     (identical)
WORLD       B  +0.0450  events=6     (identical)
```
Grade anchor entry for `simq_routing_test_seed123_500t` matches all 10 pillars exactly (AGENCY=A,
COGNITION=S, COMBAT=C, ECONOMY=C, FACTION=C, INFORMATION=C, NARRATIVE=S, PROGRESSION=C, SOCIAL=C,
WORLD=B) — 0 drift.

**Seed 456** — new mechanism vs. existing cached
`data/calibration/simq_routing_test_seed456_500t/quality_report.json`:
```
overall_score: 0.49533576243612387  ==  0.49533576243612387   (exact match)
All 10 pillars: grade, normalized_score, and event_count identical (AGENCY, COGNITION, COMBAT,
ECONOMY, FACTION, INFORMATION, NARRATIVE, PROGRESSION, SOCIAL, WORLD).
```
**Pre-existing note (not introduced by this ticket):** `grade_anchors.json`'s
`simq_routing_test_seed456_500t` entry states `COGNITION: S, NARRATIVE: A`, while both the old
cached report *and* the new mechanism actually produce `COGNITION: A, NARRATIVE: S` (i.e. the
anchor and the actual committed report already disagree, off by one grade step each, before any
change in this ticket). This passes `evaluate_simq.py`'s existing `_within_band(tolerance=1)`
check today and will continue to after migration — the mechanism swap does not change this
pre-existing anchor/report gap in either direction. This is out of scope for this ticket (no
regression introduced; the ticket's acceptance criterion is 0 *drift*, and there is none — the
new mechanism reproduces the exact same actual values the old mechanism already produced).

**Conclusion: all 3 seeds (42 from investigation; 123 and 456 from this plan) are
byte-identical between the two mechanisms.** No anchor drift risk identified.

## 4. No accidental flag leakage to other worlds — confirmed

`grep -rl ENABLE_ADVENTURE_ROUTING config/simulation_quality/profiles/` returns nothing today
(before this ticket's edit) — no existing profile YAML (`default.yaml`, `dungeon_crawl.yaml`,
`urban_political.yaml`) references the flag. After step 1's edit, only
`simq_routing_test.yaml` will contain it. `_load_profile_feature_flags()` reads only the
resolved profile file for the world being run (`_resolve_profile(name)` — name-based lookup, one
file per run) — there is no mechanism by which one world's profile YAML could leak a flag into
another world's run. Removing `ROUTING_KEYS` cannot leave routing OFF for `simq_routing_test`
(the profile YAML now supplies it) nor turn it ON for anything else (no other profile YAML
references it, and the flag defaults OFF per `src/domains/optimization/feature_flags.py:16` and
per `TCK-20260627-P0A-ADVENTURE-FLAG`). This satisfies the ticket's "Out of Scope" guard against
reversing `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` for any existing archetype world.

## 5. `make evaluate` (dry-run) — corpus-wide regression check

Baseline today (pre-change, confirmed in investigation): `390 pillars checked — 0 regressions —
0 missing` (1 scenario with no cached calibration data, unrelated to routing). Implementation
must re-confirm this exact "0 regressions" outcome after step 3's live re-run regenerates the 3
routing-scenario reports under the new mechanism — the pillar/scenario count may shift only if
new scenarios were added elsewhere in the corpus since investigation (unrelated to this ticket);
if the count differs, treat it as informational, not a blocker, as long as regressions=0.

## 6. Documentation — exact target and note text

**Chosen location:** `docs/simulation_quality/quality_scoring_contract.md`, §11.6 "Standing
Evaluation Harness" (currently ends after the "Anchor update workflow" list, before the `---`
separator preceding "## 12. Acceptance Criteria").

**Why this doc over `docs/guides/content_authoring.md`:** `content_authoring.md` is scoped to
world modules/compositions/scenario-template authoring (its own §§1-10 cover module YAML fields,
compositions, catalog IDs, scenario templates) — it never mentions `feature_flags:`,
`calibrate_simq.py`, or profile YAMLs at all (confirmed via grep — zero matches). By contrast,
`quality_scoring_contract.md` already documents `tools/evaluate_simq.py`'s exact mechanics in
§11.6 (the section that housed the special case being removed) and already references
`ENABLE_ADVENTURE_ROUTING` in three other places (§4.5 calibration-status note, and two
traceability-path bullets in the AGENCY section) — it is the audience-correct, topically-correct
home for this note.

**Exact text to insert** (as a new paragraph immediately after the "Anchor update workflow"
numbered list, before the `---` separator):

```markdown
**Feature-flag activation is profile-driven, not harness-driven:** `evaluate_simq.py` does not
special-case any scenario by name to decide which feature flags are active during a calibration
run. Every flag — including `ENABLE_ADVENTURE_ROUTING` — is activated the same way: by adding a
`feature_flags:` block to that world's `config/simulation_quality/profiles/<name>.yaml` (see §4.8),
read generically by `calibrate_simq.py::_load_profile_feature_flags()`. `simq_routing_test.yaml`
sets `ENABLE_ADVENTURE_ROUTING: "ON"` this way; no other archetype world's profile sets it, so
`ENABLE_ADVENTURE_ROUTING` remains OFF (default) for `urban_political`, `dungeon_crawl`, and
`default` — consistent with `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`. (Prior to
`TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE`, `simq_routing_test`'s 3 anchor scenarios were
the sole exception, activated via a hardcoded `ROUTING_KEYS` set and env-var injection inside
`evaluate_simq.py` itself; that special case has been removed.)
```

This directly satisfies Scope item 6 / Acceptance Criteria "Mechanism documented in an
appropriate doc."

## 7. Test coverage — confirmed no changes needed

`tests/simulation_quality/test_evaluate_harness.py` imports only `_within_band`, `_compare`,
`_parse_run_key` from `tools.evaluate_simq` (verified by re-reading the file's import line and
full contents at plan time). `test_routing_test_key` (parses `simq_routing_test_seed456_500t`
via `_parse_run_key`, a generic run-key regex parser unrelated to `ROUTING_KEYS`) is unaffected.
No test references `ROUTING_KEYS` or `_run_calibration` by name anywhere in the repo. **No test
file changes are required by this ticket.** Run the file as a regression check (step 4) but no
edits are anticipated; if the test run surfaces an unexpected failure, that would indicate a
gap this investigation/plan missed and must be re-diagnosed before proceeding, not silently
patched around.

## Explicit Scope Guards (carried into implementation)

- Do NOT touch `AdventureDecisionPhase`, `AgencyScorer`, or any AGENCY-pillar scoring logic —
  no files under `src/simulation_quality/scorers/` or the adventure-routing pipeline phase are
  part of this change.
- Do NOT add `feature_flags: ENABLE_ADVENTURE_ROUTING` to `urban_political.yaml`,
  `dungeon_crawl.yaml`, `default.yaml`, or any other existing archetype world's profile — verified
  absent today (§4) and must remain absent after this ticket.
- Do NOT author the new AGENCY unit-tier world (`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY`) —
  that ticket depends on this one but is separate work.

## Open Questions Requiring a Human Decision

**None.** UQ-1 and UQ-2 from the ticket are both resolved with direct evidence (investigation +
this plan's own live seed-123/456 trial). The one implementation-detail fork not explicitly
pre-decided by the ticket — whether `_run_calibration()` should be inlined/removed once
simplified — is resolved above with re-read evidence: it retains a real, non-routing purpose
(sys.argv monkey-patch/restore around the in-process `calibrate_simq.main()` call) and should be
kept, simplified rather than removed.
