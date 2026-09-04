---
status: active
layer: strategy
authority: P2
audience: agent
tags: [strategy]
---

# Idea 57 — Entity-Scale Fame Aggregation: a Named Sibling to `CultureDeriver`

**Source:** Deliverable #2 of `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md`
("An entity/reputation-scale aggregation shape, sibling to `CultureDeriver`'s region-scale one, for
idea 57's 'does this entity's past deeds currently make them a Living Legend' question"). That
proposal itself cites `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`'s own scope
note: idea 57 "should copy `CultureDeriver`'s aggregation shape rather than invent new
event-scoring logic." This doc is that write-up — a design, not an implementation. No `src/` file
is touched by this doc.

## The real shape being copied (confirmed via direct code read, not assumed)

`CultureDeriver` (`src/domains/culture/deriver.py`) is a three-file, three-layer pattern:

1. **Deriver** (`deriver.py`) — one pure, stateless `classmethod derive(hierarchy, entity_names=None)
   -> Dict[key, State]`. Iterates `hierarchy.events` (a `ChronicleHierarchy`'s flat
   `tuple[NarrativeLedgerEntry, ...]`, `src/domains/chronicle/grouper.py:75-86`). For each entry,
   extracts a **grouping key** (`entry.payload.get("region_id", "__global__")`,
   `deriver.py:78`), classifies `entry.event_type` against fixed frozensets into named
   accumulator buckets (`_FATALISM_EVENTS`/`_CONFLICT_EVENTS`/`_SCARCITY_EVENTS`, plus one
   compound rule branching on `entity_death`'s own payload fields), sums `entry.significance`
   additively per bucket per key, then normalises each bucket via
   `min(1.0, raw / NORMALISE_DENOMINATOR)` (`NORMALISE_DENOMINATOR = 3.0`).
2. **Model** (`model.py`) — a frozen, sloted dataclass with N named float axes in `[0.0, 1.0]`
   (`CultureState`), plus a carry-forward wrapper record (`CultureCarryForward`: key + state +
   `derived_episode: int`) that persists a snapshot across episodes even when a key produces no
   events in a later one.
3. **Exporter/Importer** (`exporter.py`) — `CultureDriftExporter.export(campaign_state, hierarchy,
   episode_index, entity_names)`, a `@staticmethod` called from
   `CampaignOrchestrator._advance_state()` (`orchestrator.py:243-246`) at every episode boundary;
   calls the Deriver, wraps each result in the CarryForward record, writes into
   `campaign_state.region_cultures: Dict[str, CultureCarryForward]` in place — untouched keys keep
   their prior snapshot. `CultureDriftImporter.get_culture(campaign_state, region_id)` is a thin,
   `None`-safe lookup, consumed by `MotivationBiasService`/`CulturalBiasApplicator`
   (`src/domains/motivation/service.py`, `src/domains/culture/applicator.py`).

**The natural per-entity grouping key already exists and needs no new wiring.**
`NarrativeLedgerEntry.subject_id` (`src/domains/campaigns/state.py:233,243`) is populated today
from `world_event.subject` (`orchestrator.py:541`) — the same generic per-entry field
`region_id` is extracted from `payload` for the region-scale case, except `subject_id` is already
a first-class column on every entry, not a payload lookup. An entity-scale Deriver can key on it
directly.

## Proposed sibling: `FameDeriver` (name for discussion, not final)

Mirror the exact 3-layer pattern:

- `FameDeriver.derive(hierarchy, entity_names=None) -> Dict[str, FameState]` — same signature
  shape as `CultureDeriver.derive`, keyed by `entry.subject_id` instead of
  `entry.payload["region_id"]`.
- `FameState` (new frozen dataclass, `src/domains/culture/model.py` or a new
  `src/domains/fame/model.py` — precedent favors a new module since this is entity-scale, not
  region-scale, and `culture/` is named for the region concept specifically) — at minimum one
  axis, `fame: float` in `[0.0, 1.0]`, normalised the same way. Whether it needs more than one
  axis (e.g. splitting "heroic fame" from "notoriety/infamy," mirroring `heroism_delta` vs.
  `notoriety_delta`'s existing split on `SocialUpdate`, `src/core/updates.py:300`) is an open
  question — see below.
- `FameCarryForward` (entity_id + `FameState` + `derived_episode`), same shape as
  `CultureCarryForward`.
- `FameExporter.export(campaign_state, hierarchy, episode_index, entity_names)`, called from the
  same `CampaignOrchestrator._advance_state()` call site immediately alongside
  `CultureDriftExporter.export()` (`orchestrator.py:243-246`) — same episode-boundary cadence, no
  new hook needed. Writes into a new `CampaignState.entity_fame: Dict[str, FameCarryForward]`
  field (mirroring `region_cultures`'s own field shape).
- `FameImporter.get_fame(campaign_state, entity_id)`, thin `None`-safe lookup — the read side idea
  57 actually needs: "once fame crosses `fame_threshold`, it becomes a `LegendFact`, discoverable
  via Perception, feeding Motivation & Doctrine bias" (idea 57's own schema,
  `docs/brainstorm/rpg_expected_schemas.html#schema-57`). The threshold-crossing check, the
  `LegendFact` class, and the Perception-system wiring are idea 57's own remaining scope — this
  doc covers only the aggregation shape that produces the `fame` number those pieces would read.

## Open question found, not resolved here: which events actually feed `fame`

`CultureDeriver`'s axis-to-event-type mapping was itself a deliberate design choice (fatalism from
calamity/traumatic death, hero_veneration from HERO death, etc.) — the entity-scale sibling needs
the same kind of choice, and the real event-type universe today is narrower than idea 57's own
framing assumes:

- `NarrativeLedgerEntry.event_type` is one of exactly 4 literal values today:
  `"quest_completed" | "entity_death" | "faction_shift" | "calamity"`
  (`src/domains/campaigns/state.py:232,242`). There is **no `combat_victory`/`monster_slain`
  event type** — a hero's most legend-worthy actions (defeating monsters) currently produce zero
  Narrative-Ledger-recordable signal under this vocabulary. This is a real, confirmed gap, not
  assumed: `NarrativeLedgerEntry`'s own docstring and `orchestrator.py`'s event-type→significance
  table (`orchestrator.py:63-67`) were read directly, not guessed from the class name.
- `subject_id` for `entity_death` is the **deceased** entity (`"The Death of {subject}"`,
  `src/domains/chronicle/naming.py:39`), not a killer — so `entity_death` can source a hero's own
  *posthumous* fame (dying gloriously), but cannot attribute fame to whoever defeated a monster.
  `quest_completed`'s `subject_id` is the questing entity itself, which is a real, usable signal
  today — narrower than "legendary deeds" but genuinely available without new wiring.
- **A second, entirely separate real signal already exists and predates Chronicle involvement
  entirely:** `entity.social.heroism_score` (`src/core/state.py`'s `SocialComponent`), already
  live, already accumulating every tick via `SocialUpdate.heroism_delta`
  (`src/systems/social_systems/contracts.py:223-227`, `relationships.py:94-96`) on contract
  success. Idea 57's own schema text ("Once Chronicle-recorded fame (from real heroism_score)
  crosses a threshold...") conflates this field with Chronicle's own output — confirmed via direct
  read of `src/domains/chronicle/significance.py`: `EventSignificanceScorer` never reads
  `heroism_score` anywhere; it scores purely by event type. These are two independent,
  unconnected signals today, not one.

**Three real options for what `fame` actually sums, not silently collapsed to one:**

| Option | What it sums | Matches epic's "copy CultureDeriver's shape, no new scoring" instruction? | Real gap |
|---|---|---|---|
| A — Chronicle-only, `quest_completed` | `entry.significance` for `quest_completed` entries, keyed by `subject_id` | Yes — literal mirror of `CultureDeriver`, zero new event-scoring | Misses combat-earned fame entirely; a hero who wins every fight but completes no quests scores 0 |
| B — Chronicle-only, `quest_completed` + `entity_death` (posthumous) | Same, plus `entity_death` where the deceased was `entity_role == HERO` (mirrors `hero_veneration`'s own existing rule) | Yes — reuses an event-type rule `CultureDeriver` already defines, still zero new scoring | Still misses in-life combat fame; only helps posthumous legends |
| C — Read `heroism_score` directly, no Chronicle aggregation at all | `entity.social.heroism_score` as of episode end | No — bypasses the aggregation-shape instruction entirely; not Chronicle-hierarchy-driven, no per-episode carry-forward semantics | Correctly captures combat-earned fame today (heroism_delta already fires on contract success broadly), but bakes in a live-state read that never "resets" the way Chronicle-derived carry-forward does |

**Recommendation:** Option B as the aggregation shape (satisfies the epic's explicit
no-new-scoring instruction, reuses the exact `hero_veneration` event-type rule `CultureDeriver`
already established as precedent), with the `entity_death`-defeats-`quest_completed`-only gap
disclosed as a known, real limitation rather than silently accepted — flag it for whoever picks up
idea 57's own implementation ticket to decide whether it's acceptable, or whether a genuinely new
`combat_victory` event type (out of this doc's scope — that's new event-scoring, not aggregation)
is worth its own follow-up. Option C is worth keeping on record as an alternate/supplementary
signal (e.g. `LegendFact`'s threshold check could read *both* the Chronicle-derived `fame` axis
*and* live `heroism_score`, taking the max) rather than discarded, since it's the only option that
captures in-life combat fame without new event-type work — but that composition decision is itself
a design call for idea 57's own ticket, not resolved here.

## What this doc does not resolve (idea 57's own remaining scope)

- The `LegendFact` class itself, `fame_threshold`'s actual numeric value (a real design-authority
  decision, same caution the atlas gives idea 34 — "no existing anchor"), and its Perception-system
  discoverability wiring.
- Whether `FameState` needs more than one axis (fame vs. notoriety/infamy, mirroring
  `heroism_delta`/`notoriety_delta`'s existing split).
- The Motivation & Doctrine bias-feed wiring itself (the "Townsperson's coming-of-age choice can
  lean toward adventurer" consumer, idea 34's own territory).

## References

- `docs/brainstorm/2026-09-04-core-rpg-legacy-memory-axis-proposal.md` (parent proposal, deliverable #2)
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` (idea 57's scope note)
- `docs/brainstorm/rpg_expected_schemas.html#schema-57` (idea 57's own frozen schema — read-only, not edited)
- `src/domains/culture/{deriver,model,exporter}.py` (the precedent being mirrored)
- `src/domains/campaigns/state.py` (`NarrativeLedgerEntry`), `src/domains/campaigns/orchestrator.py`
  (episode-boundary call site, event-type→significance table)
- `src/domains/chronicle/significance.py`, `src/domains/chronicle/naming.py` (confirmed
  `heroism_score` is not read by Chronicle's own scorer; `entity_death`'s subject is the deceased)
