# Test Plan — fixture matrix and concrete test cases

**Status:** technical design detail, not yet implemented — companion to `PROPOSAL.md` §9
**Scope:** the specific fixtures and test cases `PROPOSAL.md` §9 describes only at the philosophy
level. Written against `DATA_MODEL.md`'s schemas and `UI_INTERACTION_SPEC.md`'s interactions —
cross-referenced, not re-derived.
**Date:** 2026-07-16

---

## 1. Backend fixture matrix

One fixture JSONL line (or small file) per row — covers every schema generation
`docs/agent-monitoring/schema.md`'s "Known Limitations" section documents, so `ingest.py`'s legacy
tolerance (`PROPOSAL.md` §3, reusing `validate.py`'s allowlists per `IMPLEMENTATION_CONTEXT.md` §1)
is tested against real historical shapes, not just the current schema.

| # | Fixture shape | Represents | Expected `ingest.py` behavior |
|---|---|---|---|
| 1 | Current schema, complete run (`start_ts`+`end_ts`+`final_status: DONE`) | The common case | Parses cleanly, `is_inferred_active: false` |
| 2 | Legacy shape 1: `started_at`/`finished_at`/`status`/`phases_completed`/`notes` | Oldest documented generation | Tolerated via `validate.py`'s `LEGACY_COMPLETION_FIELDS`, normalized to the current `RunSummary` shape |
| 3 | Legacy shape 3: `ts_start`/`ts_end`/`result`/`agent` | A different legacy generation | Same tolerance path, different source field names |
| 4 | `final_status` present, `end_ts` key absent entirely | Legacy shape 2 | Tolerated, `end_ts` surfaces as `null` in the API response, not a parse failure |
| 5 | `run_id` with a `start_ts` but no completion field of any kind, and no matching `tools.jsonl` activity in the active window | A genuinely crashed run | `final_status` synthesized as `CRASHED` (mirrors `validate.py`'s own synthetic status), `is_inferred_active: false` (no recent tool activity to infer from) |
| 6 | `run_id` with a `start_ts` but no completion field, **and** recent `tools.jsonl` activity within the active window | A run genuinely still in progress | `is_inferred_active: true`, `inferred_start_ts` set from the first matching `tools.jsonl` row, per `DATA_MODEL.md` §2 |
| 7 | A `tools.jsonl` row with `run_id: null, seq: null` | Interactive/out-of-workflow tool use | Excluded from every run's `tools_by_seq`/`tools_by_run_recent` — confirmed not to leak into any run's `files_touched` or `live_tail` |
| 8 | A single malformed JSON line in the middle of an otherwise-valid file | Data corruption | Skipped, counted in `/api/health`'s `unparsed_lines` (`DATA_MODEL.md` §1), **does not** abort parsing the rest of the file |
| 9 | A ticket file with valid frontmatter but no `## Tier`/`## Priority`/`## Type` body sections | An incomplete/malformed ticket | `tier`/`ticket_type`/`priority` surface as `null` (`DATA_MODEL.md` §1's `Nullable: Yes` for `ticket_type`/`priority` — note `tier` is documented `No` there, so this case should be treated as a data-quality signal worth its own assertion, not silently defaulted) |
| 10 | Two tickets whose `ticket_id` both match the same `run_id` (shouldn't happen, but not structurally prevented) | A data-integrity edge case | Documented, deliberate behavior needed: first-match-wins or explicit ambiguity flag — **not decided in this plan**, a real open question for whoever implements `ingest.py`'s ticket↔run join (not previously named in any other document in this folder) |

Row 10 is a genuinely new finding from writing this test plan — no other document here considered
the case of an ambiguous ticket↔run match. Flagging it here rather than silently picking a default,
consistent with this whole investigation's practice of naming undecided things explicitly.

---

## 2. Backend test cases

- `test_ingest_parses_current_schema` — fixture #1, asserts full `RunSummary` field population
- `test_ingest_tolerates_legacy_started_at_shape` — fixture #2
- `test_ingest_tolerates_legacy_ts_start_shape` — fixture #3
- `test_ingest_tolerates_missing_end_ts_key` — fixture #4
- `test_ingest_classifies_crashed_run` — fixture #5
- `test_ingest_infers_active_run_from_tool_tail` — fixture #6, asserts `is_inferred_active`/`inferred_start_ts`
- `test_ingest_excludes_out_of_workflow_tool_calls` — fixture #7
- `test_ingest_skips_malformed_line_and_counts_it` — fixture #8, asserts `/api/health`'s `unparsed_lines` increments and the rest of the file still parses
- `test_ingest_ticket_body_section_fields_nullable_when_absent` — fixture #9
- `test_join_events_to_tools_by_seq` — asserts `DATA_MODEL.md` §3's `build_timeline` join produces correctly-ordered `TimelineEntry` list with matching `tool_calls`
- `test_live_tail_excludes_known_seqs` — asserts a live run's `live_tail` never duplicates tool calls already represented in `entries` (the `known_seqs` filter in `DATA_MODEL.md` §3's pseudocode)
- `test_files_touched_dedupes_by_path` — asserts `extract_files_touched` keeps first-seen `ts`/`tool` per unique path, doesn't list a repeatedly-edited file N times
- `test_concurrent_read_during_rebuild_returns_consistent_snapshot` — the test for `DATA_MODEL.md`
  §4's concurrency design: spawns a rebuild and concurrent reads, asserts every read sees either the
  fully-old or fully-new snapshot, never a partially-updated one — this is the one test case in this
  plan that exists specifically because of a gap found only while writing `DATA_MODEL.md`, not
  something `PROPOSAL.md` itself anticipated

Regression marker: none of the above are regression tests in `docs/testing/test_taxonomy.md`'s
sense (that marker is for previously-observed real bugs, per its own stated purpose, cited in
`experiments/placement_integrity/PROPOSAL.md`) — these are new-feature tests for code that doesn't
exist yet. The one exception, if `MONITORING_INSTRUMENTATION_GAP.md`'s fix lands as its own ticket:
its own test *should* carry the `regression` marker, since it fixes a confirmed, named gap — that
test lives in that ticket's own scope, not this one, per `PROPOSAL.md` §8's explicit non-dependency.

---

## 3. Frontend test cases (if the React/Vite stack option is chosen — `PROPOSAL.md` §5a)

Mirroring `frontend/src/test/`'s existing Vitest + Testing Library convention
(`IMPLEMENTATION_CONTEXT.md` §4), not introducing a different test runner:

- `TicketsView.test.tsx` — renders a fixed `TicketSummary[]` fixture, asserts filter pills narrow
  the visible rows, asserts the two distinct empty-state messages (`UI_INTERACTION_SPEC.md` §1)
  render under the correct conditions
- `RecentActivityGantt.test.tsx` — renders a mixed fixture (some completed, one inferred-active
  run), asserts bar styling differs correctly (solid vs. striped), asserts the settle-transition
  class/state changes when a run flips from active to completed between two renders
  (`UI_INTERACTION_SPEC.md` §2)
- `ReplayTimeline.test.tsx` — renders a fixed `RunTimeline` fixture, asserts scrub position
  correctly gates which tool calls are visible in the detail area (`UI_INTERACTION_SPEC.md` §3b/3c),
  asserts the live-edge segment renders the "(phase unknown — run still in progress)" caption when
  `phase`/`agent` are `null`
- `FilesTouchedPanel.test.tsx` — asserts grouping by tool kind and that the panel does not
  re-render/reset when the scrubber position changes (§3d's "not scrubber-gated" requirement)

If instead the vanilla-embedded-HTML option is chosen (`PROPOSAL.md` §5a), there is no existing test
runner for `src/api/server.py`'s own embedded JS (confirmed by its absence from
`.github/workflows/test.yml`, `IMPLEMENTATION_CONTEXT.md` §4) — this plan does not invent one for
that option; the same non-decision named in `PROPOSAL.md` §5a (stack choice affects tooling)
extends here too.

---

## Related

- `PROPOSAL.md` §9 — the testing philosophy this document makes concrete
- `DATA_MODEL.md` §2-§4 — the join algorithm, live-tail logic, and concurrency design under test here
- `UI_INTERACTION_SPEC.md` — the interactions each frontend test case exercises
- `docs/agent-monitoring/schema.md` — "Known Limitations" section, the source of the fixture matrix's legacy-shape rows
- `docs/testing/test_taxonomy.md` — the `regression` marker convention referenced in §2
- `IMPLEMENTATION_CONTEXT.md` §4 — `tests/tools/` as the eventual real location, `frontend/src/test/` as the Vitest precedent
