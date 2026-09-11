---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT
phase: open
date: 2026-09-04
tags: [testing, registry]
---

# TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT

## Title
Repo-wide audit and repair of stale tests_v2/tests/rpg parity-ledger test_path citations, including P0 entries

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
`TCK-20260904-MATERIAL-POSSESSION-PREDICATE`'s Parity phase found that `docs/parity_ledger/town_resource.yaml`
has 6 entries (`TOWN-009`, `TOWN-010`, `TOWN-013`, `TOWN-014` citing `tests_v2/parity/test_resource_interaction_parity.py`;
`TOWN-011`, `TOWN-012` citing `tests/rpg/test_resource_conservation_v2.py`) whose `test_path` values
point at test files that no longer exist anywhere in this repo — both `tests_v2/` and `tests/rpg/` as
directories are entirely absent. All 6 are `status: verified`, `priority: P0`.

A repo-wide grep found this is not isolated to one shard: `tests_v2/`-style stale citations appear in
**combat_movement.yaml (9), strategic_cognition.yaml (10), substrate.yaml (5), social_narrative.yaml
(2), world_dynamics.yaml (2), progression.yaml (1), town_resource.yaml (15)**, plus 2 more
`tests/rpg/`-style citations — roughly **44 stale citations total**, spanning multiple shards and
multiple priority levels including P0. This is a pre-2026-09-02 test-tree migration whose ledger
citations were never propagated to their post-migration equivalents.

There is already a correct, real precedent for the fix within this same shard:
`docs/parity_ledger/town_resource.yaml`'s `TOWN-005`/`TOWN-006` entries were corrected on 2026-09-02
with an inline note ("path corrected... was `tests_v2/test_occupancy_conflicts.py` — that path never
existed in this repo, only in a pre-migration test tree"), re-pointing to
`tests/unit/movement/test_occupancy_conflicts.py`. This ticket generalizes that same fix across every
remaining stale citation.

### Revised scope after investigation (2026-09-11)

Investigation (full evidence in `investigation.md`) changed the ticket materially. Scope was re-agreed
with the repository owner before planning. The original summary above is left intact as the record of
what was believed at filing.

- **28 genuinely stale entries, not ~44 — all `verified`, 27 of them P0.** Enumerated with the repo's
  own `parse_test_path_citations()` rather than a prefix grep.
- **The root cause is that `test_path` has no format contract.** It holds prose, test-run reports, and
  multi-citations. Two tools parse it by different rules, and `parity_index.py` — whose `absent_file`
  count this ticket's original acceptance criterion relied on — **is blind to 345 of 613 entries (56%),
  including 91 `verified` + P0.** That is why the stale citations went undetected.
- **14 of the 28 are phantom citations:** the cited file never existed in this repository at any point
  in its history. Those `verified` entries were never backed by a test here.
- **The `TOWN-005`/`TOWN-006` precedent is falsified.** The file its note says "never existed in this
  repo" is in git history. It should not be generalized; it is corrected in this ticket instead.

## Scope
Ordered — each step is a precondition for the next. See `plan.md`.

1. **One shared `test_path` parser.** Extract `parse_test_path_citations()` from
   `tools/gate_checks/mechanics_auditor_static.py` into `tools/parity_test_path.py`; have both it and
   `tools/parity_index.py` use it. The index stays path-level per `v1_decisions_phase0.md` — this widens
   what it can see, not what it checks.
2. **Optional `evidence_kind` field** (`existence` | `invocation` | `runtime_observation`) in the schema
   and `validate_entry()`. No enforcement rule in this ticket.
3. **Write-time format contract** in `validate_entry()`: a non-null `test_path` must parse. Applies only
   to entries being written — never a sweep, per the `TCK-20260705-GATE-DET-MECHANICS-AUDITOR` decision.
4. **Resolve the 28 entries** via `write_entry()`, P0 first, by class: A repoint (7), B deleted with no
   successor (7), C phantom (14). Before any downgrade, search the current tree for coverage of the
   entry's `text` under any name. Also correct `TOWN-005`/`TOWN-006`.
5. **Measure** against the post-Step-1 baseline (see Acceptance Criteria).

## Out of Scope
- Any change to the actual mechanics/behavior the parity entries describe — this is citation and
  evidence hygiene, not a behavior audit. If investigation of an entry finds the mechanic itself has
  drifted from its `text`, disclose it as a separate finding.
- **Enforcing** the evidence standard (forbidding `evidence_kind: existence` for `verified` P0/P1) and
  back-filling `evidence_kind` across all shards — follow-on ticket.
- Normalizing the ~127 unparseable `test_path` values not among the 28 — Step 3 prevents new ones;
  existing ones are fixed when next written.
- Symbol-level checking inside the index — deliberately path-level by prior design.
- Making oracle parity actually exercised (`test_parity_guards.py` checks oracle files exist; nothing
  compares behavior to them) — follow-on.

## Acceptance Criteria
- A fresh, complete enumeration of every stale citation across all `docs/parity_ledger/*.yaml` shards is
  recorded in investigation.md. **Done** — 28 entries, classified A/B/C.
- `parity_index.py` and `mechanics_auditor_static.py` parse `test_path` through one shared function, and
  a two-level node-id (`path::Class::method`) is accepted by both.
- `validate_entry()` rejects a non-null `test_path` that does not parse, and accepts all 10 entries in
  `TestValidateEntryAgainstRealMultiSegmentCorpus` unmodified.
- Every one of the 28 is either (a) repointed to a test that was run and passes and covers the entry's
  claim, with `evidence_kind: invocation`; or (b) set to `status: missing` with `test_path: null` and a
  `support_boundary` stating what was lost and whether the file ever existed here. No entry is left
  pointing at a nonexistent file. (Originally worded as a `divergence_note`; the schema requires that
  field only for `divergent`, so `support_boundary` is the correct field for `missing`.)
- `schema.json` and `validate_entry()` both allow a P0 entry with `status: missing`/`unsupported` to have
  a null `test_path` **only** with a non-empty `support_boundary`; every other P0 entry still requires
  `test_path` (Step 3a, approved by the repository owner 2026-09-11 after Review NEEDS_CHANGES).
- All P0 entries among the stale set are fixed first and verified.
- `absent_file` is recorded after Step 1 (expected to **rise** as newly-visible entries surface), and
  after Step 4 has decreased from that baseline by exactly the number of citations resolved. The original
  criterion measured against the pre-change count, which Step 1 would contaminate.
- `TOWN-005`/`TOWN-006` parse under the shared parser and no longer carry the falsified history claim.

## Related Tickets
- TCK-20260904-MATERIAL-POSSESSION-PREDICATE (where this gap was found)
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR (built the tolerant parser this ticket shares; source of the
  "never sweep" constraint)
- TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING (done — fixed 13 `tests_v2/` entries in
  town_resource; `TOWN-011`/`TOWN-012` cite `tests/rpg/` and were outside its scope)
- TCK-20260902-PARITY-TEST-PATH-GAP (the separate null-`test_path` state)

## Related Docs
- docs/parity_ledger/schema.json
- docs/parity_ledger/*.yaml
- docs/plans/archive/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md ("Path-only links")
- docs/plans/agent_infrastructure/reachability_verification_findings.md (Findings 1, 3, 4, 6 — on branch
  `agent-process-findings`, not yet on main)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-MATERIAL-POSSESSION-PREDICATE/
- stored_artifacts/TCK-20260705-GATE-DET-MECHANICS-AUDITOR/ (the prior format survey)
- staging_artifacts/TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT/ (this ticket)

## Related Code Areas
- docs/parity_ledger/*.yaml, docs/parity_ledger/schema.json
- tools/parity_ledger_writer.py
- tools/parity_index.py
- tools/gate_checks/mechanics_auditor_static.py
- tools/parity_test_path.py (new)
- tests/integrity/test_parity_guards.py

## Assumptions / Open Questions
- Resolved: the ~44 estimate re-enumerated to 28, and per-entry "moved vs. dropped" is resolved by
  recovering the deleted `tests_v2/` tree from git history (classes A/B/C in investigation.md).
- Open: the schema's `missing` does not distinguish "behavior absent" from "behavior present but
  unverified." For classes B and C the second is almost certainly true. This ticket uses `missing` and
  makes the distinction explicit in `support_boundary`; fixing the vocabulary is a follow-on.
- Open: Class A successors were matched by filename only. Each must be confirmed to test the entry's
  claim before repointing — `STRAT-004` shows a surviving-looking name can still have no test behind it.

## Implementation Notes
Investigate and Plan phases complete (2026-09-11). Implementation handed to `agent-working-implementer`;
Review is the next phase.

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled on completion.)
