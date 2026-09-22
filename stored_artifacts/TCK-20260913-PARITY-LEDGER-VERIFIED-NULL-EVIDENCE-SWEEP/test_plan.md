---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
artifact_type: test_plan
---

# Test Plan — TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP

This ticket is a data-correction change to `docs/parity_ledger/*.yaml`, not a code change. No new
test code is warranted; coverage is: (1) the sanctioned writer's own existing test suite, run
scoped, confirming the two writes are schema-valid and well-formed, and (2) direct code reads
confirming the `WORLD-CULT-002` re-point's factual claim before it was written.

## Scoped test run

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest \
  tests/tools/test_parity_ledger_writer.py \
  tests/tools/test_parity_ledger_schema.py \
  tests/tools/test_parity_ledger_scan.py -q
```

Result: 53 passed.

## Per-entry validation

- `python3 tools/parity_index.py build` run as a separate, visible Bash call after both writes
  (the writer already rebuilds in-process; this call is required separately for the
  `parity_write_safety` retro metric to see it — per the writer module's own docstring).
- Explicit per-item `jsonschema.validate()` against `docs/parity_ledger/schema.json`'s `items`
  sub-schema for both edited entries individually (`INFRA-228`, `WORLD-CULT-002`) — both pass.
  (A whole-shard `jsonschema.validate()` against `infrastructure.yaml` fails at an unrelated
  pre-existing entry — `proof_type: unit`, not in the enum, at an index far from either edit — a
  pre-existing corpus issue, out of this ticket's scope, not introduced by this change.)
- `git diff --stat docs/parity_ledger/` confirms only the two intended shards changed; `git diff`
  on each confirms only the intended entry (`INFRA-228` / `WORLD-CULT-002`) was touched, nothing
  else in either 2000+-entry shard.

## Pre-write factual verification (not a pytest run, but load-bearing evidence)

- `INFRA-228`: confirmed `src/domains/optimization/degradation.py` deleted (`find` + `git log
  --diff-filter=D --follow`); confirmed the cited `test_path` function absent via `grep -n "^def
  test_"` against the named file; confirmed the sub-claim's own test
  (`test_runtime_content_source_module_default_is_not_legacy_hardcoded`) exists at line 30.
- `WORLD-CULT-002`: read `src/domains/adventure/scoring.py:280-294` and
  `src/domains/culture/settlement_personality.py:1-101` directly (not grepped/inferred) to confirm
  neither call site writes the computed delta back onto any entity/durable-state object before
  re-pointing the citation as CERTAIN.

## Out of scope for this test plan

- The pre-existing `proof_type: unit` schema violation found incidentally in
  `infrastructure.yaml` during validation — not introduced by this ticket, not corrected here.
- Any test of the 1886 entries that passed the symbol-existence sweep — per the investigation's
  own stated method limitation, passing this sweep is not a correctness proof for those entries.
