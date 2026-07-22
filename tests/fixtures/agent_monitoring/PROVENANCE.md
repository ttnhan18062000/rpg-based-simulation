# Fixture Provenance — tests/fixtures/agent_monitoring/

Every `.jsonl` file in this directory is a byte-for-byte copy of exactly one real line from
`agent-monitoring/{runs,events,tools}.jsonl`, extracted via `sed -n '<line>p'` (no re-formatting, no
key reordering, no synthetic substitution). This exists so a future reader can re-verify any fixture
against the live corpus if its exact text is ever in doubt. Source locators below were current as of
2026-07-22; the real files are append-only so earlier line numbers remain stable.

| Fixture file | Source file:line | run_id / locator | Shape it represents |
|---|---|---|---|
| `shape1_started_finished_notes.jsonl` | `agent-monitoring/runs.jsonl:100` | `TCK-20260613-DOC-DOMAIN-CONTRACTS` | Legacy shape 1 — `started_at`/`finished_at`/`status`/`phases_completed`/`notes`, no `end_ts`. |
| `shape2_final_status_no_end_ts.jsonl` | `agent-monitoring/runs.jsonl:74` | `TCK-20260610-WORKER-SINGLETON-GUARD` | Legacy shape 2 — `final_status` present, `end_ts` key absent. |
| `shape3_ts_start_ts_end_result.jsonl` | `agent-monitoring/runs.jsonl:371` | `TCK-20260628-E41G-COHESION-SUSTAIN` | Legacy shape 3 — `ts_start`/`ts_end`/`result`/`agent`. |
| `shape4_completed_at_status.jsonl` | `agent-monitoring/runs.jsonl:56` | `TCK-20260610-SENSE-PERCEPTION-GATE` | Legacy shape 4 — `completed_at`/`status`, no `finished_at`/`final_status`. |
| `shape5_folder_epic_bare_status.jsonl` | `agent-monitoring/runs.jsonl:64` | `FOLDER-phase40-44-cleanup-authoring` | Legacy shape 5 — `FOLDER-*`/`EPIC-*` batch wrapper with a bare `status` field, no `final_status`/`start_ts`/`end_ts`. **One of the 7 genuinely legacy bare-status records** (investigation.md), not one of the 65 `FOLDER-*`/`EPIC-*` records that already match the current schema — verified: this record has no `final_status` key. |
| `shape6_type_checker_exception.jsonl` | `agent-monitoring/runs.jsonl:299` | `TCK-20260623-TYPE-CHECKER` | Legacy shape 6 — the one permanently-documented residual exception (schema.md: "Final residual after the fix: exactly 1"). Uses `outcome`/`phase`/`ts`, no `end_ts`/`final_status`/`status` at all. |
| `tools_jsonl_phase_agent_null_gap.jsonl` | `agent-monitoring/tools.jsonl:278` | `run_id="TCK-20260614-CERT-SAFE-SERIAL"`, `seq=2` | `tools.jsonl` null-gap variant — `run_id`/`seq` present, `phase`/`agent` absent (record predates `TCK-20260719-LIVE-PHASE-AGENT-LABEL`). |
| `tools_jsonl_interactive_null.jsonl` | `agent-monitoring/tools.jsonl:1` | `run_id=null`, `seq=null` | `tools.jsonl` interactive-call variant — tool call made outside any workflow run, by design (not legacy). |
| `events_jsonl_tool_call_count_absent.jsonl` | `agent-monitoring/events.jsonl:2` | `run_id="TCK-20260607-PATH-DRIFT-SRC"`, `seq=1` | `events.jsonl` null-gap variant — record predates both `reason_code` and `tool_call_count` fields. |
| `events_jsonl_reason_code_null.jsonl` | `agent-monitoring/events.jsonl:2` | same real line as `events_jsonl_tool_call_count_absent.jsonl` | Same record — this one real line predates both fields at once, so both fixture files intentionally hold identical content rather than synthesizing two different records. |

## Rule

Do not hand-edit any file in this directory. To refresh a fixture (e.g. if a future audit finds a
better example), re-run the same `sed -n '<line>p' <source> > <fixture>` extraction against the real
corpus and update this table's locator — never type the JSON out by hand.
