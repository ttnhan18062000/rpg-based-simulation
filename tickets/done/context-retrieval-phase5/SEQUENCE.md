# Implementation Sequence — context-retrieval-phase5

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260729-SHADOW-PACKET-CALL-SITE  (no deps in this batch)
2. TCK-20260729-SHADOW-BASELINE-COMPARISON  (depends on: TCK-20260729-SHADOW-PACKET-CALL-SITE)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

## Known Gap

The comparison view's fixture tests are built against the exact event shape
`TCK-20260729-SHADOW-PACKET-CALL-SITE` defines (real ticket run_id as the shadow-vs-synthetic
provenance signal, `phase="Retrieval"` label reused unmodified from Phase 4's
`wrap_context_packet_assembly()`). This is a strict 1-then-2 dependency, not merely a
suggested order — see `TCK-20260729-SHADOW-BASELINE-COMPARISON`'s own Assumptions/Open
Questions section.

## Risk Note

`TCK-20260729-SHADOW-PACKET-CALL-SITE` is the first ticket in this epic to modify a real
`.claude/workflows/*.js` file. It is scoped narrowly (Investigate phase only, opt-in via
`SHADOW_CONTEXT_PACKET_ENABLED`, fail-open via a `timeout` wrapper, no packet content ever
reaches an agent prompt) — but this is a materially higher-risk change than any prior
Phase 0-4 ticket, all of which were explicitly forbidden from touching workflow files.
Architecture review should apply the highest scrutiny of this batch to this ticket.
