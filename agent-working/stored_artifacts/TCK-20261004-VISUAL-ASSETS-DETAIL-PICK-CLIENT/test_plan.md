---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT
artifact_type: test_plan
tags: [architecture, determinism, mcp]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-DETAIL-PICK-CLIENT

- [x] Golden vectors (10) and FNV-1a published vectors; stability; fresh module load; no random or clock; one value; negative and large coordinates; refusals.
- [x] Mutants: `Math.random` and dropping `x` each fail tests (recorded in the ticket).
- [x] Fallback order for every step with its reason; with only `plain` adopted the pilot scene draws `plain` with the axis-free calls.
- [x] 64 x 64 spread recorded for the user.

Python cross-check of the golden vectors (run once, output pasted into the test):

```python
def fnv1a32(b):
    h = 0x811C9DC5
    for x in b: h = ((h ^ x) * 0x01000193) & 0xFFFFFFFF
    return h
pick = lambda key, x, y, seed, n: fnv1a32(f"{key}|{x}|{y}|{seed}".encode()) % n
# pick("terrain.forest", 0, 0, 1, 3) == 2 ; pick("terrain.forest", -3, -9, 1, 3) == 0 ; spread over 64 x 64 == [1354, 1397, 1345]
```

## Proof Plan
- level: unit (vitest, jsdom-free pure functions plus a recording 2D context)
- proof kind: golden vectors from an independent implementation, mutation checks, positive and negative fallback cases
- oracle source: the documented hash in `pickDetail.ts` and `docs/assets/store_contract.md`; Python mirror
- expected effect: the same cell always shows the same value; an unavailable value falls back in the documented order; nothing changes for a key without an axis
- selected commands: `npx vitest run src/visualAssets`, `npx tsc -b`, `npx eslint src/visualAssets`
