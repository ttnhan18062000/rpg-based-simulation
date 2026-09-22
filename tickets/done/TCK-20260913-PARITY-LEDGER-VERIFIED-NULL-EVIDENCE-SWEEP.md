---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
phase: done
date: 2026-09-13
tags: [testing, registry]
---

# TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP

## Title
A `status: verified` parity ledger entry can name a class that no longer exists in `src/` at all —
a dangling citation, not merely a missing one

## Status
DONE

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

**Picked up 2026-09-21** as part of a batch with `TCK-20260921-CAVEMAN-CLOSE-OUT`. See
Implementation Notes / Completion Summary for the result.

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
- [x] A ledger-wide count of `status: verified` entries whose named class/symbol is confirmed
      absent from `src/` (dangling), distinct from — and not double-counting — the bare-missing-
      citation corpus `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` already measured. Result:
      2 of 1888 (`INFRA-228`, `WORLD-CULT-002`); see `investigation.md` for the full accounting of
      why the other 154 initial hits (120 strong-candidate + 34 module-path) were false positives.
- [x] Each hit independently re-verified via git history, not present-day grep alone, before
      correction. `git log --diff-filter=D --follow` for both confirmed entries' deleted paths.
- [x] Every confirmed dangling entry corrected via `parity_ledger_writer.py`, recording the
      dangling reference as evidence, never repointed at a plausible substitute. `INFRA-228`
      downgraded to `missing` (not repointed — the one relevant successor investigation declines to
      confirm one). `WORLD-CULT-002`'s stale consumption citation was repointed, but only after
      direct code-level confirmation (CERTAIN) that both real consumers satisfy the law's required
      non-mutation property — not a "plausible-looking substitute," a verified one.
- [x] Cross-referenced explicitly against `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` so a
      reader of either ticket understands which owns which defect. See Related Tickets (unchanged)
      and `investigation.md`'s Related section.

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
`stored_artifacts/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP/` (plan.md,
investigation.md, test_plan.md).

## Related Code Areas
- `tools/parity_ledger_writer.py` (`write_entry()`, `validate_entry()` — the sanctioned write path
  this sweep's corrections must go through)
- `tools/parity_index.py` (the derived SQLite index rebuilt on every `write_entry()` call — useful
  for querying `status`/`test_path` across all shards without hand-parsing YAML)

## Assumptions / Open Questions
Resolved: a corpus-wide sweep of all 1888 `status: verified` entries (not just `PROG-014`'s own
file) found exactly 2 additional dangling/stale-citation entries — see `investigation.md`. `PROG-014`
itself was already corrected (`status: missing`) before this sweep began, by
`TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` — confirmed directly against `origin/main`
during gate review, not a gap in this sweep's own pipeline.

## Implementation Notes
See `stored_artifacts/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP/investigation.md`
for the full method, false-positive accounting, and the two confirmed findings. Both corrections
applied via `tools/parity_ledger_writer.py::write_entry()`:
- `INFRA-228`: `status: verified` → `missing`; `test_path` cleared (cited function does not exist);
  `divergence_note` added naming both the open successor question
  (`TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION`) and the one surviving
  sub-claim (module-level `runtime_content_source` default), per `rpg-feature-planning`'s and
  `agent-working-design`'s review.
- `WORLD-CULT-002`: `status: verified` unchanged (core claim + test independently sound);
  `v2_evidence`'s stale consumption-site citation re-pointed to the two real current call sites,
  confirmed CERTAIN by direct code read before writing.

`python3 tools/parity_index.py build` run as a separate, visible Bash call after both writes (the
writer itself already rebuilds the index in-process; the separate call is what the
`parity_write_safety` retro metric detects, per the writer module's own docstring).

The method's own limitation (existence-check, not correctness-check) is stated explicitly in
`investigation.md` — the other 1886 entries passed "every cited symbol resolves," not "the entry is
correct."

## Test Summary
53 passed: `tests/tools/test_parity_ledger_writer.py`, `tests/tools/test_parity_ledger_schema.py`,
`tests/tools/test_parity_ledger_scan.py` (scoped, via
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`). Both edited entries individually
validated against `docs/parity_ledger/schema.json`'s `items` sub-schema (pass). `git diff` confirms
only the two intended entries changed in their respective shards. See
`stored_artifacts/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP/test_plan.md` for full
detail, including the pre-write factual verification for `WORLD-CULT-002`'s re-point.

## Files Changed
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-228` downgraded to `missing`.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-CULT-002`'s consumption citation re-pointed.
- `docs/REGISTRY.yaml` — regenerated (unconditional post-migration self-check per closure process).
- `staging_artifacts/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP/` → moved to
  `stored_artifacts/` at close.
- `tickets/todos/TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP.md` → `tickets/done/`.

## Completion Summary
Swept all 1888 `status: verified` parity-ledger entries across all 9 shards for `PROG-014`-shape
dangling citations. Found the corpus is, on the whole, well-maintained — the large majority of
apparent hits from an initial narrow (`src/`-only) or path-substring search resolved to real,
often self-documented relocations once checked at the correct scope. Confirmed exactly 2 genuine
corrections: `INFRA-228` (a confirmed-dead class, downgraded, with the open successor question
named rather than guessed at) and `WORLD-CULT-002` (a sound core claim with one stale supporting
citation, re-pointed only after direct, CERTAIN verification). `PROG-014`, the ticket's own
motivating example, was independently confirmed already resolved before this sweep began — not a
gap in the method. The ticket's own scope boundary against
`TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` held throughout; no bare-missing-`test_path`
entries were touched.
