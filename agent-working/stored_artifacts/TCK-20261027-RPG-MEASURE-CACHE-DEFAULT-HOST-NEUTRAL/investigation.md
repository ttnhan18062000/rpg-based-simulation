---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL
artifact_type: investigation
tags: [benchmarking]
---

# Investigation

- `tools/rpg_measure/paired.py:48` bakes `/mnt/data/scratch-rpg-measure` into `DEFAULT_CACHE` at import; line 295 uses it as the `--cache` default. `/mnt/data` exists only on u24.
- `DEFAULT_CACHE` has no other reader in `tools/` or `tests/`; `grep mnt/data tools/rpg_measure` finds only that line.
- `_refuse` already prints `REFUSED: ...` to stderr, records the verdict and returns 2, the documented refusal exit code.
- Cache keys come from `result_path` (commit, child hash, ticks), which this change does not touch.
- On ubuntu `~/.cache` is on the same disk as `/data`, so ubuntu proof runs keep setting `RPG_MEASURE_CACHE` explicitly.
