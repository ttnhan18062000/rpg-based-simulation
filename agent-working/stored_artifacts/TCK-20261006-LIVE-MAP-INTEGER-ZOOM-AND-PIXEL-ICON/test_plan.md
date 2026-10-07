---
status: historical
layer: frontend
authority: P2
audience: agent
ticket_id: TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON
artifact_type: test_plan
tags: [live-map, hud, testing]
---

# Test plan — TCK-20261006-LIVE-MAP-INTEGER-ZOOM-AND-PIXEL-ICON

## Proof Plan

- level: unit and component (jsdom with a stub canvas context); proof kind: property tests over DPRs plus mutants; oracle source: the level definition n / dpr and whole-device-pixel arithmetic; expected effect: every reachable level has zoom x dpr integral at DPR 1, 1.25, 1.5, 2; selected commands: `npx vitest run` (whole frontend), `npm run build`.
