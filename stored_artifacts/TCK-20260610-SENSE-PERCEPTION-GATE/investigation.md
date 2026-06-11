---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260610-SENSE-PERCEPTION-GATE
artifact_type: investigation
tags: [sense, perception, gate]
---

# Investigation — TCK-20260610-SENSE-PERCEPTION-GATE

## Findings

- `data/content/living/sense_profiles.yaml`: 6 profiles (normal_humanoid_senses, predator_smell_senses,
  goblin_alert_senses, spider_vibration_senses, arcane_senses, undead_dread_senses)
- `SenseProfileDefinition` in `src/content/schema.py`: 7 optional string fields
  (vision, hearing, smell, magic_sense, social_reading, vibration, life_sense)
- `CatalogRepository.get_sense_profile(def_id)` already exists and works
- No existing `PerceptionGate` or perception directory — clean addition
- `PerceptionFilterService` exists and gates attention budget — distinct concern, not modified
