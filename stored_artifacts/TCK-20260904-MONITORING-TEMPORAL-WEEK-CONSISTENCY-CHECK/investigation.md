---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260904-MONITORING-TEMPORAL-WEEK-CONSISTENCY-CHECK

## Current Behavior

### Write-path bucketing (re-confirmed by direct read this session)

**`tools/agent-monitoring/post_tool_hook.py`** (full file read, 165 lines):
- Lines 54-60: `now_dt = datetime.now(timezone.utc)`; `now = now_dt.isoformat().replace("+00:00", "Z")`;
  `iso_week = now_dt.strftime("%G-W%V")`. `now` becomes the record's `ts` field (line 149) and
  `iso_week` is the folder-bucketing key (line 159: `Path("agent-monitoring/data") / iso_week /
  "tools.jsonl"`). **Confirmed: `ts` and the bucketing key are computed from the literal same
  `now_dt` value in the same statement block — bit-for-bit identical relationship, not just
  "usually close."** A mismatch between a `tools.jsonl` row's `ts` and its folder's ISO week is
  therefore never expected under the current write path; if one is ever found, it can only be
  explained by manual/legacy data (pre-`TCK-20260902-MONITORING-SHARD-WRITE-PATH` write paths) or
  direct file tampering, not a normal write-time race.

**`tools/agent-monitoring/record_events.py`** (full file read, 170 lines):
- Line 153 (comment lines 149-152 explain the design): `iso_week = datetime.now(timezone.utc).strftime("%G-W%V")`,
  computed **once per batch**, independent of any individual record's own `ts` (which is set earlier
  by the caller/orchestrator per `docs/agent-monitoring/schema.md:175` — "Captured by the orchestrator
  ... immediately before the paired `agent()` call"). Line 154: `events_file = Path("agent-monitoring/data")
  / iso_week / "events.jsonl"`. Confirmed: a batch of events written together always lands in one
  folder (write-time), while each event's own `ts` can be earlier — usually by seconds/minutes
  (one agent-call gap), not weeks, but the code contains no guarantee bounding the gap.

**`tools/agent-monitoring/record_run.py`** (full file read, 101 lines):
- Line 85: `iso_week = datetime.now(timezone.utc).strftime("%G-W%V")` — write-time, computed
  independent of `record["start_ts"]` (REQUIRED field, line 12, captured at Scope/Discover/Comprehend
  phase per `schema.md:73`, i.e. potentially at the very start of a long-running or paused/resumed
  ticket). Confirmed: no relationship is enforced or expected between `start_ts` and the folder's
  week — this is the source of the ticket's documented "legitimate divergence" case.

### `tools/agent-monitoring/verify_referential_integrity.py` (full file read, 227 lines)

The nearest existing report-only precedent, built one ticket ago
(`TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`):
- `load_all_weeks(data_dir, source)` (lines 50-78) reads every `agent-monitoring/data/*/<source>.jsonl`
  file (including `unknown-week`, unconditionally), returning `(record, week_folder_name)` tuples.
  Directly reusable (or import-reusable) for this ticket — it is source-agnostic and already reads
  the exact directory shape this ticket needs.
- `ReferentialIntegrityReport` (lines 136-180): a `@dataclass` with `.to_text()`, matching
  `validate.py`'s `compute_tool_count_drift_report()` string-rendering convention.
  `compute_referential_integrity_report()` (lines 183-199) is the library entry point;
  `main()` (lines 214-226) is a thin CLI wrapper that always exits 0 — "report-only... never
  gates... never exits non-zero on violation volume" (module docstring, lines 25-31).
- **Module docstring's actual framing is narrower than the ticket's own paraphrase.** The ticket's
  Scope says this module's "own module docstring's framing" is "the home for corpus-health checks."
  The real docstring (lines 1-38) never says this — it says, verbatim, "Verify the 2 documented
  foreign-key relationships across the multi-week ... corpus," and both existing checks
  (`check_events_to_runs`, `check_tools_to_events`) are joins between two different `.jsonl` files.
  This ticket's check is a different shape entirely: a single-file, single-record self-consistency
  check (a record's own timestamp vs. the ISO week of the folder it physically sits in) — not a
  join. This distinction matters for the module-location decision below (see Risks).

### `tools/gate_checks/done_checker_static.py` (full file read, 843 lines)

- `run_static_precheck(ticket_id, tier, start_ts)` at **line 555** (confirmed, not just the ticket's
  claimed "~line 555"). Its docstring (line 556) currently reads "Aggregate all 7 Part A checks" —
  **this must become 8** once the new check is added (both the docstring number and the `checks`
  tuple itself, lines 560-568, currently has exactly 7 entries:
  `staging_artifacts_complete`, `data_runs_clean`, `ticket_location`, `working_log_no_row_yet`,
  `frontmatter_valid`, `ticket_field_values_valid`, `docs_to_update_coverage`).
- Every `check_*` function returns `tuple[str, str]` = `(status, evidence)` — confirmed uniform
  across `check_staging_artifacts_complete`, `check_data_runs_clean`, `check_ticket_location`,
  `check_working_log_no_row_yet`, `check_frontmatter_valid`, `check_ticket_field_values_valid`,
  `check_docs_to_update_coverage` (lines 136-552). `run_static_precheck` (lines 569-572) wraps each
  `(name, (status, evidence))` pair into `{"condition": name, "status": status, "evidence": evidence}`.
- **Correction to the ticket's own status-vocabulary claim.** The ticket's Request Summary states
  "there is currently no non-blocking status value beyond `PASS`/`FAIL`/`CLEANED`." This is
  imprecise in a way worth recording exactly: `CLEANED` is returned by `clean_data_runs_early`
  (lines 197-245), but that function is **not** one of the 7 entries in `run_static_precheck`'s
  `checks` tuple — it is invoked from a separate orchestrator call site (`implement-ticket.js`,
  between Test and Parity, per its own docstring lines 205-210), not from `run_static_precheck`
  itself. Within `run_static_precheck`'s own aggregated checklist, the actual vocabulary in use
  today is **`PASS` / `FAIL` / `NA`** (`NA` used by `check_staging_artifacts_complete` and
  `check_docs_to_update_coverage` for the hotfix-tier skip case, lines 139-140 and 509-510).
  `NA` already carries a specific, different meaning ("this condition does not apply at this
  tier") from what an "informational, never-blocking, always has real evidence" status would need
  to mean — so `NA` is not a safe stand-in for the new check's "always non-blocking" requirement
  either. This sharpens (does not overturn) the ticket's own recommended resolution: an
  always-`PASS`-with-evidence design is the only option that reuses an existing, compatible status
  value in `run_static_precheck`'s real vocabulary; a genuinely new "informational" status value
  (e.g. `INFO`) would be introducing a fourth status into this specific aggregation for the first
  time, not just reusing `CLEANED`'s already-existing precedent (which lives in a different
  function, at a different call site).

## Real Corpus Findings (2026-09-04, scan against live `agent-monitoring/data/`)

Ran three independent verification passes (see Test Summary discipline — same as
`TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`'s own "report what's actually found" standard).
The corpus is live and grows with every tool call made during this investigation itself (each Bash/
Read/Edit call appends its own `tools.jsonl` row via `post_tool_hook.py`) — exact totals shift
between passes by a handful of rows; the ratios and zero-mismatch conclusion below are stable across
all three passes.

**Pass 1 — naive single-field check (`tools.ts`, `events.ts`, `runs.start_ts` only, no fallback):**
- `tools.jsonl`: 186,195 checked (1 in `unknown-week`, exempted) — **0 mismatches**.
- `events.jsonl`: 9,024 total, 28 in `unknown-week` (exempted), **32 missing `ts` entirely**, 8,964
  matched, **0 mismatches** among the ones that had `ts`.
- `runs.jsonl`: 1,394 total, 5 in `unknown-week` (exempted), **105 missing `start_ts` entirely**,
  1,284 matched, **0 mismatches** among the ones that had `start_ts`.

**Investigating the "missing field" rows**: every one of the 32 `events.jsonl` rows missing `ts`
carries a `timestamp` field instead (legacy pre-schema-enforcement shape, e.g.
`agent-monitoring/data/2026-W25/events.jsonl:38`, `run_id=TCK-20260618-AUDIT-D09-WIRING`, fields
`['details', 'event_type', 'message', 'run_id', 'system', 'tick', 'timestamp']` — no `seq`/`phase`/
`agent`/`summary`/`status` at all, i.e. pre-dates the current REQUIRED-field schema). Of the 105
`runs.jsonl` rows missing `start_ts`: 41 have `started_at` instead (e.g.
`agent-monitoring/data/2026-W24/runs.jsonl:47`, fields `['agent', 'completed_at', 'notes', 'run_id',
'started_at', 'status', 'ticket_id', 'tier']` — also missing `workflow`/`final_status`/`agent_count`,
confirming pre-schema-enforcement legacy shape); the remaining 64 are a mix of even older shapes —
some carry a generic `ts` (39 rows), 2 carry only `completed_at`, and 23 carry only a `timestamp`
field (e.g. `agent-monitoring/data/2026-W25/runs.jsonl:23`, fields `['run_id', 'status', 'summary',
'ticket_id', 'tier', 'timestamp']`) — and one batch of 6 rows in `2026-W26` uses `ts_start`/`ts_end`
(fields `['agent', 'result', 'run_id', 'ticket_id', 'tier', 'ts_end', 'ts_start', 'workflow']`).

**This is not new territory for this repo**: `docs/agent-monitoring/schema.md:511-517` ("Known
Limitations > Legacy schema generations without `end_ts`") already enumerates 5 of these exact
legacy shapes for `runs.jsonl`, and `docs/agent-monitoring/schema.md:119-121` already documents a
sanctioned field-priority fallback list used by the migration itself:
> "keyed by each row's own `start_ts` field (with a documented field-priority fallback — `ts`,
> `ts_start`, `started_at`, `completed_at`, `ts_end`, `finished_at`, `timestamp`, in that order —
> for the rare row missing `start_ts`)"

and `docs/agent-monitoring/schema.md:152-153` documents the same for `events.jsonl` ("the same
documented field-priority fallback list used for `runs.jsonl`"). The actual code is
`tools/agent-monitoring/migrate_monitoring_data.py:63-69`:
```python
RUNS_FIELD_PRIORITY = [
    "start_ts", "ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]
EVENTS_FIELD_PRIORITY = [
    "ts", "start_ts", "ts_start", "started_at", "completed_at", "ts_end", "finished_at", "timestamp",
]
```
and the tolerant parser is `tools/agent-monitoring/migrate_tools_shards.py::_parse_ts_to_week()`
(lines 48-63) — handles the standard `%Y-%m-%dT%H:%M:%S.%fZ` shape and a rare bare no-timezone
form, falling back to `UNKNOWN_WEEK_KEY` (never raises) if neither parses.

**Pass 2 — re-run using the actual sanctioned `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` lists and
`_parse_ts_to_week()`, imported directly from `migrate_monitoring_data.py`/`migrate_tools_shards.py`
(not reinvented)**, against the full real corpus, one week folder at a time:

| Source | Total rows | In `unknown-week` (exempt) | No usable field in known folder | Match | Mismatch |
|---|---|---|---|---|---|
| `runs.jsonl` | 1,394 | 5 | **0** | 1,389 | **0** |
| `events.jsonl` | 9,024 | 28 | **0** | 8,996 | **0** |
| `tools.jsonl` | 186,212 | 1 | 0 | 186,211 | **0** |

**Zero mismatches and zero unparseable-in-a-known-folder rows anywhere in the live corpus today**,
across all three sources. The 9 `runs.jsonl` rows that Pass 1 flagged as missing both `start_ts` and
`started_at` all resolve cleanly once the full 8-field priority list is applied (`ts`, `timestamp`,
etc. cover every one of them).

**Why this is a genuinely different finding from "the corpus is clean" and needs to be stated
carefully in the check's own report, not just left implicit**: the reason mismatch is zero is not
that write-time divergence can't happen — it's that the *existing* week-folder assignment for every
row currently in the corpus was **itself computed using this exact same field-priority lookup +
tolerant parser**, either by `migrate_monitoring_data.py`'s `bucket_lines_by_week_multi_field()`
(for every pre-migration `runs`/`events` row, `TCK-20260903-MONITORING-DATA-MIGRATION`) or by
`post_tool_hook.py`'s direct `ts`-equals-bucketing-key identity (for every `tools.jsonl` row, both
pre- and post-migration). No `runs.jsonl` row has yet been through a full week-spanning
pause/resume cycle *since* the new write-time-bucketing design went live
(`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, 2026-09-03) — the whole unified-weekly epic and
this ticket both landed within the same ISO week (`2026-W36`). **The check's real value is
prospective (catching the first genuine write-time-vs-record-time divergence going forward, e.g. the
next ticket whose `start_ts` is captured in W36 but whose `runs.jsonl` write lands in W37), not
retrospective** — a reader of its report must not conclude "this check found nothing, so it's
low-value"; it is finding real corpus-wide consistency precisely because the corpus's own physical
layout was constructed by the equivalent of this same rule, and its job going forward is to keep
catching genuine future drift the same way `TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG`
caught a different class of write-time corruption after the fact.

## `unknown-week` folder (confirmed exempt, per ticket's framing — correct)

`agent-monitoring/data/unknown-week/` contains 34 total rows (28 events, 5 runs, 1 tools) that were
explicitly routed there by the migration because no field in the priority list could be parsed into
an ISO week at all (`UNKNOWN_WEEK_KEY` fallback, `migrate_tools_shards.py:48-63`). Direct inspection
confirms this is not merely "missing a field" but genuinely unparseable content: e.g.
`agent-monitoring/data/unknown-week/runs.jsonl` contains rows with **numeric epoch floats** as
`start_ts` (`"start_ts": 1781425809.0960267`) rather than ISO-8601 strings — `datetime.fromisoformat()`
raises on this input, so no ISO week can ever be derived. The `unknown-week/tools.jsonl` row and
several `unknown-week/events.jsonl` rows are also structurally pre-migration/batch-summary shapes
(e.g. an `implement-epic` batch-result row, not a real per-tool-call record) with no `ts`-shaped
field at all. **The ticket's framing is correct**: there is no real ISO week to compare against for
these records — "structurally exempt, not miscounted" (ticket Scope) is the right rule, and this is
already the same exemption `verify_referential_integrity.py` extends to `unknown-week` for its own
FK checks (its `load_all_weeks()` reads it unconditionally into the join population; nothing here
special-cases it out of a join, but nothing here computes an expected-week comparison for it either
— this ticket's check is the first one that actually needs an explicit "no week to compare against"
branch).

## Malformed/missing timestamp fields — recommended fallback rule

Confirmed above: a field-priority lookup, not a single hardcoded field name, is required for
`runs.jsonl` and `events.jsonl` (not for `tools.jsonl`, which has never had a legacy variant beyond
the single already-migrated `unknown-week` row). **Recommendation: import
`RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` from `migrate_monitoring_data.py` and
`_parse_ts_to_week`/`UNKNOWN_WEEK_KEY` from `migrate_tools_shards.py` directly, rather than
re-declaring a duplicate list** — these are the actual sanctioned lists that determined where every
pre-migration row physically landed, already documented in `docs/agent-monitoring/schema.md:119-121`
and `:152-153`, and reusing them by import (not by re-typing) guarantees the check can never silently
drift out of sync with the real bucketing rule it is auditing. A record with no usable field in the
priority list, in a known (non-`unknown-week`) folder, did not occur anywhere in the real corpus
today (0 of 196,630 rows across all 3 sources) — but the check must still handle it defensively
(treat as a third bucket, "unparseable — skipped," distinct from both "match" and "mismatch/
divergence," since it is neither a positive nor a negative finding) rather than assume it can never
happen.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: add a new "Temporal Week Consistency" entry to the existing
  "Known Limitations" section (after the "Referential Integrity Verification" entry, lines 531-552),
  mirroring that entry's own structure — what the new check does, which fields/priority lists it
  reads (cross-referencing the already-documented field-priority lists at lines 119-121/152-153
  rather than re-describing them), the `unknown-week` exemption, and a real-corpus finding summary
  (zero mismatches, with the "why zero is expected right now, not proof the check is inert" caveat
  from this investigation's own findings above) plus a pointer to this ticket's stored investigation.
  Exact wording is deferred to implementation time (same precedent as child 6's own "Deferred to
  implementation time" note for its own Known Limitations entry), since it should describe whatever
  the implementer's own real-corpus run against the *finished* tool reports, not this investigation's
  scratchpad numbers verbatim.

`docs/mechanics/*.md` and `docs/engine/*.md` were considered and excluded: no chapter or contract
governs agent-monitoring tooling — this is the same, already-established conclusion
`TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY`'s own investigation reached for the identical
subsystem (its investigation.md, "Docs Requiring Update" section), which itself cites
`TCK-20260705-MONITORING-RUNID-JOIN` reaching the same conclusion before it. `docs/guides/
agent_monitoring.md` was checked directly (`grep` for `verify_referential_integrity`/`done_checker_
static`/"Part A") and contains no reference to either the referential-integrity tool or done-checker's
Part A checklist mechanism — no update needed there.

## Parity Ledger Overlap

None. `docs/parity_ledger/*.yaml` tracks simulation-subsystem behavior (`substrate.yaml`,
`combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
`social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`) — confirmed by direct `grep`
that no existing entry references agent-monitoring tool internals. `infrastructure.yaml`'s "Replay,
telemetry, observability, workers" heading covers simulation-replay/telemetry infrastructure, not
this repo's own agent tooling meta-observability — the same conclusion
`TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY` and `TCK-20260705-MONITORING-RUNID-JOIN` both
already reached for this identical subsystem.

## Prior Work

- `TCK-20260903-MONITORING-DATA-REFERENTIAL-INTEGRITY` (`stored_artifacts/TCK-20260903-MONITORING-
  DATA-REFERENTIAL-INTEGRITY/`): direct architectural precedent — report-only, `load_all_weeks()`,
  dataclass + `.to_text()`, always-exit-0 `main()`, real-corpus-findings-captured-honestly
  discipline, and (per its own plan.md's ratified Decision on item 8) the standalone-vs-shared-module
  reasoning most directly analogous to this ticket's own module-location question.
- `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY` / `TCK-20260903-MONITORING-DATA-MIGRATION`: the
  write-time bucketing design and the field-priority migration logic this check verifies the
  consequences of and directly reuses.
- `TCK-20260810-MONITORING-NEGATIVE-DURATION-TIMESTAMP-BUG` /
  `TCK-20260810-MONITORING-NEGATIVE-DURATION-BULK-CLEANUP`: precedent for this repo's "disclose
  honestly, correct only what's directly reported/in-scope, never silently bulk-fix historical data"
  discipline for a different class of timestamp-quality issue — directly informs this ticket's own
  "report-only, never repair" posture (already in Out of Scope) and the tone for any Known
  Limitations entry.
- `TCK-20260705-MONITORING-RUNID-JOIN`: established the "Known Limitations" documentation pattern in
  `schema.md` and the precedent that a "no doc genuinely governs this" conclusion for `docs/parity_
  ledger/`/Mechanics Bible is a real, evidenced judgment call for agent-monitoring tooling, not a
  lazy default.

## Risks and Open Questions

1. **Module location is a real, non-trivial decision — recommend a new sibling script, not extending
   `verify_referential_integrity.py`.** Both checks share `load_all_weeks()`, the report-only
   philosophy, and the dataclass-plus-`.to_text()` shape, which argues for extension. But:
   - The existing module's docstring (lines 1-38) and its dataclass name
     (`ReferentialIntegrityReport`) are both specifically scoped to the 2 FK joins — a temporal
     self-consistency check is not a join at all (single source file, compares a record's own
     field against its own containing folder, no second `.jsonl` file involved). Folding it in
     would either force a misleading rename of `ReferentialIntegrityReport` or bolt an unrelated
     third field onto a dataclass whose name and docstring both promise "referential integrity"
     specifically.
   - Child 6's own ratified module-location decision (`plan.md`, "Decision on item 8") chose a new
     standalone file over extending `validate.py` specifically to avoid mixing two different check
     families/read-paths into one module, even though `validate.py` is philosophically the closer
     match by content (data-quality checks over the same corpus). The same reasoning applies here,
     one level down: FK-join checks and single-record temporal-consistency checks are two different
     check families over the same corpus.
   - **Recommendation**: a new sibling script (e.g. `tools/agent-monitoring/
     verify_temporal_week_consistency.py`), importing `load_all_weeks` from
     `verify_referential_integrity.py` (documented reuse of the existing loader, not a duplicate —
     satisfies Scope's explicit "do not build a 4th independent loader"), with its own report
     dataclass. This is a recommendation for Plan to weigh, not a mandate — the ticket explicitly
     leaves this to the implementer's judgment.
2. **Status-vocabulary reconciliation (ticket's own flagged open decision).** See the "Correction to
   the ticket's own status-vocabulary claim" note above — `run_static_precheck`'s real, current
   vocabulary is `PASS`/`FAIL`/`NA` (not `PASS`/`FAIL`/`CLEANED`), and `NA` already carries an
   incompatible meaning (tier-skip, not "informational"). This does not change the ticket's own
   recommended resolution (always-`PASS`-with-evidence) — it sharpens the reasoning for it, and
   Plan should record the choice explicitly per the ticket's own instruction, citing the corrected
   vocabulary fact from this investigation rather than the ticket's original (slightly imprecise)
   framing.
3. **The check will almost certainly report zero findings against the live corpus on its first real
   run** (see Real Corpus Findings above) — this is expected and must be stated explicitly in the
   new check's own report/evidence text and in the Known Limitations doc entry, not left to imply
   "nothing to see here." A future reader (or done-checker's own evidence trail) seeing "0
   mismatches" repeatedly across many ticket closes should not conclude the check is dead weight;
   Plan/implementation should make sure the evidence string itself carries this context (e.g. total
   rows checked, not just a violation count of 0) so it reads as active verification, not a stub.
4. **No open question blocks implementation.** All required field-priority/parsing/exemption
   behavior is already implemented and documented elsewhere in this repo (migration scripts,
   schema.md) — this ticket's job is to read and check, not invent new parsing rules.

## Anti-Drift Hazards

- **`run_static_precheck`'s docstring number and the `test_run_static_precheck_all_pass_eligible`
  assertion must both move from 7 to 8 together.** `tests/tools/test_done_checker_static.py:619`
  currently asserts `len(results) == 7` with an explanatory comment tracking the check's own
  addition history (5→6→7) — this is the single most likely test to silently fail (or worse,
  silently mis-pass if not updated and the new check is accidentally left out of the `checks`
  tuple) when this ticket lands. Update the comment's history line too, not just the number.
- **Do not conflate `unknown-week` exemption with "no usable field in a known folder."** These are
  two structurally different, both-legitimate "cannot compute a mismatch" cases that must not be
  merged into one bucket in the report — `unknown-week` means "the folder itself has no real ISO
  week" (a property of where the record physically sits); "no usable field" means "the record
  landed in a real, dateable folder, but this specific record carries no timestamp-shaped field at
  all" (a property of the record's own content). Conflating them would make it impossible to tell,
  from the report alone, whether a future non-zero count in this bucket is a new, currently-unseen
  data-quality problem (a record with no timestamp field at all landing in a real week folder) or
  just ordinary legacy `unknown-week` noise growing.
- **Do not silently drop `runs.jsonl`'s already-legitimate divergence into the same "mismatch"
  bucket as `tools.jsonl`'s anomaly-framed mismatches** — this is the ticket's own central design
  constraint (Request Summary), re-confirmed by this investigation's direct source reads: there is
  no code-level guarantee bounding how far a `runs.jsonl` `start_ts` can precede its folder's week
  (a long-running/paused ticket can span arbitrarily many weeks), while a `tools.jsonl` `ts`/
  bucketing-key mismatch has no legitimate explanation under the current write path at all.
- **Do not build a 4th independent multi-week loader.** Reuse `load_all_weeks()` (import from
  `verify_referential_integrity.py` regardless of where the new check itself lives) — Scope is
  explicit on this, and it is already proven correct/tested against the real corpus shape.
- **Do not re-type `RUNS_FIELD_PRIORITY`/`EVENTS_FIELD_PRIORITY` by hand.** Import them from
  `migrate_monitoring_data.py` (and `_parse_ts_to_week`/`UNKNOWN_WEEK_KEY` from
  `migrate_tools_shards.py`) — these are the actual lists that determined the real corpus's current
  physical layout; a hand-retyped copy could silently drift from them over time with no test to
  catch the divergence.
- **Do not repair, re-bucket, or backfill any finding** — report-only, matching Out of Scope and
  every prior corpus-health tool's own precedent in this repo's history
  (`TCK-20260810-MONITORING-NEGATIVE-DURATION-*`, `verify_referential_integrity.py`).
