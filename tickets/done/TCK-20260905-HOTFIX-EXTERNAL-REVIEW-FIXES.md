---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260905-HOTFIX-EXTERNAL-REVIEW-FIXES
phase: done
date: 2026-09-05
tags: [social, strategy]
---

# TCK-20260905-HOTFIX-EXTERNAL-REVIEW-FIXES

## Title
Fix 5 real issues found by an external multi-agent review of PR #128 before merge

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
An external three-agent review (architecture, mechanics/parity, workflow-discipline) of PR #128 (the
complete M5 epic) reported NEEDS_CHANGES with 5 concrete findings, none requiring re-architecting
anything already shipped. Each finding was independently re-verified against real repo state before
fixing (not trusted blindly):

1. **Real determinism bug** (architecture) — `src/domains/belief_institution/deriver.py:156` built
   `all_subjects` from an unsorted `set()` union, whose iteration order is not guaranteed stable
   across process runs (string hash randomization), feeding a durable dict's key insertion order.
   Confirmed real via direct read; the existing `test_belief_institution_derivation_is_deterministic`
   test could not have caught this since Python's hash randomization is per-process, not per-call.
2. **Missing divergence-log entries** (architecture + mechanics/parity) — `CampaignState`'s
   direct-mutation pattern (bypassing `src/engine/patches.py`, used by 4 M5 Deriver-Exporter siblings)
   and idea 54's Clan-reputation blend folded into the P0-certified `appraise_contract()` formula
   (SOC-134) were both real, undisclosed divergences from `CLAUDE.md`'s Durable State Rule / the
   Mechanics Bible's pinned formula. Confirmed via grep: zero prior mentions in
   `docs/guidelines/intentional_divergences.md`.
3. **Pre-existing broken test citation** (mechanics/parity) — SOC-134's `test_path` named
   `TestSocialAppraisalWithNarrative::test_social_appraisal_with_narrative`, a method that does not
   exist. Confirmed via `git log -S`: this predates the M5 PR entirely (commit `6e25d4f2`), but two
   M5 tickets (`REPUTATION-LOCALITY-SCOPE`, `CLAN-REPUTATION-ASSOCIATION`) both edited this exact
   entry's `v2_evidence` field without catching it.
4. **Duplicate ticket file** (workflow) — `TCK-20260905-BELIEF-INSTITUTION-DESIGN.md` existed both
   directly in `tickets/done/` (the correct, final, post-correction version) and inside
   `tickets/done/m5-history-belief/` (a stale, pre-correction snapshot missing the ticket's own
   Implement-phase corrections). Confirmed via `diff`.
5. **Ticket paperwork gaps** (workflow) — the surviving ticket's own `## Status` field still read
   `OPEN` instead of `DONE`; both M5 epic tickets (`TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION`,
   `TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF`) had zero rows in `tickets/working_log.csv`; and the
   history-and-belief epic ticket's own Acceptance Criteria inaccurately claimed all 3 child tickets
   ended up inside `tickets/done/m5-history-belief/` — only the folder itself (now containing just
   `SEQUENCE.md`) moved there; each ticket's own individual Finalize had already relocated it directly
   to `tickets/done/`.

## Scope
- `src/domains/belief_institution/deriver.py` — wrap the `all_subjects` set union in `sorted(...)`.
- `docs/guidelines/intentional_divergences.md` — add entries §2.50 (`CampaignState` direct-mutation
  pattern) and §2.51 (Clan-reputation blend in `appraise_contract()`), plus matching Summary Table rows.
- `docs/parity_ledger/social_narrative.yaml` — correct SOC-134's `test_path` to the two real test
  methods that together cover what its own `text` describes; append a note to `v2_evidence` disclosing
  the correction and its pre-existing origin.
- Delete `tickets/done/m5-history-belief/TCK-20260905-BELIEF-INSTITUTION-DESIGN.md` (stale duplicate).
- Fix `tickets/done/TCK-20260905-BELIEF-INSTITUTION-DESIGN.md`'s `## Status` field, `OPEN` → `DONE`.
- Append the two missing epic-ticket rows to `tickets/working_log.csv`.
- Correct `tickets/done/TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF.md`'s Acceptance Criteria text about
  where the 3 child tickets actually live.

## Out of Scope
- Any change to `BeliefInstitutionDeriver`'s actual formation logic, `belief_strength` formula, or any
  other behavior — this is a pure ordering-determinism fix, no output values change for any single run.
- Re-litigating idea 54's Clan-reputation-blend design decision itself — already shipped, reviewed, and
  tested by `TCK-20260904-CLAN-REPUTATION-ASSOCIATION`; this ticket only adds the missing disclosure.
- Any other parity-ledger entry's `test_path` citation beyond SOC-134 — not audited here; a repo-wide
  stale-citation audit is already tracked separately (`TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`).

## Acceptance Criteria
- [x] `BeliefInstitutionDeriver.derive()`'s output dict has deterministic key insertion order across
      repeated calls with fresh Python processes (not just within one process) — verified by the
      `sorted()` fix; existing determinism test still passes.
- [x] `docs/guidelines/intentional_divergences.md` documents both the `CampaignState` direct-mutation
      pattern and the SOC-134/appraise_contract() Clan-reputation blend, each with rationale class and
      verification path, matching this doc's own established §2.NN format.
- [x] SOC-134's `test_path` cites two real, passing test methods.
- [x] Exactly one copy of `TCK-20260905-BELIEF-INSTITUTION-DESIGN.md` exists in the repo, and it reads
      `## Status\nDONE`.
- [x] `tickets/working_log.csv` has a row for both M5 epic tickets.
- [x] `TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF.md`'s Acceptance Criteria accurately describes where
      the 3 child tickets live.

## Related Tickets
- TCK-20260823-EPIC-RPG-M5-MEMORY-REPUTATION (epic, DONE)
- TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF (epic, DONE — this hotfix corrects its own paperwork)
- TCK-20260905-BELIEF-INSTITUTION-DESIGN (DONE — this hotfix fixes its duplicate/Status field)
- TCK-20260904-CLAN-REPUTATION-ASSOCIATION (DONE — this hotfix adds its missing divergence entry)
- TCK-20260904-REPUTATION-LOCALITY-SCOPE, TCK-20260905-CHRONICLE-FIDELITY-DRIFT,
  TCK-20260905-FAME-DERIVER-LEGEND-FACT (DONE — co-cited by the new §2.50 divergence entry)
- TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT (filed follow-up, unrelated broader audit)

## Related Docs
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/social_narrative.yaml
- CLAUDE.md (Durable State Rule, Definition of Done)

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in this ticket.

## Related Code Areas
- src/domains/belief_institution/deriver.py

## Assumptions / Open Questions
None.

## Implementation Notes
Each of the 5 findings was independently re-verified against real repo state (grep, git log, diff,
direct test runs) before being fixed — none were taken on the reviewing agent's word alone. The SOC-134
broken citation is disclosed as pre-existing (predates this PR by many commits) rather than silently
folded into "M5's own bug," since attribution matters for future triage.

## Test Summary
- `tests/unit/social/test_parity_soc_134.py` — 2/2 passed (both real methods, post-fix).
- `tests/unit/domains/belief_institution/` — 12/12 passed (determinism fix, no behavior change).
- `tests/unit/domains/ tests/unit/social/ tests/architecture/` (broader regression) — 1277 passed, 1
  deselected, 0 failed.
- `python3 tools/parity_index.py build` — status: ok, 2163 entries, 9 shards.

## Files Changed
- `src/domains/belief_institution/deriver.py`
- `docs/guidelines/intentional_divergences.md`
- `docs/parity_ledger/social_narrative.yaml`
- `tickets/done/TCK-20260905-BELIEF-INSTITUTION-DESIGN.md`
- `tickets/done/TCK-20260905-EPIC-RPG-M5-HISTORY-BELIEF.md`
- `tickets/working_log.csv`
- Deleted: `tickets/done/m5-history-belief/TCK-20260905-BELIEF-INSTITUTION-DESIGN.md`

## Completion Summary
Fixed all 5 real, independently-reverified issues an external multi-agent review found in PR #128
before merge: a genuine cross-process determinism bug in `BeliefInstitutionDeriver`, two missing
`intentional_divergences.md` disclosures, one pre-existing (not M5-introduced) broken parity test
citation perpetuated across two M5 tickets, and three ticket-paperwork hygiene gaps (a stale duplicate
file, a wrong Status field, and two missing working_log.csv rows). Nothing required re-architecting
already-shipped work. Full regression re-confirmed clean after all fixes.
