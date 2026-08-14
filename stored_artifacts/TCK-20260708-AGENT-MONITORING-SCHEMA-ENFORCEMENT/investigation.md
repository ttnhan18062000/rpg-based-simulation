---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT
artifact_type: investigation
tags: [agent-monitoring, data-quality, schema]
---

# Investigation — TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT

## Current Behavior

### `tools/agent-monitoring/record_run.py` (41 lines)
- `REQUIRED = {"run_id", "start_ts", "workflow", "tier", "final_status"}` (line 8).
- `main()` parses `--data` as JSON, then line 27: `missing = REQUIRED - set(record.keys())`. This is a
  **key-presence** check only — `set(record.keys())` includes `"workflow"` even when
  `record["workflow"] is None`, so `{"workflow": null, ...}` passes today (confirms the ticket's
  problem statement). No non-null check anywhere in the file.
- No vocabulary check of any kind on `workflow`/`tier`/any other field.
- Appends the record verbatim to `agent-monitoring/runs.jsonl` (lines 32-34) and prints a `DONE:` line.
- Entire logic lives inside `main()` — there is no importable pure function (e.g. `validate_record`).
  Only entry point is CLI (`python3 record_run.py --data '...'`) or `sys.exit(1)` on failure.

### `tools/agent-monitoring/record_events.py` (58 lines)
- `REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}` (line 8).
- `VALID_STATUS = {"ok", "failed", "blocked", "skipped"}` (line 9) — this is the one existing
  vocabulary check in either file, and it already demonstrates the reject-on-bad-value pattern the
  ticket's phase/agent warning would parallel (but `VALID_STATUS` rejects; the new check must only warn).
- Per-record loop (lines 27-38): `missing = REQUIRED - set(record.keys())` — same key-presence-only gap
  as `record_run.py`. `record.get("status") not in VALID_STATUS` (line 34) — note `.get()` means a
  `None` status already produces `"invalid status 'None'"` and correctly errors, but a `None` `phase`
  or `None` `agent` passes because there's no equivalent check for those keys.
  Also note: `errors.append` continues iterating; only after the whole batch is validates does it exit
  1 on the joined error list — the null-check must slot into this same per-record loop.
- Summary truncation to 200 chars (lines 36-38) happens in the same loop, after validation — the
  non-null check must run *before* this line touches `record.get("summary", "")` since a null summary
  would currently pass through untouched (no length check on `None`).
- Also no importable pure function; only CLI entry point.

### `tools/agent-monitoring/validate.py` (133 lines)
- Existing checks: incomplete-run detection (`_record_is_complete`, lines 40-47, using
  `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES`), runs-with-no-events (lines 92-94),
  working_log cross-check (lines 96-116).
- `main()` (lines 65-132) does everything inline: loads both files, computes checks, prints
  warnings/errors, then a single summary line (`OK: {total_runs} runs, {total_events} events —
  {N} warning(s)`, line 128). **No pure function boundary** comparable to `generate_retro.py`'s
  `generate(runs, events, label)` — the drift-report section this ticket must add has nowhere to
  attach without either (a) inlining more logic into `main()` (untestable without subprocess) or
  (b) extracting a new function (e.g. `compute_drift_report(runs, events)`) the way `generate_retro.py`
  already models. Recommend (b) for testability parity with the sibling tool.
- No canonical phase/agent/tier vocabulary constant exists anywhere in `tools/agent-monitoring/`.
  `docs/agent-monitoring/schema.md`'s phase lists (lines 139, 147) are prose-only, human-maintained,
  and already out of sync with code (see Anti-Drift Hazards — `simq-audit` workflow).

### Actual call sites (workflow orchestrators)
`grep` over `.claude/workflows/*.js` confirms exactly 4 workflows currently call
`record_run.py`/`record_events.py`: `implement-ticket.js`, `implement-epic.js`, `create-tickets.js`,
`simq-audit.js`. `schema.md`'s documented `workflow` enum (line 39) lists only 3
(`implement-ticket` \| `implement-epic` \| `create-tickets`) — **`simq-audit` is missing from the
documented enum entirely**, and its `tier` value (`"standard"`, `implement-epic.js:78`... actually
`simq-audit.js:78`) and its 8 distinct `phase` values (`Recalibrate`, `Classify Drift`,
`Update Anchors`, `Sync Docs`, `Parity Check`, `Verify`, `Report`) are undocumented in `schema.md`'s
"phase values" sections (which only cover `implement-ticket` and `create-tickets`, not `implement-epic`
or `simq-audit`). This is live evidence the doc-only vocabulary source has already drifted from code
*before* this ticket lands — directly relevant to the idea doc's Open Question about where the
canonical set should live.

`pushEvent` call sites also show `agent: 'workflow'` used in `simq-audit.js` (lines 127, 406) and
`agent: 'implement-ticket-orchestrator'` used in `implement-ticket.js:718` — neither is one of the 11
documented canonical subagent filenames (`.claude/agents/*.md`). These are legitimate
orchestrator-level (non-subagent) events, not drift to warn about — the vocabulary check's "known-good
set per workflow" must include these orchestrator pseudo-agent names, or the warn-check will fire on
every single run of `simq-audit`/`implement-ticket` (specifically its Test-phase cleanup-failure event)
and become noise from day one.

## Mechanics / Engine Constraints

None. This ticket is entirely within `tools/agent-monitoring/` (Claude Code agent tooling) and
`docs/agent-monitoring/` — explicitly out of scope for the Mechanics Bible (`docs/mechanics/`) and
Engine Contracts (`docs/engine/`), per `docs/agent-monitoring/README.md`'s own scope statement:
"Claude Code agents only... Not the RPG simulation engine's Grafana/Loki/Prometheus stack." No
mechanics chapter or engine contract constrains this work.

## Parity Ledger Overlap

No entries overlap. `docs/parity_ledger/infrastructure.yaml` has three entries whose `text` mentions
"monitoring" (`INFRA-039` "Monitoring stack checks do not silently pass with empty data" — verified,
P0; `INFRA-067` "Monitoring checks fail loudly when expected data is missing" — verified, P0;
`INFRA-042` "Monitoring compatibility is verified under realistic stack conditions" — verified, P0),
but all three are scoped to the RPG simulation engine's own monitoring/telemetry stack (the
`infrastructure.yaml` subsystem is "Replay, telemetry, observability, workers" per the engine's
Mechanics/Engine boundary), not the Claude Code agent-tooling `agent-monitoring/` directory this
ticket touches — same word, different subsystem. No parity ledger entry needs to be added or updated
for this ticket; this is agent-infrastructure tooling, not simulation-engine behavior subject to the
Mechanics Bible / parity-ledger discipline. Confirm this reading holds at Plan time (the Authoritative
Mechanics Rule in `CLAUDE.md` technically applies repo-wide, but its actual content — Mechanics Bible
chapters, `docs/parity_ledger/` schema fields like `v2_evidence`/`legacy_evidence` — has no purchase
on a tool that writes JSONL bookkeeping records for AI agent runs).

## Prior Work

- **`stored_artifacts/TCK-20260706-MONITORING-REASON-CODE/`** (investigation.md, plan.md, test_plan.md) —
  closest prior pattern. Added `reason_code` to `events.jsonl` to disambiguate collapsed gate statuses.
  Established the precedent of extending `docs/agent-monitoring/schema.md` prose *and* the workflow JS
  files together, and of adding scoped unit tests to `tests/tools/test_done_checker_static.py` (not a
  new file) plus a new test class in `tests/tools/test_generate_retro.py`. This ticket differs: there is
  no existing test file for `record_run.py`/`record_events.py`/`validate.py` to extend — new test files
  are required (see test_plan.md).
- **`stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/`** — established the precedent (now codified
  in `schema.md`'s Known Limitations) that historical schema-drifted records are read-side accommodated
  in `validate.py`, never backfilled. Directly reinforces this ticket's Out of Scope: the 98
  `workflow: null` records stay untouched; only future writes are gated.
- **`docs/parity_ledger` / TCK-20260607-MON-SCHEMA, TCK-20260607-MON-CAPTURE, TCK-20260607-MON-AGENTS,
  TCK-20260607-MON-RETRO, TCK-20260607-MON-DASHBOARD** — the original 2026-06-07 epic that built
  `record_run.py`/`record_events.py`/`validate.py`/`generate_retro.py` from scratch. Confirms these
  files' `REQUIRED`-set validation pattern is original design, not organically grown — the non-null gap
  is a day-one oversight, not a regression.
- **`tests/tools/test_generate_retro.py`** — models the exact pure-function testing approach
  (`from generate_retro import generate`, constructing `runs`/`events` lists directly, asserting on
  the returned report string) this ticket should replicate for `validate.py`'s new drift-report section.
- **`tests/tools/test_validate_frontmatter.py`** (Group 7, ~line 625) — models the subprocess exit-code
  contract test pattern (`subprocess.run([...])`, asserting return code) needed for `record_run.py`/
  `record_events.py`'s CLI-level non-null rejection, since those two scripts have no importable
  validation function today (see Anti-Drift Hazards for the refactor implication).

## Risks and Open Questions

- **Blocking (per ticket's own Assumptions section):** Confirmed no current call site in
  `.claude/workflows/*.js` passes `null`/`None` for any `REQUIRED` field — all 4 workflows
  (`implement-ticket.js`, `implement-epic.js`, `create-tickets.js`, `simq-audit.js`) construct
  `record_run.py`'s `--data` JSON with literal template values (`"${tid}"`, `"${tier}"`,
  `"${finalStatus}"`, etc.), never a bare `null`. The non-null check is safe to land as specified —
  no known caller depends on passing `null` for a `REQUIRED` field. Not blocking.
- **Design decision required at Plan time, not resolved here:** where the canonical phase/agent sets
  live. The idea doc's own Open Question is unresolved and the live evidence above (simq-audit missing
  from `schema.md`'s workflow enum and phase-value sections) shows the doc-only approach has *already*
  drifted. Recommend a JSON/YAML sidecar (e.g. `docs/agent-monitoring/vocabulary.json` or
  `tools/agent-monitoring/vocabulary.py`) that both `schema.md` (via a generated/checked table) and the
  three Python tools import from — single source of truth per the idea doc's own reasoning. This is an
  implementation decision, not an investigation-blocking one, but it is the one substantive design
  choice Plan must make explicitly rather than defaulting silently.
- **Per-workflow vocabulary scoping is confirmed correct** (ticket's second Assumption) — the actual
  data shows 4 workflows with non-overlapping phase vocabularies (`implement-ticket`: 9 phases,
  `create-tickets`: 5, `implement-epic`: at least `Implement` observed, `simq-audit`: 8 distinct phases
  none of which match `implement-ticket`'s). A single global set would immediately misclassify most of
  `simq-audit`'s and `create-tickets`'s legitimate phases as drift.
- **Orchestrator pseudo-agent names must be in the known-good set**, not just the 11 subagent
  filenames — `agent: 'workflow'` (simq-audit.js) and `agent: 'implement-ticket-orchestrator'`
  (implement-ticket.js:718) are legitimate values that would otherwise fire spurious warnings on
  effectively every run. This must be resolved in Plan/Implement, not deferred, or the warn-only
  mechanism produces noise from its first real invocation and undermines the point of the feature.
  Flagging as an open question requiring a decision: should orchestrator pseudo-agents get their own
  small allowlist entry per workflow, or a blanket "workflow"/"{x}-orchestrator" wildcard rule?
- **`validate.py` has no pure-function boundary today.** Adding the drift-report section either means
  extracting `main()`'s logic into a testable function (recommended, mirrors `generate_retro.py`) or
  accepting subprocess-only test coverage (weaker, slower, harder to construct fixture data for). This
  is a real implementation-shape decision Plan should make explicit rather than have Implement decide
  ad hoc.
- **`record_run.py`/`record_events.py` have no importable validation function either** — same
  implication. Tests for "null value rejected identically to missing key" will need either a refactor
  extracting `validate_record(record) -> list[str]` (errors) or subprocess-only testing. Recommend the
  refactor for both files for testability and to avoid duplicated validation logic between the CLI
  entry point and any future caller.

## Anti-Drift Hazards

- **Do not let the vocabulary check silently become a reject.** The ticket's Out of Scope and the idea
  doc's own Open Question are explicit: warn-only, because "monitoring write failure must never fail
  the workflow" (CLAUDE.md hard rule) argues against ever making this a hard failure. Any implementation
  that calls `sys.exit(1)` for an unrecognized phase/agent value is scope creep past this ticket and
  violates that hard rule.
- **Do not touch `implement-ticket.js`/`create-tickets.js`/`implement-epic.js`/`simq-audit.js` phase-
  calling code.** Ticket's Out of Scope is explicit. The temptation here is real: fixing `simq-audit`'s
  missing documentation in `schema.md` might feel like "just updating the doc while we're in here," but
  the ticket's Related Code Areas list only the three `tools/agent-monitoring/` files — `schema.md`
  additions for `simq-audit`'s phases would be justified only if adding it to the canonical-vocabulary
  source, and even then should be the minimum addition needed to make the sidecar accurate, not a
  broader `simq-audit` documentation pass.
- **Do not backfill or rewrite `agent-monitoring/runs.jsonl`/`events.jsonl`.** Append-only precedent is
  established twice already (`TCK-20260705-MONITORING-RUNID-JOIN`'s Known Limitations section, and this
  idea doc's own explicit decision). The 98 `workflow: null` records and the 8-casing `phase` drift stay
  exactly as they are; only new writes are gated.
- **Do not conflate the non-null check with the vocabulary check's severity.** Non-null is
  unambiguous and cheap to make a hard reject (per the idea doc's own framing: "Cheap, unambiguous, no
  vocabulary maintenance required"). Vocabulary is inherently softer (new legitimate values will appear
  as workflows evolve) and must stay warn-only. Do not let one design decision bleed into the other's
  implementation (e.g. don't make vocabulary a reject "for consistency" with the non-null check, and
  don't make non-null a warning "for consistency" with vocabulary).
- **`record_events.py`'s summary-truncation code (lines 36-38) runs `len(summary)` on
  `record.get("summary", "")`.** If the non-null check is added *after* this line instead of before,
  a `None` summary would raise `TypeError: object of type 'NoneType' has no len()` before the new
  validation ever gets a chance to reject it cleanly. Ordering matters: non-null check must precede any
  existing line that assumes a field is a string/int, not just precede the final write.
