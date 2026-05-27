# Investigation Report - Phase 1 Data Registries

## Findings
- Static registries must remain read-only during execution.
- Pydantic or custom dataclasses (DTO) will represent registry models.
- Pre-flight checks are needed to ensure recipe requirements refer to valid item or resource IDs, and enemy loot refers to valid items.
