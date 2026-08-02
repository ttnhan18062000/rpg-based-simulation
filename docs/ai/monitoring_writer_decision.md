---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, agent-monitoring, process-improvement]
---

# Monitoring Writer & Execution Identity Decision — TCK-20260721-MONITORING-WRITER-DECISION

A standalone decision/evidence artifact bundling Open Decision #3 (execution identity) and
Open Decision #5 (concurrent-write strategy) from
`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`, per Codex's
2026-07-21 batch review of `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`'s child tickets, which
determined both decisions belong in this one ticket rather than split across this ticket and
the downstream `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`.

This document **decides and evidences**. It does not implement. The recommended writer design
and the execution-identity schema proposal below are follow-on, epic-gated implementation
work — no production monitoring writer path (`tools/agent-monitoring/post_tool_hook.py` or any
other file under `tools/agent-monitoring/`) changes as part of landing this document, and no
`agent-monitoring/*.jsonl` data file is touched.

---

## 1. Legacy Schema & Identifier Inventory (AC1)

This section synthesizes and cross-references the already-documented facts in
`docs/agent-monitoring/schema.md`'s **Known Limitations** section — it does not re-derive them.
See that doc for the authoritative source; the summary below quotes its findings by reference.

### `runs.jsonl` — five legacy schema generations without `end_ts`

Per `docs/agent-monitoring/schema.md`'s "Legacy schema generations without `end_ts`"
subsection, at least five historical write generations coexist with the current schema:

1. `started_at`/`finished_at`/`status`/`phases_completed`/`notes`
2. `final_status` present but `end_ts` key absent
3. `ts_start`/`ts_end`/`result`/`agent`
4. `completed_at`/`status`
5. `FOLDER-*`/`EPIC-*` batch wrappers using a bare `status` field

Plus one exhaustively-audited single-record exception: `TCK-20260623-TYPE-CHECKER`
(`"outcome":"success"`, `"phase":"implement"`, no `end_ts`/`final_status`/`status` field at
all) — deliberately not added to `validate.py`'s allowlist (a single-record shape is not worth
speculative code), documented as a permanent, individually-verified exception.

All six shapes are handled entirely on the **read side**: `validate.py`'s
`LEGACY_COMPLETION_FIELDS` (`end_ts`, `finished_at`, `completed_at`, `ts_end`) and
`LEGACY_TERMINAL_STATUS_VALUES` allowlists recognize them as valid completion signals without
any rewrite of `runs.jsonl` itself. The one documented exception to strict append-only
behavior, `TCK-20260718-STATUS-DRIFT-REPAIR`'s casing correction on 7 records, was an audited,
line-scoped substitution — not a bulk re-serialize — and remains a one-time historical
correction, not a change to the write contract.

### `run_id` — manual/ad hoc convention

Per the same doc's "Manual/ad hoc run_id convention" subsection: the `run-{code}-{unix_ts}`
convention and ad hoc `-REDESIGN`-suffix values found in historical data are pre-refactor,
manual-session artifacts, not reproducible by current `.claude/workflows/*.js` code (confirmed
via `implement-ticket.js`'s single-capture `tid` pattern). Any hand-written record must reuse
the ticket ID verbatim — never invent a suffix or a synthesized `run-{code}-{timestamp}` value.

### `tools.jsonl` — `phase`/`agent` null gap

Per the schema doc's field table: `phase`/`agent` are `null` for records predating
`TCK-20260719-LIVE-PHASE-AGENT-LABEL` (no backfill), and are `null` by design (not a defect)
for interactive tool calls made outside an active workflow run.

### `events.jsonl` — `tool_call_count`/`cost_proxy_score` null gap

Per the schema doc's field table: both fields are `null`/absent for every event recorded
before `TCK-20260708-AGENT-COST-OBSERVABILITY` / `TCK-20260719-COST-PROXY-WRITE-PATH` (no
backfill) — a retro spanning the cutover shows partial coverage, by design.

### The identifier gap this ticket exists to close

Today, `run_id` doubles as both **the execution key** (identifying one specific workflow
invocation) and **the ticket-linkage key** (identifying which ticket the run belongs to). This
conflation is safe only as long as exactly one provider ever executes a given ticket, at most
once concurrently. It breaks once the same ticket can be executed by more than one provider
(Claude Code and Codex, per
`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`), or re-run —
two executions of the same ticket would either collide on `run_id` or require inventing a new
ad hoc suffix convention (exactly the pattern the schema doc's Known Limitations already
document as a historical mistake, see above). Section 2 below resolves this by separating the
execution key from the join key explicitly.

---

## 2. Execution Identity Model (AC2)

**This is a schema field proposal for a future implementation ticket.** No field is added to
any real record as part of this document landing — the shape below is illustrated with a
synthetic example only, never a write to any real `agent-monitoring/*.jsonl` file. This is
consistent with `validate.py`'s existing "read-side absorbs legacy variance, write-side stays
append-only" precedent (`LEGACY_COMPLETION_FIELDS` / `LEGACY_TERMINAL_STATUS_VALUES`, Section 1
above).

### Immutable per-execution key

```
execution_id = f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"
```

Stdlib-only (`secrets` + `time`), no new dependency. Example:

```
claude-code-TCK-20260721-MONITORING-WRITER-DECISION-1774276800123-a1b2c3d4
```

Generated fresh once per workflow execution. Never reused. Never treated as a lookup/join key
across runs — two executions of the same ticket produce two distinct `execution_id` values by
construction (the `unix_ts_ms` + random suffix guarantee this even for same-provider re-runs
within the same millisecond-adjacent window).

### Human-readable run reference

`run_id` is retained in its current shape/format, unchanged. It becomes a display/reference
field rather than the execution's primary key — existing tooling and human readers keep the
familiar `TCK-YYYYMMDD-SHORT-SCOPE` (or `EPIC-*`/`FOLDER-*`) shape.

### Stable cross-run join key

`ticket_id` is promoted to an **explicit top-level schema field** — today it is only implicit
inside `run_id`'s string shape. All records for all executions of the same ticket, by any
provider, share the same `ticket_id` value. This is the field
`TCK-20260713-MONITORING-SQLITE-INDEX`'s eventual read-side index and
`TCK-20260721-ORCHESTRATION-CONTRACT-ADR`'s downstream contract should join on — `execution_id`
is never reused as a join key, `ticket_id` is.

### Synthetic illustration (not a real record)

```json
{
  "execution_id": "claude-code-TCK-20260721-MONITORING-WRITER-DECISION-1774276800123-a1b2c3d4",
  "run_id": "TCK-20260721-MONITORING-WRITER-DECISION",
  "ticket_id": "TCK-20260721-MONITORING-WRITER-DECISION",
  "provider": "claude-code",
  "start_ts": "2026-07-21T10:00:00Z"
}
```

---

## 3. Candidate Writer Design Comparison (AC3)

Scored against the four criteria named in the ticket's own AC3: POSIX+Windows portability,
malformed-partial-line rejection, append-only preservation, safe two-writer concurrency.

| Candidate | POSIX+Windows portability | Malformed-line rejection | Append-only preservation | Safe two-writer concurrency |
|---|---|---|---|---|
| **1. Lock-file protocol w/ bounded retry + stale-lock recovery (`os.O_CREAT \| os.O_EXCL`) — RECOMMENDED** | Syscall-level `os.open(..., O_CREAT \| O_EXCL)` semantics are identical on POSIX and Windows Python builds — no new dependency, no platform branch needed. | Relies on a downstream reader (`validate.py`-style `load_jsonl`), not the writer itself — same posture as the current `fcntl` design. Demonstrated empirically: `tests/tools/test_monitoring_writer_lockfile_candidate.py::test_malformed_partial_line_is_rejected_by_downstream_reader` — 1 malformed line correctly rejected, all 5 valid lines correctly parsed. | By construction — the writer only ever opens the target file in append (`"a"`) mode. | Demonstrated empirically: `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines` — 10 threads x 20 iterations = 200 concurrent invocations against one shared file, **3 passed, 0 corrupted/lost/duplicated/interleaved lines**, exact match of all 200 expected record markers. |
| **2. Single local writer process/queue** | High in principle — a queue/socket handoff is platform-neutral — but adds a long-lived background process as new operational surface. Not stress-tested in this ticket (no implementation in scope). | Same downstream-reader posture as candidate 1, unevidenced here. | By design, if the process itself only appends. | Strong by design (single writer eliminates the race entirely), but at the cost of a new failure mode (queue process crash/backpressure) not evidenced here. |
| **3. Provider-local append journals + deterministic merger** | Writer side is trivially portable — each provider only ever appends to its own file, no cross-process lock needed at write time at all. | Same downstream-reader posture, unevidenced here. | Per-journal append-only by construction; the merged output's append-only status depends on the merger's own implementation, unevidenced here. | Sidesteps the write-time race entirely by deferring merge to a separate read-side step, but shifts complexity to the merger's ordering/dedup logic — unevidenced here (no implementation in scope). |

**Recommendation: Candidate 1.** It directly reuses today's append-only `tools.jsonl` shape
with a minimal, dependency-free mechanism swap (`fcntl.flock` → `os.O_CREAT | os.O_EXCL`), it is
the only candidate with direct stress-test evidence gathered in this ticket, and it requires no
new long-lived process or deferred-merge complexity. Candidates 2 and 3 are recorded as viable
alternatives for a future implementation ticket to reconsider, not ruled out.

---

## 4. Supported Development Platform Set & Evidence (AC4/AC5)

### Supported-development-platform set: **{Linux}**

Justified from repo evidence, not an arbitrarily narrowed scope:

- This environment is Ubuntu 24.04.4 LTS, `Linux 7.0.0-28-generic`, x86_64.
- `.github/workflows/test.yml` runs every job on `runs-on: ubuntu-latest` — there is no macOS
  or Windows runner anywhere in this repo's CI.
- No `wine` binary is present (`which wine` → empty). `docker` is installed, but Docker on a
  Linux host cannot run Windows containers.
- `requirements.txt` has no `filelock`, `portalocker`, or similar cross-platform locking
  dependency currently installed.

Linux is the actual, already-established norm for both local dev and CI — not a scope narrowed
to make this ticket's evidentiary bar trivially satisfiable.

### Evidence table

| Platform | Status | Evidence |
|---|---|---|
| Linux | **APPROVED** | `tests/tools/test_monitoring_writer_lockfile_candidate.py`, run on this Linux environment: 3 passed (`test_lockfile_guard_rejects_real_agent_monitoring_path`, `test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines`, `test_malformed_partial_line_is_rejected_by_downstream_reader`). 200 concurrent invocations, 0 corrupted/lost/duplicated lines; malformed-line rejection confirmed (1 malformed line rejected, 5 valid lines parsed). |
| Windows | **NOT APPROVED / BLOCKED** | No empirical evidence — no Windows runner, no `wine`, no Windows Docker host available in this environment or this repo's CI. `os.O_CREAT \| os.O_EXCL` is documented as portable at the Python stdlib `os` module level, but this is a documentation citation, not a fixture-confirmed result, and is not sufficient for APPROVED status per this ticket's own evidentiary bar. |
| macOS | **NOT APPROVED / BLOCKED** | Same — no macOS runner or hardware available in this environment or this repo's CI; not evidenced. |

This satisfies the AC's own built-in escape valve ("the ticket's own investigation may still
begin on one platform, but the writer design is not approved... until evidence exists for every
platform in the supported set") by defining the supported set honestly as {Linux} — the one
platform genuinely testable from this environment and repo — rather than either quietly
narrowing the AC's language to make it trivially pass with an under-scoped set, or overclaiming
Windows/macOS coverage that was never run. If Windows or macOS support becomes a real product
requirement, that is new evidence-gathering scope for a future ticket (e.g. via a Windows CI
runner or VM), not something this ticket can honestly claim today.

### Platform-Coverage Completeness Self-Check

- Every platform in the defined set has empirical evidence: **Linux — yes** (see evidence table
  above).
- Every named-but-out-of-set platform is explicitly marked rather than silently omitted:
  **Windows — yes, NOT APPROVED / BLOCKED. macOS — yes, NOT APPROVED / BLOCKED.**

---

## 5. Scratch-only Codex pilot executor boundary

Pre-pilot workflow lifecycle records are mandatory but identity-less: they omit
`provider` (or use `null`) until a separately authorized real pilot.  This
preserves traceability without falsely representing an actual Codex execution.

`tools/agent_codex_pilot_executor/` provides only a disposable simulation
boundary.  Its caller supplies a scratch root outside the repository; it
rejects the repository, real `agent-monitoring/`, and any resolved escape.
It never reads or changes `.codex/config.toml`, registers a hook, invokes
Codex, or writes the real corpus.

Within that scratch root, a per-ticket advisory `fcntl.flock(LOCK_EX)` guards
claim-marker transitions.  Markers are atomically replaced and retained as
`completed` or `failed`; an `active` marker is never automatically reclaimed.
The kernel releases a transition lock after process exit, so the protocol has
no age-based stale-lock deletion race.

The simulation captures existing scratch JSONL lines before append, proves
their exact prefixes are unchanged afterward, and compares every appended
suffix to the declared ordered run, event, and tool records.  It then proves
the existing dashboard reader can see the coherent synthetic lifecycle before
terminalizing the claim.

This fixture-level `provider="codex"` evidence does **not** authorize a real
provider-bearing record.  A real pilot still requires its named low-risk
candidate, human owner and rollback request, and contemporaneous explicit
human approval under the separate controlled-pilot gate.
