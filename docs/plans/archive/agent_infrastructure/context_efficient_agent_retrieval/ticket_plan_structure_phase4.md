---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-07-29
archived: 2026-08-04
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Phase 4

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`'s Phase 4 only.

This supersedes `ticket_plan_structure_phase3.md` for this batch — Phase 3 is now
`DONE` (`TCK-20260729-DETERMINISTIC-CODE-INDEX`, `TCK-20260729-HYBRID-RETRIEVAL-FUSION`,
`TCK-20260729-RETRIEVAL-CACHE-LEVELS`, `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`), giving
this phase real, working retrieval/fusion/cache/assembly code to instrument.

## Scope this batch to Phase 4 of the source doc's "Sequenced Future Epic" only

Phase 4 is **"Observability and dashboard proof — add retrieval events through the
approved shared writer and dashboard/retro queries; validate provider parity."** This
is the FIRST phase in the sequence that touches the monitoring-writer path itself —
treat it with the highest scrutiny of any phase so far. The Maturity banner still
applies in full: this batch does not authorize a new mandatory workflow gate or a new
external retrieval service. Nothing built in this phase may be wired into any
`.claude/workflows/*.js` file or invoked automatically by any existing pipeline —
Phase 3's modules remain standalone, directly-testable, callable manually; Phase 4 adds
*observation* of manual/test invocations, not automatic invocation.

**Ground every ticket in this batch in the following confirmed facts — do not
re-derive or silently contradict them:**

- `docs/parity_ledger/infrastructure.yaml` `INFRA-293`/`INFRA-294`/`INFRA-295`/`INFRA-296`
  — the 4 real, working Phase 3 modules this phase instruments:
  `tools/code_test_index.py`, `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`,
  `tools/context_packet_assembler.py`. None are wired into any workflow — any new
  retrieval event this phase adds is recorded by *test/manual invocation call sites
  within this phase's own tickets*, not by intercepting real agent workflow runs.
- `tickets/done/TCK-20260728-PHASE0-PREREQ-CONFIRMATION.md` — confirms the Phase 0
  prerequisite (provider-neutral execution identity, shared monitoring writer, stable
  replay/live boundary) is satisfied, but **only for `tools/agent-monitoring/tools.jsonl`**:
  `execution_id`/`provider`/`ticket_id` are written into every `tools.jsonl` record via
  `post_tool_hook.py:84-86`, sourced from `.claude/current_run`'s sidecar. **`runs.jsonl`
  and `events.jsonl` — written by `record_run.py`/`record_events.py` — do NOT carry
  `execution_id` or `provider` fields today** (verified: neither string appears in either
  file). This is a real, load-bearing gap: the idea doc's suggested retrieval-event field
  list (`execution_id`, `provider`, `agent_role`, `workflow`, `phase`, `ticket_id`) is only
  half-available in the schema this phase must write into.
- `docs/agent-monitoring/schema.md` — the authoritative two-file (`runs.jsonl`/
  `events.jsonl`) append-only schema, `tools/agent-monitoring/writer.py`'s
  `write_line()`/`write_lines()` as the sole verified append path (per Phase 0's AC2),
  and the derived, gitignored, rebuild-only `agent-monitoring-index/monitoring.db`
  (`build_index.py`) as the read path — never write to the index directly.
- `tools/agent-monitoring/generate_retro.py`, `tools/agent-monitoring/query.py`, and the
  existing dashboard surface (`dashboard-frontend/`) — the "dashboard/retro queries" this phase's
  AC must extend, not replace or fork. (The sibling `experiments/agent_ops_dashboard/` sandbox
  cited when this phase was originally written was deleted 2026-08-04,
  `TCK-20260804-PLANS-EXPERIMENTS-SWEEP`, as fully-shipped scaffolding; `dashboard-frontend/` was
  always the real delivered surface.)

**RESOLVED (do not re-litigate in this batch):** given the `execution_id`/`provider`
gap above, this batch's retrieval events MUST stay `run_id`-scoped only — the same
shape every existing `events.jsonl` record already uses (`run_id`, `seq`, `phase`,
`agent`, `status`, `summary`, `ts`, plus this batch's new retrieval-specific fields).
Do NOT add `execution_id` or `provider` to `runs.jsonl`/`events.jsonl` as part of this
batch — that is a `runs.jsonl`/`events.jsonl` schema-extension decision Phase 0-3 never
made, and forcing it here would silently expand this phase's actual scope into a
writer-schema migration beyond "add retrieval events through the approved shared
writer." If a ticket's investigation finds this constraint makes an idea-doc field
genuinely un-populatable (e.g. cross-provider dashboard comparison), flag it plainly as
a follow-on Phase 4b/Open-Decision item — do not silently invent a new top-level field.

**This batch should produce standard-tier ticket(s) whose deliverable is: (a) a new,
versioned retrieval-event family written exclusively through
`tools/agent-monitoring/writer.py`'s existing `write_line`/`write_lines` (no new writer
mechanism, no new file-locking scheme — Phase 0's Candidate 1 design is already decided
and evidenced, reuse it), (b) call sites inside Phase 3's own test/manual-invocation
paths (or new instrumented wrapper functions) that emit these events when
`tools/hybrid_retrieval.py`/`tools/retrieval_cache.py`/`tools/context_packet_assembler.py`
are exercised, (c) new query functions extending `generate_retro.py`/`query.py` for the
dashboard views the idea doc lists (cache hit/miss/stale rates, candidate-to-selected
ratios, freshness/authority distribution), and (d) a provider-parity validation that is
explicitly structural/test-based only — per Phase 0's own evidentiary bar, since zero
real Codex pilot executions have occurred and none may be attempted here.**

**Cover these source-doc items, each traceable to a concrete deliverable:**

1. **Retrieval event family, `run_id`-scoped** — a new, additive event shape appended to
   `events.jsonl` (not a new file — reuse the existing two-file schema) recording, per
   the idea doc's "Retrieval Observability" table, only the fields populatable under the
   `run_id`-only constraint above: `scenario`/`risk_tier` (if caller-supplied), corpus/
   graph generation, retrieval version, cache level/status, latency, candidate count,
   selected count, source-kind counts, authority/freshness counts, exclusion reason
   counts, cited-source hashes, adequacy verdict, expansion reason/count. MAY/PROHIBITED
   fields follow `docs/observability/retrieval_retention_redaction_policy.md`'s existing
   rules verbatim (hashes/IDs/counts/reason codes/scores only — never raw prompt or
   retrieved-content text) — this is a Phase 2 decision already resolved, do not
   re-derive it.
2. **Writer integration, zero new mechanism** — call sites that invoke
   `tools/agent-monitoring/writer.py`'s `write_line`/`write_lines` directly or via
   `record_events.py`'s existing pattern, proven append-only and lock-safe by Phase 0's
   own stress tests. Do not introduce a new lock/queue/journal design — Candidate 1 from
   `docs/ai/monitoring_writer_decision.md` §3 is already decided.
3. **Dashboard/retro query extensions** — new functions in `generate_retro.py`/
   `query.py` (or a clearly-scoped new module they import) producing the decision-support
   views the idea doc's "Retrieval Observability and Dashboard" section lists: cache hit/
   miss/stale-rejection rates by level, candidate-to-selected and selected-to-cited
   ratios, freshness/authority distribution, follow-up/expansion rate. Each view must be
   unit-tested against a fixture events file, not just eyeballed against live data.
4. **Structural provider-parity check** — a test/assertion (mirroring
   `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes()`'s
   read-only-invariant style) confirming the new retrieval-event shape is provider-
   neutral in its own field definitions (no Claude-Code-only or Codex-only field), even
   though no real Codex execution can populate it yet. Do not claim live cross-provider
   parity — only field-shape parity, explicitly labeled as such.

**Do NOT ticket in this batch** (still gated behind this phase's own evidence, per the
doc's Sequenced Future Epic):
- Shadow context packets, advisory-mode invocation, or any `.claude/workflows/*.js`
  wiring (Phase 5-6) — this phase only *observes* manual/test invocations, it does not
  make retrieval events fire automatically during real ticket workflows.
- Any `execution_id`/`provider` field addition to `runs.jsonl`/`events.jsonl` — see the
  RESOLVED constraint above.
- A real, consent-live Codex pilot execution to obtain end-to-end cross-provider
  evidence — `CODEX_REPLAY_PARITY_LIVE_CONSENT` must not be set as part of this batch's
  work; parity stays structural/test-based only, matching Phase 0's own bar.
- Any external vector/graph database, hosted RAG, or non-SQLite/non-JSONL storage.
- Open Decisions 5 (promotion sample-size/thresholds) and 6 (MCP tool vs.
  adapter-library exposure) — both still explicitly deferred; do not force-resolve
  either just because this phase touches adjacent monitoring code.
- A new dashboard frontend/UI surface from scratch — extend the existing
  `generate_retro.py`/`query.py`/dashboard query layer only; any new frontend rendering
  is out of scope for this phase's proof.

If investigation reveals Phase 4 cannot be meaningfully scoped without first resolving
something Phase 0-3 should have settled but didn't (beyond the `execution_id`/`provider`
gap already resolved above), say so plainly as a risk/open-question in the ticket rather
than silently guessing or re-litigating an already-closed decision.
