---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
phase: open
date: 2026-08-10
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL

## Title
Add a schema-validating write path for `docs/parity_ledger/*.yaml` and close the index-freshness
gap after ledger edits

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/parity_ledger/schema.json` exists (`id` pattern, required fields per `status`, P0 requiring
`test_path`, `divergent` requiring `divergence_note`) but nothing enforces it when a ledger shard
is actually written. `.claude/agents/parity-updater.md`'s "What to Do" section edits YAML via raw
`Read`/`Edit` with no validation step, and hand-orchestrated sessions do the same (confirmed:
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`'s session directly `Edit`ed
`combat_movement.yaml` and `substrate.yaml`, and its own tool history shows it searching for a
validator — `find ... validate_parity*`, `grep ... parity_ledger.*schema|jsonschema` — and finding
none).

Separately, `tools/parity_index.py` builds a derived, read-only SQLite index over the ledger
(`entry`/`impact`/`health` commands), reviewed in `docs/ai/parity_readpath_gate_a_decision.md`
(Gate A: **GO**, 66.7% vs. 4.8% recall vs. the legacy scan). That index is never kept fresh
automatically: `compute_tool_safety_metrics`'s `parity_write_safety` audit over the last 14 days
found **0** `docs/parity_ledger/*.yaml` writes that co-occurred with a `parity_index.py build` call
in the same run — every real edit leaves the derived index silently stale.

## Scope
- **Investigate (mandatory before Plan):** confirm the exact schema-validation surface
  `docs/parity_ledger/schema.json` currently expresses (which fields, which conditional
  requirements) and how `parity_index_baseline.py`/`context_packet_assembler.py` currently consume
  it read-side, to reuse rather than reinvent that logic.
- Add a schema-validating writer (CLI or importable function) that mutates a `docs/parity_ledger/
  *.yaml` shard only after validating the resulting entry against `schema.json` — reject on: bad
  `id` pattern, missing `v2_evidence`/`test_path` for `verified`/`divergent` status, missing
  `divergence_note` for `divergent`, non-null `test_path` violation for P0.
- After a successful validated write, either trigger `tools/parity_index.py`'s `build` in the same
  run, or make the resulting staleness impossible to miss (e.g. a mandatory `check-staleness` call
  wired into the same command) — pick one and justify the choice; do not leave both undone.
- Update `.claude/agents/parity-updater.md`'s "What to Do" (currently: "Read the relevant YAML
  file" / "Update the entry") to use the new write path instead of raw `Read`/`Edit`.
- Explicitly decide, and record in `investigation.md`, whether this ticket also resolves Gate A's
  two disclosed structural gaps (`docs/ai/parity_readpath_gate_a_decision.md` §6.2: `_PATH_REF_RE`
  doesn't recognize `.claude/`-prefixed paths; §6.3: `find_p0_intersection` raises uncaught
  `yaml.YAMLError` on a malformed shard) or defers them with a stated reason — do not silently
  ignore either.

## Out of Scope
- Wiring `tools/parity_index.py`'s **read** path (`entry`/`impact`/`health`) into `parity-updater`'s
  discovery step, or any other live workflow gate. `docs/ai/parity_readpath_gate_a_decision.md`'s
  GO verdict is explicitly scoped to the read-path review only and states in its own §5 that a
  **separate** Phase-3 scoping ticket must resolve §6.2/§6.3 "before writing any code" for that
  purpose — this ticket's write-safety scope is a different, narrower thing and must not be used
  to backdoor that larger decision.
- Any change to `docs/parity_ledger/*.yaml` content itself — this ticket builds tooling, not ledger
  edits.
- Broadening `schema.json` itself beyond what's needed to express the existing entry schema
  documented in CLAUDE.md's "Entry Schema" section.

## Acceptance Criteria
- [ ] The writer rejects a malformed entry (each of the conditions listed in Scope) with a clear,
      specific error — verified by a real test per condition, not one generic "invalid" test.
- [ ] A successful validated write either rebuilds the derived index in the same run or leaves an
      unmissable staleness signal — verified by a test asserting the chosen behavior actually
      happens.
- [ ] `.claude/agents/parity-updater.md` is updated to use the new write path; its existing
      "Entry Schema" section either stays accurate or is updated to match.
- [ ] Gate A's §6.2/§6.3 gaps are either fixed (with tests) or explicitly deferred with a written
      rationale in `investigation.md`/`plan.md` — not silently dropped.
- [ ] Scoped pytest run passes.

## Related Tickets
- TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (parent)
- TCK-20260731-PARITY-READPATH-GATE (DONE; Gate A review this ticket's write-safety scope sits
  alongside, without reopening its read-path decision)
- TCK-20260731-PARITY-INDEX-IMPORTER, TCK-20260731-PARITY-INDEX-BASELINE, TCK-20260731-PARITY-IMPACT-PROOF
  (DONE; built the index this ticket keeps fresh)
- TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY (DONE; built `check-staleness` — reuse, don't
  reimplement)
- TCK-20260807-PARITY-WRITE-SAFETY-METRIC-RESCOPE (DONE; defined the exact
  `parity_write_safety` co-occurrence semantics this ticket's evidence relies on)

## Related Docs
- `docs/ai/parity_readpath_gate_a_decision.md`
- `docs/parity_ledger/schema.json`
- CLAUDE.md's "Parity Ledger Files" / "Entry Schema" sections

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/parity_index.py`
- `tools/parity_ledger_scan.py`
- `tools/gate_checks/parity_updater_static.py`
- `.claude/agents/parity-updater.md`
- `docs/parity_ledger/*.yaml`
- `tests/tools/test_parity_index.py`

## Assumptions / Open Questions
- Whether the writer lives inside `tools/parity_index.py` itself or a sibling module — `parity_index.py`'s
  own docstring currently states it "implements no mutation CLI," so adding one may be better as a
  clearly-separate module rather than changing that file's own stated contract; not decided here,
  left to Investigate/Plan.
- Whether index-rebuild-on-write is the right default vs. a lighter staleness-flag — Gate A's own
  scope explicitly left workflow wiring undecided; this ticket should pick the narrowest option
  that closes the measured gap (0% co-occurrence) without reopening the broader Phase-3 question.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
