---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL
artifact_type: plan
tags: [benchmarking]
---

# Plan

1. `tools/rpg_measure/paired.py`: replace the import-time `DEFAULT_CACHE` with `resolve_cache()`, read when called: `$RPG_MEASURE_CACHE`, else `$XDG_CACHE_HOME/rpg-measure`, else `~/.cache/rpg-measure`. `--cache` defaults to `None` and `_run` resolves it.
2. `ensure_cache_writable(cache)` runs in `_run` before `neutral()` or any arm: it creates the directory and checks it is writable; otherwise `_refuse` prints one `REFUSED:` line naming `RPG_MEASURE_CACHE` and the path and exits 2, before any child starts. `--collected` reads a cache and writes nothing, so it is not checked.
3. Module docstring: how u24 keeps its cached arms (`RPG_MEASURE_CACHE=/mnt/data/scratch-rpg-measure`). `paired_arms.py` untouched. Cache keys untouched.
4. Three unit tests beside `tests/unit/tools/test_rpg_measure.py`: variable set, XDG/home fallback, unwritable path (no child started).
5. Gates before the SHA goes out: `tests/unit/tools` serially under MemoryMax=3G, `make code-health`, `make lint-imports`. No heavy run.
