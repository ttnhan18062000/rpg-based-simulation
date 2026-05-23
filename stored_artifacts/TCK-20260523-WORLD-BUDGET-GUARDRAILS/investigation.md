# Investigation — Milestone 74 Resource and Storage Guardrails

## Objectives
1. Review standard Pydantic schema serialization properties in `WorldSpec`.
2. Confirm the best formula for telemetry artifact size calculation based on events/tick metadata.
3. Review `WorldValidator` to safely configure profile injection.

### Discoveries
- In the engine, each entity routinely records coordinates and status changes every tick, producing roughly 100-200 bytes of telemetry per tick in the JSONL events buffer.
- Thus, estimating `0.0001` MB per entity-tick is a solid empirical baseline.
- `WorldValidator` can be instantiated with a `profile: str = "local_dev"` option or similar. Let's make it pass cleanly and support default profile definitions.
