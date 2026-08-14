---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-EPIC-STALENESS-CHECK
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement, workflows, hooks]
---

# Investigation — TCK-20260710-EPIC-STALENESS-CHECK

## Current Behavior

### How epic tickets are structured today
Two epic shapes exist, both discoverable the same way `implement-epic.js` already discovers them
(`.claude/workflows/implement-epic.js` lines 62–141):

1. **`epic_id` mode** — a single ticket file (in `tickets/inprogress/` or `tickets/done/`) with
   `## Tier` → `epic`, whose `## Related Tickets` section lists child ticket IDs in prose. Example:
   `tickets/todos/obs-isolation/TCK-20260702-OBSISO-EPIC.md` line 47:
   `TCK-20260702-OBSISO-TRACE-ASYNC, TCK-20260702-OBSISO-BROKER-CONFIG, TCK-20260702-OBSISO-WORKER-PARITY, TCK-20260702-OBSISO-ISOLATION-PROOF`.
2. **`folder` mode** — a `tickets/todos/{folder}/` directory containing a `SEQUENCE.md` (authoritative
   child-ticket ordering, parsed for `TCK-...` IDs — `implement-epic.js` lines 71–81) plus one or more
   `TCK-*.md` child ticket files directly in the folder. `tickets/todos/obs-isolation/` is actually
   a **hybrid**: it has both a `SEQUENCE.md` *and* an epic ticket file
   (`TCK-20260702-OBSISO-EPIC.md`) sitting in the same folder as its four children
   (`TCK-20260702-OBSISO-TRACE-ASYNC.md`, `-BROKER-CONFIG.md`, `-WORKER-PARITY.md`,
   `-ISOLATION-PROOF.md`) — confirmed via `ls tickets/todos/obs-isolation/`. This is the live example
   this ticket's AC targets, and it demonstrates candidate discovery needs to check **both** signals
   (epic-tier ticket file presence AND `SEQUENCE.md` presence) in the same folder, not just one.

Currently, as of this investigation (2026-07-10), `tickets/inprogress/` contains zero epic-tier
tickets (both open tickets there — this one and `TCK-20260710-FEATURE-FLAGS-GUIDE` — are `standard`
tier), and `tickets/todos/` contains exactly one `SEQUENCE.md`-bearing subfolder: `obs-isolation/`.
**There is currently no live, non-stale epic anywhere in the repo to use as a real "not flagged"
control case** — the AC's requirement for "at least one non-stale control case, real or synthetic"
will need a synthetic fixture (a temp-directory epic ticket + recent working_log/runs.jsonl rows),
not a second real example.

### How `retro_nudge_hook.py` detects "overdue" via mtime comparison
`tools/agent-monitoring/retro_nudge_hook.py` (92 lines) is the pattern to mirror:
- `_last_dated_retro_mtime()` (lines 29–33): globs `agent-monitoring/retro/RETRO-*.md` excluding
  `RETRO-ALL.md`, takes `max(p.stat().st_mtime for p in dated)`; returns `0.0` if none exist
  ("no dated report has ever existed" == "threshold already crossed").
- `_count_done_since(cutoff)` (lines 36–59): reads `agent-monitoring/runs.jsonl` line by line,
  tolerates both current (`workflow`/`final_status`/`start_ts`) and legacy (`agent`/`status`/
  `started_at`) field names, parses ISO timestamps (`.replace("Z", "+00:00")`), counts records past
  `cutoff`.
- Main body (lines 62–91): reads hook stdin JSON payload for `session_id`, short-circuits via a
  state file (`.claude/.retro_nudge_state.json`) if this session already fired (or, absent a
  `session_id`, a 1-hour cooldown), computes `count`, and if `count >= THRESHOLD` (5) prints a
  `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}` block.
  Wrapped in a bare `try/except: pass` at module scope — **any** exception anywhere silently
  swallows to no output, never raises, never blocks.
- Wired in `.claude/settings.json` at the second `PostToolUse` `"matcher": "*"` block (lines 102–110):
  `python3 tools/agent-monitoring/retro_nudge_hook.py 2>/dev/null || true` — the `|| true` is a second,
  belt-and-suspenders non-failure guarantee on top of the script's own try/except.

### How epic tickets/folders are identified vs. regular tickets
No existing code has a general-purpose "list all open epics" function — `implement-epic.js`'s
Discover phase is *reactive* (given a `folder=` or `epic_id=` argument, it reads that one target);
there is no scan-all-epics primitive to reuse directly. The new check must implement its own
discovery: (a) grep `## Tier` → `epic` across `tickets/inprogress/*.md`, and (b) glob
`tickets/todos/*/SEQUENCE.md` and read the sibling folder for an epic-tier `TCK-*.md` file (per the
hybrid `obs-isolation/` shape above — cannot assume `SEQUENCE.md` presence alone means epic, though
in the one real example it also happens to contain an epic ticket).

### `working_log.csv` real-data shape (relevant to "activity" matching)
`tickets/working_log.csv` header: `timestamp,ticket_id,title,status,summary,artifacts_path` (6
columns — the canonical shape, 760/1013 rows). But **253 rows (25%) deviate** from 6 columns:
4-col (6), 5-col (37), 7-col (45), 8-col (60), 9-col (46), 10-col (27), 11-col (12), 12-col (9),
13-col (4), 14-col (3), 17-col (2), plus 2 fully empty (0-col) rows — confirmed live via
`awk -F',' '{print NF}' tickets/working_log.csv | sort | uniq -c`. This matches the "83 non-canonical
rows across 7 shapes" figure `idea_agent_bookkeeping_determinism.md` line 103 cites for a *different*
follow-up ticket's narrower definition of "non-canonical" — the raw column-count spread here is
larger because it includes quoted-comma fields inflating naive `awk -F','` counts, not necessarily
genuinely malformed rows. Either way: a naive CSV column-position read (e.g. assuming column 2 is
always `ticket_id`) is unsafe; `csv.DictReader` (as `validate.py` already does, line 174) is the
correct approach, keyed by dict field name not position.

### Confirmed live data for the two motivating examples
- `TCK-20260702-OBSISO-EPIC` (`tickets/todos/obs-isolation/`): **zero** matches for `obsiso` (case
  insensitive) in `tickets/working_log.csv`, `agent-monitoring/runs.jsonl`, or
  `agent-monitoring/events.jsonl` — confirmed via direct grep. Folder dated 2026-07-02; today is
  2026-07-10; **8 days** of zero child-ticket activity. This is the ticket's live stale-epic proof.
- `TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC`: already `DONE` and moved to `tickets/done/simq-deep-coverage/`
  — its own `working_log.csv` row (2026-07-09T09:00:12Z) explicitly narrates the historical failure
  mode ("this epic ticket itself was left open in tickets/todos/ ... discovered while auditing"). Not
  usable as a *live* test fixture (already closed) but is directly-quoted historical evidence.
- `agent-monitoring/events.jsonl` seq 2434: the sole `"agent":"epic-closure"` event
  (`run_id: FOLDER-tickets-todos-agent-infra-hardening`, ts `2026-07-09T03:00:19Z`) — confirmed this
  is **not** a registered `implement-epic` agent: `tools/agent-monitoring/vocabulary.py`'s
  `WORKFLOW_AGENTS["implement-epic"]` = `{"implement-ticket"}` only. `"epic-closure"` does not appear
  anywhere in `vocabulary.py`, confirming the ticket's framing: this was an ad hoc manual invocation,
  not a scripted `implement-epic.js` phase. (It would register as a `agent_drift` warning in
  `validate.py`'s `compute_drift_report` if checked, though that's out of this ticket's scope to fix.)

## Mechanics / Engine Constraints
None. This is Claude-agent-orchestration tooling (`layer: ai` — this repo's tag registry note:
"layer:ai means the Claude agent system, not gameplay AI/cognition"), not simulation mechanics. No
chapter in `docs/mechanics/` or contract in `docs/engine/` governs ticket/epic bookkeeping.

## Parity Ledger Overlap
None. Confirmed by direct precedent: the sibling ticket `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`
(`stored_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/investigation.md` line 67) already
searched all 8 canonical `docs/parity_ledger/*.yaml` files for `hook`/`agent-monitoring`/`gate_check`
and found only unrelated simulation-engine "hook" homonyms (PERSISTENCE-phase hooks, CampaignOrchestrator
hooks, SIMQ narrative-pillar hooks — not Claude Code agent hooks). The same conclusion applies here:
no parity ledger entry needs updating, and none should be added.

## Prior Work
- **`tools/agent-monitoring/retro_nudge_hook.py`** (`TCK-20260704-RETRO-LOOP-ENFORCEMENT`, done,
  hotfix tier, no staging artifacts) — the direct pattern to mirror. Its own Completion Summary and
  Test Summary explicitly state: **"No automated test suite exists for `.claude/` hooks in this repo...
  verification here is manual/behavioral, matching existing precedent for this class of file."** This
  matters directly for Test Plan: the *hook wrapper* (stdin-JSON glue) has no pytest precedent, but
  this ticket's own AC explicitly requires unit tests — meaning the staleness-*logic* must be
  factored into plain, importable, pytest-testable functions (mirroring `validate.py`'s
  `compute_drift_report(runs, events) -> str` pattern, which *is* directly unit-tested), with only a
  thin, untested stdin-glue wrapper matching the existing hook-script precedent.
- **`agent-monitoring/events.jsonl` seq 2434 / `epic-closure` agent** — the only historical
  epic-closure-adjacent event, confirmed ad hoc (see Current Behavior above). No reusable code exists
  from it; it was a manual agent invocation during `FOLDER-tickets-todos-agent-infra-hardening`'s
  closure pass, not a script.
- **`tools/agent-monitoring/validate.py`** — precedent for scanning `runs.jsonl`/`working_log.csv`
  cross-references (lines 172–189: builds a `log_tids` set via `csv.DictReader`, cross-checks against
  `runs_by_id`). Directly reusable pattern for resolving child-ticket-ID → activity-timestamp joins,
  though this ticket needs the *reverse* query shape (given a ticket ID, find its most recent
  timestamp) rather than validate.py's existing shape (given a run, check ticket exists in log).
- **`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`** (stored, done) — established there is **zero
  precedent anywhere in this repo for a hook that denies/blocks** (no `permissionDecision`, no
  documented exit-code-2 pattern) — every existing gate (`DOD_BLOCKED`, `FINALIZE_INCOMPLETE`) is
  implemented via `implement-ticket.js`'s own `return {status: ...}` control flow, not via
  `.claude/settings.json` hook denial. Directly reinforces this ticket's Out-of-Scope "no hard block"
  decision and confirms the *mechanism* (advisory `additionalContext` only) is the only proven option
  if implemented as a `.claude/settings.json` hook.
- **Related-but-ruled-out siblings** (per the ticket's own "Related Stored Artifacts" section,
  independently re-confirmed): `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`,
  `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`, `TCK-20260708-AGENT-COST-OBSERVABILITY` — all
  agent-infra-hardening-epic siblings, none address epic-level staleness detection specifically.

## Risks and Open Questions
- **Staleness threshold default is unjustified by any existing precedent.** No prior ticket picked a
  "days since last activity" number for anything comparable (the retro-nudge hook uses a *count*
  threshold — 5 completed runs — not a *time* threshold). The two real calibration examples: OBSISO
  is stale at 8 days (zero activity since 2026-07-02); SIMQ-DEEP-COVERAGE-EPIC's own gap (dated
  implicitly by its children's completion, closed 2026-07-09, discovered stale same day) does not
  give a clean "days idle" number since the epic ticket itself carries no explicit last-touched
  timestamp distinct from `date:` (frontmatter creation date). Plan phase must pick and justify a
  concrete window (5–7 days per the ticket's own suggestion) — 8 days of real zero-activity data is
  the only anchor available; a shorter window (e.g. 3 days) risks false-positives on legitimately
  paused-but-not-abandoned epics with no counter-example to validate against.
- **"Child-ticket activity" timestamp source ambiguity.** The ticket's own Scope text specifies
  checking both `working_log.csv` rows and `runs.jsonl` records, taking the most recent across both.
  This is the right call per this investigation — `runs.jsonl` alone would miss the SIMQ-DEEP case
  style (working_log row exists via a manual housekeeping pass, no corresponding runs.jsonl row for a
  bespoke closure), and `working_log.csv` alone would miss in-progress runs that haven't reached
  Finalize yet. Confirmed both sources should be read; git log on the ticket file (mentioned in the
  investigator's own briefing as a third candidate) was **not** included in the ticket's actual Scope
  and should not be added without a documented reason — it would catch drive-by ticket-file edits
  (e.g. a stray typo fix) as false "activity," which the other two sources don't risk.
- **Malformed `working_log.csv` rows could produce false negatives (activity missed).** Confirmed
  live: 25% of rows deviate from the 6-column canonical shape. If a child ticket's own row is one of
  these non-canonical shapes and its `ticket_id`/`timestamp` fields don't land in the expected
  `csv.DictReader` keys, the check could wrongly treat that ticket as having no activity, prematurely
  flagging a genuinely-active epic as stale. Mitigation: use `csv.DictReader` (not raw column-index
  splitting) exactly as `validate.py` already does, and treat any row where `ticket_id` doesn't
  cleanly resolve as "unknown, do not count as evidence of staleness OR activity" rather than
  silently miscounting it either way.
- **Distinguishing a genuinely-paused epic from a stale/abandoned one is not solvable by this check
  alone.** The check can only surface a signal (time since last child activity); it cannot know
  *intent* (deliberately deprioritized vs. forgotten). This is explicitly why the ticket's Out of
  Scope correctly excludes any hard block or auto-closure — a false-positive nudge is low-cost
  (advisory text), a false-positive hard block or auto-close would not be.
- **Whether both `tickets/inprogress/` epic tickets AND `tickets/todos/**/` SEQUENCE.md folders need
  scanning: yes, both**, per the live data — `tickets/inprogress/` currently has zero epic-tier
  tickets (so today's check would trivially skip it), but the check must not hardcode "only scan
  todos/" since a future epic could reasonably live directly in `tickets/inprogress/` under
  `epic_id` mode without ever having a `todos/` folder or `SEQUENCE.md`. Both discovery paths from
  `implement-epic.js` (lines 62–141) must be mirrored.
- **No non-stale control case currently exists in the live repo** (see Current Behavior). AC #1's
  "does NOT flag any currently-open epic ticket that has recent child activity" cannot be verified
  against real repo state today — it will need either a synthetic fixture or to wait/create one.
  Flagging this explicitly rather than assuming Plan/Implement can find a live example.
- **Idea-doc precondition** (already flagged in the ticket itself, restated here per the investigator
  briefing's explicit ask): the ticket proceeds without a prerequisite `idea_epic_staleness_check.md`
  in `docs/plans/agent_infrastructure/`. Confirmed independently: neither
  `idea_agent_bookkeeping_determinism.md` nor its three siblings in that folder mention epic
  staleness anywhere. This is a scoper decision already made, not something for Investigate to
  re-litigate — noted here only because the investigator briefing asked risks to surface it as an
  open question if evidence disagreed; evidence here agrees with the ticket's own conclusion.

## Anti-Drift Hazards
- **Do not make this a hard block.** Confirmed by direct precedent
  (`TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`'s investigation): zero hooks in this repo deny or
  block a tool call; every existing gate lives in `implement-ticket.js`'s own control flow. A
  `.claude/settings.json` hook for this check has no mechanism to block anything even if someone
  wanted it to — it can only inject `additionalContext`, exactly like `retro_nudge_hook.py`. Do not
  attempt exit-code-2 or `permissionDecision` denial patterns; there is no precedent and CLAUDE.md's
  "monitoring write failure must never fail the workflow" hard rule plus this ticket's own Out of
  Scope both point the same direction.
- **Do not mutate any ticket file.** The check is read-only. It must never write `Status`/`phase`
  fields, never auto-close an epic, never move files. This is explicit in the ticket's Out of Scope
  and is directly testable (AC: "unit test that asserts no ticket file bytes change after running the
  check").
- **Do not fix the two concrete stale-epic instances as part of this ticket.** SIMQ-DEEP-COVERAGE-EPIC
  is already closed; OBSISO-EPIC is explicitly out of scope to remediate here — implementing the
  check must not accidentally also "helpfully" close, move, or edit `tickets/todos/obs-isolation/`
  while building/testing against it as a fixture. Any test exercising the real `obs-isolation/`
  folder must be read-only (confirmed via the same "no byte changes" test as above, applied
  specifically to that folder's files).
- **Do not retrofit `implement-epic.js` itself.** Out of Scope explicitly excludes wiring this check
  as an inline step of `implement-epic.js`'s existing Discover/Implement/Report phases. Keep this as
  an independent, periodic/queryable scan — a new script and/or hook, not a new phase in that
  workflow file.
- **Do not silently duplicate `WORKFLOW_AGENTS`/`WORKFLOW_PHASES` vocabulary.** If the new check ever
  needs to validate agent/phase names (it likely doesn't — it only reads timestamps and ticket IDs),
  it must import from `tools/agent-monitoring/vocabulary.py`, not hardcode its own copy — this repo
  has an explicit single-source-of-truth precedent and test guard
  (`tests/tools/test_validate_agent_monitoring.py`) against exactly this kind of drift.
- **Do not assume `working_log.csv` column positions.** Use `csv.DictReader` keyed by field name
  (`ticket_id`, `timestamp`), matching `validate.py`'s existing approach — a naive split-by-comma
  approach will silently misread 25% of real rows given the confirmed column-count variance.
- **Do not widen scope into cross-retro trend detection.** The ticket's Out of Scope explicitly
  excludes the sibling idea (comparing consecutive `RETRO-<week>.md` reports for drift) — a
  superficially similar advisory-channel mechanism but a genuinely different data source and
  question. Keep this check scoped to per-epic child-activity staleness only.
