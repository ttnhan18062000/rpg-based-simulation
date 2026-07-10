# SimQ Roadmap — Phase 0: Reliability Foundation

Scoped 2026-07-10 from `docs/plans/simq_development_roadmap.md`. Parent plan: that roadmap doc
(no epic ticket — this is a phased roadmap, not a single-ticket epic; see the roadmap's own
"Estimated Ticket Count" section for the full 6-phase breakdown and cross-phase sequencing).

**Goal:** Confirm existing SimQ measurements mean what they claim to mean before any further corpus
investment (Phases 2–4) makes that question more expensive to answer. Blocks everything downstream.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` | Phase 0.1. Re-verifies all 18 `SLOW_ANCHOR_KEYS` long-run anchors against `docs/audits/D06_longrun_health.md` F6's wall-clock-throttle finding. No dependency on 0.2. |
| 2 | `TCK-20260710-SIMQ-CONTRACT-AC-CLOSEOUT` | Phase 0.2. Closes out `quality_scoring_contract.md` §12's unchecked Acceptance Criteria. Independent of 0.1, but cleaner to cite Traceability/Testing items once 0.1 has landed — can run in parallel or either order. |

Both tickets are self-contained; neither blocks Phase 1 (which runs in parallel in a separate
folder). Phases 2–4 (corpus depth waves) should not start until both items here have landed, per
the roadmap's critical path.

See `docs/plans/simq_development_roadmap.md` §"Phase 0 — Reliability Foundation" for full
problem/evidence detail behind each ticket.
