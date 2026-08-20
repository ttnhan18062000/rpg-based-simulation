# Ticket Metadata

Master index of all active tickets with priority, effort estimate, dependencies, and status.

**Last updated:** 2026-08-20 — reconciliation pass. This table had gone stale since 2026-06-12:
several epics below were reclassified after direct verification against live `src/` and
`tickets/working_log.csv` found real feature work had landed under unrelated internal
`Epic 4.x`/`5.x` (E41/E43/E52/E53) and `TCK-` naming since 2026-06-19, never reconciled back
into this file. See the updated Completed/Partially Completed tables below for exact evidence
citations.

---

## Legend

| Column | Values |
|--------|--------|
| **Priority** | P0 (critical) · P1 (high) · P2 (medium) · P3 (low) |
| **Effort** | XS (< 1h) · S (1–4h) · M (4–16h) · L (2–5d) · XL (1–2w) · XXL (2w+) |
| **Status** | `needs-decision` · `ready` · `in-progress` · `done` |
| **Type** | bug · enhance · adjust · design · epic · infra |

---

## Completed Work

All bugs, enhancements, adjustments, design reviews, and infrastructure tickets are **done**.

| ID | Ticket | Type | Summary |
|----|--------|------|---------|
| bug-01 | Diagonal HUNT Move Conflict | bug | Higher-ID entity yields at Manhattan 2 |
| bug-02 | Hero Looting Full Bag | bug | `is_effectively_full` checks slots + weight |
| enhance-01 | Enrich Event Information | enhance | Metadata on SimEvent, enriched combat/loot/death/level_up/skill events |
| enhance-02 | Bag Max Capacity UI | enhance | Slot + weight bars with color coding |
| enhance-03 | Extend Max Tick to 50000 | enhance | EventLog ring buffer (10k cap) |
| enhance-04 | Mob Roaming Leash | enhance | Radius 15, chase cap 1.5×, give-up 20 ticks, 5% HP/tick heal on return |
| adjust-01 | Action Speed Balance | adjust | Doubled delay multipliers, SPD stat meaningful |
| design-01 | Skill Stat Scaling | design | DamageCalculator routing, crit/variance/evasion on skills |
| design-02 | Revise Ticking Mechanism | design | Fixed empty-tick stall, subsystem rate divisors |
| infra-01 | Automated Testing | infra | `make test`, deterministic replay, 575+ tests |
| infra-02 | Performance Profiling | infra | `make profile`, per-tick timing, memory profiling |
| infra-03 | Telemetry & Observability | infra | Prometheus mapping, automated docker deployment, Grafana dashboards via containerized stack, test automation |
| infra-04 | Realtime State Streaming | infra | Shifted 80ms HTTP polling to highly optimized unidirectional SSE delta payloads, heavily reducing network burden |
| infra-05 | Distributed AI Workers | infra | Integrated RabbitMQ to distribute AI evaluations to scalable daemon processes bypassing the GIL |
| infra-07 | Redis Streams Event Bus | infra | Replaced local asyncio.Queues with a Redis Stream for system-wide event broadcasting and delta state distribution |

**Automation commands:**

| Command | What it does |
|---------|-------------|
| `make test` | Run all 575+ Python tests |
| `make test-quick` | Run fast tests only (skip `@slow`) |
| `make test-cov` | Run tests with coverage report |
| `make profile` | 500-tick performance report (timing, phases, entity counts) |
| `make profile-full` | 2000-tick profile + cProfile `.prof` dump |
| `make profile-memory` | 500-tick profile with tracemalloc memory snapshot |

---

## Completed Epics

| ID | Ticket | Effort | Summary |
|----|--------|--------|---------|
| epic-15 | Region & World Overhaul | XL | Voronoi tessellation, 512×512 map, 8 biomes, 9 factions, tier 1–4 difficulty, loot scaling, region events, hero AI awareness |
| epic-16 | Performance Audit | L | Backend: 43% faster ticks (49.8ms→28.4ms), 70% fewer function calls. Frontend: 256× smaller overlay, drag-skip, minimap caching, 98% API payload reduction |
| epic-19 | [Kafka Event-Sourcing](epic-19-event-sourcing-persistence.md) | XL | Long-term durability via Apache Kafka; append-only event-sourcing allows infinite rewinds and ML data pipelines. |
| epic-04 | [Multi-Hero Party System](epic-04-multi-hero-party-system.md) | XL | **Found 2026-08-20, previously untracked here.** Delivered under internal "Epic 4.1 Full Party Adventure Loop" (E41A–E41H, `working_log.csv` 2026-06-20→06-28) — leadership election, defection/escort, `FairShareProtocol`, dedicated 500-tick multi-hero test. `src/systems/social_systems/party.py` (`PartyCoordinationSystem`), `party_lifecycle.py`, `party_composition.py`. Exceeds this epic's original scope. |

## Partially Completed Epics

| ID | Ticket | Done | Remaining | Status |
|----|--------|------|-----------|--------|
| epic-18 | [Entity Progression Depth](epic-18-entity-progression-depth.md) | Leveling Curve, Phase D Evolution, Veterancy (`src/progression/leveling.py`, `evolution.py`, `veterancy.py`, `breakthroughs.py`, all real and current) | Skill Discovery, Milestones, Battle Marks | partial — core evolution and veterancy are functional. **Flagged 2026-08-20:** "Racial Profiles" done-claim could not be re-verified — zero hits for `racial_profile`/`RacialGrowth`/per-race growth rate anywhere in current `src/`; may have been renamed/removed in a later refactor, or the original claim was already inaccurate. Left as an open question per the Uncertainty Rule rather than flipped either way. |
| epic-09 | [Pathfinding & Movement](epic-09-improved-pathfinding-and-movement.md) | F1 (A*), F2 (Terrain Costs), F4 (Path Cache), F6 (Obstacle Avoidance), F9 (Terrain Detail), F10 (Tile Tooltip) | F3 (Hazard Avoidance), F5 (Formations), F7 (Speed Mods), F8 (Path Viz) | partial — core pathfinding complete, remaining features are polish. **Corrected 2026-08-20:** the epic doc's cited implementation file (`src/ai/pathfinding.py`) no longer exists — current navigation is a rewritten flow-field architecture (`src/systems/world_systems/navigation.py`: `FlowFieldService`, `NavigationSystem`). The claimed-done pieces likely still function under the new architecture, but the doc's technical references are stale. |
| epic-06 | [World Events & Invasions](epic-06-world-events-and-invasions.md) | **Found 2026-08-20, previously listed "Open"/subsumed-only.** Real raid/war/siege mechanics live: `src/world/raid.py` (`RaidService.check_for_raid`), `src/engine/military_conflict.py` (`MilitaryConflictPhase`), `src/domains/world_emergence/`. Internal "Epic 5.3 Territorial Conflict & War" (`SiegeState`, war exhaustion) landed 2026-06-22. | The generic `WorldEvent`/`EventDef` registry this epic's doc specifies (resource events, environmental disasters as a unified framework) — not confirmed to exist; only the specific raid/war/invasion mechanics are real. | partial — functionally equivalent invasion/raid/war behavior shipped, but not via the generic event-framework architecture the doc describes. |
| epic-07 | [Reputation & Faction Diplomacy](epic-07-reputation-and-faction-diplomacy.md) | **Found 2026-08-20, previously listed "Open" P1.** A real dynamic diplomacy state machine is live: `src/domains/faction/diplomatic_state_machine.py` (`compute_transitions`, `events_from_transitions`), `diplomatic_actions.py` (treaty offer, trade agreement, non-aggression pact, alliance proposal, betrayal), `DiplomaticState` enum (NEUTRAL/TENSE/HOSTILE/WAR/ALLIED/VASSAL). Internal "Epic 5.3 Faction & Diplomacy System" (E53A–E53D) landed 2026-06-22. | The epic's -1000..+1000 tiered reputation system — only a simpler caution-modifier version exists (`src/systems/social_systems/reputation.py::ReputationService`). | partial — core "shifting alliances and faction wars" deliverable shipped; reputation piece is simpler than originally scoped. |
| epic-11 | [Replay & Observation Tools](epic-11-replay-and-observation-tools.md) | **Found 2026-08-20, previously listed "Open" P2.** Backend is production-grade and mature: `src/engine/replay_buffer.py`, `replay_manager.py` (`ReplayManager`: emit, rotate chunks, persistence, pressure reporting), `replay_sink.py`, `src/core/replay_modes.py`, `src/replay/fingerprint.py` — backed by multiple DONE `TCK-` REPLAY tickets. | F3 (timeline scrubbing UI), F4 (entity tracking UI) — no matching component found anywhere in `frontend/src/`. | partial — backend complete, frontend UI layer not started. Recommend re-scoping the remaining ticket to frontend-only rather than treating as a fresh XXL epic. |
| epic-12 | [AI Personality & Emergent Behavior](epic-12-ai-personality-and-emergent-behavior.md) | **Found 2026-08-20, previously listed "Open" P1.** F1 (long-term memory) + F2 (nemesis system) essentially delivered: `SocialComponent.grudge_history`/`nemesis_ids` (`src/core/models/social.py`), `check_nemesis_promotion` (`src/systems/social_systems/memory.py`), `NemesisRelation` (`src/domains/campaigns/state.py`), live use in AI scoring (`src/engine/cognition.py`) and combat (`src/engine/combat.py`: `grudge_delta` per hit). Internal "Epic 4.3 Social Memory as Campaign Consequence" (E43A–E43H) landed 2026-06-20→06-28. | F3 (confidence/mood) — not separately verified in this pass. | partial — the two highest-ROI pieces (memory, nemesis) are real and live; confidence/mood needs a dedicated follow-up check. |
| epic-20 | [Calamity (World Boss) System](epic-20-calamity-system.md) | **Found 2026-08-20, previously listed "Open" P1 with only "prototype... in progress."** Real drift since: `src/world/calamity.py`, `src/world/boss.py` (`BossService.check_for_boss_spawn/resolve_boss_death`), `CalamityPressurePropagator` (`TCK-20260628-E52E-SEASONAL-PROPAGATION`, DONE 2026-06-28, seasonal calamity pressure propagation between adjacent regions), plus `calamity`/`boss`/`raid` tracked as SimQ world-dynamics events (`TCK-20260629-SIMQ-EMIT-WORLD`). | Full randomized spec (per the epic's own original "in progress" note) — not independently re-verified this pass. | partial — substantially more built than the "Open" listing implied; the epic's own status line is itself already outdated. |
| epic-03 | [Day/Night & Weather](epic-03-day-night-and-weather.md) | **Found 2026-08-20, previously listed "Open" P2.** A real weather-modifier system exists (`region.weather` field, `src/world/environment.py::EnvironmentService.get_weather_multipliers()` — real STORM/RAIN/SNOW/BLIZZARD modifiers on perception/evasion/move_speed/stamina_drain, last touched 2026-07-02). `world_time`-driven `is_night` branches are real and live (`src/systems/world_systems/routine.py`, `src/ai/goals/scorers.py`). | Nothing in `src/` ever writes `region.weather` to a non-CLEAR value — the modifier consumer exists but the weather *generator* doesn't; no `TimePhase`/DAWN/DUSK enum for a full day/night cycle either. | partial — real scaffolding exists but is currently dead/unreachable; needs a weather generator to actually activate it, not a from-scratch build. |

---

## Open Epics — Prioritized by Emergent Storytelling Impact

Epics re-ordered by how much they contribute to **emergent narrative moments** — the core vision of the project.

### Priority 0 — Progression Spine (build this first)

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-17 | [Long-Story Progression Spine](epic-17-long-story-progression.md) | **P0** | XXL | Fixes the level-20 ceiling. Multi-hero, death stakes, world evolution, raids, world boss, dungeon, transcendence, hall of fame. Subsumes slimmed-down parts of E01, E04, E06, E08. Without this, the simulation stalls at tick 10,000. |
| epic-18 | [Entity Progression Depth](epic-18-entity-progression-depth.md) | **P0** | XL | Deepens micro-level growth for ALL entities. Veterancy, evolution, innate talent, toughness, revised leveling curve, skill discovery, attribute milestones, racial growth profiles, battle marks. Every living thing in the world grows through experience. |

### Tier 1 — High-Impact Narrative

**2026-08-20:** all three items originally listed here (epic-12, epic-07, epic-20) were found
partially delivered — see the Partially Completed Epics table above for evidence. Table left
empty rather than deleted, to preserve the original prioritization rationale.

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|

### Tier 2 — World Richness (deepen the world)

**2026-08-20:** epic-03 moved to Partially Completed Epics above (real weather-modifier
scaffolding exists but is dead/unreachable) — see that table for evidence.

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-02 | [NPC & Social System](epic-02-npc-and-social-system.md) | **P2** | XXL | Living town with schedules, relationships — the town becomes a character in the story. **Verified 2026-08-20:** the specific NPC-schedule/dialogue deliverable is still not started (no `NPCDef`, `src/town/*` remains static utility-point services), but a much richer entity-generic relationship substrate than this epic asked for already exists: `SocialComponent` (`src/core/models/social.py`: trust/familiarity/debt/fear/grudge/bonds/reputation), `src/systems/social_systems/relationships.py`, and biological-needs/day-night routine logic (`src/systems/world_systems/routine.py`). Worth re-scoping around this substrate rather than building from scratch. |
| epic-13 | [Ruins Exploration & Lore](epic-13-ruins-exploration-and-lore.md) | **P3** | XXL | Discovery and world history — rewards curiosity, adds narrative depth. **Verified 2026-08-20:** genuinely not started — "ruins" only exists as a generic semantic/quest-routing tag, no drift from the 2026-06-12 snapshot. |

### Tier 3 — Depth & Polish (enrich existing systems)

**2026-08-20:** epic-11 moved to Partially Completed Epics above (backend done, frontend UI
remaining) — see that table for evidence.

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| epic-05 | [Advanced Combat (remaining)](epic-05-advanced-combat-mechanics.md) | **P2** | L | Status ailments, combos, environmental combat — richer tactical combat moments. **Verified 2026-08-20:** AoE (F1) and a real `src/engine/domain/aoe_actions.py` implementation are current and live. The specific per-attacker `threat_table` aggro design (F3) this doc cites no longer exists under that name — `src/world/threat.py` is a *regional* threat-evolution service, not per-entity aggro/taunt; status ailments (F6) and combos (F2, gated on F6) remain absent. Doc's technical references are partly stale, same pattern as epic-09. |
| epic-10 | [Enchantment & Item Progression](epic-10-enchantment-and-item-progression.md) | **P3** | XL | Gear becomes meaningful and personal — socketing, enhancement, item sets. **Verified 2026-08-20:** genuinely not started — "enchant" hits are only flavor-named crafting recipes, no enhancement-level or socket system exists. No drift. |
| epic-14 | [Frontend UX Improvements](epic-14-frontend-ux-improvements.md) | **P2** | XL | Smooth animations, combat numbers, keyboard shortcuts — better watching experience. **Verified 2026-08-20:** genuinely not started — no toast/notification, damage-number, hotkey, or interpolation code found in `frontend/src/components/`. No drift. |
| epic-09 | [Pathfinding (remaining)](epic-09-improved-pathfinding-and-movement.md) | **P3** | M | Hazard avoidance, formations, speed modifiers, path visualization — polish. |

### Subsumed by Epic-17 (slimmed-down versions included)

**2026-08-20:** epic-04 moved to Completed Epics and epic-06 moved to Partially Completed
Epics above — both had real implementation land under unrelated internal naming since
2026-06-19. See those tables for evidence.

| ID | Ticket | What E17 Takes | What Remains |
|----|--------|----------------|-------------|
| epic-08 | [Transcendence & Endgame Classes](epic-08-transcendence-and-endgame-classes.md) | **P4 of Epic-20** | Trial quests, visual identity, post-transcendence growth. **Verified 2026-08-20:** genuinely not started — zero hits for "transcend"/`Warlord`/`Windwalker`/`Phantom` anywhere in `src/`. No drift. |
| epic-01 | [Dungeon System](epic-01-dungeon-system.md) | Single dungeon instance | Full dungeon generation, traps, loot tables, cooldowns. **Verified 2026-08-20:** genuinely not started — zero hits for `DUNGEON_ENTRANCE`/`DungeonTemplate`/`dungeon_instance` anywhere in `src/`. No drift. |

---

## Open Architecture & Tech Stack Improvements

| ID | Ticket | Priority | Effort | Why |
|----|--------|----------|--------|-----|
| design-03 | [Data-Driven Registries](design-03-data-driven-registries.md) | **P1** | M | Foundation for Epic-18; decouples configs from Python logic. |
| infra-06 | [Hardening & Chaos Testing](infra-06-hardening-and-chaos-testing.md) | **P3** | M | Property-Based Testing (Hypothesis) and fault injection. |

---

## Recommended Next Steps

**2026-08-20 note:** steps 7 and 9 below (epic-12 nemesis system, epic-07 faction diplomacy)
were written when both epics were believed fully unstarted. Per the reconciliation above, their
core deliverables substantially already shipped (2026-06-20→06-28) — this sequencing advice is
itself now partly stale and worth re-deriving from what's actually left (epic-12's confidence/
mood piece, epic-07's reputation-tier piece), not re-scoped here.

1. **epic-18 Phase A** (Leveling Curve + Racial Profiles) — fix the flat growth first; every entity benefits immediately
2. **epic-18 Phase B** (Veterancy + Talent) — make every entity an individual that grows through combat
3. **epic-17 Phase 1** (Multi-Hero + Death Stakes) — multiple heroes with the new progression = divergent stories
4. **epic-18 Phase C+D** (Toughness + Evolution) — mobs evolve organically; the world grows alongside heroes
5. **epic-17 Phase 2** (World Evolution) — world age, raids, world boss, camp reinforcement
6. **epic-18 Phase E+F** (Skill Discovery + Milestones + Marks) — entities earn identity through experience
7. **epic-12** (AI Personality) — nemesis system on top of marked, veteran, evolved entities = rich stories
8. **epic-17 Phase 3** (Endgame) — level cap 30, transcendence, dungeon, legendary items, hall of fame
9. **epic-07** (Faction Diplomacy) — dynamic alliances make the faction map a living story
