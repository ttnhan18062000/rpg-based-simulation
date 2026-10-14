---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02
artifact_type: report
tags: [economy, resource]
---

Pinned measurement (governor NORMAL, audit_mode, budget off, LocalSequentialExecutor, seeds 42-46, 5000 ticks, three worlds).
Scripts: chain_ms.py (one run, prints a CH row), job.sh (arm/world/seed driver), agg.py (aggregates CH rows into the table).
arm1 = main at 0b4f12af7 (free meals on); arm2 = batch 2 chain, free meals on, no gate; arm3 = chain + the free-meal removal; arm4 = arm3 + wage shift.
table4.txt is the ONE summary table (mean (SD) over 5 seeds, kind groups); per-run rows are not kept (probe rule: scripts plus one summary table).
Post-#457 paired table: table_post457_arm1_new_main_vs_arm6_batch2.txt (paired.py). arm7 ablation (profiles not applied) and the starvation trace: trace2.py, an2.py, arm7_trace_summary.md.
