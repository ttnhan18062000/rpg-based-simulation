# Progression Coverage Audit — Phase 6

This document lists existing authoritative law systems and boundaries to guarantee that Phase 6 does not duplicate existing verification paths.

## Existing Authoritative Transaction Systems

The codebase already cleanly isolates transaction legality validations using standard conservation laws:
1. **`ShopSystem`**: Uses `ResourceTransferIntent` to manage item/gold transfers authoritative checking.
2. **`BlacksmithSystem`**: Uses `ResourceTransferIntent` to verify recipe availability and material consumption.
3. **`RewardUpdate`**: Handles quest and combat rewards authoritatively, stripping arbitrary mutations.

## Scoped Phase 6 Verification Boundaries

Phase 6 focuses strictly on **progression meaning, choices, and future conversion decisions**:
- Interpreting reward meaning against active attribute/equipment gaps.
- Prioritizing keeping recipe materials vs selling unsafe junk.
- Diverging plans cleanly based on entity personality biases (greed, industry, caution).
- Emitting executable intents without duplicating law checks.
