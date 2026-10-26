---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS
artifact_type: test_plan
tags: [testing, performance, determinism]
---

# Test plan

Unit (no simulation), staged `results/` dirs in tmp_path: missing result REFUSED with its keys; mismatched python, os, image REFUSED; repeat file survives a collected run; `--jobs` / `--clean-cache` rejected; short sha rejected; verdict-json PASS, STOP, REFUSED, report_only, neutral; missing cost.json gives null wall/RSS; local mode output unchanged on a staged cache (compared against the pre-change function outputs); collected vs local table equal on one staged cache.
Real step (read-only, after Lane A exits): `--collected` over /mnt/data/scratch-rpg-measure against the local table of the same step.
