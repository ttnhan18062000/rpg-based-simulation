---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL
phase: done
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL

## Title
69 parity ledger entries left unfixed by TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS — enumerated, not silenced

## Status
DONE

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
- [x] All counts re-measured fresh via `tools/parity_corpus_check.py` before any fix work begins;
      any drift from this ticket's own recorded IDs/counts is noted, not silently assumed unchanged.
      Re-measured 3 times total (start, after PR #191 merged into main, after PR #182 merged) —
      zero drift from the ticket's own enumerated IDs every time.
- [x] Every fixable prose-run-summary entry investigated individually (not batch-guessed) and
      either fixed with a real, verified citation or explicitly recorded as "no single real
      citation identifiable" with reasoning. 59 of 63 fixed; 4 explicitly recorded as unresolvable
      (INFRA-280/302/303/304 — see Completion Summary).
- [x] `INFRA-221`/`INFRA-405`/`STRAT-236` resolved — the parser's delimiter set was safely extended
      (` | ` with required surrounding whitespace) with test coverage proving a doubled `||` (the
      one other real `|` occurrence in the whole corpus, inside INFRA-405) is never mis-split.
      INFRA-405 itself needed separate normalization (unrelated trailing-comma-annotation issue).
- [x] `INFRA-406` resolved with a verified, not guessed, determination of the real intended test.
- [x] `INFRA-TYPE-001` resolved (new small static test file,
      `tests/static/test_typecheck_gate_configured.py`, confirmed via corpus-wide grep this shape
      is a genuine one-off, not warranting a schema change).
- [x] `SOC-ABAND-TYPE-01` renamed to `SOC-ABAND-TYPE-001`, after confirming via full-repo grep no
      live file references the old id.
- [x] `tools/parity_corpus_check.py` reports `class4_bad_id_pattern: 0`.
      `class2_malformed_test_path: 4` (not 0) — explicitly justified in the Completion Summary: all
      4 remaining entries cite only frontend Vitest/Playwright tests, for which no real Python/
      pytest citation exists; extending the parser to accept them was considered and rejected
      (would silently break `mechanics_auditor_static.py::check_test_path()`'s pytest-invocation
      assumption for a different real consumer of the same shared parser).
- [x] All writes through `tools/parity_ledger_writer.py::write_entry()`; one disclosed, narrow
      exception (removing a stale duplicate `SOC-ABAND-TYPE-01` entry this same session's own
      rename write created — `write_entry()` upserts by id and has no delete API — matching this
      repo's established precedent for that exact situation).

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

See `stored_artifacts/TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL/investigation.md` for the
full per-defect-shape breakdown and `plan.md` for the shard-by-shard sequencing. Summary: fixed the
delimiter parser (one safe extension: ` | ` with required whitespace), then worked through all 68
Class 2 + 1 Class 4 entries shard by shard (combat_movement → faction → substrate → town_resource →
social_narrative/strategic_cognition → infrastructure), extracting and verifying every real
citation named in each entry's own text before normalizing `test_path`. Found and fixed several
defect shapes beyond the ticket's own three named categories (bare-comma shorthand, trailing
parentheticals/periods, line-wrap spaces, raw shell invocations, `-k`-filtered invocations,
stale/renamed citations) — all disclosed in investigation.md §2. 4 entries (INFRA-280/302/303/304)
were found genuinely unresolvable — pure frontend Vitest/Playwright evidence with no real
Python/pytest citation possible — and left untouched rather than fabricated, per investigation.md
§4's full reasoning (including why extending the shared parser to accept `.tsx`/`.ts` was
considered and rejected).

## Test Summary

New tests: `tests/tools/test_parity_test_path.py` (+2: pipe-delimiter positive case, doubled-pipe
non-match safety case) and `tests/static/test_typecheck_gate_configured.py` (+3, new file, backing
INFRA-TYPE-001). Full relevant regression suite re-run after every shard's fix batch:
`tests/tools/test_parity_ledger_writer.py`, `test_parity_test_path.py`, `test_parity_index_baseline.py`
(66 passed), then the broader `tests/tools/` + `tests/static/` + `tests/integrity/` suite at the
end (2630 passed, 26 skipped, 2 xfailed pre-existing/unrelated, 0 failed). Every citation added
was independently verified to exist (grep for the real file/function/class) before being written —
never inferred from field-name similarity alone.

## Files Changed

- `tools/parity_test_path.py` — extended `_DELIM_SPLIT_RE` to accept ` | ` (whitespace-required
  pipe delimiter), verified safe against the real corpus first
- `tests/tools/test_parity_test_path.py` — 2 new regression tests for the delimiter extension
- `tests/static/test_typecheck_gate_configured.py` (new) — real citation for INFRA-TYPE-001
- `docs/parity_ledger/combat_movement.yaml` — 11 entries fixed (COMB-295, 301-310)
- `docs/parity_ledger/faction.yaml` — 2 entries fixed (FAC-012, FAC-013)
- `docs/parity_ledger/substrate.yaml` — 2 entries fixed (SUB-383, SUB-384)
- `docs/parity_ledger/town_resource.yaml` — 5 entries fixed (TOWN-013, 014, 019, 020, 190)
- `docs/parity_ledger/social_narrative.yaml` — SOC-CROSS-EP-002, SOC-241 fixed; SOC-ABAND-TYPE-01
  renamed to SOC-ABAND-TYPE-001
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-248 fixed
- `docs/parity_ledger/infrastructure.yaml` — 34 entries fixed (INFRA-221/405/406/TYPE-001 special
  cases plus 30 prose entries); INFRA-280/302/303/304 left untouched (disclosed unresolvable)

## Completion Summary

Resolved 59 of the 68 Class 2 entries and the 1 Class 4 entry this ticket's parent
(`TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`) reported but did not fix, following its own
"enumerated, not silenced" precedent — every entry was individually investigated and either fixed
with a real, verified citation or explicitly recorded as unresolvable, never batch-guessed or
force-fixed to hit a round number.

**The remaining 4 (INFRA-280, INFRA-302, INFRA-303, INFRA-304) are honestly left unresolved, not
silently dropped.** All 4 cite only frontend Vitest/Playwright tests (`.ts`/`.tsx`/`.spec.ts`) —
there is no real Python/pytest citation these entries' own claims could ever satisfy. Extending
`tools/parity_test_path.py`'s shared parser to accept these file types was seriously considered
(4 real instances confirms this is not a one-off shape) and explicitly rejected: the parser's other
real consumer, `mechanics_auditor_static.py::check_test_path()`, unconditionally invokes
`pytest <citation>` on anything the parser accepts, and pytest cannot execute a `.tsx`/`.ts` file —
accepting the shape here would silently break real verification for a different, existing
consumer. `write_entry()`'s own validator requires `test_path` to parse on every write, so there
was no way to even persist a disclosure-only `support_boundary` update to these 4 entries without
either fabricating a fake `.py` citation (forbidden by this ticket's own hard constraint) or
bypassing `write_entry()` with a raw YAML edit to an existing historical entry (a real
corruption-risk pattern reserved for narrow, disclosed exceptions — not warranted for 4 low-urgency
entries). `tools/parity_corpus_check.py` now reports `class2_malformed_test_path: 4` (down from
68) and `class4_bad_id_pattern: 0` (down from 1) — the remaining 4 are the honest, justified floor
for this ticket's own scope, a real architectural question (frontend-test citation support) for a
future ticket to decide, not something this one should decide unilaterally.

No src/ or simulation-mechanics code touched. All writes through `write_entry()` except one
disclosed, narrow exception (removing a stale duplicate `SOC-ABAND-TYPE-01` this session's own
rename write created, since `write_entry()` has no delete API — matches this repo's established
precedent).
