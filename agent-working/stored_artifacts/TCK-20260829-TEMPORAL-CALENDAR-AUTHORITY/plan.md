---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY
artifact_type: plan
tags: [temporal, determinism, world]
---

# Plan — TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

This ticket produces a decision record, not code. Each decision point below is laid out as real options with
a recommendation, per `investigation.md`'s findings — the plan owner accepts, redirects, or defers each one
before this ticket closes. No numeric threshold becomes authoritative until that sign-off happens.

**Plan-owner sign-off, 2026-08-29: all four recommendations below (Decision 1 Option A, Decision 2 Option A,
Decision 3 Option A, Decision 4's single recommended path) are ACCEPTED as written.** This closes the
decision-record scope of this ticket. It does not authorize implementation — see "What this ticket does NOT
do" below, unchanged by this sign-off.

## Decision 1 — Calendar authority

**The problem:** four live conventions (36s/tick + 2,400/day Bible; 100/day raid; 200-tick cohort/ecology
cycle; assorted raw intervals) don't reduce to one clock.

**Options:**
- **A — Adopt the World Evolution Bible's 2,400-ticks/day as sole authority; migrate raid's 100-tick alias
  and name the cohort/ecology 200-tick interval as an explicit sub-cadence, not a rival calendar.**
  (Recommended — ACCEPTED 2026-08-29.) The Bible is already the documented, cited-elsewhere authority (`rpg_design_roadmap.md`
  already treats it as such); this option changes the fewest things — raid's constant gets renamed/rescaled,
  cohort/ecology's 200-tick interval gets documented as "how often this system re-evaluates," not "how long
  a day is." Lowest-risk, most consistent with existing citations.
  - Compatible with the temporal-axis proposal's own accepted direction (§16): human days should be
    real-world-recognizable (24h), and 2,400 ticks/day already maps cleanly to a 36s tick.
- **B — Pick a different single authority (e.g. re-derive from the proposal's 120-day fantasy year) and
  migrate all four conventions to it.** Larger blast radius — every existing raw interval (30/50/100/200/500/
  1000/2000/5000 ticks) would need re-classification against the new authority, not just raid's.
- **C — Defer; keep multiple conventions but require every new time-sensitive feature to declare its own
  named unit (the proposal's §10 "temporal contract").** Doesn't resolve the existing conflict, only prevents
  new ones from being added un-named. Real but partial — likely needed regardless of A vs. B, not a
  substitute for choosing one authority for existing content.

## Decision 2 — Age/lifecycle numbers

**The problem:** under the Bible's 2,400-ticks/day, `max_age_ticks=10000` and the `≥7000` elder threshold
produce a 4.17-day maximum lifespan — 2-3 orders of magnitude off from anything resembling a lived life.

**Options:**
- **A — Migrate age representation to fantasy-year units once Decision 1 lands, per the proposal's own §9.2
  direction, rather than inventing new tick counts.** (Recommended, and blocked on Decision 1 — ACCEPTED
  2026-08-29, unblocked now that Decision 1 is decided.) Doesn't pick
  final numbers here — that's still the proposal's own §17 "exact life-stage boundaries and lifespan
  distribution," explicitly out of this ticket's scope — just confirms this ticket doesn't attempt to.
- **B — Patch `max_age_ticks`/cohort thresholds directly under the current tick regime as an interim fix.**
  Not recommended: would produce a second migration once Decision 1 lands, the exact kind of rework this
  roadmap has flagged elsewhere (e.g. Idea 66) as a real cost worth avoiding.

## Decision 3 — Universal duration formula

**The problem:** movement (`move_cost`/`readiness_speed`) is the only subsystem with a working duration
formula; combat/craft/harvest have none.

**Options:**
- **A — Generalize movement's existing readiness-cost pattern (`base_cost × modifier / rate`) as the shared
  shape for a universal formula, with combat/craft/harvest each declaring their own base cost and modifier
  set.** (Recommended — ACCEPTED 2026-08-29.) Reuses a real, tested pattern rather than inventing one from nothing — matches the
  proposal's own §16 acceptance that shared calculation should be reused while domains own their own state.
- **B — Design a new formula shape independent of movement's pattern.** No evidence today that movement's
  shape doesn't generalize; this option exists only if a future investigation finds a concrete reason A
  doesn't fit combat/craft/harvest specifically.

## Decision 4 — Metamorphic-lab pilot sequencing

**Finding:** `src/lab/metamorphic.py` exists, is CI-tested, but has zero recorded real sessions.

**Recommendation (not a real either/or — one path):** run a small, low-stakes metamorphic-lab pilot against
an already-tuned numeric surface *before* treating any number from Decisions 1-3 as balanced, mirroring the
precedent `rpg_design_roadmap.md`'s Sequencing rules already establishes for Idea 37 (M2's race-relations
matrix). This is a process step, not a design decision — flagged here so it isn't rediscovered as a surprise
once Decision 1-3's numbers reach an actual M3+ ticket.

## What this ticket does NOT do

- Pick final numeric values for anything (tick-to-second ratio changes, life-stage boundaries, pregnancy
  duration, etc.) — those stay the temporal-axis proposal's own §17 open items, downstream of Decision 1.
- Touch `src/` — this is a decision record only.
- Re-open any of the four plan-owner decisions already made and recorded this session (Idea 66, Marriage/
  Reproduction, M6 single-contract, `CultureDeriver` ownership, permadeath ownership).

## Next step (resolved)

Decisions 1-4 recorded in `rpg_design_roadmap.md`'s "Temporal axis" section, its authoritative home — the
actual calendar-authority migration (renaming `raid.py`'s constant, documenting the cohort/ecology cycle as
a named sub-cadence, `docs/mechanics/05_world_evolution.md` cross-reference cleanup) is deliberately left as
future implementation work for a dedicated ticket, per "What this ticket does NOT do" above. This ticket now
moves to `tickets/done/`.
