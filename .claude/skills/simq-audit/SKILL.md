# simq-audit

Run the repeatable SimQ full-audit workflow: refresh the calibration corpus, diff against grade
anchors, classify drift, sync docs/parity, and finalize via chore-commit or ticket hand-off.

## Usage

```
/simq-audit
/simq-audit mode=full
/simq-audit mode=slow
/simq-audit mode=full worlds=frontier_extended,wilderness_survival
```

## Input

Parse the user's input to extract:

- `mode` — `fast` (default; `--dry-run` diff only, assumes `data/calibration/` already populated),
  `full` (re-run the engine for all fast <=500t scenarios first), or `slow` (also run the 1000t/2000t
  tier after the fast tier passes).
- `worlds` — optional comma-separated list to scope calibration re-runs (only meaningful for `mode=full`).

This workflow is invocable standalone — it does not require an open ticket to run, and by default
does not create one.

## Action

**Do not call the Workflow tool — it is not available.** Execute the workflow directly:

1. Read `.claude/workflows/simq-audit.js` in full before doing anything else.
2. Execute each phase block in order, translating JS constructs to tool calls as follows:

| JS construct | What to do |
|---|---|
| `phase('Name')` | Announce the current phase to the user |
| `log(msg)` | Output the message to the user |
| `await agent(prompt, { agentType: 'name', schema: S })` | Spawn `Agent(subagent_type: "name", prompt: prompt)`; parse its JSON response and validate it matches schema S |
| `await agent(prompt, { label: 'L' })` | Spawn `Agent(prompt: prompt)` — no specific agent type; label is for monitoring context only |
| Gate condition (e.g. `if (!updateAnchorsResult.targeted_test_passed) { ... return { status: ... } }`) | Check the agent's return value; if the gate fails, call `writeMonitoring` first, then stop and report the blocking status and re-run instruction to the user |
| `await writeMonitoring(finalStatus)` | Execute the monitoring write block defined in that function in the JS — mandatory at every exit point, including gate failures; use `python3 tools/agent-monitoring/record_run.py` and `record_events.py`, never write to those files directly |
| `return { status, ... }` | Report the final status and relevant fields to the user |

3. Carry all variables (`mode`, `worlds`, `runId`, `startTs`, `events`, `classifyResult`, etc.) across
   phases exactly as the JS does. `runId` is a synthetic ID (`SIMQ-AUDIT-<UTC timestamp from
   Recalibrate's date call, colons/dashes stripped>`) — it is not a ticket ID.

## Pipeline

1. **Recalibrate** — run `make simq-full-audit` (or `-full`/`-slow` per `mode`) via Bash inside the
   `agent()` call; capture the REGRESS rows, pytest pass/fail counts, UNCOVERED ANCHOR KEYS, and PARITY
   LEDGER CANDIDATES sections verbatim.
2. **Classify Drift** — schema-validated: classify each flagged item as `EXPECTED_DRIFT` (cites a
   specific commit/ticket), `REGRESSION`, `DA_NEEDED`, or `NO_ACTION`; compute the rollup `verdict`.
3. **Update Anchors** — schema-validated gate: edit `grade_anchors.json` +
   `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` for `EXPECTED_DRIFT` items only, then re-run a targeted pytest
   subset. Never touches `REGRESSION`/`DA_NEEDED` items — their anchors must keep failing.
4. **Sync Docs** — updates `eval_matrix_results.md`, `D20_simq_integration.md`, conditionally
   `event_type_coverage.md` and `v2_intentional_divergences.md`.
5. **Parity Check** — updates `docs/parity_ledger/*.yaml` entries flagged by `tools/simq_audit_gaps.py`,
   same verified/divergent/missing rules as `implement-ticket.js`'s Parity phase.
6. **Verify** — schema-validated DoD-style check: regression tests pass, zero uncovered anchor keys,
   every instructed doc touched or explicitly skipped.
7. **Report** — deterministic branch on `classifyResult.verdict` (no `agent()` call for the branch
   itself):
   - `no_regression` → suggests a `chore: SimQ audit <date> — <N> anchors refreshed, no regressions`
     commit message. Does **not** touch `tickets/`. Returns `DONE_NO_TICKET`.
   - `regression` or `needs_da_decision` → spawns one ticket via the `ticket-scoper` role (same
     `TICKET_SCHEMA` as `implement-ticket.js`'s Scope phase), pre-seeded with the specific
     regression/DA items from Classify Drift. Returns `NEEDS_TICKET` with the new ticket ID and a
     `/implement-ticket ticket_id=...` hand-off instruction. This workflow never fixes a regression or
     makes a DA ruling itself.

## Notes

- `writeMonitoring` is called at every exit path: `DONE_NO_TICKET`, `NEEDS_TICKET`,
  `ANCHORS_STILL_FAILING`, `BLOCKED`. Never write to `agent-monitoring/data/YYYY-Www/runs.jsonl` or `events.jsonl`
  directly — always go through `record_run.py` / `record_events.py`.
- The governance branch is deliberate: routine no-regression passes land as a lightweight chore commit
  with no ticket ceremony, mirroring the historical precedent of doc-sync commits with no ticket ID.
  Any pass that surfaces a genuine regression or an unresolved design-acknowledgment question always
  gets a real ticket — this workflow does not fix regressions or make DA rulings itself.
- `tools/simq_audit_gaps.py` and `make simq-full-audit` are read-only/informational by construction —
  they never write to `grade_anchors.json`, `test_grade_regression.py`, or any `docs/parity_ledger/*.yaml`
  file. Only the Update Anchors and Parity Check `agent()` phases make durable edits.
- See `docs/simulation_quality/audit_workflow.md` for the full usage doc and governance rationale.
