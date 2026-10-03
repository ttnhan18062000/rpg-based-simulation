---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260603-PHASE15-REGISTRY-BRIDGE
artifact_type: test_plan
tags: [phase15, registry, bridge]
---

# Test Plan - Phase 15 Registry Bridge

## Automated Verification Steps
1. Run `pytest tests/unit/core/test_registry_bridge.py` to ensure mappers work correctly and bootstrap registries cleanly.
2. Run `pytest tests/unit/strategic/test_registries.py` to confirm that the catalog-seeded registries satisfy the same assertions as the legacy hardcoded database.
3. Run `pytest` on existing core, resource, and town tests to ensure all gameplay systems query the projected values successfully.
