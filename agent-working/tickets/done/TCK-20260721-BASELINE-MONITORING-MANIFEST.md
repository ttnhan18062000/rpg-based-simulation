---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260721-BASELINE-MONITORING-MANIFEST
phase: done
date: 2026-07-21
tags: []
---

# TCK-20260721-BASELINE-MONITORING-MANIFEST

## Title
Baseline monitoring manifest and legacy compatibility fixtures

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Before touching any monitoring writer or reader, capture a read-only baseline inventory of every agent-monitoring JSONL file (counts, byte sizes, SHA-256 hashes, parser/validator results, legacy-warning counts) and build a fixture corpus covering every known historical schema generation, so later migrations can prove nothing was rewritten, reordered, or lost. This matters because the epic's Phase 0 exit criteria requires a reproducible baseline manifest and passing legacy parser fixtures before any writer or .codex/ hook is touched, and the existing agent-monitoring/*.jsonl corpus is immutable historical input that must never be rewritten, reordered, or deleted.

## Scope
- Build a read-only baseline manifest tool that inventories every agent-monitoring/*.jsonl file (runs.jsonl, events.jsonl, tools.jsonl): line count, byte size, SHA-256 hash, parser/validator result, legacy-warning count, one record per file, reproducible on re-run
- Build a fixture corpus under tests/fixtures/ covering all 6 documented legacy shapes (5 runs.jsonl generations + the TCK-20260623-TYPE-CHECKER exception, plus tools.jsonl/events.jsonl null-gap variants) per docs/agent-monitoring/schema.md
- Add a legacy-reader test asserting correct parse and provenance classification for each fixture shape
- Reuse validate.py's load_jsonl and the SHA-256 snapshot pattern from tests/agent_replay/test_no_mutation_snapshot.py

## Out of Scope
- No changes to any monitoring writer (post_tool_hook.py, record_run.py, record_events.py) — this ticket is read-only inventory/fixtures only
- No historical JSONL remediation, rewriting, reordering, or backfilling
- No live .codex/ hook wiring
- Does not implement the shared writer module (owned by the monitoring-writer-unification ticket)

## Acceptance Criteria
- [x] Manifest tool produces one record per JSONL file in agent-monitoring/ (line count, byte size, SHA-256 hash, parser result, legacy-warning count)
- [x] Running the manifest tool twice against unchanged input produces byte-identical output (reproducibility)
- [x] Manifest tool run causes zero git diff on agent-monitoring/*.jsonl (read-only proof, verified via hash comparison before and after)
- [x] Fixture corpus contains one fixture per documented legacy shape (5 runs.jsonl generations + TCK-20260623-TYPE-CHECKER exception + tools.jsonl/events.jsonl null-gap variants) as enumerated in docs/agent-monitoring/schema.md
- [x] A legacy-reader test asserts each fixture parses correctly and is classified with correct provenance (schema-generation label)
- [x] Current Claude-written monitoring records remain readable (round-trip parse test) before and after the new reader is introduced
- [x] Manifest tool avoids a full in-memory parse of tools.jsonl (~18MB) — parses in a streaming/bounded manner (verified by code review or a memory-bound test)

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
- TCK-20260705-MONITORING-RUNID-JOIN
- TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/agent-monitoring/schema.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/replay_fixture_spec.md
- tools/agent-monitoring/validate.py
- agent-monitoring/runs.jsonl
- agent-monitoring/events.jsonl
- agent-monitoring/tools.jsonl
- tests/agent_replay/test_no_mutation_snapshot.py
- tests/tools/test_validate_agent_monitoring.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py

## Assumptions / Open Questions
- Assumes this ticket is Proposed Ticket Group #1 of the already-scoped epic, not duplicate work
- Assumes no tests/fixtures/ directory for legacy shapes exists yet (confirmed genuinely new work)
- Assumes tools.jsonl size (~18MB) requires a streaming/bounded manifest approach rather than full in-memory parse-repeat; exact technique left to this ticket's Plan phase

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260721-BASELINE-MONITORING-MANIFEST/plan.md`'s 7 ordered
steps, no deviations.

1. **`tools/agent-monitoring/legacy_reader.py`** — new module, `classify_provenance(record, source)`
   pure function (no I/O). Imports `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES`
   read-only from `validate.py` (never modified). `_classify_runs` checks the `TCK-20260623-TYPE-CHECKER`
   shape (shape 6) first per the plan's Anti-Drift Notes, since its signature is the most narrowly
   identifiable; `_classify_tools` and `_classify_events` implement the remaining rules exactly as
   specified in plan.md Step 1. Added a module-level assertion tying the runs-shape rules' literal
   field names to `LEGACY_COMPLETION_FIELDS` so the two stay single-sourced, since the classify
   rules themselves are written against literal keys (matching schema.md's shape descriptions)
   rather than iterating the tuple directly.
2. **`tests/fixtures/agent_monitoring/`** — 8 new fixture `.jsonl` files (10 total files since the
   two `events_jsonl_*` fixtures intentionally hold the same verbatim real line, per plan.md), each
   extracted byte-for-byte via `sed -n '<line>p' <source> > <fixture>` from the exact real-corpus
   locations investigation.md identified (verified: `shape5_folder_epic_bare_status.jsonl` has no
   `final_status` key, confirming it is one of the 7 true-legacy records, not one of the 65
   current-schema `FOLDER-*` records). `PROVENANCE.md` documents every fixture's source file:line.
3. **`tests/tools/test_agent_monitoring_legacy_reader.py`** — Section 1 (17 inline-dict unit tests,
   one per classification rule plus edge cases), Section 2 (10 fixture-backed parametrized cases +
   the shape-5 population guard + the interactive_null exclusion-from-warnings guard).
4. Same file, Section 3 — round-trip test sampling the most recent 20 real `runs.jsonl`/
   `events.jsonl` records, asserting `classify_provenance` returns `frozenset()` for recent runs and
   agrees with `validate.py`'s own `_record_is_complete`.
5. **`tools/agent-monitoring/manifest.py`** — new module. `_scan_file` opens each file in binary
   mode once, iterates `for line_bytes in f` (line-lazy), updates a running `hashlib.sha256()` per
   line, and classifies each parseable line via `legacy_reader.classify_provenance`.
   `build_manifest()` scans all 3 files in sorted-filename order. `main()` is a CLI printing
   `json.dumps(records, indent=2, sort_keys=True) + "\n"` to stdout by default, with an optional
   `--output PATH` guarded by `_assert_safe_output_path()` which raises `ValueError` if `PATH`
   resolves under the real `agent-monitoring/` directory (manually verified: rejects
   `agent-monitoring/manifest_test.json`, accepts `/tmp/manifest_out.json`). Streamed SHA-256 was
   verified to exactly match a full-file `hashlib.sha256(path.read_bytes())` hash for `runs.jsonl`.
6. **`tests/tools/test_agent_monitoring_manifest.py`** — shape test (3 records, 6 keys each, correct
   types, `line_count == parsed_ok + parse_errors`), reproducibility test (both a `subprocess`
   double-CLI-run byte comparison and a direct double `build_manifest()` call comparison), and an
   `ast`-based static guard asserting `manifest.py`'s source contains no `.read_text()`/
   `.read_bytes()`/`.readlines()`/`.read()` attribute call.
7. Same file — zero-mutation integration test against the real `agent-monitoring/` directory
   (dirty-tree-aware two-branch design mirroring `test_no_mutation_snapshot.py`: porcelain-clean
   branch asserts still-clean after, dirty branch falls back to a SHA-256 content-hash comparison of
   the 3 real JSONL files before/after `build_manifest()`), plus a writer-byte-identity guard
   (`git diff --stat HEAD` scoped to `validate.py`/`record_run.py`/`record_events.py`/
   `post_tool_hook.py` under `tools/agent-monitoring/`, asserting empty output).

No deviations from plan.md. `agent-monitoring/tools.jsonl` shows as modified in `git status` during
this session — that is the Claude Code harness's own `PostToolUse` hook appending rows for this
session's tool calls (ambient, unrelated to this ticket's code), not a write performed by any file
this ticket added; the zero-mutation test's dirty-tree fallback branch handles exactly this case by
content-hashing immediately before/after `build_manifest()` runs, independent of ambient session
activity.

## Test Summary

- `pytest tests/tools/test_agent_monitoring_legacy_reader.py -v` — 31 passed (17 inline-dict +
  10 fixture-backed parametrized + shape-5 guard + interactive_null guard + 2 round-trip tests).
- `pytest tests/tools/test_agent_monitoring_manifest.py -v` — 6 passed (shape, 2 reproducibility
  variants, AST streaming guard, zero-mutation integration, writer byte-identity guard).
- `pytest tests/tools/test_validate_agent_monitoring.py -q` — 13 passed, unmodified (regression
  surface check per plan.md Step 1's Verify note).
- `pytest tests/tools/test_record_run.py tests/tools/test_record_events.py
  tests/tools/test_post_tool_hook.py -q` — all pass, confirming the untouched writers still behave
  identically.
- Manual CLI run: `python3 tools/agent-monitoring/manifest.py` against the real repo prints a
  3-record JSON array with no traceback; streamed SHA-256 independently verified to match a
  full-file hash.

## Files Changed

- `tools/agent-monitoring/legacy_reader.py` (new)
- `tools/agent-monitoring/manifest.py` (new)
- `tests/fixtures/agent_monitoring/` (new directory: 10 `.jsonl` fixture files + `PROVENANCE.md`)
- `tests/tools/test_agent_monitoring_legacy_reader.py` (new)
- `tests/tools/test_agent_monitoring_manifest.py` (new)

## Completion Summary

Built a read-only baseline manifest tool (`manifest.py`) and a provenance classifier
(`legacy_reader.py`) under `tools/agent-monitoring/`, backed by a verbatim-real-data fixture corpus
covering all 6 documented `runs.jsonl` legacy shapes plus the `tools.jsonl`/`events.jsonl` null-gap
variants. The manifest streams all 3 `agent-monitoring/*.jsonl` files in a single line-lazy pass
(never a full in-memory read), producing a deterministic, byte-identical-on-rerun JSON inventory
(line count, byte size, SHA-256, parser result, legacy-warning count) with zero mutation of the real
corpus, proven by a content-hash-based integration test run against the live directory. No monitoring
writer (`validate.py`, `record_run.py`, `record_events.py`, `post_tool_hook.py`) was modified — all
7 acceptance criteria are met and all 50 new/regression tests pass.
