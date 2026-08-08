---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING
artifact_type: test_plan
tags: [strategy, simulation-quality, progression]
---

# test_plan.md — TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING

## Regression Surface

- `tests/unit/ai/`, `tests/unit/engine/` (new modules touched)
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/world/test_guild_intel.py`
  (`GuildAction.visit()`'s own existing suite — must still pass unmodified, since its own logic
  was not touched)
- `tests/architecture/test_guild_action_dormancy.py` (the pre-existing guard, expected to change
  shape, not fail silently)
- `tests/unit/strategic/`, `tests/unit/kernel/` (`GoalKind`/`GoalRegistry`/`Kernel` touched)
- `tests/unit/config/test_phase10_feature_flags.py`, `tests/integration/scenarios/
  test_balance_regression.py` (new feature flag added)

## New Tests Required

- `GuildNeedScorer`: flag OFF → utility 0; flag absent → utility 0; at project capacity → utility
  0; flag ON + spare capacity + nearby `town_hall` → real `GoalScore` with correct
  `target_id`/`target_pos`; no `town_hall` in world → utility 0.
- `GuildVisitPhase`: flag OFF/absent → no-op even with an active guild project; arrived (dist ≤ 1)
  → completes visit, marks project `COMPLETED`, clears `current_project_id`/
  `current_objective_id`; not yet arrived → no-op; non-`guild`-kind project → ignored; `SUSPENDED`
  project → ignored; missing building / unparseable target → no-op (never crashes).
- `test_guild_action_dormancy.py`: updated (not deleted) to confirm the reference is limited to
  exactly the one deliberate site (`guild_visit.py`) — still a real guard against future
  unreviewed dispatch sites.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/ai/ tests/unit/engine/ \
  tests/unit/world/test_guild_pipeline.py tests/unit/world/test_guild_intel.py \
  tests/architecture/test_guild_action_dormancy.py -q

.venv/bin/python3 -m pytest tests/unit/strategic/ tests/unit/kernel/ -q

.venv/bin/python3 -m pytest tests/unit/config/test_phase10_feature_flags.py \
  tests/integration/scenarios/test_balance_regression.py -q
```

## Real-kernel verification (beyond unit tests — required, given this touches the AI decision
## layer)

1. **Controlled arrival test**: synthetic entity placed exactly at `hero_guild_routing`'s real
   `town_hall` with a hand-constructed active `guild` project — confirms `GuildVisitPhase`
   generates a genuine `QuestState` in one tick, proving the mechanism correct end-to-end
   independent of AI-decision timing.
2. **Natural, unmodified runs**: `sandbox_world_seed42` (3000 ticks, flag ON, no synthetic setup)
   — confirms the full goal-competition → movement → arrival → quest-generation chain works via
   the live AI decision layer alone. `hero_guild_routing`/`urban_political` at 1500-3000 ticks —
   confirms no crash, and documents (doesn't hide) that combat-heavy worlds may not complete a
   guild visit within tested tick budgets (a real behavioral characteristic of GUILD's
   deliberately modest utility, not a defect).
3. Real, non-mocked monkeypatch tracing of `TacticalDecisionSystem._resolve_target_position()`
   during a live run — used to diagnose (not just guess) the `TownScorer` target-encoding bug
   before deciding how to route around it.

## Anti-Drift Test Guards

Any future ticket wiring another town-service action (`InnAction`/`ClassHallAction`/`HomeAction`)
should re-run this same real-kernel verification discipline (controlled arrival test + natural
run), not assume unit tests alone are sufficient — this ticket's own investigation found 3
distinct architectural blockers (`_resolve_target_position` parsing, no real building content,
`WorkerPacket`'s state-access restriction) that only surfaced through real-kernel tracing, not
static reading.
