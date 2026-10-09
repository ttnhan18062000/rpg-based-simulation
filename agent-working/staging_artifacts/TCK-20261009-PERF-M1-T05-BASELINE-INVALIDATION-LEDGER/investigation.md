---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER
date: 2026-10-09
tags: [performance, determinism, testing]
---

# Investigation: TCK-20261009-PERF-M1-T05-BASELINE-INVALIDATION-LEDGER

Context scan: `search_docs` (baseline invalidation, M1 corrections), `graphify query` (perf baselines), then the follow-up greps below.

## Search commands used (AC1)
- `git ls-files '*.json' '*.yaml' '*.yml' '*.jsonl' '*.csv'` minus agent-working, registries, parity ledger, lock files: 888 tracked data files.
- `grep -lE 'canonical_state_hash|state_hash|tick_compute|phase_cost|dropped_work|work_debt|digest|p95_tick|tick_ms|ticks_per_second|certification_result'` over that list, grouped by directory: `tests/perf/baselines` (15), `docs/observability/baselines` (15), `docs/audits` (2, code inventory), `docs/performance` (1), `tests/unit/kernel/golden` (1), `docker/grafana/dashboards` (1), `data/worlds/*` (21 compile reports).
- `git grep -lE '\b[0-9a-f]{64}\b'` over non-Python tracked files: the 21 compile reports (`canonical_state_hash`), 120 `data/worlds/*/resolved/*` (content/catalog fingerprints, not state digests), one API-key hash in the Makefile. `git grep` of quoted 64-hex strings in `tests/*.py`: only `test_proof_digest_contract.py` pins a state digest.
- `git ls-files | grep -iE 'certification.*\.(json|yaml)|cert.*result'` outside src/tests/docs/plans: none. No certification result file is committed.
- Consumers: `git grep` for each baseline path (see the ledger's Consumer column).

## Facts that decide statuses
- Merge commits (date): T01 #352 `0b3023d7a` 10-05; T02 #319 `cf7cbcb08` 10-04; T03b #379 `33588b966` 10-06 (also DEV-014); #380 `ae4388854` 10-06; salience #387 `3e466e132` 10-06; DEV-017/018 #448 `28d0af111` 10-08; DEV-019 #455 `77fe33645` 10-09. The worker fix's code landed `bc00caa1a` 2026-09-13.
- Capture dates come from the embedded `timestamp`: `tests/perf` synthetic files 2026-05-15, `docs/observability` files 2026-05-19, `simq_corpus_*` 2026-08-07, `baseline_5k` 2026-08-17 (`generated_at`), grade anchors committed 2026-08-31. Every artifact predates every M1 change, so capture-versus-merge ordering never excludes a change; applicability decides.
- `resolution_overhead` key: absent from the 12 May synthetic `tests/perf` files (older pipeline, `apply/combat/movement/resource/strategic` buckets), present in all 13 `docs/observability` per-scenario files, `latest.json`, `matrix_full.json` and the three `simq_corpus_*` files. DEV-017's double count lived in how that key was computed, so only files with it are affected.
- Budget check (max tick versus the profile's `max_tick_budget_ms`, DEV-014's cutoff): all below 0.6x except `tests/perf/resource_100_concurrent` (101.0 vs 100.0, 1.01x) and `latest.json` IDLE_5000 (`PERF_4GB_LOCAL`, p95 117.4, max 149.9 vs 100.0). No file stores a `mode_sequence`, so a cutoff cannot be excluded for those two.
- Worker count from `PERF_PROFILES`: every `*_LOCAL` profile has 0 workers, every `*_CONC` has 4.
- `docs/observability/baselines/latest.json` is read by `python3 -m src gate` and `compare-sweep` (`docs/guides/simulation.md:98`, `observability.md:161`); `tests/perf/baselines` by `tests/perf/test_perf_regression_baseline.py` and `tools/perf/check_perf_regression.py`; `baseline_5k.json` by `tests/regression/test_behavioral_5k.py` (not audit_mode: flags only `no_frame_pacing`).
- No `PERF_*` profile sets `signal_contract`, so CANONICAL cannot be selected for a perf run without a profile addition (an M2 `src/` change).
- `StateFingerprinter` (MD5, `src/replay/fingerprint.py`) never read `work_debt` or `periodic_due_ticks` and was not changed by #455, so the compile reports' `state_hash` is unaffected; only `canonical_state_hash` moves.
