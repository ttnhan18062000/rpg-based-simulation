---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-EXACT-LOOKUP-CONVENTION
artifact_type: investigation
tags: [ai, documentation]
---

# Investigation — TCK-20260802-EXACT-LOOKUP-CONVENTION

## Current Behavior

**`tools/parity_index.py` — the exact-lookup precedent.**

- `_connect_readonly(db_path)` (`tools/parity_index.py:87-92`): the shared read-only entry
  point for all three query functions. Raises `IndexNotBuiltError` if the derived SQLite DB
  doesn't exist yet (`:88-91`), otherwise opens `sqlite3.connect(f"file:{db_path}?mode=ro",
  uri=True)` (`:92`) — a connection-string-level read-only guarantee, not just "we don't call
  `.execute` with a write verb." No `entry()`/`impact()`/`health()` call site ever opens a
  writable connection.
- `entry(entry_id, db_path=None)` (`:485-531`): exact primary-key lookup (`SELECT * FROM
  entries WHERE id = ?`, `:489`). Explicit, typed no-match shape: `{"entry_id": entry_id,
  "found": False}` (`:493`) — never an exception, never an empty dict, never a silently-empty
  list. On a hit, joins all four `_REF_TABLES` (`code_refs`/`test_refs`/`constraint_refs`/
  `ticket_refs`, `:76`) plus `entry_health`, each row carrying an explicit
  `selection_reason` string from `_selection_reason()` (`:95-98`) so a caller can see *why* a
  reference was attached, not just that it was.
- `impact(changed_path=None, test_path=None, symbol=None, db_path=None)` (`:534-593`): exact
  path-equality lookup (`WHERE path = ?`, `:545`/`:552`) across `_IMPACT_PATH_TABLES` (`:80`,
  `code_refs`/`constraint_refs`/`ticket_refs`) plus `test_refs`. No filter at all →
  `{"status": "no_filter_provided", "results": []}` (`:536`); a filter with zero hits →
  `{"status": "no_match", "results": []}` (`:583`); the two "nothing happened" states are
  distinguishable in code, not collapsed. Results are sorted deterministically by
  `(_PRIORITY_ORDER, _STATUS_SEVERITY, entry_id)` (`:575-581`, `_PRIORITY_ORDER`/
  `_STATUS_SEVERITY` defined at `:78-79`) — never similarity score. `symbol` is accepted but
  explicitly never used for filtering; when passed, an explicit `warnings` list states this
  in the response (`:585-589`) rather than silently ignoring the argument or pretending
  symbol-level precision was achieved — proven by
  `tests/tools/test_parity_index.py::TestImpactQuery::test_impact_never_claims_symbol_level_match`
  (`:697-724`).
- `health(subsystem=None, priority=None, db_path=None)` (`:596-643`): exact equality filters
  on `entries.subsystem`/`entries.priority` (`:607-612`), deterministic `ORDER BY
  entries.shard, entries.id` (`:615`), returns a `summary` (ledger generation metadata) plus a
  flat `findings` list — no ranking, no relevance score field at all.
- Module docstring (`:34-36`) states the exact/fuzzy boundary explicitly: `"impact, entry, and
  health (the Phase-2 read path) were added by TCK-20260731-PARITY-IMPACT-PROOF... search
  (FTS-backed) remains out of scope and unimplemented."` This is not incidental — it is a
  named, deliberate boundary the module's own author already drew.
- `tests/tools/test_parity_index.py::TestArchitectureGuards` (`:513-546`) enforces this
  boundary at the test level: `test_impact_entry_health_still_forbid_search_cli` (`:515-533`)
  asserts `add_parser("search"...)` is absent from source and `--help` output never mentions
  `search`; `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` (`:535-546`) asserts no
  `parity-record`/`parity_record` token and no `open(..., "w")`/`.write_text()` call touching
  `docs/parity_ledger` anywhere in the module.

**`tools/hybrid_retrieval.py` — the fuzzy counterpart.**

- `reciprocal_rank_fusion(ranked_lists, k=DEFAULT_RRF_K)` (`:59-77`): literal RRF, `score =
  sum(1/(k+rank))` per channel a doc_id appears in (`:73-77`). This is a similarity/relevance
  *score*, structurally incomparable to `impact()`'s priority/status sort key (already
  established as Constraint B in `context_packet_contract.md` §5, cited below).
- `filter_candidates(ranked_lists, metadata_by_id, *, authority_in=None, freshness_in=None)`
  (`:127-156`): pre-fusion metadata filtering, opt-in (`:142-143`), preserves relative order,
  excludes rather than down-ranks.
- `hybrid_fuse_and_filter(...)` (`:224-331`): orchestrates bounded independent dense (ANN,
  `_dense_candidates()`, `:193-211`) + lexical (BM25) retrieval, unions by `doc_id`, applies
  `filter_candidates()`, fuses via `reciprocal_rank_fusion()`, returns `HybridResult` objects
  ranked by fused score (`ordered_ids = sorted(..., key=lambda d: (-fused_scores[d], d))[:top_k]`,
  `:299`). Built specifically to fix a confirmed bug where a lexical-only exact match could
  fall outside the dense channel's candidate cut (module docstring, `:11-19`) — i.e. even this
  fuzzy path's own history shows exact-match cases are a known hazard *within* similarity
  search, reinforcing why a separate deterministic-exact path is valuable for cases (like gate
  evidence) that cannot tolerate a ranked/approximate answer.

**`docs/engine/contracts/context_packet_contract.md` — current state.**

Ends at `## 6. Open Decision 8 Resolution` (line 393 of the file as read). §1-§2 define the
`ContextRequest`/`ContextPacket` schema; §3 resolves Open Decision 3 (per-`kind`
authority/freshness population, three branches: REGISTRY-backed / `unrated` sentinel /
differently-shaped-primitive); §4 is the verification path (states this contract needs no
`docs/parity_ledger/` entry, same posture as agent-monitoring tooling); §5 resolves Open
Decision 7 (cross-kind ranking — three technical constraints resolved, residual
inclusion-floor/ordering question explicitly deferred to human sign-off, zero repo precedent
for the underlying mechanism); §6 resolves Open Decision 8 (`stored_artifact` becomes a new
REGISTRY-backed `kind`, Branch 1; `staging_artifacts/` exclusion confirmed intentional
permanent design). This ticket appends `## 7. Open Decision 9 Resolution` after §6, following
the identical additive pattern §5 and §6 already established — no edit to §1-§6's existing
text.

## Mechanics / Engine Constraints

None from `docs/mechanics/` — this ticket is agent-orchestration/retrieval tooling
documentation, not simulation logic, the same posture `context_packet_contract.md` §4
already states explicitly for this entire contract family ("this contract governs
agent-orchestration/retrieval tooling, not simulation logic... A future reader should not
read the absence of a parity ledger entry here as a gap").

The one binding "engine contract" constraint is procedural, not mechanical: this ticket's
Scope/Out-of-Scope explicitly forbids editing `context_packet_contract.md` §1-§6's existing
text (only additive `## 7.` is permitted) and forbids any code change to `tools/parity_index.py`,
`tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, `tools/generate_registry.py`.

## Docs Requiring Update

- `docs/engine/contracts/context_packet_contract.md`: append a new `## 7. Open Decision 9
  Resolution` section (after the existing `## 6. Open Decision 8 Resolution`) recording the
  yes/no verdict on naming the exact-vs-fuzzy split as a general convention — required
  regardless of which verdict Plan/Implement lands on, since both the "yes" and "no" AC
  branches (ticket lines 45-46) require writing the resolution into this doc (or a named
  sibling doc).

Also required, though not a `docs/` path (so tracked here for completeness, not in the bullet
above): `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s `OPEN DECISION
9` entry (`:205-209`) should move from `**UNRESOLVED**` to `**RESOLVED**` with a one-paragraph
outcome summary and citation to the new §7, mirroring exactly how
`TCK-20260802-CONTEXT-KIND-PRIORITY` and `TCK-20260802-STORED-ARTIFACT-KIND` each updated
their own Decision entry (7 and 8 respectively) in this same epic ticket.

## Parity Ledger Overlap

None found. Searched `docs/parity_ledger/infrastructure.yaml` for any entry whose `text`/
`v2_evidence` mentions `parity_index.py`, `hybrid_retrieval.py`, or `context_packet` — six
matches (`INFRA-294` through `INFRA-299`, all `status: verified`, `priority: P2` except
`INFRA-299` at `P1`), covering `hybrid_retrieval.py`'s RRF module, the retrieval cache, the
`ContextPacket` assembler, the retrieval-event field set, retro metrics rendering, and the
shadow-packet call site — but **none for `tools/parity_index.py` itself**. This is expected,
not a gap: `context_packet_contract.md` §4 already establishes that this whole tooling family
(agent-orchestration/retrieval infra, not simulation logic) does not require a
`docs/parity_ledger/` entry, and `parity_index.py`'s own docstring and the Gate A decision doc
confirm it was reviewed and landed under that same non-simulation posture. This ticket
produces no new parity-ledger-relevant behavior change either way (documentation-only, no code
touched) — no entry ID needs updating.

## Prior Work

- `docs/ai/parity_readpath_gate_a_decision.md` — the direct evidentiary basis for whether the
  exact-lookup pattern has "enough real signal." **Verdict: GO** (§"Verdict" line 22), but
  explicitly **narrowly scoped**: §5 states the GO verdict rests on `impact()`/`entry()`/
  `health()` never regressing recall relative to two legacy comparison surfaces
  (`find_p0_intersection`, `derive_mapping`) on a 9-case corpus (6 real + 3 synthetic), with
  aggregate recall 66.7% vs. 4.8% (§4) and zero unexplained false positives (§3). Critically,
  §5's own "Next action" explicitly scopes the *next* step as "a future Phase-3 ticket to
  define how impact()/entry()/health() would be wired behind a workflow gate or shadow context
  packet" — i.e. even the GO verdict's own authors treated "wire this into real use" as the
  next open question, not "generalize this into a naming convention for other kinds." The gate
  decision measured parity-domain retrieval quality; it did not measure or claim anything about
  whether the *pattern shape* (read-only SQLite index, exact equality lookup, deterministic
  sort, explicit no-match shape) would transfer to a different `kind`'s data.
- `tests/tools/test_gate_a_readpath_review.py` — the reproduction harness for the Gate A
  numbers (`docs/ai/parity_readpath_gate_a_decision.md` §7), confirms the review re-verified
  pinned real ledger data and asserted `tools/parity_index.py` byte-identity throughout.
- `tickets/done/TCK-20260802-CONTEXT-KIND-PRIORITY.md` (Open Decision 7) and
  `tickets/done/TCK-20260802-STORED-ARTIFACT-KIND.md` (Open Decision 8) — both closed siblings
  from the same 2026-08-02 batch (`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/
  ticket_plan_structure_opendecisions_7_9.md`), same additive-`context_packet_contract.md`-section
  pattern, same epic-ticket-entry-update pattern, same "if genuine value judgment, say so
  plainly rather than presenting a self-chosen answer as settled" instruction repeated in both
  their own Assumptions/Open Questions. Decision 7 ultimately *did* defer its hardest residual
  question (inclusion-floor/ordering) to human sign-off, citing "zero existing repo precedent
  for the underlying mechanism." Decision 8 reached a definitive "yes" without deferral,
  because it had strong technical grounds: the frontmatter fields empirically and structurally
  matched Decision 3's existing Branch 1 vocabulary (`STATUS_VALUES`/`AUTHORITY_VALUES`
  literally shared, not analogous), and a real empirical corpus scan (2,941 files) supported
  the claim. These two outcomes are the direct precedent for how to weigh Decision 9: Decision
  9's situation is closer to Decision 7's ("do we have real precedent to derive an objective
  answer from, or is this a value call reasonable people could contest?") than to Decision 8's
  (clean structural/vocabulary match).

## Risks and Open Questions

- **The central open question this ticket must resolve is a genuine value judgment, not a
  technical derivation, and the investigation should say so plainly** (see "own honest
  assessment" in the final report — not duplicated here to avoid the investigation.md
  pre-deciding what Plan should weigh). The risk is that Plan/Implement resolve it by default
  toward "yes, name a convention" simply because the GO verdict language is available to quote,
  without confronting that the GO verdict is about parity-domain recall, not about
  pattern-generalizability.
- **n=1 risk.** No second real `kind` has ever needed a gate-safe exact lookup. Any
  "applicability criteria" section written now cannot be tested against a second case, so it
  either overfits to `parity_index.py`'s specific implementation choices (SQLite, materialized
  `entry_health` table, four fixed `_REF_TABLES`) or is abstracted so far that it's
  unfalsifiable until a real second use case arrives to test it against.
- **Scope-creep risk explicitly flagged by the ticket itself**: "Real risk of scope creep into
  implementation since parity_index.py's Gate A verdict was GO — explicitly forbidden in this
  batch" (ticket Assumptions/Open Questions). A convention section that reads as an
  implementation invitation (e.g. prescriptive "future kinds must implement X") rather than a
  documentation record would itself be a soft violation of Out of Scope's "no building of a
  second exact-lookup module to prove the pattern," even though it is only prose.
- If a "yes, adopt a convention" verdict is chosen, the new §7 must be careful not to imply
  `tools/parity_index.py`'s specific SQLite-backed architecture is now mandatory for any future
  gate-safe lookup — the generalizable properties (read-only access, deterministic sort,
  explicit typed no-match response, no similarity ranking, no mutation surface) are separable
  from the specific storage technology chosen for this one instance.

## Anti-Drift Hazards

- Do not touch `docs/engine/contracts/context_packet_contract.md` §1-§6's existing text —
  append-only, exactly like §5 and §6 before it. `TestArchitectureGuards`-style hash/byte
  fixture tests in the two sibling test files
  (`tests/tools/test_context_kind_priority_decision.py`,
  `tests/tools/test_stored_artifact_kind_decision.py`) already assert §1-§5/§1-§6 stayed
  byte-identical across their own tickets; a new test for this ticket must add the same
  guarantee for §1-§6 remaining untouched by the §7 append.
  Do not renumber `## 6.` or shift its heading level.
- Do not edit `tools/parity_index.py`, `tools/hybrid_retrieval.py`,
  `tools/context_packet_assembler.py`, or `tools/generate_registry.py` — zero diffs required
  (ticket AC #5). In particular, do not add a `search` subcommand to `parity_index.py` "to
  prove the point" — `TestArchitectureGuards::test_impact_entry_health_still_forbid_search_cli`
  (`tests/tools/test_parity_index.py:515-533`) already asserts this is absent and must keep
  passing unmodified.
- Do not re-litigate Open Decisions 1-6 (context_packet_contract.md §1-§3), 7 (§5), or 8 (§6) —
  this ticket's own scope explicitly forbids reopening them.
- Do not conflate the Gate A GO verdict's *parity-retrieval-quality* claim with a claim about
  *pattern-generalizability* — these are two different assertions and the investigation above
  found no evidence the GO verdict document itself ever makes the second claim.
