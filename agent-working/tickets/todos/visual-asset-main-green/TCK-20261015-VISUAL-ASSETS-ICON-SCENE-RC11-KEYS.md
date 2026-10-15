---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261015-VISUAL-ASSETS-ICON-SCENE-RC11-KEYS
phase: open
date: 2026-10-15
tags: [architecture, testing]
---

# TCK-20261015-VISUAL-ASSETS-ICON-SCENE-RC11-KEYS

## Title
Main's Frontend tests: give the 18 rc-0011 marker keys their fallbacks in the icon page and correct the key counts (#598)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
GitHub #598. #596 (`51b044c69`, `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`) registered 18 `icon.*` keys in `visual_assets/catalog/definitions/visual_keys.yaml` but did not update `frontend/src/visualAssets/__tests__/iconScene.test.ts`. That test pins the icon key counts (`14 + 22`, `22`) and needs a declared fallback for every key the page does not draw. Main's Frontend job has been red since #596 (last green: run 38607062136 at `2dabff8c1`), and every open PR inherits the failure (#588, #589, #590). The ticket said "No `src/` or `frontend/` change", so nobody ran the frontend vitest after the registry pins moved. That is how the failure got through.

## Scope
- `frontend/src/visualAssets/iconScene.ts`: declare a fallback for each of the 18 new keys. These are 4 buildings (`healer_hut`, `town_hall`, `mine_entrance`, `watchtower`), 1 marker (`nest`) and 13 `icon.node.*` keys. **Copy** each key's registry `fallback` (`glyph` + `text`) the way `V2_FALLBACKS` copies the v2 ones (the page imports nothing from the app or the registry). The note starts with `identifying` (all 18 have `safety_class: identifying`). Where the description names a hex (`#aaa`, `#7dd3a0`, ...), the shown text contains that exact string, because the test checks `/#[0-9a-f]{6}/`, and a 3-digit `#aaa` does not match it, so keep the registry spelling. Extend the comments that say "22 icon set v2 keys" so they name what the table now holds.
- `frontend/src/visualAssets/__tests__/iconScene.test.ts`: change the counts to the real sets, by name rather than one bare number: 14 drawn + 22 icon set v2 + 18 object markers (rc-0011) = 54 registered; 40 undrawn. Also change the "22" in the `it(...)` titles.
- Route check done by asset-planner (2026-10-15): `python3 -m tools.sessions.route` gives both files as **split rpg/asset**, "the asset domain owns the client half of the visual-asset store". These files are the icon preview page and its pins, so they are the asset half. asset-planner posts the planned diff shape on #598 for rpg-planner. If rpg-planner objects before you commit, STOP and tell asset-planner.

## Out of Scope
- No change to the registry, rc-0011, the store, or any `visual_assets/` file.
- The page does NOT start drawing the 18 markers (no `ICON_SIZES`/`ICON_KEYS` change). That would be activation work, and activation is parked except for icons the owner chooses.
- No change to `fallback.ts`, `resolver.ts` or any live-app file. The live client still resolves no aliases (known gap).

## Acceptance Criteria
- [ ] `iconScene.test.ts` passes, run scoped: `cd frontend && npx vitest run src/visualAssets/__tests__/iconScene.test.ts` (under the MemoryMax cap). Then the whole `src/visualAssets/` vitest directory passes, scoped.
- [ ] Each of the 18 fallbacks is a copy of its registry `fallback`. Name the check you used in the ticket (for example, a throwaway diff of `yaml fallback` vs the table), and keep the existing hex test as the guard.
- [ ] `npm run lint`/`tsc` for the frontend is clean for the two files, if the repo has such a script (the CI Frontend job is the reference; read `.github/workflows/` for its exact commands and run the same ones scoped).
- [ ] The ticket names the reason: why #596's own CI did not catch this. Check whether #596's PR ran the Frontend job at all (path filter?) and record the answer. If the Frontend job is path-filtered and skipped `visual_assets/`-only changes, say so in the ticket and tell asset-planner. Do not change the workflow; that is a separate question for its owner.

## Related Tickets
- Cause: `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE` (#596)
- Precedent for the table: `TCK-20261007-VISUAL-ASSETS-ICON-V2-KEYS-AND-RC`
- Same batch: `TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR` (#555)

## Related Docs
- `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/store_contract.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261013-VISUAL-ASSETS-OBJECT-MARKER-DRAFTS/` (the 18 keys and their fallback wording)

## Related Code Areas
- `frontend/src/visualAssets/iconScene.ts` (`V2_FALLBACKS`, `fallbackFor`), `frontend/src/visualAssets/__tests__/iconScene.test.ts`, `visual_assets/catalog/definitions/visual_keys.yaml` (read only)

## Assumptions / Open Questions
- Assumed: the page keeps one hand-copied fallback table, as it does today. A generated table would be a design change, not this hotfix.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
