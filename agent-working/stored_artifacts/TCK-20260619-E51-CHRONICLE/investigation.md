# Investigation — TCK-20260619-E51-CHRONICLE

## Summary

Zero code exists for event compression or chronicle generation. The pipeline reads existing outputs (`NarrativeLedger` from E32, `simulation_events.jsonl`, social memory events from E43) and produces `Chronicle.md` + structured JSON. This is a post-run, not a tick-live, pipeline.

## Key Findings

### Input Sources

**NarrativeLedger** (from E32D):
- `NarrativeLedgerEntry(episode, tick, event_type, subject_id, payload, significance)`
- `event_type` values: `quest_completed`, `entity_death`, `faction_destroyed`, `calamity`
- `significance: float` (0.0–1.0) already pre-scored in the ledger

**SimulationEvent** (`src/observability/events.py:L54`):
- Raw tick-level events in `simulation_events.jsonl`
- Event kinds include: world events (calamity, resource_depleted), social events (betrayal_desertion, leadership_changed, belief_contradiction), economic (INFLATION_SPIRAL)

**Social Memory Consequence Events** (from E43E):
- `LEGENDARY_ARRIVAL`, `KNOWN_TRAITOR_SPOTTED`, `OLD_DEBT_COLLECTED`

### Existing Pattern to Follow

`stored_artifacts/TCK-20260529-OBS-PHASE23-BEHAVIOR-TIMELINE-EPISODES/investigation.md` — behavior timeline episodes from the observability pipeline. This is a reference for how tick-level event streams are grouped into episodes. Implement the same grouping approach.

### Output Structure

```
Chronicle.md
  YAML frontmatter: {campaign_id, total_episodes, total_ticks, era_count}
  # [Campaign Title]
  ## Era 1: ...
    ### Episode 1: ...
      - Incident: ...  (3–10 events)
    ### Episode 2: ...
  ## Era 2: ...
```

`chronicle.json` (REST API backing store):
```json
{
  "campaign_id": "...",
  "eras": [
    {
      "id": "era_1",
      "name": "The Age of Chaos",
      "episodes": [...],
      "incidents": [...],
      "named_milestones": ["The Fall of Iron Gate", ...]
    }
  ]
}
```

### Significance Scoring Formula

Extend `NarrativeLedgerEntry.significance` at ChronicleCompiler level:
```
event_significance = base_significance + entity_reach * 0.2 + cascade_count * 0.1
```
- Entity deaths of `HERO` entities: base = 0.8
- Faction destroyed: base = 0.9
- Quest completed: base = 0.7
- Calamity: base = 0.85
- Harvest/routine events: base = 0.1 (filtered below threshold)

Threshold for Chronicle inclusion: `event_significance ≥ 0.5`

### Named Entity Assignment

Chronicle names are deterministic:
- Named milestones: `{event_type}_{subject_id}_{tick}` → formatted as "The Death of Aldric (Tick 247)"
- Named wars/alliances: provided by E53 Faction Diplomacy (NarrativeLedger faction events)

### What Is Missing
1. `ChronicleCompiler` class — post-run pipeline entry point
2. Event significance scorer (extend beyond NarrativeLedger significance)
3. Grouping algorithm: events → incidents → episodes → eras
4. Named entity assignment for readable names
5. `Chronicle.md` renderer (structured Markdown with YAML frontmatter)
6. REST endpoints: `GET /api/v1/chronicle/{campaign_id}` + `.../eras/{era_id}/summary`
7. `docs/simulation/domains/chronicle_contract.md` (new doc)
