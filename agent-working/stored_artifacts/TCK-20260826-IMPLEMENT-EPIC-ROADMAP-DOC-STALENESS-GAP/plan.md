---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP
artifact_type: plan
tags: [workflows, documentation, process-improvement]
---

# Plan — TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP

## Steps

1. **New module** `tools/gate_checks/epic_tracking_doc_static.py`:
   - `MARKER_BEGIN` / `MARKER_END` constants (the two HTML-comment markers).
   - `parse_tracking_doc_from_sequence(sequence_text: str) -> str | None` — scans lines for a
     `tracking_doc:` prefix (case-sensitive, first match wins), returns the trimmed path or `None`.
   - `render_status_line(done_count, total_count, remaining_count, description, ts) -> str` — the
     exact one-paragraph status text.
   - `update_tracking_doc_status_block(doc_path, *, done_count, total_count, remaining_count,
     description, ts) -> dict` — reads `doc_path`; if either marker missing, returns
     `{"status": "markers_missing", "doc_path": str(doc_path)}` (no write); if file missing, returns
     `{"status": "doc_not_found", "doc_path": str(doc_path)}`; else replaces the exact text between
     the markers (marker lines themselves preserved) with the new status line, writes the file,
     returns `{"status": "updated", "doc_path": str(doc_path), "line": <the new line>}`.

2. **Tests** `tests/tools/test_epic_tracking_doc_static.py`:
   - `parse_tracking_doc_from_sequence`: found (mid-file, first line, trailing whitespace), not
     found (no such line), multiple candidate lines (first wins).
   - `update_tracking_doc_status_block`: markers present → replaced correctly, surrounding content
     byte-identical outside the markers, idempotent on a second call (re-run doesn't duplicate
     anything); markers present but reversed/only one present → `markers_missing`; doc file doesn't
     exist → `doc_not_found`; multi-line prior content between markers is fully replaced by the new
     single line (proves "replace", not "append").

3. **`.claude/workflows/implement-epic.js`** (folder mode only, per Out of Scope):
   - Discover's `folder` branch prompt: after Step 2 (read `SEQUENCE.md`), add Step 2b — run
     `python3 -c "import sys; sys.path.insert(0,'tools'); from gate_checks.epic_tracking_doc_static
     import parse_tracking_doc_from_sequence; print(parse_tracking_doc_from_sequence(open('<seq
     path>').read()) or '')"` against the already-read `SEQUENCE.md` (skip entirely if no
     `SEQUENCE.md` was found in Step 2). Return the result as a new `tracking_doc` field.
   - `DISCOVER_SCHEMA`: add optional `tracking_doc: { type: 'string' }` (empty string when not
     declared or not folder mode).
   - In the Report phase, before the final `return`: if `discovery.mode === 'folder' &&
     discovery.tracking_doc`, spawn one `agent()` call that runs
     `update_tracking_doc_status_block(...)` via `python3 -c` with the real `doneCount`,
     `ticketIds.length`, `remaining.length`, a mode description (`` folder-based batch at
     `${folder}` ``), and a freshly-captured timestamp; capture and log the returned `status`. Add
     the result under a new `tracking_doc_update` key on the workflow's final return value (visible
     to the caller, not silently swallowed either way).
   - This runs on every batch invocation (not gated on `batchStatus === 'DONE'`), matching the
     ticket's own "after each batch run" wording — a partial batch that stops on a gate failure
     still gets its done/remaining counts refreshed.

4. **`.claude/skills/implement-epic/SKILL.md`**: add a `tracking_doc` row to the Input list, a
   `SEQUENCE.md` convention note, and a Phases-table/Notes update describing the Report-phase
   status-block behavior and its explicit no-op-with-warning behavior when markers are declared but
   absent.

5. **Demonstration (AC4)**: the pytest suite in step 2 IS the real, deterministic demonstration —
   exercises the exact Python function the JS workflow calls, against a scratch `SEQUENCE.md` +
   scratch tracking doc with markers, proving the status block updates correctly. Running the full
   `implement-epic.js` orchestrator live is out of this session's own scope (requires the
   user-gated `Workflow` tool) and isn't necessary to satisfy "can be a scratch/test folder, does
   not need to be a live epic."

6. **Follow-up ticket**: file `TCK-20260826-HOTFIX-LIVE-MAP-RECONNECTION-ROADMAP-STALE` (hotfix,
   per Out of Scope) for the genuinely-stale `live_map_scaling_roadmap.md` + `live_map_reconnection_
   epic.md` frontmatter found during investigation — not implemented as part of this ticket.

## Acceptance criteria mapping
- AC1 (disclose other stale docs) → investigation.md's audit; `hud_delivery_roadmap.md` clean,
  `live_map_scaling_roadmap.md` stale (follow-up ticket filed, step 6).
- AC2 (concrete tracking_doc mechanism, explicit no-op when undeclared) → steps 1-3; no `SEQUENCE.md`
  or no `tracking_doc:` line → `parse_tracking_doc_from_sequence` returns `None`/empty string →
  Report's `if` guard is false → no Python call made at all (true no-op, not a call that happens to
  do nothing).
- AC3 (SKILL.md updated) → step 4.
- AC4 (real batch run demonstrates the block updating) → step 2's pytest suite, step 5.
