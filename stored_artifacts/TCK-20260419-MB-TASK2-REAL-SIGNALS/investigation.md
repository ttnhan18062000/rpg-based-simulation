# Investigation: Milestone B Real Signal Implementation

Confirmed that `WorkerManager` point-in-time sampling was inadequate.
Implemented Peak Inflight tracking to ensure saturation is visible to the governor.
Refactored `RuntimeStatus` and `SignalCollector` to use 5-tick rolling windows for all trends/averages.
Verified that `RuntimeProfile` correctly governs sampling cadences.
