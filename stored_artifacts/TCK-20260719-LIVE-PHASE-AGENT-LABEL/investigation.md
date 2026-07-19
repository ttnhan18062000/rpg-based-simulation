---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-LIVE-PHASE-AGENT-LABEL
artifact_type: investigation
tags: [agent-monitoring, observability, workflows]
---

# Investigation — TCK-20260719-LIVE-PHASE-AGENT-LABEL

## Current Behavior

### `.claude/workflows/implement-ticket.js` — `writeSidecar` helper and its 10 call sites

`writeSidecar` is defined once, at `.claude/workflows/implement-ticket.js:202-209`, as a 1-arg
helper:

```js
const writeSidecar = async (seq) => {
  await bash(
    `python3 -c "
import json, sys
open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2])}))
" "${tid}" "${seq}" 2>/dev/null || true`
  )
}
```

It closes over `tid` (module-scope `const`, set once at `implement-ticket.js:164` after the Scope
agent call resolves) and writes only `{run_id, seq}` to `.claude/current_run`.

Verified by direct grep (`grep -n "writeSidecar(" implement-ticket.js`) — **exactly 10** call
sites, all of the form `await writeSidecar(events.length + 1)`, at lines **419, 460, 541, 610,
679, 740, 889, 981, 1044, 1098**. This exactly matches the ticket's Scope-bullet line-number claim
— the ticket's own "do not trust the idea doc's line numbers, actual lines are these 10" note is
correct and current as of this investigation; no drift since the ticket was written. Mapped to
phase/agent:

| Line | Phase (from preceding `phase('X')`) | Agent literal (from the paired `pushEvent(...)` call a few lines after) |
|---|---|---|
| 419 | `Investigate` (`phase('Investigate')` at :416) | `investigator` (`agentType: 'investigator'` at :449, `pushEvent('Investigate', 'investigator', ...)` at :453) |
| 460 | `Plan` (:457) | `planner` (:482, pushEvent at :521) |
| 541 | `Review` (:525) | `architecture-reviewer` (:565, pushEvent at :583) |
| 610 | `Implement` (:594) | `implementer` (:634, pushEvent at :637) |
| 679 | `Architecture-Verify` (:647) | `architecture-reviewer` (:696, pushEvent at :714) — same agent literal as Review, different phase |
| 740 | `Test` (:722) | `test-scoper` (:756, pushEvent at :772) |
| 889 | `Parity` (:826) | `parity-updater` (:910, pushEvent at :956) |
| 981 | `Security-Review` (:967, conditional block) | `security-reviewer` (:993, pushEvent at :1011) |
| 1044 | `Verify` (:1017) | `done-checker` (:1074, pushEvent at :1092) |
| 1098 | `Finalize` (:1096) | `finalizer` (agent() call at :1099 has no `agentType` option at all; the literal `'finalizer'` only appears at the paired `pushEvent('Finalize', 'finalizer', 'ok', ...)` call at :1200) |

At every site the phase and agent are **string literals already known at the call site** — no
runtime-computed value needs threading in, confirming the idea doc's core premise.

I independently confirmed there is **no 11th `writeSidecar(` call anywhere in the file** — full
`grep -n "writeSidecar("` returns exactly 11 hits total: the 10 call sites above plus the one
definition at :202 (matched only by the comment reference at :34, which is prose, not a call).
`writeMonitoring` (the function at :258-320, invoked at 8 different exit points) never calls
`writeSidecar` itself — confirmed by inspection of its body; this is intentional (see
`test_writeMonitoring_call_has_no_preceding_sidecar_write` below) since `writeMonitoring`'s own
tool calls must stay unattributed (`run_id: null`), not attributed to whatever phase preceded it.

### The 3rd, non-`writeSidecar()` sidecar-write path — Scope phase (`implement-ticket.js:44-53`)

Confirmed exactly as the ticket describes. Immediately after `phase('Scope')` (:29) and before the
ticket-scoper `agent()` call (:79), there are two inline `bash()` branches (not using the
`writeSidecar` helper, which can't be called yet — it closes over `tid`, not resolved until the
Scope agent call returns):

```js
if (ticketId) {
  await bash(
    `python3 -c "
import json, sys
open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1}))
" "${ticketId}" 2>/dev/null || true`
  )
} else {
  await bash(`printf '{}' > .claude/current_run 2>/dev/null || true`)
}
```

- Resume branch (`ticketId` truthy): writes `{'run_id': ticketId, 'seq': 1}` — no `phase`/`agent`
  keys today.
- New-ticket branch: writes an empty `{}` — no keys at all.

Both `phase='Scope'` and `agent='ticket-scoper'` are known literals in scope at this point in the
file (the Scope pushEvent call at :349 hardcodes `'Scope'`/`'ticket-scoper'`) — so technically
nothing prevents adding them to the resume branch's JSON literal. The ticket correctly flags this
as a real gap the source idea doc never considered (the idea doc's "10 call sites" enumeration
predates this Scope-phase coverage entirely — Scope sidecar coverage was added later by
TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION).

### `tools/agent-monitoring/post_tool_hook.py` — sidecar read and record write

Reads `run_id`/`seq` from `.claude/current_run` at lines 43-51 inside a `try/except Exception:
pass` block, defaulting both to `None` on any read failure (missing file, malformed JSON, missing
keys via `.get(...) or None`). Builds the `tools.jsonl` record dict at lines 61-70:

```python
record = {
    "session_id": session_id,
    "run_id": run_id,
    "seq": seq,
    "ts": now,
    "tool": tool_name,
    "input_summary": _input_summary(tool_name, tool_input),
    "status": status,
    "duration_ms": duration_ms,
}
```

Then appends it to `agent-monitoring/tools.jsonl` (lines 72-77), wrapped in `fcntl.flock(f,
fcntl.LOCK_EX)` / `fcntl.flock(f, fcntl.LOCK_UN)` around the `open()+write()` — this locking was
added by **TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK** (2026-07-16, already in
`tickets/done/`, no `stored_artifacts/` folder because it was a `hotfix`-tier ticket — no staging
artifacts required per CLAUDE.md's hotfix rule). Adding two more keys (`phase`, `agent`) to the
`record` dict is fully compatible with this lock: the whole dict is serialized and written as one
`f.write()` call inside the existing `flock`-guarded block, so extra keys don't change the
synchronization behavior at all — this ticket's change sits entirely upstream of the lock (in how
`record` is *built*), not the write mechanism itself. No signature or behavior change to the
locking code is needed.

### `docs/agent-monitoring/schema.md`

The `tools.jsonl` Fields table is at lines 219-228 (confirmed — 8 rows: `session_id`, `run_id`,
`seq`, `ts`, `tool`, `input_summary`, `status`, `duration_ms`), matching the ticket's citation
exactly. The nullable-field convention precedent the ticket points to (lines 109-111) is actually
on the **`events.jsonl`** Fields table (`tool_call_count`, `reason_code`, `cost_proxy_score` rows)
— the ticket's phrasing ("following the same convention used when ... were added") means reuse the
*documentation style* (Type/Nullable/Description columns + a "`null` for all records predating
TCK-..." note), not that those fields live on `tools.jsonl`. This is a minor imprecision in the
ticket text, not a blocker — the intent is unambiguous once the actual doc is read.

Two prose sections will go stale if not touched, though neither is named in the ticket's AC:
- "How tool calls are attributed to agent events" (lines 234-242) says the sidecar holds
  `{"run_id": "...", "seq": N}` — becomes incomplete (not wrong, just incomplete) once `phase`/
  `agent` are added.
- `docs/guides/agent_ops_dashboard.md:173-178`'s "Known limitation" section states tools.jsonl's
  "underlying data type has no such fields at all for live entries" — this sentence becomes
  literally false after this ticket (the fields will exist, just unconsumed by the dashboard UI).
  This doc is **not** in the ticket's Related Docs and updating it is arguably adjacent to the
  ticket's explicit Out-of-Scope bullet ("dashboard-side consumption... is separate, follow-up
  work") — flagged as a minor doc-drift risk, not a blocker, since the *functional* claim (the
  dashboard still shows "phase unknown") stays true.

### `tools/agent-monitoring/vocabulary.py`

Confirms canonical phase/agent literals for `implement-ticket`: `WORKFLOW_PHASES` (:21-24) and
`WORKFLOW_AGENTS` (:40-44) both already include every phase/agent literal identified in the table
above (`Scope`, `Investigate`, `Plan`, `Review`, `Implement`, `Architecture-Verify`, `Test`,
`Parity`, `Security-Review`, `Verify`, `Finalize` / `ticket-scoper`, `investigator`, `planner`,
`architecture-reviewer`, `implementer`, `test-scoper`, `parity-updater`, `security-reviewer`,
`done-checker`, `finalizer`, `implement-ticket-orchestrator`). Nothing in this module needs to
change — it's already the correct target vocabulary for the new `tools.jsonl` fields, it's just not
*used* to validate them (see Out of Scope bullet 3, confirmed correct below).

## Mechanics / Engine Constraints

None apply. This is agent-orchestration tooling (`.claude/workflows/`, `tools/agent-monitoring/`)
— no `docs/mechanics/` chapter or `docs/engine/` contract governs it, consistent with how the
closest prior precedent, **INFRA-274** (`TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS`, also an
orchestrator-side `implement-ticket.js` gate-logic change), was scoped: its `support_boundary` note
explicitly states "no simulation behavior is involved." The same applies here.

## Parity Ledger Overlap

**No existing parity ledger entry covers this mechanism.** Searched `docs/parity_ledger/
infrastructure.yaml` (the correct file — subsystem "Replay, telemetry, observability, workers")
for any entry mentioning `sidecar`, `current_run`, `writeSidecar`, or `tools.jsonl`-schema changes;
the only hits are **INFRA-212** (an unrelated `decision_trace_index.json` sidecar in the
kernel/replay subsystem, not agent-monitoring) and **INFRA-275** (Agent Ops Dashboard backend,
mentions `tools.jsonl` only as one of three files `ingest.py` reads generically). Neither entry's
`text`/`v2_evidence` describes the `.claude/current_run` → `writeSidecar` → `post_tool_hook.py`
mechanism this ticket modifies.

However, the closest-precedent ticket for *scope shape* — **INFRA-274**
(`TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS`, an orchestrator-side `implement-ticket.js` logic
change with no simulation behavior) — **did** get its own new `infrastructure.yaml` entry at
`status: verified`, `priority: P1`, with a `support_boundary` note explaining why it's tracked
despite being non-simulation. That is this repo's established convention: orchestration-tooling
behavior changes to `implement-ticket.js`/`post_tool_hook.py` get their own parity ledger entries
even when no Mechanics Bible chapter applies. **This ticket should very likely add a new
`infrastructure.yaml` entry** (next available ID: **INFRA-281** — highest current ID in the file is
INFRA-280, confirmed by scanning all 285 entries) documenting the `writeSidecar(seq, phase, agent)`
signature change, the `post_tool_hook.py` record-dict addition, and the Scope-phase decision.

This also matters procedurally: the Parity phase in `implement-ticket.js` (:832-833) only
*skips* the `parity-updater` agent call when **both** `implementation.files_changed.every(f =>
!f.startsWith('src/'))` **and** `!implementation.behavior_changed`. None of this ticket's files
(`.claude/workflows/implement-ticket.js`, `tools/agent-monitoring/post_tool_hook.py`,
`tests/tools/*.py`, `docs/agent-monitoring/schema.md`) are under `src/`, so `parityNoSrcChange` will
be `true` — **the Parity phase will only run if the Implement-phase agent reports
`behavior_changed: true`**. It should: `tools.jsonl`'s on-disk schema changes (two new keys per
row) and `writeSidecar`'s call signature changes are observable behavior changes to the monitoring
data pipeline, even though no simulation behavior changes. Flagging this explicitly so the
Implement-phase agent doesn't under-report `behavior_changed` and accidentally skip Parity.

No P0 entries are touched by this ticket.

## Prior Work

- **`stored_artifacts/TCK-20260710-CURRENT-RUN-SIDECAR-BASH/`** — established the original
  `.claude/current_run` sidecar mechanism and the `try/except`-wrapped read pattern
  `post_tool_hook.py` still uses today. Its own investigation recommended (Decision 1) extending
  sidecar coverage to call sites that never had one (Scope) — the direct ancestor of the 3rd write
  path this ticket must now decide on.
- **`stored_artifacts/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION/`** — added the Scope-phase
  inline sidecar branches (the 3rd write path) and moved `writeMonitoring`'s sidecar-clear to Step 0.
  Found via empirical audit that ~35% of historical `tool_call_count` values were wrong due to two
  now-fixed timing gaps — evidence that this subsystem has a real history of silent correctness bugs
  from timing/ordering assumptions, relevant caution for this ticket's own call-site threading.
- **`stored_artifacts/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH/`** — moved `date -u` timestamp capture
  from agent-prompt text to the orchestrator (`captureTs()`), inserted immediately before each
  `writeSidecar` call. This is the "intervening captureTs() insertion" the ticket cites as the cause
  of the idea doc's stale +22 line-number offsets — confirmed consistent with the actual diff shape
  (a `captureTs()` call + a blank line before each `writeSidecar` site).
- **`tickets/done/TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK.md`** (hotfix, no stored_artifacts
  folder) — added the `fcntl.flock` write lock and, critically, **a new test file**
  `tests/tools/test_post_tool_hook.py` with 3 tests. See Risks below — this directly contradicts
  a specific factual claim in this ticket's own Scope section.

## Risks and Open Questions

**1. (Correctness-blocking) The ticket's claim "no dedicated test file exists for
`post_tool_hook.py` today (no `tests/tools/test_post_tool_hook.py` found)" is FALSE as of this
investigation.** `tests/tools/test_post_tool_hook.py` exists (created 2026-07-16 by
TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK, confirmed via `ls -la` — file is dated Jul 16
22:49) with 3 tests. Two of them will **break** under this ticket's planned change unless updated:

- `test_single_writer_produces_one_well_formed_line` (line 54) and
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` (line 72) both assert
  `set(record.keys()) == _RECORD_FIELDS` (exact set equality, lines 62 and 93), where
  `_RECORD_FIELDS` (lines 23-26) is a hardcoded closed set: `{"session_id", "run_id", "seq", "ts",
  "tool", "input_summary", "status", "duration_ms"}`. Adding `phase`/`agent` keys to the record dict
  will make `record.keys()` a strict superset of `_RECORD_FIELDS`, failing the `==` equality check.

This must be treated as **in-scope, must-fix regression surface** — not "extend a suite that
doesn't exist" (per the ticket's Scope bullet 6) but "update `_RECORD_FIELDS` at
`tests/tools/test_post_tool_hook.py:23-26` to include `phase`/`agent`, and add dedicated new tests
for the phase/agent read+include behavior in the same file" (which already has the right test
infrastructure — subprocess-driven hook invocation with a real `.claude/current_run` sidecar file
in `tmp_path`). This does not block implementation (the fix is small and mechanical) but the
planner/implementer must not skip it — it's a real gap in the ticket's stated scope, not merely a
documentation slip.

**2. (Decision required, not blocking) `tests/tools/test_current_run_sidecar_orchestrator.py`
regression surface is broader than the ticket's 3 named tests.** The ticket names
`_COVERED_SITE_ADJACENCY`, `test_tid_and_seq_passed_as_argv_not_json_embedded`, and
`test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`. Verified two more
in the same file will also break on a 3-arg `writeSidecar(seq, phase, agent)` signature change,
purely mechanically (not a design decision, just missed in the ticket's enumeration):

- `test_sidecar_bash_write_precedes_each_covered_agent_call` (line 93-99): the regex
  `r"await writeSidecar\(events\.length \+ 1\)"` used at line 99 to count exactly 10 call sites
  anchors on a bare `writeSidecar(events.length + 1)` with nothing after — an argument list of
  `(events.length + 1, 'Investigate', 'investigator')` will not match, so the `== 10` count assertion
  will find 0 and fail. Must update the regex (or the whole test) alongside `_COVERED_SITE_ADJACENCY`.
- `test_finalize_call_site_still_registers_sidecar` (line 117-129): its regex at lines 119-121,
  `r"phase\('Finalize'\).*?await writeSidecar\(events\.length \+ 1\)\nawait agent\(\n..."`, has the
  same bare-call anchoring problem for the Finalize site specifically.

**3. (Decision required — this IS the ticket's own flagged open question, restated with evidence)
Whether to add `phase='Scope'`/`agent='ticket-scoper'` to the Scope-phase inline sidecar write
(`implement-ticket.js:44-53`) has a real test-coupling cost either way:**

- **If yes** (add the literals to the resume-branch JSON dict): the exact hardcoded string
  `"open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1}))"` asserted
  at `tests/tools/test_current_run_sidecar_orchestrator.py:161` (inside
  `test_scope_phase_has_sidecar_coverage`) will need updating too — a test the ticket's Scope bullet
  does **not** list among the three needing updates. This is a second gap in the ticket's stated test
  scope, contingent on which way the Scope decision goes.
- **If no** (leave Scope's inline write as-is, decide the answer is "no" with a documented
  rationale — e.g. "Scope's own tool calls during ticket creation/resume are a single, short-lived
  phase already well-identified by `run_id` alone; the two-branch inline write predates and is
  structurally decoupled from the `writeSidecar` helper this ticket threads phase/agent through, and
  extending it is a separable, low-value follow-up"): no test changes needed for this file beyond the
  three the ticket already names, and `post_tool_hook.py`'s read logic naturally produces `phase:
  null, agent: null` for Scope-phase tool calls (consistent with AC #2's "outside any active workflow
  run" nullable behavior, generalized to "sidecar present but missing these keys").

  Investigation does not decide this — CLAUDE.md's Uncertainty Rule applies ("do not collapse
  investigation into exact coordinates too early") and the planner/implementer is better positioned
  to weigh the incremental test-maintenance cost against the value of Scope-phase phase/agent
  labeling for the live dashboard's very first phase. Both options satisfy AC #6 ("an explicit,
  documented decision is implemented") as long as the "no" option's rationale is written down
  somewhere durable (ticket Implementation Notes at minimum).

**4. (Non-blocking, confirmed low-risk) Dashboard consumption is genuinely unaffected.**
`src/api/agent_ops_dashboard/ingest.py` reads `tools.jsonl` rows but its `phase`/`agent` derivation
(lines 669-670, inside the events-processing path, not the tools-processing path) comes from
`events.jsonl` records, not from `tools.jsonl` rows directly — confirmed by reading the surrounding
code. Adding `phase`/`agent` keys to `tools.jsonl` records is additive and does not intersect any
existing dashboard field-mapping logic. `tests/tools/test_agent_ops_dashboard_ingest.py` and
`test_agent_ops_dashboard_concurrency.py` build their own synthetic `tools.jsonl` fixture dicts with
a small field subset (`tool`, `input_summary`, `ts`, `duration_ms`) and never assert an exact/closed
field set on real hook output — no update needed there.

**5. (Non-blocking) `validate.py`'s drift report (`compute_drift_report`) only reads
`events.jsonl` for phase/agent vocabulary checks, never `tools.jsonl`** — confirmed via `grep` of
`tools/agent-monitoring/validate.py` (the function signature is `compute_drift_report(runs, events)`,
no `tools` parameter). This confirms the ticket's Out-of-Scope bullet 3 (leaving the new
`tools.jsonl` phase/agent values unvalidated against `vocabulary.py`) is safe — there is no existing
validator that would need updating or that would start silently misfiring.

## Anti-Drift Hazards

- **Do not touch `writeMonitoring`'s own logic.** It intentionally never calls `writeSidecar` (its
  own tool calls must stay `run_id: null`) — this is asserted by
  `test_writeMonitoring_call_has_no_preceding_sidecar_write`. A 3-arg signature change to
  `writeSidecar` must not tempt adding a `writeMonitoring`-tracking call as a "consistency" fix — that
  is explicitly Out of Scope (flushing/history semantics) per this ticket and the source idea doc.
- **Do not widen this into phase/gate history.** The ticket's Out-of-Scope is explicit and the idea
  doc's own "Would NOT unlock" section is explicit: this is additive per-tool-call labeling only, not
  a `writeMonitoring` call-cadence change. Resist any temptation to "also flush events.jsonl earlier"
  while already touching this file.
- **Do not silently expand the two-test-file blast radius found above (#1, #2) into a general
  refactor of either test file's assertion strategy.** The idea doc itself raised this as an open
  question ("whether `_COVERED_SITE_ADJACENCY`'s assertion strategy itself should change to be less
  brittle") — that redesign is a separate, larger decision than this ticket's mechanical
  find-and-update scope. Update the specific broken assertions; do not redesign the test's approach.
- **Preserve the argv-quoting convention.** `writeSidecar`'s existing body passes `tid`/`seq` as
  individually-quoted argv elements (`"${tid}" "${seq}"`), never JSON-embedded in the `-c` string —
  the file has repeated, explicit comments (e.g. around `p0ScanOutput`, `filesChangedArgs`) warning
  that embedding JSON directly in a double-quoted `python3 -c "..."` string corrupts the script on
  unescaped nested quotes. The new `phase`/`agent` args must follow the same pattern:
  `"${tid}" "${seq}" "${phase}" "${agent}"` as additional argv elements, read via `sys.argv[3]`/
  `sys.argv[4]`, not embedded as `'phase': '${phase}'` inline in the `-c` string.
- **Preserve the fail-open contract.** `writeSidecar`'s `2>/dev/null || true` suffix and
  `post_tool_hook.py`'s outer `try/except Exception: pass` must both remain untouched in spirit — a
  malformed/missing `phase`/`agent` value must degrade to `null`, never raise or block a tool call
  (CLAUDE.md Hard Rule: "monitoring write failure must never fail the workflow").
- **Keep the `writeSidecar` helper's single-definition invariant.** `test_writeSidecar_defined_once_
  after_pushEvent_before_classifyChecklistFailure` asserts `source.count("const writeSidecar = async
  (seq)") == 1` and its position between `pushEvent` and `classifyChecklistFailure` — the updated
  test must re-assert "defined exactly once" against the new signature, not accidentally allow a
  second helper definition to slip in during editing.
