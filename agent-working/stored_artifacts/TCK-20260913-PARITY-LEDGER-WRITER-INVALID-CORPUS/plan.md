---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
artifact_type: plan
phase: inprogress
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# Plan: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS

## Approach

Executed in the order the ticket itself requires: baseline fix first, then the Class 1 policy
decision, then the mechanical classes (3, 2). See `investigation.md` for full detail and the
self-caught corrections along the way.

## Files to add / change

| File | Change |
|---|---|
| `tools/parity_corpus_check.py` (new) | Report-only scan over the whole ledger, classified into the ticket's 3 named classes plus a 4th (bad id pattern) found via cross-check against the real validator. Not a CI gate. |
| `tests/tools/test_parity_index_baseline.py` | Converted the exact-equality assertion to a ratchet (`_MISSING_TEST_PATH_CEILING`, may only decrease). |
| `tests/tools/test_parity_ledger_writer.py` | `TestStep3aRealLegacyEntryNeedsExplanation` updated to document SUB-325's now-fixed state plus an independent synthetic-entry test that Step 3a's rule is still real. |
| `tools/parity_test_path.py` | Added `_DIR_RE` so a bare directory citation (a valid pytest argument `check_test_path()` already handles) parses correctly. |
| `tests/tools/test_parity_test_path.py` | 3 new tests for the directory-citation shape (accept, reject a no-trailing-slash truncation, multi-citation participation). |
| `docs/parity_ledger/{combat_movement,infrastructure,substrate}.yaml` | Class 3: 15 entries gained `support_boundary`, via `write_entry()` only. |
| `docs/parity_ledger/{combat_movement,faction,infrastructure,progression,social_narrative,strategic_cognition,substrate,town_resource,world_dynamics}.yaml` | Class 2: 51 entries' `test_path` normalized, via `write_entry()` only. |
| `tickets/inprogress/TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS.md` | Class 1 policy decision recorded (Option A: freeze, no longer provisional); Implementation Notes/Test Summary/Files Changed/Completion Summary. |

## Explicitly out of scope (per the ticket's own text, and confirmed still correct)

- Re-verifying the behavior behind any entry.
- Fabricating `test_path` for Class 1's 1537 uncited entries, or guessing a plausible-but-unnamed
  file for a Class 2 prose entry with no single specific citation.
- Reclassifying `SUB-325`/`SUB-326`'s claim framing — `docs/plans/rpg_design_roadmap/
  rpg_spatial_index_hardening_plan.md` already scopes that as its own follow-up.
- Building `legacy_unverified` (Class 1 Option C) — a multi-ticket undertaking of its own scale;
  named as a real, credible future option in investigation.md, not built here.
- `evidence_kind` back-fill across all shards, and the two still-unfiled follow-ons from
  `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (oracle parity unexercised; `missing` status
  vocabulary ambiguity) — the ticket names both explicitly as out of scope, still true.

## Acceptance-criteria map

| Ticket AC | Status |
|---|---|
| Three class counts re-measured, script committed | Done — `tools/parity_corpus_check.py`, cross-checked at zero mismatch against the real validator |
| Corpus validation report exists and is runnable; blocking decided | Done — report-only, not a CI gate (77%+ invalid at start makes a blocking gate unlandable, matching the ticket's own reasoning) |
| Every Class 2 entry parses; count reaches 0 | **Partial — 56/124 fixed (45%), 68 remain.** See investigation.md's honest accounting: the residual is prose-only citations with no single specific file ever named (guessing one would be inventing a citation), one genuine pre-existing bad citation, and one entry whose evidence is a Makefile target, not a pytest citation. Flagging for Review rather than forcing a false "0". |
| Every Class 3 entry has `support_boundary` | Done — 15/15, verified via `parity_corpus_check.py` showing `class3_no_support_boundary: 0` |
| Class 1 policy decided, not silent | Done — Option A (freeze), de-provisionalized after the baseline fix, recorded in the ticket body |
| All writes through `write_entry()` | Done — every single ledger write in this ticket went through it; verified via `git diff` showing only field-level changes, never a structural/raw edit |
| Baseline test no longer forces a hotfix for a legitimate correction; comment and assertion agree | Done — ratchet, verified to actually catch a regression (not just always-pass) |

## Risk / open item for Review

**AC #3 (Class 2 reaches 0) is not fully met, by design rather than by running out of effort
partway through** — the honest choice at 56/124 was between (a) stopping here and reporting the
real, verified residual accurately, or (b) continuing to force through entries where the only path
to a "clean" test_path is picking a file that was never specifically named, which starts to look
like inventing evidence rather than reformatting it. Chose (a). Raising this explicitly rather than
either quietly declaring the AC met or silently lowering ambition without saying so.
