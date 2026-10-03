---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
artifact_type: test_plan
tags: [feature-flags]
---

# Test Plan — TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

## Regression Surface

All commands below were run this session with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest ...` (the worktree's bare
`python3` lacks `pydantic`, a pre-existing, unrelated environment gap — same substitution the
combat-engagement sibling ticket used).

**Unit**
- `tests/unit/cognition/test_phase2_self_model_phase.py` — direct `SelfModelUpdatePhase`/service
  unit coverage. Re-ran combined with the allowlist test below: **12 passed**.
- `tests/unit/optimization/test_component_patches.py` — `SelfModelPatch` durable-materialization
  coverage (not independently re-run this session; last confirmed passing at
  `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`'s own Test Summary, 14 passed combined with
  the phase test above).
- `tests/unit/config/test_phase10_feature_flags.py` — `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist; must
  continue to reject `ENABLE_SELF_MODEL_COGNITION` as not-ON-default under the expected "keep OFF"
  outcome. Re-ran: **12 passed** (combined with the phase test above).
- `tests/unit/worldassembly/test_corpus_diversity.py -k unit_selfmodel_pilot` — population-stability
  guard for the one shipped-ON world (not independently re-run this session; last confirmed passing
  at that world's own ticket close).

**Integration**
- `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b or belief"` — the
  cross-tick-boundary Branch B proof
  (`test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`) and
  siblings. Re-ran: **7 passed, 3 deselected**.
- `tests/integration/test_world_profile_feature_flag_guardrail.py` — all 7 test functions, including
  T5's documented `urban_political` exception. Re-ran full file: **67 passed**.
- `tests/integration/test_scenario_feature_flag_defaults.py` — a second copy of the
  `_DELIBERATE_ON_DEFAULT_FLAGS` allowlist (per `rollout_flag_decisions_m1.md`'s own disclosed
  "three independently-maintained copies" finding); not independently re-run this session, scope it
  in Implement/Verify per the combat-engagement sibling's own precedent (Step 6 there ran all three
  copies together).
- `tests/certification/test_phase10_enhanced_determinism_parity.py` — third allowlist copy; same
  status as above.
- `tests/integration/scenarios/test_balance_regression.py -k adventure_routing_defaults_off` —
  `ENABLE_ADVENTURE_ROUTING`'s own default-OFF sentinel (`DEV-002`'s verification path), relevant
  because this ticket's AC2 resolution rests on that flag having zero live gating call sites; a
  failure here (flag default flipped) would not itself change AC2's static-analysis finding but
  would be a signal to re-verify the grep result. Not independently re-run this session — in scope
  for Implement.

**Simulation Quality (grade-anchor regression)**
- `tests/simulation_quality/test_grade_regression.py -k selfmodel` — the two permanent grade-anchor
  probe tests (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
  `test_urban_political_selfmodel_execution_isolated_grade_anchor`) plus 4 other `selfmodel`-matched
  entries (`unit_selfmodel_pilot_seed{42,123,456}_200t` band checks live inside the same
  parametrized suite under a different `-k` match, and `unit_selfmodel_pilot_seed42_1000t`'s
  tolerance-guard test). Re-ran: **6 skipped** — `data/calibration/{run_key}/quality_report.json`
  absent locally (gitignored/ephemeral, confirmed empty this session), not a failure. **Producing a
  fresh calibration report for at least the two probe-profile run_keys
  (`urban_political_selfmodel_probe_seed42_200t`,
  `urban_political_selfmodel_execution_probe_seed42_200t`) and re-running this file un-skipped is
  the primary way this ticket satisfies AC1's "run and documented" requirement** — see New Tests
  Required below (not a new test, but the concrete trial-execution step this ticket's job actually
  is).

## New Tests Required

Per AC1 ("a real corpus-profile ON trial is run and documented") and AC2 (the combination
question): this ticket is fundamentally evidence-gathering, not a source-code change, mirroring the
combat-engagement sibling's own precedent ("New Tests Required: None... the trial itself is not a
pytest artifact"). No new pytest test is strictly required to satisfy AC1/AC3. One optional,
genuinely valuable addition for Plan's consideration:

- **Test name**: `test_enable_adventure_routing_has_no_live_gating_call_site` (or similarly named)
- **Category**: architecture guard (static analysis, not a runtime scenario)
- **What it verifies**: greps `src/` for `is_enabled("ENABLE_ADVENTURE_ROUTING")` /
  `get_flag_mode("ENABLE_ADVENTURE_ROUTING")` / `run_phase(..., feature_flag="ENABLE_ADVENTURE_ROUTING")`
  and asserts zero matches outside `feature_flags.py`'s own registration — turning this
  investigation's AC2 resolution (currently a prose finding in `docs/engine/known_limitations.md`
  §1.5 and this ticket's own investigation.md) into a standing regression guard. If a future ticket
  ever re-wires `ENABLE_ADVENTURE_ROUTING` to gate something again, this test fails loudly and forces
  an explicit update to `known_limitations.md` §1.5's claim, rather than letting the doc silently go
  stale the way the sibling `_DELIBERATE_ON_DEFAULT_FLAGS` triple-copy problem already demonstrates
  can happen with unenforced claims in this codebase.
- **Where it should live**: `tests/unit/config/test_phase10_feature_flags.py` (co-located with the
  existing allowlist tests) or a new `tests/architecture/` guard file if one exists for this class of
  static check — confirm the existing convention before choosing (not yet confirmed this session;
  Implement's job).
- **Not required to satisfy any Acceptance Criterion literally** — AC2 only requires the combination
  question be "resolved, not left open again," which this investigation's static finding + doc update
  already does. This test is a durability improvement Plan may accept or decline.

## Scoped Pytest Commands

```
# Self-model phase unit + component-patch coverage, allowlist sanity
.venv/bin/python3 -m pytest tests/unit/cognition/test_phase2_self_model_phase.py \
  tests/unit/optimization/test_component_patches.py \
  tests/unit/config/test_phase10_feature_flags.py -q

# Branch B integration (cross-tick materialization + belief-assimilation interaction)
.venv/bin/python3 -m pytest tests/integration/domains/test_fused_loop.py \
  -k "self_model or branch_b or belief" -q

# Per-world flag/content guardrail (includes the urban_political exception, T5)
.venv/bin/python3 -m pytest tests/integration/test_world_profile_feature_flag_guardrail.py -q

# All 3 _DELIBERATE_ON_DEFAULT_FLAGS allowlist copies + ENABLE_ADVENTURE_ROUTING default sentinel
.venv/bin/python3 -m pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/test_scenario_feature_flag_defaults.py \
  tests/certification/test_phase10_enhanced_determinism_parity.py -q
.venv/bin/python3 -m pytest tests/integration/scenarios/test_balance_regression.py \
  -k adventure_routing_defaults_off -q

# Population stability for the one shipped-ON world
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py \
  -k unit_selfmodel_pilot -q

# Grade-anchor regression (self-model probes) — run AFTER producing fresh calibration reports,
# otherwise these 6 will (correctly) skip rather than assert anything
.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k selfmodel -q
```

## Anti-Drift Test Guards

- **`test_self_model_flag_content_pairing_both_directions_with_documented_exception` (T5,
  `test_world_profile_feature_flag_guardrail.py`) is the primary drift guard for the
  `urban_political` exception itself** — it fails loudly if any other world silently develops the
  same seeded-but-unflagged mismatch without a matching `known_exceptions` entry, and it fails if the
  documented exception's own claimed state (`content_seeded=True, flag_on=False`) goes stale. Do not
  touch `tests/simulation_quality/fixtures/expected_world_flag_state.json`'s `known_exceptions` block
  as part of this ticket unless the trial genuinely changes `urban_political`'s flag state (which Out
  of Scope forbids).
- **`_DELIBERATE_ON_DEFAULT_FLAGS` allowlist tests (3 copies) are the guard against silently
  flipping this flag's default** — under the expected "keep OFF" recommendation, all three must
  continue to reject `ENABLE_SELF_MODEL_COGNITION` as ON-default. A pass here after Implement is
  direct evidence the ticket did not accidentally do what its Out of Scope forbids.
- **`test_adventure_routing_defaults_off` (`test_balance_regression.py`) guards against a silent
  flip of `ENABLE_ADVENTURE_ROUTING`'s own default** — irrelevant to this ticket's own scope change,
  but relevant to AC2's resolution staying valid: if a future session flips this flag's default
  without re-wiring any gate, AC2's "resolved" status (structural inertness) still holds; if a future
  session both flips the default *and* re-wires a gate, this test alone would not catch the
  regrant — that is exactly the gap the proposed `test_enable_adventure_routing_has_no_live_gating_call_site`
  guard (New Tests Required, above) would close, which is why it is proposed even though not
  strictly required.
- **The two `test_grade_regression.py` grade-anchor probe tests are the anti-drift guard against a
  silent grade regression in either isolated (`urban_political_selfmodel_probe`) or full-stack
  (`urban_political_selfmodel_execution_probe`) self-model activation** — they must be run with fresh
  `data/calibration/` reports (not left `skipped`) at least once during this ticket's Implement phase
  to count as real re-verification, not just confirmed-not-broken-by-omission.
- **Do not weaken, skip-mark, or delete any of the above tests to make this ticket "pass" faster** —
  per CLAUDE.md's Gate Integrity rule, a `skip` from a missing local calibration report is legitimate
  and disclosed; converting a real assertion into a skip to dodge a genuine failure is not.
