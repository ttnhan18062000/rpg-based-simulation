---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
phase: inprogress
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS

## Title
1677 of 2187 parity entries are in states `validate_entry()` would reject — the writer gates new writes but is not an invariant

## Status
INPROGRESS

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
- **Class 1 (1537 without `test_path` at implementation time — re-measured, see investigation.md):**
  decide and record the policy. Three honest options: (a) accept it as the ledger's historical
  baseline and freeze it, so no *new* entry may omit `test_path`; (b) treat P0/`verified`-without-
  evidence as a distinct reportable state; (c) introduce an explicit status for it (e.g.
  `legacy_unverified`) so the claim these entries actually support is the one they state.

  **Decided: (a), no longer provisional** (the baseline-fix precondition below is done). No new
  code needed for the freeze itself — `validate_entry()` already requires `test_path` for any new
  `verified`/`divergent` write, and the new ratchet baseline test now also catches a count
  regression through any non-writer path. (b)'s reporting half already exists as a side effect of
  this ticket's own required tool, `tools/parity_corpus_check.py` (P0/P1 breakdown in its
  `findings`). (c) was seriously considered, not just noted and dropped: it would need a
  `schema.json` enum change, a `validate_entry()` change, and individually re-triaging up to 1537
  entries' status — a multi-ticket undertaking on the scale of this whole ticket or larger, out of
  proportion to decide unilaterally here. Remains a real, credible option for a dedicated future
  ticket if the ledger's maintainers want a sharper vocabulary than "verified" for pre-writer-era
  entries.
- **Never invent citations for Class 1.** Bulk-adding plausible test paths would convert an honest gap
  into a false record: the ledger would then assert verification that never happened, with a path that
  makes it look checked, and the fabrication would be far harder to detect afterwards than the current
  uncited state. Any change here alters status or adds an explanation; it never adds a citation that was
  not run. (Raised by `rpg-feature-planning`, 2026-09-13.)
- **Resolve the exact-equality baseline test first — it is this sweep's gate.**
  `tests/tools/test_parity_index_baseline.py:178` asserts `live_missing == 1314`, where `live_missing`
  counts entries whose status is `verified`/`divergent` **and** which lack a `test_path` (line 118).
  That set is *exactly* this ticket's Class 1 verified subset: 1307 P0/`verified` + 7 P1/`verified` =
  1314. (`legacy_verified` is excluded from the count, which is why it reads 1314 where Class 1 totals
  1536.) Consequences:
  - Option (a) freeze — the count does not move; the test is unaffected.
  - Options (b)/(c) — every entry downgraded out of `verified` **drops out of the count**, moving it
    from 1314 toward zero and breaking an exact-equality assertion at scale.
  - The test's own comment (lines 121-122) says the count "naturally drifts downward … it is not a
    frozen invariant" while the assertion demands exact equality. The comment and the assertion
    contradict each other; that contradiction is the thing to fix.
  - It has already cost four baseline-bump hotfix tickets (2026-08-30, 09-02, 09-05, 09-13), so today
    correcting a parity entry costs a ticket while leaving it wrong costs nothing — the incentive runs
    backwards. A ratchet (`live_missing` may never *increase*) is the obvious candidate and still
    catches the regression the test exists to catch, but read the four precedent tickets first: they
    may record a reason for equality that the comments do not.
  **Fix the baseline before deciding the Class 1 policy, not alongside it.** While exact equality
  stands, options (b)/(c) look expensive purely because the test would break — which biases the
  decision toward (a) for a reason that has nothing to do with what is right for the ledger. A ratchet
  (`live_missing` may never *increase*) permits the downward movement (b)/(c) would cause, so once the
  baseline is fixed the policy question is unconstrained and can be decided on its merits. Treat this
  ticket's own recommendation of (a) as provisional until then, and re-state it after.
  Raised by `rpg-feature-planning`, 2026-09-13, who then handed their standalone `layer: testing`
  ticket to this one — the baseline question is owned here, with no parallel ticket open.
- Check the "never sweep" constraint (`TCK-20260705-GATE-DET-MECHANICS-AUDITOR`) is respected: it
  forbids running pytest across the corpus. Pure validation runs no tests and is cheap (2187 entries,
  sub-second), so it is not a sweep in that sense — state this rather than assume it.

## Out of Scope
- Re-verifying the behavior behind any entry, or adding tests to make claims true.
- **Fabricating `test_path` values for uncited entries** — see the Class 1 prohibition above. This is a
  hard constraint, not a preference.
- **Still-unfiled follow-ons from `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`, named here so
  they are not lost again:** (a) oracle parity is not exercised — `test_parity_guards.py` checks the
  oracle files exist and are well-formed, nothing compares behavior to them; (b) the `missing` status
  conflates "behavior absent" with "behavior present but unverified". Both need their own tickets.
- `evidence_kind` back-fill across all shards (audit follow-on 1's second half) — this ticket's Class 1
  policy decision should come first, since back-filling a field onto entries with no evidence at all is
  premature.

## Acceptance Criteria
- [x] The three class counts are re-measured and recorded, with the script committed so the next person
      re-runs rather than re-derives. (`tools/parity_corpus_check.py`, cross-checked at zero
      mismatch against the real `validate_entry()`; also found a 4th class the ticket's own text
      didn't name — see investigation.md.)
- [x] A corpus validation report exists and is runnable; whether it blocks is decided and documented.
      (Report-only, not a CI gate — 77%+ invalid at start makes a blocking gate unlandable.)
- [ ] **Partial.** Every Class 2 entry parses under `parity_test_path.parse_test_path_citations()`; the count of
      malformed entries reaches 0, verified by re-running the measurement. **56 of 124 fixed (45%);
      68 remain** — genuinely requiring individual judgment (prose citations naming no single
      specific file, one pre-existing bad citation, one entry whose evidence is a Makefile target
      rather than a pytest citation). See investigation.md/plan.md for the full accounting and the
      reasoning for not forcing the rest through guesswork. Flagged for Review.
- [x] Every Class 3 entry has a non-empty `support_boundary`. (15/15 — `parity_corpus_check.py`
      confirms `class3_no_support_boundary: 0`.)
- [x] Class 1 has a recorded policy decision, not silence. (Option A — freeze — decided and
      de-provisionalized after the baseline fix; see Scope section above.)
- [x] All writes went through `write_entry()`; no raw YAML edit of a ledger shard.
- [x] The baseline test no longer forces a hotfix ticket for a legitimate correction, and its comment
      and assertion agree with each other. (Converted to a ratchet; verified it actually catches a
      regression, not just always-passing.)

### Downstream consequence (2026-09-13)

`rpg-feature-planning` reports the RPG side had been citing parity entries as authoritative evidence in
determinations. On this measurement they are changing method to verify against code rather than cite the
ledger. Their `STRAT-239` case — `verified`, P1, whose `v2_evidence` only confirmed a default parameter
existed while the behavior it described had never executed — was treated as an outlier at the time; at
1307 uncited P0s it reads as a sample. Worth stating in the Completion Summary: the value of this work is
partly that other sessions stop over-trusting the ledger, independent of how many entries get repaired.

## Related Tickets
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done, PR #160) — source of follow-ons 1 and 2,
  and of the Step 3a rule that makes Class 3 visible.
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` (open, RPG side, branch
  `gameplay-gaps-batch`) — **scope split agreed with `rpg-feature-planning`, 2026-09-13:** theirs
  covers the narrow *dangling-reference* case (an entry marked `verified` naming `StatsProxy`, a
  class no longer present anywhere in `src/`); this ticket covers the corpus-wide policy question
  (1307 uncited P0 entries, 60% of the ledger). Different defects, different fixes. Their case
  resolves to `missing`/`divergent` with the dangling name recorded — never re-pointed at a
  plausible substitute, per this ticket's no-fabrication constraint.
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
Built `tools/parity_corpus_check.py` (report-only, cross-checked at zero mismatch against the real
`validate_entry()` over all 2187 entries), which also surfaced a 4th defect class the ticket's own
text didn't name (`SOC-ABAND-TYPE-01`'s bad id pattern — reported, not fixed, different defect
class). Fixed the baseline test's exact-equality-vs-ratchet contradiction after checking all 6
precedent hotfix tickets found no hidden rationale for exact equality. Fixed all 15 Class 3
entries via `write_entry()`, catching and correcting a wrong claim about `SUB-325`/`SUB-326`
before it shipped (a pre-existing, deeper investigation had already answered the same question
better). Fixed 56 of 124 Class 2 entries: 51 via a verified normalizer (parenthetical stripping,
shell-command extraction, multi-file `::`-shorthand expansion, multi-target pytest parsing — every
proposed fix checked against real files/functions on disk before writing, which caught 5 real
problems including 2 bugs in my own normalizer), plus 5 via a genuine, narrow `parity_test_path.py`
parser extension (directory citations — verified end-to-end with the real venv python before
committing). Decided and recorded the Class 1 policy (Option A, freeze) once the baseline blocker
was resolved. 68 Class 2 entries remain, genuinely requiring individual judgment rather than being
mechanically safe to auto-fix — reported honestly rather than forced to a false "0".

## Test Summary
```
pytest tests/tools/test_parity_test_path.py tests/tools/test_mechanics_auditor_static.py \
       tests/tools/test_parity_ledger_writer.py tests/tools/test_parity_index.py \
       tests/tools/test_parity_index_baseline.py -q
# 120 passed
```
Every one of the 56 applied ledger fixes additionally verified against real files/functions on
disk (not just parser acceptance) before being written — this is not captured by the pytest run
above, since pytest doesn't execute against ledger content.

## Files Changed
- `tools/parity_corpus_check.py` — new.
- `tools/parity_test_path.py` — `_DIR_RE` added for directory citations.
- `tests/tools/test_parity_test_path.py` — 3 new tests.
- `tests/tools/test_parity_index_baseline.py` — ratchet conversion.
- `tests/tools/test_parity_ledger_writer.py` — `TestStep3aRealLegacyEntryNeedsExplanation` updated.
- `docs/parity_ledger/{combat_movement,faction,infrastructure,progression,social_narrative,strategic_cognition,substrate,town_resource,world_dynamics}.yaml` — 56 entries fixed via `write_entry()`.
- `staging_artifacts/TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS/{investigation.md,plan.md,test_plan.md}`.

## Completion Summary
Fixed the baseline test (exact-equality → ratchet), decided and recorded the Class 1 policy
(freeze, Option A), fixed Class 3 in full (15/15), and fixed 56 of 124 Class 2 entries with a real
parser capability extension for directory citations along the way. Found and reported a 4th defect
class the ticket's own text never named. Caught and corrected two of my own mistakes before they
shipped — a wrong claim about `SUB-325`/`SUB-326`'s spatial-index evidence, and two bugs in my own
Class 2 normalizer — both via independent verification against real files, not assumed correct.

**Honest gap, not silence**: AC #3 (Class 2 reaches 0) is only 45% met. The remaining 68 entries
are prose run-summaries naming no single specific file, one genuine pre-existing bad citation, and
one entry whose real evidence is a Makefile target rather than a pytest citation — none are safely
auto-fixable without either guessing a citation that was never actually named (this ticket's own
no-fabrication principle, applied to Class 2 in spirit) or a materially larger, separate parser
redesign. Raised explicitly for Review rather than declared complete or silently descoped.
