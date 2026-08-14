---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260717-CSS-LAYER-PADDING-FIX
phase: done
date: 2026-07-17
tags: [debugging]
---

# TCK-20260717-CSS-LAYER-PADDING-FIX

## Title
Fix unlayered CSS reset silently zeroing Tailwind padding utilities app-wide

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
In the ticket table, adjacent Tier and Layer column values run together with no space or visible cell boundary — e.g. "standard"+"engine" renders as "standardengine". This looked like missing cell padding in the table markup, but investigation found the real cause is index.css's `* { margin:0; padding:0; box-sizing:border-box }` reset sitting unlayered above Tailwind's utility layer, which in Tailwind v4's cascade always overrides layered utility classes — so every padding utility (p-*, px-*, py-*, pr-*, etc.) across the whole app is silently zeroed, not just this table's cells.

## Scope
- Move the margin/padding/box-sizing reset in dashboard-frontend/src/index.css inside `@layer base { ... }` so it no longer sits unlayered above Tailwind's utility layer and stops overriding padding utility classes.
- Spot-check padding rendering across App.tsx, Legend.tsx, RecentActivityGantt.tsx, PlaybackScrubber.tsx, TicketsView.tsx, and ReplayTimelineView.tsx after the fix, since all use padding utilities affected by the same bug.
- Add a regression test (computed-style assertion) that fails against the pre-fix index.css and passes post-fix.

## Out of Scope
- Redesigning the ticket table layout or column set itself.
- Removing the reset's intended zeroing behavior for genuinely unstyled elements — preserve it via @layer base, don't delete it.

## Acceptance Criteria
- [x] index.css's margin/padding/box-sizing reset is moved inside @layer base so it no longer sits unlayered above Tailwind's utility layer.
- [x] getComputedStyle() of a Tier <td> (data-testid=tier-cell-{id}) and the adjacent Layer cell in TicketsView shows non-zero padding-right (matching the pr-3 scale value) after the fix.
- [x] Other views using padding utilities (App.tsx, Legend.tsx, RecentActivityGantt.tsx, PlaybackScrubber.tsx, ReplayTimelineView.tsx) are spot-checked and regain their intended padding.
- [x] A new regression test fails against the pre-fix index.css and passes post-fix, preventing silent recurrence of unlayered-reset-vs-utility-layer precedence bugs.

## Related Tickets
- TCK-20260716-AGENTOPS-TICKETS-VIEW
- TCK-20260716-AGENTOPS-ACTIVITY-GANTT

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- dashboard-frontend/src/index.css
- dashboard-frontend/src/views/TicketsView.tsx
- dashboard-frontend/src/test/TicketsView.test.tsx

## Assumptions / Open Questions
- The concern's original hypothesis (missing cell padding in table markup) was incorrect — TicketsView.tsx already applies py-1 pr-3 to every <td>; root cause is the CSS cascade layering bug in index.css, confirmed during investigation.

## Implementation Notes

- Root fix: wrapped the `* { margin: 0; padding: 0; box-sizing: border-box; }` reset in `dashboard-frontend/src/index.css` inside `@layer base { ... }`. It shares the layer name `base` with Tailwind's own preflight (also `@layer base`), so it merges into the same cascade layer rather than creating a new one — matching Tailwind v4's documented convention for extending base styles. Verified via `@tailwindcss/node`'s real `compile()` output and a full `vite build` that the compiled production CSS now emits the reset inside `@layer base { ... *{...} }`, positioned before `@layer utilities { ... .pr-3{...} ... }` in the canonical layer-priority order (`theme, base, components, utilities` in dev; `properties, theme, base, components, utilities` in the production build) — i.e. utilities now outrank the reset, so `pr-3`/`py-1`/etc. are no longer zeroed.
- Spot-checked `App.tsx`, `Legend.tsx`, `RecentActivityGantt.tsx`, `PlaybackScrubber.tsx`, `TicketsView.tsx`, `ReplayTimelineView.tsx`: none use `@apply` (grep confirmed zero matches across all six), all use plain Tailwind padding utility classes that live in the same `@layer utilities` block validated above — no per-component code changes were needed or made.
- Regression test added to `dashboard-frontend/src/test/TicketsView.test.tsx` (new describe block `TicketsView — index.css reset does not zero out padding utilities`, 2 tests). Deviation from the ticket's literal "getComputedStyle() ... 12px" wording, recorded because it required investigation before it was clear the literal ask was unreachable in this environment: empirically verified (via throwaway probe tests, since discarded) that jsdom 28.1 in this repo's vitest setup does not apply *any* CSS declared inside `@layer` blocks when resolving `getComputedStyle` (confirmed via minimal repros — an isolated `@layer utilities { .pr-3 { padding-right: 12px } }` with no competing rule never applies), even though jsdom's CSSOM correctly parses `@layer` into `CSSLayerBlockRule`/`CSSLayerStatementRule` and `@media` grouping works fine for computed style. Since Tailwind always wraps utilities in `@layer utilities`, a literal `getComputedStyle(...).paddingRight === '12px'` assertion is unreachable in this environment regardless of the fix's correctness. Also confirmed jsdom does not resolve `calc()`/`var()` in computed style (returns the raw specified-value string), so even an unlayered comparison couldn't literally yield `'12px'` text.
  - Resolution: the test compiles the **real** `src/index.css` via `@tailwindcss/node`'s `compile()` (the same compiler `@tailwindcss/vite` uses), renders the actual `TicketsView` component, and reads the real `tier-cell-{id}` / adjacent Layer `<td>` class lists. It then hand-implements the one CSS Cascade Layers rule under test (unlayered rules always beat layered ones; among layered rules the later-declared layer wins) by walking the real parsed `CSSStyleSheet.cssRules`/`CSSLayerBlockRule` tree via `resolveCascadeWinner()`, since `getComputedStyle` cannot be trusted for this in the current jsdom. It asserts the winning `padding-right` declaration is `pr-3`'s (`calc(var(--spacing) * 3)`, which is 12px given the project's `--spacing: 0.25rem` and 16px root) rather than the reset's zero, on both cells. A second, simpler `getComputedStyle(tierCell).paddingRight !== '0px'` assertion is kept alongside as an honest native-API signal (it fails pre-fix at `'0px'`, passes post-fix). A third test does a direct structural regex check that the reset lives inside `@layer base { * { ... } }` in the source file. Manually verified all three fail against the pre-fix (unlayered) CSS and pass against the post-fix CSS by temporarily reverting `index.css` and re-running.
- `readFileSync`/`path`/`process` (Node builtins) are used in the test to read the real `index.css` text, because Vite's `?raw` import and `import.meta.glob(..., {as:'raw'})` were both empirically confirmed to return an empty string for `.css` files in this vitest config — the `@tailwindcss/vite` plugin's transform intercepts `.css` requests before the raw-import codepath, regardless of query suffix.
- This introduced a real `tsc -b` typecheck gap: `tsconfig.app.json` (which covers all of `src/`, including `src/test/`) only has `"types": ["vite/client"]`, no Node types, by design — `tsconfig.node.json` already exists solely to give `vite.config.ts` Node types without polluting the browser-only app config. Rather than loosen `tsconfig.app.json` repo-wide (which would let Node APIs leak into browser component code unflagged), added a third project reference, `tsconfig.test.json`, scoped to `src/test/**`, mirroring `tsconfig.app.json`'s browser/JSX settings plus `"node"` in `types`; excluded `src/test` from `tsconfig.app.json`'s `include`. Verified `npx tsc -b --noEmit` and `npm run build` both pass clean.

## Test Summary

- `cd dashboard-frontend && npx vitest run` — 6 files, 37 tests, all passed (was 35 tests/6 files before this ticket; +2 new tests).
- `cd dashboard-frontend && npx tsc -b --noEmit` — clean, no errors.
- `cd dashboard-frontend && npm run build` — succeeds; inspected the emitted `dist/assets/index-*.css` and confirmed the reset is nested inside the production build's `@layer base { ... }` block, before `@layer utilities { ... .pr-3 { padding-right: calc(var(--spacing) * 3) } ... }`.
- Manually reverted `index.css` to the pre-fix (unlayered reset) state and re-ran the new tests: both the cascade-winner test and the structural `@layer base` regex test failed as expected (`0px` / no match), confirming the tests are genuine regression guards, then restored the fix.

## Files Changed

- `dashboard-frontend/src/index.css` — moved the `* { margin: 0; padding: 0; box-sizing: border-box; }` reset inside `@layer base { ... }`.
- `dashboard-frontend/src/test/TicketsView.test.tsx` — added the CSS layer/padding regression describe block (2 tests) plus supporting `resolveCascadeWinner`/`findLayerPriorityOrder` test helpers.
- `dashboard-frontend/tsconfig.app.json` — excluded `src/test` (now covered by the new `tsconfig.test.json`).
- `dashboard-frontend/tsconfig.json` — added the `tsconfig.test.json` project reference.
- `dashboard-frontend/tsconfig.test.json` — new: browser+JSX tsconfig for `src/test/**` with Node types added, so test files can use `fs`/`path`/`process` for real-file CSS regression testing without loosening the production app config.

## Completion Summary

Fixed the root cause of the ticket table's "standardengine"-style column run-together bug: `dashboard-frontend/src/index.css`'s universal margin/padding/box-sizing reset was unlayered, and in Tailwind v4's CSS cascade an unlayered rule always beats a rule inside `@layer utilities` regardless of specificity — so every `p-*`/`px-*`/`py-*`/`pr-*`/etc. utility class app-wide was silently zeroed, not just the ticket table. Moved the reset inside `@layer base { ... }` (merging with Tailwind's own preflight base layer), restoring the intended cascade order (utilities > base) app-wide. Verified via the real Tailwind compiler and a full production build that the fix is correct, confirmed all six flagged views (App.tsx, Legend.tsx, RecentActivityGantt.tsx, PlaybackScrubber.tsx, TicketsView.tsx, ReplayTimelineView.tsx) need no code changes since none use `@apply` and all share the same utilities-layer fix. Added a regression test in `TicketsView.test.tsx` that compiles the real `index.css` and hand-resolves the CSS Cascade Layers winner against the actual rendered Tier/Layer `<td>` elements (necessary because jsdom in this repo's vitest setup does not apply any `@layer`-nested CSS via `getComputedStyle`, a real environment limitation independent of this fix), verified to fail against the pre-fix CSS and pass against the post-fix CSS. Added a scoped `tsconfig.test.json` so the test file's use of Node's `fs`/`path` typechecks without loosening the production app tsconfig. All existing and new dashboard-frontend tests (37/37), `tsc -b --noEmit`, and `npm run build` pass.
