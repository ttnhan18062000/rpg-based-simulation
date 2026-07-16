# UI Interaction Spec — view-by-view UX detail

**Status:** technical design detail, not yet implemented — companion to `PROPOSAL.md` §5, §7
**Scope:** concrete columns/filters/interactions for each view named in `PROPOSAL.md`. Written to be
stack-agnostic (`PROPOSAL.md` §5a's three-way stack decision is still open) — noted explicitly
wherever a detail depends on which option is chosen.
**Date:** 2026-07-16

---

## 1. Tickets view

**Layout:** a single sortable/filterable table, not a board/kanban — this repo's ticket model has
three lifecycle directories (`inprogress`/`done`/`todos`), not a small fixed set of columns a
kanban board suits well, and `PROPOSAL.md` §3 already chose "filterable table" over any richer
layout.

**Columns** (left to right): `Ticket ID` (monospace, matches `src/api/server.py`'s existing
`.run-card-id` styling convention if the vanilla-HTML stack option is chosen — `PROPOSAL.md` §5a) ·
`Title` (truncated, full text on hover) · `Tier` · `Type` · `Priority` (color-coded: P0 red, P1
amber, P2 default) · `Layer` · `Status` (workflow status badge — `OPEN`/`INPROGRESS`/`BLOCKED`/
`DONE`, per `DATA_MODEL.md` §1's `workflow_status` field, not the frontmatter `status` field) ·
`Tags` (pill list, max 3 shown + "+N more") · `Date` · a trailing link icon, shown only when
`run_id_match` is non-null (`DATA_MODEL.md` §1).

**Filters** (a filter bar above the table, mirroring `src/api/server.py`'s `.filter-bar`/
`.filter-pill` pattern already proven in this codebase): multi-select pills for `Tier`, `Layer`,
`Priority`, `Tag`; a `Status` dropdown (`OPEN`/`INPROGRESS`/`BLOCKED`/`DONE`/all); a `Lifecycle`
toggle (`In Progress` / `Done` / `Todo` / `All`, default `All`); a free-text search box matching
`q` against title + ticket ID.

**Sort:** `Date` descending by default (newest first), toggleable to ascending. No other sort
columns for v1 — this is a filterable log, not a spreadsheet; if more sort dimensions are wanted
later, `docs/guides/ticket_reporting.md`'s deferred "velocity/throughput" pillar (`PROPOSAL.md` §2)
is the more natural home for aggregate/sorted views, not this table.

**Row click:** if `run_id_match` is set, navigate to that run's Replay timeline (§3). If not (a
ticket with no matching agent-monitoring run — plausible for very old or manually-created tickets),
expand the row in place to show the ticket file's raw body text, read-only.

**Empty state:** "No tickets match these filters" if filters exclude everything; "No tickets found"
(distinct copy) if the repo genuinely has zero ticket files — this distinction matters the same way
`epic_staleness_check.py`'s stale-vs-never-started distinction matters (`docs/guides/
agent_monitoring.md`) — don't collapse two different "nothing to show" reasons into one message.

---

## 2. Recent Activity view (cross-run Gantt — the default landing page)

**Time window selector:** pills for `Last 24h` / `Last 7d` / `Custom range` (date pickers), default
`Last 24h`. Backs the `/api/runs?since=...` query param (`DATA_MODEL.md` §1).

**Row layout:** one row per `run_id`, grouped by nothing by default (chronological by `start_ts`/
`inferred_start_ts` descending — most recent activity at top). If the window contains enough
concurrent runs that rows would visually overlap in time, stack them into additional rows rather
than compressing the time axis — horizontal position must stay a true time axis, never rescaled per
row, or the Gantt loses its core "when did this actually happen" value.

**Bar rendering:**
- Completed run: solid bar, left edge `start_ts`, right edge `end_ts`, fill color by
  `final_status` (`DONE` green, any `*_BLOCKED`/`*_FAILED`/`CONFLICTS_DETECTED` red, `EPIC_SCOPED`/
  `NOTHING_TO_CREATE` neutral gray — mirroring `PROPOSAL.md` §7's status vocabulary from
  `schema.md`).
- Inferred-active run (`is_inferred_active: true`, `DATA_MODEL.md` §1): striped/animated fill,
  left edge `inferred_start_ts` (explicitly softer-edged or annotated "~" to signal it's an
  estimate — never rendered identically to an authoritative `start_ts`), right edge pinned to "now"
  and advancing.
- A small legend (fixed, not per-row) explaining the color/pattern coding once, not repeated on
  every row — matches `src/api/server.py`'s existing category/severity legend convention.

**Hover tooltip:** `run_id`, `tier`, `workflow`, duration so far (or final `duration_s`),
`agent_count`. No tool-level detail in the tooltip — that's what clicking through to the Replay
timeline is for.

**Click:** navigate to that run's Replay timeline (§3).

**Settle transition** (`PROPOSAL.md` §7b): when a bar's underlying run flips from inferred-active
to completed between polls, animate the fill from striped to solid and snap the left edge from
`inferred_start_ts` to the now-available authoritative `start_ts` — a brief (≤300ms) transition, not
an instant cut, so the correction is visible rather than a silent jump a user might read as a bug.

---

## 3. Run Detail / Replay timeline

The centerpiece view (`PROPOSAL.md` §7b). Two zones: a horizontal phase timeline (top), and a
tool-call/replay detail area (below) that responds to scrubbing the timeline above it.

### 3a. Phase timeline (top zone)

One segment per `TimelineEntry` (`DATA_MODEL.md` §1), left to right in `seq` order, segment width
proportional to that phase's duration (derived from consecutive `ts` deltas, per `PROPOSAL.md`
§7b). Each segment shows: phase label (`Investigate`, `Plan`, etc.), agent name (smaller, below the
phase label), a status icon (`ok` check, `failed` X, `blocked` stop, `skipped` dash — matching
`schema.md`'s `status` vocabulary), and a small `cost_proxy_score` badge if non-zero.

**Live edge** (only when `RunTimeline.is_live` is `true`, `DATA_MODEL.md` §1): appended after the
last known segment, a visually distinct "LIVE" segment rendering `live_tail`'s raw tool calls as
unlabeled ticks (no phase/agent name — `phase`/`agent` are `null` here until
`MONITORING_INSTRUMENTATION_GAP.md`'s fix lands, and the UI must show this honestly, e.g. a
"(phase unknown — run still in progress)" caption, never a guessed label). A pulsing indicator
(reusing `src/api/server.py`'s `.logo-dot`/`pulse` keyframe pattern if the vanilla-HTML stack option
is chosen) marks this segment as actively growing.

### 3b. Playback / scrub control

A scrubber below the phase timeline, draggable, plus play/pause and a speed selector (`1x` / `5x`
/ `20x`). Scrubbing or playing moves a cursor across the phase timeline; the detail area (3c) shows
whatever tool calls fall at or before the cursor's current position, revealed progressively during
playback rather than all at once — this is what makes it a *replay*, not just a static list
(`PROPOSAL.md` §7b's explicit distinction). Playback never fetches new data — it replays the
already-fetched `RunTimeline` payload client-side; polling for genuinely new data (the live edge,
§3a) is a separate, independent refresh cycle.

### 3c. Detail area (below the scrubber)

For the phase/tool-call range currently exposed by the scrubber position: a chronological list of
tool calls (`tool`, `input_summary`, `duration_ms`, `status`), each with a "View Details JSON"
toggle — directly reusing `src/api/server.py`'s `loadEntityTimeline()`/`toggleDetails()` pattern
(`PROPOSAL.md` §5a), which already solves "show a compact summary line, reveal the full raw record
on demand" for structurally the same kind of data.

### 3d. Files-touched panel (side panel, always visible, not scrubber-gated)

Renders `RunTimeline.files_touched` (`DATA_MODEL.md` §1) grouped by tool kind (`Read` / `Edit` /
`Write` / `MultiEdit`), each entry showing the file path and first-touched timestamp. Not
scrubber-gated (unlike 3c) — it's a whole-run summary, not a moment-in-time view, so it stays static
regardless of scrub position. Read-only: paths are not clickable (no file-browsing capability in
this dashboard, matching `PROPOSAL.md` §10's write-back-free scope).

---

## 4. Cross-cutting interaction notes

- **Stale-data banner** (`PROPOSAL.md` §6): a persistent, dismissible-but-reappearing banner at the
  top of every view when the most recent poll failed — states "Showing data as of `HH:MM:SS` —
  connection to dashboard server lost" rather than silently freezing.
- **Loading state:** a skeleton/placeholder matching each view's real layout (not a generic
  spinner) on first load only — subsequent polls update in place without a loading flash, since
  `PROPOSAL.md` §3's mtime-cache design means most polls return instantly from memory.
- **Empty states:** distinct copy per view for "no data yet" (a fresh repo/experiment with no
  ticket or monitoring history at all) vs. "no data matches your filters" — same principle as §1's
  Tickets view empty-state distinction, applied consistently across all three views.

---

## Related

- `PROPOSAL.md` §5, §5a, §7b — the view definitions and stack-option context this document assumes
- `DATA_MODEL.md` §1 — every field referenced here (`is_inferred_active`, `files_touched`, `live_tail`, etc.) is defined there
- `src/api/server.py` — `loadEntityTimeline()`/`toggleDetails()` (§3c), `.filter-bar`/`.filter-pill` (§1), `.logo-dot`/pulse keyframe (§3a) — the reusable UI patterns cited throughout
- `TEST_PLAN.md` — frontend test cases exercise the interactions specified here
