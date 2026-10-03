---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION
artifact_type: investigation
tags: [ai, bug]
---

# Investigation — TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION

## Current Behavior

### `tools/knowledge_search.py::_collect_docs_chunks()` (L237–448), doc_id derivation at L279–293

```python
# Determine section: immediate subdirectory of docs_root
if len(rel_parts) > 1:
    section = rel_parts[0]
else:
    section = ""
stem = md_file.stem
...
doc_id = f"{section}/{stem}" if section else stem
```

`section` keeps only `rel_parts[0]` — the immediate subdirectory of `docs/` — discarding every
deeper path segment. `doc_id` is a document-level identity (no chunk qualifier); each chunk's own
`id` field is `f"{doc_id}#{heading_slug}-{seq:03d}"` or `f"{doc_id}#body-000"` (L305, 321, 348,
372, 391, 415, 435). Confirmed real example: `docs/engine/contracts/knowledge_gateway_mcp/
measurement_baseline_contract.md` (exists, 19290 bytes) → `section = "engine"`, `stem =
"measurement_baseline_contract"` → `doc_id = "engine/measurement_baseline_contract"`, silently
dropping `contracts/knowledge_gateway_mcp/`.

**Important shape detail not stated in the ticket**: the SQL `knowledge_docs.doc_id` column and
every downstream consumer (`cmd_build()` L706–712, `cmd_build_incremental()` L909–915,
`hybrid_retrieval.py`) actually receive `doc["id"]` (the **chunk**-level id, with `#anchor`
suffix) for `doc_chunk` rows — not the bare `doc["doc_id"]` field. This was intentionally fixed
this way by `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` (see Prior Work) which explicitly declared
the anchored chunk-level `doc_id` column "correct and unaffected" and out of scope to change. This
ticket's fix is orthogonal: it changes the **path-segment** derivation (`section`), not the anchor
suffix — `f"{doc_id}#{anchor}"` stays a 2-part split on the *last* `#`, and `_derive_title()`
(`search_server.py` L124, `search_mcp.py` L168) already splits on the *last* `/`
(`doc_id.split("/")[-1]`), which is nesting-depth-agnostic — no downstream code assumes exactly
one `/` in `doc_id`.

### Real-corpus collision count (mandatory quantification, ticket Scope item 1)

Wrote and ran a script computing `doc_id = f"{section}/{stem}"` for every real file under `docs/`
(excluding `docs/archive/` and `docs/lab/`, matching `_collect_docs_chunks()`'s own exclusion
guard exactly):

- **338 total files** scanned.
- **338 distinct `doc_id` strings** produced.
- **0 collisions** — no two distinct real files currently resolve to the same truncated `doc_id`.
- **120 of the 338 files (35.5%)** are nested more than one level under `docs/` and therefore have
  a *truncated* (but not yet *colliding*) `doc_id` today — e.g. all 5 files under
  `docs/engine/contracts/knowledge_gateway_mcp/` collapse to `engine/{stem}`, same as the ~29
  files directly under `docs/engine/contracts/` (depth 2) and the 8 files at depth 3–4. They
  happen not to share a stem with anything else today, but the risk is real and unbounded — any
  future doc added under a new subdirectory with a stem matching an existing shallower or
  differently-nested doc under the same top-level section silently overwrites/aliases in the BM25
  `doc_ids` list and in any code that treats `doc_id` as unique (e.g.
  `search_server.py`'s `doc_ids.index(doc_id)`, first-match-wins).
- Depth distribution (subdir levels before filename, `docs/` excluded): `{0: 3, 1: 215, 2: 83, 3:
  29, 4: 8}`.

**Verdict**: the ticket's "Collision risk" framing (item 1) is a real, currently-latent risk with
zero live collisions today — the "Confirmed real-world impact" framing (item 2) is the actual,
already-manifested problem, and it is not a same-index collision at all; it's a **cross-index
identity mismatch** (see next section).

### The actual confirmed real-world impact mechanism (not a collision)

`docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`'s "An additional,
genuine root cause discovered during Implementation" section (read in full) documents this
precisely: Phase 0's `doc_id` (truncated, `"engine/infrastructure_compat_contract"`) and Phase 1's
`source_id` (built from the full `source_path` field, normalizes to
`"engine/contracts/infrastructure_compat_contract#..."`) are **different strings for the same
document** even after Phase 1's own documented normalization (Design Decision D2) is applied
correctly. This caused `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s honest §4.3 recall FAIL for
5 of 7 entries (Q1, Q3, Q4, Q6, Q7), independent of the separate, expected Q2/Q5 architectural
cause (single-primary-provider routing).

### `tools/context_packet_assembler.py` (read in full)

`candidate_from_hybrid_result()` (L144–165): `source_id=result.doc_id` — assigned once, straight
through, never parsed, split, or pattern-matched anywhere in this file. `doc_id` is treated as a
fully opaque identity string. **No changes needed here; safe against the fix.**

### `tools/search_server.py` (read in full)

L212: `idx = _APP_STATE.doc_ids.index(doc_id)` — `doc_ids` is the BM25-parallel list
(`_ks._load_bm25()` returns `(bm25, doc_ids)`, itself built from `[d["id"] for d in corpus]` in
`_build_bm25_index()`, L484) and `doc_id` here is the SQL row's `doc_id` column value. Both sides
of this `.index()` lookup are produced from the same corpus-collection pass at build time, so as
long as the fix is applied consistently to both the SQL insert and the BM25 doc_ids list (it is —
both derive from the same `doc["id"]`/`doc_id` computation in `_collect_docs_chunks()`), this
remains an exact-string-match lookup on an opaque key. **No parsing of the `/`-nesting structure
anywhere in this file.** `_derive_title()` (L124–128) does `doc_id.split("/")[-1]` — takes the
*last* segment regardless of how many `/`s precede it, then strips a leading `NN_` numeric prefix
and title-cases. Nesting-depth-agnostic; unaffected by the fix.

### `tools/search_mcp.py` (read in full)

L132–133: `"doc_id": r.doc_id, "title": _derive_title(r.doc_id)` — same `_derive_title()`
implementation as `search_server.py` (L168–172), same nesting-depth-agnostic `.split("/")[-1]`
behavior. **No changes needed.**

### `tools/hybrid_retrieval.py` (read in full — not explicitly listed in ticket's Related Code
Areas but is the actual query-time consumer wired into `cmd_query()`'s hybrid path and
`search_mcp.py::_run_search()`)

`HybridResult.doc_id` (L170) is a frozen dataclass field, opaque string throughout
`hybrid_fuse_and_filter()`, `_dense_candidates()`, `_fetch_row_by_doc_id()`,
`reciprocal_rank_fusion()`, `filter_candidates()`, `resolve_metadata()`. `resolve_metadata()`
(L104–120) — the REGISTRY authority/freshness join — keys off **`path`**, not `doc_id`
(`registry_index.get(path)`), so `docs/REGISTRY.yaml` lookups are entirely unaffected by the
`doc_id` scheme change (REGISTRY is path-keyed already). **No changes needed anywhere in this
file**, but note it as an additional real consumer alongside the 3 named in the ticket.

### Incremental index-build path — the ticket's own flagged Open Question, resolved with evidence

**The ticket's premise is factually wrong on one detail and its practical conclusion is the
opposite of what a surface reading suggests.** Grepped `tools/knowledge_search.py` for
`hashlib`/`sha256`/`content_hash` — zero matches. There is **no content-hash-based cache-reuse
logic** anywhere in this file (that description applies to `tools/retrieval_cache.py`'s embedding
cache, a *different* module, per parity ledger entry INFRA-295 — not to `knowledge_search.py`'s
own manifest/cache pair). `knowledge_search.py`'s incremental path (`cmd_build_incremental()`,
L753–942) uses **mtime comparison** against `manifest.json` (`os.path.getmtime(p)` vs
`manifest[p]`, L783–791), nothing else.

Tracing the actual control flow for "code-derivation-scheme changed, but no `docs/`/`tickets/`
source file's mtime changed" (exactly this ticket's situation — the fix touches only
`tools/knowledge_search.py`, which is never itself a manifest-tracked corpus path):

1. L768: `corpus = _collect_corpus(corpus_root)` runs **unconditionally** on every incremental
   invocation, using the (now-fixed) live derivation code — so the freshly computed `corpus` list
   *does* contain correct new-scheme `doc_id`/`id` values in memory.
2. L781–795: every corpus path's mtime is compared against the manifest. Since no doc/ticket file
   changed, every path lands in `unchanged`; `new_paths` and `deleted` are both empty.
3. **L801–806**: `if n_changed == 0 and n_deleted == 0: print("... Index is up to date."); return
   0` — an **early return that exits before the DB is ever opened, written, or replaced.** The
   freshly-recomputed-but-discarded `corpus` from step 1 never reaches disk.

**Conclusion, stated definitively**: `make knowledge-index-update` (the incremental path) will
**silently no-op** after this fix lands — it will print "Index is up to date" and leave
`knowledge-index/knowledge.db` holding the **old, truncated** `doc_id` values indefinitely, because
its only change-detection signal (file mtime under 4 tracked corpus roots) is blind to a pure
source-code logic change. **A full, non-incremental rebuild — `make knowledge-index` (→
`cmd_build()`, which unconditionally `unlink()`s and rewrites `knowledge.db`, L679–681) — is
required** to actually apply this fix to the live index. This resolves the ticket's own flagged
Open Question with code-level evidence, not a guess, and corrects its "content-hash-based" premise
to the real mechanism (mtime-based manifest comparison with an unconditional-noop-on-zero-diff
fast path).

### `tools/agent-monitoring/kgmcp_phase1_gateway_runner.py::_normalize_phase1_source_id()` (read in
full, L116–207, plus its actual call site)

Grepped the entire file for `doc_id` — the **only** occurrence is inside this function's own
docstring (L128–129), explaining *why* Phase 1 was deliberately built not to depend on it. The
function itself only ever receives and transforms Phase 1's `evidence_id` strings (`doc:{path}#
{anchor}`, `ticket:{id}`, `file:{path}`, `symbol:{text}`) — built by
`tools/knowledge_gateway_packet_assembly.py::_evidence_id_for_context_search_result()` (read in
full, L100–125), whose own docstring states explicitly: *"`doc_id` is a chunk-scoped retrieval ID,
not a `docs/REGISTRY.yaml` registry-id, and is never used as the identity component — `source_path`
is the correct registry-id-shaped field."* Phase 1 already reads `result["source_path"]` (L109),
never `result["doc_id"]`. `_compute_threshold_4_3()` (L165–207) compares `gateway_sources`
(normalized Phase 1, `source_path`-derived) against `baseline_sources` — read verbatim from the
**frozen** `_PHASE0_FIXTURE_PATH` JSON fixture (historical, Out-of-Scope for this ticket to
re-run). Neither side of this comparison ever touches the live `doc_id` field.

**Verdict: `_normalize_phase1_source_id()` needs no update.** It was already built to be
insulated from this exact bug (per its own docstring, written with full knowledge of the
truncation). `tests/tools/test_kgmcp_phase1_baseline_comparison.py::
test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner` exercises the runner's
full live-call path (`run_corpus()`, all 7 corpus entries against the real gateway) — since that
path never reads `doc_id`, it is unaffected by this fix and should be re-run only as a
belt-and-suspenders regression check, not because code there needs to change.

### `tools/eval_search.py` and `make eval-search` (read in full)

`_run_query()` (L18–34) parses `knowledge_search.py query`'s tab-separated stdout, column 0 =
`doc_id` (chunk-anchored, per the `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX` precedent).
`_strip_anchor()` (L37–39) strips only the `#anchor` suffix (`doc_id.split("#", 1)[0]`) — it does
**not** touch the `/`-nesting structure at all, so it is unaffected by this fix mechanically. `make
eval-search` runs 61 real curated queries from `tools/eval/queries.json` and reports real
Recall@5/Recall@10/MRR@10 — this is a genuine, runnable regression check, confirmed functional
(last known real numbers per the precedent ticket: Recall@5 0.53 | Recall@10 0.65 | MRR@10 0.33,
below the 0.80 pass threshold — a pre-existing, out-of-scope-for-this-ticket condition, not
something this fix is expected to cross).

**However — a real regression risk in the fixture itself, found by direct measurement, not
inference**: cross-referenced all 61 queries' `expected_doc_ids` (35 distinct values) against the
real `docs/` corpus's current-scheme `doc_id`s. **9 of the 61 queries** have an `expected_doc_ids`
entry that names a truncation-affected (depth > 1) real doc under its OLD scheme:

| query | expected_doc_ids (old scheme) | real path (would become) |
|---|---|---|
| "replay contract determinism" | `engine/replay_contract` | `docs/engine/contracts/replay_contract.md` → `engine/contracts/replay_contract` |
| "scheduler_contract tick scheduling" | `engine/scheduler_contract` | → `engine/contracts/scheduler_contract` |
| "parity_ledger infrastructure status verified" | `engine/infrastructure_overview` | → `engine/contracts/infrastructure_overview` |
| "observability and replay for simulation determinism verification" | `engine/replay_contract`, `engine/observability_contract` | → `engine/contracts/replay_contract`, `engine/contracts/observability_contract` |
| "engine support matrix grid movement resource interaction official status" | `engine/supported_gameplay_surface` | → `engine/contracts/supported_gameplay_surface` |
| "worker_contract provider execution obligations" | `engine/worker_contract` | → `engine/contracts/worker_contract` |
| "observability contract signal emission requirements" | `engine/observability_contract` | → `engine/contracts/observability_contract` |
| "infrastructure_overview monitoring parity coverage status" | `engine/infrastructure_overview` | → `engine/contracts/infrastructure_overview` |

If `tools/eval/queries.json` is **not** updated to the new-scheme `doc_id` values in the same
change as the fix, these 9 queries' `_hit()`/`_reciprocal_rank()` comparisons will go from
correctly matching (today) to silently failing (post-fix) — a real, measured Recall@5/MRR@10
regression risk directly threatening this ticket's own AC #5 ("No regression to
`tools/eval_search.py`'s recall/MRR metrics"). The remaining 5 dangling `expected_doc_ids`
(`TCK-20260612-LOCAL-CTX-EVAL`, `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`,
`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`, `TCK-20260713-MONITORING-SQLITE-INDEX`,
`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) are ticket IDs from the `tickets/done/`
corpus source, whose `doc_id` derivation (`md_file.stem`, unrelated code path) this ticket does
not touch — confirmed not a concern.

## Mechanics / Engine Constraints

None. This is agent-orchestration/retrieval tooling under `tools/`, not simulation code — no
`docs/mechanics/*` chapter or `docs/engine/*` contract governs `doc_id` semantics, consistent with
the existing parity ledger precedent (INFRA-294/295/296 all state "no `src/` file touched, no
Mechanics Bible chapter or engine contract governs this module's semantics").

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: this fix is the same class of agent-tooling-
  infrastructure change as INFRA-294 (RRF fusion), INFRA-295 (retrieval cache), and INFRA-296
  (context packet assembler) — each added a new `INFRA-29x` entry documenting the change,
  `v2_evidence`, and a regression `test_path`. This fix should add a new entry (next available ID)
  under the same precedent, `status: verified`, `priority: P2`, `test_path` pointing at the new
  `tests/tools/test_knowledge_search.py` nested-doc_id regression test(s).
- `docs/guidelines/agent_working_environment.md`: contains a worked example at line 136
  (`"doc_id": "mechanics/02_combat_laws#h2-damage-formula-001"`) — this specific example is a
  depth-1 doc and is **not** affected by the fix (verified: `docs/mechanics/02_combat_laws.md` is
  one level under `docs/`), so no edit is strictly required to that example, but the doc should be
  checked during Implement for any other doc_id-shape claims that assume 2-segment paths.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry documents the `doc_id` derivation itself (checked
`infrastructure.yaml`, the only file whose entries reference `knowledge_search.py`/`search_mcp.py`
at all — INFRA-188, INFRA-294, INFRA-295, INFRA-296 — none of them describe `_collect_docs_chunks()`'s
`section`/`stem`/`doc_id` logic as their subject). None are P0. No existing `test_path` needs to be
re-verified as a precondition of this fix; a **new** entry is needed (see Docs Requiring Update).

## Prior Work

- **`TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`** (read in full) — the directly relevant
  precedent. Fixed `make eval-search`'s blanket 0.00 Recall@5/MRR@10 caused by a bare-vs-anchored
  `doc_id` string mismatch (`expected_doc_ids` in `queries.json` are bare `{section}/{stem}`;
  `knowledge_docs.doc_id` is chunk-anchored `{section}/{stem}#{anchor}`). Fixed by stripping the
  anchor **at comparison time in `eval_search.py` only** — explicitly declared
  `knowledge_search.py`'s anchored `doc_id` "correct and unaffected," out of scope to change.
  **Guarantee this fix must not regress**: `_strip_anchor()`'s anchor-stripping behavior stays
  correct (it operates on the last `#`, untouched by this ticket) — but this ticket's own change
  to the `/`-nesting *does* require a fixture update (`queries.json`'s 9 affected
  `expected_doc_ids`, detailed above) to keep that precedent's fix intact.
- **`TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH`** — original corpus-builder design this ticket
  corrects (introduced the `section = rel_parts[0]` truncation).
- **`TCK-20260612-LOCAL-CTX-MCP`** — built `search_mcp.py`; confirmed its `_derive_title()` is
  nesting-depth-agnostic (see Current Behavior).
- **`TCK-20260729-HYBRID-RETRIEVAL-FUSION`** / **`TCK-20260729-CONTEXT-PACKET-ASSEMBLY`** /
  **`TCK-20260729-RETRIEVAL-CACHE-LEVELS`** — built `hybrid_retrieval.py`,
  `context_packet_assembler.py`, `retrieval_cache.py` respectively, all of which already treat
  `doc_id` as an opaque string (confirmed above) — establishes the pattern this fix should follow
  (change the derivation, leave every consumer's opaque-string handling untouched).
- **`TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`** — the ticket that discovered this bug; its
  `phase1_baseline_comparison.md` §"An additional, genuine root cause" is the authoritative
  real-world-impact evidence, read and cited above. Its `kgmcp_phase1_gateway_runner.py`
  companion code was already built insulated from `doc_id` (confirmed above) — no update needed.

## Risks and Open Questions

- **Resolved** (was the ticket's flagged Open Question): the incremental build path
  (`make knowledge-index-update`) will silently no-op on this fix (see Current Behavior). **Plan
  must specify a full rebuild (`make knowledge-index`), not the incremental target**, to actually
  apply the fix to `knowledge-index/knowledge.db`.
- **New risk found, not in the ticket's original Open Questions**: `tools/eval/queries.json` has 9
  queries whose `expected_doc_ids` must be updated to the new nested-path scheme in the same
  change, or `make eval-search`'s Recall@5/MRR@10 will regress — directly threatening AC #5. Plan
  should treat this fixture update as in-scope, not a follow-up.
- Local dev environment currently lacks `sentence-transformers`/`sqlite-vec` installed (verified:
  both `ModuleNotFoundError` on plain `python3 -c "import ..."`) — the actual `make
  knowledge-index` full-rebuild + DB-content verification (AC #3) will need to run in an
  environment with `pip install -e ".[knowledge]"` completed (per the two-dev-environment note:
  `.venv/bin/python3` or `/home/vboxuser/Work/venv/bin/python3`). Not a scope question, just an
  execution-environment note for Implement.
- No open question blocks Plan. The two resolved items above (full rebuild required; queries.json
  fixture needs 9-entry update) should both be written explicitly into plan.md rather than
  discovered again during Implement.

## Anti-Drift Hazards

- **Do not touch anchor-stripping logic** (`eval_search.py::_strip_anchor()`,
  `_normalize_phase1_source_id()`'s anchor handling) — those are correct, precedent-protected
  behaviors for a different part of the `doc_id` shape (the `#anchor` suffix), orthogonal to this
  ticket's `/`-nesting fix. Conflating the two would re-break the `TCK-20260711` precedent.
  Reference `tools/knowledge_search.py:293` when scoping — the fix is `section`/`doc_id`
  derivation only.
- **Do not "fix" `kgmcp_phase1_gateway_runner.py`** — it was deliberately built not to depend on
  `doc_id`; editing it would be unnecessary scope creep the ticket's own Out of Scope section
  already warns against ("Any change to the Knowledge Gateway MCP epic's own code... remains
  untouched").
- **Do not re-run or alter `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON`'s committed results doc**
  (`phase1_baseline_comparison.md`) — explicitly Out of Scope; its historical FAIL result stands
  as recorded even after this fix lands.
- **Do not silently skip the `queries.json` fixture update** to make `make eval-search` "pass more
  easily" — update the 9 affected `expected_doc_ids` because they are now factually wrong (they'd
  describe the old, buggy scheme), not to inflate the recall number. If Recall@5 changes as a
  result, report the real new number.
- **Use a full rebuild, not `--incremental`**, for the index rebuild AC — confirmed above that the
  incremental path will no-op silently and appear to succeed (exit 0, "Index is up to date")
  while leaving the bug live. This is an easy, silent-failure trap for whoever implements this.
