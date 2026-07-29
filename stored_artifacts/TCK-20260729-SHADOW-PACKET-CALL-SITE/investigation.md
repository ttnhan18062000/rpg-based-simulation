---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-SHADOW-PACKET-CALL-SITE
artifact_type: investigation
tags: [workflows, agent-monitoring, observability]
---

# Investigation — TCK-20260729-SHADOW-PACKET-CALL-SITE

## Current Behavior

### `.claude/workflows/implement-ticket.js` — Investigate phase (current, unmodified)

- `phase('Investigate')` at `.claude/workflows/implement-ticket.js:441`.
- `investigationTs = await captureTs()` (line 443), then `await writeSidecar(events.length + 1 +
  seqOffset, 'Investigate', 'investigator')` (line 444), then, on the **very next line with no
  interleaving statement**, `investigation = await agent(...)` (line 445-475, `{ label:
  'investigate', agentType: 'investigator' }`).
- `investigationText = investigation.toString().trim()` (line 477) then `pushEvent('Investigate',
  'investigator', 'ok', investigationText.slice(0, 200), investigationTs)` (line 478).
- `pushEvent` (defined line 224-235) assigns `seq: events.length + 1 + seqOffset` **at push time**
  — i.e. the real Investigate event's seq is fixed only once `events.push(...)` actually runs at
  line 478, using whatever `events.length` is *at that point* (after any other event has already
  been pushed earlier in the run, but before Investigate's own event exists yet).
- No env-var-gated call, no `timeout`, and no reference to `context_packet_assembler.py` or
  `retrieval_events.py` exists anywhere in `.claude/workflows/*.js` today (confirmed by grep — zero
  hits for `context_packet_assembler|retrieval_events|SHADOW_CONTEXT_PACKET` in `.claude/`).

### Orchestrator-only `bash()` call precedent this ticket must mirror

Three existing call sites establish the exact convention (individually-quoted argv elements,
never JSON-embedded in the `-c` string; a `MARKER:`/`TAG_CHECK_JSON:`/`ARCH_CHECK_JSON:`-prefixed
JSON string; `indexOf` + `try/catch JSON.parse`):

- `tagCheckOutput` — `.claude/workflows/implement-ticket.js:353-360`, inside Scope, after
  `ticketInfo` resolves.
- `docStalenessOutput` — `.claude/workflows/implement-ticket.js:677-679`, inside Implement, after
  `implementation.files_changed` resolves. Calls `tools/gate_checks/doc_staleness_check.py` as a
  plain CLI (`python3 tools/gate_checks/doc_staleness_check.py <bool> <path> <path> ...`), not a
  `python3 -c` inline script — the simplest of the three shapes.
- `archCheckOutput` — `.claude/workflows/implement-ticket.js:722-729`, inside Architecture-Verify,
  same `python3 -c "..." ${filesChangedArgs}` inline-import shape as `tagCheckOutput`.

None of these three write directly to `agent-monitoring/events.jsonl` themselves — they return a
JSON blob that the orchestrator JS parses and folds into an *existing* `pushEvent(...)` call's
status/evidence. This ticket's shadow-packet call is different in kind: `emit_retrieval_event()`
(inside `wrap_context_packet_assembly()`) performs its own direct file write via
`writer.write_lines()`, bypassing `pushEvent`/`events` array/`writeMonitoring` entirely. There is
no existing precedent in this file for an orchestrator-only `bash()` call that durably writes a
JSONL row itself rather than returning data for the JS side to act on — this is new load-bearing
territory, not a pure copy of the 3-call convention.

### `tools/context_packet_assembler.py::assemble_context_packet()` (`tools/context_packet_assembler.py:266-291`)

Keyword-only signature: `assemble_context_packet(*, packet_id, corpus_generation,
retrieval_version, budget_requested, included_candidates: list[Candidate], excluded:
list[tuple[Candidate, str]] = ())`. `included_candidates` must be real `Candidate` dataclass
instances (from `unrated_candidate()`, `candidate_from_code_index_record()`,
`candidate_from_hybrid_result()`, or `candidate_from_parity_ledger_fixture()`), not plain dicts —
so a `python3 -c` invocation must import and construct these, it cannot pass a bare JSON list
through and expect the function to coerce it. An empty `included_candidates=[]` list is valid and
produces `budget_returned=0`, `included=[]`.

### `tools/retrieval_events.py::wrap_context_packet_assembly()` (`tools/retrieval_events.py:264-308`)

`wrap_context_packet_assembly(*, seq, summary, run_id=RUN_ID_PACKET, status='ok',
events_file=None, **assemble_kwargs)`. `run_id` defaults to the synthetic literal
`"RETRIEVAL-EVENT-context-packet"` (`RUN_ID_PACKET`, line 260) — the ticket's scope requires
overriding this default with the real ticket's `tid`. `phase="Retrieval"` and
`agent=AGENT_PACKET` (`"context-packet-wrapper"`) are hardcoded inside the function body (lines
295-296) and the ticket's Out of Scope explicitly forbids touching them. `events_file=None`
resolves to `record_events.EVENTS_FILE` (`agent-monitoring/events.jsonl`) inside
`emit_retrieval_event()` (`tools/retrieval_events.py:133`) — the real, shared monitoring file, not
a synthetic sandbox.

### `tools/agent_replay_codex/consent_gate.py` (whole file, 31 lines)

`require_live_consent(env=None)` raises `ConsentNotGrantedError` unless
`env.get("CODEX_REPLAY_PARITY_LIVE_CONSENT") == "1"` **exactly** — no truthy coercion (`'true'`,
`'yes'`, unset, empty all refuse). This is a **Python-level, in-process** gate called from inside
Python code before a `subprocess` object is created. It has zero direct applicability to an
**orchestrator-side shell `bash()` call** — there is no Python entry point here to guard, only a
shell command string. The pattern to adapt is the *strict-equality-to-`"1"`* semantics, translated
into a shell `if [ "$SHADOW_CONTEXT_PACKET_ENABLED" = "1" ]; then ...; fi` (or equivalent) guard
wrapping the `bash()` command string itself — not a Python import of `consent_gate.py`.

### `.claude/workflows/*.js` never reads `process.env` today

`grep -n "process.env" .claude/workflows/*.js` returns zero hits. Every existing conditional
behavior in this file (tier, ticket_id, etc.) comes from the `args` object the workflow harness
passes in, not from OS environment variables. `SHADOW_CONTEXT_PACKET_ENABLED` must therefore be
read **inside the bash shell command string** (`$SHADOW_CONTEXT_PACKET_ENABLED` at shell level),
not via any `process.env` reference in the surrounding JS — there is no existing JS-side env-var
read to mirror, and introducing one would be new, unproven territory this ticket should avoid.

### No `timeout` primitive exists anywhere in this codebase today

`grep -rn "timeout" .claude/workflows/*.js tools/*.py` (excluding test files) returns no shell
`timeout <N>s` usage anywhere — `tools/perf_guard.py:165` uses pytest's `-p no:timeout` plugin
disable flag, an unrelated concept. This ticket introduces the **first** use of coreutils
`timeout` in this repo's orchestration layer, exactly as the ticket's Scope states ("the only
fail-open primitive available since no existing timeout primitive exists elsewhere").

### `vocabulary.py` / `record_events.py` — confirmed no modification needed

- `emit_retrieval_event()` (`tools/retrieval_events.py:91-135`) calls **only**
  `record_events.validate_record()` (the 7-field REQUIRED/status check) — it never calls
  `record_events.warn_vocabulary_drift()`. Confirmed structurally (`record_events.py:71-83` shows
  `warn_vocabulary_drift` is only invoked from `record_events.py`'s own `main()`, which
  `emit_retrieval_event()` never calls) and behaviorally (`tests/tools/test_retrieval_events.py`'s
  `test_new_run_id_prefix_produces_no_vocabulary_warning` asserts `capsys.readouterr().err == ""`
  for a call using the synthetic `RUN_ID_HYBRID` prefix).
- **However**, once this ticket passes the *real* `tid` (a `"TCK-..."`-prefixed run_id) into
  `wrap_context_packet_assembly()`, `vocabulary.infer_workflow(tid)` resolves to
  `"implement-ticket"` (a *known* workflow) for the first time for one of these wrapper-emitted
  events — previously every wrapper call used a synthetic `RETRIEVAL-EVENT-*` prefix that
  `infer_workflow()` deliberately returns `None` for. This does not break `emit_retrieval_event()`
  itself (it still only calls `validate_record()`), but it does mean the **separate**, read-only
  `tools/agent-monitoring/validate.py::compute_drift_report()` function (imported by
  `generate_retro.py`/weekly retros) will, for the first time, see a real
  `("implement-ticket", "Retrieval")` phase pair and a real `("implement-ticket",
  "context-packet-wrapper")` agent pair — **neither is in `vocabulary.py`'s
  `WORKFLOW_PHASES["implement-ticket"]` or `WORKFLOW_AGENTS["implement-ticket"]` sets** — and will
  count them under "Non-canonical phase/agent values" in every future drift report once
  `SHADOW_CONTEXT_PACKET_ENABLED=1` runs occur. `compute_drift_report()`'s own docstring confirms
  this is non-gating, warn-only reporting (`"Never gates anything"`), so no test/CI breaks — but a
  future reader of a drift report will see a recurring, unexplained-looking `'Retrieval': N` /
  `'context-packet-wrapper': N` line unless this is documented as **expected**, not a bug to chase.
  See Risks and Open Questions below.

### `.claude/current_run` sidecar attribution (tools.jsonl inflation precedent)

`tools/agent-monitoring/post_tool_hook.py` fires for **every** tool call (not just agent-internal
ones) and reads `.claude/current_run` to attribute the call's `(run_id, seq, phase, agent)`. Any
new orchestrator-only `bash()` call placed inside the Investigate phase, while the sidecar still
holds `('Investigate', 'investigator')` (written by `writeSidecar` at line 444, and not
overwritten until the *next* `writeSidecar` call for Plan), will have its own tool-call row
attributed to Investigate's `(run_id, seq)` — inflating Investigate's `tool_call_count`/
`cost_proxy_score` slightly. This is **not a new failure mode this ticket introduces** — the exact
same thing already happens for `tagCheckOutput` (Scope), `docStalenessOutput` (Implement), and
`archCheckOutput` (Architecture-Verify), all of which run while their phase's sidecar value is
still active. It is a known, accepted, pre-existing characteristic of the orchestrator-bash()
convention (root-caused and partially fixed by `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`
for the *writeMonitoring*-internal case specifically, not for this class of mid-phase check calls),
not a regression to fix here.

### Hard placement constraint — `writeSidecar`→`agent()` adjacency guard

`tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`
asserts the **exact literal string** `"  await writeSidecar(events.length + 1 + seqOffset,
'Investigate', 'investigator')\n  investigation = await agent("` appears verbatim in
`implement-ticket.js` (one of 10 such adjacency strings, one per phase). The new shadow-packet
`bash()` call **must not** be inserted between `writeSidecar(...)` and `investigation = await
agent(...)` — doing so breaks this regression test immediately. The only safe placement inside the
Investigate phase block is **before** `captureTs()`/`writeSidecar()` (unlikely — nothing to record
yet) or **after** `investigation = await agent(...)` resolves (natural — mirrors
`docStalenessOutput`'s post-agent-call placement inside Implement). Placing it **after**
`pushEvent('Investigate', ...)` (line 478) additionally means `events.length` has already
incremented by the time a `seq` value is computed for the shadow call, giving it a **distinct**
next `seq` slot rather than colliding with Investigate's own real event's `seq` (both would
otherwise independently evaluate `events.length + 1 + seqOffset` to the *same* number, since nothing
else pushes to `events` in between) — see Risks and Open Questions.

## Mechanics / Engine Constraints

This ticket touches only agent-orchestration/observability tooling (`.claude/workflows/*.js`,
`tools/agent-monitoring/*.py`, `tools/context_packet_assembler.py`,
`tools/retrieval_events.py`) — none of `docs/mechanics/`'s six chapters or `docs/engine/`'s
kernel/authoritative-pipeline contracts govern simulation state, formulas, or the 32-phase
mutation pipeline that this change would need to respect. No engine contract is implicated.

The one relevant engine-contract-shaped document is
`docs/engine/contracts/context_packet_contract.md` — it explicitly states (§4, "Verification
Path"): *"No code enforces this contract yet... A future Phase 3 ticket that implements
`ContextPacket` construction/serialization must add its own `tests/`-path verification for that
code. That future ticket will not need a `docs/parity_ledger/` entry: this contract governs
agent-orchestration/retrieval tooling, not simulation logic..."* — Phase 3
(`TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) already satisfied that verification obligation; this
ticket only adds a *caller* of the already-verified `assemble_context_packet()`/
`wrap_context_packet_assembly()` functions, so no new parity-ledger-relevant engine-contract claim
is introduced.

## Parity Ledger Overlap

**None.** This is a pure agent-orchestration/observability change with no simulation-logic
behavior change. Confirmed by direct precedent: `docs/engine/contracts/context_packet_contract.md`
§4 explicitly states the packet-assembly contract itself needs no parity ledger entry, citing the
same posture already recorded for agent-monitoring tooling under
`docs/parity_ledger/infrastructure.yaml`'s INFRA-281 through INFRA-292 entries (`support_boundary`
field) — i.e., agent-orchestration/retrieval tooling is explicitly out of parity-ledger scope by
established convention, not merely absent by omission. Grepping
`docs/parity_ledger/*.yaml` for `context_packet|retrieval_event|shadow_packet|implement-ticket`
returns no hits. No P0 parity entry is implicated, so no `test_path` obligation arises from this
ticket.

## Prior Work

- **`TCK-20260729-CONTEXT-PACKET-ASSEMBLY`** (done; `stored_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/`)
  — built `tools/context_packet_assembler.py` itself. Explicitly scoped as "never imported by or
  referenced from any `.claude/workflows/*.js` file" (module docstring, line 11) — this ticket is
  the **first** to cross that boundary, and does so only via a `python3 -c`/CLI-style shell
  invocation, never a direct JS import (there is no JS import mechanism for Python modules here
  anyway).
- **`TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT`** (done; `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/`)
  — built `tools/retrieval_events.py`, `emit_retrieval_event()`, and the 3 `wrap_*()` wrappers,
  including `wrap_context_packet_assembly()` this ticket calls. Its plan.md's Resolved Decision 1
  establishes the `RETRIEVAL-EVENT-<slug>` synthetic run_id convention this ticket **deliberately
  diverges from** (per the ticket's own Request Summary: reuse the real ticket's `run_id` instead
  of adding a new field) — this is documented, sanctioned divergence, not an oversight.
- **`TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK`** (done) — built
  `tools/retrieval_event_parity_check.py::assert_no_provider_specific_fields()`, a structural (not
  live) guard that `RETRIEVAL_EVENT_FIELDS` never grows a provider-specific field. This ticket adds
  no new field to `RETRIEVAL_EVENT_FIELDS`, so `test_retrieval_event_parity_check.py` and this
  guard are unaffected by construction — one of this ticket's own Acceptance Criteria explicitly
  requires this test to "pass unmodified."
- **`TCK-20260729-RETRIEVAL-RETRO-VIEWS`** (done) — wired retrieval-event dashboard/retro queries
  into `generate_retro.py`. Once this ticket's shadow calls start emitting real-`run_id`-attributed
  `Retrieval`-phase events, those events become visible in this ticket's retro/dashboard views for
  the first time under a *real* ticket's run_id, mixed alongside the `RETRIEVAL-EVENT-<slug>`
  standalone rows already covered.
- **`docs/ai/default_packet_scenarios_decision.md`** (Open Decision 1 resolution) — establishes
  that "Ticket implementation" (the standard `implement-ticket.js` pipeline) is a scenario that
  justifies a default packet at a **Medium** directional tier — directly relevant context for
  whatever `budget_requested` value the Plan phase chooses for the smoke-test candidate set,
  though this ticket's own Out of Scope forbids wiring a real retrieval pipeline, so the actual
  candidate set stays minimal/empty regardless of the tier language.
- **Orchestrator-only bash() precedent tickets**: `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK` (tag
  check), `TCK-20260711-DOC-STALENESS-GATE-CHECK` + `TCK-20260720-GATE-CHECK-WIRING-DECISIONS`
  (doc-staleness wiring), and the Architecture-Verify static-check wiring establish the exact
  "orchestrator-run, not agent-self-reported... individually-quoted argv elements... MARKER-prefixed
  JSON... try/catch parse" convention this ticket's call site must visually match, even though (as
  noted above) this ticket's call differs in kind by writing a durable JSONL row itself rather than
  only returning data for the JS side to fold into an existing `pushEvent`.
- **`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`** — root-caused and partially fixed the
  "orchestrator's own Bash/python invocations get attributed to whatever `(run_id, seq)` sidecar
  value is still active" class of issue for `writeMonitoring`'s own internal calls specifically.
  Directly relevant background for reasoning about where in the Investigate phase to place this
  ticket's new bash() call (see Current Behavior's sidecar-attribution note above) — not something
  this ticket needs to re-fix, but essential context for not reintroducing the same class of bug
  by accident.

## Risks and Open Questions

1. **Placement inside Investigate phase (blocking a specific implementation choice, not blocking
   scope)** — the shadow-packet `bash()` call must go strictly *after*
   `investigation = await agent(...)` resolves (cannot sit between `writeSidecar` and `agent()` per
   the hard adjacency-guard test above). Placing it after `pushEvent('Investigate', ...)` (rather
   than between the agent-call and the pushEvent) avoids both a `seq` collision with Investigate's
   own real event and any illusion that the shadow-packet outcome could influence
   `pushEvent`'s status/summary — reinforcing "strictly advisory." This is a concrete recommendation
   for the Plan phase, not an assumption baked into scope.
2. **`seq` collision if placed carelessly — ORIGINAL RECOMMENDATION WAS WRONG, superseded below.**
   `pushEvent`'s `seq` for Investigate's real event is only fixed at `events.push(...)` time
   (`events.length + 1 + seqOffset` evaluated at `.claude/workflows/implement-ticket.js:224-235`'s
   push). The **original** version of this finding recommended "sequencing the call after
   `pushEvent('Investigate', ...)` has already run" to avoid a collision. **A subsequent
   architecture-review gate (NEEDS_CHANGES) found this recommendation insufficient**: the shadow
   write goes directly to `events.jsonl` via `emit_retrieval_event()`
   (`tools/retrieval_events.py:91-135`, `write_lines()` call at line 132), entirely bypassing the
   JS `events` array — `events.length` never advances because of the shadow call, regardless of
   where in the phase it is placed. Concretely: let `L` = `events.length` immediately after
   Investigate's own `pushEvent` has run (`implement-ticket.js:478`). If the shadow call computes
   `seq` via the identical expression `events.length + 1 + seqOffset` *at any point after that*,
   it evaluates to `L + 1 + seqOffset`. Plan's `writeSidecar(events.length + 1 + seqOffset, 'Plan',
   'planner')` (`implement-ticket.js:485`) runs next and evaluates the **same** expression against
   the **same**, still-unchanged `events.length` (`L`, since nothing pushed to the JS array in
   between) — producing the identical value `L + 1 + seqOffset`. So the shadow event and Plan's
   real event collide on `(run_id, seq)` **regardless of whether the shadow call is placed before
   or after Investigate's own `pushEvent`** — placement alone cannot fix this; the shadow event
   needs a seq value from an entirely different, disjoint numbering scheme. See the new
   "Resolved: Disjoint Shadow-Event Seq Scheme" subsection below for the confirmed fix.
3. **`docs/agent-monitoring/schema.md`'s provenance section is currently a false statement once
   this ticket ships** — `docs/agent-monitoring/schema.md:273-291` (the "Provenance... for
   standalone invocations" note) currently states flatly: *"retrieval events are emitted from
   test/manual invocations of the Phase 3 retrieval modules... **none of which are wired into any
   `.claude/workflows/*.js` file** — there is no tracked implement-ticket/... run to attach to."*
   This ticket makes that statement inaccurate for the `context_packet_assembler.py` wrapper
   specifically (it *does* now get wired into `implement-ticket.js`'s Investigate phase, gated by
   `SHADOW_CONTEXT_PACKET_ENABLED`). This document is the natural, load-bearing candidate for the
   ticket's required "docs/ path update in files_changed" — more directly load-bearing than
   `docs/ai/default_packet_scenarios_decision.md` or a new `docs/engine/contracts/` note (the
   ticket's own Assumptions/Open Questions leaves the exact file as a Plan-phase decision; this
   finding is strong evidence for `docs/agent-monitoring/schema.md` specifically, since leaving it
   unedited means shipping a doc that is now factually wrong about this one wrapper).
4. **Vocabulary-drift report side effect (non-blocking, but should be documented so it isn't
   mistaken for a bug)** — once real-`tid`-attributed shadow events start landing in
   `events.jsonl`, `tools/agent-monitoring/validate.py::compute_drift_report()` and
   `generate_retro.py`'s equivalent will begin showing `'Retrieval': N` /
   `'context-packet-wrapper': N` lines under "Non-canonical phase/agent values" for the
   `implement-ticket` workflow, indefinitely, by design (per the ticket's explicit Out of Scope:
   `phase="Retrieval"` and the wrapper's agent names must not change, and must not be added to
   `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`, since that would misrepresent them as
   real workflow phases). This is warn-only, never gating (`compute_drift_report`'s own docstring:
   "Never gates anything"), but a future weekly-retro reviewer unfamiliar with this ticket could
   mistake the recurring drift line for an actual vocabulary regression. Recommend the Plan phase
   have the implementer add one sentence to `docs/agent-monitoring/schema.md`'s existing
   Provenance note (the same doc edit satisfying #3) stating this is expected once
   `SHADOW_CONTEXT_PACKET_ENABLED=1` is used, not a bug.
5. **Candidate-set construction detail, not yet resolved** — `assemble_context_packet()` requires
   real `Candidate` dataclass instances for `included_candidates`, not plain dicts/JSON. The
   ticket's Scope says "minimal smoke-test candidate set (derived from the ticket's own
   title/summary, or empty)". An **empty** `included_candidates=[]` is the simplest, lowest-risk
   choice (`assemble_context_packet` handles it cleanly — `included=[]`, `budget_returned=0`) and
   avoids needing to construct `unrated_candidate(...)` calls inline inside a `python3 -c` string
   for ticket-title/summary text (which would need careful shell-quoting of arbitrary ticket prose
   — a real injection-adjacent risk if not done via individually-quoted argv elements, consistent
   with this file's own established convention). This is left as a genuine open implementation
   choice for the Plan phase — not decided here, per the Uncertainty Rule ("vague leads stay vague
   until evidence narrows them").
6. **Env-var gate mechanics** — `SHADOW_CONTEXT_PACKET_ENABLED` must be read shell-side
   (`$SHADOW_CONTEXT_PACKET_ENABLED` inside the `bash()` command string), since no
   `.claude/workflows/*.js` file reads `process.env` anywhere today and this ticket should not be
   the one to introduce that as a new JS-side pattern when a pure-shell guard achieves the same
   opt-in behavior with less surface area change.
7. **Timeout duration `N`** — genuinely unresolved per the ticket's own Assumptions section; no
   existing `timeout <N>s` precedent value exists anywhere in this repo to copy. Left to Plan.

### Resolved: Disjoint Shadow-Event Seq Scheme (post-review correction)

**Every real per-phase `seq` value for a run is provably `>= 1`.** Both `seq`-producing
expressions in `implement-ticket.js` — `pushEvent`'s `events.length + 1 + seqOffset`
(`implement-ticket.js:226`) and every `writeSidecar(events.length + 1 + seqOffset, ...)` call
(`implement-ticket.js:444, 485, 566, 635, 751, 812, 961, 1053, 1116, 1170`) — are algebraically
bounded below by 1, because `events.length >= 0` (a JS array length) and `seqOffset >= 0`
(`resolveSeqOffset()` at `implement-ticket.js:49-61` calls
`tools/agent-monitoring/seq_offset.py::compute_seq_offset()`, which starts `max_seq = 0` and only
ever raises it — `seq_offset.py:29-37` — so it can never return negative, confirmed by
`tests/tools/test_seq_offset.py::test_compute_seq_offset_returns_zero_for_run_id_with_no_prior_history`).
Therefore **any `seq <= 0` is mathematically guaranteed disjoint from the real per-phase range for
the entire run**, independent of run length, resume count, or `seqOffset` magnitude — this is a
provable property, not a practically-bounded heuristic (a large-constant scheme, e.g. `1_000_000 +
counter`, would only be disjoint in practice, contingent on no run ever accumulating that many real
phases/resumes; the negative scheme needs no such assumption).

**Recommended concrete scheme:** pass a **negative literal** as the shadow call's `seq` argument to
`wrap_context_packet_assembly(seq=..., ...)`, computed independently of `events.length`/`seqOffset`
entirely — no expression shared with `pushEvent`/`writeSidecar` at all. Two viable variants, in
order of robustness:

- **Fixed sentinel `seq=-1`.** Sufficient if the shadow call site can only ever fire once per
  `run_id` (true for a single, uninterrupted run, since the ticket's Out of Scope restricts the
  call site to exactly one place — Investigate only, no duplication into other phases).
- **Monotonic negative counter (recommended over the fixed sentinel)** —
  `seq = -(1 + prior_shadow_count_for_this_run_id)`, where `prior_shadow_count_for_this_run_id` is
  a small read-only scan of `agent-monitoring/events.jsonl` counting existing records matching
  this `run_id` with `agent == "context-packet-wrapper"` (`AGENT_PACKET`,
  `tools/retrieval_events.py:260`). **This robustness matters concretely, not just
  theoretically**: Investigate *can* re-execute for the same `run_id` — this very ticket
  (`TCK-20260729-SHADOW-PACKET-CALL-SITE`) is itself mid-resume after a NEEDS_CHANGES
  architecture-review gate failure sent it back through Investigate again. A fixed `-1` sentinel
  would make a second shadow-call execution collide with the *first* shadow event (both `-1`) —
  harmless to the real per-phase invariant (still `<= 0`, still disjoint from real seqs), but it
  would silently lose the first shadow event's own identity in any `(run_id, seq)`-keyed
  last-write-wins structure, the same class of bug this ticket is fixing, just confined to the
  shadow-event sub-population instead of colliding with a real one. The counter variant costs one
  extra read of `events.jsonl` (mirroring `seq_offset.py::compute_seq_offset()`'s own resume-lookup
  precedent, just filtered to shadow rows and negated) and eliminates this residual gap.
  Implementation detail (construction of this counter, e.g. a new tiny pure function vs. an inline
  scan in the `python3 -c` shadow-call script) is left to the Plan phase — both keep
  `tools/retrieval_events.py` itself workflow-unaware (satisfying
  `test_retrieval_event_wrapper_single_source.py`) since the counting logic lives in the caller
  (`implement-ticket.js`'s shell invocation or a helper it calls), not inside `retrieval_events.py`.

**Zero changes required to `pushEvent`/`writeSidecar`, and no mutation of the JS `events` array** —
both hard constraints from this re-investigation's task are satisfied: the shadow call computes its
own `seq` value completely independently, never touching `events.length` or `seqOffset`.

**Confirmed: no consumer breaks on a negative or otherwise non-1-based `seq` value:**

- `tools/agent-monitoring/record_events.py::validate_record()` (`record_events.py:22-32`) checks
  only that required fields (including `seq`) are present and non-`None`, and that `status` is one
  of the 4 valid values — there is no type, sign, or range constraint on `seq` anywhere in this
  function.
- `tools/agent-monitoring/seq_offset.py::compute_seq_offset()` (`seq_offset.py:29-37`) only takes a
  `max()` over `seq` values — a negative shadow-event `seq` is simply always less than the running
  `max_seq` (which starts at 0), so it can never become the offset for a future resumed session;
  it is silently ignored by this computation, exactly as intended.
- `tools/agent-monitoring/weight_sensitivity_check.py::_load_tool_rows_and_events()`
  (`weight_sensitivity_check.py:117-141`) builds `tool_rows_by_group` keyed by `(run_id, seq)` from
  `tools.jsonl` (whose `seq` values come only from real `writeSidecar`-driven `.claude/current_run`
  sidecar writes — always positive) and separately builds `phase_of`/`agent_of` dicts keyed by
  `(run_id, seq)` from **all** of `events.jsonl`, including the shadow row. In
  `compute_weight_sensitivity_report()` (`weight_sensitivity_check.py:100-135`), the loop is `for
  key, rows in tool_rows_by_group.items(): if key not in phase_of: continue` — it only ever looks
  up keys that originated from `tool_rows_by_group` (always positive-seq keys). The shadow event's
  `(run_id, negative_seq)` entry in `phase_of`/`agent_of` is simply never queried — it sits inertly
  in the dict, exactly the harmless outcome CLAUDE.md's "monitoring write failure must never fail
  the workflow" spirit calls for here (no crash, no wrong grouping, no silently-dropped real data).
- `tools/agent-monitoring/build_index.py:74, 89` declare `seq INTEGER` (no `CHECK`/`UNIQUE`
  constraint — SQLite accepts negative integers in an `INTEGER` column without complaint) and
  `idx_events_run_id_seq`/`idx_tools_run_id_seq` (`build_index.py:82, 96`) are plain non-unique
  indexes, not `UNIQUE` constraints — `docs/agent-monitoring/schema.md`'s own text confirms this
  design choice explicitly ("`events`/`tools` tables use non-unique `(run_id, seq)` indexes, not a
  `UNIQUE` constraint — historical pause/resume seq-collision duplicates... exist in the live
  corpus and would crash a naive unique-key rebuild"), i.e. the index layer was already built
  expecting non-unique/anomalous `seq` values to exist, and does not reject them.
- **Minor, non-blocking cosmetic caveat**: `docs/agent-monitoring/schema.md:137`'s field-table row
  for `seq` currently reads "1-based call order within the run. Monotonically increasing." — a
  negative shadow-event `seq` technically violates this sentence's literal wording (though it
  never violates any consumer's actual behavior, per the four bullets above). Any future code that
  naively `sorted(events, key=lambda e: e['seq'])` for chronological display (an illustrative
  pattern shown in `docs/agent-monitoring/schema.md`'s own example around line 393, not live
  production code today) would place the negative-seq shadow row *first*, before Scope's `seq=1`
  event — chronologically wrong (the shadow call actually fires during/after Investigate), but
  purely a display-ordering quirk for an advisory/never-gating event, not a correctness bug. This
  doc row needs a one-sentence carve-out alongside the Provenance-paragraph edit already identified
  in Risk #3 above (`docs/agent-monitoring/schema.md:273-291`) — both edits belong in the same
  `docs/` file this ticket already needs to touch for the doc-staleness gate.

None of these open questions block understanding scope — they are concrete implementation choices
correctly deferred to the Plan phase, not unresolved ambiguities about *what* this ticket must do.

## Anti-Drift Hazards

- **Do not** insert the new `bash()` call between `writeSidecar(events.length + 1 + seqOffset,
  'Investigate', 'investigator')` and `investigation = await agent(...)` — this breaks
  `tests/tools/test_current_run_sidecar_orchestrator.py::test_sidecar_bash_write_precedes_each_covered_agent_call`'s
  exact-adjacency string match immediately.
- **Do not** modify `wrap_context_packet_assembly()`'s hardcoded `phase="Retrieval"` or
  `agent=AGENT_PACKET` — both the ticket's Out of Scope and
  `tests/tools/test_retrieval_events.py::TestWrapContextPacketAssembly` assert these literals
  directly; changing them breaks an existing, unrelated-to-this-ticket test.
- **Do not** add a `shadow_mode` (or equivalent) field to `RETRIEVAL_EVENT_FIELDS` —
  `tests/tools/test_retrieval_event_parity_check.py` and the ticket's own Acceptance Criteria both
  require `RETRIEVAL_EVENT_FIELDS` to stay exactly as-is; the real-`run_id` reuse *is* the
  provenance signal, by design.
- **Do not** touch `tools/retrieval_events.py` itself to add any workflow-awareness —
  `tests/tools/test_retrieval_event_wrapper_single_source.py::test_module_never_references_workflow_files_or_pipeline_entry_points`
  asserts the module's source never contains `".claude/workflows"`, `"implement-ticket.js"`,
  `"pushEvent"`, or `"writeSidecar"`. All wiring must live in `implement-ticket.js`, calling
  `retrieval_events.py`'s already-published functions from the outside — never the reverse.
- **Do not** let a packet-build failure/timeout change `pushEvent('Investigate', ...)`'s
  status/summary or the workflow's return value — the shadow call's own exit code/output must be
  fully discarded (`... 2>/dev/null || true`, matching the established fail-open suffix convention
  already used by `writeSidecar`), not merely logged.
- **Do not** let any packet content (a real `ContextPacket`'s `included[]`/`excluded_summary[]`, or
  any candidate text) reach an `agent()`-prompt template string anywhere in this file — this is a
  distinct, separately-verified Acceptance Criterion (grep-based), independent from the "does not
  block/gate" criterion.
- **Do not** wire `tools/hybrid_retrieval.py` into this call site — the ticket's Out of Scope is
  explicit that real-candidate wiring is a deferred follow-up; the candidate set here must stay
  hand-built/minimal or empty.
- **Do not** add this call site to any phase other than Investigate — in particular, do not
  duplicate it into Plan "for consistency"; that is explicitly Out of Scope.
- **Do not** compute the shadow call's `seq` argument using `events.length + 1 + seqOffset` (or
  any expression that reads the JS `events` array/`seqOffset`) — this is the exact bug an
  architecture-review gate previously caught (see Risk #2 and "Resolved: Disjoint Shadow-Event Seq
  Scheme" above): that expression always aliases onto whatever the *next real phase's* `pushEvent`/
  `writeSidecar` will independently compute, because the shadow write never advances
  `events.length`. Use a negative literal (or a negative monotonic counter derived from a read of
  `agent-monitoring/events.jsonl`, never from the JS array) instead.
