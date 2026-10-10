---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Plan: TCK-20261010-PERF-M2-T05-BASELINE-LIFECYCLE

Pre-planned by perf-planner (M2 epic "Delivery plan"); the known-debt ledger was split out to T05b before this started (dispatch 2026-10-10,
commit 8a552770a). Written at close, after the implementation. No `src/` change (OD-8).

## Order
1. `tools/perf/baseline_lifecycle.py`: `refusals`, `promote`, `check`, the CLI; `LEGACY_TRIPWIRE_REFERENCES` (the 15 files).
2. `tests/unit/perf/test_baseline_lifecycle.py`.
3. `docs/performance/perf_baseline_policy.md` rewritten as lifecycle rules; parity `INFRA-431`.

## Decisions where the ticket left a choice
- **Versioned file layout:** `tests/perf/baselines/<name>.vNNNN.json`, top level, so the "every `*.json` is a record or a listed legacy file" check sees
  promoted baselines. The file is the record plus a top-level `promotion` object; `BenchmarkRecord.from_dict` ignores unknown keys, so it stays a
  valid record. Cause, note, time, before identity and after identity live in `promotion`.
- **Chain:** `identity.baseline_ref` (already in schema 1.0) points at the previous version with its digest, so editing an earlier version is detected
  by `check`. The digest is over the record without `promotion`.
- **A refusal reports every applicable reason** and writes nothing (exit 2). A stale `cost_accounting_version` is refused as well as a missing one
  (a candidate measured under old accounting is not a baseline).
- **The cause must exist:** a ticket id must be a file under `agent-working/tickets/`, a `DEV-nnn` must be a heading in the divergences doc. A PR
  number cannot be checked offline and is accepted by shape.
- **The allowlist is a constant in the tool** (not a data file in the baselines directory, which the check would itself enumerate).
- **No interim known-reds loader** (perf-planner's instruction); the ledger is T05b.
- **Tests live in `tests/unit/perf/`** (my domain), not `tests/tools/`.
