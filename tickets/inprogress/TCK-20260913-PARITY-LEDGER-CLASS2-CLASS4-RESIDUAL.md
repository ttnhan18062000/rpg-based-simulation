---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL
phase: open
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL

## Title
69 parity ledger entries left unfixed by TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS — enumerated, not silenced

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` fixed 56 of 124 Class 2 (malformed `test_path`)
entries and reported the remaining 68 honestly rather than forcing a false "0" via guessed
citations. It also found, but did not fix, 1 Class 4 entry (bad `id` pattern — a defect class its
own ticket text never named). Filed here per explicit instruction from `agent-working-design`
during that ticket's review: an acceptance-criteria caveat inside a closed ticket, pointing at
nothing, is the exact failure mode `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`'s own four
unfiled "— follow-on" notes already demonstrated — nobody noticed for days because nothing pointed
at anything real.

**Re-measure before starting** — `docs/parity_ledger/*.yaml` content moves continuously; the exact
counts/IDs below were current as of 2026-09-13 via `python3 tools/parity_corpus_check.py`, not
guaranteed still accurate. Re-run that tool first.

## Scope
- **Class 2 residual, 68 entries, by shape** (from `tools/parity_corpus_check.py`'s own
  classification; IDs below, re-verify against a fresh run before acting on any of them):
  - **Prose run-summary, no single specific file ever named (63 entries)**: `COMB-295, COMB-301,
    COMB-302, COMB-303, COMB-304, COMB-305, COMB-306, COMB-307, COMB-308, COMB-309, COMB-310,
    FAC-012, FAC-013, INFRA-230, INFRA-231, INFRA-234, INFRA-272, INFRA-273, INFRA-274, INFRA-275,
    INFRA-277, INFRA-278, INFRA-279, INFRA-280, INFRA-281, INFRA-282, INFRA-283, INFRA-284,
    INFRA-285, INFRA-286, INFRA-287, INFRA-288, INFRA-289, INFRA-290, INFRA-291, INFRA-302,
    INFRA-303, INFRA-304, INFRA-306, INFRA-307, INFRA-309, INFRA-314, INFRA-322, INFRA-323,
    INFRA-324, INFRA-325, INFRA-326, INFRA-329, INFRA-330, INFRA-331, INFRA-392, INFRA-404,
    INFRA-407, SOC-CROSS-EP-002, SOC-241, STRAT-248, SUB-383, SUB-384, TOWN-013, TOWN-014,
    TOWN-019, TOWN-020, TOWN-190`. Each describes a broad test-suite run (e.g. "full scoped pytest
    re-run across tests/unit/tactical/, tests/unit/combat/, ...") with no single citation the
    original author actually named — normalizing these means *choosing* a representative file,
    which is materially closer to inventing a citation than reformatting one. Read each entry's
    full `text`/`v2_evidence` before deciding whether a real, specific test can be identified from
    the claim itself (as was done for `SUB-325`/`SUB-326` in the parent ticket), or whether the
    entry's own claim is genuinely too broad for any single citation and needs a different kind of
    resolution (e.g. multiple real citations covering the described scope, found by reading the
    actual test files in the named directories — not guessed).
  - **Pipe-delimited multi-citation (3 entries)**: `INFRA-221, INFRA-405, STRAT-236`. The parser
    (`tools/parity_test_path.py`) only accepts `,`/`;`/`+` as multi-citation delimiters, not `|`.
    Check whether extending the delimiter set is safe (does `|` appear anywhere in a real single
    citation, where treating it as a delimiter would incorrectly split something that should stay
    together?) before treating this as automatically as simple as it looks.
  - **Genuine pre-existing bad citation (1 entry)**: `INFRA-406` — cites
    `test_wave2_wave3_agents_do_not_gain_tools_field` in `tests/tools/test_wave1_agent_tools_
    frontmatter.py`, a function name that was never real (only `test_wave2_...` and
    `test_wave3_...` exist separately, as of the parent ticket's investigation). Needs a human/
    agent decision: which of the two real tests (or both) was actually meant, verified against
    the entry's own claim text — not guessed from name similarity alone.
  - **Non-pytest evidence (1 entry)**: `INFRA-TYPE-001` — cites `make typecheck-py`, whose real
    evidence is a build/lint gate configuration (`pyproject.toml`'s `[tool.mypy]` section, a
    Makefile target, a CI step), not a pytest citation at all. The schema has no field for "this
    claim's evidence is a non-pytest gate check". Decide: extend the schema/parser to express this
    (a real, distinct need, but broader than this one entry — check whether other entries share
    this shape before building single-entry infrastructure), or find/write an actual pytest-level
    check that could stand in as the citation instead.
- **Class 4, 1 entry**: `SOC-ABAND-TYPE-01` (`social_narrative.yaml`) — `id` field has a 2-digit
  numeric suffix (`-01`) where `_ID_PATTERN` in `tools/parity_ledger_writer.py` requires exactly 3
  digits (`^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`). The entry is otherwise fully evidenced (real, parseable
  `test_path`, real `v2_evidence`) — this is purely an ID-format defect. Renaming a ledger entry ID
  has its own blast radius: grep the whole repo (docs, tools, other ledger entries' cross-
  references) for `SOC-ABAND-TYPE-01` before renaming, to confirm nothing else names it.
- Re-run `python3 tools/parity_corpus_check.py` after any fix batch to confirm the exact expected
  count delta, matching the parent ticket's own verification discipline.

## Out of Scope
- Re-verifying the behavior behind any entry (same constraint the parent ticket carried).
- Fabricating a `test_path` for any of the 63 prose-run-summary entries where no single real
  citation can be identified from the entry's own claim text after genuine investigation — if
  investigation finds no real citation is identifiable, record that honestly (a `support_boundary`-
  style disclosure, or escalate the question) rather than invent one.
- Class 1 (the 1537 entries with no `test_path` at all, and the Class 1 freeze policy) — decided
  and closed by the parent ticket; not reopened here.
- The parent ticket's own disclosed residual risks (partial-install-style gaps) — not applicable
  here, this ticket is pure ledger data + possibly parser extension, no merge-driver mechanism
  involved.

## Acceptance Criteria
- [ ] All counts re-measured fresh via `tools/parity_corpus_check.py` before any fix work begins;
      any drift from this ticket's own recorded IDs/counts is noted, not silently assumed unchanged.
- [ ] Every fixable prose-run-summary entry investigated individually (not batch-guessed) and
      either fixed with a real, verified citation or explicitly recorded as "no single real
      citation identifiable" with reasoning.
- [ ] `INFRA-221`/`INFRA-405`/`STRAT-236` resolved (either the parser's delimiter set is safely
      extended with test coverage proving `|` never appears inside a real single citation, or these
      are normalized another way).
- [ ] `INFRA-406` resolved with a verified, not guessed, determination of the real intended test(s).
- [ ] `INFRA-TYPE-001` resolved or explicitly deferred with a stated reason (e.g. "needs a schema
      change out of proportion for one entry — tracked separately").
- [ ] `SOC-ABAND-TYPE-01` renamed to a valid 3-digit id, after confirming no other file references
      the old id.
- [ ] `tools/parity_corpus_check.py` reports `class2_malformed_test_path: 0` and
      `class4_bad_id_pattern: 0`, or any remaining count is itself explicitly justified (not silent).
- [ ] All writes through `tools/parity_ledger_writer.py::write_entry()`; no raw YAML edit.

## Related Tickets
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` (done) — parent ticket; fixed Class 3 in full,
  56/124 of Class 2, decided the Class 1 policy, found but did not fix this ticket's own scope.
- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` (done, PR #160) — the ticket whose own
  unfiled follow-ons are the precedent this ticket exists to not repeat.
- `TCK-20260705-GATE-DET-MECHANICS-AUDITOR` (done) — the "never sweep" constraint; still applies
  (pure field-level validation, no pytest execution across the corpus).

## Related Docs
- `docs/parity_ledger/schema.json`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS/` — full investigation/plan
  detail on the normalizer, the verification discipline, and why these 68 weren't force-fixed.

## Related Code Areas
- `tools/parity_ledger_writer.py` (`validate_entry`, `write_entry`, `_ID_PATTERN`)
- `tools/parity_test_path.py` (`parse_test_path_citations`, delimiter handling)
- `tools/parity_corpus_check.py` (the re-measurement tool)
- `docs/parity_ledger/{combat_movement,faction,infrastructure,social_narrative,strategic_cognition,substrate,town_resource}.yaml`

## Assumptions / Open Questions
- Whether extending `_DELIM_SPLIT_RE` to accept `|` is safe without also checking whether any real,
  currently-valid single citation contains a literal `|` character (unlikely in a `.py` path or
  test name, but not yet confirmed).
- Whether `INFRA-TYPE-001`'s "evidence is a non-pytest gate check" shape is genuinely unique to
  this one entry, or common enough across the ledger to warrant a real schema field rather than a
  one-off resolution.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
