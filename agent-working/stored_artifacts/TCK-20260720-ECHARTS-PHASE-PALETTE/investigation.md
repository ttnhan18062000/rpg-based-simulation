---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260720-ECHARTS-PHASE-PALETTE
artifact_type: investigation
tags: [dashboard, observability]
---

# Investigation — TCK-20260720-ECHARTS-PHASE-PALETTE

## Current Behavior

**`dashboard-frontend/src/lib/chartPalette.ts`** (full file, 14 lines) — the only file in
`dashboard-frontend/src/lib/`, so this ticket's new module is the second file that directory
will ever contain:

```ts
export const CHART_SERIES_1 = '#3987e5' // blue
export const CHART_SERIES_2 = '#008300' // green
```

Its header comment establishes the convention the ticket asks the new module to mirror:
1. States which validator ran (`dataviz` skill's `scripts/validate_palette.js`) and against which
   *actual* app surface — `--color-bg-tertiary: #242835` — not the skill's generic default.
2. Reports the concrete result per constant, including a WARN (`CHART_SERIES_2` sits at 2.97:1,
   just under the 3:1 floor) and its accepted mitigation (always paired with a visible value
   label, never used color-only) — this is the skill's "relief rule" in practice.
3. Records that the app's own `--color-accent-*` tokens were tried first and rejected because
   they fail the lightness-band check on this dark surface, and are kept for other UI roles
   (status text) that the validator doesn't cover.

This is a 2-series palette only — `chartPalette.ts` has never had to solve the "how many hues"
problem this ticket raises. Both slots are the dataviz skill's own default dark categorical
slots 1 and 6 (see `palette.md`), used verbatim.

**Consumers of `chartPalette.ts` today:**
- `dashboard-frontend/src/components/BarChart.tsx:2,28` — imports `CHART_SERIES_1` as the
  `color` prop default.
- `dashboard-frontend/src/components/GroupedBarChart.tsx:2,28-29` — imports both constants as
  `series1Color`/`series2Color` prop defaults.
- `dashboard-frontend/src/components/GanttBar.tsx` — **does NOT import `chartPalette.ts` at
  all.** It colors its three-way status bucket (`done`/`failed`/`neutral`) via Tailwind utility
  classes (`bg-accent-green`, `bg-accent-red`, `bg-text-secondary`, `STATUS_BUCKET_COLOR_CLASS`
  at L24-28) plus a CSS pattern class (`gantt-bar--inferred-pattern`) for the "estimated/live"
  state. This is a real gap against the ticket's Related Code Areas framing ("how it currently
  references chartPalette.ts, since the new palette module should follow the same integration
  pattern") — GanttBar has no such pattern to follow; it solves a different, 3-bucket status
  problem, not a per-series-identity color problem. The two components whose convention *is*
  directly relevant are `BarChart.tsx`/`GroupedBarChart.tsx` (both take the color as a prop with
  a `chartPalette.ts` constant as the default, imported as a plain named export).

**`tools/agent-monitoring/vocabulary.py`** (confirmed by direct read, not trusted from the
ticket's transcription) — `WORKFLOW_PHASES` is a `dict[str, set[str]]` keyed by workflow name:
- `implement-ticket` (11): Scope, Investigate, Plan, Review, Implement, Architecture-Verify,
  Test, Parity, Security-Review, Verify, Finalize
- `create-tickets` (5): Comprehend, Investigate, Structure, Write, Link
- `implement-epic` (1): Implement
- `simq-audit` (7): Recalibrate, Classify Drift, Update Anchors, Sync Docs, Parity Check,
  Verify, Report

Union across all four sets, deduplicating `Investigate` (implement-ticket ∩ create-tickets),
`Implement` (implement-ticket ∩ implement-epic), and `Verify` (implement-ticket ∩ simq-audit) =
**exactly 21 distinct strings**, matching the ticket's AC #2 literal list verbatim, in this
canonical order derived from a straightforward per-workflow walk:

```
Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity,
Security-Review, Verify, Finalize, Comprehend, Structure, Write, Link, Recalibrate,
Classify Drift, Update Anchors, Sync Docs, Parity Check, Report
```

Confirmed: each is a Python `set` (explicit module docstring at L1-13 warns these are grepped
from real call sites, not copied from stale docs), so no ordering is defined in source — the
ticket's own framing ("must be an explicitly-authored deterministic assignment, not reliant on
Python set iteration order") is correct and matches `is_known_agent`/`infer_workflow`'s existing
defensive style in the same file.

**`dashboard-frontend/package.json`** — no D3/echarts/vis-timeline dependency exists yet
(`dependencies`: 5 Radix packages, `class-variance-authority`, `clsx`, `react`, `react-dom`,
`tailwind-merge`). Confirmed via grep: zero occurrences of `echarts` anywhere in
`dashboard-frontend/src/**/*.{ts,tsx}` or in `package-lock.json`. This ticket is the first to
introduce the dependency — there is no existing tree-shaken-import pattern elsewhere in this
frontend to mirror; the tree-shaken import list (`echarts/core` + `CustomChart`,
`TooltipComponent`, `DataZoomComponent`, `GridComponent`, `CanvasRenderer`) is specified directly
in the ticket/proposal doc, not derived from precedent in this repo.

**No existing test file for `chartPalette.ts`.** `dashboard-frontend/src/test/` has 11 files
(`App`, `StatsView`, `GroupedBarChart`, `GlossaryTooltip`, `RecentActivityGantt`,
`useRunsPolling`, `TicketsView`, `GanttBar`, `ReplayTimelineView`, `BarChart`, `TimeAxis`); none
targets `chartPalette.ts` directly today — its two constants are only exercised indirectly via
`BarChart.test.tsx`/`GroupedBarChart.test.tsx`. The new palette module's test file will be the
first direct test of anything in `src/lib/`.

## Mechanics / Engine Constraints

None — this is dashboard/agent-tooling work (`layer: observability`), entirely outside
`src/`. No Mechanics Bible chapter or engine contract governs it. Confirmed no
`docs/mechanics/`/`docs/engine/` cross-reference is applicable, consistent with every prior
dashboard ticket's `support_boundary` note in `docs/parity_ledger/infrastructure.yaml`
(e.g. INFRA-275: "no simulation behavior is involved").

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`, entry **INFRA-275** (`status: verified`,
`priority: P2`) is the rolling ledger entry that already accumulates every Agent Ops Dashboard
ticket's `v2_evidence`, including the original creation of `chartPalette.ts` under
`TCK-20260718-STATS-TAB-FRONTEND`:

> "`Skill(skill: "dataviz")` was invoked before any chart component code was written; its
> palette-validation step (`scripts/validate_palette.js`) was run against the dashboard's
> actual dark chart surface (`--color-bg-tertiary #242835`, not the skill's generic default) —
> the app's own pre-existing `--color-accent-*` tokens FAILED the lightness-band check against
> that surface and were not reused for chart fills; the skill's validated default dark 8-hue
> categorical set PASSED, with only its first two slots used
> (`dashboard-frontend/src/lib/chartPalette.ts`)."

This is the direct precedent this ticket extends from a 2-slot to a full 21-key mapping still
built from the *same* validated 8-hue dark categorical set — no new palette source, just a
different derivation of how the 8 hues map onto more than 8 identities.

Also relevant, same entry: **INFRA-280** (`status: verified`, `priority: P2`) — the
`GLOSSARY-TOOLTIPS-FRONTEND` ticket that added `BarChart.tsx`/`GroupedBarChart.tsx`'s optional
`descriptions` prop, and explicitly recorded *why* it did **not** wire glossary tooltips into
`GanttBar.tsx`: "GanttBar renders only `run.run_id` as text, never a raw status string... no 1:1
mapping exists." This corroborates the finding above that `GanttBar.tsx` is architecturally
outside the `chartPalette.ts` convention family.

No P0 entries are touched by this ticket — both relevant entries are P2, and neither carries a
`test_path` that this ticket's change would invalidate (`INFRA-275`'s and `INFRA-280`'s
`v2_evidence`/`test_path` fields reference `BarChart.test.tsx`/`GroupedBarChart.test.tsx` at
their *current* content; this ticket does not modify those files, only adds a sibling module, so
their existing assertions stay valid unless a future ticket wires the new palette into them).

No new parity ledger entry is strictly required by CLAUDE.md's rule ("when a behavior changes,
find the relevant entry and update status/v2_evidence") since this ticket adds new capability
rather than changing verified behavior — but per the established pattern (every prior dashboard
ticket appends its own v2_evidence paragraph to INFRA-275), Finalize should append a paragraph to
INFRA-275 documenting the new module, mirroring the STATS-TAB-FRONTEND precedent's own
palette-validation writeup style.

## Prior Work

- **`TCK-20260718-STATS-TAB-FRONTEND`** (`tickets/done/`, artifacts in `stored_artifacts/`) —
  direct precedent: created `chartPalette.ts`, ran the dataviz skill's validator against this
  app's real dark surface for the first time, and made the explicit call that the app's
  `--color-accent-*` tokens are unusable for chart fills.
- **`TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND`** — added the `descriptions` prop pattern to
  `BarChart`/`GroupedBarChart` and the glossary category `phase` with all 21 phase descriptions
  already authored (`GET /api/glossary`, `category="phase"`) — the proposal doc explicitly notes
  these should be reused for phase tooltip/legend copy in the future `ProgressTimelineView` work,
  not re-authored. Not this ticket's job (rendering is out of scope), but relevant so the new
  palette module's header comment/tests don't duplicate description text that already exists
  server-side.
- **`docs/plans/agent_ops_dashboard/proposal_progress_timeline.md`** — the source proposal this
  ticket was carved out of (Concern 2 of 5). Confirms: (a) the three-way library evaluation
  that led to Apache ECharts, rejecting `timelines-chart` and `react-calendar-timeline` on
  maintenance grounds; (b) the exact tree-shaken import list this ticket must use; (c) that this
  ticket is a stated hard prerequisite for Concern 3 (`ProgressTimelineView.tsx`), which will
  retire `GanttBar.tsx`/`TimeAxis.tsx`/`Legend.tsx` entirely — reinforcing that no *rendering*
  integration should be attempted here, since the very component this palette would render into
  doesn't exist yet and today's `GanttBar` isn't shaped to consume it.
- No `docs/REGISTRY.yaml` entry exists yet for a ticket with `chartPalette`, `echarts`, or
  `palette` in scope beyond the two above (checked via direct grep of the regenerated registry).

## Risks and Open Questions

1. **RESOLVED by user, 2026-07-30** (do not re-litigate): 21 fully-distinct generated hues
   conflicts with the dataviz skill's non-negotiable categorical cap. Confirmed the exact rule
   text in the skill's own files: `references/anti-patterns.md:21` — "❌ Cycling / generating
   hues past 8. A 9th categorical color, generated or reused." and
   `references/choosing-a-form.md:54` — "Never solve 'too many series' by generating more
   hues." Resolution: cluster the 21 phases into 8 hue families (Section "Anti-Drift Hazards"
   below has the concrete assignment) using the skill's own documented 8-slot dark categorical
   set, varying **lightness** within a family as the primary always-on distinguisher.

2. **Pattern/texture is not a free second channel for default rendering.** The skill's own
   `color-formula.md` (§ "Texture fill") states the "Lines" texture fill is "triggered by the
   accessibility setting, print, or `forced-colors` — never decorative, never on by default."
   The ticket's Assumptions/Open Questions section paraphrases the user's resolution as
   "lightness/pattern variation within each family" — read literally, *pattern* cannot be the
   default within-family distinguisher without contradicting the skill's own rule that texture
   is an opt-in a11y channel, not baseline encoding. **Recommendation for Plan:** treat lightness
   step as the sole default-rendering distinguisher within a family (it is measurable,
   `validate_palette.js`'s ordinal path already checks `ORDINAL_MIN_DL = 0.06`), and treat the
   Lines texture as available-but-optional for the future `forced-colors`/print path, consistent
   with the skill's rule — not a contradiction of the user's decision, since the AC only requires
   the *color* mapping's key set and contrast, not that pattern is rendered by default (rendering
   itself is explicitly out of scope for this ticket).

3. **Per-color contrast risk from stepping lightness within a family.** The dark categorical
   band `validate_palette.js` enforces is narrow: OKLCH L ≈ 0.48–0.67 (`BAND.dark` at
   `validate_palette.js:34`). Fitting 2-3 members' lightness steps inside that band while each
   individually clears the ≥3:1 contrast-vs-`#242835` floor (AC #3, same floor `chartPalette.ts`
   already applies) is not guaranteed to pass cleanly for every family — `chartPalette.ts`'s own
   header comment already documents one WARN-band constant (`CHART_SERIES_2` at 2.97:1) mitigated
   by a mandatory visible-label pairing. **Open question for Plan, not assumed:** every one of
   the ~21 generated hex values must actually be run through
   `dataviz/scripts/validate_palette.js` (or its `.py` twin) against `--surface "#242835"
   --mode dark`, and any WARN-band result needs the same "always paired with a visible label"
   mitigation `chartPalette.ts` already established — this cannot be verified by inspection
   alone and must happen during Implement, not assumed to pass from the family design alone.

4. **`npm install echarts echarts-for-react` requires network access.** Not verified in this
   investigation (out of scope to attempt an actual install); if the implementation sandbox has
   no registry access, `package-lock.json` regeneration will need to happen in an environment
   that does, or via a pre-vendored approach. Flagging as a blocking risk for Implement to check
   early, not assumed resolved.

5. **No cross-language sync guard exists or is being added** (explicitly out of scope per the
   ticket) — confirmed no mechanism currently keeps a TS phase list in sync with
   `vocabulary.py`'s `WORKFLOW_PHASES` short of the completeness test this ticket adds. If a 5th
   workflow or new phase string is ever added to `vocabulary.py`, the TS module will silently
   miss it until the completeness test's literal list is manually updated. This is an accepted,
   already-approved tradeoff (ticket's own Out of Scope), not a new risk this investigation is
   raising — restated here only so Plan doesn't rediscover it as a surprise.

## Anti-Drift Hazards

- **Do not wire the new palette module into `GanttBar.tsx`, `BarChart.tsx`, or
  `GroupedBarChart.tsx` rendering.** Confirmed out of scope by the ticket text ("No visible UI
  change or chart rendering"); `GanttBar.tsx` in particular has no existing integration point to
  extend (see Current Behavior) — adding one here would be scope creep into the future
  `ProgressTimelineView` ticket's job.
- **Do not touch `tools/agent-monitoring/vocabulary.py`** — explicitly out of scope; the 21-item
  TS list must be hand-copied, verified against source (as this investigation did), not imported
  or generated from Python at build time.
- **Do not build a cross-language sync guard** (e.g. a script that imports `vocabulary.py` and
  cross-checks the TS file at CI time) — explicitly rejected in Out of Scope; a completeness test
  with the literal list is the accepted mechanism.
- **Do not import the full `echarts` bundle anywhere**, even transitively through a convenience
  re-export — the AC requires zero occurrences of a bare `'echarts'` import anywhere in
  `dashboard-frontend/src`; only `echarts/core` plus the five named submodule imports are
  allowed. `dashboard-frontend/src/components/GanttBar.tsx`'s sibling, the future
  `ProgressTimelineView.tsx`, is not part of this ticket — do not add ECharts *usage* code here,
  only the dependency and the color module.
- **Concrete 8-family hue clustering recommendation** (for Plan to formalize), built from the
  dataviz skill's own validated dark categorical set (`palette.md`, dark column) rather than any
  new hue, using the user's own "stage of pipeline" framing extended to all 21 phases:

  | Family | Hue (dark hex) | Phases (member count) | Semantic grouping |
  |---|---|---|---|
  | 1 | blue `#3987e5` | Scope, Comprehend, Recalibrate (3) | workflow intake / problem framing |
  | 2 | aqua `#199e70` | Investigate, Structure (2) | research / organizing understanding |
  | 3 | violet `#9085e9` | Plan, Write, Link (3) | design / authoring output |
  | 4 | green `#008300` | Implement, Sync Docs (2) | building / producing the change |
  | 5 | orange `#d95926` | Review, Architecture-Verify, Classify Drift (3) | pre/post-change structural check |
  | 6 | yellow `#c98500` | Test, Parity, Parity Check (3) | correctness/consistency validation |
  | 7 | magenta `#d55181` | Security-Review, Update Anchors (2) | guard / integrity gates |
  | 8 | red `#e66767` | Verify, Finalize, Report (3) | closing / done-state gates |

  Totals to exactly 21 (3+2+3+2+3+3+2+3). Within each family, step OKLCH lightness by ≥0.06 per
  member (matching `validate_palette.js`'s own `ORDINAL_MIN_DL` threshold) staying inside the
  dark band (L 0.48–0.67), holding the family's hue/chroma constant — e.g. family 1's three
  members would occupy roughly the light/mid/dark thirds of that band rather than three
  arbitrary blues. This is a recommendation, not a final assignment — Plan should treat the
  family membership as fixed (it satisfies AC #2's key-set requirement regardless of internal
  lightness choices) but the exact hex-per-member still needs to be derived and run through the
  validator per Risk 3 above before being hardcoded.
- **Header comment convention must be mirrored, not abbreviated.** `chartPalette.ts`'s comment
  names the exact surface hex tested, states the validator script used, and records any WARN with
  its mitigation. A 21-entry table has more surface area for this to be skipped or summarized
  away — the AC explicitly requires it ("documented in the module's header comment mirroring
  chartPalette.ts's existing comment convention").
