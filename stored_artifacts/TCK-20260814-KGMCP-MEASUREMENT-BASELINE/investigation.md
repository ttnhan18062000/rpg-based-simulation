---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260814-KGMCP-MEASUREMENT-BASELINE
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement]
---

# Investigation — TCK-20260814-KGMCP-MEASUREMENT-BASELINE

## Current Behavior

### 0. Sibling ticket status (mandatory pre-Plan check per this ticket's own Scope)
`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` is **DONE** (`tickets/done/TCK-20260810-
CONTEXT-TOOLING-EFFECTIVENESS-TRACKING.md`, closed earlier this session as part of the
`agent-tooling-integrity-hardening` epic). Its landed work, confirmed by direct source read
(not assumed from the ticket text alone):

- Relocated `SEARCH_TOOL_NAMES`, `build_search_count_section(tools)`, and
  `build_raw_investigation_count_section(tools)` from `tools/agent-monitoring/
  retrieval_baseline_metrics.py` into `tools/agent-monitoring/generate_retro.py`
  (`generate_retro.py:336-427`), to resolve a circular-import constraint.
  `retrieval_baseline_metrics.py` now only re-imports these three names
  (`retrieval_baseline_metrics.py:28-37`) — it no longer defines them.
- Added `compute_search_investigation_trend(tools)` (`generate_retro.py:1049-1057`), a thin
  wrapper over the two relocated functions, wired into `generate()`'s `## Search &
  Investigation Effort` trended section.
- Extended `compute_tool_safety_metrics(events, tools)` (`generate_retro.py:1060-1172`) with a
  third top-level key, `read_count_correlation` (`generate_retro.py:1109-1141`): per-
  Investigate-phase-pair `Read`-call counts split by that pair's own search-before-grep
  compliance (`per_pair_compliance`, reused from the pre-existing `search_before_grep`
  computation — no second scan of `tools`), reporting `count`/`median`/`average` per group,
  `None` (never a fabricated `0`) for empty groups. Real last-observed numbers from the
  `--all` corpus run (documented in that ticket's Implementation Notes): compliant-group
  median 12.0 (n=138) vs. non-compliant-group median 9.0 (n=79).
- Added `compute_parity_index_readpath_call_count(tools)` (`generate_retro.py:298-321`) and its
  supporting path-anchored regex `_PARITY_INDEX_READPATH_RE` (`generate_retro.py:286`), wired
  into an always-rendered `## Parity Index Read-Path Usage` section — explicitly out of scope
  for this ticket's baseline work (a different subsystem, `tools/parity_index.py`, not the
  Knowledge Gateway).

**This ticket's baseline work must reuse `compute_search_investigation_trend`,
`build_search_count_section`, `build_raw_investigation_count_section`, and the general
"never-silent, `derivation`-string" convention those functions established — not build a
second `read_to_search_ratio`-equivalent computation.** The sibling ticket's own Scope
explicitly anticipated this ticket by name ("Extended by TCK-20260810-... to add a
raw-investigation... section" is already recorded against `INFRA-292` in
`docs/parity_ledger/infrastructure.yaml:6355-6357`, and this ticket's own Related Tickets
list cites it as the dependency).

### 1. `tools/agent-monitoring/retrieval_baseline_metrics.py` (current, post-relocation)
175 lines. A one-off/periodic snapshot tool (`build_baseline_report`, `retrieval_baseline_metrics.py:143-154`),
distinct from `generate_retro.py`'s recurring weekly cadence per its own module docstring
(`retrieval_baseline_metrics.py:1-20`). Composes exclusively from imports — `_load_runs_and_events`,
`load_jsonl`, `DEFAULT_TOOLS_FILE`, `_resolve_status`, `_is_gate_fail`, `SEARCH_TOOL_NAMES`,
`build_raw_investigation_count_section`, `build_search_count_section` (all from `generate_retro.py`),
plus `classify_provenance` (`legacy_reader.py`) and `_assert_safe_output_path` (`manifest.py`). It
never reimplements search/read counting — after the sibling ticket's relocation, **no
search/read-counting logic is defined in this file at all**; it is a pure consumer. Report keys:
`ticket_id`, `generated_note`, `context_tokens`, `search_count`, `raw_investigation_count`,
`duration`, `gate_outcome`, `review_rework`, `legacy_schema_notes` (`retrieval_baseline_metrics.py:143-154`).
`build_context_tokens_section()` (`retrieval_baseline_metrics.py:55-61`) explicitly reports
`status: "unavailable"` — real token/context-size telemetry is platform-blocked, cited against
`docs/agent-monitoring/schema.md`'s "What is not recorded" section. This is directly relevant to
this ticket's "serialized tokens returned" requirement (§20/§22): there is no live per-call token
count anywhere in `agent-monitoring/*.jsonl`; any token figure this ticket records must be a
one-time, explicitly-labeled manual/derived measurement (e.g. a character-based estimate or
direct provider-response byte count captured at corpus-recording time), not a claim of ongoing
platform telemetry.

### 2. `tools/agent-monitoring/generate_retro.py` (current, 1808 lines)
Key functions this ticket must reuse (verified by direct read, not the ticket text alone):
- `compute_search_investigation_trend(tools)` (`:1049-1057`) — the reusable entry point for
  search-count / raw-investigation-count numbers.
- `compute_tool_safety_metrics(events, tools)` (`:1060-1172`) — owns `read_count_correlation`.
  This ticket's §18.1 "repeated misses by entity and intent" and "queries that repeatedly
  require the same evidence set" requirements are a *different* metric (per-corpus-query
  repeated-demand, keyed by deterministic intent/entity ID) from `read_count_correlation`
  (per-Investigate-pair `Read`-count vs. search-before-grep compliance) — they must not be
  conflated even though both live conceptually under "search/investigation effort."
- `SEARCH_TOOL_NAMES` (`:336-340`) — frozenset `{mcp__knowledge-search__search_docs,
  ToolSearch, WebSearch}`. Out of Scope explicitly forbids modifying this.
- `_is_search_or_graphify_call` / `_is_grep_call` (`:227-250`) — the CLAUDE.md search-before-
  grep compliance detectors, a distinct vocabulary from `SEARCH_TOOL_NAMES` per its own inline
  comment (`:228-231`, "deliberately independent... do not import or reuse that constant here").
- `_PARITY_INDEX_READPATH_RE` / `compute_parity_index_readpath_call_count` (`:286-321`) — the
  "always-render 0 today, no code change needed once a call site exists" pattern this ticket
  should mirror for its own repeated-demand section if it starts at zero real data.

### 3. Existing latency/duration measurement infrastructure (question 3)
`agent-monitoring/tools.jsonl` already records a real, per-tool-call `duration_ms` field: "Wall-
clock milliseconds from PreToolUse to PostToolUse. `null` if the pre-hook temp file was missing"
(`docs/agent-monitoring/schema.md:367`). `agent-monitoring/runs.jsonl` records `duration_s`
(wall-clock seconds, `null` for crashed runs, `docs/agent-monitoring/schema.md:75`) and
`cost_proxy_score` (a weighted proxy over `Σ(Bash duration_ms)` plus other tool-type terms,
`docs/agent-monitoring/schema.md:215-227`). `tools/agent-monitoring/manifest.py` (Wrapper
pattern, `docs/agent-monitoring/schema.md:281`) measures `latency_ms` via `time.perf_counter()`
around a wrapped call — this is the existing, proven pattern for "measure wall-clock time of one
operation" that this ticket's lookup/evidence-validation/provider-fallback/packet-assembly/
end-to-end measurement-point *definitions* should cite as the intended instrumentation
mechanism, without inventing a new timing primitive. **No live gateway exists to attach this
instrumentation to yet** — Phase 0's own §20 wording is "Define separate measurement for lookup,
evidence validation, provider fallback, packet assembly, and end-to-end latency," not "measure
them," confirming this ticket's deliverable here is a measurement-point *contract* (what each
point means, where its wrapper attaches, what it will emit), not live code.

### 4. `tests/tools/test_retrieval_baseline_metrics.py` (321 lines, read in full)
Established conventions this ticket's new tests must mirror: (a) reuse-not-reimplement AST
guards (`test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`, `:55-67`) proving
the module never reads `*.jsonl` directly and never opens a file for writing outside
`--output`; (b) "never-silent" derivation-string tests for every section
(`test_baseline_report_search_count_is_marked_or_derived_never_silent`, `:110-114`); (c) explicit
zero/undefined handling instead of a crash or fabricated number
(`test_baseline_report_raw_investigation_count_ratio_never_silent_if_present`, `:177-199`,
covers both the finite-ratio and the `"undefined: ..."` string branches); (d) a real-corpus
plausibility test with no tmp_path substitution
(`test_baseline_report_raw_investigation_count_plausible_on_real_corpus`, `:201-206`); (e) a
zero-mutation guard against the real `agent-monitoring/` directory via `git status --porcelain`
before/after (`test_baseline_report_tool_causes_zero_diff_on_real_corpus`, `:294-307`); (f) a CLI
subprocess smoke test asserting the exact top-level key set
(`test_baseline_report_cli_runs_against_real_corpus_and_prints_json`, `:310-320`).

### 5. Representative-query corpus (investigation question 2)
No representative-query corpus fixture exists anywhere in this repo today. `grep`-equivalent
search across `*.py`/`*.md`/`*.json`/`*.yaml` for `representative_quer(y|ies)` returns only this
ticket, its epic parent, and `docs/plans/knowledge-gateway-mcp-proposal.md` itself — no prior
ticket created one. `tests/tools/fixtures/`, `test_corpus_registry.py`,
`test_tag_corpus_sweep.py`, and `test_corpus_perf_baseline.py` exist but cover unrelated corpora
(tag registry sweep, doc-corpus perf, Codex hook payload) — none is a query/retrieval corpus.
**This ticket creates the first one.**

### 6. Knowledge-Gateway MCP Phase 0 delivery-plan state (§20, direct read)
Of Phase 0's 10 checklist bullets, 7 are marked **Done** by the three already-closed sibling
tickets (`TCK-20260814-KGMCP-CONTRACT-SCHEMAS`, `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) and
1 is **Drafted / pending ratification** (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`). The
**3 bullets with no completion annotation at all** are exactly this ticket's scope:
"Record current latency, tool-call counts, repeated-demand signals, and returned-token estimates
for representative queries," "Define separate measurement for lookup, evidence validation,
provider fallback, packet assembly, and end-to-end latency," and "Predeclare measurable
promotion thresholds from that baseline" (`docs/plans/knowledge-gateway-mcp-proposal.md:1071-1075`).
This confirms the ticket's scope boundary against its siblings' already-landed work with no gap
or overlap.

### 7. Sibling contract-only precedent (investigation question 4)
Both closed KGMCP siblings (`KGMCP-CONTRACT-SCHEMAS`, `KGMCP-EVIDENCE-CACHE-IDENTITY`) delivered
**documentation/instrumentation-contract artifacts under `docs/engine/contracts/
knowledge_gateway_mcp/`**, plus AST/text-based tests in `tests/tools/`, with **zero edits to any
live gateway code** (none exists) and, per `KGMCP-EVIDENCE-CACHE-IDENTITY`'s own Implementation
Notes, a fixture-based test modeling a documented rule where "no live invalidation function
exists to call." This ticket's "define measurement points" and "predeclare thresholds" work
should follow the same shape: a new contract doc (e.g.
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`) defining the 5
latency measurement points as an instrumentation contract Phase 1+ code must emit into, plus a
**recorded-data artifact** (the corpus + its real baseline numbers) that is genuinely measured
now — unlike the two siblings, this ticket's AC explicitly requires *real tool invocations*, not
only contract prose ("recorded direct-tool baseline... using real tool invocations against this
repository, not estimates").

## Mechanics / Engine Constraints

None. This is agent-orchestration/retrieval tooling, not simulation logic — no `docs/mechanics/`
chapter or `docs/engine/` runtime contract (kernel, pipeline, combat, economy) governs it, matching
the posture both sibling KGMCP tickets already established
(`stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/investigation.md` "Mechanics / Engine
Constraints" section, and `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`'s equivalent). The only
CLAUDE.md constraint that applies is the Authoritative Mechanics Rule's parity-ledger clause,
addressed under Parity Ledger Overlap below.

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`: new contract
  doc (does not exist yet) defining the 5 distinct latency measurement points (lookup,
  evidence-validation, provider-fallback, packet-assembly, end-to-end per §18), the repeated-
  demand estimation design (deterministic intent/entity IDs and keyed query hash only, no raw
  prompt text, per §18.1), and the predeclared promotion thresholds derived from the recorded
  baseline (per §20) — mirrors the role and location of
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` for this
  ticket's subject matter.
- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 0 checklist's 3 currently-unannotated
  bullets ("Record current latency...", "Define separate measurement for lookup...",
  "Predeclare measurable promotion thresholds...") need a "**Done**
  (`TCK-20260814-KGMCP-MEASUREMENT-BASELINE`)" annotation with a cross-reference to the new
  contract doc and the recorded-corpus artifact, matching the sibling tickets' own annotation
  style at lines 1043-1094.
- `docs/agent-monitoring/README.md`: needs a note (under or beside the existing "Baseline Metrics
  Snapshot" section, `README.md:50`) pointing at the new representative-query corpus artifact and
  distinguishing it from the recurring `retrieval_baseline_metrics.py`/`generate_retro.py`
  cadence this ticket's own ticket text explicitly requires it to reuse, not duplicate.
- `docs/parity_ledger/infrastructure.yaml`: a new `INFRA-XXX` entry is warranted if this ticket's
  implementation adds real code (a corpus-recording script/module) under
  `tools/agent-monitoring/`, following the INFRA-281-through-INFRA-292 "agent-tooling-
  infrastructure precedent for ledgering this class of change" — see Parity Ledger Overlap below
  for the open question on whether this applies.

## Parity Ledger Overlap

- `INFRA-292` (`docs/parity_ledger/infrastructure.yaml:6348`, status: `verified`, priority: `P2`,
  `test_path` implied via `tests/tools/test_retrieval_baseline_metrics.py`) — covers
  `retrieval_baseline_metrics.py`'s baseline-metrics reporting tool, already amended once by the
  sibling `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s relocation addendum
  (`:6390-6394`). **Not P0** — no passing `test_path` is mandatory before this ticket's changes,
  but a real-corpus, non-fabricated test is still required by this ticket's own AC7.
- The two sibling KGMCP tickets (`KGMCP-CONTRACT-SCHEMAS`, `KGMCP-EVIDENCE-CACHE-IDENTITY`) each
  concluded **no parity ledger entry is required** for MCP wire-contract-only documentation, citing
  the `support_boundary` precedent already established for agent-monitoring tooling under
  `INFRA-281` through `INFRA-292` (their own investigation.md files, read directly). That
  precedent is scoped to *pure contract prose with no live code* — it does not automatically
  extend to this ticket if this ticket's implementation ends up adding a real Python
  module/script (e.g. a corpus-runner script under `tools/agent-monitoring/`) to actually record
  the "real tool invocations against this repository" baseline, since every `INFRA-281` through
  `INFRA-292` entry *does* cover real code in `tools/agent-monitoring/`. **Open question for
  Plan**, flagged rather than resolved here (see Risks and Open Questions below).
- No entry in any `docs/parity_ledger/*.yaml` shard currently references `knowledge_context`,
  `knowledge_gateway`, `kgmcp`, or `measurement_baseline` by text search — confirms no existing
  entry needs a status change on Investigate's own account (only a possible new entry).

## Prior Work

- `stored_artifacts/TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING/` — the direct
  predecessor this ticket depends on; its `investigation.md`/`plan.md` document exactly how
  `read_count_correlation`, the trended search/read-investigation section, and the
  parity-index read-path section were wired without duplicating loaders (the anti-duplication
  precedent `test_baseline_report_tool_reuses_load_data_pattern_not_a_fourth_loader` enforces).
- `stored_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/` — origin of
  `raw_investigation_count`/`read_to_search_ratio`, predecessor to the sibling above.
- `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/` and
  `stored_artifacts/TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY/` — direct structural precedent
  for how this ticket's Phase-0-contract-only deliverables should be shaped (new doc under
  `docs/engine/contracts/knowledge_gateway_mcp/`, AST/text-based tests in `tests/tools/`, a "Done
  (ticket-id)" annotation added to §20, zero edits to any not-yet-existing gateway code).
- `docs/agent-monitoring/schema.md` §"Detecting a specific script's subcommand in `Bash` rows" —
  the path-anchored-regex convention this ticket should reuse if it needs to detect any new
  tool-call shape in `tools.jsonl` (e.g. corpus-recording script invocations), rather than
  inventing a new detection idiom.

## Risks and Open Questions

1. **Blocking for Plan**: does "recorded direct-tool baseline... using real tool invocations
   against this repository, not estimates" require a new committed Python script under
   `tools/agent-monitoring/` (parity-ledger-relevant, testable, re-runnable), or a one-time,
   manually-run recording captured directly into the contract doc / a static JSON fixture (like
   the sibling KGMCP tickets' pure-doc deliverables)? The ticket AC's "Tests mirror
   `tests/tools/test_retrieval_baseline_metrics.py`'s never-silent, derivation-string convention"
   wording leans toward "a real script with `derivation` strings," which is a code-level pattern,
   not achievable in pure Markdown — Plan must decide and should treat this as the single
   highest-leverage design decision in this ticket, since it determines whether a new
   `INFRA-XXX` parity ledger entry is warranted (see Parity Ledger Overlap above).
2. **Repeated-demand design (§18.1) has no real data to seed from.** Since no gateway exists,
   there are no real `keyed query hash` records anywhere yet. The repeated-demand section can
   only be a *design* (schema for the deterministic intent/entity ID + query hash, and how
   repeated misses would be grouped) validated against the representative-query corpus itself
   (treating the corpus's own queries as a stand-in demand sample) — it cannot report real
   production repeated-demand numbers. This must be stated explicitly, not implied as live data.
3. **Token counts have no live telemetry source** (`build_context_tokens_section()` already
   reports `"unavailable"` for the existing baseline tool). Any "serialized tokens returned"
   number this ticket records must be a one-time manual/derived measurement with an explicit
   method disclosed (e.g. character-count heuristic, matching the already-frozen
   `kgmcp_char_heuristic_v1` method in `docs/engine/contracts/knowledge_gateway_mcp/
   redaction_retention_policy.md` §8) — reusing that already-ratified method, not inventing a
   second token-counting convention, is the lower-risk path and should be flagged to Plan.
4. **§20's explicit "do not invent thresholds before baseline exists" instruction** means the
   Implementation phase must genuinely run the representative-query corpus first and derive
   thresholds from the actual recorded numbers — a plan that predeclares specific numeric
   thresholds without having first executed the corpus queries would violate this ticket's own
   stated constraint and the proposal's explicit prohibition.
5. The `KGMCP-REDACTION-RETENTION-POLICY` ticket is only **drafted, not ratified**
   (`docs/plans/knowledge-gateway-mcp-proposal.md:1079-1083`) — if this ticket's token-counting
   approach depends on citing `kgmcp_char_heuristic_v1`, it should note that dependency is on an
   unratified draft, not a final decision, and should not treat it as more final than it is.

## Anti-Drift Hazards

- **Do not re-derive `read_to_search_ratio`, `search_count`, or `raw_investigation_count` from
  scratch.** Import and call `compute_search_investigation_trend`/`build_search_count_section`/
  `build_raw_investigation_count_section` from `generate_retro.py` exactly as
  `retrieval_baseline_metrics.py` already does — a second parallel computation is explicitly the
  failure mode this ticket's own Scope text warns against.
- **Do not touch `SEARCH_TOOL_NAMES`'s membership or the Bash-exclusion rationale** — Out of
  Scope explicitly forbids this, reused verbatim per the sibling ticket's own out-of-scope note.
- **Do not conflate `read_count_correlation` (search-before-grep compliance vs. Read-call count)
  with the new §18.1 repeated-demand metric** — they measure different things over different
  populations (Investigate-phase pairs vs. corpus queries) and must not be merged into one
  section or reuse one another's field names in a way that implies equivalence.
- **Do not fabricate latency/token numbers for measurement points that have no live gateway to
  measure.** The correct, honest output for "lookup latency," "evidence-validation latency,"
  etc. today is a measurement-point *definition* (what it means, where it will attach, what unit
  it will use) plus the *direct-tool* baseline numbers that stand in for the pre-gateway world —
  never an invented number dressed as a live measurement, matching the "never-silent,
  never-fabricated" convention every existing section in `retrieval_baseline_metrics.py`/
  `generate_retro.py` already follows.
- **Do not silently skip the `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` status check**
  the ticket itself calls out — it is real and already done, so Plan should build directly on its
  landed sections without re-litigating whether to build a parallel path.
- **Do not implement any part of a live gateway.** Out of Scope is explicit: "Wiring any of this
  into a live gateway — no gateway exists yet in Phase 0."
