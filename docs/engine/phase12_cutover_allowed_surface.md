# Phase 12 Cutover-Allowed Surface

This document defines the exact simulation surface eligible for production cutover in Phase 12.

## 1. Allowed Supported Surface
Phase 12 is authorized to cut over the following behaviors to the `src` engine:

| Category | Allowed Items | Constraint |
| :--- | :--- | :--- |
| **Movement** | All | Bit-identical parity ratified. |
| **Resource** | Harvest, Loot | All items in `ITEM_REGISTRY` supported. |
| **Strategic** | All Bounded | Must use `StrategicRedirectionSystem`. |
| **Social** | Recruitment | Must use `SocialComponent` truth. |
| **Combat** | Legal Moves | All moves must pass `LegalityService` LoS/Engagement checks. |
| **System** | CLI, REST, WS | All Phase 10 hardened protocols are allowed. |

## 2. Allowed Execution Modes
- **Headless CLI**: High-confidence cutover.
- **REST API Serve**: High-confidence cutover.
- **WebSocket (BWS)**: High-confidence cutover.
- **Deterministic Replay**: Authoritative recording/playback allowed.

## 3. Allowed Consumers
- **Frontend v2**: Optimized for V2 protocols.
- **Automation Harness**: Authorized for regression testing.
- **Cutover Workers**: Authorized for production simulation.

## 4. Forbidden Assumptions (Phase 12 Guardrails)
- **Do NOT** assume legacy `Turning Points` logic exists.
- **Do NOT** assume legacy `Economy breakthroughs` (XP, Level-up) are functional.
- **Do NOT** assume `Evasion` or `Damage Variance` exists in V2 resolution.

---
**Ratification Status**: PROVISIONAL (Cutover Surface Defined)
**Audit Date**: 2026-04-24
