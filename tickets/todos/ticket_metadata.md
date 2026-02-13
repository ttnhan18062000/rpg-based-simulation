# Ticket Metadata

Master index of all active tickets with priority, effort estimate, dependencies, and status.

**Last updated:** 2025-02-12

---

## Legend

| Column | Values |
|--------|--------|
| **Priority** | P0 (critical) · P1 (high) · P2 (medium) · P3 (low) |
| **Effort** | XS (< 1h) · S (1–4h) · M (4–16h) · L (2–5d) · XL (1–2w) · XXL (2w+) |
| **Status** | `needs-decision` · `ready` · `in-progress` · `done` |
| **Type** | bug · enhance · adjust · design · epic · infra |

---

## Bugs

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| bug-01 | [Diagonal Adjacent HUNT Move Conflict](bug-01-diagonal-hunt-move-conflict.md) | P1 | S | done | — |
| bug-02 | [Hero Keeps Looting When Full Bag](bug-02-hero-looting-full-bag.md) | P1 | S | done | — |

## Enhancements

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| enhance-01 | [Enrich Event Information](enhance-01-enrich-event-information.md) | P2 | M | done | — |
| enhance-02 | [Bag Max Capacity UI](enhance-02-bag-max-capacity-ui.md) | P3 | XS | done | bug-02 (related) |
| enhance-03 | [Extend Max Tick to 50000](enhance-03-extend-max-tick-limit.md) | P3 | XS | done | epic-16 (verify perf first) |
| enhance-04 | [Mob Roaming Leash Distance](enhance-04-mob-roaming-leash.md) | P1 | M | done | — |

## Adjustments

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| adjust-01 | [Action Speed Balance Review](adjust-01-action-speed-balance.md) | P2 | S | done | design-02 (related) |

## Design Reviews

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| design-01 | [Skill & Basic Attack Stat Scaling](design-01-skill-stat-scaling.md) | P1 | S | done | — |
| design-02 | [Revise Ticking Mechanism](design-02-revise-ticking-mechanism.md) | P2 | M | done | — |

## Infrastructure (Testing & Profiling)

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| infra-01 | [Automated Testing Infrastructure](infra-01-automated-testing.md) | P0 | S | done | — |
| infra-02 | [Performance Profiling Infrastructure](infra-02-performance-profiling.md) | P0 | S | done | — |

**Automation commands:**

| Command | What it does |
|---------|-------------|
| `make test` | Run all 440+ Python tests |
| `make test-quick` | Run fast tests only (skip `@slow`) |
| `make test-cov` | Run tests with coverage report |
| `make profile` | 500-tick performance report (timing, phases, entity counts) |
| `make profile-full` | 2000-tick profile + cProfile `.prof` dump |
| `make profile-memory` | 500-tick profile with tracemalloc memory snapshot |

## Epics (New)

| ID | Ticket | Priority | Effort | Status | Dependencies |
|----|--------|----------|--------|--------|-------------|
| epic-15 | [Region & World Overhaul](epic-15-region-difficulty-scaling.md) | P1 | XL | in-progress | — |
| epic-16 | [Performance Audit & Optimization](epic-16-performance-audit.md) | P2 | L | ready | — |

## Epics (Existing — Updated)

| ID | Ticket | Priority | Effort | Status | Dev Note |
|----|--------|----------|--------|--------|----------|
| epic-05 | [Advanced Combat Mechanics](epic-05-advanced-combat-mechanics.md) | P1 | XXL | ready | F4 (Ranged Combat) flagged as standalone priority |
| epic-11 | [Replay & Observation Tools](epic-11-replay-and-observation-tools.md) | P2 | XXL | ready | Rewind-to-event UX added as MVP path |

## Epics (Existing — Unchanged)

| ID | Ticket | Priority | Effort |
|----|--------|----------|--------|
| epic-01 | [Dungeon System](epic-01-dungeon-system.md) | P3 | XXL |
| epic-02 | [NPC & Social System](epic-02-npc-and-social-system.md) | P3 | XXL |
| epic-03 | [Day/Night & Weather](epic-03-day-night-and-weather.md) | P3 | XL |
| epic-04 | [Multi-Hero Party System](epic-04-multi-hero-party-system.md) | P2 | XXL |
| epic-06 | [World Events & Invasions](epic-06-world-events-and-invasions.md) | P3 | XXL |
| epic-07 | [Reputation & Faction Diplomacy](epic-07-reputation-and-faction-diplomacy.md) | P3 | XL |
| epic-08 | [Transcendence & Endgame Classes](epic-08-transcendence-and-endgame-classes.md) | P3 | XL |
| epic-09 | [Improved Pathfinding & Movement](epic-09-improved-pathfinding-and-movement.md) | P2 | XL |
| epic-10 | [Enchantment & Item Progression](epic-10-enchantment-and-item-progression.md) | P3 | XL |
| epic-12 | [AI Personality & Emergent Behavior](epic-12-ai-personality-and-emergent-behavior.md) | P2 | XXL |
| epic-13 | [Ruins Exploration & Lore](epic-13-ruins-exploration-and-lore.md) | P3 | XXL |
| epic-14 | [Frontend UX Improvements](epic-14-frontend-ux-improvements.md) | P2 | XL |

---

## Recommended Execution Order

Tickets that need developer decision before work can start are marked. Suggested order for actionable items:

### Phase 0 — Infrastructure (DONE)

- ✅ **infra-01** — Automated testing (`make test`, deterministic replay, conflict resolver, inventory goals)
- ✅ **infra-02** — Performance profiling (`make profile`, per-tick phase timing, memory profiling)

### Phase 1 — Bugs & Quick Wins (needs-decision → ready → ship)

1. ✅ **bug-01** — Diagonal HUNT conflict — higher-ID entity yields at Manhattan 2 — 5 tests in `test_conflict_resolver.py`
2. ✅ **bug-02** — Looting when full bag — `is_effectively_full` checks slots + weight — 8 tests in `test_inventory_goals.py`
3. ✅ **enhance-02** — Bag capacity UI — slot + weight bars with color coding in InspectPanel
4. ✅ **enhance-03** — Extend max tick to 50000 + EventLog ring buffer (10k cap)
5. ✅ **enhance-04** — Mob roaming leash — radius 15, chase cap 1.5×, give-up 20 ticks, 5% HP/tick heal on return — 17 tests in `test_mob_leash.py`

### Phase 2 — Design Decisions (needs-decision)

6. ✅ **adjust-01** — Action speed balance — doubled all delay multipliers, added building interaction delays — SPD stat now meaningful
7. ✅ **design-01** — Skill stat scaling — damage_type on SkillDef, DamageCalculator routing, crit/variance/evasion on skills — 16 tests in `test_skill_scaling.py`
8. ✅ **design-02** — Revise ticking mechanism — fixed empty-tick stall bug, subsystem rate divisors (core/env/economy) — 11 tests in `test_subsystem_ticks.py`

### Phase 3 — Gameplay Enhancements

9. ✅ **enhance-01** — Enrich event info — metadata on SimEvent, enriched combat/loot/death/level_up/skill events — 9 tests in `test_enriched_events.py`
10. 🔧 **epic-15** — Region & World Overhaul — Phase A–D done: Region/Location dataclasses, 192×192 map, sub-locations, difficulty stat scaling (HP/ATK/DEF/gold/level by tier 1–4), boss arena +1 difficulty, minimap labels, locations panel, EPIC rarity + items, loot quality scaling by difficulty tier (F4), tier 4 chests, region enter/leave events (F9), hero AI difficulty awareness (F8) — 30 tests in `test_regions.py`, 13 in `test_difficulty_scaling.py`, 14 in `test_loot_scaling.py`, 12 in `test_region_events.py`

### Phase 4 — Major Features

11. **epic-05 F4** — Ranged combat *(standalone from full epic)*
12. **epic-16** — Performance audit *(before scaling up)*
13. **epic-11** — Replay & observation tools *(after enhance-01)*

### Phase 5 — Long-term Epics

14. Remaining epics (01–04, 06–10, 12–14) prioritized by developer preference
