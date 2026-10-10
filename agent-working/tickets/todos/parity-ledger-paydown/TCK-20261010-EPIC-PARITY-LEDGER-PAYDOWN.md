---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN
phase: open
date: 2026-10-10
tags: []
---

# TCK-20261010-EPIC-PARITY-LEDGER-PAYDOWN

## Title
Epic — Parity-ledger paydown: clear the ~1,300 P0 entries with no test_path, one ledger file at a time, smallest first

## Status
EPIC_SCOPED

## Tier
epic

## Type
repair

## Priority
P2

## Request Summary
`TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC` (codebase) was closed by the owner on 2026-10-10 under
its own AC 3. It filed no child in seven days, and errors only fell from 2,862 to 2,851, all paid
down by other domains in passing. CLAUDE.md requires every `P0` parity entry to have a passing
`test_path`. That rule is broken for about 1,300 P0 entries. The CI ratchet
(`tests/codebase/test_parity_ledger_schema_gate.py`, run in `Tools · a–e`) only stops the count
from rising; it does not bring it down.

This epic carries the remainder forward as deliberate, sequenced work for the owning domains.
**lead-planner** sequenced it on 2026-10-10 and the owner approved the plan. The children are
filed by **rpg-planner**, since 7 of the 8 ledger files are rpg-owned. The owner's 2026-10-03 and
2026-10-04 rules from the closed epic carry over unchanged:
- **Schema stays strict.** A verified or divergent entry needs a test_path. A P0 entry needs a
  test_path unless it is `missing`/`unsupported` with a `support_boundary`. Downgrading to
  `legacy_verified` does not clear a P0 error.
- **`proof_type`.** Remap out-of-enum values to the existing enum, entry by entry, with a reason.
  Never extend the enum.
- **Ratchet.** Each child runs `python3 -m codebase.gates.parity_ledger_schema tighten --yes` in
  the same PR and commits `codebase/baselines/parity_ledger_schema_baseline.json`. codebase keeps
  tightening as counts fall.

Counts on main `312fbd78c` (codebase-planner, 2026-10-10). Each pair is P0 test_path errors / all
test_path errors, then extra proof_type errors.

| Order | Ledger file | Owner | P0 / all | proof_type |
|---|---|---|---|---|
| 1 | world_dynamics | rpg | 87 / 88 | 0 |
| 2 | progression | rpg | 89 / 99 | 0 |
| 3 | town_resource | rpg | 130 / 144 | 1 |
| 4 | strategic_cognition | rpg | 142 / 198 | 0 |
| 5 | infrastructure | **testing** (owner, 2026-10-10) | 149 / 162 | 19 |
| 6 | social_narrative | rpg | 164 / 208 | 0 |
| 7 | combat_movement | rpg | 238 / 265 | 4 |
| 8 | substrate | rpg | 308 / 355 | 1 |

## Scope
- One child per ledger file, split further if a file is too large for one PR (substrate, for
  example). Each child resolves every entry in its file in one of three ways:
  - cite the real test that proves the entry;
  - change its status to what the evidence supports, with the reason;
  - use an owner-approved exception mechanism, if one ever exists (none does today).
- **Order: smallest first**, so the method is proven and the ratchet visibly moves early. The table
  order above is the default.
- **Start condition:** rpg starts after its current decision-core and starvation-chain work
  (`TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` and its
  chain), not ahead of it. testing's `infrastructure` child may start any time.
- **Ownership:** `docs/parity_ledger/**` routes to rpg, `infrastructure.yaml` included. The owner
  assigned infrastructure's paydown to testing on 2026-10-10, so testing edits an rpg-owned file
  for that child. rpg-planner acknowledges this when it files the child, or the manifest gets an
  `ownership_split`. That edit is governing-file class; the owner confirms it.

## Out of Scope
- Changing the schema rules, the proof_type enum, or the ratchet mechanism.
- Bulk downgrades without per-entry evidence.
- The faction ledger, if it has no errors on current main. rpg-planner checks this when filing.

## Acceptance Criteria
1. Each listed ledger file reaches 0 P0 test_path errors and 0 proof_type errors.
2. Every child PR tightens `parity_ledger_schema_baseline.json`, and the baseline never rises.
3. A sample of the cited test_paths actually pass. Each child's own verification states which.
4. The epic closes when every child is done, or each remaining file carries an owner-recorded
   decision.

## Related Tickets
- `TCK-20261003-PARITY-LEDGER-REMEDIATION-EPIC` (predecessor; closed 2026-10-10 by codebase)
- `TCK-20261003-PARITY-LEDGER-SCHEMA-RATCHET` (the gate)
- `TCK-20261007-EPIC-DECISION-CORE-LIVE-MOTIVATION-AND-HONEST-FIGHT-OR-FLEE-INPUTS` (runs first)

## Related Docs
- `docs/parity_ledger/README.md`, `docs/parity_ledger/schema.json`
- CLAUDE.md "Parity Ledger" (the P0 rule)

## Related Stored Artifacts
None.

## Related Code Areas
`docs/parity_ledger/*.yaml`, `codebase/gates/parity_ledger_schema.py`,
`codebase/baselines/parity_ledger_schema_baseline.json`

## Assumptions / Open Questions
- Counts move as other work lands. Each child re-counts on current main when it starts.

## Implementation Notes
Scope-only. Filed by lead-planner as a handoff. rpg-planner files the children (testing-planner
files infrastructure's) and may re-order them with a stated reason.

## Test Summary
Defined by child tickets.

## Files Changed
(Child tickets.)

## Completion Summary
(Open.)
