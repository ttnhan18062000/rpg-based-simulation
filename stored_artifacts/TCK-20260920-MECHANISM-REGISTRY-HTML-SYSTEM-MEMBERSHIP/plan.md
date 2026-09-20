---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP
phase: done
date: 2026-09-20
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260920-MECHANISM-REGISTRY-HTML-SYSTEM-MEMBERSHIP

## Approach

Pure rendering addition to `generate_mechanism_registry_html.py`. No new data model, no new
computation — everything the page needs (`systems` field per mechanism, `build_system_rollup()`)
already exists from prior tickets in this same epic.

1. **Per-row systems**: build a plain dict `{mechanism_id: systems_list}` straight from
   `data.get("mechanisms")` inside `render()` — a lookup, not a second registry read. Add a
   "Systems" `<td>` with pill-badge spans, and a `data-systems="..."` attribute on the `<tr>` for
   the filter script to key off (comma-joined system names, or the literal string `"unassigned"`).

2. **Rollup section**: call `build_system_rollup(data)` once, reuse its dict verbatim. Write
   `_pct()`/`_pt_delta()`/`_STATE_ORDER`/`_rollup_row_html()` helpers mirroring
   `generate_mechanism_system_rollup_view.py`'s own row-formatting logic exactly, so the two views
   can never independently disagree in shape (only in file format, md vs html). Append `unassigned`
   as its own explicit row, never conditionally omitted.

3. **Filter control**: a `<select id="system-filter">` with `All systems` + each real system name
   (sorted) + `unassigned`. Vanilla JS `change` listener toggles an `is-hidden` class on
   `tr[data-systems]` rows whose `data-systems` doesn't include the chosen value. No new JS
   dependency — this page already ships zero JS before this ticket, so the new `<script>` block is
   additive, not a new build step.

4. **`--check` wiring**: add `mechanism-registry-html-check` to the Makefile wrapping the
   generator's pre-existing `--check` flag (no script change needed — it already worked, just
   wasn't callable via `make`). Add it to `.github/workflows/test.yml`'s existing "Mechanism
   registry checks (blocking)" step, as the 5th check alongside the 4 already wired by
   `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING`.

5. **Verify the blocking check for real**: deliberately break a mechanism's state without
   regenerating the HTML, run the new Make target, capture and confirm a real non-zero exit code,
   then restore and confirm zero diff — same discipline the CI-wiring ticket already established
   for its own 4 checks.

## Test plan (see test_plan.md)

Extend `tests/unit/tools/test_mechanism_registry_html.py` in place — same file, same fixture
(`registry_data`, module-scoped, loads the real `registries/mechanisms.yaml`). New tests cover
each Acceptance Criterion directly; the one pre-existing test broken by the new rollup table's own
`<tr>` elements (`test_render_is_not_truncated`) gets narrowed to count only `<tr data-systems=`
rows, which the rollup table's own rows never carry.

## Scope guards

- Do not touch `registries/mechanisms.yaml`'s schema or any mechanism's `systems`/`state`/
  `verified` fields.
- Do not modify `build_system_rollup()`/`mechanisms_by_system()` — consume unmodified.
- If rendering surfaces something that looks like a data problem (e.g. a mechanism whose systems
  membership looks wrong), report it rather than fixing it inline — out of scope for a rendering
  batch.
