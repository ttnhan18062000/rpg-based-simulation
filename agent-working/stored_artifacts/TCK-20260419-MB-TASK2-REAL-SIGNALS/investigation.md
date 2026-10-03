---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260419-MB-TASK2-REAL-SIGNALS
artifact_type: investigation
tags: [mb, task2, real, signals]
---

# Investigation: Milestone B Real Signal Implementation

Confirmed that `WorkerManager` point-in-time sampling was inadequate.
Implemented Peak Inflight tracking to ensure saturation is visible to the governor.
Refactored `RuntimeStatus` and `SignalCollector` to use 5-tick rolling windows for all trends/averages.
Verified that `RuntimeProfile` correctly governs sampling cadences.
