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
  a two-level node-id (`path::Class::method`) is accepted by both. **Done** — both import
  `tools/parity_test_path.py::parse_test_path_citations` (the same object;
  `test_mechanics_auditor_static_reimports_same_function_object` asserts identity); the two-level
  node-id case is pinned by `test_two_level_node_id_is_accepted`.
- `validate_entry()` rejects a non-null `test_path` that does not parse, and accepts all 10 entries in
  `TestValidateEntryAgainstRealMultiSegmentCorpus` unmodified. **Done** — verified unmodified/still
  passing; new rejection covered by `test_writer_rejects_unparseable_test_path`.
- Every one of the 28 is either (a) repointed to a test that was run and passes and covers the entry's
  claim, with `evidence_kind: invocation`; or (b) set to `status: missing` with `test_path: null` and a
  `support_boundary` stating what was lost and whether the file ever existed here. No entry is left
  pointing at a nonexistent file. (Originally worded as a `divergence_note`; the schema requires that
  field only for `divergent`, so `support_boundary` is the correct field for `missing`.) **Done** — 9
  repointed (all citations run and passing), 19 set to `missing` with `support_boundary`, plus
  `TOWN-005`/`TOWN-006` corrected (30 entries total). Real numbers deviate from the plan's 7/7/14 split
  — see plan.md's Deviations section (COMB-008 downgraded on closer read; COMB-002 recovered via an
  independently-found real test) — `absent_file` confirms zero remaining broken citations.
- `schema.json` and `validate_entry()` both allow a P0 entry with `status: missing`/`unsupported` to have
  a null `test_path` **only** with a non-empty `support_boundary`; every other P0 entry still requires
  `test_path` (Step 3a, approved by the repository owner 2026-09-11 after Review NEEDS_CHANGES). **Done**
  — `TestStep3aLockstepWithSchemaJson` runs both representations against the same fixtures and asserts
  identical accept/reject.
- All P0 entries among the stale set are fixed first and verified. **Done** — all 28 are P0 (confirmed by
  live re-scan, not just the investigation's estimate); all resolved in Step 4, verified against a fresh
  post-fix enumeration (0 entries citing a nonexistent file).
- `absent_file` is recorded after Step 1 (expected to **rise** as newly-visible entries surface), and
  after Step 4 has decreased from that baseline by exactly the number of citations resolved. The original
  criterion measured against the pre-change count, which Step 1 would contaminate. **Done** — pre-Step-1:
  103, post-Step-1 baseline: 131 (+28), post-Step-4: 103 (-28, exactly the number of stale citations
  resolved).
- `TOWN-005`/`TOWN-006` parse under the shared parser and no longer carry the falsified history claim.
  **Done** — clean `test_path` citations, accurate deletion history (commit 6e5c2899) moved to
  `support_boundary`.

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
- docs/ai/README.md (Parity discipline bullet narrowed for the new missing/unsupported P0 carve-out)
- docs/ai/agents.md (parity-updater Entry update rules narrowed + evidence_kind noted)
- docs/testing/how_to_add_requirement_tests.md (Section 6 worked flow notes evidence_kind + the
  missing/unsupported carve-out)

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
Investigate and Plan phases complete (2026-09-11). Implementation executed 2026-09-11, all 5 plan
steps plus 3a:

- **Step 1**: Extracted `parse_test_path_citations()` (and its three regexes) from
  `tools/gate_checks/mechanics_auditor_static.py` into new `tools/parity_test_path.py`.
  `mechanics_auditor_static.py` now imports the function by name (same object, pinned by
  `test_mechanics_auditor_static_reimports_same_function_object`). `tools/parity_index.py`'s
  `_populate_ref_tables` now calls the shared parser instead of `_TEST_PATH_DECLARED_RE`, inserting
  one `test_refs` row per parsed citation (was one row per entry, only for single-citation paths).
  `_declared_test_path_exists`'s file-level `split("::", 1)[0]` check (implemented as
  `_path_resolves`) was left untouched — index stays path-level. Measured effect: `absent_file`
  rose from 103 (pre-Step-1) to 131 (post-Step-1 baseline) as 28 previously-invisible stale
  citations surfaced.
- **Step 2**: Added nullable `evidence_kind` (`existence`/`invocation`/`runtime_observation`) to
  `schema.json`'s `properties` and mirrored as an enum check in `validate_entry()`. No enforcement
  rule added (confirmed by `test_writer_accepts_verified_p0_with_existence_evidence_kind`).
- **Step 3**: `validate_entry()` now rejects a non-null `test_path` that doesn't parse via the
  shared parser, applying only to `write_entry()` calls (no sweep). Not mirrored in `schema.json`
  (JSON Schema can't express the parser's backtick/multi-citation logic, and nothing runs
  jsonschema validation over the full on-disk ledger).
- **Step 3a**: Rewrote `schema.json`'s `allOf[2]` (nested if/then/else) and `validate_entry()`'s
  mirroring block together: a P0 entry with `status` in `{missing, unsupported}` now requires
  non-empty `support_boundary` instead of `test_path`; every other P0 status is unchanged.
  `TestStep3aLockstepWithSchemaJson` runs both representations against 7 shared fixtures and
  asserts identical accept/reject. Confirmed the 15 pre-existing P0 missing/unsupported null-
  `test_path` entries (e.g. SUB-325) are unaffected by this ticket — `TestStep3aRealLegacyEntryNeedsExplanation`
  documents SUB-325 is now writable but still rejected as-is (needs its own `support_boundary`,
  not touched here — follow-on).
- **Step 4**: Re-verified the 28 entries independently (not just trusting investigation.md's class
  labels) by reading each Class A successor's actual content and running it, and by grepping
  `Compliance IDs:`/`Logic ID` header-comment tags across `tests/` as an additional cross-check.
  This surfaced two corrections beyond the plan's 7/7/14 split (documented in plan.md's
  Deviations section): **COMB-008** downgraded out of Class A (successor file exists but tests a
  different claim — typed-update preservation, not quiet-tick passive advancement); **COMB-002**
  recovered from Class B into a repoint (a real, unrelated-looking test under
  `tests/unit/domains/optimization/` genuinely invokes `LegalityServiceV2.verify_occupancy`, one
  of its two cited functions). Net: **9 repointed**, **19 set to `missing`**, plus `TOWN-005`/
  `TOWN-006` corrected — 30 entries written via `write_entry()`, all P0. Every repointed citation
  was run and confirmed passing before being written. Verified via `yaml.safe_load` diffing that
  entry counts/ids in all 7 touched shards are unchanged and only the intended fields moved.
- **Step 5**: `absent_file` 103 → 131 (Step 1) → 103 (Step 4, exactly -28). `missing_test_path`
  stayed 1315 throughout — the 19→missing entries all had a non-null (stale) `test_path` before
  and a null one after, but `missing` status is outside that count's `{verified, divergent}` scope
  in both states, so it never moved; no baseline literal update was needed (confirmed by running
  `tests/tools/test_parity_index_baseline.py`, still green).

## Test Summary
Ran (all pass): `tests/tools/test_parity_test_path.py` (new, 7 tests), `tests/tools/test_parity_index.py`
(41, incl. 1 new multi-citation test), `tests/tools/test_parity_index_baseline.py` (15, unmodified),
`tests/tools/test_parity_ledger_writer.py` (36, incl. 1 updated + 11 new), `tests/tools/test_parity_ledger_schema.py`
(7, incl. 4 new), `tests/tools/test_mechanics_auditor_static.py` (25, unmodified),
`tests/integrity/test_parity_guards.py` (unmodified), `tests/tools/test_parity_ledger_scan.py` +
`test_parity_updater_static.py` + `test_parity_prompt_ledger_file_list.py` + `test_retrieval_event_parity_check.py`
(regression check, unmodified), plus every newly-cited test node individually
(`test_occupancy_conflict_resolution`, `TestDirectiveEvent`, `test_snapshot_immutability`,
`test_law_of_capacity_enforcement`, `test_law_of_weight_enforcement`, `test_weather_modifiers`,
`test_transformations.py`, `TestCognitionProfile`,
`test_movement_legality_uses_snapshot_result_equivalent_to_current_logic`). Total: 128 tests in the
scoped regression command + 14 individually-run cited tests + 1 corrective re-run, all passing.

## Files Changed
- `tools/parity_test_path.py` (new)
- `tools/gate_checks/mechanics_auditor_static.py`
- `tools/parity_index.py`
- `tools/parity_ledger_writer.py`
- `docs/parity_ledger/schema.json`
- `docs/parity_ledger/combat_movement.yaml`
- `docs/parity_ledger/progression.yaml`
- `docs/parity_ledger/social_narrative.yaml`
- `docs/parity_ledger/strategic_cognition.yaml`
- `docs/parity_ledger/substrate.yaml`
- `docs/parity_ledger/town_resource.yaml`
- `docs/parity_ledger/world_dynamics.yaml`
- `tests/tools/test_parity_test_path.py` (new)
- `tests/tools/test_parity_index.py`
- `tests/tools/test_parity_ledger_writer.py`
- `tests/tools/test_parity_ledger_schema.py`
- `staging_artifacts/TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT/plan.md` (Deviations section added)
- `tickets/inprogress/TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT.md` (this file)
- `docs/ai/README.md` (Doc phase: narrowed the "P0 parity entries require a passing test_path" claim)
- `docs/ai/agents.md` (Doc phase: narrowed parity-updater's P0 entry-update rule + noted evidence_kind)
- `docs/testing/how_to_add_requirement_tests.md` (Doc phase: added evidence_kind step + missing/unsupported carve-out note)
- `docs/parity_ledger/infrastructure.yaml` (Parity phase: added `INFRA-415`, documenting the write-time contract change itself)

## Completion Summary
Implemented the full 6-step plan (1, 2, 3, 3a, 4, 5). A shared `parity_test_path.py` parser now
backs both `parity_index.py` and `mechanics_auditor_static.py`, closing the blind spot where the
index's own narrower regex couldn't see 345 of 613 ledger entries. `evidence_kind` is now a
schema/writer field (descriptive only, no enforcement — that's a follow-on). `validate_entry()`
gained a write-time format contract (non-null `test_path` must parse) and Step 3a's narrowed P0
rule (`missing`/`unsupported` P0 entries need `support_boundary` instead of `test_path`), with
`schema.json` kept in lockstep via a dedicated cross-check test. All 28 stale entries — plus
`TOWN-005`/`TOWN-006`'s falsified-history precedent — were resolved through `write_entry()`: **9
repointed to real, passing, on-topic tests** (evidence_kind: invocation), and **19 moved from
`verified` to `missing`** with a `support_boundary` explaining exactly what was lost (a deleted
test and its commit, or a citation to a file that never existed in this repository) and stating
plainly that `missing` here means unverified, not known-broken. This visibly downgrades 19 P0
entries' apparent evidence quality — the honest, correct result of finding they were never
actually backed by a test in this repository. Per-entry investigation caught two cases the plan's
own Class A/B/C split got wrong (COMB-008 has a same-named successor that tests something else
entirely; COMB-002 has real coverage hiding under an unrelated directory, found only by cross-
checking `Compliance IDs:` header comments) — both documented in plan.md's Deviations section.
`absent_file` moved 103 → 131 → 103 exactly as the plan predicted, and `missing_test_path`'s
baseline (1315) needed no update since `missing`-status entries fall outside its
`{verified, divergent}` scope regardless of `test_path`. Scope holds: no mechanics/behavior were
changed, only citation and evidence-contract hygiene.
