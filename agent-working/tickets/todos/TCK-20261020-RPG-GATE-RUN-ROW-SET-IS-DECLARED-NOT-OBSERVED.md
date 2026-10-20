---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED
phase: open
date: 2026-10-20
tags: [testing, regression, simulation-quality]
---

# TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED

## Title
The rpg gate contract says a world's run-row set is declared by the module, not observed. The report shows a seed whose rows differ from its world's other seeds as a `contract_error`, so it is visible before the candidate step refuses it.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
rpg-planner's Lane B dry-ran harness → report → candidate (2026-10-20). The candidate refused with "row O4.accepted (group meat+plant+prepared) is absent from seed(s) [42]; every seed must report the same rows".

testing-planner checked the full-size v1 documents (run 39212800104 on 864f7b281, read-only at /mnt/data/scratch-rpg-planner/gate_v1/). The sparsity happens at full size, in every world:
- crowded_frontier: O4.accepted/meat+plant+prepared missing on each seed (1-2 rows).
- urban_political: the same on s42, s44 and s46.
- frontier_living_world: 4-9 rows missing per seed, across O2.deaths (all four groups) and O4.accepted (meat, meat+plant+prepared).

These are keyed COUNT rows: O2.deaths by cause key, O4.accepted by source key. The module emits a key only when an event happened. That run's candidate was refused earlier (no rpg-gate-candidate.json in the artifact), so it never reached this check. The report did not show it at all.

**testing-planner ruling, 2026-10-20:**
1. "Every seed must report the same rows" STANDS. Testing's tools never read an absent row as 0: a dropped row and a true zero would look the same, which is the blindness class V1/V4 just had.
2. The fix is rpg's module (rpg-planner): for each world, emit every declared `(id, group, key)` on every seed document, with `value: 0` when no event occurred. The key domain is a declared enumeration (death causes, food sources), never "keys seen in this run". It must land before the v1 record. It moves only the module's source, which the harness hash covers by name and source, as intended before v1.
3. A share or rate whose denominator can be 0 on a seed (O1.*) must have a defined value in the module, or the row is not a run row. It is never left out on that seed.
4. This ticket (testing): state the rule in the format doc, and make the mismatch visible in the report.

## Scope
1. **Format doc** (`rpg_gate_baseline_format.md`, next to the candidate's refusal list and the row-key rule):
   - A world's run-row set `(id, group, key, tick)` is declared by the module, so every seed document of a world carries the same rows.
   - A count with no events is emitted as 0.
   - A share with an empty denominator has a defined value or is not a run row.
   - The report and the candidate never impute an absent row.
   Cite this ticket.
2. **Report** (`rpg_gate_report.py`): for each world, compare the run-row sets of its seed documents.
   - Each row key absent from at least one seed, but present in another, gives ONE `no-data`/`contract_error` row for that key, detail `row absent from seed(s) [..]; every seed reports the same rows`. Show it in the markdown and count it in the tally, as for the reference-level contract_error in #666.
   - Do not change how present rows are judged.
3. **Candidate:** unchanged (it already refuses). Add a test that pins the existing refusal text for a keyed row.
4. **Stub metrics:** if `tests/helpers/rpg_gate_stub_metrics.py` cannot emit a seed with a missing keyed row, add a mode (for example `RPG_GATE_STUB_SPARSE_SEED`).
5. **Do NOT edit** `rpg_gate_harness.py`, `rpg_gate_run.py` or `tests/helpers/kernel_pinning.py`. They are the harness hash.

## Out of Scope
- rpg's module change (ruling 2), and any value, k or floor.
- Reading absent as 0, anywhere.

## Acceptance Criteria
- [ ] AC1: the format doc states the declared-row-set rule.
- [ ] AC2: a report test where one seed lacks a keyed row gives exactly one contract_error row for it, shown in the markdown and counted in the tally. When every seed has the row, there is no such row.
- [ ] AC3: offline re-run of the report on run 39212800104's documents (copy them to the scratchpad first). Quote the new row-set contract_error count per world. Before rpg's change it is >0 in all three worlds.
- [ ] AC4: the candidate refusal test passes. `git diff origin/main -- tools/test_architecture/rpg_gate_harness.py tools/test_architecture/rpg_gate_run.py tests/helpers/kernel_pinning.py` is empty.
- [ ] AC5: `tests/simulation_quality/rpg_gate/` and `tests/unit/tools -k rpg_gate` pass, and CI is green.

## Related Tickets
- TCK-20261019-RPG-GATE-REQUIRED-VALIDITY-PER-LEVEL (#663; the per-world contract checks)
- TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD (#666; the contract_error visibility pattern)
- TCK-20261019-RPG-GATE-EVERY-VALIDITY-ROW-HAS-A-KERNEL-POSITIVE (the same blindness class)

## Related Docs
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts
- (none)

## Related Code Areas
- tools/test_architecture/rpg_gate_report.py, rpg_gate_candidate.py (test only)
- tests/helpers/rpg_gate_stub_metrics.py, tests/unit/tools/test_rpg_gate_report.py

## Assumptions / Open Questions
- Not a v1 blocker by itself: the candidate already refuses, so v1 waits on rpg's dense emission whatever happens here. This ticket makes the cause visible in the report instead of only in the candidate step's summary line.
- rpg_gate_report.py is not in `_HARNESS_SOURCES`, so this does not move the harness hash.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
