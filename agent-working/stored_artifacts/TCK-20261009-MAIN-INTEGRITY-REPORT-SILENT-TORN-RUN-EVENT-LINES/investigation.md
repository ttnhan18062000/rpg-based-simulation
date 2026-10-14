---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES
artifact_type: investigation
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20261009-MAIN-INTEGRITY-REPORT-SILENT-TORN-RUN-EVENT-LINES

Context search: `search_docs` returned only closed integrity-report tickets (no open duplicate); the graphify graph file is missing in this worktree, so code structure came from direct reads.

## Current Behavior
- `tools/agent-monitoring/main_integrity_report.py:173-183` `_load_rows(reader, kind)`: iterates `sorted(reader.paths)`, regex-matches `data/<week>/[<batch>.]{runs|events}.jsonl`, and for each non-blank line does `rows.append(json.loads(line))` with `except ValueError: pass`. A torn line vanishes with no trace. It also appends ANY parsed value, so a line that parses to a list/str/number (e.g. `[1, 2]`) is appended as a "row".
- `:186-188` `check_duplicate_runs` passes `_load_rows(reader, "runs")` to `duplicate_run_record_check.check_duplicate_run_records` (tools/gate_checks/) and returns the `evidence` of non-PASS results.
- `:191-196` `check_event_seq` passes `_load_rows(reader, "events")` to `find_seq_duplicates_and_gaps`, which does `e.get("run_id")` (event_seq_integrity_check.py:54-56). A non-dict row therefore raises AttributeError today, so AC4 (non-dict skipped, no crash) is a real behavior change for events, not just a no-op. `classify_duplicate_groups(runs)` very likely also assumes dicts (to confirm at implement time).
- Sibling pattern to copy: `check_working_log` `:108-120` emits `f"{p}:{lineno}: invalid JSON, skipped"` (1-based `enumerate(..., 1)`, blank lines skipped but still counted in lineno), and silently skips non-dict values.
- `build_report` `:207-208` calls both checks; `render` prints findings per check. `_load_rows` has no other caller (grep: only the two checks above).

## Mechanics / Engine Constraints
None from `docs/mechanics/` or `docs/engine/`: this is a report-only tooling change with no simulation law involved. Relevant project rules: report-only (exit 0 unless `--strict`), reads a git ref only (never working tree), deterministic sorted-path ordering must be kept.

## Docs Requiring Update
- `docs/agent-monitoring/README.md`: the "Main-branch integrity report" paragraph (line ~280) lists what the report covers; add that torn lines in runs/events shards are named under the duplicate-runs / event-seq checks instead of being dropped. The ticket says "update only if a doc describes the report's findings"; it does.

The module docstring of `main_integrity_report.py` (check list, lines 12-24) should also be adjusted in code; it is not under `docs/`.

## Parity Ledger Overlap
None. `grep` of `docs/parity_ledger/` finds no entry on the integrity report or monitoring tooling; no P0 implications.

## Prior Work
- TCK-20261008-MAIN-INTEGRITY-REPORT-TORN-WORKING-LOG-LINE: the identical fix in `check_working_log` (pattern and test `test_a_torn_working_log_shard_line_is_reported_and_the_rows_around_it_still_count`, test file lines 210-222).
- TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT and TCK-20261001-INTEGRITY-REPORT-EPIC-TIER-FALSE-POSITIVES: origin and tuning of the report.
- TCK-20261008-RECORD-EVENTS-CRASHES-ON-TORN-TOOLS-LINE (#437): same torn-line class elsewhere.

## Risks and Open Questions
- Finding shape: the check functions return `list[str]`; torn-line strings are simply concatenated into that list. For `check_duplicate_runs`, the downstream result is currently at most one FAIL-evidence string, so the torn-line strings go in front of/after it; order should be deterministic (suggest torn lines first, in sorted path/line order).
- Changing `_load_rows` return type to `(rows, torn)` is safe (single caller pair), but a hidden import elsewhere is unverified beyond grep of the repo for `main_integrity_report` (docs, Makefile, tests only).
- Whether non-dict lines should be dropped inside `_load_rows` (needed to avoid the AttributeError crash) is implied by AC4; no decision needed.
- Real main may already contain torn lines, so the report on origin/main will gain new findings after this lands; that is intended and report-only.
- Ticket Assumptions mention the search index/graph were unavailable; not a blocker.

## Anti-Drift Hazards
- Do not touch `check_working_log`, `duplicate_run_record_check`, `event_seq_integrity_check`, or gate wiring (out of scope).
- Do not repair or filter real torn lines on main; do not make the report exit non-zero by default.
- Keep sorted path order and 1-based line numbers counting blank lines (match sibling).
- A torn line must be reported once per load: `_load_rows` must be called once per kind (it is), and the finding must not be duplicated by both checks (runs lines only under duplicate_runs, events lines only under event_seq).
- Do not let the new strings break `render`/`--json` output shape (`findings` stays dict of `list[str]`).
