---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-SKILL-PATH-MONITORING-NULL-TS-AND-VERDICT-STRICTNESS
artifact_type: plan
tags: [ai]
---

# Plan

1. `record_events.py --default-ts` (fills only missing/null ts; strict without it).
2. writeMonitoring prompt and skill pass `--default-ts "<END_TS>"`.
3. Skill documents the verdict-strictness duty (no code change, no gate loosened).
4. Tests on the exact failing input.
