Pinned measurement (governor NORMAL, audit_mode, budget off, LocalSequentialExecutor, seeds 42-46, 5000 ticks, three worlds).
Scripts: chain_ms.py (one run, prints a CH row), job.sh (arm/world/seed driver), agg.py (aggregates CH rows into the table).
arm1 = main at 0b4f12af7 (free meals on); arm2 = batch 2 chain, free meals on, no gate; arm3 = chain + the free-meal removal; arm4 = arm3 + wage shift.
table4.txt is the ONE summary table (mean (SD) over 5 seeds, kind groups); per-run rows are not kept (probe rule: scripts plus one summary table).
