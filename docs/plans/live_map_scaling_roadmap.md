---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, performance]
---

# Roadmap — Live Map: Reconnection, Then Evidence-Driven Scaling

**Purpose**: this player-facing live-map effort spans more work than one epic can hold cleanly. This doc
ties the milestones together and states the sequencing/gating rule once, instead of repeating it in each
epic. Each milestone beyond M1 is **evidence-gated, not started speculatively** — this isn't a suggestion,
it's the same "any real optimization need becomes a separate future ticket, driven by evidence" philosophy
already stated throughout M1's own plan doc, applied consistently across the whole roadmap rather than just
within one epic.

## Milestones

### M1 — Core Reconnection (ships a real, working, connected map)

**Tracking epic**: `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` (already fully scoped — 7 scope items, full
plan doc at `docs/plans/live_map_reconnection_epic.md`).

Ships: new `StatePresenter` methods (map/static serialization), the entity-delta broadcast (with the
externally-reviewed and independently-verified connect-time snapshot/handoff correctness fix), 3 new REST
routes, the `/api/v1/manifest` endpoint (with the protocol-version/dictionary-version split), the
`useSimulation.ts` frontend rewire, and a real percentile-based performance-validation pass. Also lays cheap
groundwork later milestones depend on without a breaking change: additive-only schema versioning, and a
reserved (unimplemented) spatial-subscription field on the broadcast envelope.

**M1 is the milestone that produces the real evidence M2 and M3 are gated on** — actual measured FPS,
actual measured bandwidth at actual entity counts, not the analytical estimates this roadmap and M1's own
plan doc currently rely on.

### M2 — Rendering Performance at Scale (client-side, gated on M1)

**Tracking epic**: `TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE` (new, scope-only — see its own
ticket).

Ships: chunked terrain caching (replacing a single whole-map bitmap, sized and bounded against real browser
canvas/memory limits — Safari's tighter ceiling, not Chrome's generous one), and layered entity rendering
using the corrected two-bucket model (currently-animating entities redrawn every frame, genuinely-idle ones
skipped) rather than the originally-flawed "server DirtySet implies render sparsity" reasoning.

**Gate**: does not start until M1 has shipped and its performance-validation pass shows a real, measured
need — not designed or built speculatively. The full design is already written (M1's plan doc §B); this
milestone scopes and executes it once gated, it doesn't re-derive it.

**Touches**: `frontend/src/components/GameCanvas.tsx`, `frontend/src/hooks/useCanvas.ts` — explicitly the
files M1's own scope keeps untouched.

### M3 — Interest Management / Spatial Broadcast Filtering (server-side, gated on M1)

**Tracking epic**: `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` (new, scope-only — see its own ticket).

Ships: turning the frontend's existing client-side, cosmetic-only vision-range filtering into real
server-side broadcast filtering — only sending a viewer the entities relevant to what they can currently
see, using the spatial-subscription field M1 reserves in its broadcast envelope specifically for this.

**Gate**: does not start until M1 has shipped and its performance-validation pass provides real bandwidth
numbers at real entity/viewer counts. An independent analytical pass this session (not a live measurement)
modeled roughly 1.5–5MB/s per viewer at a 10,000-entity target scale with a 10–20% per-tick changed
fraction — a real, non-hypothetical risk, but still an estimate, not measured evidence. M3 doesn't start
until that estimate is replaced with real numbers from M1.

**Touches**: the backend broadcast/presenter layer — not the renderer, no overlap with M2.

## Sequencing rules

- **M1 is a hard prerequisite for both M2 and M3.** Neither may start — not even be scoped into child
  tickets — before M1 ships and produces real performance numbers.
- **M2 and M3 are independent of each other.** No dependency in either direction; either can be picked up
  first once M1's gate clears, or both can proceed in parallel.
- **Detailed child-ticket breakdown for M2 and M3 is deliberately not done yet.** Both are scope-only at the
  epic tier for now, per direct instruction — this roadmap and the two epic tickets exist to capture the
  milestone structure and design intent, not to fully plan implementation before M1's real evidence exists.

## References

- `docs/plans/live_map_reconnection_epic.md` — M1's full plan doc. §B ("Layered, Cache-First Rendering
  Architecture") is M2's design source; §D ("External Design Review — Findings, Independently Verified"),
  specifically its bandwidth reassessment, is M3's design source.
- `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` — M1's ticket.
- `TCK-20260821-EPIC-LIVE-MAP-RENDERING-PERFORMANCE` — M2's ticket.
- `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` — M3's ticket.
