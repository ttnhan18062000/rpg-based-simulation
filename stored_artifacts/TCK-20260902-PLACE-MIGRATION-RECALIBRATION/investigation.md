---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-PLACE-MIGRATION-RECALIBRATION
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260902-PLACE-MIGRATION-RECALIBRATION

`state_hash` (`StateFingerprinter`) confirmed blind to Place data in Stage A — used `canonical_state_hash`
instead for the state-hash-first check. All 21 worlds' canonical hash changed (expected: real new Place
data), already independently verified isolated to `regions`/`places` only via Stage A/B's own canonical-dict
diffs at 3 entity-count scales — not re-derived here.

Full 81-run_key `grade_anchors.json` sweep (`tools/calibrate_simq.py`, one fresh calibration per run_key):
18/81 matched, 61/81 drifted, 2/81 failed (`urban_political_selfmodel_execution_probe_seed42_200t`,
`urban_political_selfmodel_probe_seed42_200t` — no matching `data/worlds/` directory, a tooling/naming
issue unrelated to content).

**Causal isolation test** (the key finding): reverted all 6 content modules idea 66 touched to their
exact pre-migration state, re-ran the previously-drifted `unit_information_source_seed123_200t` — it
still drifted identically (SOCIAL: anchor A/1.8 vs. fresh S/3.97). This proves the drift is entirely
unrelated to idea 66's Place migration. `grade_anchors.json` last committed `5993cac3` (2026-08-31), 21
commits ago — the same root-cause class (stale, unmaintained fixture) as Stage A's
`world_compile_report.json` finding, now confirmed to extend to a second, independent fixture.

The one hand-verified control run_key (`unit_information_source_seed42_200t`, checked before the full
sweep) matched its anchor across all 10 pillars exactly — consistent with seed/scenario-dependent
pre-existing drift, not a uniform migration effect (which would show up identically across scenarios
sharing the same content, not selectively by seed).
