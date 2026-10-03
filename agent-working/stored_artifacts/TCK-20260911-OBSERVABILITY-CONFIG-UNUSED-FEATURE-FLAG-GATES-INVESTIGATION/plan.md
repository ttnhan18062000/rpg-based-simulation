# Plan — TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION

## Disposition (peer-reviewed)
Close on the narrow claim: 3 of the 10 named flags (`is_event_recorder_enabled`,
`is_entity_timeline_enabled`, `is_warehouse_ingest_enabled`) are confirmed vestigial scaffolding —
their real subsystems are live but gated a different way (coarse `ObservabilityMode` directly, not
this fine-grained flag layer) — deleted. The other 8 are one underlying finding, not 8 independent
dispositions: a fully-built, individually-tested behavior-analytics pipeline that was never started
in production, backing 7 permanently-empty API endpoints. Spun out as its own standard-tier ticket
per peer review's explicit instruction, rather than resolved here — "wire vs. defer" is a real
product decision, not a flag-cleanup question.

## Steps
1. Delete `is_event_recorder_enabled()`/`is_entity_timeline_enabled()`/`is_warehouse_ingest_enabled()`
   from `ObservabilityConfig` — confirmed vestigial, real subsystems gated a different way,
   confirmed live.
2. File `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` for the 8-flag /
   7-endpoint finding, framed as the open wire-vs-defer question, cross-referenced in both
   directions with `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION`
   (the same shape, second instance in this batch).
3. Record both generalizable lessons in investigation.md (grep-scope risk in both directions;
   coarse-vs-fine gating mismatch generalizing past the 10 named flags) for whoever does a similar
   pass next.
4. Close this ticket.

## Guardrails
- Do not decide the behavior-analytics pipeline's own wire-vs-defer disposition here — real product
  decision, routed to its own ticket per peer review's explicit instruction.
- Do not remove the underlying `OBS_EVENT_RECORDER`/`OBS_ENTITY_TIMELINE`/`OBS_WAREHOUSE_INGEST`
  preset-dict entries — this ticket's own Scope is the unused convenience *methods*, not the
  broader mode-preset table structure.
- Do not chase the "17 flags, only 2 actually called by name" generalization beyond recording it —
  that's a larger question than this ticket's own named 10 flags, noted for a future pass, not
  resolved here.
