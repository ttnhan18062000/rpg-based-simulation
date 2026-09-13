---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
phase: open
date: 2026-09-13
tags: [testing, registry]
---

# TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP

## Title
A `status: verified` parity ledger entry with `test_path: null` has now recurred three times in one
file — sweep the whole ledger for the same defect rather than fixing them one citation at a time

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` found and corrected `PROG-001` in
`docs/parity_ledger/progression.yaml`: `status: verified`, P0, with `test_path: null` and
`proof_type: null` — a claim marked verified that was never actually backed by a test in this
repository's history. `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`'s own investigation
found the identical shape twice more **in the same file**: `PROG-014` (`status: verified`, P0,
`test_path: null`, citing a dead V1 concept, `StatsProxy`, that doesn't exist in `src/`), and a
third, adjacent instance in `docs/compliance/checklist.md`'s `PROG-086` entry (a citation of a
citation — a test file that doesn't exist and a line reference to unrelated code).

Three occurrences of the same defect shape in one file, found across two unrelated investigations
months apart, is a pattern, not a coincidence. Per peer review: "if the ledger says 'verified'
where nothing was ever verified, everything downstream that trusts it inherits the error, and this
whole arc has been paying for exactly that." This ticket exists to find out how far the pattern
extends before more downstream work inherits a false premise from a citation nobody re-checked.

**This ticket records the need for the sweep. It does not run the sweep** — per peer instruction,
filed now, picked up later.

## Scope
- Query `docs/parity_ledger/*.yaml` (all shards, not just `progression.yaml`) for every entry where
  `status == "verified"` and `test_path is None` (and/or `proof_type is None`) — the exact shape of
  all three confirmed defects so far.
- For each hit, verify independently (do not trust the entry's own `v2_evidence` prose) whether a
  real test actually backs the claim, following the same method
  `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` used (git-history inventory of test paths
  ever committed, not just a present-day grep, to catch a test that existed once and was later
  deleted along with the claim's own justification).
- Correct each confirmed-stale entry via `tools/parity_ledger_writer.py` (the sanctioned,
  schema-validating write path) — never raw YAML edits — following `PROG-001`'s and `PROG-014`'s
  own corrected shape (`status: missing`, `support_boundary` explaining what was actually found).
- Note whether `docs/compliance/checklist.md` (a separate, non-schema-validated citation format)
  has its own version of this defect at a scale worth a follow-up sweep — this ticket's own
  PROG-086 fix was a single spot-correction, not a sweep of that file.

## Out of Scope
- Fixing the underlying gameplay/mechanics gap any individual stale entry describes (e.g. whether
  veterancy should modify combat) — that's each entry's own disposition question, decided
  separately, same as `PROG-014`'s.
- Auditing `divergent`/`unsupported`/`legacy_verified` statuses for the same defect shape — this
  ticket is scoped to `verified` + null `test_path` specifically, the exact shape confirmed three
  times so far. A different status combination showing the same trust-erosion pattern is a
  separate finding for whoever runs this sweep to surface, not pre-scoped here.

## Acceptance Criteria
- [ ] A complete, ledger-wide count of `status: verified` entries with `test_path: null` (and/or
      `proof_type: null`), broken down by shard file.
- [ ] Each hit independently re-verified (not assumed stale from the pattern alone) before
      correction — some may turn out to be genuinely verified via a citation format this scan
      doesn't recognize (e.g. `proof_type: parity` entries that verify via structural comparison
      rather than a single test file).
- [ ] Every confirmed-stale entry corrected via `parity_ledger_writer.py`, in a single batch commit
      referencing this ticket.
- [ ] A determination (not necessarily a full sweep) of whether `docs/compliance/checklist.md` has
      the same defect at meaningful scale, to decide whether it needs its own follow-up ticket.

## Related Tickets
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done — found and corrected the first
  instance, `PROG-001`; the method this sweep should reuse)
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (done — found and corrected the second and
  third instances, `PROG-014` and checklist.md's `PROG-086`, while investigating a separate
  declared-intent question; the ticket whose own finding surfaced this pattern is worth sweeping)

## Related Docs
- `docs/parity_ledger/schema.json` (the schema `parity_ledger_writer.py`'s `validate_entry()`
  enforces on write; this ticket does not propose changing it, only correcting entries that
  violate its spirit while remaining technically schema-valid)
- `docs/compliance/checklist.md` (the separate, non-schema-validated citation format that may carry
  its own version of this defect — see Scope's last bullet)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tools/parity_ledger_writer.py` (`write_entry()`, `validate_entry()` — the sanctioned write path
  this sweep's corrections must go through)
- `tools/parity_index.py` (the derived SQLite index rebuilt on every `write_entry()` call — useful
  for querying `status`/`test_path` across all shards without hand-parsing YAML)

## Assumptions / Open Questions
- Whether the full ledger has dozens of these or just a handful more is genuinely unknown — this
  ticket exists specifically because nobody has looked at the whole ledger for this shape yet, only
  at the two files two unrelated investigations happened to touch.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
