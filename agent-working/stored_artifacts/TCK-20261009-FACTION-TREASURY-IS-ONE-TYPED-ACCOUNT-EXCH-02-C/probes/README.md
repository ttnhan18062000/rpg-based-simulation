---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-FACTION-TREASURY-IS-ONE-TYPED-ACCOUNT-EXCH-02-C
artifact_type: report
tags: [economy, resource]
---

Batch-3 (treasury) measurement. Pinned NORMAL governor, `audit_mode`, `LocalSequentialExecutor`, seeds 42-46, 5000 ticks, three worlds.
Scripts: `chain_ms3.py` (one run, prints a CH row with coin accounting: start, end, created by spawns, drift, hero treasury, owed debts), `paired3.py` (paired mean diff, SE, 2-SE flags
per kind group), `coin_probe.py` (per-tick coin by category), `town_close.py` (treasury and building state every 250 ticks), `deaths.py` (death list with ticks).
`paired_table_main_vs_batch3.txt` is the ONE summary table (base = main plus batch 4, t3 = batch 3). Per-run rows are not kept.

Findings in the table: coin drift is 0.0 to 0.4 per run against +5942 to +8602 on main; tax paid by the poor is 0; the hero treasury ends near 2 gold against about 10,000 on
main because the +10 building mint is gone and treasury income is dormant while the free meal stands (urban seed 42: treasury 660 at tick 250, 1 at 750; functional buildings
7 of 7 at 500, 1 of 7 at 750, 0 of 7 from 1000 to 2000). Ablation (kill gold restored, 1000 ticks, same seeds): alive@1000 identical to batch 3, so the early dip of about 2 alive
is not kill coin. Death trace (crowded seed 46): first divergence from main by tick 40 (the first upkeep and levy tick).
