---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-TIMELINE-RANGE-CONTROL
artifact_type: plan
tags: [dashboard, observability]
---

# Implementation Plan — TCK-20260720-TIMELINE-RANGE-CONTROL

## Summary

Add a range-control UI above `ProgressTimelineView.tsx`'s chart — four quick-range preset buttons
(1h/6h/24h/7d) plus a custom start/end `<input type="datetime-local">` pair — that replaces the
component's current fixed `SINCE_WINDOW_MS = 24h` window with live `sinceIso`/`untilIso` React
state, feeding both into the bulk timeline fetch (`useRunTimelinesPolling`) so the server-side
`until` bound (already landed by `TCK-20260720-BULK-RUN-TIMELINE`, INFRA-301) is actually consumed.
Four independent pieces: (1) a pure `dashboard-frontend/src/lib/timeRangePresets.ts` module holding
the single source of truth for preset durations and the `datetime-local` <-> UTC-ISO conversion;
(2) a new, independently-testable `dashboard-frontend/src/components/RangeControl.tsx` presentational
component, styled and structured after `TicketsView.tsx`'s real filter-bar precedent (not the
ticket's own inaccurate "Stats tab" citation — `StatsView.tsx` has no form controls at all); (3) an
`api.ts` signature extension so `useRunTimelinesPolling` actually forwards `until` to the bulk
endpoint (today it silently drops it even though the private `fetchRunTimelines` layer already
supports it); (4) wiring all of the above into `ProgressTimelineView.tsx`, replacing its
setter-less `useState` initializer with live `sinceIso`/`untilIso` state, while leaving
`toChartOption.ts`'s `nowIso` and both `dataZoom` instances completely untouched and
non-interacting, per the ticket's explicit Out-of-Scope.

Two decisions the investigation deliberately left to Plan (not to the user — both are pure
implementation-shape calls with no ticket-text ambiguity) are resolved below and must not be
revisited during Implement without a new decision record.

## Resolved Decisions

1. **`useRunTimelinesPolling` signature: append `untilIso` as an optional 3rd positional
   parameter, after the already-defaulted `intervalMs`** —
   `useRunTimelinesPolling(sinceIso: string, intervalMs = 5000, untilIso?: string)`. This is
   investigation.md's option (c). Chosen because it is the *only* one of the three options that
   satisfies test_plan.md's explicit constraint that the existing 2-positional-arg call sites in
   `useRunTimelinesPolling.test.ts` (`useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999)`,
   both existing tests) "must keep working unchanged": option (a) (insert `untilIso` as the 2nd
   arg) would silently reinterpret those calls' 2nd arg as `untilIso` instead of `intervalMs` if
   the test file isn't edited, and editing it would still be a source change to "unchanged" call
   sites; option (b) (options-object 2nd arg) would break the same calls outright since they pass a
   raw number, not an object, and giving the 2nd param dual number-or-object shape is unnecessary
   complexity purely to avoid a slightly awkward parameter order. Option (c) leaves every existing
   call site's meaning bit-for-bit identical — new code that wants `until` passes all three
   positionally: `useRunTimelinesPolling(sinceIso, 5000, untilIso)`. This is consistent with
   `useRunsPolling`'s own plain-positional-parameter convention (no options-object precedent exists
   for either public hook), so it does not introduce a new calling convention into `api.ts`.
   `fetchAllRunTimelinesSince` gains a matching optional 2nd parameter
   (`fetchAllRunTimelinesSince(sinceIso: string, untilIso?: string)`), forwarded unchanged to every
   `fetchRunTimelines({ since, until, limit, offset })` page call — `fetchRunTimelines` itself is
   untouched, it already accepts `until`.

2. **`useRunsPolling` / `GET /api/runs` is NOT extended with `until` in this ticket.** The known
   consequence — a custom picker with `untilIso` in the past would still list y-axis rows (via
   `useRunsPolling`, unbounded above) for runs with no visible segments (via `useRunTimelinesPolling`,
   bounded) — is accepted as a documented, non-blocking limitation, not fixed here. Justification,
   directly against the ticket's own text and this project's scope-discipline rule ("never plan
   more work than the ticket scope... note adjacent problems as future tickets, do not add them to
   this plan"):
   - The ticket's Out-of-Scope reads "Implementing the bulk endpoint's `until` param itself — this
     ticket only consumes it once available." Adding a *new* `until` param to a *different*
     endpoint (`GET /api/runs`) is strictly more backend work than that sentence licenses, not less
     — it would be inventing new server-side filtering, not consuming an existing one.
   - `GET /api/runs` and `useRunsPolling`/`fetchRuns`/`FetchRunsParams` do not appear anywhere in
     the ticket's Scope or (corrected) Related Code Areas.
   - The inconsistency is real but cosmetic: an empty-looking y-axis row for a run with no segments
     in the selected window is still informative (it tells the user the run exists but had no
     activity in-window), not misleading or broken.
   - A client-side-only mitigation (filtering the already-fetched `runs` array against `untilIso`
     before passing it to `toChartOption`) was considered and explicitly rejected for *this* plan:
     no acceptance criterion requires it, and adding it would be solving an adjacent problem the
     investigation surfaced rather than one the ticket's AC list asks for — exactly what the
     Planning Rules say not to fold in. It is noted below as a candidate follow-up, not implemented.
   - This is enforced by an architecture-guard test (Step 2) so a future accidental partial-`until`
     addition to `useRunsPolling` doesn't silently create a half-bounded, undocumented state.

3. **`RangeControl` is extracted to its own file, `dashboard-frontend/src/components/RangeControl.tsx`**,
   not defined inline in `ProgressTimelineView.tsx` the way `TicketsView.tsx`'s `FilterSelect` is
   inline in its view file. Reasoning: `test_plan.md`'s New Test #1/#2 both explicitly anticipate a
   possible standalone `RangeControl.test.tsx`, and this control has two genuinely independent pure
   concerns (preset-duration math, `datetime-local`->UTC-ISO conversion) that benefit from being
   unit-tested without mounting the full mocked-ECharts `ProgressTimelineView` tree. `components/`
   already holds every other reusable, non-view-specific UI piece in this codebase
   (`StatTile.tsx`, `GlossaryTooltip.tsx`, etc.) — `RangeControl` fits that shelf.

4. **Preset selector uses a button group (`aria-pressed` toggle buttons), not a `<select>`.**
   Both are "plain HTML" per the ticket's own text; a button group is used because (a) it matches
   `TicketsView.tsx`'s own toggle-button precedent for the tag chips (lines ~280-296) at least as
   directly as `FilterSelect`'s `<select>` does, and (b) a `<select>` implies a single persistent
   "current value" that must always match one of its options — exactly the class of bug
   `TCK-20260718-FILTER-SELECT-DROPOUT` hardened against — whereas the range-control's "current
   range" can legitimately be a *custom* value matching no preset at all (after editing the
   datetime-local inputs). A button group naturally supports "none of the four are currently
   highlighted" without needing `FilterSelect`'s defensive missing-option branch at all.

## Steps

### Step 1 — Extend `useRunTimelinesPolling`/`fetchAllRunTimelinesSince` to forward `until`
**Files:** `dashboard-frontend/src/api.ts`

**Change:** Two edits to the existing "Bulk run timelines" block (currently lines ~449-530):

1. `fetchAllRunTimelinesSince`: add an optional 2nd parameter and forward it into every page's
   `fetchRunTimelines` call:
   ```ts
   async function fetchAllRunTimelinesSince(
     sinceIso: string,
     untilIso?: string,
   ): Promise<Record<string, TimelineEntry[]>> {
     const merged: Record<string, TimelineEntry[]> = {}
     let offset = 0

     for (;;) {
       const page = await fetchRunTimelines({
         since: sinceIso,
         until: untilIso,
         limit: RUN_TIMELINES_PAGE_LIMIT,
         offset,
       })
       const pageRunCount = Object.keys(page.entries_by_run).length
       Object.assign(merged, page.entries_by_run)
       if (pageRunCount < RUN_TIMELINES_PAGE_LIMIT) {
         break
       }
       offset += RUN_TIMELINES_PAGE_LIMIT
     }

     return merged
   }
   ```
   (`fetchRunTimelines` itself is untouched — its `params.until` handling already exists.)
2. `useRunTimelinesPolling`: add the optional 3rd param per Resolved Decision 1, forward it to
   `fetchAllRunTimelinesSince`, and include it in the effect's dependency array so a change to
   `untilIso` alone (with `sinceIso` unchanged) still triggers a re-poll:
   ```ts
   export function useRunTimelinesPolling(
     sinceIso: string,
     intervalMs = 5000,
     untilIso?: string,
   ): UseRunTimelinesPollingResult {
     const [entriesByRun, setEntriesByRun] = useState<Record<string, TimelineEntry[]>>({})
     const [isLoading, setIsLoading] = useState(true)
     const [error, setError] = useState<Error | null>(null)

     useEffect(() => {
       let cancelled = false

       async function poll() {
         try {
           const merged = await fetchAllRunTimelinesSince(sinceIso, untilIso)
           if (!cancelled) {
             setEntriesByRun(merged)
             setError(null)
             setIsLoading(false)
           }
         } catch (err) {
           if (!cancelled) {
             setError(err instanceof Error ? err : new Error(String(err)))
             setIsLoading(false)
           }
         }
       }

       poll()
       const intervalId = setInterval(poll, intervalMs)
       return () => {
         cancelled = true
         clearInterval(intervalId)
       }
     }, [sinceIso, intervalMs, untilIso])

     return { entriesByRun, isLoading, error }
   }
   ```

**Do NOT touch:** `fetchRunTimelines` (already correct), `useRunsPolling`, `fetchAllRunsSince`,
`fetchRuns`, `FetchRunsParams`, `mergeAndSortRuns` — none of these change in this step (see
Resolved Decision 2).

**Verify:** New tests added to `useRunTimelinesPolling.test.ts` in Step 1b below, plus the file's 3
existing tests continue passing unmodified.

---

### Step 1b — `useRunTimelinesPolling.test.ts`: new tests for `until` forwarding + 2-arg compatibility
**Files:** `dashboard-frontend/src/test/useRunTimelinesPolling.test.ts`

**Change:** Add two new `it()` blocks to the existing `describe('useRunTimelinesPolling', ...)`
block (per test_plan.md New Test #6) — do not modify the file's 3 existing tests:

1. `'forwards until to the bulk fetch query string when the 3rd argument is provided'` — render the
   hook with `useRunTimelinesPolling('2026-07-15T00:00:00Z', 5000, '2026-07-16T00:00:00Z')`, assert
   the mocked `fetch`'s first call URL's query string contains `until=2026-07-16T00%3A00%3A00.000Z`
   (or the equivalent decoded assertion via `new URL(...).searchParams.get('until')`).
2. `'2-argument call omits until from the query string (2nd arg still means intervalMs, not untilIso)'`
   — render the hook with only `useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999)` (the
   exact existing call shape), assert the mocked `fetch`'s call URL has no `until` param at all.
   This directly proves the 2-arg call sites' meaning did not silently shift.

**Do NOT touch:** the 3 pre-existing `it()` blocks in this file (pagination-union-merge,
single-page-no-second-request, error handling) — leave their bodies byte-for-byte as-is.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/useRunTimelinesPolling.test.ts`.

---

### Step 2 — `useRunsPolling`/`GET /api/runs` no-`until` architecture guard (no source change)
**Files:** `dashboard-frontend/src/test/useRunsPolling.test.ts`

**Change:** Per Resolved Decision 2, add one new `it()` to the existing
`describe('useRunsPolling', ...)` block that reads `api.ts`'s own source as text (mirroring
`toChartOption.test.ts`'s `?raw` Vite-import regex-guard pattern from the prior ticket) and asserts:
1. The `FetchRunsParams` interface body contains no `until` field.
2. The `useRunsPolling` function signature line contains no `until` parameter.

```ts
import apiSource from '../api.ts?raw'

it('FetchRunsParams/useRunsPolling still have no until param (decision: not extended by TCK-20260720-TIMELINE-RANGE-CONTROL)', () => {
  const paramsBlock = apiSource.match(/export interface FetchRunsParams \{[^}]*\}/)?.[0] ?? ''
  expect(paramsBlock).not.toMatch(/\buntil\b/)
  const signatureLine = apiSource.match(/export function useRunsPolling\([^)]*\)/)?.[0] ?? ''
  expect(signatureLine).not.toMatch(/\buntil\b/)
})
```

This is a permanent regression guard, not a one-time acceptance check — its purpose is to prevent a
future implementer from "fixing" the documented y-axis-row inconsistency by silently bolting an
`until` param onto `useRunsPolling` without a new decision record.

**Do NOT touch:** `useRunsPolling`, `fetchRuns`, `fetchAllRunsSince`, `FetchRunsParams` themselves —
this step adds a test only, no source edit anywhere.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/useRunsPolling.test.ts`.

---

### Step 3 — Create `timeRangePresets.ts` (pure preset math + datetime-local conversion)
**Files:** `dashboard-frontend/src/lib/timeRangePresets.ts` (new)

**Change:** New pure module, no React, no DOM dependency beyond the standard `Date` global:

```ts
export interface RangePreset {
  id: string
  label: string
  durationMs: number
}

export const RANGE_PRESETS: RangePreset[] = [
  { id: '1h', label: '1h', durationMs: 60 * 60 * 1000 },
  { id: '6h', label: '6h', durationMs: 6 * 60 * 60 * 1000 },
  { id: '24h', label: '24h', durationMs: 24 * 60 * 60 * 1000 },
  { id: '7d', label: '7d', durationMs: 7 * 24 * 60 * 60 * 1000 },
]

// Single source of truth for "today's default window" (previously ProgressTimelineView.tsx's own
// local SINCE_WINDOW_MS = 24 * 60 * 60 * 1000 literal). Both the initial-mount default AND the
// "24h" preset button MUST read this same constant/preset entry — never a second, independently
// typed 24h literal (Anti-Drift Hazard from investigation.md).
export const DEFAULT_PRESET_ID = '24h'
const DEFAULT_PRESET = RANGE_PRESETS.find((p) => p.id === DEFAULT_PRESET_ID)
if (!DEFAULT_PRESET) {
  throw new Error(`RANGE_PRESETS is missing the default preset id ${DEFAULT_PRESET_ID}`)
}
export const DEFAULT_WINDOW_MS = DEFAULT_PRESET.durationMs

export function computePresetRange(
  presetId: string,
  nowMs: number,
): { sinceIso: string; untilIso: string } | null {
  const preset = RANGE_PRESETS.find((p) => p.id === presetId)
  if (!preset) return null
  return {
    sinceIso: new Date(nowMs - preset.durationMs).toISOString(),
    untilIso: new Date(nowMs).toISOString(),
  }
}

// Converts an <input type="datetime-local"> value (naive local time, "YYYY-MM-DDTHH:mm", no
// seconds, no timezone) to a UTC ISO 8601 string matching the backend's zero-padded
// lexical-comparison convention. `new Date(value)` interprets the naive string in the browser's
// local timezone; `.toISOString()` re-renders it as zero-padded UTC. Returns null for an empty or
// unparseable value (e.g. the input was cleared) rather than throwing or emitting "Invalid Date".
export function datetimeLocalToUtcIso(value: string): string | null {
  if (!value) return null
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return null
  return parsed.toISOString()
}

// Inverse of datetimeLocalToUtcIso, for populating an <input type="datetime-local">'s displayed
// value from a UTC ISO string. Renders in the browser's local time, truncated to minutes (matching
// the input's own minute-granularity default).
export function utcIsoToDatetimeLocalValue(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
```

**Do NOT touch:** any existing file. This is a brand-new module with zero imports from `api.ts`,
`toChartOption.ts`, or `phasePalette.ts`.

**Verify:** Step 3b's `timeRangePresets.test.ts`.

---

### Step 3b — `timeRangePresets.test.ts`
**Files:** `dashboard-frontend/src/test/timeRangePresets.test.ts` (new)

**Change:** Pure-function unit tests, no rendering, per test_plan.md New Test #2/#3:

1. **`computePresetRange`** — for each of the 4 preset ids, with a fixed `nowMs`, assert
   `sinceIso === new Date(nowMs - durationMs).toISOString()` and `untilIso === new Date(nowMs).toISOString()`
   exactly; assert `computePresetRange('bogus', nowMs) === null`.
2. **`datetimeLocalToUtcIso`** — (a) a straightforward same-day value converts correctly to UTC
   ISO; (b) at least one value whose local-time-to-UTC conversion crosses a date boundary (e.g. a
   late-evening local value in a timezone that pushes the UTC date forward a day — use
   `vi.stubEnv`/a fixed offset or construct the expected value via the same `new Date(...).toISOString()`
   call the implementation uses, so the test is timezone-independent rather than hardcoding a
   specific UTC-offset assumption); (c) empty string and a clearly-invalid string (`'not-a-date'`)
   both return `null`, no throw.
3. **`utcIsoToDatetimeLocalValue`** — round-trips: for a fixed ISO string, assert the output is a
   zero-padded `YYYY-MM-DDTHH:mm` shape (regex `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$`), and that
   `datetimeLocalToUtcIso(utcIsoToDatetimeLocalValue(iso))` round-trips back to the same instant
   modulo seconds truncation (compare `Date.parse` values with a &lt;60000ms tolerance, not string
   equality, since the local-value shape drops seconds).
4. **`DEFAULT_WINDOW_MS` equals the `'24h'` preset's `durationMs`** — a one-line guard that these
   two never diverge (`expect(DEFAULT_WINDOW_MS).toBe(RANGE_PRESETS.find(p => p.id === '24h')!.durationMs)`).

**Do NOT touch:** any other test file in this step.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/timeRangePresets.test.ts`.

---

### Step 4 — Create `RangeControl.tsx` component
**Files:** `dashboard-frontend/src/components/RangeControl.tsx` (new)

**Change:** New presentational component, styled per `TicketsView.tsx`'s real filter-bar precedent
(`bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary`, `data-testid` on
every interactive element, immediate-call-on-change — no submit button):

```tsx
import { useState } from 'react'
import {
  RANGE_PRESETS,
  DEFAULT_PRESET_ID,
  computePresetRange,
  datetimeLocalToUtcIso,
  utcIsoToDatetimeLocalValue,
} from '@/lib/timeRangePresets'

export interface RangeControlProps {
  sinceIso: string
  untilIso: string
  onRangeChange: (sinceIso: string, untilIso: string) => void
}

export function RangeControl({ sinceIso, untilIso, onRangeChange }: RangeControlProps) {
  // Ephemeral UI-only state (which preset button, if any, is highlighted) — not durable, does not
  // need to survive a remount, mirrors what button was last clicked rather than re-deriving it by
  // comparing sinceIso/untilIso against every preset on every render.
  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(DEFAULT_PRESET_ID)

  function handlePresetClick(presetId: string) {
    const range = computePresetRange(presetId, Date.now())
    if (!range) return
    setSelectedPresetId(presetId)
    onRangeChange(range.sinceIso, range.untilIso)
  }

  function handleCustomStartChange(value: string) {
    const iso = datetimeLocalToUtcIso(value)
    if (iso === null) return
    // Lexical string comparison, matching the backend's own bounding convention (Anti-Drift
    // Hazard) — refuse an inverted range rather than silently sending since > until.
    if (iso >= untilIso) return
    setSelectedPresetId(null)
    onRangeChange(iso, untilIso)
  }

  function handleCustomEndChange(value: string) {
    const iso = datetimeLocalToUtcIso(value)
    if (iso === null) return
    if (sinceIso >= iso) return
    setSelectedPresetId(null)
    onRangeChange(sinceIso, iso)
  }

  return (
    <div className="flex flex-wrap items-end gap-3" data-testid="timeline-range-control">
      <div className="flex items-center gap-1" data-testid="timeline-range-presets">
        {RANGE_PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            data-testid={`range-preset-${preset.id}`}
            aria-pressed={selectedPresetId === preset.id}
            onClick={() => handlePresetClick(preset.id)}
            className={`px-2 py-1 rounded-md text-[11px] border ${
              selectedPresetId === preset.id
                ? 'bg-accent-blue/15 text-accent-blue border-accent-blue'
                : 'bg-bg-tertiary text-text-secondary border-border'
            }`}
          >
            {preset.label}
          </button>
        ))}
      </div>
      <label className="flex flex-col text-[11px] text-text-secondary gap-0.5">
        Start
        <input
          type="datetime-local"
          data-testid="range-custom-start"
          key={`start-${sinceIso}`}
          defaultValue={utcIsoToDatetimeLocalValue(sinceIso)}
          onChange={(event) => handleCustomStartChange(event.target.value)}
          className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary"
        />
      </label>
      <label className="flex flex-col text-[11px] text-text-secondary gap-0.5">
        End
        <input
          type="datetime-local"
          data-testid="range-custom-end"
          key={`end-${untilIso}`}
          defaultValue={utcIsoToDatetimeLocalValue(untilIso)}
          onChange={(event) => handleCustomEndChange(event.target.value)}
          className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary"
        />
      </label>
    </div>
  )
}
```

`defaultValue` + a `key` derived from the current `sinceIso`/`untilIso` (not `value`) is deliberate:
it lets each input remount and pick up the parent's latest value whenever a preset click changes
`sinceIso`/`untilIso` externally, while remaining freely typeable/editable during normal user
interaction without React fighting every keystroke the way a fully-controlled `value` prop would.

**Do NOT touch:** `TicketsView.tsx`, `FilterSelect` — read only as a styling/structure reference,
never imported from or modified.

**Verify:** Step 4b's `RangeControl.test.tsx`.

---

### Step 4b — `RangeControl.test.tsx`
**Files:** `dashboard-frontend/src/test/RangeControl.test.tsx` (new)

**Change:** Component-level tests using `@testing-library/react`, per test_plan.md New Test #1/#2:

1. **Each preset button calls `onRangeChange` with `sinceIso = now - <preset duration>`,
   `untilIso = now`** — `vi.useFakeTimers()` + `vi.setSystemTime(...)` to pin "now"; for each of
   1h/6h/24h/7d, click `data-testid="range-preset-<id>"` and assert `onRangeChange` was called with
   the exact ISO strings `computePresetRange` would produce (import and reuse that function to
   compute the expected value — do not hand-compute a second time in the test).
2. **Custom start/end inputs emit zero-padded UTC ISO strings on change** — `fireEvent.change` on
   `range-custom-start`/`range-custom-end` with a `datetime-local`-shaped value string (e.g.
   `'2026-07-20T23:30'`), assert `onRangeChange` was called with a value matching
   `/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/`. If jsdom's `datetime-local` input change-event
   simulation proves unreliable in this environment (flagged as a real risk in investigation.md),
   fall back to asserting `datetimeLocalToUtcIso`/`utcIsoToDatetimeLocalValue` directly (already
   covered by Step 3b) and keep this test scoped to proving the `onChange` handler is wired to call
   them — do not skip the wiring assertion even if the DOM-level value simulation is awkward.
3. **Selecting a preset then editing a custom input clears the preset highlight** — click
   `range-preset-24h` (assert `aria-pressed="true"`), then `fireEvent.change` on
   `range-custom-start`; assert `range-preset-24h`'s `aria-pressed` is now `"false"` and no other
   preset button has `aria-pressed="true"` either (guards the `FILTER-SELECT-DROPOUT`-class bug: no
   preset button should ever silently claim to be "active" once the range no longer matches it).
4. **Rejects an inverted custom range** — with `sinceIso`/`untilIso` props set, `fireEvent.change`
   on `range-custom-end` with a value earlier than the current `sinceIso`; assert `onRangeChange`
   was NOT called (the lexical `sinceIso >= iso` guard fires).

**Do NOT touch:** `ProgressTimelineView.test.tsx` in this step (Step 5b covers integration).

**Verify:** `cd dashboard-frontend && npx vitest run src/test/RangeControl.test.tsx`.

---

### Step 5 — Wire `RangeControl` + live `sinceIso`/`untilIso` into `ProgressTimelineView.tsx`
**Files:** `dashboard-frontend/src/views/ProgressTimelineView.tsx`

**Change:**
1. Remove the file-level `SINCE_WINDOW_MS` constant; import `DEFAULT_WINDOW_MS` from
   `@/lib/timeRangePresets` instead (single source of truth, per Anti-Drift Hazard).
2. Replace the setter-less `const [sinceIso] = useState(...)` with paired, settable state:
   ```ts
   const [sinceIso, setSinceIso] = useState(() => new Date(Date.now() - DEFAULT_WINDOW_MS).toISOString())
   const [untilIso, setUntilIso] = useState(() => new Date().toISOString())
   ```
3. Change the `useRunTimelinesPolling` call to pass `untilIso` as the 3rd positional argument
   (Resolved Decision 1), explicitly passing the existing default `intervalMs` value since JS
   cannot skip a middle positional parameter:
   ```ts
   const { entriesByRun } = useRunTimelinesPolling(sinceIso, 5000, untilIso)
   ```
   Leave `useRunsPolling(sinceIso)` exactly as-is — no `untilIso` argument (Resolved Decision 2).
4. Add a single handler and pass it + the two state values to a new `<RangeControl>` rendered
   directly above `<ReactEChartsCore>`:
   ```tsx
   function handleRangeChange(nextSinceIso: string, nextUntilIso: string) {
     setSinceIso(nextSinceIso)
     setUntilIso(nextUntilIso)
   }
   ```
   ```tsx
   <div data-testid="progress-timeline-view" className="flex flex-col h-full p-4 gap-3">
     <RangeControl sinceIso={sinceIso} untilIso={untilIso} onRangeChange={handleRangeChange} />
     <ReactEChartsCore
       echarts={echarts}
       option={option}
       onEvents={onEvents}
       style={{ height: '100%', width: '100%' }}
       notMerge
     />
   </div>
   ```
   (`gap-3` added to the existing `flex flex-col h-full p-4` wrapper so the control and the chart
   don't visually collide — a pure layout change, not a behavior change.)
5. Add the import: `import { RangeControl } from '@/components/RangeControl'` and
   `import { DEFAULT_WINDOW_MS } from '@/lib/timeRangePresets'`.

**Do NOT touch:** `nowIso`/`NOW_TICK_MS`/the `setInterval` ticking effect (untouched — still drives
only `toChartOption`'s live-segment trailing edge, never repurposed as a default for `untilIso`);
`toChartOption` call signature (still `toChartOption(runs, entriesByRun, nowIso, glossary)` — do
not pass `untilIso` into it); the `onEvents.click` handler; the `dataZoom` array (lives entirely
inside `toChartOption.ts`, never read or written here). Do not add any `onEvents.datazoom` handler.

**Verify:** Step 5b's extended `ProgressTimelineView.test.tsx`.

---

### Step 5b — Extend `ProgressTimelineView.test.tsx`: default window, dataZoom independence, range-control integration
**Files:** `dashboard-frontend/src/test/ProgressTimelineView.test.tsx`

**Change:** Add new tests to the existing file (its `vi.mock('echarts-for-react/lib/core', ...)`
and `vi.mock('@/api', ...)` setup from the prior ticket is reused as-is, extended to also capture
calls into `useRunTimelinesPolling`'s mock so `untilIso` can be asserted):

1. **Default mount reproduces `now-24h` to `now` bit-for-bit (AC #3)** — `vi.useFakeTimers()` +
   `vi.setSystemTime(...)`; render with no interaction; assert the mocked `useRunsPolling` was
   called with `sinceIso === new Date(fixedNow - 24*60*60*1000).toISOString()` and the mocked
   `useRunTimelinesPolling` was called with that same `sinceIso` and `untilIso === new
   Date(fixedNow).toISOString()`. This is the single highest-value regression guard per
   test_plan.md — any drift here silently changes production default behavior.
2. **Quick-range preset click updates the bounded fetch, not just the chart (AC #1)** — click
   `range-preset-1h` (rendered via the real, unmocked `RangeControl`); assert the mocked
   `useRunTimelinesPolling` is re-invoked (React re-render) with `sinceIso`/`untilIso` matching
   `now-1h`/`now` exactly (fake timers pinned, exact-value assertion per test_plan.md, not a
   tolerant range).
3. **Custom picker change triggers a refetch bounded by the exact custom values (AC #2)** —
   `fireEvent.change` on `range-custom-start`/`range-custom-end` (or fall back per Step 4b test 2's
   contingency) and assert the mocked `useRunTimelinesPolling`'s next call reflects the exact
   converted UTC ISO values, not the previous default window.
4. **`dataZoom`/range-control independence (AC #4)** — after a preset click or custom-picker
   change that alters `sinceIso`/`untilIso`, assert `capturedProps.option.dataZoom` is still
   exactly the same two declarative entries (`type: 'inside'`, `type: 'slider'`, no injected
   `start`/`end`/`startValue`/`endValue`) as the pre-existing "two dataZoom entries" test already
   asserts on initial mount — i.e. changing the range control must not perturb `dataZoom`'s shape.
   Also assert `capturedProps.onEvents` still has no `datazoom`/`dataZoom` key (extends the
   existing "does not wire any datazoom/dataZoom onEvents handler" test's spirit across a
   range-control interaction, not just at mount).
5. **Range control renders above the chart** — assert `screen.getByTestId('timeline-range-control')`
   exists alongside the existing `mocked-echarts` assertion, and that
   `screen.getAllByTestId('mocked-echarts')` still returns exactly one element (guards against the
   new markup accidentally causing the mocked chart to render more than once).

**Do NOT touch:** the existing "row-click navigates" and root-`data-testid` tests' assertions
beyond what's needed to keep them passing with the new markup present.

**Verify:** `cd dashboard-frontend && npx vitest run src/test/ProgressTimelineView.test.tsx`.

---

### Step 6 — Full scoped regression run
**Files:** none (verification only)

**Change:** none — run, in order, from `dashboard-frontend/`:
```
npx vitest run src/test/ProgressTimelineView.test.tsx src/test/useRunTimelinesPolling.test.ts \
  src/test/useRunsPolling.test.ts src/test/App.test.tsx src/test/toChartOption.test.ts \
  src/test/timeRangePresets.test.ts src/test/RangeControl.test.tsx
npx tsc -b --noEmit
npm run build
```
then from the repo root:
```
python3 -m pytest tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_frontend_api_surface.py -v
```

**Do NOT touch:** any file outside Steps 1-5 — this step is verification-only. Never run the
unscoped `npx vitest run` (whole `src/test/` directory) or `pytest tests/`.

**Verify:** all commands pass, zero regressions in any file this ticket doesn't touch
(`toChartOption.test.ts`, `App.test.tsx`, and the two backend guard files should all be unaffected
pass-throughs).

---

### Step 7 — Browser verification (mandatory, distinct from vitest/tsc)

**This step is required before the ticket can be considered done.** Vitest/tsc prove the
range-control *wires* correctly against mocked hooks; they do not prove it *renders* as a usable,
legible control in a real browser, or that a real preset click / custom picker interaction visibly
re-draws the chart against real (or realistically shaped) data.

**Note on environment tooling:** the immediately-prior ticket in this same area
(`TCK-20260720-PROGRESS-TIMELINE-VIEW`) found browser automation unavailable in this execution
environment (`claude-in-chrome` not set up, no `mcp__claude-in-chrome__*` tools registered, no
Playwright/Puppeteer, no system browser binary) and substituted a documented non-visual
verification instead of skipping or falsely claiming a pass (see that ticket's stored `plan.md`,
"Revision 2"). **The same tooling gap may exist for this ticket.** If so, follow the identical
honest-substitution pattern: do not skip this step silently, do not claim a visual pass that did
not happen. Re-check availability first (`claude-in-chrome` skill, `ToolSearch` for
`mcp__claude-in-chrome__*`, `command -v google-chrome chromium chromium-browser`) since environment
state can change between tickets.

**Change:** none (verification only). From `dashboard-frontend/`: `npm run dev`. Then, with real
browser access:

1. Confirm the range-control (4 preset buttons + 2 datetime inputs) renders above the chart, styled
   consistently with the rest of the dashboard (not visually broken/unstyled).
2. Click each of the 1h/6h/24h/7d preset buttons; confirm the highlighted (`aria-pressed`) button
   changes and the chart's visible time window narrows/widens accordingly, with a real network
   request to `/api/runs/timeline?...` containing the expected `since`/`until` values (check the
   Network tab).
3. Set a custom start/end via the two datetime inputs; confirm no preset button remains highlighted
   and the chart's window updates to the custom range, again backed by a real bounded network
   request.
4. Confirm dragging the chart's own `dataZoom` slider/inside-zoom does NOT change the range-control's
   displayed preset/custom values and does NOT fire a new `/api/runs`-family network request — the
   two layers must visibly stay independent.
5. On a fresh page load with no interaction, confirm the initial network request's `since`/`until`
   match "now-24h" to "now" (same as pre-ticket behavior).

If tooling is unavailable, substitute the same class of non-visual verification the prior ticket
used (start the real backend + Vite dev server, confirm `/api/runs/timeline` responds with real
`since`/`until` bounds matching what the range-control would send, confirm the new files compile
and are served by Vite with no transform errors) and record explicitly, in the ticket's
Implementation Notes and in this plan's own Deviations section (add a new "Revision" entry, do not
edit Steps 1-6 to pretend this happened), exactly what was and was not verified.

**Do NOT** substitute this step with only `npm run test -- --run` and `npx tsc -b --noEmit`.

**Verify:** direct visual/interactive confirmation of items 1-5 above, or an honestly-documented
substitution per the above.

---

### Step 8 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add one new entry. Re-verify the true next-free ID at implementation time (`grep -n
"^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5` — as of planning the tail is
`INFRA-303`, so the next id is expected to be `INFRA-304`, but re-check since other in-flight work
could claim it first). Entry shape, following `INFRA-301`/`INFRA-303`'s field set:

- `status: verified`
- `priority: P2`
- `text`: describes the `RangeControl` component, `timeRangePresets.ts`'s preset/conversion
  helpers, the `useRunTimelinesPolling` 3-arg signature extension (Resolved Decision 1), and the
  explicit decision to leave `useRunsPolling`/`GET /api/runs` un-extended (Resolved Decision 2).
- `v2_evidence`: cite post-implementation line numbers in `api.ts` (Step 1), `timeRangePresets.ts`
  (Step 3), `RangeControl.tsx` (Step 4), `ProgressTimelineView.tsx` (Step 5).
- `proof_type: regression`
- `test_path`: `dashboard-frontend/src/test/RangeControl.test.tsx` (most directly exercises the new
  component's contract) — or `ProgressTimelineView.test.tsx`'s default-window test if that reads as
  more directly proving the entry's "no default-behavior regression" claim; implementer's judgment.
- `divergence_note: null`
- `support_boundary`: same "no simulation behavior, Mechanics Bible chapter, or engine contract
  governs this module" framing `INFRA-301`/`INFRA-303` use, plus a one-line cross-reference to
  INFRA-301 (`until` param origin) and INFRA-303 (`ProgressTimelineView`/`useRunTimelinesPolling`
  origin) per the ledger's own established cross-reference pattern.

**Do NOT touch:** `INFRA-301`, `INFRA-303`, or any other existing entry — add-only.

**Verify:** manual cross-check that `test_path` exists and passes; YAML validates against
`docs/parity_ledger/schema.json`.

---

### Step 9 — Ticket hygiene: correct stale Related Code Areas, fill close-out sections
**Files:** `tickets/inprogress/TCK-20260720-TIMELINE-RANGE-CONTROL.md`

**Change:** Before moving to `tickets/done/`:
1. Replace the ticket's "Related Code Areas" list (currently the stale
   `RecentActivityGantt.tsx`/`TimeAxis.tsx`/`GanttBar.tsx` set, all deleted by
   `TCK-20260720-PROGRESS-TIMELINE-VIEW`) with the real files this plan touches:
   `dashboard-frontend/src/views/ProgressTimelineView.tsx`, `dashboard-frontend/src/api.ts`,
   `dashboard-frontend/src/components/RangeControl.tsx`, `dashboard-frontend/src/lib/timeRangePresets.ts`.
2. Fill `## Implementation Notes` with the two Resolved Decisions from this plan (signature shape,
   `useRunsPolling` scope decision) and the Step 7 browser-verification outcome (pass, or the
   honest substitution actually performed).
3. Fill `## Test Summary` and `## Files Changed` per Definition of Done.

**Do NOT touch:** any other ticket field's substantive content beyond what's listed; do not
retroactively edit the ticket's Scope/Out-of-Scope/Acceptance Criteria sections themselves.

**Verify:** `done-checker`'s frontmatter/field validation passes.

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope section and the investigation's Anti-Drift
Hazards — none of the following may be touched by this plan:

- **Do not implement the bulk endpoint's `until` param itself** — already done (INFRA-301); this
  ticket only consumes it via `fetchAllRunTimelinesSince`/`useRunTimelinesPolling` (Step 1).
- **Do not modify `RecentActivityGantt.tsx`, `TimeAxis.tsx`, or `GanttBar.tsx`** — all three are
  deleted; the ticket's own stale Related Code Areas list must not send an implementer looking for
  them (corrected in Step 9, but do not resurrect the files themselves).
- **Do not touch `toChartOption.ts` or its `nowIso` parameter/signature** — confirmed unrelated,
  drives only the live-segment trailing edge. Do not repurpose `nowIso` as a default `untilIso`.
- **Do not let `sinceIso`/`untilIso` read from or write to `dataZoom`'s state** — both `dataZoom`
  entries stay purely declarative inside `toChartOption.ts`; no `onEvents.datazoom` handler is ever
  added in `ProgressTimelineView.tsx`.
- **Do not add an `until` param to `GET /api/runs`, `get_runs()`, `FetchRunsParams`, `fetchRuns`, or
  `useRunsPolling`** — Resolved Decision 2, explicit and permanent for this ticket, guarded by
  Step 2's regression test.
- **C5 docs update** (`docs/guides/agent_ops_dashboard.md`,
  `docs/observability/agent_ops_dashboard_contract.md`) — deferred to a separate ticket, not
  touched here.
- **Do not add filtering/grouping-by-tier/workflow/status controls** to the range-control or
  `ProgressTimelineView` — out of scope per the ticket and the originating proposal doc.
- **Do not introduce a second `24h`/`24 * 60 * 60 * 1000` literal** anywhere — `DEFAULT_WINDOW_MS`
  in `timeRangePresets.ts` is the single source, used by both the initial-mount default and (via
  `RANGE_PRESETS`) the `'24h'` preset button.

## Dependency Map

- **Step 1** (`api.ts` hook extension) — independent, first.
- **Step 1b** (its tests) — depends on Step 1.
- **Step 2** (`useRunsPolling` guard test) — independent of Step 1; can run in parallel.
- **Step 3** (`timeRangePresets.ts`) — independent of Steps 1-2.
- **Step 3b** (its tests) — depends on Step 3.
- **Step 4** (`RangeControl.tsx`) — depends on **Step 3** (imports its helpers).
- **Step 4b** (its tests) — depends on Step 4.
- **Step 5** (`ProgressTimelineView.tsx` wiring) — depends on **Step 1** (extended hook), **Step 3**
  (`DEFAULT_WINDOW_MS`), and **Step 4** (`RangeControl` component).
- **Step 5b** (its tests) — depends on Step 5.
- **Step 6** (regression run) — depends on all of Steps 1-5b.
- **Step 7** (browser verification) — depends on Step 5 being functionally complete.
- **Step 8** (parity ledger) — depends on Step 6 (cites real post-implementation evidence).
- **Step 9** (ticket hygiene) — last, depends on all prior steps being complete.

Steps 1/1b, 2, and 3/3b may proceed fully in parallel with each other; Step 4/4b requires Step 3
first; Step 5/5b is the integration point requiring Steps 1, 3, and 4 all complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Quick-range preset (1h/6h/24h/7d) sets `sinceIso`/`untilIso` and bounds the bulk timeline fetch, not just chart `dataZoom` | Step 1, Step 4, Step 5 | `RangeControl.test.tsx` test 1; `ProgressTimelineView.test.tsx` test 2 |
| Custom start/end picker emits zero-padded ISO 8601 UTC strings and triggers a refetch bounded by those exact values | Step 3, Step 4, Step 5 | `timeRangePresets.test.ts` test 2; `RangeControl.test.tsx` test 2; `ProgressTimelineView.test.tsx` test 3 |
| Initial mount with no interaction reproduces today's default (`now-24h` to `now`), no default-behavior regression | Step 3, Step 5 | `ProgressTimelineView.test.tsx` test 1 |
| Range-control state does not reset/couple to the chart's independent `dataZoom` state | Step 5 (no wiring added) | `ProgressTimelineView.test.tsx` test 4 |
| Server-side bounding depends on the bulk endpoint's `until` support (already landed, INFRA-301) — ticket is a consumer only | Step 1 | N/A — precondition already satisfied, confirmed in investigation.md |

## Anti-Drift Notes

- **`DEFAULT_WINDOW_MS`/`RANGE_PRESETS` in `timeRangePresets.ts` is the only place a `24h`-shaped
  duration literal may live.** `ProgressTimelineView.tsx`'s initial-mount default and the `'24h'`
  preset button must both trace back to this single constant — never reintroduce a second
  independently-typed `24 * 60 * 60 * 1000` literal.
- **`useRunTimelinesPolling`'s new 3rd parameter is positional, after the defaulted `intervalMs`.**
  Any new call site that wants `until` must pass `intervalMs` explicitly (e.g. `(sinceIso, 5000,
  untilIso)`) — there is no way to "skip" the 2nd positional param in JS/TS.
- **`useRunsPolling` staying `until`-unbounded is an intentional, documented, permanently-guarded
  decision (Resolved Decision 2), not an oversight.** Do not add `until` to it in this ticket's
  scope; Step 2's test exists specifically to catch a future accidental partial-add.
- **`RangeControl`'s inputs use `defaultValue` + a `key` tied to the current ISO prop, not a fully
  controlled `value`.** This is deliberate (avoids React fighting every keystroke while still
  syncing after external preset-driven changes) — do not "simplify" it to a plain controlled `value`
  without re-verifying the preset-click-then-type interaction still works.
- **Lexical string comparison, not `Date` comparison, governs the backend's bounding.** As long as
  both `sinceIso`/`untilIso` are produced via `.toISOString()` (guaranteed by `computePresetRange`
  and `datetimeLocalToUtcIso`), lexical and chronological ordering coincide — but this is a fragile
  invariant, not a rewritable assumption; never bypass these two helpers to hand-construct an ISO
  string elsewhere.
- **`toChartOption.ts`'s `nowIso` parameter and both `dataZoom` entries are read-only reference
  points for this ticket — never modified, never fed from `sinceIso`/`untilIso`, and never fed
  back into `sinceIso`/`untilIso`.** This is the single most likely scope-creep vector in this
  ticket per the investigation; Step 5b test 4 is a permanent regression guard for it.
- **Candidate future ticket, not in this plan's scope:** client-side filtering of the already-fetched
  `runs` array against `untilIso` before passing it to `toChartOption`, to eliminate the documented
  y-axis-row inconsistency from Resolved Decision 2, without touching the backend. Noted here per
  the Planning Rules ("note adjacent problems as future tickets") — not to be implemented as part
  of this ticket.

## Deviations

**Revision 1 (implementation-time deviation, Step 8 — no scope/design change).** The plan tentatively
cited `INFRA-304` as the next-free parity ledger id and expected to re-verify at implementation
time. `grep -n "^- id: INFRA-" docs/parity_ledger/infrastructure.yaml | tail -5` at implementation
time confirmed the tail was still `INFRA-303` (no other in-flight work had claimed a slot since
planning), so `INFRA-304` was used exactly as tentatively planned — recorded here only because the
plan explicitly asked for re-verification, not because the id actually changed.

**Revision 2 (implementation-time deviation, Step 7 — environment tooling gap, not a scope or
design change).** Per the plan's own anticipation ("The same tooling gap may exist for this
ticket"), browser automation was re-checked at implementation time and confirmed unavailable in
this execution environment, exactly as the immediately-prior ticket
(`TCK-20260720-PROGRESS-TIMELINE-VIEW`) found: the `claude-in-chrome` skill reported the extension
is not set up; `ToolSearch` for `mcp__claude-in-chrome__*` returned no matches; `command -v
google-chrome chromium chromium-browser` all failed. The plan's mandated fallback was followed:
the real dashboard backend (`uvicorn src.api.agent_ops_dashboard.main:app`, port 8471) and the real
Vite dev server (`npm run dev`, port 5174, proxying `/api`) were started; all 4 changed/new
frontend files (`RangeControl.tsx`, `timeRangePresets.ts`, `ProgressTimelineView.tsx`, `api.ts`)
were confirmed served by Vite with 200 responses (no transform errors); real `GET
/api/runs/timeline` requests with `since`/`until` values shaped exactly like the `'24h'` and `'1h'`
presets' output were issued both directly against the backend and through the Vite proxy, both
returning 200 with real production data bounded correctly; a real `GET /api/runs?since=...`
request (no `until`, confirming Resolved Decision 2's behavior end-to-end) also returned 200. Both
servers were cleanly torn down afterward. **Not verified**: actual on-screen rendering/legibility,
real mouse click/hover interaction, drag-based `dataZoom` interaction, and Network-tab-level
visual confirmation that a range-control change doesn't trigger a stray request. This is recorded
in the ticket's Implementation Notes as well, per the plan's own instruction not to edit Steps 1-6
to pretend this happened.
