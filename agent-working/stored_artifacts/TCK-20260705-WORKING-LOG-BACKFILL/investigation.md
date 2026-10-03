---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKING-LOG-BACKFILL
artifact_type: investigation
tags: [agent-monitoring, data-quality, working-log, csv-parsing]
---

# Investigation — TCK-20260705-WORKING-LOG-BACKFILL

## Current Behavior (file:line)

`python3 tools/agent-monitoring/validate.py` (re-run fresh at investigation time, 2026-07-05) currently
flags **62** distinct `TCK-*` run_ids with `WARNING: Run marked DONE has no working_log entry: <id>`. This
matches the ticket's cited count exactly — no drift since filing.

The check itself lives in `tools/agent-monitoring/validate.py:96-108` ("3. Cross-check" block):

```python
if LOG_FILE.exists():
    log_tids = set()
    with open(LOG_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row.get("ticket_id", "").strip()
            if tid.startswith("TCK-"):
                log_tids.add(tid)
    for run_id, run in runs_by_id.items():
        if not run_id.startswith("TCK-"):
            continue
        status = run.get("final_status") or run.get("status")
        if status == "DONE" and run_id not in log_tids:
            warnings.append(f"Run marked DONE has no working_log entry: {run_id}")
```

**Central finding of this investigation: none of the 62 flagged run_ids represent a genuine missing
`working_log.csv` row.** Every single one already has a row in `tickets/working_log.csv` today. They are
invisible to `validate.py`'s check for two independent, confirmed reasons — neither of which is a
`working_log.csv` gap:

### Reason A — legacy malformed column order (39 of 62 cases)

`tickets/working_log.csv`'s header (line 1) is `timestamp,ticket_id,title,status,summary,artifacts_path`.
`csv.DictReader` maps row values to these keys **positionally**, regardless of what each row's own
content actually is. A large historical block of rows (lines ~539, ~669, ~763-769, ~795-864, etc. — 71
rows total across the whole file, confirmed via a full-file scan) place the ticket_id in **column 1**
instead of column 2, e.g.:

```
tickets/working_log.csv:795:
TCK-20260623-FIX-ARENA,2026-06-24,standard,bug,simulation,DONE,Fix kernel2 thread leak...,src/certification/harness.py;tests/arena/test_arena_stress.py
```

Under `DictReader`, this row's `row["ticket_id"]` evaluates to `"2026-06-24"` (column 2), not
`"TCK-20260623-FIX-ARENA"` — so `tid.startswith("TCK-")` is `False` and the row is silently never added to
`log_tids`, even though the ticket is unambiguously logged in the file. Spot-checked against
`tickets/done/TCK-20260623-FIX-ARENA.md`'s own Title/Completion Summary — content matches verbatim
(kernel2 thread-leak fix, teardown OSError). Same pattern confirmed for
`TCK-20260610-ARCHETYPE-DEFAULT-PATH` (line 539) and `TCK-20260619-E53Cb-SIEGE-MODEL` (line 763) by direct
comparison against their `tickets/done/` files.

33 of the 62 flagged run_ids hit this pattern directly (run_id == the malformed row's column-1 value). A
further 6 (`TCK-20260619-E53Cb-SIEGE-MODEL-run`, `-E53Cc-TERRITORY-TRANSFER-run`,
`-E53Cd-WAR-EXHAUSTION-run`, `-E53Db-SIEGE-BETRAYAL-LEDGER-20260623`,
`-E53Dc-COMPILER-INTEGRATION-20260623`, `-E53Dd-DOC-ARCHIVE-20260623`) hit this pattern **after** stripping
a run_id suffix (see Reason B) — their base ticket_id has a malformed row at `working_log.csv:763-769`.

### Reason B — run_id ≠ ticket_id, base ticket_id already logged correctly (23 of 62 cases)

Confirmed directly from `agent-monitoring/runs.jsonl`: many of the flagged run_ids carry a hash/timestamp/
`-run-NNN` suffix not present in the real ticket file, and — critically — **the run record itself often
carries a separate `ticket_id` field distinct from `run_id`** that validate.py never reads, e.g.:

```json
{"run_id":"TCK-20260619-E53Cb-SIEGE-MODEL-run","ticket_id":"TCK-20260619-E53Cb-SIEGE-MODEL", "final_status":"DONE", ...}
```

For 22 of these cases, the base ticket_id (stripped of suffix, or read from the record's own `ticket_id`
field) has a **wellformed** row already in `working_log.csv` (single `grep -c "^[^,]*,{base},"` hit each):
`TCK-20260614-LIFECYCLE-SUPERVISOR`, `-OBS-BACKPRESSURE`, `-REPLAY-BACKPRESSURE`, `-RESOURCE-DASHBOARD`,
`TCK-20260619-COMBAT-ECOLOGY`, `-E-READ-MODEL`, `-E12A-BALANCE-MEASURE`, `-E12B-BLOCKER-RECAL`,
`-E12C-BALANCE-TESTS`, `-E13C-RECIPES`, `-E41C-REWARD-DIST`, `-E42A-INFO-NEED`, `-E42B-INFO-PROVIDER`,
`-E42E-LEAD-TYPES`, `-E43A-SOCIAL-MEM-MODEL`, `-E53Aa-FACTION-STATE`, `-E53Ac-DIRECTIVE-PROP`,
`-E53Ad-TENSION-UPDATE`, `TCK-20260629-SIMQ-EMIT-AGENCY`, `-SIMQ-EMIT-COGNITION`, `-SIMQ-EMIT-ECONOMY`,
`-SIMQ-EMIT-WORLD`.

The 23rd case, `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN`, is the exact pattern already root-caused by
the sibling ticket `TCK-20260705-MONITORING-RUNID-JOIN` ("Pattern 2. Ticket-rename mismatch" /
"ad hoc `run_id` suffix invented during a manual/direct monitoring-write session, not a real ticket
rename"). `git log --follow` on that ticket showed no rename; `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN.md`
does not exist (only `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md`); and `working_log.csv` already
carries **3** correctly-keyed rows under the true `TCK-20260701-HAZARD-NATIVE-IMMUNITY` id (lines 905, 907,
909 — original pass, REDESIGN-content pass, and a post-DONE AMENDED correction), confirming the second
implementation pass's work was logged under the correct base ticket_id even though its `runs.jsonl` record
used the ad hoc `-REDESIGN` run_id.

**39 (Reason A) + 23 (Reason B) = 62 — the full flagged set, no residual.**

## Definitive Table

| run_id (as flagged) | verified via | title / summary source | verdict |
|---|---|---|---|
| TCK-20260610-ARCHETYPE-DEFAULT-PATH | malformed row, working_log.csv:539 (col1=ticket_id) + tickets/done/ exact match | "Promote archetype-native entity construction..." | exclude — already logged (malformed row) |
| TCK-20260610-CATALOG-ARENA-SMOKE | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-CATALOG-SCENARIO-BUILDER | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-CATALOG-VS-LEGACY-SEMANTICS | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-COMBAT-RELATION-PROJECTION | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-QUEST-RELATION-PROJECTION | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-REGION-THREAT-PROJECTION | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-SCENARIO-RESOLVER-UNXFAIL | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260610-STRICT-MATRIX-UNXFAIL | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260614-LIFECYCLE-SUPERVISOR-7d657d31 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key (base already logged) |
| TCK-20260614-OBS-BACKPRESSURE-5f2e3960 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260614-REPLAY-BACKPRESSURE-9214654b | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260614-RESOURCE-DASHBOARD-04a633be | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-COMBAT-ECOLOGY-20260620T040000Z | base (suffix-stripped) has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E-READ-MODEL-20260620T031000Z | base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E11A-HERO-AUTHORING | malformed row (col1) + tickets/done/ exact match | "Author HERO entities in sandbox_world..." | exclude — already logged (malformed row) |
| TCK-20260619-E12A-20260620 | base E12A-BALANCE-MEASURE has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E12B-20260620 | base E12B-BLOCKER-RECAL has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E12C-20260620 | base E12C-BALANCE-TESTS has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E13C-RECIPES-20260620T072424Z | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E41C-20260621-001 | base E41C-REWARD-DIST has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E42A-INFO-NEED-run-001 | base E42A-INFO-NEED has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E42B-INFO-PROVIDER-run-1 | base E42B-INFO-PROVIDER has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E42E-LEAD-TYPES-run-001 | base E42E-LEAD-TYPES has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E43A-SOCIAL-MEM-MODEL-run-001 | base E43A-SOCIAL-MEM-MODEL has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E53Aa-FACTION-STATE-implement-001 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E53Ac-DIRECTIVE-PROP-run | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E53Ad-TENSION-UPDATE-run | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260619-E53Ca-CONFLICT-PHASE | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E53Cb-SIEGE-MODEL-run | runs.jsonl `ticket_id` field → base has malformed row, working_log.csv:763 | "Epic 5.3Cb Squad Commitment + Siege State Model" | exclude — duplicate key + malformed row |
| TCK-20260619-E53Cc-TERRITORY-TRANSFER-run | base malformed row, working_log.csv:764 | — | exclude — duplicate key + malformed row |
| TCK-20260619-E53Cd-WAR-EXHAUSTION-run | base malformed row, working_log.csv:765 | — | exclude — duplicate key + malformed row |
| TCK-20260619-E53Db-SIEGE-BETRAYAL-LEDGER-20260623 | base malformed row, working_log.csv:767 | — | exclude — duplicate key + malformed row |
| TCK-20260619-E53Dc-COMPILER-INTEGRATION-20260623 | base malformed row, working_log.csv:768 | — | exclude — duplicate key + malformed row |
| TCK-20260619-E53Dd-DOC-ARCHIVE-20260623 | base malformed row, working_log.csv:769 | — | exclude — duplicate key + malformed row |
| TCK-20260619-E62A-CULTURE-MODEL | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E62B-CULTURE-DERIVER | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E62C-MOTIVATION-OVERLAY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E62D-PARITY-VERIFY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E63A-GATE-VERIFY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E63B-MANIFEST-MODEL | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E63C-REGISTRY-LOADER | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260619-E63D-BALANCE-PARITY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-ARENA | malformed row, working_log.csv:795 + tickets/done/ exact match | "Fix arena simulation behavioral regression..." | exclude — already logged (malformed row) |
| TCK-20260623-FIX-BEHAVIORAL-MISC | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-COMBAT-QUEST | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-CONTENT-REGISTRY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-DOCS-INTEGRITY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-ENTITY-ID | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-INVENTORY-DEFAULTS | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-KERNEL-PHASES | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-OBS-QUEUE | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-RUNTIME-MODE | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-STAT-FORMULAS | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-TEST-TEARDOWN | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260623-FIX-WORLDASSEMBLY | malformed row (col1) + tickets/done/ exact match | — | exclude — already logged (malformed row) |
| TCK-20260628-SIMQ-E1-FOUNDATION | malformed row, working_log.csv:864 + tickets/done/ exact match | "Core models and data layer for simulation quality scoring..." | exclude — already logged (malformed row) |
| TCK-20260629-SIMQ-EMIT-AGENCY-1782753561 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260629-SIMQ-EMIT-COGNITION-1782753912 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260629-SIMQ-EMIT-ECONOMY-1782754776 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260629-SIMQ-EMIT-WORLD-1782754367 | runs.jsonl `ticket_id` field → base has wellformed row | — | exclude — duplicate key |
| TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN | base has 3 wellformed rows (905/907/909); no `tickets/done/*-REDESIGN.md` file exists; matches TCK-20260705-MONITORING-RUNID-JOIN's confirmed "ad hoc run_id" Pattern 2 | — | exclude — ad hoc run_id, already logged under true id |

**Verdict summary: 0 include-in-backfill / 62 exclude-with-reason.** No new `working_log.csv` rows are
warranted — every flagged ticket already has a row.

## `working_log.csv` Format (confirmed)

Header (line 1): `timestamp,ticket_id,title,status,summary,artifacts_path`

A canonical wellformed row (line 2):
```
2026-03-21T12:56:34Z,TCK-20260321-ENRICH-EVENT-INFORMATION,Enrich Event Information,DONE,Implemented Domain EventBus + Dataclass Telemetry,stored_artifacts/enhance-01/
```
6 fields, `timestamp` full ISO-8601 with `Z`, fields containing commas double-quoted (e.g. line 3's summary).
Full-file scan: 944 data rows total — 837 wellformed (ticket_id in column 2), 71 malformed (ticket_id in
column 1, legacy shape used for a documented historical block roughly 2026-06-10 through 2026-06-29), and
36 in a third legacy shape (`date, batch-uuid, ticket_id-in-col3`, exclusively pre-2026-06-07
`TCK-20260530-PHASE*`/`TCK-20260606-GRAPH-MODELFIX` rows plus one `D20-AUDIT-UPDATE` non-`TCK-` row — none
of the 62 flagged ids overlap this third shape).

## Mechanics/Engine Constraints

Not applicable — this is a pure agent-monitoring/tooling data-quality question, not a simulation mechanics
change. No `docs/mechanics/` or `docs/engine/` contract governs `working_log.csv` format.

## Parity Ledger Overlap

None. `working_log.csv` and `validate.py` are not simulation subsystems tracked by the parity ledger.

## Prior Work

- `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` (done): fixed `validate.py`'s cross-check to fall back from
  `final_status` to legacy `status` field, which is what surfaced this ticket's 62-count (up from the
  original 8-9 estimate, later corrected in that ticket's own record to "8 new cases, 54→62 total"). That
  ticket explicitly deferred the backfill decision to this ticket. It did **not** address the CSV
  column-order parsing gap or the run_id≠ticket_id join gap documented above — those are new findings from
  this investigation.
- `TCK-20260705-MONITORING-RUNID-JOIN` (done): root-caused the exact "ad hoc run_id suffix, not a real
  rename" pattern independently confirmed above for `HAZARD-NATIVE-IMMUNITY-REDESIGN`, and separately
  established the "reuse the exact ticket ID as `run_id`" convention going forward (documentation-only fix,
  in `docs/agent-monitoring/schema.md`). Historical run_id/ticket_id mismatches from before that convention
  (all of Reason B above) were left unaddressed by design (append-only precedent) — this investigation
  independently rediscovers the same class of mismatch from the working_log-cross-check angle rather than
  the events-join angle that ticket covered.
- Neither prior ticket investigated `working_log.csv`'s own malformed-row population (Reason A) — that is
  this investigation's own new finding.

## Risks and Open Questions

1. **The ticket's AC2 ("re-running validate.py after the backfill shows zero, or a documented justified
   residual, warnings") cannot be satisfied by adding rows**, because there is nothing missing to add. The
   62 warnings will persist unchanged after this ticket's "backfill" work (there being none to do) unless
   one of the following — both explicitly **out of scope** for this ticket as currently written — is also
   done:
   (a) fix `validate.py`'s CSV cross-check to parse malformed legacy rows correctly (e.g. detect
       column-1-vs-column-2 shape per row, or use `csv.reader` + heuristic instead of blind `DictReader`)
       and to consult a run record's own `ticket_id` field when present instead of blindly using `run_id`
       as the join key; or
   (b) normalize/rewrite the 39 malformed rows into the canonical 6-column shape.
   AC2 does explicitly allow "a documented, justified residual" — this investigation recommends treating
   all 62 as exactly that residual, with the reasons in the table above serving as the documentation, and
   recommends spinning off a follow-up ticket for option (a) (a `validate.py` fix, matching this session's
   established pattern of fixing the checker rather than rewriting history).
2. **Rewriting the 39 malformed rows in place (option b) is explicitly not authorized by this ticket's
   scope** ("Append one row per confirmed-complete ticket... following the existing format" — append, not
   rewrite) and would touch 39 pre-existing lines rather than add new ones, a materially larger and riskier
   operation than what was scoped. Recommend NOT doing this under this ticket; flag as a separate follow-up
   if the team wants the ledger's column shape normalized.
3. Given finding (1), the Plan phase should decide between: (i) closing this ticket with the table above as
   the "exclude, reason: <specific>" disposition for all 62 and zero CSV writes, updating AC2's residual to
   be explicitly "62, documented, root-caused, not a real gap"; or (ii) re-scoping to actually fix the
   `validate.py` parsing gap (which would require revisiting this ticket's "Out of Scope" line "Any change
   to `validate.py` itself"). This investigation recommends (i), since (ii) contradicts the ticket's
   explicit Out of Scope line and was already deliberately deferred by the sibling schema-gap ticket.

## Anti-Drift Hazards

- **Do not blindly append 62 new rows.** Doing so would violate the ledger's own stated invariant ("exactly
  one row per completed ticket") by creating duplicates for tickets that already have a row (malformed or
  under a different run_id key) — the opposite of what this ticket is meant to fix.
- **Do not "fix" the 39 malformed rows in place under this ticket's scope** — that is a `working_log.csv`
  rewrite of pre-existing content, not an append, and is a materially different, larger change than what
  was scoped and approved.
- **Do not touch `validate.py`** — explicitly out of scope per this ticket and the sibling
  `MONITORING-VALIDATE-SCHEMA-GAP`/`MONITORING-RUNID-JOIN` tickets' established division of labor.
- **Do not touch `runs.jsonl`/`events.jsonl`** — append-only, confirmed zero diff required by AC4.
- If a future pass decides to normalize the malformed rows or extend `validate.py`'s parser, it must be
  scoped as its own ticket (this investigation flags it as a recommended follow-up, not something to fold
  into this ticket's finalize step).
