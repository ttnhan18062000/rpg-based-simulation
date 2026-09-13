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
A `status: verified` parity ledger entry can name a class that no longer exists in `src/` at all —
a dangling citation, not merely a missing one

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
found `PROG-014` in the same file, marked `verified`, P0, `test_path: null` — but with a sharper,
more specific defect than a bare missing citation: it names `StatsProxy`, a class confirmed to
have **zero presence anywhere in `src/`** (a dead V1-era concept). This is a *dangling* reference,
not merely an absent one — the entry doesn't just lack evidence, it points at something that
doesn't exist to be evidence for. A related, adjacent instance in `docs/compliance/checklist.md`'s
`PROG-086` entry (a citation of a citation — a test file that doesn't exist and a line reference to
unrelated code) was corrected in the same ticket.

**Scope split agreed with `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`
(`agent-working-design`, branch `parity-writer-invalid-corpus`), 2026-09-13.** That ticket measured
the ledger corpus-wide and found **1677 of 2187 entries (77%)** would be rejected by
`validate_entry()` if forced through it — 1536 with no `test_path` at all (1307 P0/`verified`), the
same bare-missing-citation shape `PROG-001`/`PROG-014` share, at a scale this ticket never
attempted to measure. **This ticket does not own that corpus-wide policy question.** It is narrowed
to the distinct defect it actually found and can speak to with real evidence: an entry marked
`verified` whose named class no longer exists in `src/` at all — a dangling reference, not a bare
missing one. `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` owns the 1307-entry policy
question (freeze as historical baseline / flag as distinct reportable state / new status value);
this ticket does not duplicate that measurement or pre-empt that decision.

**This ticket records the need for the fix. It does not implement it** — filed now, picked up
later.

## Scope
- Query `docs/parity_ledger/*.yaml` (all shards, not just `progression.yaml`) for `status:
  verified` entries whose named class/function/module is **confirmed absent from `src/` entirely**
  (not merely uncited) — grep each named symbol before concluding it's dangling, the same
  verification `PROG-014` got before this ticket was filed.
- For each hit, follow the same method `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` used:
  a git-history inventory of the named symbol/path, not just a present-day grep, to distinguish
  "never existed" from "existed once, was deleted along with the claim's own justification."
- Correct each confirmed dangling entry via `tools/parity_ledger_writer.py` (the sanctioned,
  schema-validating write path) — never raw YAML edits — following `PROG-001`'s and `PROG-014`'s
  own corrected shape (`status: missing` or `status: divergent`, `support_boundary` recording the
  dangling reference as evidence of what was actually found).
- **Never repoint a dangling citation at a plausible-looking substitute** — the same constraint
  `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` states for its own corpus: an entry whose
  named class is gone becomes `missing`/`divergent` with the dangling name recorded as evidence,
  never silently re-cited against something else that merely looks related.

## Out of Scope
- **The corpus-wide policy question for entries with no `test_path` at all** (1307 P0/`verified`
  entries, ~60% of the ledger) — owned by `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`.
  This ticket does not re-measure that corpus or pre-empt that ticket's own policy decision.
- Fixing the underlying gameplay/mechanics gap any individual stale entry describes (e.g. whether
  veterancy should modify combat) — that's each entry's own disposition question, decided
  separately, same as `PROG-014`'s.
- `docs/compliance/checklist.md`'s own citation-quality question at scale — this ticket's own
  `PROG-086` fix (in the veterancy ticket that found it) was a single spot-correction, not a claim
  that file needs its own sweep.

## Acceptance Criteria
- [ ] A ledger-wide count of `status: verified` entries whose named class/symbol is confirmed
      absent from `src/` (dangling), distinct from — and not double-counting — the bare-missing-
      citation corpus `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` already measured.
- [ ] Each hit independently re-verified via git history, not present-day grep alone, before
      correction.
- [ ] Every confirmed dangling entry corrected via `parity_ledger_writer.py`, recording the
      dangling reference as evidence, never repointed at a plausible substitute.
- [ ] Cross-referenced explicitly against `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` so a
      reader of either ticket understands which owns which defect.

## Related Tickets
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done — found and corrected `PROG-001`, a
  bare-missing-citation instance; the git-history verification method this ticket should reuse)
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (done — found and corrected `PROG-014`
  (dangling `StatsProxy` reference) and checklist.md's `PROG-086`, while investigating a separate
  declared-intent question)
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` (open, `agent-working-design`, branch
  `parity-writer-invalid-corpus`) — **owns the corpus-wide policy question** (1307 P0/`verified`
  entries with no `test_path` at all, ~60% of the ledger). Scope split agreed 2026-09-13: that
  ticket covers bare-missing-citation entries at corpus scale; this ticket covers the narrower,
  distinct dangling-reference defect (`PROG-014` naming a class that no longer exists) this arc's
  own investigation actually found and verified. Never repoint a dangling citation at a plausible
  substitute — same constraint stated in both tickets.

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
- Whether other dangling-class-reference entries exist beyond `PROG-014` is genuinely unknown —
  this ticket's own scan (confirmed absent from `src/`, not merely uncited) is a different query
  than `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`'s own measurement, so its 1677-entry
  count does not directly answer how many of those are also dangling versus merely uncited.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
