---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-HAZARD-KIND-CORPUS-WIDE
artifact_type: plan
tags: [simulation-quality, world, corpus, calibration]
---

# Implementation Plan — TCK-20260710-HAZARD-KIND-CORPUS-WIDE

## Summary

Replace the 3-world `HAZARD_KIND_MATCH_WORLDS` allowlist in
`tests/unit/worldassembly/test_corpus_diversity.py` with corpus-wide parametrization of
`test_hazard_kind_matches_populating_faction_immunity` over all 17 `data/worlds/*` world_ids,
reusing the existing `_load_resolved_spec`/`_faction_hazard_immunities`/`pytest.skip` pattern
verbatim. The investigation's dry run (executed against the live, unmodified test logic) found
**zero mismatches across all 17 worlds and 45 hazardous-populated-region checks**, including
every `bandit_road` occurrence — so no code-level exception, xfail, or skip is added for the
known `town_council`/`bandit_road` case. Instead, a documentation-only comment is added citing
`docs/guidelines/intentional_divergences.md` §2.30 and `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` so a
future reader understands why that case passes (the test's region-level "any populating faction"
matching semantics, not a content fix) rather than mistaking it for an oversight. The change is
test-file-only in `src`/content terms; three docs get closeout edits (`audit_fix_plan.md` P2-O,
`simq_development_roadmap.md` Phase 1.1, and — per this planner's judgment call below —
`SEQUENCE.md`'s now-empirically-disproven ordering rationale).

## Steps

### Step 1 — Parametrize the matching test over the full corpus

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`

**Change:** Replace the `HAZARD_KIND_MATCH_WORLDS = ["dungeon_crawl", "urban_political",
"generated_frontier_3_42"]` list (line 41) with a full-corpus source. Two acceptable
implementations, implementer's choice, both consistent with the file's existing patterns:
(a) a new constant `ALL_CORPUS_WORLDS` built by globbing `WORLDS_ROOT.iterdir()` (filtering to
directories, matching how `WORLDS_ROOT` is already used elsewhere in the file), or (b) a
constant literal list of all 17 world_ids (matching the style of `ANCHORED_WORLD_BANDS`'s keys).
Prefer (a) if it can be written as a short, readable module-level expression — it self-updates as
the corpus grows, which is the entire point of this ticket (stop reactive, per-sweep allowlist
edits). If (a) adds meaningful complexity (e.g. needs filtering out `world_index.json` or
non-world directories), fall back to (b) with an explicit literal list; either is acceptable to
this plan. Update `@pytest.mark.parametrize("world_id", HAZARD_KIND_MATCH_WORLDS)` (line 413) to
reference the new source. Do not change the test function's body (lines 425-447) — the matching
logic itself (region-level "any populating faction," `matched = any(hazard_kind in
immunities.get(f, set()) for f in populating_factions)`) is unchanged.

**Do NOT touch:** The test function body/matching logic (lines 425-447), `_load_resolved_spec`,
`_faction_hazard_immunities`, `test_hazard_kind_completeness` (lines 390-406) or
`HAZARD_KIND_COMPLETENESS_WORLDS`.

**Verify:** `pytest tests/unit/worldassembly/test_corpus_diversity.py -k
test_hazard_kind_matches_populating_faction_immunity -v` — must show 17 parametrized cases
(2 of which, `unit_information_source`/`unit_selfmodel_pilot`, trivially pass with zero
hazardous-populated-region assertions per the investigation's dry-run table), 0 failures, 0
unexpected skips (all 17 worlds have resolved specs on disk per the investigation's corpus
listing — `pytest.skip` should not trigger for any of them, but the mechanism stays in place as a
defensive guard per Scope's "reuse the existing helper pattern" instruction).

### Step 2 — Remove the superseded allowlist and update the module docstring

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`

**Change:** Remove the old `HAZARD_KIND_MATCH_WORLDS` name entirely (if Step 1 used approach (a)
or a differently-named constant, there should be no lingering reference to the old name anywhere
in the file — confirm via grep). Update the module docstring's item 3 (lines 12-15, currently
"`test_hazard_kind_completeness` — every non-zero-hazard region must either declare `hazard_kind`
or have every populating archetype's faction declare a matching `hazard_immunities` entry...") to
also describe the corpus-wide matching test (item 3b, currently undocumented in the module
docstring — only `test_hazard_kind_completeness` is listed at the module level). Add a short
docstring line noting `test_hazard_kind_matches_populating_faction_immunity` now runs
unconditionally across the full calibration corpus (all `data/worlds/*` world_ids), not a fixed
allowlist. Also update the comment block directly above the old constant (lines 36-40, "Worlds
this ticket's fix... directly targeted — scoped narrowly...") since it describes allowlist
provenance that no longer applies — replace it with a short comment noting the test now runs
corpus-wide and citing this ticket.

**Do NOT touch:** Docstring items 1, 2, 4 (entity-count bands, population stability, module
family anchoring) — unrelated to this ticket.

**Verify:** `grep -n "HAZARD_KIND_MATCH_WORLDS" tests/unit/worldassembly/test_corpus_diversity.py`
returns empty (AC #2). Manual read of docstring lines 12-19 confirms corpus-wide coverage is
described.

### Step 3 — Add explanatory comment for the `town_council`/`bandit_road` case (no runtime exception)

**Files:** `tests/unit/worldassembly/test_corpus_diversity.py`

**Change:** Add a code comment adjacent to `test_hazard_kind_matches_populating_faction_immunity`
(either in its docstring, lines 415-424, or immediately above the `for region in
spec.get("regions", [])` loop) stating: this test's matching semantics are region-level "any
populating faction is immune," not per-faction "every populating faction is immune"; at
`bandit_road` (6 of the 17 worlds), `town_council` is not immune to `NATURAL_TERRAIN` but
`bandit_company`/`merchant_league` are, so the region-level check passes even though
`town_council`'s own entities take real, unmitigated per-tick drain at runtime
(`src/world/environment.py::calculate_hazard_drain` resolves immunity per-entity, not
per-region). This is a known, ratified condition — see
`docs/guidelines/intentional_divergences.md` §2.30 and `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` —
not an oversight in this test. Do **not** add an `xfail`, `skip`, or any conditional branch keyed
on `town_council` or `bandit_road` — the comment is documentation only; the test executes
identically for every world including the 6 containing `bandit_road`.

**Do NOT touch:** `docs/guidelines/intentional_divergences.md` (owned by
`TCK-20260710-TOWN-COUNCIL-HAZARD-DA`, out of scope here — cite it, do not edit it). Do not add
any per-world or per-region conditional/exception logic to the test body.

**Verify:** Manual read confirms the comment exists and cites both the doc section and the
ticket. `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind -v` still shows
all `bandit_road`-containing worlds (`crowded_frontier`, `frontier_extended`,
`frontier_living_world`, `frontier_marches`, `generated_frontier_3_42`, `urban_political`) passing
with no xfail/skip markers (AC #3 outcome (b); test_plan.md's "No `xfail`/`skip` should be added"
anti-drift guard).

### Step 4 — Close out P2-O in `docs/plans/audit_fix_plan.md`

**Files:** `docs/plans/audit_fix_plan.md`

**Change:** Update the P2-O row in the summary table (line 743) from `OPEN (added 2026-07-09)` to
`RESOLVED (2026-07-11)` (or the actual completion date) with a short evidence note, mirroring the
P2-Q row's format immediately below it (line 745: `**RESOLVED (2026-07-10)** — ruled (a)
intentional, see intentional_divergences.md §2.30 — TCK-20260710-TOWN-COUNCIL-HAZARD-DA`). Use a
parallel format, e.g. `**RESOLVED (2026-07-11)** — test_hazard_kind_matches_populating_faction_immunity
now runs corpus-wide (17/17 worlds) — TCK-20260710-HAZARD-KIND-CORPUS-WIDE`. Also update the
detailed P2-O section body (starting line 415, "`hazard_kind` completeness has recurred 3 times as
a reactive, per-sweep fix — needs a structural test") to note resolution, matching whatever
closeout convention nearby resolved entries use in that section (check a nearby resolved entry,
e.g. P2-M or P2-P, for the exact heading-suffix convention before editing — likely appending
`— **RESOLVED (verified <date>)**` to the heading, consistent with lines 263 and similar).

**Do NOT touch:** Any other row in the summary table besides P2-O. Do not touch the P2-Q row
(already resolved, not this ticket's finding) beyond leaving it as-is.

**Verify:** Manual read of line 743 (or its shifted line number after edits) shows `RESOLVED`, not
`OPEN`. `grep -n "P2-O" docs/plans/audit_fix_plan.md` shows consistent resolved status across all
occurrences.

### Step 5 — Mark Phase 1.1 done in `docs/plans/simq_development_roadmap.md`, and correct the disproven ordering-coupling claim

**Files:** `docs/plans/simq_development_roadmap.md`

**Change:** Two narrow edits, both additive/corrective rather than a rewrite:
1. Section `### 1.1 — hazard_kind corpus-wide completeness test (P2-O)` (starting line 194):
   append a completion note (matching whatever convention the doc uses for Phase 0's completed
   items, e.g. the "(2026-07-11) — Phases 2-4 are unblocked..." style at line 80) stating Phase
   1.1 landed via `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`, and specifically correct the sentence at
   line 206 ("once 1.2 lands") — the corpus-wide dry run found the test passes unconditionally
   corpus-wide with no dependency on 1.2's landing (region-level "any" semantics already covered
   every `bandit_road` occurrence via `bandit_company`/`merchant_league`'s immunities, independent
   of 1.2's ruling).
2. The "Correction (2026-07-10, after ticketing)" callout box (lines 180-189): append a further
   dated note (e.g. "Correction (2026-07-11, post-implementation)") stating the original coupling
   claim itself — "running 1.1's corpus-wide test before 1.2's DA ruling lands hits the
   `town_council`/`bandit_road` case as a live, expected test failure" — was empirically
   disproven by 1.1's own investigation dry run: the test's region-level "any populating faction"
   matching semantics meant `bandit_road` already passed via `bandit_company`/`merchant_league`'s
   immunities regardless of ordering or of 1.2's ruling. Do not delete the original claim text —
   append the correction below it, preserving the historical record, consistent with how this doc
   already layers corrections (the existing 2026-07-10 box itself is additive over the original
   text).

**Do NOT touch:** Phase 0, Phase 2, Phase 3, Phase 4 sections; the Phase 1.2 section (owned by the
already-done `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`, only reference it).

**Verify:** Manual read confirms Phase 1.1 marked complete and the "once 1.2 lands" framing is
corrected. `grep -n "1.1" docs/plans/simq_development_roadmap.md` shows no remaining claim that
1.1 depends on or requires 1.2's landing.

### Step 6 — Correct `SEQUENCE.md`'s ordering rationale (planner's scope decision — see below)

**Files:** `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md`

**Change:** This file's "Why this order" column (row 1, line 11) asserts the same now-disproven
claim as the roadmap doc's pre-2026-07-11 text: "running 1.1's corpus-wide test before this DA
ruling lands hits the `town_council`/`bandit_road` case as a live failure." Append a short
correction note below the table (not a rewrite of the table itself, to preserve the historical
record of why the order was originally chosen) stating: this ticket's investigation dry run
(2026-07-11) found the claim does not hold — the corpus-wide test's region-level "any populating
faction" matching semantics meant `bandit_road` passed via `bandit_company`/`merchant_league`'s
immunities independent of ordering or of Phase 1.2's landing; both tickets are now done regardless
of this correction, but a future reader of this file should not conclude the observed clean
landing validates the original coupling theory. Cite `TCK-20260710-HAZARD-KIND-CORPUS-WIDE`'s
investigation.md as the source of the correction.

**Rationale for including this step:** the identical stale claim exists in three places
(`SEQUENCE.md`, and two spots in `simq_development_roadmap.md` corrected in Step 5). Correcting
the roadmap doc while leaving `SEQUENCE.md` — a small, adjacent, folder-level doc describing the
exact same two tickets — with the disproven claim would create an inconsistency between two docs
about the same fact, discoverable by any future reader who checks both. This is a one-line
factual correction (append-only, not a scope redesign), matching the precedent already set this
session (the sibling `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` ticket closed out adjacent plan docs
alongside its own change). It is not a code or test change and carries no risk to the ticket's
`git diff --stat` guard (Step 6's file is a `.md` ticket-folder doc, not a test or src file).

**Do NOT touch:** The table's original "Order"/"Ticket" columns or row content — append a
correction note only, do not delete or rewrite the original reasoning text.

**Verify:** Manual read confirms the correction note is present and cites this ticket's
investigation.md.

### Step 7 — Regression verification pass

**Files:** none (verification only)

**Change:** Run, in order:
1. `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind -v` — must pass (AC
   #6, exact command from ticket line 98 / test_plan.md).
2. `pytest tests/unit/worldassembly/test_corpus_diversity.py -k test_hazard_kind_completeness -v`
   — compare pass/fail set against a pre-change baseline run; must be identical (AC #5,
   test_plan.md's anti-drift guard — `test_hazard_kind_completeness` must show 0 diffs in
   behavior).
3. `git diff --stat` — must show only `tests/unit/worldassembly/test_corpus_diversity.py` plus the
   three doc files touched in Steps 4-6 (`docs/plans/audit_fix_plan.md`,
   `docs/plans/simq_development_roadmap.md`,
   `tickets/todos/simq-roadmap-phase1-process-hardening/SEQUENCE.md`) and the ticket file itself.
   No diff to `src/worldassembly/resolver.py`, `src/world/environment.py`,
   `data/content/social/factions.yaml`, or `docs/parity_ledger/world_dynamics.yaml` (AC #4).
4. (Recommended, not AC-required) `pytest tests/unit/worldassembly/test_corpus_diversity.py -v`
   for full-file regression confidence given shared module-level fixtures/constants.
5. (Recommended) `pytest tests/unit/world/test_regional_consequences.py -v` and `pytest
   tests/unit/worldbuilding/test_world_compiler.py -k bandit_road -v` per test_plan.md's
   adjacent-file confirmation — both are read-only-reference checks expected to be byte-identical
   to baseline since no `src/` files change.

**Do NOT touch:** Do not run repo-wide `pytest tests/` (Testing Rule; test_plan.md explicitly
scopes this out).

**Verify:** All commands above pass/match baseline; this step itself is the final verification
gate for the whole ticket.

## Scope Guards

- Do not modify `src/worldassembly/resolver.py`'s `"PHYSICAL"` hazard_kind default.
- Do not modify `src/world/environment.py::calculate_hazard_drain`.
- Do not modify `test_hazard_kind_completeness`'s logic or its `HAZARD_KIND_COMPLETENESS_WORLDS`
  parametrization list.
- Do not modify `ANCHORED_WORLD_BANDS` or `EXPECTED_DISTINCT_POPULATED_FACTIONS`, or fold any
  newly-covered world into either.
- Do not redesign `test_hazard_kind_matches_populating_faction_immunity`'s region-level "any"
  matching logic into a per-faction "every" check — that is a real latent gap (Risk 2 in
  investigation.md) but is explicitly out of scope; a redesign would newly fail on
  `town_council`/`bandit_road` and require the very exception mechanism this ticket confirms is
  currently unnecessary.
- Do not add an `xfail`, `skip`, or any named exception for `town_council`/`bandit_road` — the
  dry run shows none is needed; adding one would violate the Scope's "no broad/wildcard exception
  mechanism" guard and would misrepresent a passing case as an expected failure.
- Do not edit `docs/guidelines/intentional_divergences.md` — owned by
  `TCK-20260710-TOWN-COUNCIL-HAZARD-DA`; cite §2.30, do not modify it.
- Do not touch `data/content/social/factions.yaml` or `docs/parity_ledger/world_dynamics.yaml` —
  confirmed unaffected by the investigation; touching either would be undocumented scope creep
  and would trip the AC #4 `git diff` guard.
- Do not rewrite or delete the original ordering-rationale text in `SEQUENCE.md` or the
  pre-existing "Correction (2026-07-10...)" box in `simq_development_roadmap.md` — append
  corrections only, preserving the historical decision record.

## Dependency Map

- Steps 1, 2, 3 are sequential within the same file (`test_corpus_diversity.py`) but each is
  independently verifiable: Step 1 can be verified once its parametrization change lands (test
  passes/skips correctly), Step 2 is a pure cleanup/docstring pass verifiable by grep, Step 3 adds
  a comment with no behavioral effect, verifiable by re-running the same test command from Step 1.
  Recommended order is 1 → 2 → 3 (parametrize first, then clean up the now-dead name, then
  document the known-passing edge case) but 2 and 3 could be done in either order relative to each
  other without breaking anything.
- Steps 4, 5, 6 (doc closeouts) are independent of each other and of Steps 1-3 — they touch
  different files with no shared state. They depend only on Steps 1-3 having landed (so the
  closeout claims "test now runs corpus-wide" are true when written), not on each other.
- Step 7 depends on Steps 1-6 all being complete — it is the final gate.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — parametrized over all 17 `data/worlds/*` worlds, passes for all except the documented exception | Step 1 | `pytest tests/unit/worldassembly/test_corpus_diversity.py -k test_hazard_kind_matches_populating_faction_immunity -v` (Step 1 Verify; confirmed clean per investigation dry run — no exception needed) |
| AC #2 — `HAZARD_KIND_MATCH_WORLDS` no longer exists as a coverage-limiting allowlist | Step 2 | `grep -n "HAZARD_KIND_MATCH_WORLDS" tests/unit/worldassembly/test_corpus_diversity.py` empty |
| AC #3 — `town_council`/`bandit_road` neither silent pass nor silent fail; outcome (b), mechanism now matches | Step 3 | Manual read of comment + `pytest ... -k hazard_kind -v` shows all 6 `bandit_road` worlds passing, no xfail/skip |
| AC #4 — `git diff` touches only test files (and documented content fix if any; none found) | Steps 1-6 (scope discipline), verified in Step 7 | `git diff --stat` in Step 7 |
| AC #5 — `test_hazard_kind_completeness` unmodified in behavior | Step 1/2/3 (scope guard: do not touch it) | `pytest ... -k test_hazard_kind_completeness -v` before/after diff (Step 7) |
| AC #6 — `pytest tests/unit/worldassembly/test_corpus_diversity.py -k hazard_kind` passes locally | Steps 1-3 | Step 7, command 1 |
| AC #7 — genuine new (4th+) recurrence documented if found | N/A — investigation's dry run found none; stated explicitly in Completion Summary, not a code step | N/A (documentation-only; no recurrence found per investigation.md) |

## Anti-Drift Notes

- The investigation's dry run is authoritative: 0 mismatches across all 17 worlds, 45
  hazardous-populated-region checks, including all 6 `bandit_road` occurrences. Do not
  pre-emptively add exception scaffolding "just in case" — if Step 1's actual pytest run surfaces
  a genuine failure the dry run didn't predict (e.g. from an environment/content drift between
  investigation and implementation time), stop and treat it as new information per the ticket's
  own Out-of-Scope contingency (surface-and-reference by default; only fix in-ticket if
  self-evidently the same narrow content-authoring pattern already used three times) — do not
  silently patch content to make the dry run's premise hold.
- `town_council`'s per-entity unmitigated drain at `bandit_road` is real and ratified (§2.30,
  ruling (a), intentional "conflict-pressure flavor") — this ticket's test still cannot see it
  (region-level "any" semantics), and that is a known, accepted, out-of-scope limitation, not a
  bug this ticket introduces or is responsible for closing.
- P2-Q has already landed (`TCK-20260710-TOWN-COUNCIL-HAZARD-DA`, done 2026-07-11) with zero
  content changes (confirmed empty `git diff --stat` in that ticket's own Test Summary) — so
  nothing about Step 1's dry-run result depends on ticket-landing order; it would have passed
  identically before or after P2-Q.
- Two worlds (`unit_information_source`, `unit_selfmodel_pilot`) have zero hazardous populated
  regions — Step 1 must not special-case them; the test's existing `if hazard_level <= 0 or not
  populating_factions: continue` guard already handles this as a trivial pass with no assertions
  executed, consistent with the ticket's Assumptions section on graceful degradation.
- SEQUENCE.md and the two `simq_development_roadmap.md` correction spots (Step 5, Step 6) are
  append-only edits by design — this preserves the paper trail of why the original (incorrect)
  ordering decision was made, which has its own value as a lesson-learned record, rather than
  erasing it.

## Unresolved Questions

None. The one open question flagged by the investigation (whether to correct `SEQUENCE.md`'s
stale ordering rationale) was explicitly delegated to this planning step for a judgment call; see
Step 6 for the decision (fix it, via an append-only correction note) and its rationale.
