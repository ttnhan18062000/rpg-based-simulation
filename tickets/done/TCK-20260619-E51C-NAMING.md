---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51C-NAMING
phase: done
date: 2026-06-20
tags: [chronicle, naming, named-milestones, deterministic, phase-5]
---

# TCK-20260619-E51C-NAMING

## Title
Epic 5.1C · Named Entity and Milestone Assignment

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Chronicle entries need human-readable names ("The Death of Aldric") generated deterministically from entity identity + event type.

**Requires:** TCK-20260619-E51B-GROUPER

## Scope

New file `src/domains/chronicle/naming.py`:

```python
class ChronicleNamer:
    TEMPLATES = {
        "entity_death": "The Death of {subject}",
        "faction_destroyed": "The Fall of {subject}",
        "quest_completed": "The Quest of {subject}",
        "calamity": "The Calamity at Tick {tick}",
        "WAR_DECLARED": "The {subject} War Declaration",
        "TERRITORY_TRANSFERRED": "The Fall of {subject}",
        "ALLIANCE_FORMED": "The Alliance with {subject}",
    }

    @staticmethod
    def name_milestone(entry: NarrativeLedgerEntry, entity_names: dict[int, str]) -> str:
        subject = entity_names.get(int(entry.subject_id), str(entry.subject_id))
        template = ChronicleNamer.TEMPLATES.get(entry.event_type, "{subject}")
        return template.format(subject=subject, tick=entry.tick)

    @staticmethod
    def name_era(era_index: int, dominant_event_type: str) -> str:
        era_names = {
            "entity_death": "The Age of Conflict",
            "faction_destroyed": "The Age of Collapse",
            "calamity": "The Age of Calamity",
        }
        return era_names.get(dominant_event_type, f"Era {era_index + 1}")
```

Names are pure functions of input — deterministic across runs with same NarrativeLedger.

## Acceptance Criteria
- `test_milestone_naming_deterministic` passes (same entry → same name every call)
- Named eras match dominant event type

## Related Tickets
- TCK-20260619-E51-CHRONICLE (parent epic)
- TCK-20260619-E51B-GROUPER (required)
- TCK-20260619-E51D-RENDERER (blocked on this)

## Related Code Areas
- `src/domains/chronicle/naming.py` (new)

## Test Summary
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py::test_milestone_naming_deterministic -x -v
```
## Files Changed
- `src/domains/chronicle/naming.py` (new) — ChronicleNamer with TEMPLATES, ERA_NAMES, name_milestone(), name_era()
- `src/domains/chronicle/__init__.py` (updated) — exports ChronicleNamer
- `tests/unit/chronicle/test_chronicle_compiler.py` (updated) — TC-13 through TC-18 added (18 total pass)
- `docs/parity_ledger/social_narrative.yaml` (updated) — SOC-CHRON-003 entry added

## Completion Summary
Created `src/domains/chronicle/naming.py` with `ChronicleNamer`: a stateless, deterministic
namer for chronicle milestones and eras. `name_milestone()` resolves subject via safe int-cast
of subject_id (raw-string fallback), applies TEMPLATES[event_type] substitution with {subject}
and {tick}; unknown event types return bare subject name. `name_era()` maps dominant_event_type
to ERA_NAMES with "Era N" (1-based) fallback. 6 new tests (TC-13 through TC-18) added — all
18 tests pass. SOC-CHRON-003 parity ledger entry added.
