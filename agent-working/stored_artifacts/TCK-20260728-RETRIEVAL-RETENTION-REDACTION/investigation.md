---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260728-RETRIEVAL-RETENTION-REDACTION
artifact_type: investigation
tags: [ai, observability, agent-monitoring]
---

# Investigation — TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Current Behavior

**No retrieval event, cache entry, or redaction concept exists anywhere in `src/` or `tools/`
today.** A repo-wide `grep -rli "redact"` (excluding `.git/` and `graphify-out/`) returns exactly 4
hits, all inside this batch's own planning docs/tickets
(`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`,
`ticket_plan_structure_phase2.md`, this ticket's own body in both
`tickets/inprogress/` and `tickets/todos/context-retrieval-phase2/`) plus two unrelated hits in
`stored_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/test_plan.md` and
`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/plan.md` that mean "redact secrets from a captured
CLI fixture," not "redaction policy for retrieval telemetry." This confirms the ticket's own
Assumptions claim: there is genuinely no prior redaction convention to extend, only a retention
convention (below) to extend by analogy.

**`src/observability/reporting/retention.py`** — the durable-artifact retention module the ticket
names as the thing to extend:

- `RetentionPolicy` (L13-57): `classify_run(manifest, base_dir) -> (category, reason,
  retention_days)`. Three categories, in priority order:
  - `baseline_source_run` (L36-37): `manifest.is_baseline_source == True` → `365*10` days
    (effectively permanent).
  - `important_failed_run` (L54-55): `status == "FAILED"` or `anomalies.json` contains a
    `severity == "CRITICAL"` entry → `protected_retention_days` (default 30).
  - `recent_run` (L57, fallback): everything else → `normal_retention_days` (default 7).
- `RetentionManager` (L60-241): `generate_cleanup_plan()` (L73-167) scans `data/runs/*` run
  directories, classifies each via the policy, computes `age_days` from `manifest.started_at`, and
  buckets into `eligible_runs` (expired) vs `protected_runs`. `execute_cleanup()` (L169-241) deletes
  a fixed list of heavy telemetry files (L129-143: `simulation_events.jsonl`,
  `metric_windows.jsonl`, `hard_law_violations.jsonl`, several `behavior_*` files) but preserves
  `run_manifest.json` (stamped with `telemetry_pruned: true`) and writes an audit log to
  `data/runs/cleanup_log.json`. Corrupted runs (missing manifest) are deleted wholesale.
  Note: this file does `from __future__ import annotations` (L1), so the unimported `Optional` used
  in `RetentionManager.__init__`'s type hints (L67-68) never raises at runtime (PEP 563 defers
  annotation evaluation) — a latent gap, not a live bug, and out of this ticket's scope to touch.
- **What this governs**: filesystem artifacts under `data/runs/{run_id}/` produced by *simulation*
  runs (kernel/observability output) — it has no relationship to `agent-monitoring/*.jsonl`
  (workflow/agent orchestration telemetry) or to any retrieval/cache concept.

**`src/core/retention.py`** — the in-memory analog:

- `OverflowPolicy` (IntEnum, L11-18): `REJECT`, `EVICT_OLDEST`, `TRUNCATE_NEWEST`, `COMPACT`
  (COMPACT raises `NotImplementedError` unless subclassed, L61-64).
- `RetentionError` (L21-23): raised only under `REJECT` when full.
- `BoundedBuffer[T]` (L26-89): a fixed-`capacity` deque-backed buffer with `append()` enforcing the
  policy, plus `to_list()`/`clear()`. No time-based duration concept at all — purely a bounded-count
  eviction primitive, orthogonal to `RetentionPolicy`'s day-based durations.
- Tests: `tests/unit/core/test_retention.py` (43 lines, 3 tests) cover `EVICT_OLDEST`, `REJECT`, and
  `TRUNCATE_NEWEST` directly against `BoundedBuffer`.

**`docs/agent-monitoring/schema.md`** — the "What is not recorded" section (queried per this
ticket's own scope) states token counts and per-agent tool-call counts are not recorded, for
platform reasons — it says nothing about retention/expiry of `runs.jsonl`/`events.jsonl`/
`tools.jsonl` themselves. Separately, grepping the rest of the doc confirms these three JSONL files
are **append-only with no pruning mechanism at all** — the "Historical Corrections" section
describes exactly one narrow, audited exception (a casing fix to 7 records) and explicitly states
"the file remains append-only for all writes going forward." **This is a material finding**: unlike
`src/observability/reporting/retention.py` (which actively deletes expired simulation-run
telemetry), the existing agent-monitoring schema has no analog of "delete after N days" — it is
retain-forever by convention. Any new retrieval-event family added to this schema (per the idea
doc's "Retrieval Observability and Dashboard" section) would, by default, inherit this
append-only-forever behavior unless the new decision doc explicitly says otherwise.

**`docs/observability/loki_label_policy.md`** — adjacent precedent cited by the ticket. It
authorizes exactly 6 low-cardinality static Loki stream labels and prohibits 8 named
high-cardinality dynamic identifiers (`tick`, `entity_id`, `worker_id`, `causal_id`,
`transaction_id`, `run_id`, `target_id`, `quest_id`) from ever being promoted to indexed labels —
they must live inside the structured JSON body instead, queried via LogQL's `| json` parser. This
is a **different mechanism** (index-cardinality control, not content redaction) governing a
**different system** (Loki stream labels, not retrieval cache/event telemetry) — useful only as a
structural analogy ("a fixed list of MAY/PROHIBITED identifiers, precisely enumerated, with a
stated mechanism for why") not as a source of literal field names to copy.

## Mechanics / Engine Constraints

None of `docs/mechanics/` (01-06) or `docs/engine/` govern this scope — those chapters are
simulation-law contracts (combat, economy, cognition, world evolution); this ticket is
agent-orchestration/retrieval tooling, a documented separate posture already established by the
sibling `docs/engine/contracts/context_packet_contract.md` (§4 Verification Path: "this contract
governs agent-orchestration/retrieval tooling, not simulation logic, the same posture already
recorded for agent-monitoring tooling under `docs/parity_ledger/infrastructure.yaml`'s INFRA-281
through INFRA-292 entries (`support_boundary` field)"). The same posture applies here — no
Mechanics Bible chapter or Engine Contract constrains this decision doc.

The two constraints that *do* directly bind this doc are both from the idea doc itself
(`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`):

- **Design Principle 5** ("No raw prompt or source-text telemetry," lines 74-76): "Monitoring
  stores identifiers, hashes, counts, scores, and reason codes—not full prompts, full retrieved
  content, or unredacted tool payloads." This is the literal MAY/PROHIBITED split the ticket's
  Acceptance Criteria demand.
- **Risks table** (lines 305-315), row "Retrieval telemetry leaks sensitive content" → mitigation
  "Store hashes, IDs, counts, and reason codes only; never raw prompts or chunks." Same vocabulary,
  restated as a risk/mitigation pair — this is the row Open Decision 4 exists to operationalize.
- **Promotion approval gate** (lines 250-262) also lists "privacy boundary: monitoring contains no
  raw prompts, raw retrieved source text, or sensitive tool payloads" as one of six conditions
  required before any scenario is promoted from advisory to default — meaning this decision doc's
  MAY/PROHIBITED list is not just descriptive, it is a precondition a later Phase 5 gate will check
  against.

## Parity Ledger Overlap

**None found.** A grep for `retrieval|redaction|retention|cache` across all 4 populated
`docs/parity_ledger/*.yaml` files (`strategic_cognition.yaml`, `combat_movement.yaml`,
`infrastructure.yaml`, `social_narrative.yaml`) returns only unrelated hits: strategic-cognition
project/lead retention bonuses, movement-plan/route caches, API `ReadModelCache`, and one
retrieval-baseline-metrics entry (`INFRA-...` at `infrastructure.yaml:5931-5956`, `test_path:
tests/tools/test_retrieval_baseline_metrics.py`) that documents the *baseline-measurement tool*
from the sibling `TCK-20260728-RETRIEVAL-BASELINE-METRICS` ticket, not this decision. None concern
a retrieval-event/cache-entry retention or redaction policy.

This is consistent with the sibling `docs/engine/contracts/context_packet_contract.md`'s explicit
statement that agent-orchestration/retrieval tooling does not require a parity ledger entry (same
`support_boundary` posture as `infrastructure.yaml` INFRA-281 through INFRA-292). No P0 entries are
affected; **no new parity ledger entry is needed** for this decision doc.

## Prior Work

Three sibling decision docs landed in this exact batch (all dated 2026-07-29, all resolving one
Open Decision from the same idea doc, all under the same epic
`TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`) establish the structural precedent this doc must
follow:

1. **`docs/ai/default_packet_scenarios_decision.md`** (`TCK-20260728-DEFAULT-PACKET-CRITERIA`,
   resolves Open Decision 1) — pattern: verified-facts-first, cites real tool output
   (`retrieval_baseline_metrics.py`), explicitly refuses to fabricate a token-count figure where
   evidence doesn't support one, states tiers as "directional... not measured," and marks the
   epic ticket's own Open Decision line `RESOLVED` with a citation rather than editing the idea doc.
2. **`docs/ai/code_test_index_boundaries_decision.md`** (`TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`,
   resolves Open Decision 2) — pattern: verifies claims directly against installed package source
   (not assumed), explicitly corrects a factual error in the ticket's own stated premise
   (`rationale_for` misclassification), and states unresolved gaps plainly rather than papering over
   them.
3. **`docs/engine/contracts/context_packet_contract.md`** (`TCK-20260728-CONTEXT-PACKET-SCHEMA`,
   resolves Open Decision 3) — pattern: lands under `docs/engine/contracts/` (not `docs/ai/`)
   because it is a data-*shape* contract, not a process-decision record; explicitly states two
   labeled "Extension" sections beyond the idea doc's literal field list (the `unrated` sentinel for
   non-registry-backed `kind` values, and the `parity_ledger_entry` proxy); and states explicitly
   that "no code change accompanies this document." Its `included[]` field list (source_id, kind,
   path, heading_or_symbol, **hash**, authority, freshness, **score**, inclusion_reason,
   excerpt_budget) is the exact vocabulary this ticket's MAY-contain list (hashes, IDs, counts,
   reason codes, scores) must stay consistent with — `hash` and `score` are already-named
   `ContextPacket` fields, not new terms this doc invents.

All three share one procedural precedent directly relevant here: **the idea doc's own "Open
Decisions" list is never edited directly** — resolution is recorded only in the epic ticket's
Assumptions/Open Questions section (already done for Decisions 1-3, see
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` lines 80-116), with the same
`OPEN DECISION N — **RESOLVED** (date, ticket_id): <question> Answer: <summary>. Full ... :
<doc path>` line shape.

**`stored_artifacts/TCK-20260518-CACHE-REGISTRY/investigation.md`** — a much older ticket about an
entirely different kind of cache (`MovementPlanCache`, `ReadModelCache`, `AuthoritativeState`'s
spatial-grid caches — in-memory simulation caches governed by `ICacheable`/`CacheRegistry`/
`CacheBudgetPolicy` in `src/engine/cache_registry.py`). This is **not** directly reusable prior art
for retrieval/redaction policy — it establishes an eviction/budget pattern for gameplay-simulation
caches, not a retention-duration-and-content-redaction pattern for agent-tooling telemetry. Cited
here only to confirm no closer prior art exists; do not conflate the two systems.

**Process note (not part of this doc's content, but relevant to Finalize):** this ticket's actual
source todos file is `tickets/todos/context-retrieval-phase2/TCK-20260728-RETRIEVAL-RETENTION-REDACTION.md`
(verified identical via `diff` to the `tickets/inprogress/` copy) — a *different* folder than
`tickets/todos/context-efficient-retrieval/SEQUENCE.md`, which the ticket's own Related Code Areas
lists. The `context-efficient-retrieval/` folder is the already-completed Phase 0-1 batch (all 3
tickets done, files already `rm`'d, leaving only its `SEQUENCE.md`) — a different batch from this
one. See Anti-Drift Hazards below for the Finalize-time implication.

## Risks and Open Questions

1. **"Explicitly extending RetentionPolicy's categories" must not be read as a code mandate.** The
   ticket's own Scope/AC wording ("explicitly extending `src/observability/reporting/retention.py`'s
   RetentionPolicy categories") sits next to an equally explicit Out of Scope line forbidding any
   change to `retention.py`. The only coherent reading: this decision doc extends the *conceptual
   category taxonomy* (the `recent_run`/`important_failed_run`/`baseline_source_run` naming and
   duration-tiering pattern) in prose/design only, as new named categories a **future** Phase 3
   ticket would add to `retention.py` or a sibling module — not a literal diff to the file today.
   This should be stated explicitly in the decision doc itself to prevent a future reader (or a
   Verify-phase gate) from treating "extending" as evidence code should have landed.
2. **Agent-monitoring's append-only-forever convention conflicts with a duration-based retention
   model for retrieval events specifically.** The idea doc's own "Retrieval Observability and
   Dashboard" section proposes adding retrieval events to "the shared monitoring schema" — but
   `docs/agent-monitoring/schema.md` confirms `runs.jsonl`/`events.jsonl`/`tools.jsonl` are
   append-only with no deletion mechanism at all today (unlike `retention.py`'s active
   7d/30d/permanent pruning of `data/runs/*` simulation artifacts). This decision doc must take an
   explicit position: does "retention" for retrieval events mean (a) they get their own
   `RetentionPolicy`-style prunable category once a future writer exists, or (b) they inherit
   agent-monitoring's retain-forever convention and "retention" here means content redaction only,
   not duration? Flagging this rather than assuming an answer — this materially changes what
   "retention duration... for retrieval events" in the AC actually resolves to.
3. **Doc location is directionally supported but not confirmed.** The ticket's own Related Code
   Areas calls `docs/observability/retrieval_retention_redaction_policy.md` a "working suggestion,"
   not a mandate. Direct analogy to `docs/observability/loki_label_policy.md` (same directory, same
   "policy" naming shape, same MAY/PROHIBITED-list structure) supports this location strongly — but
   it diverges from both sibling patterns in this same batch (`docs/ai/*_decision.md` for
   process-decision records, `docs/engine/contracts/*.md` for data-shape contracts). Since this doc
   is neither purely a decision-record nor a data-shape contract but closest in kind to
   `loki_label_policy.md` (an operational data-handling policy), `docs/observability/` is the better
   fit of the three candidates — but this is this investigation's judgment, not a confirmed mandate,
   and the Plan phase should make the final call explicitly rather than by default.
4. **Three cache levels have materially different natural retention shapes**, per the idea doc's
   own Cache design table (§"3. Cache design"): embedding/index cache is keyed by content hash +
   chunking version (stable until source/model changes — closer in spirit to
   `baseline_source_run`'s long duration); query-result cache is keyed by normalized query + corpus
   generation + retrieval version (invalidated on any indexed-source or ranking change — closer to
   `recent_run`'s short duration); context-packet cache is keyed by task/ticket/phase + cited hashes
   (explicitly ticket/task-scoped, likely the shortest-lived of the three, arguably should not
   outlive the ticket it was built for). A single blanket duration across all three would
   contradict the idea doc's own "not one blanket policy" framing (also called out in this ticket's
   Assumptions). The decision doc must assign each level its own category rather than reusing one
   number for all three.

## Anti-Drift Hazards

- **Do not touch `src/observability/reporting/retention.py`, `src/core/retention.py`, or any
  `tools/agent-monitoring/*.py` writer.** Explicit Out of Scope and an Acceptance Criterion in the
  ticket itself; a Verify-phase gate should treat any diff touching these paths as a scope
  violation.
- **Do not force-resolve Open Decisions 1, 2, 3, 5, or 6.** 1-3 are already resolved by sibling
  tickets in this same batch (see Prior Work); 5 and 6 remain explicitly open on the epic ticket and
  are out of scope here (the ticket's own Out of Scope line: "Force-resolving any Open Decision
  other than Decision 4").
- **Do not fabricate precision this corpus cannot support.** Following the
  `default_packet_scenarios_decision.md` precedent of refusing to invent a token-count figure when
  `context_tokens` is platform-unavailable: this doc may specify concrete retention *durations*
  (the ticket explicitly asks for exactly that, and `retention.py`'s own day-based categories are a
  reasonable, cited basis to extend by analogy) but must not invent exact storage-size limits,
  precise dollar/compute costs, or byte-level payload caps not grounded in any existing measurement.
- **Do not edit the idea doc's own "Open Decisions" list.** Per the established sibling precedent
  (context_packet_contract.md §4), resolution is recorded only in
  `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open Questions
  section — mark "OPEN DECISION 4 — **RESOLVED**" there, matching the exact line shape used for
  Decisions 1-3.
- **Do not conflate `loki_label_policy.md`'s label-cardinality mechanism with this doc's
  content-redaction mechanism.** They solve different problems (index-cardinality explosion vs.
  sensitive-content leakage) for different systems (Loki stream labels vs. retrieval cache/event
  payloads) — cite it only as structural precedent for "a precisely enumerated MAY/PROHIBITED
  list," never copy its literal identifier list as if it applied to retrieval telemetry.
- **Finalize-time folder mismatch**: this ticket's real source file lives in
  `tickets/todos/context-retrieval-phase2/`, not the `tickets/todos/context-efficient-retrieval/`
  path the ticket body's Related Code Areas names (that path is the separate, already-completed
  Phase 0-1 batch folder, which currently retains only its `SEQUENCE.md` after all 3 of its ticket
  files were `rm`'d — a pre-existing, unrelated housekeeping gap, not this ticket's doing).
  `context-retrieval-phase2/` has no `SEQUENCE.md` and, once this ticket's file is removed, will
  become fully empty — per the "never leave a completed folder's skeleton in `tickets/todos/`" rule,
  Finalize should remove the now-empty `context-retrieval-phase2/` directory rather than leaving an
  empty skeleton behind, and should not confuse it with `context-efficient-retrieval/`.
