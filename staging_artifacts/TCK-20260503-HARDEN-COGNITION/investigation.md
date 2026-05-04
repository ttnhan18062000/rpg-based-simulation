# Investigation: Strategic Cognition Hardening

## Current State Analysis
- `StrategicIntelligenceSystem.evaluate_all_concerns`: Checks `entity.active` and `entity.combat.alive`.
- `StrategicIntelligenceSystem.evaluate_strategic_intent`: Checks `entity.active` and `entity.combat.alive`.
- `LegalityServiceV2.verify_action_legality`: Checks `status_frozen` and `status_stunned`.

## Gaps Identified
- `StrategicIntelligenceSystem` does not check `status_frozen` or `status_stunned`. This means a frozen entity might still spend CPU cycles evaluating strategic intents, which is wasteful and potentially incorrect if the intent leads to immediate actions that would then be rejected by the legality service.
- The `phase9_entry_support_boundary.md` is outdated and lists many supported features as `UNSUPPORTED`.

## Proposed Fix
- Sync the early exit logic in `StrategicIntelligenceSystem` with `LegalityServiceV2`.
- Audit the staggered frequency to ensure it's not bypassed by any secondary entry points.
