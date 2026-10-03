---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261003-APPRAISAL-READS-REPUTATION-WITHOUT-A-KNOWLEDGE-GATE
phase: open
date: 2026-10-03
tags: [social, strategy, determinism]
---

# TCK-20261003-APPRAISAL-READS-REPUTATION-WITHOUT-A-KNOWLEDGE-GATE

## Title

`SocialAppraisalSystem` reads `public_reputation` and `clan_reputation` with no knowledge gate —
catalog-CONFLICTING against PERC-01/KNOW-01, and blocked on what `public_reputation` means

## Status

BLOCKED

## Tier

standard

## Type

repair

## Priority

P2

## Request Summary

`src/systems/social_systems/appraisal.py` reads another entity's reputation directly when appraising a
contract, with no check that the appraising entity could know it:

- **line 46** — `public_reputation`
- **line 64** — `clan_reputation`

`world-rule-catalog-design` records both as *current behaviour, catalog-CONFLICTING* against
**PERC-01 / KNOW-01** (the inherited reputation-reach entry). This ticket does **not** assert the reads
are wrong — see Status.

**Why this is BLOCKED and not a hard bug.** Whether a gate-free read is "knowledge the entity cannot
legitimately have" depends on what `public_reputation` *is*, and that is an open owner decision:
**`docs/plans/systemic_world/owner_decision_memo.md` row 4** asks whether it is a publicly knowable
fact, a declared-scope claim, a derived projection, or a technical fallback. Its recorded default is
"None yet. Define its meaning and provenance first. Its current use as a global fallback for strangers
is not evidence that it is public knowledge."

The two branches, neither pre-judged:

- Owner rules **publicly knowable fact** → the read is legitimate. The catalog's PERC-01/KNOW-01
  reputation-reach entry is re-stated, the CONFLICTING evidence dissolves, and **no code changes.**
- Owner rules **anything else** → the fix needs a reputation knowledge channel that does not exist
  (perception/knowledge transfer). That is perception-foundation feature work, parked by memo rows 7
  and 8.

Either way **there is no wrong value to correct today, only an undefined meaning.** That is why this is
filed as blocked-on-a-decision rather than as a defect or as plain parked feature work.

## The pin list — expected failures if these reads are ever gated

Measured by `test-architecture-implementer`, Phase 2 social batch: mutation baseline on `appraisal.py`
at `origin/main 9640ff942` (mutmut 2.5.1, 345 mutants, 188 killed / 157 survived). **The `:46` and
`:64` reads carry 7 mutants and all 7 were killed**, so they are genuinely exercised. Record:
`tests/mutation/baselines/src_systems_social_appraisal_v1.json`; report
`docs/testing/social_test_report_2026-10-03.md` §4.

Gating these reads **will** fail the following. **These are pins on today's behaviour, not defects** —
whoever gates the reads should expect them and update them deliberately, with the reasoning recorded:

1. `tests/unit/social/test_parity_soc_134.py::test_high_public_reputation_source_accepted`
2. `tests/unit/social/test_parity_soc_134.py::test_zero_public_reputation_source_rejected`
3. `tests/unit/social/test_reputation_learning.py::test_public_vs_private_trust`
4. `tests/unit/social/test_domain_7_social.py::test_appraisal_traits`
5. `tests/unit/social/test_appraisal_logic.py::test_stranger_judgment_incorporates_clan_reputation`
6. `tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py::test_defection_degrades_clan_reputation_and_flips_stranger_loan_decision`

This list is embedded at filing time deliberately, so it is not rediscovered later as a confusing red
suite.

## Scope

- **Nothing, until memo row 4 is decided.** This ticket exists to hold the evidence and the pin list.
- On the "publicly knowable fact" branch: no code change; the catalog entry is re-stated by
  `world-rule-catalog-design` and this ticket closes decision-only.
- On any other branch: scope is defined then, and belongs to the perception-foundation epic rather
  than here.

## Out of Scope

- Changing the reads now. There is no agreed target behaviour to change them to.
- Editing the six pinned tests. They correctly pin today's behaviour.
- Re-stating the PERC-01/KNOW-01 catalog entry — `world-rule-catalog-design` owns catalog content.
- `reputation.py`'s lack of a direct test importer (77% covered through other modules) — a separate
  observation from the same batch, not a defect.

## Acceptance Criteria

1. Memo row 4 is decided, and this ticket records which branch applies.
2. **If "publicly knowable fact":** the catalog entry is re-stated, this ticket closes decision-only,
   and **no test in the pin list changes.**
3. **If any other ruling:** the work is re-scoped onto the perception-foundation epic, and the pin
   list travels with it.
4. If the reads are ever gated, each of the six pinned tests is updated deliberately with its reasoning
   recorded, and none is silently relaxed or skipped.
5. The `SOC-134` parity caveat below is addressed rather than left to be re-cited.

## Parity-ledger caveat — read before citing SOC-134

`SOC-134` records this appraisal behaviour as **verified**. That is true **of the code and not of the
rule**: it confirms the implementation matches its documented behaviour, and is *not* confirmation that
the behaviour satisfies PERC-01/KNOW-01. Do not re-cite `SOC-134` as rule confirmation. Noted here at
`world-rule-catalog-design`'s request.

Related, from the same batch and not this ticket's scope: **211 of 227 P0 entries in
`docs/parity_ledger/social_narrative.yaml` have no `test_path`** (166 verified, 44 legacy_verified, 1
missing), against CLAUDE.md's rule that P0 requires a passing one. `SOC-052` (missing, P0) cites
`tests_v2/parity/test_entity_construction.py`, which never existed in this repo.

## Related Tickets

- `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` (open, feature, parked by row 7) — touches
  `appraisal.py`; measurements here go stale when it lands.
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — memo row 8 settled which perception is
  authoritative; a reputation knowledge channel would belong to the same foundation.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` (open, moved into decision-7 foundation
  scope) — "proves a mechanism executes, not that it matters".

## Related Docs

- `docs/plans/systemic_world/owner_decision_memo.md` **row 4** — the blocking decision
- `docs/world_rules/social-lineage/social-relations.md` — PERC-01 / KNOW-01 reputation reach
- `docs/world_rules/social-lineage/lineage-descent.md` — LIN-02's collapsed step two
- `docs/mechanics/07_social_political_dynamics.md` — **note: this chapter is absent from CLAUDE.md's
  Mechanics Bible table, which stops at 06.** Raised with the owner separately.
- `docs/testing/social_test_report_2026-10-03.md` §4 — the mutation evidence
- `docs/parity_ledger/social_narrative.yaml` — `SOC-134`

## Related Stored Artifacts

- None of this ticket's own. The evidence lives in the Phase 2 social batch's report (cited above),
  which is the citation of record rather than a copy here.

## Related Code Areas

- `src/systems/social_systems/appraisal.py:46` — `public_reputation` read
- `src/systems/social_systems/appraisal.py:64` — `clan_reputation` read
- `src/systems/social_systems/reputation.py` — where a gate would most likely live

## Assumptions / Open Questions

- Whether a gate, if needed, belongs in `appraisal.py`, in `reputation.py`, or in a knowledge channel
  above both is open and depends on row 4's branch.
- `social` is a registered **tag** but **not a registered layer** (`python3 tools/layer_registry.py
  list`), so this ticket uses `layer: strategy` — its registry note covers bounded cognition, which a
  knowledge gate is. A `social` layer was deliberately **not** registered here: layer registration is
  append-only and irreversible, and that is not a call to make incidentally on a blocked ticket. Worth
  the registry owner's attention, since at least one doc already carries `layer: social`.

## Implementation Notes

_Blocked. Nothing to implement until memo row 4 is decided._

## Test Summary

_Blocked. The pin list above is the test-side record._

## Files Changed

_None yet._

## Completion Summary

_Blocked on owner decision memo row 4._
