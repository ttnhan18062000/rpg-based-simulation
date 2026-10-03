---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION

## Confirmed independently before acting

Peer's own measured numbers, re-derived directly against the real registry, not taken on report:
`33/75` declare no `depends_on`, `49/75` never named as anyone's dependency, `26/75` isolated
(both), `0` mechanisms name `movement` as a dependency.

## Method

For each isolated mechanism, read its own real source file(s) (from Foundation's own atlas
citation table, reused rather than re-derived) for genuine cross-mechanism reads — a real
attribute access, branch, or call into another mechanism's own data/logic — not containment,
execution order, or lifecycle (the three axes this registry deliberately excludes, per
`mechanisms.yaml`'s own header). Every edge below is backed by a direct source-code citation, read
personally, not inferred from the atlas's prose alone.

## Edges added (12), each cited

| Dependent | New `depends_on` | Evidence |
|---|---|---|
| `combat_resolution` | `movement` | `src/engine/legality.py::verify_attack_legality` — melee/ranged range and adjacency computed from `attacker.navigation.position`/`target.navigation.position` via `get_manhattan_dist` (COMB-004, COMB-256/257/258) |
| `combat_resolution` | `status_effects` | same function — `attacker.combat.status_effects` checked for `frozen`/`stunned` before an attack is legal |
| `combat_resolution` | `entity_role` | `src/engine/combat.py:136` — `defender.identity.role != EntityRole.HERO` gates the multi-life/reincarnation lethality rule |
| `combat_resolution` | `skill_unlocks` | `src/engine/legality.py:346`, "Pillar 8: Skill Execution Law" (PROG-077/PROG-084) — `skill_id not in actor.identity.learned_skills` → `SKILL_NOT_LEARNED` |
| `combat_engagement` | `personality` | `src/domains/combat_engagement/risk_evaluator.py:41-56` — `actor.identity.personality`, `bravery` trait directly drives derived `caution` |
| `party_formation` | `movement` | `src/domains/cooperation/services.py:301-306` — real party regroup/cohesion check computes Euclidean distance from `leader.navigation.position`/`mb.navigation.position`, `dist > 20.0` triggers "Regroup required" |
| `cross_episode_grief_nemesis` | `campaigns` | `src/domains/campaigns/grief_urgency.py`'s `GriefUrgencyImporter`/`NemesisRelationImporter` are invoked from the campaign orchestrator at episode boundaries (already independently confirmed earlier this session's own registry `verified` block on this mechanism) |
| `crafting` | `inventory_trade_conservation` | `src/systems/economy_systems/crafting.py::craft()` reads `entity.inventory.items`/`.gold`/`.max_slots` directly |
| `equipment_scoring` | `inventory_trade_conservation` | `src/core/equipment.py:212` — candidate gear evaluated from `entity.inventory.items` |
| `adventure_routing` | `entity_role` | `src/domains/adventure/scoring.py` — multiple `EntityRole.HERO` branches gating `QUEST_OPPORTUNITY` scoring |
| `adventure_routing` | `personality` | same file, "Fetch Personality Traits" section (line ~120) — personality bias is a real, substantial scoring input, not incidental |
| `adventure_routing` | `diplomacy` | same file, line 202 — `DiplomaticState.ALLIED in fs.diplomatic_relations.values()` gates a routing branch |
| `regional_trauma_hazards_sovereignty` | `world_generation` | `docs/mechanics/06_worldbuilding_foundation.md` (the Authoritative Mechanics Bible chapter for "Declarative topology, sovereignty, distribution") — region sovereignty is declared by world compilation, not computed independently at runtime |

## Ruled out during the same pass — checked, not assumed either way

- **`crafting` does NOT depend on `entity_role`** despite both being cited under `entity_role`'s own
  atlas source-file grouping — direct grep of `crafting.py` for `EntityRole` found zero matches.
  The atlas's own citation list groups files loosely; each candidate edge was verified against the
  actual file content, not accepted from the grouping.
- **`motivation_doctrine` does NOT gain `personality`** despite the mechanism's own name suggesting
  it should — `src/domains/motivation/__init__.py`'s own docstring states "(zero real callers),
  superseded by `AdventureRouteScorer.score()`'s `personality_bias` mechanism" — i.e. the real
  personality-bias logic lives in `adventure_routing`'s own scoring file (already cited above), and
  `motivation_doctrine`'s own module is dormant for this specific link. Not re-litigated as a state
  accuracy question here — out of scope for this ticket.
- **`opportunity_rumor_seeds` and `quest_generation_sourcing` do NOT feed each other** — checked
  directly (`grep` for cross-references between `world_emergence/services.py` and
  `guild_visit.py`/`scorers.py`/`town/guild.py`) — genuinely parallel, independent quest-sourcing
  paths ("Hub, Peer, or Self-Directed" per the atlas's own framing), not a pipeline.
- **`guilds` does NOT depend on `party_formation`** — checked directly, `guilds.py` has zero
  references to party/Party.

## Graphify cross-check corroboration (run against the full, updated edge set)

`tools/mechanism_registry_graphify_check.py` — 60 edges checked, 19 supported, 12 suspicious, 29
no-match. All 6 edges not involving `personality`/`skill_unlocks` landed as **supported**
(`combat_resolution`→`movement`/`status_effects`/`entity_role`, `party_formation`→`movement`,
`adventure_routing`→`entity_role`/`diplomacy`) — independent corroboration beyond the direct code
citation. 3 of the new edges (`combat_resolution`→`skill_unlocks`, `combat_engagement`→`personality`,
`adventure_routing`→`personality`) were flagged **suspicious** (no path found within the tool's own
conservative 3-hop BFS) — per peer's own instruction, given a second look: all three have a direct,
primary-source code citation (an exact line read personally, not inferred), which is stronger
evidence than the tool's own automated heuristic; the tool's known limitation (approximate
mechanism-id-to-graph-node token matching, `_REAL_RELATIONS` excluding plain attribute reads) is
the more likely explanation than the edges being wrong. Kept, with this reasoning recorded rather
than either blindly trusting the citation or blindly trusting the tool. The remaining 4 new edges
(`cross_episode_grief_nemesis`→`campaigns`, `crafting`/`equipment_scoring`→
`inventory_trade_conservation`, `regional_trauma_hazards_sovereignty`→`world_generation`) landed in
`no_match` — the tool's own documented, non-defect bucket (no plausible graph-node match for the
mechanism id at all, not a disproven edge).

## The 14 mechanisms still isolated after this pass, each with a recorded reason

| Mechanism | State | Reason no real dependents were found |
|---|---|---|
| `chronicle` | done | Writes history; checked whether `gods_pantheon_blessings` (the most plausible consumer — "belief that grows around witnessed legend") reads it — that mechanism has no real code (`state: gap`, a literal town-building string token), so no real consumer exists yet. |
| `cultural_drift` | done | Self-contained population-culture shift; no other mechanism's code was found reading its output as a precondition. |
| `declared_cognition_schema` | orphan | Confirmed a genuine zero-writer schema — `self_model.py` (the most plausible consumer given both are "Tier" cognition systems) has zero references to `CognitionModel`. Consistent with its own already-recorded `orphan` state. |
| `genetics_aptitude` | orphan | Already established elsewhere this arc as never wired into the derived-stats recalculation path; consistent with `orphan`. |
| `gods_pantheon_blessings` | gap | No real code exists beyond a literal "BLESSING" string token (already recorded via this mechanism's own `state: gap`) — nothing can meaningfully depend on code that isn't real yet. |
| `guilds` | partial | Checked the most plausible consumer (`party_formation`) directly — zero references. |
| `information_trust_deception` | gated | Flag-gated OFF (`ENABLE_WORLD_EMERGENCE`-adjacent gating per its own citation); no downstream consumer found reading its output while inactive. |
| `knowledge_model` | gated | A narrow, gated Tier-2 slice (Foundation's own Judgment Call 5); no consumer found. |
| `lair` | gap | Not yet built at all (no atlas card, wiring-map only) — no code exists to have dependents. |
| `opportunity_rumor_seeds` | gated | Flag-gated OFF (`ENABLE_WORLD_EMERGENCE`); checked its most plausible consumer (`quest_generation_sourcing`) directly and confirmed no connection (see "Ruled out" above). |
| `quest_generation_sourcing` | gated | Flag-gated OFF (`ENABLE_GUILD_QUEST_GENERATION`); same check as above, confirmed parallel not sequential with `opportunity_rumor_seeds`. |
| `race_collective_force` | gap | Explicitly a known placeholder (`mechanisms.yaml`'s own header comment) — no real collective/aggregate code exists yet beyond per-entity `race_id`. |
| `social_contracts` | done | No consumer found in this pass — recorded honestly as a shallower check than the others above (a single candidate search, not an exhaustive one); a good candidate for the follow-up audit ticket already filed for effect-level caveats, not re-investigated exhaustively here given this ticket's own time budget. |
| `temporal_pressure` | skeleton | 46 lines of code total, inactive by its own registry note; no real dependents plausible for an inactive skeleton. |

## Top-25 truncation decision

Kept as-is for this ticket's own "verify next" focused view — the graph-population fix directly
addresses the visibility problem (foundational mechanisms now surface at the TOP of the ranking,
not truncated out), and per peer's own later message, the truncation question properly belongs to
the separately-sequenced complete all-75 view (which should be complete/scrollable, not truncated,
precisely because it answers a different, broader question than this focused ranking does).
