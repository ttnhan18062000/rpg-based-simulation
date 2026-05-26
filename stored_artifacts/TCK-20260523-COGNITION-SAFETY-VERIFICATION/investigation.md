# investigation.md - Parity & Performance Checks

- State Hash Parity: simulation logic runs deterministically via the Kernel. The state hash is calculated from the entity map at the end of each tick.
- Performance limits: light-mode overhead must remain under 1% of total compute tick budget.
- Memory: verify snapshots are flushed to JSONL iteratively rather than building huge memory buffers.
