---
status: active
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS
date: 2026-10-15
tags: []
---

# Investigation: TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS

- The knowledge index and graphify graph were absent in the worktree; context came from direct reads (disclosed in the ticket).
- Existing parts reused: `rpg_gate_run.build_kernel` (pinned governor, audit_mode, no frame pacing), `RunLedger` (tally event in the run's event file), `require_host_independent_runs` (run_determinism.py; the manifest records `audit_mode` and `signals_zeroed`), `lifecycle.death_record` (cause), `kind_group` / `is_person`.
- The keeps_coin problem: the diet step grew the keeps_coin set in the new arm, so counting people by the new arm's flag was not like-for-like. The tool fixes the set at the base arm's tick-0 roster and reads both arms on those ids.
- Under audit_mode two runs of one arm are byte-identical, so the base-vs-base spread is 0 and cannot be a standard error; the SE comes from the per-seed paired differences.
- Gaps: no typed record of pre-check refusals exists at this commit (the table says "not measured"); a base arm older than the counters reports the counters as n/a, never zero; a floor value is not yet set.
- Memory: 3 parallel runs fit, more get reaped; `--jobs` defaults to 2.
