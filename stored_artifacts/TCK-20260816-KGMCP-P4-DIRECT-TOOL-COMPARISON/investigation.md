---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON
artifact_type: investigation
tags: [ai, mcp, testing]
---

# Investigation — TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON

## Current Behavior

### Central question resolved: this ticket has genuinely new, non-duplicative work

Sibling ticket 3 (`TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`, DONE, `INFRA-353`)
answered a different question ("should any workflow phase call the gateway") using **only
already-existing** Phase 1-3 measurement documents (`phase1_baseline_comparison.md`,
`phase2_baseline_recomparison.md`, `phase3_pilot_acceptance_measurement.md`) and
`RETRO-2026-W33.md`. Its own `INFRA-353` entry states explicitly it used "the real, committed
Phase 1-3 latency/token measurements ... without cherry-picking" — it never ran a new live
gateway-vs-direct call, and it never measured or discussed "quality" at all: a full-text grep of
every `docs/engine/contracts/knowledge_gateway_mcp/*.md` file, `docs/plans/knowledge-gateway-mcp-
proposal.md`, and this ticket's own file for the word "quality" turns up **zero** occurrences
anywhere except this ticket's own Scope/Acceptance Criteria text. Ticket 3's evidence covers the
latency/token half of this ticket's Scope item (b) only in aggregate/per-candidate-point form, not
a fresh paired per-entry run, and never touches the quality/completeness half at all.

Three concrete, real gaps make this ticket's own live run necessary rather than reusable from
Phase 1-3 fixtures:

1. **Stale Q3 routing.** `TCK-20260816-KGMCP-P4-PARITY-ADAPTER` (DONE, `INFRA-351`) changed
   `ROUTING_TABLE["requirement_completeness_verification"]` from a dead-end
   (`primary_providers=("context_search",)`, `not_yet_routed="parity_ledger"`, never actually
   dispatched) to a real, live `primary_providers=("context_search", "parity_ledger")` row whose
   `call_providers_for_routing_decision()` branch now genuinely reaches
   `tools/parity_index.py::entry()` (`docs/plans/knowledge-gateway-mcp-proposal.md:1366-1380`). This
   directly affects `Q3_requirement_completeness` — one of the corpus's 7 entries. Every existing
   Phase 1/2/3 fixture recorded Q3's gateway response **before** this change landed, so those
   numbers no longer describe current gateway behavior for that entry. A fresh live run is required
   to compare against the current system, not a historical one.
2. **`TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`** (DONE, `INFRA-352`) resolved what its own
   investigation calls "a genuine conflict, not yet resolved" in changed-path routing integration —
   another live-behavior change postdating the Phase 1-3 fixtures.
3. **The graphify half of source-completeness has never been measured, in any phase.** Phase 1's
   `_compute_threshold_4_3()` (`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py:143-190`,
   Design Decision D3) explicitly evaluates §4.3's no-regression-recall threshold using the
   `context_search` half of the source union **only**, because the Phase 0 baseline fixture
   (`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`) recorded graphify's
   `raw_stdout_bytes` (a byte count) but never a resolvable source list. Every `recall_report` in
   the Phase 3 fixture still carries `"graphify_half_status": "N/A"` verbatim, unchanged since
   Phase 1. This N/A has never been closed across 3 phases. Closing it is real, new instrumentation
   work this ticket's Scope item (b) implicitly requires (graphify is one of the two direct-tool
   calls named in Scope's own example, `search_docs`/`graphify query`).

### What "run the real equivalent direct-tool call" concretely means per entry

Per `tools/agent-monitoring/kgmcp_baseline_runner.py` (the Phase 0 precedent, frozen/read-only) and
`tools/agent-monitoring/kgmcp_phase1_gateway_runner.py` through `kgmcp_phase3_gateway_runner.py`
(the gateway-side precedent, frozen/read-only per each's own module docstring "never touches"
list):

- **Context Search direct call:** `tools/search_mcp.py::_run_search(query_text, top_k=8)`, called
  directly (never through `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check` — those write to
  `agent-monitoring/events.jsonl`, which every one of these runner scripts must never mutate),
  timed with `time.perf_counter()`.
- **Graphify direct call:** `subprocess.run(["graphify", "query", query_text], cwd=repo_root,
  capture_output=True, text=True, timeout=120)`, CLI-shelled per
  `docs/engine/contracts/knowledge_gateway_mcp_contract.md` Design Decision D1 (no in-process
  adapter exists).
- **Parity Ledger direct call (new as of this ticket, per the ticket's own Scope example):**
  `tools/parity_index.py::entry(entry_id, db_path=None)` (signature at
  `tools/parity_index.py:550`) — only meaningful for `Q3_requirement_completeness`, the one entry
  whose `use_case` is `feature_completeness_check` and whose routing shape now genuinely dispatches
  to `parity_ledger`. This was not callable at Phase 0 (`kgmcp_baseline_runner.py`'s own
  `_PARITY_LEDGER_NOT_YET_CALLABLE_NOTE` disclosed this honestly at the time) and is the first
  ticket where a real parity-ledger-adapter comparison is even possible.
- **Gateway call:** `tools/knowledge_gateway_mcp.py::_run_knowledge_context(query_text)`, loaded
  in-process via `importlib.util` (mirroring `kgmcp_phase1_gateway_runner.py:_load_gateway_module`),
  timed the same way, `providers_selected` read from a direct `knowledge_gateway_router.route()`
  call.

### Raw output retention gap — the concrete new instrumentation this ticket adds

No predecessor fixture retains the raw text of either side for content/quality comparison:
- `kgmcp_baseline_runner.py::_run_context_search()` captures `raw_results` in its return dict
  (L85), but `run_corpus()`'s written `entry["context_search"]` dict (L144-150) **drops it**,
  keeping only `results_count` and `sources_recalled` (a doc-id list). Confirmed by reading the
  committed fixture: `entries[0]["context_search"].keys()` is exactly `{derivation, latency_ms,
  results_count, sources_recalled, tool_call_count}` — no raw text field.
- `_run_graphify()` captures `raw_stdout` (L108) but `run_corpus()` keeps only
  `raw_stdout_bytes` (a byte count) — confirmed the same way:
  `entries[0]["graphify"].keys()` is `{derivation, latency_ms, raw_stdout_bytes, tool_call_count}`.
- No Phase 1/2/3 fixture keeps the gateway's own raw response text either — only derived counts,
  `source_id` lists, and pass/fail booleans (confirmed via `entries[0].keys()` on the Phase 3
  fixture: fields are latency/token/cache-status/recall/conflicts records, never a raw payload
  string).

A quality/completeness comparison genuinely needs the raw text (or a structured evidence-item list
with enough content to judge, not just an id) on **both** sides for at least the querying agent's
own judgment pass. This is new instrumentation, not a re-derivation from existing fixtures — no
prior runner or fixture in this repo has ever persisted it.

## Mechanics / Engine Constraints

Not applicable in the Mechanics Bible sense (agent-infrastructure measurement, not simulation
mechanics), mirroring ticket 3's own finding. The governing constraints are
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 4's fourth bullet ("Compare gateway
packets against existing direct-tool behavior") and `measurement_baseline_contract.md`'s existing
§4.1/§4.2/§4.3 threshold definitions, which this ticket's new runner must reuse (via import, not
reimplementation) for the latency/token/recall axes and extend only for the genuinely new
quality/graphify-recall axis.

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: mark Phase 4's fourth bullet ("Compare gateway
  packets against existing direct-tool behavior") done, mirroring the inline "**Done**
  (`TCK-...`)" annotation style already used for the first bullet at proposal.md:1368, citing this
  ticket's real per-query-type result.
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`: new file — the
  real per-query-type latency/token/quality comparison result, in the same location and audience as
  the sibling `phase1_baseline_comparison.md`/`phase2_baseline_recomparison.md`/
  `phase3_pilot_acceptance_measurement.md` docs this ticket's own methodology extends.
- `docs/parity_ledger/infrastructure.yaml`: new `INFRA-354` entry (next ID after `INFRA-353`),
  certifying this ticket's measurement tool and honest reporting as correct/tested — mirroring
  `INFRA-353`'s own "certifies methodology, not conclusion" precedent, per this ticket's own
  Acceptance Criteria #4.

## Parity Ledger Overlap

- `INFRA-353` (`docs/parity_ledger/infrastructure.yaml:10201`) — sibling ticket 3's entry; direct
  precedent for this ticket's own entry's "methodology, not conclusion" framing and for confirming
  no live paired run or quality axis was ever measured there.
- `INFRA-351` (`:10053`) — Parity Adapter; the real routing-behavior change (Q3 now dispatches to
  `parity_ledger`) that makes reusing Phase 1-3 fixtures for Q3 stale.
- `INFRA-352` (`:10138`) — Changed-Path Context; the second real behavior change postdating Phase
  1-3 fixtures.
- `INFRA-350`, `INFRA-339` (`:9941` and earlier) — Phase 3 and Phase 1 measurement-methodology
  entries; same "certifies methodology" precedent this ticket's own new entry follows.
- No P0 entries are touched — this is a measurement/reporting ticket with no runtime behavior
  change to certify as P0-correct; the new `INFRA-354` entry is `P2`, mirroring `INFRA-353`'s own
  priority, and still requires a real passing `test_path` per `schema.json`'s `status: verified`
  requirement regardless of priority.

## Prior Work

- `stored_artifacts/TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION/` — read in full (see
  Current Behavior above); establishes both the precedent this ticket's parity entry follows and
  the concrete evidence that this ticket's own quality/live-run work is not already done.
- `stored_artifacts/TCK-20260816-KGMCP-P4-PARITY-ADAPTER/` and
  `stored_artifacts/TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT/` — establish the two concrete
  behavior changes (see Current Behavior above) that make a fresh live run necessary.
- `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `kgmcp_phase1_gateway_runner.py`/`kgmcp_phase2_gateway_runner.py`/`kgmcp_phase3_gateway_runner.py`
  — the direct precedent this ticket's own new runner must import from (`CORPUS`, `CORPUS_VERSION`,
  `kgmcp_char_heuristic_v1_token_count`, `_compute_threshold_4_3` where reusable) and must never
  reimplement, mirroring every predecessor's own explicit "imports, never reimplements" convention.
- `tests/docs/test_redaction_retention_policy_doc.py` — structural precedent for a doc-only test
  (`test_path`) against a static markdown file's required section headings and phrases; this
  ticket's own new results doc can follow the same pattern for its `test_path`.

## Risks and Open Questions

- **Genuinely open, must not be assumed away: the frozen 7-entry corpus has no "gold" answer for
  any entry.** `kgmcp_baseline_corpus.CORPUS` (`tools/agent-monitoring/kgmcp_baseline_corpus.py`)
  carries only `id`, `query_text`, `routing_shape`, `use_case` per entry — no expected-answer,
  expected-source-set, or rubric field anywhere. Neither `docs/plans/knowledge-gateway-mcp-
  proposal.md` §22 (Representative Use Cases) nor any Phase 0-3 doc defines a correctness rubric.
  This means "quality" cannot be scored as an objective pass/fail the way latency/tokens/recall-
  against-Phase-0-baseline can. The two defensible, honestly-labeled proxies available are: (a)
  source/evidence-set completeness — extending the existing §4.3 recall proxy to finally cover the
  graphify half (closing Design Decision D3's 3-phase-old N/A), which is at least mechanically
  reproducible; and (b) a disclosed, necessarily subjective judgment call by whoever runs this
  ticket's Implementation, reading both sides' raw content per entry and stating plainly whether the
  gateway's budget/dedup/routing dropped something materially useful the direct call kept, or vice
  versa. (b) must be reported as a soft, reviewer-judged signal, never dressed up as a scored
  metric — the plan.md and the resulting doc must say this explicitly, not imply an objective score
  exists. This is a real limitation of the corpus, not a limitation of this ticket's method; do not
  resolve it by inventing a rubric that redefines "quality" beyond what Scope's own language
  ("equal-or-better answer," "drops something a direct call would have kept") already implies —
  that language is itself judgment-based, not formula-based.
- **Open, not blocking:** whether Q2/Q5 (the two graphify-primary-routed entries per Phase 1's
  Design Decision D4) will show a genuine graphify-side recall gap once finally measured, or whether
  Design Decision D3's 3-phase-old gap turns out to be closeable with 100% recall — the real
  measurement decides; this investigation does not assume either outcome.
- **Open, not blocking:** whether the ticket's new runner should re-run Q3 against the
  now-current gateway only, or also re-run all 7 entries fresh (rather than reusing Phase 3's
  still-current numbers for the 6 unaffected entries) for full self-consistency of a single
  "as-of-today" comparison table. Given Changed-Path-Context (`INFRA-352`) also touched live
  routing/cache behavior in ways not fully scoped by this investigation, the safer, more honest
  choice is a full fresh 7-entry run rather than a partial re-run — Planning should decide and
  record this explicitly rather than silently mixing stale and fresh numbers in one table.

## Anti-Drift Hazards

- **Do not silently mix stale Phase 1-3 fixture numbers with fresh Phase 4 numbers in the same
  comparison table without labeling which is which.** At minimum, Q3 must be freshly measured; see
  the open question above on whether all 7 should be.
- **Do not invent an objective "quality score" the corpus cannot support.** Report the source-
  completeness proxy and the disclosed subjective judgment separately, and label the latter as
  reviewer judgment, not a computed metric — per Scope's own language, which is itself
  judgment-phrased ("does it drop something ... a direct call would have kept").
- **Do not let the new `INFRA-354` entry certify the comparison's *conclusion*** (whether the
  gateway wins or loses per query type) — per this ticket's own Acceptance Criteria #4 and
  `INFRA-353`'s own precedent, it certifies the measurement tool and honest reporting only.
- **Do not touch any frozen predecessor file.** `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `kgmcp_baseline_runner.py`, `kgmcp_phase1_gateway_runner.py`,
  `kgmcp_phase2_gateway_runner.py`, `kgmcp_phase3_gateway_runner.py`, and every existing
  `tests/tools/fixtures/kgmcp_*_results.json` file are read-only inputs, mirroring every
  predecessor runner's own explicit "never touches" list.
- **Do not implement any workflow integration.** Out of Scope explicitly forbids any diff to the
  gateway, router, cache, or Parity adapter, and forbids declaring Phase 4 complete or the gateway
  broadly superior/inferior — this ticket reports the real, per-query-type measurement only.
