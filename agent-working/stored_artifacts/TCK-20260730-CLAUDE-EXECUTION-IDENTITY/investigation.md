---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CLAUDE-EXECUTION-IDENTITY
artifact_type: investigation
tags: [ai, workflows, agent-monitoring, observability, testing]
---

# Investigation — TCK-20260730-CLAUDE-EXECUTION-IDENTITY

## Current Behavior

### Summary of the gap

`.claude/workflows/implement-ticket.js` (1417 lines) writes `run_id`, `seq`, `phase`, `agent`
into the `.claude/current_run` sidecar and into `agent-monitoring/{runs,events,tools}.jsonl`
records, but never constructs `provider` or `execution_id`, and never threads `ticket_id` as an
explicit field (today it is only implicit inside `run_id`'s string value). The read side
(`tools/agent-monitoring/post_tool_hook.py`, `record_events.py`, `record_run.py`, the dashboard's
`ingest.py`/`models.py`) already fully supports these three fields — built and tested by the DONE
`TCK-20260721-MONITORING-WRITER-UNIFICATION` — but has never seen them on a real write. This
ticket is a pure **write-side activation**: no production Python monitoring-tool code needs to
change, only `.claude/workflows/implement-ticket.js`.

### Complete call-site inventory (file:line, as of this investigation)

**A. Direct `agent-monitoring/*.jsonl` disk-write call sites** (i.e. actually invoke
`record_events.py`/`record_run.py`):

1. **`writeMonitoring(finalStatus)`** — defined at `implement-ticket.js:314-357`. This is the
   *only* function that emits real `runs.jsonl`/`events.jsonl` records for the normal workflow
   path. It is an `agent()` call whose prompt tells the agent to run
   `python3 tools/agent-monitoring/record_events.py --data '...'` (Step 2, embeds `"run_id":
   "${tid}"` per event, line 341) and `python3 tools/agent-monitoring/record_run.py --data '...'`
   (Step 3, embeds `"run_id":"${tid}"` in the JSON literal, line 348). It closes over `tid`
   (defined line 202) exactly the way `writeSidecar`/`captureTs` do.
   Called at **15 sites** (all pass only a status string — no call site itself touches
   `record_events.py`/`record_run.py`, they all funnel through this one function):
   `implement-ticket.js:401` (`CONFLICTS_DETECTED`), `:413` (`TAGS_NOT_REGISTERED`), `:428`
   (`EPIC_SCOPED`), `:611` (`NEEDS_HUMAN_INPUT`), `:673` (`review.verdict` —
   `NEEDS_CHANGES`/`BLOCKED`), `:775` (`DOC_STALENESS_BLOCKED`), `:851` (`archVerify.verdict`),
   `:908` (`TESTS_FAILED`), `:955` (`DATA_RUNS_CLEAN_FAILED`), `:1090` (`PARITY_INCOMPLETE`),
   `:1148` (`SECURITY_BLOCKED`), `:1228` (`DOD_BLOCKED`), `:1325` and `:1337`
   (`FINALIZE_INCOMPLETE`, two branches of the same check), `:1347` (`DONE`).
   **Because every one of these 15 call sites funnels through the single `writeMonitoring`
   function body, threading `provider`/`execution_id`/`ticket_id` requires editing that one
   function's prompt text once (Steps 2 and 3), not 15 separate diffs.**

2. **Scope-agent-failed fallback path** — `implement-ticket.js:189-194`. Runs when the
   `ticket-scoper` agent returns null/malformed output (no valid `ticket_id`). Calls
   `record_events.py` (line 190) and `record_run.py` (line 193) **directly via `bash()`**,
   bypassing `writeMonitoring` entirely (deliberately — `tid`/`pushEvent`/`writeMonitoring` don't
   exist yet at this point in execution). Uses `fallbackRunId = ticketId || 'SCOPE-FAILED-...'`
   as `run_id`. This is the path AC bullet 4 ("no-ticket Scope and scope-failure path remain
   identity-less") describes — **no `provider`/`execution_id`/`ticket_id` should be added here**,
   confirmed correct as-is: `executionId` (see Design Decision 1 below) is only computed after
   `tid` is set at line 202, and this path returns before that line ever runs.

**B. `.claude/current_run` sidecar writes** (not `agent-monitoring/*.jsonl` directly, but feed
`tools.jsonl` via `post_tool_hook.py`'s sidecar read — see Current Behavior/post_tool_hook.py
below):

3. **`writeSidecar(seq, phase, agent)`** — defined `implement-ticket.js:240-247`. Closes over
   `tid`. Writes `{'run_id', 'seq', 'phase', 'agent'}` only. Called at exactly 10 sites (all via
   the fixed adjacency pattern `await writeSidecar(events.length + 1 + seqOffset, '<Phase>',
   '<agent>')` immediately before the paired `await agent(...)` call): Investigate (`:456`), Plan
   (`:559`), Review (`:640`), Implement (`:709`), Architecture-Verify (`:825`), Test (`:886`),
   Parity (`:1035`), Security-Review (`:1127`), Verify (`:1190`), Finalize (`:1244`). Single
   function body edit threads `execution_id`/`provider` to all 10 — same "edit once" shape as
   `writeMonitoring`.
4. **Scope-phase resume-branch inline sidecar write** — `implement-ticket.js:62-67`. Runs before
   `writeSidecar` even exists (before `tid` is known — this is the *raw, unvalidated* input
   `ticketId`, not yet confirmed to correspond to a real ticket file). Writes `{'run_id':
   ticketId, 'seq', 'phase': 'Scope', 'agent': 'ticket-scoper'}` directly via its own inline
   `bash()`/python3 call (can't reuse `writeSidecar`, which closes over `tid`, not defined yet).
5. **Scope-phase new-ticket branch clear** — `implement-ticket.js:69`. `printf '{}' >
   .claude/current_run` — neutral clear, no identity fields relevant.
6. **`writeMonitoring`'s own internal Step 0 clear** — `implement-ticket.js:324`. `printf '{}' >
   .claude/current_run` inside the agent prompt — also neutral, and `writeMonitoring`'s own
   agent-call is permanently sidecar-*tracking*-free by design (confirmed by
   `test_writeMonitoring_call_has_no_preceding_sidecar_write`).

**C. Not real disk-write call sites (both TCK-20260731's flagged questions, resolved below with
evidence):**

7. **`classifyChecklistFailure(checklist, ticketId, ticketTier)`** — `implement-ticket.js:287-312`.
   Shells out via `bash()` (lines 291-297) to
   `tools/gate_checks/done_checker_static.py::_frontmatter_has_unregistered_tags` — a **pure
   read/classify call**, returns a `reasonCode` string (`'tag_registry_rejection'` or
   `'dod_condition_failed'`). It never imports or calls `record_events.py`/`record_run.py`. Its
   return value is later passed into `pushEvent(...)` at line 1225, which only mutates the
   in-memory `events` array; the array is flushed to disk by the *subsequent*
   `writeMonitoring('DOD_BLOCKED')` call at line 1228 — i.e. `classifyChecklistFailure`'s output
   does reach disk, but only via the ordinary `writeMonitoring` mechanism already covered in
   inventory item A.1, not as an independent write site.
8. **`check_tag_drift` Finalize-phase hook** — `implement-ticket.js:1383-1402`. Bash-shells to
   `tools/gate_checks/done_checker_static.py::check_tag_drift(tid)` (a read-only check), then (if
   `FLAGGED`) calls `pushEvent('Finalize', 'finalizer', 'failed', ...)` at line 1400. Critically,
   this runs **after** `writeMonitoring('DONE')` has already executed and returned (line 1347) —
   there is no further disk flush after this point in the file. This `pushEvent` call only mutates
   the already-final in-memory `events` array; it is provably never written to any
   `agent-monitoring/*.jsonl` file in this run. Confirms the ticket's own description ("mutates
   the local events array without a further disk flush, since writeMonitoring has already run").
   The structurally identical, older `check_monitoring_write_recorded` block (`:1356-1377`)
   establishes this exact "post-DONE pushEvent, no re-flush" pattern already.

**Conclusion for TCK-20260731's question:** Neither `classifyChecklistFailure`'s shell-out nor
`check_tag_drift`'s Finalize hook is a real `record_events.py`/`record_run.py` disk-write call
site. Both are pure read/classify calls. No fix is needed for TCK-20260731 — its own Investigate
phase (when picked up) should record "no real monitoring-jsonl write introduced by either call
site, no fix needed," citing this investigation.

### `tools/agent-monitoring/post_tool_hook.py` (already built, TCK-20260721-MONITORING-WRITER-UNIFICATION)

Lines 50-61 and 84-86: already reads `execution_id`/`provider`/`ticket_id` off the
`.claude/current_run` sidecar JSON (`sidecar.get("execution_id") or None`, etc.) and writes them
into every `tools.jsonl` record, defaulting to `None` on any read failure or absent key (fail-open,
consistent with `phase`/`agent`'s existing precedent). **No code change needed here** — populating
`tools.jsonl` with real identity values is purely a function of `writeSidecar` (inventory item
B.3) starting to write those fields into the sidecar.

### `tools/agent-monitoring/record_events.py` and `record_run.py` (already built)

Neither has `provider`/`execution_id`/`ticket_id` in its `REQUIRED` set
(`record_events.py:14`, `record_run.py:12` — both correctly unchanged, confirmed by
`test_record_events_required_fields_unchanged`). Both use `{**record, ...}` merge semantics when
constructing the written line (`record_events.py:121,141`; `record_run.py:65,68`), so any extra
keys present in the `--data` JSON payload — including `provider`/`execution_id`/`ticket_id` —
pass straight through into the written JSONL line untouched. This is empirically proven by
`tests/tools/test_record_events.py::test_execution_identity_fields_pass_through_unchanged` and
`tests/tools/test_record_run.py::test_execution_identity_fields_pass_through_unchanged` (both
pre-existing, both green today). **No signature or validation change needed in either file** —
this ticket only needs to change what JSON payload `writeMonitoring`'s agent prompt constructs.

### Dashboard/reader side (already built)

`src/api/agent_ops_dashboard/`'s `ingest.py`/`models.py` already has `RunSummary.provider`,
`.execution_id`, `.ticket_id`, `.identity_provenance` (`"native"` vs `"legacy"`), and
`DashboardCache.get_runs(provider=..., execution_id=...)` filtering — all covered by
`tests/tools/test_agent_ops_dashboard_ingest.py:405-472` and `:804-834` (legacy-shape +
new-format mixed-corpus parsing). **No code change needed.** This ticket's controlled validation
run will be the *first* real data these already-tested code paths ever see.

## Mechanics / Engine Constraints

Not a Mechanics Bible / `docs/engine/` concern — this is agent-infrastructure/observability
tooling (`.claude/workflows/`, `tools/agent-monitoring/`), outside the simulation engine's
authoritative-state and combat/economy/strategy law surfaces. No chapter of `docs/mechanics/` or
contract in `docs/engine/` constrains this change. The governing "law" here is the durable
append-only-write contract in `docs/ai/monitoring_writer_decision.md` and the schema contract in
`agent-orchestration/monitoring-schema.yaml`, both already-decided inputs this ticket consumes,
not re-derives.

## Parity Ledger Overlap

- **`INFRA-275`** (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P2`) —
  the entry documenting `TCK-20260721-MONITORING-WRITER-UNIFICATION`'s dashboard-side additive
  `provider`/`execution_id`/`ticket_id` support (`models.py`, `ingest.py`,
  `test_run_summary_carries_provider_execution_id_ticket_id_when_present`,
  `test_get_runs_filters_by_provider_and_execution_id`). This entry's claims remain true and
  unaffected by this ticket (the dashboard code itself doesn't change) — but this ticket is the
  first to make those fields carry *real* data, so `INFRA-275` (or a new sibling entry) should
  get a follow-up note/evidence line once this ticket lands, per the Parity Rule (docs and ledger
  stay in sync with what's operationally true, not just what's been built). Not P0 — no
  `test_path` gate blocks this ticket on `INFRA-275` specifically.
- **`INFRA-281`** (status `verified`, priority `P2`) — documents `writeSidecar(seq)` being
  widened to `writeSidecar(seq, phase, agent)` for `TCK-20260719-LIVE-PHASE-AGENT-LABEL`. This
  ticket widens `writeSidecar`'s *body* again (adds `execution_id`/`provider` to the JSON it
  writes) without changing its call signature — `INFRA-281`'s own claims (phase/agent threading)
  remain accurate, but its `v2_evidence` describing `writeSidecar`'s exact body may need a
  supplementary note since the function it cites is being extended again.
- No P0 entries found for this scope (searched `infrastructure.yaml` for
  `execution|provider|sidecar|writeSidecar|writeMonitoring` — all hits are P1/P2, none P0), so
  no ledger entry forces a `test_path` gate on this specific change.
- `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`
  (not a parity-ledger YAML entry, but the authoritative status tracker for this exact
  activation): Section 5's status table row `Execution identity | Schema supported, not supplied
  by real Claude/Codex writes | Not operational` and its "Current limitation" bullet ("Real
  Claude workflow records do not currently supply `provider` or `execution_id`") will become
  **stale** once this ticket lands and must be updated in the same session (see Anti-Drift
  Hazards).

## Prior Work

- **`TCK-20260721-MONITORING-WRITER-UNIFICATION`** (DONE) — built the entire additive schema,
  shared `writer.py` (lock-file protocol, `os.O_CREAT|O_EXCL`, Linux-only per its own
  platform-coverage self-check), and read-side support for `provider`/`execution_id`/`ticket_id`
  across all three JSONL files plus the dashboard. Its `stored_artifacts/` `investigation.md` and
  `plan.md` explicitly frame this as "follow-on, epic-gated implementation work" — i.e. it built
  the capability and deliberately deferred activation, which is exactly this ticket's job.
- **`TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS`** (DONE) — built
  `tools/agent_codex_pilot_guardrails/ticket_selection.py::assert_no_concurrent_claim`, which
  raises when a `ticket_id` is concurrently claimed by 2+ distinct `provider` values found in
  `runs.jsonl`. Its own docstring (`ticket_selection.py:33-34`) states this "check is proven only
  against synthetic fixture lists" and `provider_field_coverage()` exists specifically to make
  visible that the real corpus currently has zero provider-bearing records. This ticket is the
  gap that guard was built anticipating — once real `provider="claude"` writes exist,
  `assert_no_concurrent_claim` starts operating against real data for the first time.
- **`docs/ai/monitoring_writer_decision.md`** §2 (Execution Identity Model, AC2) — the
  already-decided design this ticket implements verbatim:
  `execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"`, `run_id`
  unchanged/display-only, `ticket_id` promoted to an explicit top-level field.
  `docs/architecture/agent_orchestration_contract.md`'s "Execution Identity (Consumed Input)"
  subsection quotes this verbatim and marks it "Status: Consumed-as-input" — confirming this
  ticket does not get to alter the field shape, only activate it.
- **`TCK-20260731-CODEX-EXECUTION-IDENTITY-TAG-SWEEP`** (OPEN, `tickets/todos/`) — filed as a
  pointer ticket specifically flagging `classifyChecklistFailure` and `check_tag_drift` as
  needing this investigation's confirmation. Resolved above (Current Behavior, item C) — that
  ticket can close as a no-op confirmation once it re-reads this investigation.

## Risks and Open Questions

**Resolved (per this investigation's own required questions):**

1. **Where/how is `execution_id` generated, and threaded without a giant diff?** Generate once,
   immediately after `const tid = ticketInfo.ticket_id` (`implement-ticket.js:202`), before the
   "Agent Monitoring Setup" block (`:206`) — i.e. before `pushEvent`, `writeSidecar`,
   `writeMonitoring` are defined, so all three can close over it exactly the way they already
   close over `tid`. Recommended shape (matches the file's own established
   `resolveSeqOffset`/`resolveScopeTicketLocation` MARKER-prefixed-bash-JSON idiom, but keeps
   `tid` out of the python `-c` string entirely to avoid any quoting risk):
   ```js
   const PROVIDER = 'claude'
   const execIdSuffixRaw = await bash(`python3 -c "
   import secrets, time
   print('EXECID:' + str(int(time.time() * 1000)) + '-' + secrets.token_hex(4))
   " 2>/dev/null`)
   const execIdMarker = (execIdSuffixRaw || '').indexOf('EXECID:')
   const execIdSuffix = execIdMarker !== -1 ? execIdSuffixRaw.slice(execIdMarker + 'EXECID:'.length).trim() : `${Date.now()}-fallback`
   const executionId = `${PROVIDER}-${tid}-${execIdSuffix}`
   ```
   This is a **single insertion point**. `writeSidecar`'s function *body* (not its call sites,
   not its signature) gets `'execution_id': sys.argv[5], 'provider': sys.argv[6]` appended, with
   `${executionId}`/`${PROVIDER}` appended as new trailing argv elements in the bash template
   literal (after `"${agent}"`, never inserted between existing args — see Anti-Drift Hazards for
   why ordering matters here). `writeMonitoring`'s prompt text (Steps 2 and 3, lines ~341 and
   ~348) gets `"execution_id": "${executionId}", "provider": "${PROVIDER}", "ticket_id":
   "${tid}"` added to the per-event and run-record JSON construction instructions. **Zero of the
   15 `writeMonitoring(...)` call sites or 10 `writeSidecar(...)` call sites themselves need to
   change** — only the two function bodies.

2. **TCK-20260731's question — real disk-write call sites?** No. Both
   `classifyChecklistFailure` (`:287-312`) and `check_tag_drift` (`:1383-1402`) are pure
   read/classify calls; neither imports or invokes `record_events.py`/`record_run.py`. See
   Current Behavior item C for full evidence.

3. **`provider="claude"` vs. legacy `claude-code` — where would a stray token get emitted?**
   Nowhere in any real write path. Grepped the full `tools/agent-monitoring/`,
   `agent-orchestration/`, `docs/ai/`, `.claude/workflows/` tree for `claude-code`: the only
   hits are (a) illustrative prose in `docs/ai/monitoring_writer_decision.md:109,136,139` and
   `docs/ai/shadow_promotion_gate_thresholds_decision.md:75,202` (historical/documentation
   vocabulary — never edited by this ticket, since it is a `Quoted verbatim` snapshot the
   orchestration contract explicitly consumes as "Status: Consumed-as-input"), and (b)
   `tools/retrieval_event_parity_check.py:16`'s `_KNOWN_PROVIDER_TOKENS =
   frozenset({"codex", "claude", "claude-code"})` — a **completely separate subsystem**
   (retrieval-event field-name-collision guard for the shadow context-packet system, gated behind
   `SHADOW_CONTEXT_PACKET_ENABLED`, itself out of scope per this ticket's own Related Tickets
   note). That constant is a naming-collision allowlist, not an emission site — it never writes
   `provider` or `execution_id` to any file. **Operationally**: no code change is needed to stop
   emitting `claude-code` (nothing does), and no read-side normalization/aliasing of a legacy
   `claude-code` value exists anywhere today (`validate.py`, `legacy_reader.py`, `vocabulary.py`,
   dashboard `ingest.py` — grepped, zero hits for provider-value normalization) because no
   historical data has ever carried a `provider` field at all. "Reader-compatible legacy/
   documentation vocabulary, never as an alternative newly emitted token" means: (a) this
   ticket's own new tests must assert `provider="claude"` is the only value new code ever
   constructs (never `claude-code`), and (b) if a test wants to exercise "the reader tolerates a
   legacy-shaped `claude-code` value" it should do so as a synthetic fixture proving no crash/
   silent-drop — not as evidence of a real historical value, since none exists in the corpus. No
   normalization code is required to be written for this ticket's ACs to be satisfiable; test
   coverage can assert tolerant pass-through behavior against a synthetic `claude-code` row using
   the exact `{**record, ...}` merge semantics already proven generic in `record_events.py`/
   `record_run.py`.
4. **Do `record_events.py`/`record_run.py` need signature changes?** No. Confirmed via source
   read (`REQUIRED` sets unchanged, `{**record, ...}` pass-through) and via two pre-existing,
   currently-green tests exercising exactly this
   (`test_execution_identity_fields_pass_through_unchanged` in both
   `tests/tools/test_record_events.py:267-284` and `tests/tools/test_record_run.py:177-194`).
   These fields are genuinely "schema-supported but not populated" as the closure doc frames it
   — this ticket only needs to populate the `--data` payload `writeMonitoring`'s prompt already
   constructs.

**Open (needs a Plan-phase decision, not blocking but should be made explicit in plan.md):**

- **Should the Scope-phase resume-branch's pre-`tid` sidecar write (`implement-ticket.js:62-67`,
  using the raw, not-yet-validated `ticketId`) also carry `execution_id`/`provider`?**
  Recommendation: **no** — `execution_id` is defined ("generated only after a real ticket ID is
  known") to be created once, after `tid` is confirmed by the `ticket-scoper` agent at line 202.
  The resume branch's own early Scope-phase tool calls (e.g. `resolveScopeTicketLocation`'s
  `bash()` call at line 93) would keep `run_id` populated (from the raw `ticketId`) but
  `execution_id`/`provider` null — consistent with `post_tool_hook.py`'s existing null-default
  handling and with AC bullet 4's spirit (don't synthesize identity before a ticket is confirmed
  real). This narrows the blast radius (item B.4 in the inventory stays unchanged) and should be
  called out explicitly in plan.md rather than silently assumed.
- **Baseline verification mechanism (AC's last bullet — "all pre-existing monitoring JSONL
  lines/bytes remain unchanged").** No existing helper in this repo does a byte-level pre/post
  comparison of `agent-monitoring/*.jsonl` specifically for this purpose (the closest precedent,
  `TCK-20260705-...`'s prefix-comparison language, is descriptive, not a reusable script). Plan
  phase should specify the exact mechanism: e.g. `wc -l`/checksum snapshot of each file
  immediately before the controlled validation run, then a diff against the same prefix
  afterward — this is new evidentiary work, not reuse of an existing tool.

## Anti-Drift Hazards

- **`writeSidecar`'s call signature must stay exactly `(seq, phase, agent)`.**
  `tests/tools/test_current_run_sidecar_orchestrator.py::test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`
  does a literal string match on `"const writeSidecar = async (seq, phase, agent)"`, and
  `test_sidecar_bash_write_precedes_each_covered_agent_call` regex-matches the exact 3-arg call
  shape at all 10 sites. New fields must be threaded via **closure** (over `executionId`,
  `PROVIDER`), never by widening the parameter list — this is the same idiom `tid` itself already
  uses.
- **Argv ordering inside `writeSidecar`'s bash template literal.**
  `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` asserts the literal
  substring `'"${tid}" "${seq}" "${phase}" "${agent}"'` is present unbroken in the helper body.
  New argv elements (`"${executionId}" "${PROVIDER}"`) must be **appended after** `"${agent}"`,
  never inserted between existing args, or this test breaks on a substring match, not a semantic
  one.
- **Do not add `provider`/`execution_id`/`ticket_id` to `record_events.py`'s or `record_run.py`'s
  `REQUIRED` sets.** `test_record_events_required_fields_unchanged` pins `REQUIRED` to exactly 7
  fields; these three stay optional/additive by design (a record from a workflow this ticket
  doesn't touch — `implement-epic`, `create-tickets` — must keep writing valid records without
  them).
- **Doc-staleness gate will require a real `docs/` path in `files_changed`.**
  `tools/gate_checks/doc_staleness_check.py::check_doc_staleness` FAILs when `behavior_changed`
  is true, a changed path matches `src/` or `.claude/workflows/*.js`, and zero changed paths start
  with `docs/`. This ticket's only production file change is `.claude/workflows/implement-ticket.js`
  and `behavior_changed` will almost certainly be reported `true` (new fields now populate real
  JSONL output). **`agent-orchestration/intentional-divergences.md` does NOT satisfy this gate**
  (it is not under `docs/`) even though its "Known Configuration Gaps" note is the most directly
  stale text in the repo about this exact ticket. The implementer must update at least one file
  actually under `docs/` —
  `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`
  (Section 5's status table row and "Current limitation" bullet) is the natural target, alongside
  the `agent-orchestration/` file for completeness.
- **`writeMonitoring`'s Step 0 sidecar-clear-first ordering
  (`test_writeMonitoring_step0_sidecar_clear_precedes_other_steps`) and the exact Step 0-1-2-3
  labels must remain unchanged** — only the *content* of what Steps 2/3 instruct the agent to
  write (adding 3 fields to the JSON) should change, not the step structure/ordering/count.
- **The Scope-agent-failed fallback path (`:189-194`) and the initial Scope resume/new-ticket
  sidecar writes (`:62-70`) must stay identity-less** — see Risks/Open Questions above. Adding
  `execution_id` there would require synthesizing an identity before a ticket is confirmed real,
  directly contradicting AC bullet 4.
- **`check_tag_drift`'s and `check_monitoring_write_recorded`'s post-`writeMonitoring('DONE')`
  `pushEvent` calls must remain non-flushing.** Do not "fix" this by adding a second
  `writeMonitoring` call after them — that would violate the established, intentional
  "advisory-only, never re-opens a closed run" pattern documented in both blocks' own comments,
  and would double-write a `DONE`-equivalent run record.
- **`INFRA-281`'s existing `v2_evidence` describes `writeSidecar`'s body as of
  `TCK-20260719-LIVE-PHASE-AGENT-LABEL`.** The Parity phase for this ticket should extend/append
  to `INFRA-281` and/or `INFRA-275`, not silently leave them describing a now-stale function body
  without a pointer to the newer state.
