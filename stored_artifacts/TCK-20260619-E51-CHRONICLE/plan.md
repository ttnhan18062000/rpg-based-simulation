# Plan — TCK-20260619-E51-CHRONICLE

## Approach

Post-run pipeline. `ChronicleCompiler` reads `NarrativeLedger` + `simulation_events.jsonl`; groups events into hierarchy; generates `Chronicle.md` and `chronicle.json`; exposes via REST.

## Sequence

**E51A → E51B → E51C → E51D → E51E** (strictly sequential)

---

## E51A · Event Significance Scorer

New file `src/domains/chronicle/significance.py`:

```python
BASE_SIGNIFICANCE = {
    "entity_death": 0.5,    # HERO death: 0.8
    "faction_destroyed": 0.9,
    "quest_completed": 0.7,
    "calamity": 0.85,
    "LEGENDARY_ARRIVAL": 0.75,
    "KNOWN_TRAITOR_SPOTTED": 0.6,
    "betrayal_desertion": 0.7,
    "leadership_changed": 0.4,
    "INFLATION_SPIRAL": 0.5,
}

CHRONICLE_THRESHOLD = 0.5

class EventSignificanceScorer:
    @staticmethod
    def score(entry: NarrativeLedgerEntry | SimulationEvent) -> float:
        base = BASE_SIGNIFICANCE.get(entry.event_type, 0.1)
        # HERO entity deaths are weighted higher
        hero_bonus = 0.3 if entry.payload.get("entity_role") == "HERO" else 0.0
        return min(1.0, base + hero_bonus)
```

---

## E51B · Event → Incident → Episode → Era Grouping

New file `src/domains/chronicle/grouper.py`:

```python
class ChronicleGrouper:
    INCIDENT_TICK_WINDOW = 50     # events within 50 ticks → same incident
    EPISODE_INCIDENT_MIN = 5      # ≥5 incidents → episode boundary
    ERA_EPISODE_MIN = 3           # ≥3 episodes → era boundary

    def group(self, entries: list[NarrativeLedgerEntry]) -> ChronicleHierarchy:
        # 1. Filter: only entries above CHRONICLE_THRESHOLD
        # 2. Sort by (episode, tick)
        # 3. Group into incidents: entries within INCIDENT_TICK_WINDOW of each other
        # 4. Group incidents into episodes: episode boundary from NarrativeLedger.episode field
        # 5. Group episodes into eras: first episode is era 1; era break when ≥ERA_EPISODE_MIN complete
        ...
```

---

## E51C · Named Entity Assignment

New file `src/domains/chronicle/naming.py`:

```python
class ChronicleNamer:
    @staticmethod
    def name_milestone(entry: NarrativeLedgerEntry, entity_names: dict[int, str]) -> str:
        subject_name = entity_names.get(int(entry.subject_id), entry.subject_id)
        templates = {
            "entity_death": f"The Death of {subject_name}",
            "faction_destroyed": f"The Fall of {subject_name}",
            "quest_completed": f"The Quest of {subject_name}",
            "calamity": f"The Calamity at Tick {entry.tick}",
        }
        return templates.get(entry.event_type, f"{entry.event_type}: {subject_name}")
```

Names are deterministic (entity name from `IdentityComponent.name` + event type).

---

## E51D · Chronicle.md Generator

New file `src/domains/chronicle/renderer.py`:

Produces structured Markdown with YAML frontmatter:
```markdown
---
campaign_id: "..."
total_episodes: 3
total_ticks: 2000
era_count: 2
---
# Chronicle of [Campaign Name]
## Era 1: The Age of Turmoil
### Episode 1: First Blood
- **The Death of Aldric** (Tick 247) — ...
```

Also writes `chronicle.json` as structured JSON backing store.

---

## E51E · REST Endpoints

New `src/api/routes/chronicle.py`:
```
GET /api/v1/chronicle/{campaign_id}
    → full structured chronicle.json
GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary
    → {era_id, name, milestone_count, named_milestones[]}
```

After E51E: create `docs/simulation/domains/chronicle_contract.md`. Register router in `src/api/server.py`. Run `make knowledge-index-update`.
