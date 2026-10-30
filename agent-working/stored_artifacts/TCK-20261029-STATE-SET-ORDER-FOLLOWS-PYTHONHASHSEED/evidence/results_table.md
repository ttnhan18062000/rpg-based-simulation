# Seed-0 acceptance evidence for TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (rulings 4, 5, 6)

Base de5a223ca (merge-base of B) against B (tree 8c0a48599; `src/` and `tools/` unchanged on later heads). PYTHONHASHSEED=0, audit_mode, one interpreter for every run of both arms: the main checkout's `.venv/bin/python` (not synced during the batch). Wrapper: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, sequential, MemAvailable >= 3 GB before each run. Scripts: `evidence/` beside this file (`arm_child.py` from tools/rpg_measure, `go.sh`, `batch1000.sh`, `compare35.py`, `inst.py`, `attribute.py`, `prefix.py`). The VM kernel-panicked at 21:49 on 2026-10-30 mid-batch; a control re-run after the reboot (B, frontier_living_world s42 1000t) gave the identical final hash a8072692aeddcfd2da94bcd58b0b9fe1a5e32b553056f3393b5c8b1855a6e0f9 and identical per-entity state and counters.

## Outcomes, 1000-tick set (15 pairs) and 5000-tick s42 pairs (3)

| world | seed | ticks | base final hash | B final hash | alive base/B | deaths by cause | counters |
|---|---|---|---|---|---|---|---|
| frontier_living_world | 42 | 1000 | 607de1258016 | a8072692aedd | 31/31 | same | same |
| frontier_living_world | 42 | 5000 | 548b423e43b2 | 300a55218931 | 27/27 | same | same |
| frontier_living_world | 43 | 1000 | 34ab8a5e0128 | be7d7f7cc5b5 | 34/34 | same | same |
| frontier_living_world | 44 | 1000 | 8cbd22c131f2 | bcbcc8b4407f | 25/25 | same | same |
| frontier_living_world | 45 | 1000 | 2a3be909c6fd | 3da93c858aba | 30/30 | same | same |
| frontier_living_world | 46 | 1000 | 15ced0222ef9 | c52baa9762b8 | 31/31 | same | same |
| urban_political | 42 | 1000 | c6a06e429c66 | d962ff60695c | 22/22 | same | same |
| urban_political | 42 | 5000 | 324e9dea1f81 | 849024338a6c | 22/22 | same | same |
| urban_political | 43 | 1000 | 7c1c4a9ba3fe | 561d69d39368 | 22/22 | same | same |
| urban_political | 44 | 1000 | 5733488276b1 | bf74272ff24d | 24/24 | same | same |
| urban_political | 45 | 1000 | 55f6145f36d0 | 1ef10bcf846c | 14/14 | same | same |
| urban_political | 46 | 1000 | 3058b0c50df1 | ded0a3c5f68e | 20/20 | same | same |
| crowded_frontier | 42 | 1000 | 7031f948ae62 | 08afbabcb4b3 | 8/8 | same | same |
| crowded_frontier | 42 | 5000 | 5299195cf82a | 32f5d8b11c0e | 1/1 | same | same |
| crowded_frontier | 43 | 1000 | 6af9a50ed902 | afb26deaa913 | 18/18 | same | same |
| crowded_frontier | 44 | 1000 | c10f438a8097 | d0dbd29cf877 | 17/17 | same | same |
| crowded_frontier | 45 | 1000 | 45e089b8ea4a | a436e4fb28bc | 12/12 | same | same |
| crowded_frontier | 46 | 1000 | f0adf11af94c | 68bc92c62268 | 24/24 | same | same |

Per-world 5-seed sums (1000t set): none outside max(1, 5% of main) (`compare35.py 1000`); 5000t s42 pairs: all equal (`compare35.py 5000`). All 18 pairs moved the final hash.

## First difference per moved-hash seed (instrumented pairs; trims aligned by (tick, entity), kept/dropped compared as SETS, order ignored)

| world | seed | trace | first set difference (tick, entity) | verdict | inputs identical | real set-differing trims | order-only differences | trims base/B | keys only in base / only in B |
|---|---|---|---|---|---|---|---|---|---|
| frontier_living_world | 42 | 5000t | t304 e26 | TIE (urgency 0.5) | True | 489 | 131 | 43219/43294 | 8 / 83 |
| frontier_living_world | 43 | 1000t | t76 e14 | TIE (urgency 0.5) | True | 64 | 16 | 5496/5497 | 0 / 1 |
| frontier_living_world | 44 | 1000t | t400 e30 | TIE (urgency 0.5) | True | 67 | 60 | 5307/5307 | 0 / 0 |
| frontier_living_world | 45 | 1000t | t383 e17 | TIE (urgency 0.5) | True | 29 | 5 | 2426/2426 | 1 / 1 |
| frontier_living_world | 46 | 1000t | t233 e17 | TIE (urgency 0.5) | True | 118 | 47 | 4875/4875 | 0 / 0 |
| urban_political | 42 | 1000t | t205 e15 | TIE (urgency 0.5) | True | 10 | 4 | 897/897 | 0 / 0 |
| urban_political | 43 | 1000t | t193 e17 | TIE (urgency 0.5) | True | 14 | 13 | 3124/3124 | 0 / 0 |
| urban_political | 44 | 1000t | t256 e14 | TIE (urgency 0.8) | True | 4 | 0 | 4/4 | 0 / 0 |
| urban_political | 45 | 1000t | t236 e14 | TIE (urgency 0.5) | True | 69 | 8 | 5173/5173 | 0 / 0 |
| urban_political | 46 | 1000t | t105 e15 | TIE (urgency 0.5) | True | 15 | 3 | 2141/2141 | 0 / 0 |
| crowded_frontier | 42 | 1000t | t116 e24 | TIE (urgency 0.5) | True | 90 | 61 | 4349/4349 | 0 / 0 |
| crowded_frontier | 43 | 1000t | t226 e14 | TIE (urgency 0.5) | True | 30 | 52 | 2301/2301 | 0 / 0 |
| crowded_frontier | 44 | 1000t | t194 e16 | TIE (urgency 0.5) | True | 99 | 12 | 2634/2634 | 0 / 0 |
| crowded_frontier | 45 | 1000t | t390 e30 | TIE (urgency 0.5) | True | 55 | 23 | 3216/3215 | 1 / 0 |
| crowded_frontier | 46 | 1000t | t123 e17 | TIE (urgency 0.5) | True | 15 | 2 | 905/905 | 0 / 0 |

urban_political s42 and crowded_frontier s42 at 5000t reuse their 1000t traces, and frontier_living_world s42 at 1000t reuses its 5000t trace (ruling 6, ASK 2). Prefix check, once per world, same arm (B): the state hash at t1000 equals the 1000t run's final hash.

| world | hash at t1000 of a run configured for 5000 ticks (prefix.py) | 1000t run final hash | equal |
|---|---|---|---|
| urban_political | d962ff60695c0713 | d962ff60695c0713 | yes |
| crowded_frontier | 08afbabcb4b3477c | 08afbabcb4b3477c | yes |
| frontier_living_world (base) | 5000t trace checkpoint at tick 1000: 607de1258016fc87 | 607de1258016fc87 | yes |
| frontier_living_world (B) | 5000t trace checkpoint at tick 1000: a8072692aeddcfd2 | a8072692aeddcfd2 | yes |

## Post-merge check (ruling 7): merged B (fe6cb5772) against origin/main c5139b410

PYTHONHASHSEED=0, audit_mode, seed 42, 1000 ticks, the main checkout's `.venv/bin/python` for every run. Trees: `trees/base2` (c5139b410) and `trees/B2` (fe6cb5772), differing only in B's 8 `src` files. Scripts: `chain4.sh`, `compare_post.py`, `attribute.py`.

| world | base2 hash | merged B hash | alive base/B | deaths | counters | outside max(1, 5%) | first set difference | verdict |
|---|---|---|---|---|---|---|---|---|
| frontier_living_world | 607de1258016 | a8072692aedd | 31/31 (same set) | same | same | none | t304 e26 | TIE (0.5), inputs identical |
| urban_political | c6a06e429c66 | d962ff60695c | 22/22 (same set) | same | same | none | t205 e15 | TIE (0.5), inputs identical |
| crowded_frontier | 7031f948ae62 | 08afbabcb4b3 | 8/8 (same set) | same | same | none | t116 e24 | TIE (0.5), inputs identical |

The base2 and merged-B hashes equal the de5a223ca and B hashes of the 1000t set (same worlds, seed 42), so #788, #789 and #791 to #793 moved none of them.

Merged B, crowded_frontier s42 1000t, final hash by PYTHONHASHSEED: 0, 1, 2, 3 all `08afbabcb4b3477c`. IDENTICAL.
