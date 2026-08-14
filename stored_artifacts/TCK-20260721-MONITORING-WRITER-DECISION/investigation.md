---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-DECISION
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260721-MONITORING-WRITER-DECISION

## Current Behavior

### `tools/agent-monitoring/post_tool_hook.py` (the current single writer)

- Top-level script (not importable as functions — reads `sys.stdin` immediately on import),
  executed as a subprocess by Claude Code's `PostToolUse` hook mechanism.
- Line 3: `import fcntl` — POSIX-only, no Windows equivalent (`msvcrt` is the Windows analog;
  confirmed absent from this environment's stdlib: `python3 -c "import msvcrt"` raises
  `ModuleNotFoundError`).
- Lines 65-76: builds a `record` dict with fields `session_id`, `run_id`, `seq`, `phase`,
  `agent`, `ts`, `tool`, `input_summary`, `status`, `duration_ms` — matches
  `docs/agent-monitoring/schema.md`'s `tools.jsonl` schema exactly (10 fields, all present in
  every record — confirmed against `tests/tools/test_post_tool_hook.py`'s `_RECORD_FIELDS`
  set).
- Lines 78-83 (ticket's cited "lines 3, 80-83" — line numbers shifted slightly by the current
  file state but the mechanism is identical):
  ```python
  tools_file = Path("agent-monitoring/tools.jsonl")
  tools_file.parent.mkdir(parents=True, exist_ok=True)
  with open(tools_file, "a") as f:
      fcntl.flock(f, fcntl.LOCK_EX)
      f.write(json.dumps(record, separators=(",", ":")) + "\n")
      fcntl.flock(f, fcntl.LOCK_UN)
  ```
  This is the exact mechanism the ticket describes: an advisory POSIX lock, acquired
  immediately after open, held across one JSON-line write, released explicitly (not relying
  solely on `with`-block close, though close would also release it).
- Lines 24 and 85-86: the entire body (locking included) sits inside a top-level
  `try: ... except Exception: pass` — any locking failure (unsupported platform, OS error,
  lock timeout) is silently swallowed. This fail-silent contract is load-bearing per
  `CLAUDE.md` ("Monitoring write failure must never fail the workflow") and is the reason
  `test_locking_failure_does_not_propagate` exists.
- The lock is advisory and only serializes writers that go through this same hook script
  (documented explicitly in `docs/agent-monitoring/schema.md`'s "Write locking" subsection,
  lines 253-255) — it does not protect against a non-cooperating process (e.g. a future Codex
  writer using a different write path) writing to the file directly.

### `tests/tools/test_post_tool_hook.py`

Four tests, all currently passing (confirmed via the predecessor ticket's Test Summary — not
re-run here since this ticket must not touch this file per the containment rule):
- `test_single_writer_produces_one_well_formed_line`
- `test_phase_and_agent_included_when_sidecar_present`
- `test_phase_and_agent_default_to_none_on_partial_sidecar`
- `test_concurrent_writers_produce_no_interleaved_or_truncated_lines` — **this is the
  "150-invocation concurrent-writer harness" this ticket must mirror**: 10 threads × 15
  iterations = 150 hook subprocess invocations against one shared `tools.jsonl` in a
  `tmp_path` fixture, asserting every line is independently valid JSON and all 150 expected
  records are present with none lost/duplicated/merged (lines 111-140).
- `test_locking_failure_does_not_propagate` — execs the hook source with `fcntl.flock`
  monkeypatched to raise `OSError`, asserts clean exit 0 / empty stderr (lines 143-167).

### `tools/agent-monitoring/validate.py`

Read-side only; does not write to `tools.jsonl`. Relevant to this ticket only as evidence of
how prior legacy-schema drift was handled (read-side normalization, not write-time or
historical-data changes) — `LEGACY_COMPLETION_FIELDS` / `LEGACY_TERMINAL_STATUS_VALUES`
(lines 31-41) is the precedent pattern: normalize interpretation at read time, never rewrite
existing JSONL lines. This same "read-side absorbs legacy variance, write-side stays
append-only" pattern is directly relevant to how a future `provider`/`execution_id` schema
field rollout should be evidenced (old records readable as `provider: claude-code` per the
source plan, no destructive rewrite).

## Mechanics / Engine Constraints

Not applicable. This ticket concerns dev-tooling/agent-orchestration infrastructure
(`tools/agent-monitoring/`), not simulation engine mechanics. No chapter of
`docs/mechanics/` or contract in `docs/engine/` constrains this work.

## Parity Ledger Overlap

None. This is dev-tooling, not simulation-engine behavior — no `docs/parity_ledger/*.yaml`
subsystem (substrate, combat_movement, strategic_cognition, town_resource, progression,
social_narrative, world_dynamics, infrastructure) covers agent-monitoring writer internals.
Confirmed via `mcp__knowledge-search__search_docs` (no relevant hits) and by the ticket's own
"likely None" framing, consistent with the sibling `TCK-20260721-CODEX-CAPABILITY-MATRIX`
investigation's identical finding for the same batch. No parity ledger entry needs updating
as a result of this investigation.

## Prior Work

- **`TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`** (done, hotfix tier — no staging
  artifacts exist for it per the hotfix-tier rule; its full investigation/methodology lives
  in the ticket body itself, read in full). This is the direct predecessor this ticket must
  revisit. Its own "Out of Scope" explicitly deferred cross-platform (Windows) locking
  "unless the platform survey below finds POSIX-only is NOT already the established norm
  elsewhere in `tools/`" — and separately, its own Assumptions section flagged that this was
  "the first use of `fcntl` in `tools/`" (confirmed again in this investigation: `grep -rn
  "sys.platform\|os.name\|platform.system" tools/` returns zero hits — no existing
  platform-guard precedent anywhere in `tools/`). The Codex second-writer requirement is
  precisely the trigger condition that ticket named for reopening this decision.
  Methodology to mirror: 150-invocation (10 threads × 15 iterations) concurrent-writer
  subprocess harness against a `tmp_path` fixture, verifying zero corrupted/interleaved/lost
  lines. Its Implementation Notes also record a higher-stress ad hoc manual check (40×40 =
  1600 invocations, 0 corruption even pre-fix, attributed to small-write atomicity at this
  scale on this filesystem/kernel) — useful context that raw `write()`-syscall atomicity at
  small record sizes on a local/tmp filesystem may already mask real races in a short
  synthetic test; the lock remains correct as defense against the documented production
  incident regardless.
- **`TCK-20260607-MON-SCHEMA`** (done, standard tier, stored artifacts at
  `stored_artifacts/TCK-20260607-MON-SCHEMA/`) — established the original two-JSONL-file
  (`runs.jsonl`, `events.jsonl`; `tools.jsonl` added later) schema and the full
  `tools/agent-monitoring/` tool family (`record_run.py`, `record_events.py`,
  `generate_retro.py`, `validate.py`, `query.py`). Baseline for the "legacy schema
  generations" inventory this ticket's AC1 requires — `docs/agent-monitoring/schema.md`'s
  Known Limitations section (see below) is the authoritative, already-cross-referenced
  enumeration of what came after this baseline.
- **`TCK-20260713-MONITORING-SQLITE-INDEX`** — confirmed **still open**
  (`tickets/todos/agent-monitoring-derived-index/TCK-20260713-MONITORING-SQLITE-INDEX.md`,
  status OPEN, not done — the parent ticket's "if relevant" framing correctly anticipated
  this might not be closed). It is a **read-side derived index** (gitignored SQLite build
  from the existing JSONL files, explicitly "JSONL files themselves stay exactly as-is...
  this is purely a new read-path convenience layer, not a change to the write path" — its
  own Out of Scope line 43). Genuinely related-not-duplicate, as the parent ticket's
  Assumptions section states: it normalizes legacy shapes for *reading*, this ticket decides
  the *write* contract and execution identity. Its own Scope explicitly excludes any writer
  change. No conflict; the two efforts' outputs are complementary (this ticket's chosen
  execution-identity/schema fields become new columns that ticket's eventual builder would
  need to normalize, but that's out of scope here).
- **`stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/`** and
  **`stored_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/`** (both done, same batch) —
  established this batch's containment/evidence-density precedent: exact file:line citations,
  explicit "ran the test, N passed" verification style, decision-record deliverables with
  zero production-file changes, and (for CODEX-CAPABILITY-MATRIX specifically) an explicit
  practice of flagging what's *not yet* proven by direct experiment vs. documentation
  citation alone — directly relevant to this ticket's own "recommended design NOT APPROVED
  until every supported-platform's evidence exists" requirement.
- **`idea_provider_agnostic_agent_orchestration_finding_01_claude.md`** and the handoff doc —
  establish that Open Decision #3 (execution identity) and #5 (concurrent-write strategy) are
  explicitly bundled into this one ticket, per Codex's 2026-07-21 batch review, rather than
  split across this ticket and the downstream `ORCHESTRATION-CONTRACT-ADR` ticket.

## Risks and Open Questions

- **Platform testability is the central open question for the Plan phase.** This environment
  (`u24desktop`, Ubuntu 24.04.4 LTS, Linux 7.0.0-28-generic, x86_64) is Linux-only. Confirmed:
  - `python3 -c "import msvcrt"` → `ModuleNotFoundError` (Windows-only stdlib module, absent
    here — expected, but confirms no native way to exercise Windows locking semantics from
    this machine).
  - No `wine` binary present (`which wine` → empty).
  - `docker` **is** installed (`docker --version` → `Docker version 29.5.3`), but Docker on a
    Linux host cannot run Windows containers (Windows containers require a Windows host with
    the Windows-containers feature, or Docker Desktop on Windows/macOS) — this does not
    unlock real Windows testability from this sandbox.
  - CI (`.github/workflows/test.yml`) runs every job on `runs-on: ubuntu-latest` — there is
    **no macOS or Windows runner anywhere in this repo's CI**, confirming Linux-only is the
    established norm for both local dev and CI, not just this one sandbox.
  - `requirements.txt` has no `filelock`, `portalocker`, or similar cross-platform locking
    library currently installed (checked; zero matches) — any candidate design proposing a
    portable locking library would be a new dependency, not an already-vetted one.
  - **Conclusion for the Plan phase:** the AC's "every platform in the supported set" cannot
    honestly include Windows with *empirical* stress-test evidence gathered from this
    environment. The realistic options are: (a) define the supported-development-platform set
    as Linux-only (matching the actual, already-established CI/dev reality), which trivially
    satisfies "evidence on every platform in the set" with the one platform actually available;
    or (b) include Windows in the supported set on the strength of *documented behavior
    analysis* only (e.g. `msvcrt.locking()` semantics from Python's own stdlib docs, or a
    portable library's cross-platform test suite as secondary evidence) while explicitly
    marking the Windows row as **NOT APPROVED / BLOCKED** pending real hardware/CI evidence —
    this satisfies the AC's own explicit fallback clause ("must be explicitly marked NOT
    APPROVED / BLOCKED until evidence exists for every platform in that set"). This choice is
    not made by this investigation — it is squarely a Plan-phase decision, and the ticket's own
    prompt explicitly asked for it to be flagged rather than assumed.
  - A non-POSIX-locking mechanism *can* still be demonstrated from this Linux-only environment
    without literally invoking `msvcrt` — e.g. a lock-file-protocol design (candidate 1) using
    `os.O_CREAT | os.O_EXCL` atomic-create-based mutual exclusion, or an `sqlite3`
    (`BEGIN IMMEDIATE`) transaction-based lock, are both non-`fcntl` mechanisms that run
    identically on POSIX and Windows Python builds and *are* testable here. This is likely how
    the AC's "at least one non-POSIX-locking mechanism" clause gets satisfied without requiring
    literal Windows hardware — but confirming that reading of the AC, and picking the specific
    mechanism, is a Plan-phase call, not this investigation's to make.
- **The three candidate designs are explicitly a minimum comparison set, not pre-decided**
  (ticket's own Assumptions). This investigation does not recommend one — that is Plan-phase
  scope per the ticket's own "no implementation of the chosen writer design" Out-of-Scope line.
- **Execution-identity format is fully open.** The source plan's Open Decision #3 offers three
  candidate shapes (UUID execution IDs; deterministic provider/ticket/attempt identifiers; or
  both) and states "a deterministic human-readable ID plus a generated UUID is likely best for
  operations" as a *recommendation*, not a decision. The new schema fields the plan proposes
  (`provider`, `runtime`, `execution_id`, `ticket_id`, `workflow_version`,
  `hook_schema_version`) are a starting proposal, not finalized — Plan phase must decide the
  exact `execution_id` format string and whether `ticket_id` remains literally the `run_id`
  field or becomes a separate field once `run_id` no longer uniquely identifies an execution.
- **`docs/agent-monitoring/schema.md`'s Known Limitations section is the authoritative
  existing inventory this ticket's AC1 must cross-reference, not re-derive.** It already
  documents:
  1. Five legacy `runs.jsonl` schema generations without `end_ts` (enumerated at lines
     315-321): `started_at`/`finished_at`/`status`/`phases_completed`/`notes`;
     `final_status` present but `end_ts` absent; `ts_start`/`ts_end`/`result`/`agent`;
     `completed_at`/`status`; `FOLDER-*`/`EPIC-*` batch wrappers with a bare `status`.
  2. A sixth, single-record legacy shape found by exhaustive audit
     (`TCK-20260623-TYPE-CHECKER`: `"outcome":"success"`, `"phase":"implement"`, no
     `end_ts`/`final_status`/`status` at all) — deliberately not added to the allowlist
     (single-record, not worth speculative code), documented as a permanent individually-
     verified exception.
  3. The manual/ad hoc `run-{code}-{unix_ts}` and `-REDESIGN`-suffix `run_id` convention —
     pre-refactor artifacts, not reproducible by current workflow code; documented rule: any
     hand-written record must reuse the exact ticket ID verbatim, never invent a suffix.
  4. `tools.jsonl`'s own known gaps: `phase`/`agent` null for pre-`TCK-20260719-LIVE-PHASE-
     AGENT-LABEL` records (no backfill); `run_id`/`seq` null for interactive (non-workflow)
     tool calls by design, not a defect.
  5. `events.jsonl`'s `tool_call_count`/`cost_proxy_score` null for pre-cutover records (no
     backfill, `TCK-20260708-AGENT-COST-OBSERVABILITY` / `TCK-20260719-COST-PROXY-WRITE-PATH`).
  This inventory (AC1) is therefore primarily a **synthesis/cross-reference** task pulling
  these already-documented facts together with the source plan's new-field proposal and the
  "identifier gaps" framing (e.g. `run_id` doubling as both execution key and ticket ID today,
  which the source plan explicitly calls out as the thing that "cannot remain the sole
  execution key once the same ticket can be run by both providers") — not a from-scratch
  re-derivation. Plan/Implement should write the inventory as a synthesis document that cites
  `docs/agent-monitoring/schema.md`'s Known Limitations verbatim/by reference rather than
  restating it independently (risk of drift between two descriptions of the same facts).
- **Gap: no existing stored artifact or ADR precedent in this repo for a "writer design
  comparison" decision record** (distinct from the AGENTS-DIR-DISPOSITION and CODEX-
  CAPABILITY-MATRIX evidence-density precedent, which are audits/matrices, not head-to-head
  design comparisons). Plan phase should pick a comparison format (e.g. a scoring table per
  the AC's four criteria — POSIX+Windows portability, malformed-partial-line rejection,
  append-only preservation, safe two-writer concurrency — × 3 candidate designs) since no
  existing repo doc format is a direct template for this specific artifact shape.

## Anti-Drift Hazards

- **Do not modify `tools/agent-monitoring/post_tool_hook.py`.** This is the exact file the
  containment rule and this ticket's own Out of Scope forbid touching — it is also the direct
  target of the *next* (follow-on, epic-gated) implementation ticket. Any code written by this
  ticket must live in an isolated fixture/harness location (e.g. under
  `staging_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/` or a clearly-marked throwaway
  test module), never edit the real hook.
- **Do not touch any `agent-monitoring/*.jsonl` file.** No historical cleanup, no backfill, no
  even read-only "let me just check" scripts that could accidentally open the real files in
  write mode. The stress-test harness (mirroring `test_post_tool_hook.py`'s own pattern) must
  run against a `tmp_path`/temp-directory fixture file, never the real
  `agent-monitoring/tools.jsonl`.
- **Do not implement the chosen writer design.** The AC and Out of Scope are explicit: this
  ticket recommends and evidences a design; it does not wire it into `post_tool_hook.py` or
  any production path. A tempting scope-creep is to "just also update the hook since I'm
  already testing it" — resist this; that is the follow-on epic-gated ticket's job.
- **Do not silently narrow "every platform in the supported set" to "the one platform I could
  test" without explicitly marking the gap.** The AC has a built-in escape valve for this
  exact situation (explicit NOT APPROVED / BLOCKED marking) — using it correctly (rather than
  either overclaiming Windows evidence that doesn't exist, or quietly redefining the supported
  set post-hoc to make the AC trivially pass) is the anti-drift-critical part of this ticket.
- **Do not conflate this ticket's execution-identity decision with the downstream
  `ORCHESTRATION-CONTRACT-ADR` ticket's broader contract-format ADR.** Per the ticket's own
  Assumptions and the source plan's Codex-reviewed note, execution identity is decided *here*;
  `ORCHESTRATION-CONTRACT-ADR` consumes this decision as an input, it does not re-decide it.
- **Do not backfill or reinterpret existing `run_id` values in `runs.jsonl`/`events.jsonl`/
  `tools.jsonl` as part of demonstrating the new execution-identity model.** Any example
  records used to illustrate the new format must be synthetic/fixture data, not edits to real
  historical lines — consistent with the append-only precedent documented throughout
  `docs/agent-monitoring/schema.md`.
