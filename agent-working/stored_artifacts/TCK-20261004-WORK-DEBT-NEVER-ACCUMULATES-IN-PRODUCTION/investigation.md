---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION
date: 2026-10-04
tags: [performance, determinism, testing]
---

# Investigation: TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION

Starting facts are the ticket's own trace (perf-planner, 2026-10-04). This file collects what was verified. Findings are appended as the work proceeds and summarised in the ticket.

- Writers, readers and history are recorded in the ticket's Implementation Notes.
- Open questions at start: is there any path that raises debt other than `inject_work_debt`? Does dropped work feed anything that could have been the debt? What did Milestone 4 intend?

## Findings (verified 2026-10-04)
- No producer exists. Writers: only the executor's `DRAIN_DEBT` (always <= 0) feeds `work_debt_updates`; `PressureInjector.inject_work_debt` is the only code that raises debt and has no caller. Across 363 commits no added line increases debt.
- Test: 4 non-combat scenarios under the smallest accepted tick budget with `audit_mode` off stay at `work_debt == {}` and signal 0 while the governor reaches DEGRADED/SURVIVAL and about 70 000 dropped-work units are counted. The count is dominated by the fixed `record_dropped_work(9999)` watchdog sentinel (`kernel.py:463`).
- Dead because of it: governor SURVIVAL/DEGRADED debt thresholds and recovery limit, phase_governor debt term, kernel `debt_ratio`, the debt half of `global_salience`, the consumer half (DRAIN_DEBT, apply clamp, validator rule), and every telemetry or reporting field.
- Intent: Milestone 4 designed "overflowed work becomes debt, drained next tick, rejected over capacity"; only the consumer half was built.
- Recommendation: retire in two steps (document certification/injection-only now; retire when the gate lifts); no producer unless the owner wants a debt-driven feature and writes its contract (a deterministic overflow input does not exist today).
