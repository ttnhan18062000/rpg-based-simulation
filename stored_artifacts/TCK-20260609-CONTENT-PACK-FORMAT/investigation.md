---
ticket: TCK-20260609-CONTENT-PACK-FORMAT
phase: investigation
---

# Investigation

No existing pack format in codebase. Existing catalog schema uses Pydantic BaseModel
with extra="forbid". Pattern established in SimulationScenarioDefinition (scenarios) and
WorldCompositionSpec (worldassembly). Following same pattern for ContentPackManifest.

Key design decision: consumer requirement enforced via @model_validator on the schema
itself, not just the validator — fails fast at construction time.
