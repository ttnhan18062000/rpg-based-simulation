---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260728-EVAL-FIXTURE-REPAIR
artifact_type: plan
tags: [testing]
---

# Implementation Plan — TCK-20260728-EVAL-FIXTURE-REPAIR

## Summary

This plan repairs the 7 confirmed-stale `expected_doc_ids` in `tools/eval/queries.json`
(6 by correcting the doc_id string to match the live index's actual — buggy but
unchanged-by-this-ticket — doc_id scheme; 1, `engine/contracts/progression_package`,
by converting it into a genuine `no-result` fixture rather than inventing an
unverified replacement), extends the fixture with 7 new category values and 3
new per-entry fields, fixes the Recall@5/Recall@10 denominator bug so it
excludes no-answer queries the same way MRR@10 already does, and adds one new
metric (`duplicate_rate`) distinct from Recall@5/MRR@10. Every open question
flagged in `investigation.md` is resolved below as a stated implementation
decision, not left for the implementer to infer. All work stays inside the
ticket's three Related Code Areas (`tools/eval/queries.json`,
`tools/eval_search.py`, `tests/tools/test_eval_search.py`) — the indexer bug in
`tools/knowledge_search.py` that caused the staleness is explicitly not touched.

## Resolved Decisions (binding on the implementer — do not re-litigate)

1. **`progression_package` entry** — converted into a `no-result` category
   fixture, not replaced with an unverified content-equivalent doc. Cleanest
   resolution: turns a known-broken fixture into a deliberate, correctly-scoped
   test case. See Step 2 and Step 6.
2. **Recall@5/Recall@10 denominator** — both must use the same
   `queries_with_expected`-style exclusion MRR@10 already uses, per AC5's
   explicit "excluded from recall/MRR denominators" wording. This does NOT
   touch the 0.80 threshold value itself (Out of Scope forbids that) — it only
   corrects what population the threshold is measured against, which is what
   AC5 demands. See Step 8.
3. **`symbol-to-test` / `changed-path` categories** — implemented as doc/ticket
   PROXIES given the live corpus never indexes `src/`/`tests/` (only
   `tickets/done/*.md` Request Summary sections, `stored_artifacts/*/investigation.md`
   snippets, `tickets/working_log.csv` rows, and `docs/`). Each such entry's
   `notes` field must say explicitly that it is a doc/ticket proxy for a
   code-symbol or changed-path concept, not literal source-code retrieval. See
   Step 6.
4. **Category semantics** — additive. The existing 4 categories (`semantic`,
   `exact-term`, `cross-section`, `edge-case`) are kept byte-identical in
   meaning and minimums; the 7 new category values are added alongside them,
   giving 11 distinct category values total. Nothing is renamed, merged, or
   removed.
5. **`context_budget` / `source_lifecycle_assumption` / `allowable_alternatives`
   schema** (no prior schema exists anywhere in the repo — first definition):
   - `context_budget`: **integer**, approximate token budget for injecting
     this doc's content if retrieved. Use ~1800 for `mechanics/*` chapter-level
     docs (long, multi-section), ~900 for `engine/*`/`core/*`/`architecture/*`
     contract-style docs (medium, single-topic), ~700 for `guidelines/*` docs,
     ~400 for ticket/investigation-snippet targets (short, single-paragraph
     indexed text). Pick per-entry based on the target doc's actual type, not
     a single global constant.
   - `source_lifecycle_assumption`: **string enum**, one of `"current"` |
     `"superseded"` | `"archived"` | `"volatile"`. Every existing (post-repair)
     entry gets `"current"` — none of the repaired entries point at an
     archived or superseded doc; the one entry that did (`progression_package`)
     is removed from `expected_doc_ids` in Step 2, not kept as `"archived"` on
     a live-indexed entry. Only the new `no-result`/`policy-vs-superseded`
     entries in Step 6 use `"archived"` / `"superseded"` / `"volatile"`.
   - `allowable_alternatives`: **array of doc_id strings**, other doc_ids that
     would also count as a correct match. `[]` for existing entries by
     default — multi-answer existing entries (e.g. `AuthoritativeState`) already
     model "any of these count" via `expected_doc_ids` being a set; do not
     duplicate that into `allowable_alternatives` unless a *new*, currently-unlisted
     doc_id should also score as correct.

## Steps

### Step 1 — Repair the 6 path-only stale `expected_doc_ids` strings
**Files:** `tools/eval/queries.json`
**Change:** In place, replace the stale string with the live index's actual
doc_id in each entry's `expected_doc_ids` list (no other field changes):
- `queries.json:124` (`"replay contract determinism"`, exact-term): `"engine/contracts/replay_contract"` → `"engine/replay_contract"`
- `queries.json:130` (`"scheduler_contract tick scheduling"`, exact-term): `"engine/contracts/scheduler_contract"` → `"engine/scheduler_contract"`
- `queries.json:148` (`"parity_ledger infrastructure status verified"`, exact-term): `"engine/contracts/infrastructure_overview"` → `"engine/infrastructure_overview"`
- `queries.json:166` (`"watchdog adr simulation safety"`, exact-term): `"architecture/adr-004-simulation-watchdog"` → `"architecture/simulation_watchdog"`
- `queries.json:172` (`"performance optimization adr bounded cognition"`, exact-term): `"architecture/adr-005-performance-optimization"` → `"architecture/performance_optimization"`
- `queries.json:208` (`"observability and replay for simulation determinism verification"`, cross-section): `["engine/contracts/replay_contract", "engine/contracts/observability_contract"]` → `["engine/replay_contract", "engine/observability_contract"]`

**Do NOT touch:** `tools/knowledge_search.py`'s `_collect_docs_chunks()` /
`section = rel_parts[0]` (L275-278) — that is the indexer bug that *produced*
these doc_ids; this ticket corrects the fixture to match current indexer
behavior, it does not correct the indexer. Do not touch any other field
(`query`, `notes`, `category`) on these 6 entries.
**Verify:** `test_no_stale_expected_doc_ids` (Step 3) — none of the 7 known-stale
strings appear anywhere in `expected_doc_ids` after this step (6 of 7; the 7th
is handled in Step 2).

### Step 2 — Convert the `progression_package` cross-section entry
**Files:** `tools/eval/queries.json`
**Change:** At `queries.json:194-199` (query `"entity attribute changes after
XP reward and level up"`, category `cross-section`), remove the dead
`"engine/contracts/progression_package"` id from `expected_doc_ids`, leaving
`["mechanics/01_entity_anatomy"]` only. Category, query text, and notes stay
`cross-section` — this entry keeps testing the mechanics/engine cross-reference
concept, just without the unmatchable second id. The `no-result` fixture that
replaces `progression_package`'s *test intent* (archived-doc unmatchability) is
a separate new entry added in Step 6, not this one.
**Do NOT touch:** Do not substitute `docs/mechanics/attribute_progression_contract.md`
as a replacement id here — investigation.md flags that its content-equivalence
to the archived `progression_package.md` was never verified, and substituting
an unverified id would trade one wrong assumption for another. This entry
simply loses its stale second id.
**Verify:** `test_no_stale_expected_doc_ids` (Step 3).

### Step 3 — Add the stale-id regression guard test
**Files:** `tests/tools/test_eval_search.py` (`TestQueriesJson` class)
**Change:** Add `test_no_stale_expected_doc_ids`: load `queries.json`, flatten
all `expected_doc_ids` across all entries into one set, assert none of the 7
known-stale strings (list them as a module-level constant,
`_KNOWN_STALE_DOC_IDS`, next to the test) is present. Fast, deterministic,
no live index required — the always-runs baseline (per test_plan.md's
recommendation, the optional live-index-backed stronger check is out of scope
for this ticket; do not add a `pytest.mark.skipif` live-DB variant here, that
would be scope creep beyond the ticket's 6 ACs).
**Do NOT touch:** `TestStripAnchor`, `TestReciprocalRank`, `TestHit` classes —
untouched by this ticket's scope per test_plan.md.
**Verify:** `pytest tests/tools/test_eval_search.py::TestQueriesJson::test_no_stale_expected_doc_ids -v` fails before Step 1/2, passes after.

### Step 4 — Backfill the 3 new fields onto all existing 40 entries
**Files:** `tools/eval/queries.json`
**Change:** Add `allowable_alternatives` (`[]`), `source_lifecycle_assumption`
(`"current"`), and `context_budget` (integer per the type/value rule in
Resolved Decision 5) to every one of the 40 pre-existing entries (the 6 from
Step 1 and the 1 from Step 2 already have their `expected_doc_ids` corrected
by this point — add the 3 new fields to those same entries, don't re-touch
`expected_doc_ids` again here). This is a pure additive field backfill — do
not alter `query`, `expected_doc_ids`, `category`, or `notes` on any of these
40 entries in this step.
**Do NOT touch:** category values or counts (that's Step 6). Do not add these
3 fields with placeholder/null values — every entry must have a real,
per-entry-considered value, not a copy-pasted default across all 40 (the
`context_budget` value in particular must vary by doc type per Resolved
Decision 5, not be a single constant).
**Verify:** `test_new_fields_present_all_entries` (Step 5).

### Step 5 — Update `test_required_keys` for the new schema
**Files:** `tests/tools/test_eval_search.py` (`TestQueriesJson.test_required_keys`)
**Change:** Extend the existing loop (currently asserting `query`,
`expected_doc_ids`, `notes` presence/type at L38-43) to also assert:
- `allowable_alternatives` present, `isinstance(..., list)`, every element `str`
- `source_lifecycle_assumption` present, `isinstance(..., str)`, non-empty,
  and a member of `{"current", "superseded", "archived", "volatile"}`
- `context_budget` present, `isinstance(..., int)`, `> 0`
Also add a **new** dedicated test `test_new_fields_present_all_entries` (or
fold into the extended `test_required_keys` — implementer's call, but the
assertions above must exist somewhere and run over every entry) per
test_plan.md's New Tests #2.
**Do NOT touch:** the existing `query`/`expected_doc_ids`/`notes` assertions —
extend, don't replace.
**Verify:** `pytest tests/tools/test_eval_search.py::TestQueriesJson::test_required_keys -v` fails before Step 4, passes after.

### Step 6 — Add the 7 new category values (minimum 3 entries each, 21 new entries)
**Files:** `tools/eval/queries.json`
**Change:** Append 21 new entries (append to the end of the array — do not
interleave with existing entries), 3 per new category, each with all 7 fields
(`query`, `expected_doc_ids`, `category`, `notes`, `allowable_alternatives`,
`source_lifecycle_assumption`, `context_budget`) populated from the start (no
separate backfill step needed for these, unlike Step 4's existing entries).
Category values, verbatim as named in the ticket's Scope section:
- `"doc/exact-id"` — 3 entries targeting an exact, unambiguous single doc_id
  by name (similar intent to `exact-term` but explicitly single-answer,
  doc-identity-focused rather than concept-focused).
- `"policy-vs-superseded"` — 3 entries where the query could plausibly match
  either a current doc or a superseded/archived one; `expected_doc_ids` names
  the current doc, `source_lifecycle_assumption: "superseded"` or
  `"archived"`, and `allowable_alternatives` may name the superseded id if it
  should still count. This is the category the investigation flagged as the
  natural home for the `progression_package` concept (see below) — the 21
  entries must include one policy-vs-superseded entry pairing
  `mechanics/attribute_progression_contract`-or-equivalent-live-doc as
  `expected_doc_ids` against `progression_package`'s superseded/archived
  status **only if** the implementer verifies (by running
  `python3 tools/knowledge_search.py query "<text>" --top-k 10` against the
  live index) that the live doc is genuinely a content match for the query
  intent; if not verifiable, use a different, verifiable policy-vs-superseded
  pairing instead — do not force an unverified pairing just to reference
  `progression_package` twice.
- `"ticket-history"` — 3 entries targeting a `tickets/done/TCK-*` doc_id
  (ticket_id itself, no anchor) by matching content from that ticket's
  Request Summary section (the only section indexed for tickets — verify
  with `_extract_request_summary`'s behavior, `tools/knowledge_search.py:72-87`).
- `"symbol-to-test"` — 3 entries, each a PROXY: query names a specific
  function/module by name, `expected_doc_ids` targets a ticket or doc whose
  indexed text (Request Summary / doc chunk) names that same function/module.
  `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` is a verified usable target —
  its Request Summary section literally names `knowledge_docs.doc_id`,
  `tools/eval_search.py`, and the chunk-level `id` field. `notes` must state
  explicitly: `"proxy — targets a ticket documenting the symbol, not literal
  source-code retrieval (corpus does not index src/)"`.
- `"changed-path"` — 3 entries, each a PROXY: query references a specific file
  path, `expected_doc_ids` targets a ticket whose Request Summary text names
  that same path (e.g. `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`'s Request
  Summary names `tools/eval_search.py` and `tools/eval/queries.json` inline).
  `notes` must state explicitly: `"proxy — targets a ticket whose summary
  names the changed path, not a literal path-ownership index (corpus does not
  index src/ or tests/)"`.
- `"provider/workflow/monitoring"` — 3 entries targeting docs under
  `docs/engine/contracts/` (provider-facing contracts) or observability/
  monitoring topics (e.g. `engine/observability_contract`,
  `engine/infrastructure_overview` — the corrected doc_ids from Step 1 are
  legitimate reuse targets here).
- `"no-result"` — 3 entries with `expected_doc_ids: []`. One of these three
  MUST be the `progression_package` proxy: a query themed around "engine
  contract for progression package rewards" (or similarly worded to evoke the
  archived doc's topic without expecting a match), `expected_doc_ids: []`,
  `source_lifecycle_assumption: "archived"`, `notes` stating explicitly this
  models the real `docs/archive/engine_contracts/progression_package.md` —
  intentionally unmatchable because `docs/archive/` is permanently excluded
  from the index by design, not a bug. This is the Resolved Decision 1
  conversion. The other 2 `no-result` entries are new genuinely-unanswerable
  queries (distinct from the existing 4 empty-expected `edge-case` entries —
  do not duplicate or move those; `edge-case` stays untouched per Resolved
  Decision 4).
**Do NOT touch:** the 4 existing categories' entries, counts, or minimums.
Do not rename `doc/exact-id` or `provider/workflow/monitoring` to
hyphenated forms — use the literal slash-containing strings as named in the
ticket's Scope section, since AC2 checks for "the new category values"
verbatim.
**Verify:** `test_category_balance` (Step 7).

### Step 7 — Rewrite `test_category_balance` for all 11 categories
**Files:** `tests/tools/test_eval_search.py` (`TestQueriesJson.test_category_balance`)
**Change:** Replace the 4 hardcoded `.count()` calls (L48-56) with a single
source-of-truth dict, e.g.:
```python
_CATEGORY_MINIMUMS = {
    "semantic": 15, "exact-term": 15, "cross-section": 5, "edge-case": 5,
    "doc/exact-id": 3, "policy-vs-superseded": 3, "ticket-history": 3,
    "symbol-to-test": 3, "changed-path": 3, "provider/workflow/monitoring": 3,
    "no-result": 3,
}
```
then loop over it asserting `categories.count(name) >= minimum` for each,
plus an assertion that every entry's `category` is a key in
`_CATEGORY_MINIMUMS` (catches typos/unregistered categories, per
test_plan.md's "Category-set drift guard").
**Do NOT touch:** the 4 existing minimums (15/15/5/5) — keep them exactly as
they are, per Resolved Decision 4.
**Verify:** `pytest tests/tools/test_eval_search.py::TestQueriesJson::test_category_balance -v` fails before Step 6, passes after.

### Step 8 — Fix the Recall@5/Recall@10 denominator bug
**Files:** `tools/eval_search.py`, function `evaluate()` (L53-109)
**Change:** Move the `queries_with_expected` computation (currently L98,
`sum(1 for q in per_query if q["rr"] is not None)`) to before the
`recall5`/`recall10` computation, and change:
```python
recall5 = hits5 / total if total else 0.0
recall10 = hits10 / total if total else 0.0
```
(currently L95-96) to divide by `queries_with_expected` instead of `total`.
Keep `total = len(queries)` (L54) as-is — it is still used correctly for the
`"Queries: {total}"` print line (L104) and should stay reporting the full
query count there, only the recall denominators change. `mrr10`'s existing
`queries_with_expected`-based computation (L98-99) is untouched — this step
makes recall5/recall10 consistent with it, not the other way around.
**Do NOT touch:** the 0.80 `--threshold` default (`main()` L157-158) or the
`return 0 if recall5 >= threshold else 1` gate logic (L109) — only the
denominator changes, not the threshold value or pass/fail mechanism, per
Resolved Decision 2 and the ticket's Out of Scope.
**Verify:** `test_no_result_queries_excluded_from_recall_denominator` (Step 9);
re-run `TestEvaluateExitCode`'s existing 5 cases to confirm they still pass
unchanged (all use fully-populated `expected_doc_ids`, so `queries_with_expected == total` for those fixtures and the denominator change is a no-op for them — must be verified by running the class, not assumed, per test_plan.md's anti-drift guard).

### Step 9 — Add the denominator regression test + threshold-unchanged guard
**Files:** `tests/tools/test_eval_search.py` (extend `TestEvaluateExitCode`)
**Change:** Add `test_no_result_queries_excluded_from_recall_denominator`:
build a query list mixing N answerable queries (mocked `_run_query` returns a
hit for all) with M `expected_doc_ids: []` queries, run `evaluate()`, and
assert `recall5 == 1.0` (not `N/(N+M)`) by inspecting the printed/report
recall value — this test must be written to fail against the pre-Step-8 code
(`total = len(queries)`) to prove it locks in the fix, per test_plan.md's
instruction. Since `evaluate()` doesn't return recall values directly (only an
exit code), assert via the saved report JSON's `metrics.recall_at_5` field
(mirrors `test_report_saved_to_reports_dir`'s existing pattern of reading the
written report) rather than parsing stdout.
Also add `test_threshold_default_unchanged`: assert the CLI's `--threshold`
argparse default is still `0.80` (read `_mod.main`'s argparse setup, or
equivalent), per test_plan.md's "Threshold-unchanged guard" and AC6.
**Do NOT touch:** `TestEvaluateExitCode`'s 5 existing test methods — add new
methods, don't edit existing ones (they must keep passing byte-identical).
**Verify:** both new tests pass; full `TestEvaluateExitCode` class passes.

### Step 10 — Add the `duplicate_rate` metric
**Files:** `tools/eval_search.py`
**Change:** Add a new pure function near `_reciprocal_rank`/`_hit` (L42-50):
```python
def _duplicate_rate(results: list[str]) -> float:
    """Fraction of retrieved results that are duplicates of an earlier
    result, after reducing to document-level identity."""
    if not results:
        return 0.0
    stripped = [_strip_anchor(d) for d in results]
    return (len(stripped) - len(set(stripped))) / len(stripped)
```
Wire it into `evaluate()`'s per-query loop (near L82-93): compute
`dup_rate = _duplicate_rate(results)` per query, append to `per_query` dict as
`"duplicate_rate": dup_rate`, and average across all queries (not just
`queries_with_expected` — duplicate rate is a retrieval-quality signal
independent of whether an expected answer exists) into a new
`avg_duplicate_rate` value. Add `avg_duplicate_rate` to the print summary line
(L103) and to `_save_report`'s `metrics` dict (L130-140) as
`"avg_duplicate_rate"`.
**Do NOT touch:** Recall@5/Recall@10/MRR@10 computation logic — this is an
additive metric, not a replacement. Do not add a new hard dependency (no
`yaml`, no frontmatter parsing) — `duplicate_rate` is chosen specifically
because it needs nothing beyond the existing `results` list, consistent with
the anti-drift hazard against adding mandatory dependencies or unbuilt
frontmatter infrastructure. Do not create a new file (e.g.
`tools/eval_metrics.py`) — the ticket's Related Code Areas name
`tools/eval_search.py` directly; keep the new function there.
**Verify:** new `TestDuplicateRate` class (Step 11).

### Step 11 — Test the `duplicate_rate` metric
**Files:** `tests/tools/test_eval_search.py`
**Change:** Add `TestDuplicateRate` class mirroring `TestReciprocalRank`/`TestHit`'s
pattern (pure function, no mocking):
- `test_no_duplicates_is_zero`: `_duplicate_rate(["a", "b", "c"]) == 0.0`
- `test_all_duplicates`: `_duplicate_rate(["a", "a", "a"]) == pytest.approx(2/3)`
- `test_partial_duplicates_after_anchor_strip`: `_duplicate_rate(["a#h1-000", "a#h2-001", "b"])` counts `"a#h1-000"`/`"a#h2-001"` as the same document after `_strip_anchor` → `== pytest.approx(1/3)`
- `test_empty_results_is_zero`: `_duplicate_rate([]) == 0.0`
Also extend one `TestEvaluateExitCode` case (or add a new one) asserting
`"avg_duplicate_rate"` appears in the saved report's `metrics` dict, mirroring
`test_report_saved_to_reports_dir`'s existing key-presence pattern.
**Do NOT touch:** existing metric test classes.
**Verify:** `pytest tests/tools/test_eval_search.py::TestDuplicateRate -v` and the extended report-key test pass.

### Step 12 — Record the AC6 decision and run the manual baseline
**Files:** `tickets/inprogress/TCK-20260728-EVAL-FIXTURE-REPAIR.md` (Implementation Notes / Test Summary sections — not a staging artifact, but must be updated at Verify/Finalize time)
**Change:** This is a documentation-only step, not a pytest test (per
test_plan.md New Tests #6). After Steps 1-11 land, run
`python3 tools/eval_search.py` manually (matches ticket's "no CI wiring" Out of
Scope — this stays a manual Makefile target) and record the new Recall@5/
Recall@10/MRR@10/avg_duplicate_rate baseline in the ticket's Test Summary,
explicitly distinguishing it from the prior 0.53 baseline (which was measured
under both the stale-id bug and the denominator bug). State explicitly in
Implementation Notes: "the 0.80 Recall@5 threshold value is unchanged; only
the doc_ids being scored against and the denominator population changed."
**Do NOT touch:** `.github/workflows/*.yml` or the `Makefile` — verify at this
step that neither was touched anywhere in Steps 1-11 (no CI wiring is
introduced).
**Verify:** Manual run exits with a real, non-placeholder Recall@5 number;
ticket's AC6 checkbox can be marked done because the decision is recorded in
both this plan (Resolved Decision 2 above) and the ticket body.

## Scope Guards

- Do not modify `tools/knowledge_search.py` at all — specifically not
  `_collect_docs_chunks()` (L232-443) or its `section = rel_parts[0]` line
  (L275-278). That is the root-cause indexer bug; fixing it is a separate,
  more invasive ticket outside this one's Related Code Areas.
- Do not change the `--threshold` default (`0.80`) in `tools/eval_search.py`'s
  `main()`, and do not change `evaluate()`'s `return 0 if recall5 >= threshold
  else 1` gate mechanism.
- Do not add `eval_search.py` (or a wrapper) to `.github/workflows/*.yml` or
  make it a blocking `Makefile` target beyond its existing manual
  `make eval-search` invocation.
- Do not build new doc frontmatter status/authority infrastructure — the
  `duplicate_rate` metric chosen in Step 10 needs none; do not additionally
  implement the authority/freshness metric option in this ticket (the ticket
  requires "at least one" new metric; `duplicate_rate` satisfies AC4 alone).
- Do not touch `TestStripAnchor`, `TestReciprocalRank`, `TestHit`, `TestRunQuery`,
  or `TestMainNoIndex` test classes.
- Do not merge, rename, or change minimums for the 4 existing category values
  or their entries.
- Do not substitute an unverified replacement doc_id for
  `engine/contracts/progression_package` — it is dropped, not replaced (Step 2).

## Dependency Map

- Steps 1, 2 are independent of each other (different entries) and must both
  complete before Step 3 (Step 3's blocklist test checks both stale-id fixes).
- Step 3 depends on Steps 1 and 2.
- Step 4 depends on Steps 1 and 2 (backfills fields onto the already-corrected
  entries) but is independent of Step 3.
- Step 5 depends on Step 4.
- Step 6 is independent of Steps 1-5 (appends new entries) but its
  `progression_package`-themed `no-result` entry should be written with
  awareness that Step 2 already removed the dead id from the original entry —
  no ordering dependency, just shared context.
- Step 7 depends on Step 6.
- Step 8 is independent of Steps 1-7 (pure `eval_search.py` logic change).
- Step 9 depends on Step 8.
- Step 10 is independent of Steps 1-9 (additive metric function).
- Step 11 depends on Step 10.
- Step 12 depends on all of Steps 1-11 being complete (final manual run +
  documentation).
- Recommended execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12
  (this ordering satisfies all dependencies and keeps queries.json changes
  grouped before eval_search.py changes, though 8-11 could run in parallel
  with 1-7 if preferred since they touch different files).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — every `expected_doc_id` resolves to a live doc_id, no stale/archived entries | Steps 1, 2 | `test_no_stale_expected_doc_ids` (Step 3) |
| AC2 — queries.json extended with new category values + new required fields | Steps 4, 6 | `test_new_fields_present_all_entries` (Step 5), `test_category_balance` (Step 7) |
| AC3 — test_required_keys / test_category_balance updated to assert new fields/categories | Steps 5, 7 | Steps 5 and 7's own tests |
| AC4 — at least one new metric distinct from Recall@5/MRR@10, unit-tested | Steps 10, 11 | `TestDuplicateRate` (Step 11) |
| AC5 — no-result queries produce graceful zero-result output and are excluded from recall/MRR denominators | Steps 6 (no-result entries), 8 (denominator fix) | `test_no_result_queries_excluded_from_recall_denominator` (Step 9) |
| AC6 — decision recorded: new categories tracked separately, 0.80 gate meaning unchanged | Resolved Decision 2 (this plan) + Step 12 | `test_threshold_default_unchanged` (Step 9); ticket body update (Step 12, docs-only, no test) |

## Anti-Drift Notes

- The staleness root cause is `tools/knowledge_search.py:275-278`'s
  `section = rel_parts[0]` collapsing nested path segments. This ticket fixes
  the *fixture* to match that behavior, not the indexer. If a future ticket
  fixes the indexer bug itself, `tools/eval/queries.json`'s doc_ids fixed in
  Step 1 will need re-repairing back toward the originally-intended nested
  scheme — that is expected and out of scope here.
- `TestEvaluateExitCode`'s 5 existing cases all use fully-populated
  `expected_doc_ids` (no empty lists), so `queries_with_expected == total` for
  every one of them — the Step 8 denominator change is mathematically a
  no-op for these specific fixtures, but this must be confirmed by running the
  class after the change, not assumed from this reasoning alone.
- `docs/archive/` exclusion from the index is intentional, documented
  behavior (`knowledge_search.py`'s module docstring and `_collect_docs_chunks`
  L251-253/L261-262) — the `no-result` entry for `progression_package` in
  Step 6 must frame this as "working as designed," not as a gap to fix.
  `source_lifecycle_assumption: "archived"` on that entry is the correct
  documentation of this fact, not a placeholder.
- `symbol-to-test`/`changed-path` entries must not imply source-code-level
  retrieval capability that doesn't exist yet (the corpus never indexes
  `src/`/`tests/` — confirmed via `_collect_corpus()` docstring,
  `knowledge_search.py:128-140`). Every such entry's `notes` field carries the
  explicit proxy disclaimer from Step 6 so a future contributor doesn't
  mistake the category for literal symbol/path indexing and try to "fix" it
  by building that capability inside this ticket's blast radius.
- No parity ledger entry is needed (confirmed in investigation.md — pure
  agent-tooling, no mechanics/engine-contract overlap, no P0 entries touched).

## Deviations

- **Step 6, `policy-vs-superseded` pairing**: the plan conditionally suggested
  pairing `mechanics/attribute_progression_contract` (current) against
  `progression_package` (archived) "only if the implementer verifies ... that
  the live doc is genuinely a content match." Verification failed: reading
  both files showed `docs/archive/engine_contracts/progression_package.md` is
  about Phase-5 resource-engine-loop certification (grid movement, resource
  interaction, town resolution, strategic AI, performance baseline), not
  XP/attribute progression — the topical overlap is name-only. Per the plan's
  own fallback instruction ("if not verifiable, use a different, verifiable
  policy-vs-superseded pairing instead"), used 3 different, directly-verified
  archived→current pairs instead: `combat/combat_movement_rulebook.md` →
  `combat/combat_movement_overhaul_spec` (both cover Manhattan-distance/
  orthogonal-adjacency spatial rules), `engine_contracts/support_matrix.md` →
  `engine/supported_gameplay_surface` (both are Grid-Movement/Resource-
  Interaction support matrices), and `engine_contracts/unsupported_register.md`
  → `engine/legacy_replacement_ledger` (both track legacy-vs-V2 system
  disposition). The `progression_package` concept was instead placed in the
  `no-result` category as originally planned, themed on its real content
  (resource-engine phase-5 certification) rather than the plan's illustrative
  "rewards" wording, so the query text stays honest about what the archived
  doc actually contains.
- No other deviations. All other steps, field values, and test additions
  match this plan as written.
