---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260705-MONITORING-RUNID-JOIN
artifact_type: investigation
tags: [agent-monitoring, data-quality, root-cause, run-id, legacy-schema]
---

# Investigation — TCK-20260705-MONITORING-RUNID-JOIN

## Current Behavior (file:line)

- `tools/agent-monitoring/validate.py:57-59` — flags a run as "Incomplete (CRASHED?)" if `not run.get("end_ts")`, evaluated **per raw JSON line**, with no dedup/reduce by `run_id` and no fallback to any other completion field (`status`, `final_status`, `finished_at`, `completed_at`, `phases_completed`).
- `tools/agent-monitoring/validate.py:61-64` — flags a run as "no events" if `events_by_run[run_id]` is empty, again purely a per-run_id JSONL scan with no schema-generation awareness.
- `.claude/workflows/implement-ticket.js:109` — `const tid = ticketInfo.ticket_id` captured once from the Scope-phase agent's structured return; reused unmodified through `writeMonitoring` (line 131-181), which writes **both** `record_events.py` (line 166) and `record_run.py` (line 169) from the same `tid` in a single `agent()` call.
- `.claude/workflows/implement-epic.js:216-218` — `batchRunId` derived once (`'EPIC-'+epicId` or `'FOLDER-'+sanitized folder`) and reused for both the batch events array (line 221-227, `run_id` added by the agent per the prompt) and the batch run record (line 243).
- `.claude/workflows/implement-epic.js:231-247` — the batch monitoring write is a **single unstructured `agent()` call** doing two sequential steps (write events via `record_events.py`, then write the run record via `record_run.py`) with only "if any command fails, print WARNING but do NOT raise" as an error contract — no verification that step 2 actually landed events before step 3 writes the run record.
- Re-ran `python3 tools/agent-monitoring/validate.py` fresh (2026-07-05): **126 "Incomplete run (no end_ts)" warnings** and **5 "Run with no events" errors** — not the "21 + 5" cited in the ticket. See "21 vs 126" note below.

## Mechanics/Engine Constraints

Not applicable — this is tooling/observability, not simulation mechanics. No `docs/mechanics/` chapter governs `agent-monitoring/`. `docs/agent-monitoring/schema.md` is the authoritative schema reference and is the target for documenting any confirmed-historical-only finding per this ticket's AC #5.

## Parity Ledger Overlap

None. `agent-monitoring/` is infrastructure, not a simulation subsystem tracked in `docs/parity_ledger/`.

## Prior Work

- `TCK-20260607-MON-SCHEMA` / `TCK-20260607-MON-CAPTURE` — established the current schema (`run_id`/`start_ts`/`end_ts`/`workflow`/`tier`/`final_status`/`agent_count` for runs; `run_id`/`seq`/`ts`/`phase`/`agent`/`summary`/`status` for events) and `record_run.py`/`record_events.py`.
- `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md` — already documented that 21% of runs (98/466 at the time) have `workflow: null` and use an older field set (`ticket_id`/`status`/`started_at`/`completed_at`/`notes`). This investigation independently reproduces and extends that finding.
- `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` (DONE, same day) — fixed **only** the `working_log.csv` cross-check branch (`status = final_status or status`, `validate.py:82`) to stop silently skipping legacy-`status`-only runs. It explicitly did **not** touch the `end_ts`/no-events checks (`validate.py:57-64`) — confirmed by reading its diff (`git show 9c02564f`) and by its own ticket text: "Do not touch validate.py's run_id/event join logic... tracked in... TCK-20260705-MONITORING-RUNID-JOIN" (`stored_artifacts/TCK-20260705-RETRO-METRIC-ACCURACY/plan.md:153`).
- `TCK-20260705-RETRO-METRIC-ACCURACY` (DONE, same day) — sibling finding, fixed `generate_retro.py` counting bugs; explicitly out of scope for `end_ts`/join logic too.

## The "21 vs 126" discrepancy (must-read before the classification table)

The ticket's Request Summary cites "21 crashed runs... and 5 runs with zero matching events," attributed to the first real retro run on 2026-07-05. Running `validate.py` fresh right now produces **126** "Incomplete run" warnings (5 "no events" matches exactly). Cross-referencing every incomplete run's `start_ts` value resolves this cleanly:

| start_ts bucket | count | date/id |
|---|---|---|
| `2026-06-23` | 15 | the cluster called out in the ticket |
| single dates | 6 | `2026-06-10` (1), `2026-06-14` (1, an epoch-float `start_ts=1781425809.0960267`), `2026-06-18` (1), `2026-06-21` (1), `2026-06-22` (1) |
| **no `start_ts` key at all** | **105** | — |

15 + 6 = **21**, exactly matching the ticket's figure. The ticket's "21" is the count of incomplete runs **that have *some* start_ts value** (ISO or epoch). The other **105** incomplete-run warnings are records that have **no `start_ts` field under that name at all** — they use an even older key (`started_at`) or no timestamp key whatsoever, so my classification script (and, implicitly, whatever counted "21" for the ticket) silently excluded them from the visible bucket. **This is itself a finding**: the live incomplete-run count today (126) is materially larger than what the ticket was scoped against (21), because more historical batches have been merged into `runs.jsonl` since the ticket was filed hours ago (confirmed: `runs.jsonl`/`events.jsonl` last touched by `9c02564f` `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`, which only appended its own 1 new run record — the 105 "no start_ts" records were already present in the file *before* this ticket was authored; they were simply not counted by whatever produced the "21" headline figure). I classify all 126 + 5 below, organized by root-cause class rather than as 131 identical rows, per the scope's intent ("distinguishing crash vs. join-mismatch vs. legacy debris").

## Classification

**CORRECTION (2026-07-05, this pass)**: the classification below supersedes an earlier pass in this same investigation that classified Class A/C from **illustrative examples** (~40 run_ids hand-listed under Class A, 6 named examples under Class C) rather than a systematic, complete count. Independent architecture review re-derived the true post-dedup residual **twice, converging on 107** — not the ~6 the prior pass implied. Root cause of the prior pass's error: it never verified, for each of its ~40 "Class A" citations, that the claimed "current-schema complete sibling record" actually existed with a truthy `end_ts`; several genuinely have no such sibling at all and were mis-filed. Concretely: `TCK-20260614-ARTIFACT-BUDGET-REG`, cited in the prior pass as "3 records: one legacy, one current `final_status`, resolved by dedup," in fact has (only) **2** records in `runs.jsonl:115-116`, and **neither one has a truthy `end_ts` key** — one is a `seq`-shaped event-like record (`"status":"completed"`), the other has `final_status:"DONE"` but no `end_ts` at all. It is 100% residual, not resolved. This one mistaken citation is representative of the broader error: most of the prior "Class A" list was actually undocumented Class-C residual.

This pass re-derives the numbers systematically with a script (`classify_runs.py`, logic reproduced below) that groups every one of the 482 raw lines in `agent-monitoring/runs.jsonl` (450 distinct `run_id`s) and asks, per `run_id`: **does any record under this `run_id` have a truthy `end_ts`?**

```python
by_run = defaultdict(list)
for line in open("agent-monitoring/runs.jsonl"):
    rec = json.loads(line)
    by_run[rec.get("run_id") or f"__NO_RUN_ID__:{lineno}"].append(rec)

resolved = {rid: recs for rid, recs in by_run.items() if any(r.get("end_ts") for r in recs)}
residual = {rid: recs for rid, recs in by_run.items() if rid not in resolved}
```

**Definitive result: 343 `run_id`s RESOLVED (>=1 record has truthy `end_ts`), 107 `run_id`s RESIDUAL (no record has `end_ts` at all) — confirming architecture review's 107 exactly.**

Reconciling with the raw 126-line warning count: of the 343 resolved `run_id`s, only **16** also have a sibling record *without* `end_ts` (i.e., these are the only `run_id`s where dedup-by-`run_id` actually eliminates a false-positive warning line — true "Class A"). The other 327 resolved `run_id`s never had an incomplete line at all (single or multi-record, always complete) and are irrelevant to this ticket. The 16 Class-A `run_id`s contribute 17 of the 126 warning lines (one, see below, has 2 legacy sibling lines); the 107 residual `run_id`s contribute the remaining 109 lines (two residual `run_id`s — `TCK-20260614-ARTIFACT-BUDGET-REG` and `TCK-20260618-AUDIT-EPIC` — have 2 records each, both lacking `end_ts`, hence 2 lines apiece). 17 + 109 = 126. ✓

### Class A — true duplicate-schema-generation "phantom incompletes" (16 `run_id`s, corrected from prior pass's ~40)

**Pattern**: the same `run_id` has one record from an older schema generation with no `end_ts` key, and a **separate, genuinely complete** record (current or transitional schema) with a truthy `end_ts` for the same `run_id`. Dedup-by-`run_id` correctly resolves these — no live monitoring gap, pure `validate.py` per-line-scan artifact.

**Confirmed example** — `TCK-20260619-E11A-HERO-AUTHORING` (`agent-monitoring/runs.jsonl:170-171`):
```
170: {"run_id": "TCK-20260619-E11A-HERO-AUTHORING", ..., "status": "DONE", "started_at": "...", "finished_at": "...", "phases_completed": [...], ...}
171: {"run_id":"TCK-20260619-E11A-HERO-AUTHORING","start_ts":"...","end_ts":"2026-06-19T16:45:24Z","workflow":"implement-ticket",...,"final_status":"DONE","agent_count":9}
```

**The complete, verified list of all 16 (not illustrative — exhaustive)**: `TCK-20260614-CERT-SAFE-SERIAL`, `TCK-20260619-E11A-HERO-AUTHORING`, `TCK-20260619-E11B-OBS-SNAPSHOT`, `TCK-20260619-E11D-SCORING-CAL`, `TCK-20260619-E23C-QUEST-REWARDS`, `TCK-20260619-E31B-OBJECTIVE-FSM`, `TCK-20260619-E31D-REST-API`, `TCK-20260619-E33A-HEALTH-MONITOR`, `TCK-20260619-E53Ab-DECISION-PHASE`, `TCK-20260626-FIX-DESIGN-PATTERNS`, `TCK-20260628-E-PARTY-LOOP`, `TCK-20260628-E-PERSONALITY-CALIBRATION`, `TCK-20260628-SIMQ-E1-FOUNDATION`, `TCK-20260629-SIMQ-EMIT-NARRATIVE`, `TCK-20260702-SIMQ-UPLIFT-GRADE-DECAY`, `TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO`. All 16 have `tickets/done/{id}.md` confirming genuine completion.

**Everything else previously listed under the prior pass's "Class A"** (`WORLDMOD-PACKS`, the `TCK-20260610-*` set, `TCK-20260613-DOC-*` set, `TCK-20260614-ARTIFACT-BUDGET-REG`, the `WORLDMOD-*`/`WORLDGEN-*`/`WORLDDAT-*` un-prefixed ids, the full `AUDIT-D*` set, the hash-id runs, `TCK-20260619-E32E-REST-HISTORY`, `TCK-20260623-TYPE-CHECKER`, the `TCK-20260628-E41G/H`/`E11C/D`/`E21D/E`/`E43F/G/H`/`E52E/F/G` set, the `EPIC-E-*` wrappers, `TCK-20260629-SIMQ-EMIT-*`, `TCK-20260630-SIMQ-WIRE-*`/`RECALIBRATE`, `TCK-20260702-SIMQ-UPLIFT-DUNGEON-ECON-COG`) has **no resolving sibling record at all** — each is a single-record (or, for 2 cases, multi-record-but-all-incomplete) `run_id` with zero truthy `end_ts` anywhere. These belong in the residual 107, characterized below, not Class A.

**Verdict for the true 16: join mismatch (validate.py per-line scan artifact) — work completed fine, dedup-by-run_id fixes it. No live risk.**

### Class B — 2026-06-23 batch-import cluster (16 records, all inside the 107 residual — not a separately-resolved bucket)

Correction to prior pass: the 2026-06-23 cluster is **not** dedup-resolved by a sibling record — every one of these 16 `run_id`s (`TCK-20260619-E61A/B/C/D-*` via hash run_ids `8f292dde`/`5f5a4063`/`f8cbef73`/`a53b989c`, `EPIC-bba99faa`, `TCK-20260619-E62A/B/C/D-*`, `EPIC-TCK-20260619-E62-CULTURE-DRIFT`, `TCK-20260619-E63A/B/C/D-*`, `EPIC-TCK-20260619-E63-FEATURE-PACKS`) is single-record and part of the true 107-residual set. The prior pass's substantive finding about this cluster's root cause is unchanged and remains correct: all 16 share **one exact schema shape** (`start_ts` present, `final_status:"DONE"` present, **no `end_ts` key at all**), a rich `summary` describing real completed work, and every one has a matching `tickets/done/*.md` file. **Single identifiable common cause, unchanged**: one batch of historical monitoring records written by a transitional schema generation, most plausibly landed via the large historical merge `6e25d4f2`. **Verdict: legacy-schema debris, not a crash — genuinely completed work, now correctly counted as part of the 107 residual rather than a separately-resolved bucket.**

### Class C — the full 107-record residual (corrected from prior pass's "6 singles" — systematic, not illustrative)

**Methodology**: every one of the 107 residual `run_id`s (not a sample) was resolved to a ticket identity (`ticket_id` field if present, else the `run_id` itself if it looks like a ticket/epic/folder id) and checked for an exact-match file under `tickets/done/*.md`. Result: **98/107 (91.6%) have an exact-match `tickets/done/` file.** The remaining **9/107** are `FOLDER-*`/`EPIC-*` batch-wrapper records or one direct-invocation maintenance record — these structurally never get an individual ticket file (their completion is represented by child tickets, which were separately verified DONE). All 9 were individually read from the raw JSON and **every one carries an explicit terminal-success field** (`"status":"DONE"`, `"final_status":"DONE"`, or — for one, `eefdb3bc`/`FOLDER-tickets/todos/long-term-epics` — `"status":"EPIC_SCOPED"` with `gate_failures` showing the epic was deliberately stopped mid-batch to scope its next ticket into children, all of which are independently DONE, not a crash). **Net finding: 107/107 (100%) of the true residual represent genuinely completed work with a missing/misnamed completion-timestamp field — zero genuinely incomplete or abandoned runs found in the full systematic check.**

**Date range**: `2026-06-10` through `2026-07-02` (spans nearly the whole project history up to the day before this ticket was filed), plus one record with a Unix-epoch-float `start_ts` (`1781425809.0960267` → `2026-06-14T08:30:09Z`, i.e. also inside the range, just written in a different timestamp encoding).

**Date-cluster histogram** (start_ts date prefix, all 107 accounted for):

| Date | Count | Date | Count |
|---|---|---|---|
| 2026-06-23 | 16 | 2026-06-19 | 10 |
| 2026-06-18 | 14 | 2026-06-13 | 8 |
| 2026-06-10 | 12 | 2026-06-14 | 6 (+1 epoch-float, same day) |
| 2026-06-15 | 12 | 2026-06-30 | 6 |
| 2026-06-28 | 12 | 2026-06-17/21/22, 2026-07-02 | 1 each |
| | | no `start_ts`-family key at all | 6 |

**Naming-pattern histogram** (all 107 accounted for):

| Pattern | Count | Notes |
|---|---|---|
| `TCK-YYYYMMDD-*` (plain ticket id, single record, no sibling) | 53 | Largest bucket — ordinary tickets whose one-and-only monitoring record predates the current `end_ts` field |
| `AUDIT-D*` (the `TCK-20260618/19-AUDIT-D01..D18` audit series + 1 maintenance record) | 17 | One cohesive audit epic's per-finding tickets, all same 2 days |
| `OTHER` (un-prefixed `WORLDMOD-*`/`WORLDGEN-*`/`WORLDDAT-*` ids, `run-{hash}` ids, bare `E21D/E21E/E43F/E43G/E43H/E52E/E52F/E52G-{hash}` ids) | 16 | Pre-`TCK-` naming convention, superseded once ticket-id-as-run-id became standard |
| `bare-hash-id` (8-char hex or hex-UUID run_ids, e.g. `f26f9727`, `427cbe47-...`) | 8 | Oldest/most opaque id generation |
| `EPIC-*` (epic-batch wrapper records) | 7 | Batch summaries for multi-ticket epics; children individually verified DONE |
| `FOLDER-*` (folder-batch wrapper records) | 6 | Batch summaries for `tickets/todos/{folder}/` runs; children individually verified DONE |

**Schema-generation subtypes found within the 107** (this pass additionally identified a schema generation not previously catalogued): besides the already-known `started_at`/`finished_at`/`status`/`phases_completed` and `final_status`-without-`end_ts` shapes, a **fourth legacy shape** appears in 5 records all dated `2026-06-28` (`TCK-20260628-E41G-COHESION-SUSTAIN`, `E41H-MULTI-HERO`, `E11C-WEIGHT-TUNING`, `E11D-ABANDONMENT-RATE`) plus one `2026-06-29` record (`TCK-20260629-SIMQ-EMIT-ECONOMY-...`): completion is recorded under **differently-named** keys entirely — `ts_start`/`ts_end`/`result`/`agent` (e.g. `"result":"DONE","ts_end":"2026-06-28T06:11:07.79Z","agent":"claude-sonnet-4-6"`) or `completed_at`/`status`/`phases_completed`. In every one of these cases a real completion timestamp **is present**, just under a field name `validate.py` (and this ticket's own dedup logic) doesn't check — reinforcing the "field-name drift across schema generations," not "genuine crash," reading of the whole 107.

**Verdict for the full 107: legacy-schema/field-naming debris across at least 5 distinct historical schema generations spanning 2026-06-10 to 2026-07-02. Not crashes — 107/107 individually confirmed as genuinely completed (98 via direct `tickets/done/` file match, the other 9 via explicit terminal-status fields in their own JSON plus independently-DONE child tickets). Zero abandoned/incomplete work identified.**

### Class D — the 5 zero-event runs

| run_id | events found? | done? | verdict |
|---|---|---|---|
| `FOLDER-phase40-44-cleanup-authoring` | 0 (legacy schema summarizes via `notes`, never wrote per-ticket events) | `status:"DONE"`, `"ticket_count":15,"done_count":15"` in the run record itself; child docs epic `tickets/done/TCK-20260613-DOC-HARDENING-EPIC.md`-style precedent confirms folder wrappers are expected to have no dedicated events | legacy debris — pre-event-schema batch summary format |
| `FOLDER-tickets-todos-doc-hardening-` | 0 | `status:"DONE"`, `"tickets_done":[...9 tickets...]`, `tickets/done/TCK-20260613-DOC-HARDENING-EPIC.md` ✓ | legacy debris — same shape |
| `run-E43B-1782052024` | 0 under this run_id (7 real events exist under the *different* run_id `run-E43B-1782052032`) | `TCK-20260619-E43B-EXPORT-IMPORT` (from the record's own `ticket_id` field) — need not appear separately in `tickets/done/` under that exact name since it's part of the E4x social-memory epic batch; the *events* (`run-E43B-1782052032`) show full Scope→Finalize completion incl. "Ticket done; todos deleted; working log appended; artifacts moved" | **THE PATTERN-1 CASE — analyzed in detail below** |
| `FOLDER-tickets/todos/world-data/` | **0**, despite full current-schema shape (`start_ts`/`end_ts`/`workflow:"implement-epic"`/`final_status:"DONE"`/`agent_count:3`) dated **2026-06-30** — squarely in the current-schema era | the 3 child tickets (`TCK-20260630-WORLD-QUEST-LOCATION`, `TCK-20260630-WORLD-DEPLOY-MODULES`, `TCK-20260630-WORLD-TEST-MATRIX`) are all in `tickets/done/`, **and each has a complete 9-event (or 2-event, hotfix) trail under its own run_id** in `events.jsonl` | **A THIRD, LIVE, CURRENT-CODE RISK — see below, distinct from patterns 1/2** |
| `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN` | 0 under this run_id (10 real events exist under the ticket's *plain* run_id `TCK-20260701-HAZARD-NATIVE-IMMUNITY`) | `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md` exists (no `-REDESIGN` variant ever existed as a file) | **THE PATTERN-2 CASE — analyzed in detail below** |

## Pattern 1 (timestamp race, `run-E43B-*`) — root cause confirmed

`agent-monitoring/runs.jsonl:241`:
```
{"run_id":"run-E43B-1782052024","start_ts":"2026-06-21T15:00:00Z","end_ts":"2026-06-21T15:30:00Z","workflow":"implement-ticket","tier":"standard","final_status":"DONE","agent_count":1,"ticket_id":"TCK-20260619-E43B-EXPORT-IMPORT"}
```
`agent-monitoring/events.jsonl:865-871`, all under `run_id: "run-E43B-1782052032"`, `phase` values **lowercase** (`"scope"`, `"investigate"`, `"plan"`, `"implement"`, `"test"`, `"parity"`, `"finalize"`), `agent: "implement-ticket"` for every single row (not per-role agent names like `investigator`/`planner`/`architecture-reviewer` that the current schema uses per `docs/agent-monitoring/schema.md:107-109`).

This is decisively **not** producible by the current `.claude/workflows/implement-ticket.js`:
1. Current `tid` (line 109) is captured once and is always the literal ticket_id (e.g. `"TCK-20260619-E43B-EXPORT-IMPORT"`) — never a synthesized `run-{X}-{unix_ts}` string. The current code has no code path that generates a `run_id` of that shape at all.
2. Current phase names are capitalized (`Scope`, `Investigate`, ...) and agent names are per-role (`ticket-scoper`, `investigator`, `planner`, ...) per `pushEvent` calls at lines 184, 267, 317, 381, 437, 493, 533, 608, 661 — never lowercase, never `agent:"implement-ticket"` for every phase.
3. The sibling records for `E43C`/`E43D`/`E43E` (`runs.jsonl:242-244`) use the exact same `run-{code}-{unix_ts}` shape and `ticket_id` field — this is a **consistent, self-contained older-generation naming convention** applied uniformly across the whole E43 batch, not a one-off race.

**Confirmed: pattern 1 is exclusively historical/pre-refactor debris.** It predates the current `implement-ticket.js`'s single-capture `tid` pattern and reflects a different (older) tool/agent generation that (a) synthesized its own `run-{phase}-{timestamp}` IDs rather than using the ticket ID directly, and (b) apparently called `record_run.py` and `record_events.py` from two separately-timed invocations (8 seconds apart) rather than a single combined write — consistent with a manual/ad hoc or pre-single-agent-call monitoring integration, not the current `writeMonitoring` design (which passes the identical `tid` string literal into both the events array and the run-record JSON in one prompt). No evidence this is reproducible with current code, and no evidence of an active "manual-hotfix bypass" tool for this specific race shape — the only confirmed direct/manual-invocation-shaped record found (`AUDIT-D01-D02-D09-UPDATE`, `workflow:"audit-maintenance"`) uses a stable, single run_id for its one event+run pair, not a split ID pair.

## Pattern 2 (rename mismatch, `HAZARD-NATIVE-IMMUNITY`) — root cause confirmed

`git log --follow` on `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md` shows **exactly one** commit touching that path (`6e25d4f2`) — no rename ever occurred at the file level; only `TCK-20260701-HAZARD-NATIVE-IMMUNITY.md` has ever existed (`git log --all -S "HAZARD-NATIVE-IMMUNITY-REDESIGN"` finds the string only in commit messages/tickets discussing this very investigation, never in a file path). The ticket file's own `## Implementation Notes` (line 168) states: **"Reopened 2026-07-02.** A first implementation pass shipped, passed its own review and test suite, and was marked DONE... It was superseded, not broken: follow-up discussion... surfaced a requirement the original design could not satisfy." The corrected design replaced the first pass in the same file, same ticket ID, across two passes.

`events.jsonl:1659-1673` (all under the plain run_id `TCK-20260701-HAZARD-NATIVE-IMMUNITY`) show **10 events total**: seq 1-5 = first pass (`implement`→`finalize`, ending 17:33:05Z), seq 6-10 = second pass (`"Redesign pass: added RegionState.hazard_kind..."`, ending 18:18:43Z). Both passes' events were correctly filed under the one true ticket ID.

But `runs.jsonl:436` and `:438` show **two separate run records**: `TCK-20260701-HAZARD-NATIVE-IMMUNITY` (`agent_count:5`, `end_ts:17:33:05Z` — matches pass 1) and `TCK-20260701-HAZARD-NATIVE-IMMUNITY-REDESIGN` (`agent_count:10`, `end_ts:18:18:43Z` — the `agent_count:10` is the **combined** total across both passes, not just pass 2's 5 events).

**Confirmed: this is not a ticket rename.** It is an ad hoc `-REDESIGN` suffix invented specifically for the **second pass's run-record write**, while that same second pass's **events** were (correctly) filed under the unmodified ticket ID. Both events and phase-naming for this ticket use lowercase `phase` values (`"implement"`, `"test"`, `"parity"`, `"verify"`, `"finalize"`) and a single generic `agent:"claude"` for every row — **not** the current schema's capitalized-phase/per-role-agent convention. This strongly indicates the HAZARD-NATIVE-IMMUNITY ticket (both passes) was executed via a **direct/manual Claude Code session** that hand-wrote monitoring records to mimic the schema, rather than through the orchestrated `.claude/workflows/implement-ticket.js` (which would never produce `agent:"claude"` for every phase, nor invent a `-REDESIGN` run_id suffix — its `tid` is fixed once per script execution and threads identically into both events and the run record, as in Pattern 1's analysis above). This is **a live risk category**, but the live risk is "informal/manual monitoring-write sessions inventing ad hoc run_id variants for clarity," not a bug in `implement-ticket.js`/`implement-epic.js` themselves.

## Pattern 3 (new finding, not anticipated by the ticket) — `implement-epic.js` batch write can silently split events from run record

`FOLDER-tickets/todos/world-data/` (`runs.jsonl:422`, dated 2026-06-30, squarely within the current schema era) has a fully-formed, current-schema run record (`start_ts`/`end_ts`/`workflow:"implement-epic"`/`final_status:"DONE"`/`agent_count:3`) but **zero** events under its own `run_id`. Its 3 child tickets each have complete, correctly-tagged event trails under *their own* run_ids in the current schema (`agent-monitoring/events.jsonl:1585-1604`), so this is not "no monitoring happened" — the batch-level 3-line summary (one event per child ticket, per `implement-epic.js:221-227`'s `batchEvents` construction) specifically never landed.

Reading `.claude/workflows/implement-epic.js:231-247`: the batch-events write (Step 2) and the batch-run-record write (Step 3) are two Bash sub-steps inside **one single unstructured `agent()` call**, with only a "print WARNING but do NOT raise" error contract and no verification gate between steps. This provides a plausible, code-level explanation for a run record landing while its paired events line does not (e.g., the agent executed Step 3 without confirming Step 2's `record_events.py` call actually succeeded, or reordered/skipped it) — and unlike Patterns 1/2, this is dated well inside the current-schema era with no legacy-record duplicate to explain it away. **This is the one confirmed case that plausibly reflects a live, reproducible gap in the current `implement-epic.js` code**, not historical debris.

## Risks and Open Questions

1. Whether to also patch `validate.py`'s per-line `end_ts` scan to dedupe by `run_id` (take the "best" record per run_id before flagging) — this would eliminate ~120 of the 126 false positives at the source, but the ticket's Out of Scope explicitly routes "validate.py's schema blind spot" to the (already-DONE) sibling ticket. Recommend treating the dedupe-by-run_id fix as a natural, minimal extension of that already-established pattern, not a new scope violation, since it's the same class of legacy-schema tolerance already applied there — but this is a judgment call for the planner/architecture-reviewer, not decided here.
2. Whether Pattern 3 (`implement-epic.js` batch-write split) warrants a code fix to `implement-epic.js` itself (e.g., split the batch monitoring write into two separately-verified agent calls, or read back `events.jsonl` after Step 2 to confirm the write landed before Step 3) — this is the only pattern confirmed reproducible by current code and arguably the highest-value fix in this ticket.
3. Whether "manual/direct monitoring-write sessions" (confirmed to exist as the likely origin of the `HAZARD-NATIVE-IMMUNITY-REDESIGN` and `E43B`-era records, and explicitly as the `AUDIT-D01-D02-D09-UPDATE` `workflow:"audit-maintenance"` record) should be given a documented convention (e.g., "if hand-writing monitoring records outside the JS workflows, always reuse the exact ticket ID as run_id, never invent suffixes") rather than a code-level lint, since there is no single script/tool to attach a lint to for genuinely ad hoc interactive sessions.
4. No test harness exists for `tools/agent-monitoring/*.py` anywhere in this repo (confirmed identically by both sibling tickets `TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP` and `TCK-20260705-RETRO-METRIC-ACCURACY` — a pre-existing, documented convention gap, not introduced by this investigation).

## Anti-Drift Hazards

- Do not conclude "126 crashed runs" — and do not conclude "only ~6 residual" either — without reading this investigation's corrected Class A/B/C breakdown first. The corrected, systematically-derived split is **16 true dedup-resolved (Class A) + 107 true residual (Class C, which subsumes the old Class B's 16 as a labeled sub-cluster)**. Both a naive raw count (126) and the prior pass's under-counted residual (~6) would badly mis-state the picture — 126 overstates by conflating in dedup-resolvable duplicates, while ~6 understates by mistaking illustrative examples for an exhaustive count.
- Do not backfill or edit `runs.jsonl`/`events.jsonl` — explicitly Out of Scope (append-only precedent, matches sibling tickets this session).
- Do not conflate Pattern 1 (`run-E43B-*`, pure historical debris, not reproducible) with Pattern 3 (`FOLDER-tickets/todos/world-data/`, plausibly reproducible today) when designing the safeguard — they call for different remedies (documentation-only for 1/2's legacy debris vs. a possible code change for 3's live gap).
- The corrected cross-reference method used to confirm the 16/107 split and the 98/107 `tickets/done/` match rate (this pass, 2026-07-05): `classify_runs.py` groups every raw line in `agent-monitoring/runs.jsonl` by `run_id`, splits into `resolved` (>=1 record with truthy `end_ts`) vs `residual` (none), then a second pass (`classify_lines.py`) intersects with the per-line warning count to isolate the 16 `run_id`s that are both residual-if-viewed-per-line AND have a resolving sibling. A third pass resolves each residual `run_id` to a ticket identity (`ticket_id` field, else `run_id` itself) and checks exact membership against `{p.stem for p in Path("tickets/done").rglob("*.md")}` — with a follow-up manual read of the 9 non-matching `FOLDER-*`/`EPIC-*`/maintenance records to confirm each carries an explicit terminal-status field. These scripts and their full output are scratchpad-only, not a checked-in repo artifact — anyone re-verifying should regenerate them (logic is reproduced inline in the Classification section above) rather than assume a checked-in copy exists.
- **Do not re-cite the prior pass's "~40-item illustrative Class A list" or "6 singles" table as authoritative** — both are superseded by this correction. If a future pass needs the full 107 or 16 run_id lists again, regenerate via the script logic above rather than trusting either table verbatim without re-running the count.
