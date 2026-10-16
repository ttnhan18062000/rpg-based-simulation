---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED
artifact_type: investigation
date: 2026-10-15
tags: [performance, observability]
---

# Investigation: TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED

Checked on origin/main d7d328875 with the committed tree.

- #597 (TCK-20261014-PERF-TICK-COST-GROWTH-INVESTIGATION, d7d328875): `decision_trace` frames are 0.0-1.4 % of the tick-thread samples in every profile (tick_cost_growth.md §4).
- `src/observability/cognition/decision_trace_writer.py:82` creates `QueueDrainWorker(queue=self._queue, file_write_fn=self._write_entry_to_file)`. `src/observability/queue.py:116` runs it as a daemon thread named `observability-drain-worker`. The tick thread calls `_write_entry_to_file` only in `close()` (`:177`, the final drain at shutdown).
- The file has been unchanged since 29d78798a (2026-08-14). The writer was already threaded when this ticket's September cProfile was taken, so that run's 200 calls were most likely the shutdown drain or a profiler that saw every thread. This was not re-checked, and it does not change the close.
