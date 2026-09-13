---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
phase: open
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS

## Title
1677 of 2187 parity entries are in states `validate_entry()` would reject — the writer gates new writes but is not an invariant

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`rpg-implementer` hit a parity entry (`SOC-CHRON-005`) whose `test_path` held a raw shell command
(`pytest tests/unit/domains/chronicle/test_chronicle_compiler.py -x -v`). `parity_ledger_writer.py`
rejected the whole entry when an unrelated edit forced it through validation. Reported by
`rpg-feature-planning`, who asked how many entries are in writer-invalid states.

**Measured, 2026-09-13** — every entry in `docs/parity_ledger/*.yaml` run through `validate_entry()`
read-only: **1677 of 2187 (77%) would be rejected.** They are three different problems:

| Class | Count | Shape |
|---|---|---|
| No `test_path` at all | **1536** | 1307 P0/`verified`, 222 P0/`legacy_verified`, 7 P1/`verified` |
| Malformed `test_path` | **~126** | prose, shell commands, multi-citation strings, run summaries |
| No `support_boundary` | **15** | 13 P0/`unsupported`, 2 P0/`missing` |

The first class is the substantive one: **1307 P0 entries assert `verified` with no test citation of
any kind.** That is not hand-editing — it is the ledger predating the writer
(`TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`). The writer validates what passes through it; it has
never been an invariant over the file, and nothing else checks the corpus. So the evidence-standard
question `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` raised ("what does this evidence
prove?") has a prior question underneath it: most entries carry no evidence field at all.

**This ticket also repairs a process failure of its own.** That audit's plan listed four follow-ons
"to file at close", and its closed ticket repeats them as "— follow-on ticket". **None was ever
filed.** Verified 2026-09-13: no ticket in `tickets/todos/` or `tickets/inprogress/` matches any of
them. The findings died in prose on a closed ticket — the exact pattern
`docs/plans/agent_infrastructure/reachability_verification_findings.md` describes. This ticket
carries forward follow-ons 1 and 2; follow-ons 3 (oracle parity unexercised) and 4 (`missing`
vocabulary conflates absent with unverified) are still unfiled and are named in Out of Scope so they
are not lost a second time.

## Scope
- Re-measure the three classes at implementation time (the counts move as entries are written) and
  record the numbers.
- **Add a corpus check** that runs `validate_entry()` over every on-disk entry and reports the counts,
  as a tool, not a blocking gate. It must not fail CI on landing: 77% invalid means a blocking test is
  unlandable. Decide explicitly whether it later becomes blocking with a documented baseline (the
  `test_parity_index_baseline.py` precedent) or stays a report.
- **Class 2 (~126 malformed `test_path`):** normalize through `write_entry()` only. Prose and run
  summaries move to `support_boundary`; multi-citation strings become parseable citations; shell
  commands become the node-id they invoke. Never a raw YAML edit.
- **Class 3 (15 missing `support_boundary`):** these are the pre-existing P0 `missing`/`unsupported`
  entries that Step 3a's narrowed rule now requires an explanation for. Write a real explanation per
  entry — "no explanation recorded" is itself the honest one where nothing is known.
- **Class 1 (1536 without `test_path`):** decide and record the policy. Do **not** bulk-add citations;
  there is nothing to cite. The options are to accept it as the ledger's historical baseline and freeze
  it (no new entry may omit `test_path`), or to treat P0/`verified`-without-evidence as a distinct
  reportable state. Recommend the first, with the baseline recorded, because the second is a
  multi-month re-verification project.
- Check the "never sweep" constraint (`TCK-20260705-GATE-DET-MECHANICS-AUDITOR`) is respected: it
  forbids running pytest across the corpus. Pure validation runs no tests and is cheap (2187 entries,
  sub-second), so it is not a sweep in that sense — state this rather than assume it.

## Out of Scope
- Re-verifying the behavior behind any entry, or adding tests to make claims true.
- **Still-unfiled follow-ons from `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`, named here so
  they are not lost again:** (a) oracle parity is not exercised — `test_parity_guards.py` checks the
  oracle files exist and are well-formed, nothing compares behavior to them; (b) the `missing` status
  conflates "behavior absent" with "behavior present but unverified". Both need their own tickets.
- `evidence_kind` back-fill across all shards (audit follow-on 1's second half) — this ticket's Class 1
  policy decision should come first, since back-filling a field onto entries with no evidence at all is
  premature.

## Acceptance Criteria
- [ ] The three class counts are re-measured and recorded, with the script committed so the next person
      re-runs rather than re-derives.
- [ ] A corpus validation report exists and is runnable; whether it blocks is decided and documented.
- [ ] Every Class 2 entry parses under `parity_test_path.parse_test_path_citations()`; the count of
      malformed entries reaches 0, verified by re-running the measurement.
- [ ] Every Class 3 entry has a non-empty `support_boundary`.
- [ ] Class 1 has a recorded policy decision, not silence.
- [ ] All writes went through `write_entry()`; no raw YAML edit of a ledger shard.

## Related Tickets
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done, PR #160) — source of follow-ons 1 and 2,
  and of the Step 3a rule that makes Class 3 visible.
- `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL` (done) — introduced `validate_entry()`; the corpus
  predates it.
- `TCK-20260705-GATE-DET-MECHANICS-AUDITOR` (done) — the "never sweep" constraint to respect.

## Related Docs
- `docs/parity_ledger/schema.json`
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — the "gate that cannot fail
  on existing data" pattern this is an instance of.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT/`

## Related Code Areas
- `tools/parity_ledger_writer.py` (`validate_entry`, `write_entry`)
- `tools/parity_test_path.py`
- `docs/parity_ledger/*.yaml`

## Assumptions / Open Questions
- The 1536 figure is dominated by one historical fact, not by many small causes. Confirm by sampling
  entry creation dates before accepting the "predates the writer" explanation rather than inheriting it
  from this ticket.
- Whether `legacy_verified` should be exempt from the `test_path` requirement by design — 222 P0
  entries carry it, and if the status means "verified against the legacy engine, not here", requiring a
  local test path may be the wrong rule rather than the data being wrong.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
