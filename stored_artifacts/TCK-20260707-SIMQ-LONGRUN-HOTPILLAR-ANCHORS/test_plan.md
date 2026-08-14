---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS
artifact_type: test_plan
tags: [simulation-quality, corpus, calibration, agency, faction, cognition, stasis]
---

# Test Plan — TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS

## Regression Surface
This is a data-only ticket (new calibration artifacts + fixture entries + key-list additions); no
scorer, hub, or engine source changes. The regression surface is therefore "does everything that
already passes keep passing," grouped by category:

**Unit — SimQ scorer/accumulator/report (must all still pass unmodified):**
- `tests/simulation_quality/test_agency_scorer.py`
- `tests/simulation_quality/test_cognition_scorer.py`
- `tests/simulation_quality/test_faction_scorer.py`
- `tests/simulation_quality/test_social_scorer.py`
- `tests/simulation_quality/test_accumulator.py`
- `tests/simulation_quality/test_report.py`
- `tests/simulation_quality/test_weights.py`
- `tests/simulation_quality/test_timegate_penalties.py` (covers the `stasis_N` one-shot-cap fix
  `INFRA-237`'s divergence_note documents — must stay green since this ticket may exercise long
  `stasis_N` streaks for the first time in `hero_guild_routing`/`simq_routing_test` at 1000t)

**Integration — hub, persistence, harness:**
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_quality_hub_event_translation.py`
- `tests/simulation_quality/test_persistence.py`
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_scenario_coverage.py`
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (`INFRA-262`) — must stay green
  whether or not Scope item 3 adds a `unit_faction_tension.yaml` profile; if one is added, this test
  (and its fixture `tests/simulation_quality/fixtures/expected_world_flag_state.json`) must be
  updated in the same change, not left to drift.

**Corpus/world-content (indirectly relevant — confirms the 4 prerequisite tickets' fixes hold under
this ticket's new long-run runs):**
- `tests/unit/worldassembly/test_corpus_diversity.py` — specifically
  `test_population_stability[urban_political]` is **already `xfail(strict=True)`** (per
  `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`), tracking the open
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` defect. This test must remain `xfail` (not newly
  fail in a different way, not newly pass unexpectedly without the tracking ticket having landed) —
  an unexpected pass here would mean `strict=True` fails the suite and is itself a signal worth
  investigating before trusting this ticket's `urban_political` 2000t SOCIAL data.

**Full slow-anchor regression (existing 11 keys must still pass with unmodified anchors):**
- `pytest tests/simulation_quality/test_grade_regression.py -m slow` — all 11 pre-existing
  `SLOW_ANCHOR_KEYS` must stay within ±1 band of their committed anchors. This requires the 11
  existing `data/calibration/{run_key}/quality_report.json` reports to still be present (they are
  currently committed) — this ticket must not delete or regenerate them unless intentionally
  re-verifying, in which case any drift must be treated as a real regression per the existing anchor
  convention, not silently absorbed.

## New Tests Required
Per this ticket's data-only mechanism, "new tests" are new fixture entries + key-list string
additions — no new test *functions* are needed (both `test_grade_within_anchor_band_long_run` and
`test_grade_anchor_file_exists_and_valid` are already parametrized generically over
`SLOW_ANCHOR_KEYS`/`grade_anchors.json` keys). The concrete additions:

1. **New anchor keys in `SLOW_ANCHOR_KEYS`** (`tests/simulation_quality/test_grade_regression.py`,
   after line 118), one per Plan-phase-decided seed × world × tick combination, minimum set implied
   by Scope item 2:
   - `unit_selfmodel_pilot_seed{N}_1000t` (at least 1)
   - `unit_faction_tension_seed{N}_1000t` (at least 1)
   - `unit_faction_tension_seed{N}_2000t` (at least 1)
   - `hero_guild_routing_seed{N}_1000t` (at least 1)
   - `simq_routing_test_seed{N}_1000t` (at least 1)
   - `urban_political_seed{N}_2000t` (at least 1)
   - Category: regression anchor (parametrized, not a bespoke test function).
   - Verifies: each new key's committed grade snapshot stays within ±1 band on future runs — this is
     the actual regression-guard artifact of the ticket, exercised automatically by
     `test_grade_within_anchor_band_long_run` once the key exists in both `SLOW_ANCHOR_KEYS` and
     `grade_anchors.json`.
   - Lives at: `tests/simulation_quality/test_grade_regression.py` (key list) +
     `tests/simulation_quality/fixtures/grade_anchors.json` (grade dict) +
     `data/calibration/{run_key}/quality_report.json` (source-of-truth calibration artifact, git-
     committed per the existing convention).

2. **Structural sanity — implicit, already covered.**
   `test_grade_anchor_file_exists_and_valid` (line 242) already asserts every entry in
   `grade_anchors.json` has exactly 10 pillar grades, all in `GRADE_ORDER` — this will automatically
   validate the new entries' structural correctness with no code change. No new assertion needed.

3. **Population-erosion cross-check (new, ad hoc — not a committed pytest test, a Plan/Implement-
   phase verification step).** Before trusting `urban_political_seed{N}_2000t`'s SOCIAL grade, cross-
   reference the calibration run's entity-alive count (from the underlying
   `data/runs/{run_id}/` telemetry or an equivalent count derivable from `simulation_events.jsonl`)
   against `test_population_stability`'s 60% floor at whatever tick count is available. This is not
   a new committed test — `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` already owns the
   population-stability regression guard — but the Implementation Notes / `eval_matrix_results.md`
   write-up for Hypothesis 4 must state the observed alive-percentage explicitly, not just the SOCIAL
   grade in isolation, so the confound documented in investigation.md Risk 1 is traceable.

## Scoped Pytest Commands
```bash
# Fast scorer/hub/persistence/harness regression (must be 0 new failures):
.venv/bin/python3 -m pytest tests/simulation_quality/ -m "not slow" -v

# Slow anchor regression — existing 11 + this ticket's new keys, once committed:
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -m slow -v

# Corpus population-stability guard (confirm urban_political stays the known xfail, nothing new breaks):
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -v

# Feature-flag guardrail (confirm unit_faction_tension profile decision didn't silently break the fixture):
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v

# AC-mandated full harness checks (per ticket Scope item 6 — run late, after all anchors committed):
make evaluate        # --dry-run: diffs committed data/calibration/ reports, no engine re-run
make evaluate-full    # re-runs the ENTIRE anchor corpus (all keys, not just fast) — expect long runtime
```
Do **not** run bare `pytest tests/` — scope stays within `tests/simulation_quality/` and the two named
corpus/guardrail files above, per repo testing rule.

## Anti-Drift Test Guards
- **`test_grade_within_anchor_band` (fast suite) must show zero drift on the 5 target worlds' 200t/
  500t anchors.** Since this ticket only adds new *long-run* keys, none of the existing fast anchors
  for `unit_selfmodel_pilot`, `unit_faction_tension`, `hero_guild_routing`, `simq_routing_test`, or
  `urban_political` should move — any fast-anchor drift while adding a slow anchor would indicate an
  unintended cross-run interaction (e.g., a shared mutable config file edited incorrectly) and must
  block the ticket, not be waved through as "expected long-run behavior."
- **`test_timegate_penalties.py::TestAgencyTimegate` must stay green** — this is the test that
  guards the exact `stasis_N` one-shot-cap fix (`INFRA-237`) whose behavior at 1000t on
  `hero_guild_routing`/`simq_routing_test` is one of this ticket's own open hypotheses. If this
  ticket's long-run AGENCY data shows unexpected decay, checking whether this specific test still
  passes is the fastest way to rule in/out a `stasis_N` regression vs. a content/mechanics finding.
- **`test_population_stability[urban_political]` must remain `xfail`, not newly pass or newly fail
  differently.** An unexpected state change here (pass, or a different failure tick/percentage) is a
  signal that either the collapse ticket landed concurrently (re-verify prerequisites) or this
  ticket's own changes somehow touched world content — neither should happen from a data-only
  anchor-addition ticket.
- **`INFRA-262`'s guardrail fixture (`expected_world_flag_state.json`) must reflect the actual Scope
  item 3 decision.** If no profile is created, the fixture's existing `unit_faction_tension`
  default-fallback entry needs no change and the guardrail test's pass is itself the anti-drift
  signal that no profile silently appeared. If a profile *is* created, the guardrail test must be
  updated in the same commit — a red guardrail here after this ticket is the drift signal to catch
  a forgotten fixture update.
- **`SLOW_ANCHOR_KEYS` must gain exactly the keys the Plan phase commits to — no more, no less.**
  Cross-check the final `SLOW_ANCHOR_KEYS` list length against `plan.md`'s stated seed/world/tick
  grid before considering the ticket done; a silent extra or missing key is the most likely
  copy-paste drift failure mode for this exact mechanism (precedent: every prior
  `SLOW_ANCHOR_KEYS`/`FAST_ANCHOR_KEYS` addition ticket has been a simple list-append, and omissions
  there are easy to miss since `pytest.skip` — not a failure — is what happens when a
  `grade_anchors.json` entry exists without a matching calibration report, or vice versa).
