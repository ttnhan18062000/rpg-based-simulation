# Implementation Sequence — live-map-reconnection

Tickets must be implemented in this order. Generated from intra-batch dependency analysis
(cross-referencing each ticket's own `## Related Tickets` section against the other 7 tickets in
this batch). `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260821-PRESENT-MAP-STATIC  (no deps in this batch)
2. TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT  (depends on: TCK-20260821-PRESENT-MAP-STATIC)
3. TCK-20260821-REST-MAP-STATIC-STATS  (depends on: TCK-20260821-PRESENT-MAP-STATIC)
4. TCK-20260821-WS-ENTITY-DELTA-BROADCAST  (no deps in this batch)
5. TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD  (depends on: TCK-20260821-WS-ENTITY-DELTA-BROADCAST)
6. TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET  (depends on: TCK-20260821-WS-ENTITY-DELTA-BROADCAST, TCK-20260821-REST-MAP-STATIC-STATS)
7. TCK-20260821-LIVE-MAP-PERF-VALIDATION  (depends on: TCK-20260821-PRESENT-MAP-STATIC, TCK-20260821-WS-ENTITY-DELTA-BROADCAST, TCK-20260821-REST-MAP-STATIC-STATS, TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET)
8. TCK-20260821-PHASED-LOADING-STATE-MACHINE  (depends on: TCK-20260821-WS-ENTITY-DELTA-BROADCAST, TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET)

## Why This Order Matters

TCK-20260821-PRESENT-MAP-STATIC and TCK-20260821-WS-ENTITY-DELTA-BROADCAST are the two load-bearing
prerequisites — the only tickets with no in-batch dependency, and every other ticket transitively
needs one or both of them first. PRESENT-MAP-STATIC (the new `StatePresenter.present_map`/
`present_static` methods) must land before both REST-MAP-STATIC-STATS (which wraps those methods in
real routes) and MANIFEST-ID-LOOKUP-ENDPOINT (whose `terrain_types` id-space must match whatever
grid-encoding scheme PRESENT-MAP-STATIC settles on). WS-ENTITY-DELTA-BROADCAST (the real per-tick
delta payload over `/api/v1/ws`) must land before DELTA-ENVELOPE-SPATIAL-FIELD (which adds one field
to that same envelope and has no implementation surface without it) and before
REWIRE-USESIMULATION-WEBSOCKET (the frontend consumer of that payload shape).
REWIRE-USESIMULATION-WEBSOCKET also needs REST-MAP-STATIC-STATS, since the frontend hook's initial
load fetches `/map`/`/static` alongside opening the WebSocket. LIVE-MAP-PERF-VALIDATION is last among
the backend/rewire work by design — it measures the finished, connected system, so it has nothing to
measure until PRESENT-MAP-STATIC, WS-ENTITY-DELTA-BROADCAST, REST-MAP-STATIC-STATS, and
REWIRE-USESIMULATION-WEBSOCKET are all done. PHASED-LOADING-STATE-MACHINE's `SYNCING` status
represents the real connect-time handoff WS-ENTITY-DELTA-BROADCAST and REWIRE-USESIMULATION-WEBSOCKET
implement, so it waits on both rather than wiring against a mechanism that doesn't exist yet.

Running alphabetically would attempt several tickets before their real prerequisites are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets are
skipped automatically.
