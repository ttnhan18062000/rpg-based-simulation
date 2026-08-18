---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION
artifact_type: plan
tags: [ai, bug]
---

# Implementation Plan — TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION

## Summary

`tools/knowledge_search.py::_collect_docs_chunks()` derives `doc_id` as `f"{section}/{stem}"`
where `section = rel_parts[0]` (only the immediate subdirectory of `docs/`), discarding any deeper
nesting (`tools/knowledge_search.py:279–293`). This plan changes the derivation to use the full
relative path under `docs_root` (minus the `.md` suffix), preserving all nesting. Because the fix
touches only in-process derivation logic and not any manifest-tracked corpus file's mtime, the
incremental rebuild path (`make knowledge-index-update`) will silently no-op and must not be used —
a full rebuild (`make knowledge-index`) is required to apply the fix to the live index
(`knowledge-index/knowledge.db`). `tools/eval/queries.json` has 9 `expected_doc_ids` entries keyed
to the old truncated scheme; these are updated in the same change so `make eval-search` measures
against the corrected scheme rather than regressing. All three named downstream consumers
(`context_packet_assembler.py`, `search_server.py`, `search_mcp.py`) plus the two additional real
consumers found in investigation (`hybrid_retrieval.py`, `kgmcp_phase1_gateway_runner.py`) treat
`doc_id` as an opaque string and require no code changes — only their existing test suites are run
to confirm. A new `docs/parity_ledger/infrastructure.yaml` entry (`INFRA-340`, next available ID)
documents the change per the INFRA-294/295/296 precedent for this class of agent-tooling-
infrastructure fix.

## Steps

### Step 1 — Fix `doc_id` derivation to preserve full nested path

**Files:** `tools/knowledge_search.py`

**Change:** In `_collect_docs_chunks()` (`tools/knowledge_search.py:237–293`), replace the
truncated `section`/`stem` derivation of `doc_id` with one built from the full relative path.

Confirmed current code (read `tools/knowledge_search.py:260–293`):
```python
try:
    rel = md_file.relative_to(docs_root)
except ValueError:
    continue
rel_parts = rel.parts
...
if len(rel_parts) > 1:
    section = rel_parts[0]
else:
    section = ""
stem = md_file.stem
...
doc_id = f"{section}/{stem}" if section else stem
```
`rel` (line 262) is already computed relative to `docs_root` (the `docs/` directory itself, not
its parent) — confirmed by the function's own docstring at `tools/knowledge_search.py:245`: `path
— relative path string from corpus_root (e.g. "docs/mechanics/02.md")`, which shows `corpus_root`
is the parent of `docs/` (its `path_str`, line 289, includes the `docs/` prefix), while `docs_root`
itself (used for `rel` at line 262) is the `docs/` directory. This distinction matters: `rel` does
NOT include a `docs/` prefix, so the new `doc_id` must be built from `rel`, not `path_str` — using
`path_str` would wrongly prepend `docs/` to every `doc_id`, a regression `_derive_title()` and every
downstream opaque-string consumer would silently absorb without erroring, but which would silently
break every existing chunk-level anchor (`f"{doc_id}#{anchor}"`) that today has no `docs/` prefix.

**New code**, replacing lines 279–293:
```python
# doc_id preserves the full nested relative path under docs_root, not just
# the immediate subdirectory — fixes TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION.
doc_id = rel.with_suffix("").as_posix()

# section retained for the existing "section" chunk-metadata field (used by
# search_mcp.py's --section post-filter) — still the immediate subdirectory,
# unchanged semantics, computed the same way as before.
section = rel_parts[0] if len(rel_parts) > 1 else ""
```
Remove the now-unused `stem = md_file.stem` line only if nothing else in the function references
`stem` — confirmed by reading the full function body (`tools/knowledge_search.py:237–448`) that
`stem` is not referenced anywhere else in `_collect_docs_chunks()`; safe to delete.

**Concrete before/after example**, using the real nested doc cited in the ticket and investigation
(`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`, confirmed to exist
by investigation.md, 19290 bytes):
- `rel` = `engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`
- **Before**: `doc_id = "engine/measurement_baseline_contract"` (drops `contracts/knowledge_gateway_mcp/`)
- **After**: `doc_id = "engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract"`
- Depth-1 unaffected example (`docs/mechanics/02_combat_laws.md`): `rel = mechanics/02_combat_laws.md`
  → `doc_id = "mechanics/02_combat_laws"` — byte-identical to the pre-fix value, since
  `rel.with_suffix("").as_posix()` degenerates to `f"{section}/{stem}"` exactly when `rel` has only
  one path segment before the filename plus the immediate subdirectory (2 parts total). This is why
  the fix is a strict generalization, not a behavior change, for the 218/338 real docs already at
  depth 1.

**Also update the function's docstring** (`tools/knowledge_search.py:242–249`), which currently
states `doc_id — "{section}/{stem}" (document-level identity, no chunk qualifier)` — this is now
stale and must read `doc_id — full relative path under docs_root, minus ".md" suffix (document-level
identity, no chunk qualifier)`, or equivalent, to avoid the docstring itself becoming a source of
truth drift for the next implementer touching this function.

**Every other writer to `doc_id`/`id`**: `_collect_docs_chunks()` (this function) is the **sole**
writer of `doc_id` and chunk-`id` values — confirmed by grep across `tools/knowledge_search.py` for
`"doc_id"` and `f"{doc_id}#`: all six chunk-emission sites (lines 305, 306, 321, 322, 348, 349, and
their H3-split siblings later in the function) read the single `doc_id` local variable computed
once at line 293 (soon-to-be the new one-line expression above) — none re-derive it independently.
`cmd_build()` (`tools/knowledge_search.py:627+`) and `cmd_build_incremental()`
(`tools/knowledge_search.py:753+`) both consume the `corpus` list `_collect_docs_chunks()` returns
and write it verbatim into the SQL `knowledge_docs.doc_id` column and the BM25 `doc_ids` parallel
list — neither re-derives or mutates `doc_id`. No other module writes to `knowledge_docs.doc_id` or
the BM25 index's `doc_ids` list; both are single-writer, single-pass build artifacts, not
concurrently written at runtime. No ordering/race/collision concern applies to this step.

**Do NOT touch:** the `#anchor` suffix logic (`_heading_slug()`, the `f"{doc_id}#{...}"`
f-strings themselves, zero-padded `seq` numbering) — only the pre-`#` `doc_id` portion's shape
changes; the anchor-composition code stays byte-identical. Do not touch `path_str`
(`tools/knowledge_search.py:287–291`) or the `path` chunk-metadata field — those already carry the
full `docs/...`-prefixed path and are unaffected/unused by this fix.

**Verify:** `test_collect_docs_chunks_preserves_full_nested_path`,
`test_collect_docs_chunks_no_collision_same_stem_different_subdir`,
`test_collect_docs_chunks_single_level_path_unchanged`,
`test_chunk_id_anchor_suffix_unaffected_by_nesting_fix` (test_plan.md items 1–4).

### Step 2 — Full index rebuild (not incremental)

**Files:** none (operational step — runs `make knowledge-index`); `knowledge-index/knowledge.db`
and `knowledge-index/manifest.json` are regenerated as a result, not hand-edited.

**Change:** Run `make knowledge-index` (confirmed real target name, `Makefile:307`, comment
"Build local semantic knowledge index (developer env only — not CI)") — **not**
`make knowledge-index-update` (`Makefile:313`, the incremental target). `make knowledge-index`
routes to `cmd_build()`, which unconditionally `unlink()`s (`tools/knowledge_search.py:681`) and
rewrites `knowledge.db` from a fresh `_collect_corpus()` pass, so the Step 1 code change is
guaranteed to reach disk.

**Why not incremental** (see Design Decision section below for the full citation trail):
`cmd_build_incremental()`'s only change-detection signal is per-path mtime comparison against
`manifest.json` (`tools/knowledge_search.py:781–791` per investigation.md); since this fix touches
only `tools/knowledge_search.py` itself — never a manifest-tracked `docs/`/`tickets/` corpus path —
every path's mtime is unchanged, so `n_changed == 0 and n_deleted == 0` and the function returns 0
at `tools/knowledge_search.py:801–806` before ever opening or rewriting the DB. Running only the
incremental target would leave the old, truncated `doc_id` values live indefinitely while appearing
to succeed.

**Other writers to `knowledge-index/knowledge.db`**: `cmd_build()` and `cmd_build_incremental()`
are the only two code paths that write this file (both in `tools/knowledge_search.py`); no other
module opens it for writing. `tools/retrieval_cache.py` owns a separate, distinct file
(`knowledge-index/retrieval_cache.db`, confirmed by investigation's citation of INFRA-295) and never
writes to `knowledge.db`. Running `make knowledge-index` while another process might be reading
`knowledge.db` (e.g. `search_server.py` under active dev) is an existing, pre-existing operational
concern unrelated to this fix — not a new risk this step introduces.

**Do NOT touch:** `tools/retrieval_cache.py` or `knowledge-index/retrieval_cache.db` — out of
scope, untouched by this fix, per investigation's confirmation that it is a distinct file/module.

**Verify:** manual sample check (test_plan.md's "Post-fix ... manual Verify-phase sanity check")
— query the rebuilt `knowledge.db` for a known nested doc (e.g.
`engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract`) and confirm the full-path
`doc_id` is present, plus `test_build_incremental_noop_leaves_stale_doc_id_documented`
(test_plan.md item 6) as an automated guard that the incremental no-op behavior itself is locked in
and not silently "fixed" by a future change without deliberate scoping.

**Depends on:** Step 1 (rebuild must run against the fixed derivation code, not before it).

### Step 3 — Update `tools/eval/queries.json`'s 9 stale fixture entries

**Files:** `tools/eval/queries.json`

**Change:** Update the `expected_doc_ids` field for the 9 queries investigation.md identified as
keyed to the old truncated scheme (all currently `engine/{stem}`, all real docs living under
`docs/engine/contracts/`, confirmed by investigation.md's cross-reference table). Apply exactly this
mapping (old → new):
- `engine/replay_contract` → `engine/contracts/replay_contract`
- `engine/scheduler_contract` → `engine/contracts/scheduler_contract`
- `engine/infrastructure_overview` → `engine/contracts/infrastructure_overview`
- `engine/observability_contract` → `engine/contracts/observability_contract`
- `engine/supported_gameplay_surface` → `engine/contracts/supported_gameplay_surface`
- `engine/worker_contract` → `engine/contracts/worker_contract`

Apply to every `expected_doc_ids` array entry matching these 6 distinct old-scheme strings,
across the 9 affected query objects (some queries list more than one `expected_doc_ids` value, e.g.
the "observability and replay for simulation determinism verification" query has two: both
`engine/replay_contract` and `engine/observability_contract` must be updated in that one query's
array). Do not alter any other field on these query objects (`query` text, other unaffected
`expected_doc_ids` entries in the same array, any threshold/weight fields) and do not alter any of
the other 52 queries.

**Every other writer to `tools/eval/queries.json`**: this is a hand-maintained fixture file, not a
generated artifact — grep confirms no code in `tools/` or `tests/` writes to it programmatically
(only `tools/eval_search.py` reads it, at `_run_query()`/the query-loading path). No concurrent-
write or ordering concern; this is a plain, single-editor fixture edit.

**Do NOT touch:** the 5 dangling `expected_doc_ids` entries referencing `tickets/done/` ticket IDs
(`TCK-20260612-LOCAL-CTX-EVAL`, `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`,
`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`, `TCK-20260713-MONITORING-SQLITE-INDEX`,
`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) — those derive `doc_id` from
`md_file.stem` alone (the `tickets/done/` corpus branch, a different code path this ticket does not
touch), confirmed unaffected by investigation. Do not touch `_strip_anchor()` in
`tools/eval_search.py` — orthogonal, protected by the `TCK-20260711` precedent.

**Verify:** `test_queries_json_expected_doc_ids_match_current_scheme` (test_plan.md item 7).

**Depends on:** Step 1 (the new-scheme values this step writes must match Step 1's actual output
format).

### Step 4 — Verify downstream consumers unchanged (no source edits)

**Files:** none changed. Test suites run only:
`tests/tools/test_context_packet_assembler.py`, `tests/tools/test_search_server.py`,
`tests/tools/test_search_mcp.py`, `tests/tools/test_hybrid_retrieval.py`,
`tests/tools/test_kgmcp_phase1_baseline_comparison.py`,
`tests/tools/test_kgmcp_measurement_baseline.py`.

**Change:** No code change. Run the regression suite listed above (per test_plan.md's Scoped
Pytest Commands) and confirm all pass unmodified. Investigation confirmed by direct reading of each
file:
- `context_packet_assembler.py::candidate_from_hybrid_result()` (`L144–165`): `source_id=result.doc_id`
  assigned once, never parsed — opaque passthrough.
- `search_server.py` (`L212`, `L124–128`): `doc_ids.index(doc_id)` exact-string lookup (both sides
  produced from the same build-time corpus pass, so the format change is consistent on both sides);
  `_derive_title()` uses `doc_id.split("/")[-1]`, nesting-depth-agnostic.
- `search_mcp.py` (`L132–133`, `L168–172`): same `_derive_title()` pattern, opaque `doc_id`
  passthrough in the response payload.
- `hybrid_retrieval.py`: `HybridResult.doc_id` (`L170`) opaque throughout; `resolve_metadata()`
  (`L104–120`) keys off `path`, not `doc_id` — REGISTRY lookups unaffected.
- `kgmcp_phase1_gateway_runner.py::_normalize_phase1_source_id()` (`L116–207`): only reference to
  `doc_id` is in its own docstring explaining why it was built not to depend on it; it reads
  `result["source_path"]` (`L109`), never `result["doc_id"]`.

Add new test 5 (`test_derive_title_agnostic_to_nesting_depth`, test_plan.md item 5) to
`tests/tools/test_search_server.py` and `tests/tools/test_search_mcp.py` as an explicit regression
guard confirming this claim in code, not just by inspection.

**Do NOT touch:** the source code of any of the 5 files named in this step — this step is
verification-only plus one new guard test per file pair. No behavior in these files changes.

**Verify:** full scoped pytest command from test_plan.md passes; new test 5 passes.

**Depends on:** Step 1 (must run against the corrected `doc_id` format to be a meaningful check).

### Step 5 — Re-run `make eval-search`, compare to documented baseline

**Files:** none changed (operational verification step).

**Change:** Run `make eval-search` after Steps 1–3 are complete and the index has been rebuilt
(Step 2). Compare Recall@5/Recall@10/MRR@10 against investigation.md's documented pre-fix baseline
(Recall@5 0.53 | Recall@10 0.65 | MRR@10 0.33, both below the pre-existing 0.80 pass threshold —
a known, out-of-scope condition per investigation.md, not something this fix is expected to cross).
Report the real post-fix numbers in `Test Summary`; do not adjust the fixture further to chase a
particular number — if numbers move (up or down) for reasons other than the 9 corrected entries,
investigate and report honestly rather than silently re-editing `queries.json` again.

**Do NOT touch:** the 0.80 pass threshold definition itself (out of scope — a pre-existing,
separately-tracked condition per investigation.md and the ticket's own AC #5 framing, which asks
only for "no regression," not for crossing the threshold).

**Verify:** `make eval-search` output recorded in ticket `Test Summary`; no regression relative to
the pre-fix baseline attributable to this change (a change in the 9 corrected queries' own hit/miss
status is expected and acceptable — that is the fix, not a regression).

**Depends on:** Steps 1, 2, 3 (rebuilt index + corrected fixture must both be in place first).

### Step 6 — Parity ledger entry `INFRA-340`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after the last existing entry (`INFRA-339`, confirmed the highest
existing ID by grep of `^- id: INFRA-` across the file) as `id: INFRA-340`, following the exact
field shape and precedent tone of `INFRA-294`/`INFRA-295`/`INFRA-296` (all read in full by
investigation — each documents a `tools/` agent-infrastructure change with `status: verified`,
`priority: P2`, `proof_type: regression`, a `test_path`, and a `support_boundary` note stating no
`src/` file was touched and no Mechanics Bible chapter/engine contract governs this module).
Content: `doc_id` derivation in `tools/knowledge_search.py::_collect_docs_chunks()` changed from
truncated `{section}/{stem}` to full nested relative path under `docs_root`; `v2_evidence` cites
`tools/knowledge_search.py:279–293` (new line numbers after Step 1's edit); `test_path:
tests/tools/test_knowledge_search.py`; `support_boundary` states no `src/` file touched, no
Mechanics Bible/engine contract governs `doc_id` semantics (matching the existing precedent
language investigation.md already confirmed applies here).

**Do NOT touch:** any existing `INFRA-*` entry (`INFRA-294` through `INFRA-339`) — append only,
this ledger is append-only per project convention.

**Verify:** `python3 tools/parity_ledger_lint.py` or equivalent existing lint/validate script (check
`Makefile`/`tools/` for the actual validator name during Implement) confirms the new entry is
well-formed YAML matching the ledger schema.

**Depends on:** Step 1 (line-number citation must reference the post-fix code).

## Scope Guards

- No change to `context_packet_assembler.py`, `search_server.py`, or `search_mcp.py` source code
  — their test suites are run, never edited, per Step 4.
- No change to `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` — confirmed unaffected;
  editing it is explicit scope creep the ticket's own Out of Scope section warns against.
- No change to `tools/knowledge_gateway_*.py` (the Knowledge Gateway MCP epic's own code) — ticket
  Out of Scope.
- No retroactive edit to `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`
  — that ticket's (`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`) historical record stands as-is;
  explicit ticket Out of Scope.
- No re-running of `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s full baseline comparison — ticket
  Out of Scope.
- No change to `eval_search.py::_strip_anchor()` or any `#anchor`-suffix composition/parsing logic
  anywhere (`knowledge_search.py`'s `f"{doc_id}#{anchor}"` f-strings, `_normalize_phase1_source_id()`'s
  anchor handling) — orthogonal to this fix, protected by the `TCK-20260711-EVAL-SEARCH-DOCID-
  ANCHOR-FIX` precedent.
- No change to `docs/guidelines/agent_working_environment.md` — confirmed its one `doc_id` example
  (line 136) is depth-1 and already correct under both old and new schemes; verified no other
  `doc_id`-shape claim exists in that file.
- No change to any `INFRA-*` entry other than the new `INFRA-340` append.
- No `--incremental` rebuild anywhere in the implementation or verification steps — `make
  knowledge-index-update` must not be substituted for `make knowledge-index` at any point in this
  ticket's execution.
- No `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` edits.
- No edits to `tools/retrieval_cache.py` or `knowledge-index/retrieval_cache.db` — distinct,
  unaffected module/file.

## Dependency Map

- Step 1 is the root change; Steps 2, 3, 4, 6 all depend on it (rebuild must run post-fix, fixture
  values must match post-fix format, consumer tests must run against post-fix format, ledger entry
  must cite post-fix line numbers).
- Step 5 depends on Steps 1, 2, and 3 jointly (needs the rebuilt index AND the corrected fixture to
  produce a meaningful, non-regressed comparison).
- Step 4 depends only on Step 1 (does not need the rebuilt index or fixture — consumer code reads
  `doc_id` as an opaque string regardless of index freshness, though running it after Step 2 is
  natural in execution order).
- Step 6 can run any time after Step 1 (does not depend on 2/3/4/5 completing, only on knowing the
  final line numbers).
- Suggested execution order: 1 → 2 → 3 → 4 → 5 → 6 (matches file order above; 4 and 6 could be
  reordered relative to 2/3/5 without correctness impact, but this order matches natural
  verification flow).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `investigation.md` reports real, quantified collision count | Already satisfied by investigation.md (0 collisions / 338 files / 120 truncated-but-non-colliding) — no plan step needed, pre-existing artifact | N/A (investigation.md itself) |
| `doc_id` derived from full nested relative path under `docs/`, verified against a real multi-level-nested doc | Step 1 | `test_collect_docs_chunks_preserves_full_nested_path`, manual check in Step 2's Verify against `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` |
| `knowledge-index/knowledge.db` rebuilt and confirmed to contain corrected `doc_id` values for a real sample of nested docs | Step 2 | manual sample query (Step 2 Verify) + `test_build_incremental_noop_leaves_stale_doc_id_documented` (guards against the silent-noop trap) |
| `context_packet_assembler.py`, `search_server.py`, `search_mcp.py` existing test suites all still pass against corrected `doc_id` format | Step 4 | `tests/tools/test_context_packet_assembler.py`, `tests/tools/test_search_server.py`, `tests/tools/test_search_mcp.py` (full suites, run unmodified) |
| No regression to `tools/eval_search.py`'s recall/MRR metrics vs. pre-fix baseline | Steps 3, 5 | `test_queries_json_expected_doc_ids_match_current_scheme` + `make eval-search` output compared to investigation.md's documented baseline (Recall@5 0.53 / Recall@10 0.65 / MRR@10 0.33) |

## Anti-Drift Notes

- **Do not conflate the `/`-nesting fix with the `#`-anchor fix.** `tools/knowledge_search.py:293`
  (pre-fix line number) is the sole target of Step 1 — the fix is `section`/`doc_id` derivation
  only; the `f"{doc_id}#{anchor}"` composition pattern used across all six chunk-emission sites
  stays byte-identical. Conflating the two would re-break the `TCK-20260711-EVAL-SEARCH-DOCID-
  ANCHOR-FIX` precedent, which explicitly declared the anchored chunk-level `doc_id` "correct and
  unaffected" and out of scope.
- **`make knowledge-index-update` will silently "succeed" (exit 0, print "Index is up to date")
  while leaving the bug live** — this is the single easiest trap in this ticket. Step 2 must use
  `make knowledge-index` (the full-rebuild target), confirmed against the real `Makefile:307` vs.
  `Makefile:313` target names, not inferred from naming convention alone.
- **`path_str` (built from `corpus_root`) already carries a `docs/` prefix; `rel` (built from
  `docs_root`) does not.** The new `doc_id` derivation in Step 1 must use `rel`, not `path_str` —
  using the wrong one would silently prepend a spurious `docs/` segment to every `doc_id`, breaking
  the depth-1 byte-identical-output guarantee (`test_collect_docs_chunks_single_level_path_unchanged`)
  and every existing chunk-anchor string.
- **Do not silently skip or "soften" the `queries.json` fixture update to make `make eval-search`
  look better** — the 9 entries are updated because they are now factually wrong under the
  corrected scheme, not to inflate the recall number. If Recall@5/MRR@10 shifts as a result (in
  either direction), report the real number in `Test Summary`.
- **The 5 remaining dangling `expected_doc_ids` entries in `queries.json`** (ticket-ID-keyed, not
  `docs/`-path-keyed) are a different, unrelated code path (`md_file.stem` for the `tickets/done/`
  corpus branch) — do not touch them; they are correctly out of this ticket's fix surface.
- **`resolve_metadata()` in `hybrid_retrieval.py` is `path`-keyed, not `doc_id`-keyed** — a
  reasonable but incorrect assumption during implementation might be that REGISTRY-authority lookups
  need updating too; investigation confirmed they do not (`docs/REGISTRY.yaml` is path-keyed
  already, unaffected by any `doc_id` scheme change).

## Deviations (recorded during Implement)

- **`tests/tools/test_eval_search.py::_KNOWN_STALE_DOC_IDS` required an update not listed in any
  plan step.** Discovered during Step 4/7 test-suite verification: `TCK-20260728-EVAL-FIXTURE-
  REPAIR` had previously added `test_no_stale_expected_doc_ids` plus a module-level
  `_KNOWN_STALE_DOC_IDS` set containing exactly the 4 full-path strings
  (`engine/contracts/replay_contract`, `engine/contracts/scheduler_contract`,
  `engine/contracts/observability_contract`, `engine/contracts/infrastructure_overview`) — that
  ticket had repaired `queries.json` in the *opposite* direction (full-path → truncated) to match
  the then-live, pre-this-fix truncated `doc_id` scheme, and asserted those full-path strings must
  never reappear in `queries.json`. This ticket's Step 1 fix + Step 3 fixture update reverses that
  direction (truncated → full-path is now correct), which put exactly those 4 strings back into
  `queries.json` and would have failed `test_no_stale_expected_doc_ids` had `_KNOWN_STALE_DOC_IDS`
  not been updated. Removed those 4 entries from `_KNOWN_STALE_DOC_IDS` (with an explanatory
  comment citing this ticket) and left the other 3 unrelated entries (`architecture/adr-004-*`,
  `architecture/adr-005-*`, `engine/contracts/progression_package` — all genuinely archived/
  excluded docs, unrelated to this fix) untouched. This is a small, mechanical, necessary
  consequence of Steps 1+3 as planned, not a scope change — recorded here per the project's
  "never silently deviate" rule since plan.md's Step 4 file list did not name this specific
  assertion.
- Steps 1–5 executed as planned, in the planned order (1 → 2 → 3 → 4 → 5). Step 6 (parity ledger
  `INFRA-340` entry) intentionally deferred to this ticket's own later Parity phase, per this
  ticket's explicit instruction — not executed in this Implement pass.
