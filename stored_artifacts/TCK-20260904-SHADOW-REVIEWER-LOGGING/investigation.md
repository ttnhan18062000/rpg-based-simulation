---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-SHADOW-REVIEWER-LOGGING
artifact_type: investigation
tags: [ai, agent-monitoring, security]
---

# Investigation — TCK-20260904-SHADOW-REVIEWER-LOGGING

## Current Behavior

### Architecture-Verify call site (`.claude/workflows/implement-ticket.js:951-1030`)
Post-Implement static backstop, skipped for `hotfix`. Sequence at lines 958-1029:
1. `bash()` runs `tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks()` over
   `implementation.files_changed`, parsed via an `ARCH_CHECK_JSON:` marker (:962-976).
2. `archVerifyTs = await captureTs()` (:990).
3. `await writeSidecar(events.length + 1 + seqOffset, 'Architecture-Verify', 'architecture-reviewer')`
   (:991) — writes `.claude/current_run` (+ session-scoped copy) so the *next* tool calls get
   attributed to this `(run_id, seq)`.
4. `const archVerify = await agent(prompt, { label: 'architecture-verify', schema: ARCH_VERIFY_SCHEMA,
   agentType: 'architecture-reviewer' })` (:992-1009) — **no `model:` key in the options object**.
5. On `verdict !== 'APPROVED'`: `pushEvent('Architecture-Verify', ..., 'failed', ...)`,
   `writeMonitoring(archVerify.verdict)`, and an early `return { status: archVerify.verdict, ... }`
   (:1011-1024) — this is the exact place a candidate-only failure must never reach.
6. On APPROVED: `pushEvent('Architecture-Verify', 'architecture-reviewer', 'ok', ...)` (:1026).

### Security-Review call site (`.claude/workflows/implement-ticket.js:1341-1395`)
Conditional — fires only when `ticketInfo.tags.includes('security')` or
`ticketInfo.suggested_skills.includes('/security-review')` (:1347-1348), reading raw ticket
frontmatter as ground truth (not the derived-only `suggested_skills` field alone — this hardening
is itself a prior architecture-review finding, see the comment at :1342-1345). Structurally
identical two-line pattern: `writeSidecar(events.length + 1 + seqOffset, 'Security-Review',
'security-reviewer')` (:1363) immediately followed by `const securityReview = await agent(prompt, {
schema: SECURITY_REVIEW_SCHEMA, agentType: 'security-reviewer' })` (:1364-1376) — again no `model:`
key. Same early-return-on-non-APPROVED shape at :1378-1391.

Both `agent()` calls use the default `agentType` resolution (`.claude/agents/architecture-reviewer.md`,
`.claude/agents/security-reviewer.md`), and **0/16 `.claude/agents/*.md` files declare a `model:`
frontmatter key** — confirmed by direct grep of every file's frontmatter block in this investigation
(none has a `model:` line). No existing `agent()` call anywhere in `.claude/workflows/*.js`
(`implement-ticket.js`, `implement-epic.js`, `create-tickets.js`, `simq-audit.js`) passes a `model:`
key in its options object today — this ticket would be the first.

### `model:` override resolution (verified, not guessed)
The ticket's own note already resolved this from the `workflow-authoring` skill's documented script
API: `agent(prompt, opts)` supports `opts.model?: string` — "opts.model overrides the model for this
agent call. Default to omitting it... the agent inherits the main-loop model... Only set it when
you're highly confident a different tier fits the task." I re-verified this against the real code
rather than trusting the skill doc in isolation:
- `.claude/workflows/implement-ticket.js` opens with `export const meta = { name: 'implement-ticket',
  ..., phases: [...] }` (line 1) and its body uses exactly the hook set the `workflow-authoring`
  skill documents for a real `Workflow`-tool script: `agent(prompt, opts)`, `bash()`, `phase()`,
  `log()`, `args`. This is direct, mechanical evidence that `implement-ticket.js` **is** executed as
  a `Workflow`-tool script, not merely JS that happens to share syntax with one — so the skill's
  `agent()` API reference applies to these exact call sites verbatim.
- No contradicting evidence found: no other ticket/doc in this repo claims `model:` must instead be
  set via per-agent-file frontmatter, and the `Related Docs`/registry search surfaced nothing to the
  contrary. `docs/parity_ledger/infrastructure.yaml`'s Wave 2 note (id starting `Wave 1 agent-tools
  frontmatter rollout`, TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE) explicitly defers
  `architecture-reviewer`/`security-reviewer`/`planner`'s own `tools:` frontmatter rollout to a future
  "Wave 2" — a different frontmatter key (`tools:`, not `model:`) but confirms these two agent files
  are deliberately *not* yet being edited for infrastructure reasons unrelated to this ticket; nothing
  there implies `model:` frontmatter is the intended mechanism.
- **Resolution: `opts.model` on the specific `agent()` call is the correct, verified mechanism.** The
  candidate call is a second, distinct `agent(sameOrAdaptedPrompt, { ...opts, model: CANDIDATE_MODEL,
  agentType: 'architecture-reviewer' })` invocation alongside the existing production call, not a
  frontmatter edit to `architecture-reviewer.md`/`security-reviewer.md` (which would change the
  *production* call's model too — exactly what Out of Scope prohibits).

## Mechanics / Engine Constraints
This ticket touches only agent-orchestration/observability tooling (`.claude/workflows/*.js`,
`tools/agent-monitoring/`) — no `src/` simulation code, no Mechanics Bible chapter, no engine
contract. No formula/law from `docs/mechanics/` or `docs/engine/` constrains this work.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: needs a new additive field family (mirroring the existing
  "Retrieval-event field family" section, e.g. `shadow_reviewer_schema_version`, `candidate_model`,
  `candidate_verdict`, `candidate_cost_proxy_score`, `candidate_wall_time_ms`) plus a `seq` field
  carve-out note for the new shadow-reviewer negative-seq rows (mirroring the existing
  `context-packet-wrapper` `seq <= 0` exception already documented at the `seq` field row), and a
  `phase`/`agent` vocabulary note that the new shadow call sites are expected to show as
  non-canonical in `compute_drift_report()` (same precedent as `Retrieval`/`context-packet-wrapper`).
- `docs/parity_ledger/infrastructure.yaml`: needs a new `INFRA-3xx` entry documenting the new
  dual-call-site shadow-reviewer mechanism, mirroring `INFRA-299`'s shape (exact line numbers,
  env-var gate name, negative-seq formula, fail-open wrapper) — this is the established convention
  for every prior addition/modification to `.claude/workflows/implement-ticket.js`'s
  monitoring-write behavior (INFRA-299, and the sidecar-widening entries at ~lines 5626/5651 of this
  same file).
- `tests/tools/test_current_run_sidecar_orchestrator.py`: explicitly in scope per the ticket body —
  not a "doc" in the docs/ sense, so not listed as a Format-1 bullet here (done-checker's coverage
  check only parses `docs/` paths); tracked instead under Test Plan's Regression Surface / New Tests
  Required below.

The `docs/ai/shadow_promotion_gate_thresholds_decision.md` doc (path:
`docs/ai/shadow_promotion_gate_thresholds_decision.md`, under `docs/ai/`) is not required to change
for this ticket: it resolves a different, already-closed decision (Open Decision 5 for the
*retrieval-context-packet* shadow-evaluation promotion gate — sample size, thresholds, attribution
method for `SHADOW_CONTEXT_PACKET_ENABLED`), and this ticket's own Out of Scope explicitly excludes
"building the separate comparison-decision milestone that determines when the shadow window has
'enough evidence' to promote" for the reviewer-model case — that would be the document to extend
if/when that follow-up ticket is scoped, not this one. This ticket's "bounded sample window" AC is a
narrower, purely mechanical stop condition (see Risks/Open Questions below), not a promotion
decision, so it does not touch this doc's content.

## Parity Ledger Overlap
- `docs/parity_ledger/infrastructure.yaml`, entry `INFRA-299` (status: verified) — the exact
  precedent this ticket must reuse: "New advisory, opt-in shadow-packet call site ...
  `implement-ticket.js`'s Investigate phase (only), one orchestrator-side `bash()` statement
  invoking `tools/context_packet_assembler.py`'s `assemble_context_packet()` ... Uses a
  monotonic-negative `seq` counter ... env-var gate ... fail-open." `test_path:
  tests/tools/test_shadow_packet_call_site.py`. Not itself modified by this ticket (this ticket adds
  a structurally similar, but functionally distinct, mechanism at two different call sites) — but
  its own line-number citations of `implement-ticket.js` will not shift, since this ticket's new code
  is added at the Architecture-Verify/Security-Review sites, well after the Investigate-phase
  shadow-packet block cited by INFRA-299.
- No `P0` entries in `infrastructure.yaml` or any other ledger file overlap with this ticket's scope
  (`grep` for "shadow"/"reviewer" across all `docs/parity_ledger/*.yaml` surfaced only INFRA-299,
  the frontmatter-rollout entry `INFRA-402`-adjacent Wave 1 entry — unrelated `tools:` frontmatter,
  not `model:` — and several unrelated simulation-domain "shadow state"/"shadow shapers" entries in
  `world_dynamics.yaml`/`social_narrative.yaml` that are pure string-overlap, not scope overlap).
- No new entry needed in `combat_movement.yaml`, `town_resource.yaml`, `progression.yaml`,
  `social_narrative.yaml`, `strategic_cognition.yaml`, `world_dynamics.yaml`, `substrate.yaml`,
  or `faction.yaml` — none of those subsystems are touched.

## Prior Work
- `TCK-20260729-SHADOW-PACKET-CALL-SITE` (done) — the exact reusable pattern (see Risks below for
  one live defect found in it during this investigation).
- `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` (done) — resolves the *different* retrieval-packet
  promotion gate; useful as a design analog for "how to reason about sample-size floors" (see its §3:
  per-scenario run-count floor AND elapsed-period floor, whichever is later) but not directly reused
  code, and explicitly out of this ticket's scope to extend.
- `TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER` / `TCK-20260705-WORKFLOW-SECURITY-GATE` (done) —
  built the two production call sites this ticket adds shadow calls alongside; both still current,
  read in full above.
- `TCK-20260710-SECURITY-REVIEWER-AGENT-DOC` (done) — wired `security-reviewer.md` into the
  Security-Review phase; no `model:` frontmatter added, confirming the 0/16 count.
- `TCK-20260904-COST-PROXY-EPIC-TICKETS` (referenced throughout `docs/agent-monitoring/schema.md`,
  landed very recently) — gave `implement-epic.js`/`create-tickets.js` their own `writeSidecar`
  helpers using a disjoint **negative** `seq` range (`-1..-4`) alongside a pre-existing positive-seq
  array, for exactly the same reason a shadow-reviewer call needs one here: avoiding collision with
  the real per-phase positive-seq range. Directly analogous precedent for the recommendation below.

## Risks and Open Questions

1. **The `INFRA-299` precedent this ticket must reuse contains a live, unexercised bug.**
   `implement-ticket.js:597` computes `prior_shadow_count` via
   `load_jsonl(record_events.EVENTS_FILE)` — but `tools/agent-monitoring/record_events.py` no longer
   defines an `EVENTS_FILE` module attribute (confirmed: `grep -n "EVENTS_FILE"
   tools/agent-monitoring/record_events.py` returns nothing; the attribute was removed by
   `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`'s per-week-shard cutover). This raises
   `AttributeError`, silently swallowed by the surrounding `try/except Exception: pass` — so the
   shadow-packet call, whenever `SHADOW_CONTEXT_PACKET_ENABLED=1` is actually set, currently does
   *nothing* (never reaches `wrap_context_packet_assembly()`). This is consistent with
   `docs/ai/shadow_promotion_gate_thresholds_decision.md` §5's confirmation that zero real
   shadow-packet events exist in production — the flag has apparently never been turned on anywhere,
   so this defect has never been observed. **Implication for this ticket:** do not copy
   `load_jsonl(record_events.EVENTS_FILE)` verbatim into the new shadow-reviewer call sites. The
   correct, currently-working equivalent is `validate.load_data_glob(Path("agent-monitoring/data"),
   "events")` — the exact pattern `tools/agent-monitoring/seq_offset.py` itself uses for its own
   prior-`seq` lookup, and the same default-path computation `retrieval_events.py`'s own
   `emit_retrieval_event()` falls back to when no `events_file` is passed. Whether to *also* fix the
   pre-existing Investigate-phase shadow-packet call site's `EVENTS_FILE` bug in this same ticket (it
   is one line, directly adjacent in spirit) or leave it for a separate hotfix is a judgment call for
   Plan — flagged here, not decided.
2. **`pushEvent()` cannot carry the new fields this ticket needs.** `pushEvent(phaseLabel, agentName,
   status, summary, ts, toolCallCount, reasonCode)` (:244-255) only ever pushes the 7 base-schema
   fields into the in-memory `events` array — there is no way to attach `candidate_model`,
   `candidate_verdict`, or a distinctly-attributed cost/timing figure through it. The shadow verdict
   record must instead be emitted through a direct, `bash()`-invoked Python write mirroring
   `emit_retrieval_event()`'s shape (validate via `record_events.validate_record()`, write via
   `writer.write_lines()`) with a new additive field family analogous to `RETRIEVAL_EVENT_FIELDS` —
   this is the concrete meaning of "reuse the mechanism" for the schema-emission half of the work.
3. **The sidecar-adjacency test count genuinely needs to go from 11 to 13, not just have wording
   tweaked.** See Test Plan for the mechanical detail — confirmed by reading
   `test_sidecar_bash_write_precedes_each_covered_agent_call` in full: it asserts an exact regex
   count (`== 11`) of `await writeSidecar(events.length + 1 + seqOffset, ...)` occurrences, plus an
   exact list of 11 adjacency substrings. Two new shadow call sites, each needing their own
   `writeSidecar(...)`-then-`agent(...)` pair for correct `tool_call_count`/`cost_proxy_score`
   attribution (see point 2's cost-attribution requirement — merging the shadow call's tool
   footprint into the production call's `(run_id, seq)` bucket would violate AC #3's "labeled by
   which reviewer produced them" requirement), push this to 13. **Open question, not decided here:**
   should the new shadow `writeSidecar()` calls use the standard positive
   `events.length + 1 + seqOffset` expression, or a new negative-seq scheme? Positive would corrupt
   the monotonic invariant `pushEvent`/`writeSidecar` real-event seq numbering relies on (the shadow
   call's own tool calls would consume a slot in the real sequence without a corresponding
   `pushEvent()`, since AC #2 forbids the shadow verdict from being written to the same `events`
   array the production verdict uses). **Recommendation:** reuse the already-established negative-seq
   convention (both `TCK-20260729-SHADOW-PACKET-CALL-SITE`'s `-(1 + prior_shadow_count)` and
   `TCK-20260904-COST-PROXY-EPIC-TICKETS`'s fixed `-1..-4` range for `implement-epic.js`) — scoped
   per reviewer type (e.g. `-(1 + prior_shadow_count_for_this_run_id_and_reviewer)`), since the two
   reviewers accumulate at very different rates (see point 5) and a single shared negative counter
   would make the two reviewers' shadow-call counts impossible to distinguish from the sidecar side
   alone.
4. **Placement matters for a second, separate hardcoded test.**
   `tests/tools/test_step0_ts_orchestrator.py::test_ts_capture_bash_precedes_each_covered_agent_call`
   also hardcodes exact `captureTs()`→`writeSidecar()`→`agent()` triple-adjacency substrings for both
   `Architecture-Verify` and `Security-Review` (and asserts they exist verbatim via substring
   search, not an exact total count). As long as the new shadow-call blocks are appended *after* each
   existing three-line production triple (not spliced between `captureTs()`/`writeSidecar()`/
   `agent()`), this second test needs no changes — confirmed by reading it in full; it has no
   total-occurrence-count assertion analogous to the sidecar test's `== 11`. This is a placement
   constraint for Plan/Implement, not something to guess at during implementation.
5. **Asymmetric accumulation rate for the bounded window (ticket's own flagged open question,
   confirmed real).** `Security-Review` only fires for `security`-tagged tickets (or ones whose
   derived `suggested_skills` include `/security-review`) — `docs/agent-monitoring/schema.md`
   explicitly documents it as "absent entirely (not even a `skipped` event) for every other ticket."
   `Architecture-Verify` fires on every non-hotfix run. A single shared sample-window counter across
   both reviewers would let `Architecture-Verify` alone exhaust it long before `Security-Review`
   accumulates any real evidence. **Recommendation (see below).**
6. **No existing run-count/time-window gate check pattern exists to copy wholesale.** Grepped
   `tools/`, `docs/`, `.claude/` for `sample_window`/`SHADOW_WINDOW`/`shadow_window`/
   `window_closed`/`sample_count`/`shadow_sample` — no hits relevant to this scope. The closest real
   precedent is the *shape* already used twice in this codebase for a cheap, no-new-state check: scan
   `agent-monitoring/data/*/events.jsonl` for prior rows matching a marker (agent name / a new
   additive field) for a given key, and compare the count against a fixed threshold —
   `seq_offset.py::compute_seq_offset()` and the Investigate-phase shadow-packet block's own
   `prior_shadow_count` computation both already do exactly this shape, just for a different purpose
   (seq continuation, not a stop condition). **Recommendation:** a new small, testable, importable
   function (mirroring `seq_offset.py`'s `__main__`/`MARKER:`-prefixed-JSON convention so
   `implement-ticket.js` can call it via the same `bash()` + marker-index pattern as
   `resolveScopeTicketLocation`/`archCheckOutput`/`unresolvedCheckOutput`), e.g.
   `shadow_reviewer_window.py::is_shadow_window_open(reviewer: str, max_samples: int) -> bool`,
   counting prior shadow-reviewer events (via `validate.load_data_glob`, scanning for the new
   additive field family / a reviewer-specific agent-name suffix) **across all run_ids** (not scoped
   to the current run_id — a *sample* window bounds total observations across many tickets, unlike
   the per-run negative-seq collision-avoidance counter, which is correctly per-run_id). Threshold
   should be a named constant per reviewer (not one shared constant), directly addressing point 5 —
   e.g. a smaller floor for `security-reviewer` given its far slower accumulation, larger for
   `architecture-reviewer`. This function is a pure boolean gate a run can check cheaply before
   deciding whether to fire the candidate `agent()` call at all (skip it entirely once closed,
   satisfying AC #4) — it is deliberately *not* the promotion-decision machinery Out of Scope
   excludes; it never decides whether to promote, only whether to keep collecting samples.
7. **Prompt content for the candidate call.** Whether the candidate model receives the exact same
   prompt as the production reviewer, or a prompt stripped of the `verified_by`/static-check-results
   framing (since a different model may reason about the static-check evidence differently than the
   one the schema/prompt was tuned for) is an implementation-time judgment call, not resolved here —
   flag for Plan, do not assume an answer.
8. **Which candidate model to use is not specified anywhere in the ticket, Related Tickets, or
   Related Docs.** No model name/tier is named. This must be an explicit decision at Plan time (a
   real model identifier the harness recognizes, per the `claude-api` skill's model-id reference) —
   flagged as blocking for Plan, not guessed here.

## Anti-Drift Hazards
- Do not let the candidate call's `verdict` reach any `pushEvent(..., 'failed', ...)` /
  `writeMonitoring(...)` / early `return` path — those three are the only places either production
  call site currently affects workflow outcome, and AC #2's own required test (a test stubbing a
  candidate-only-failing scenario) exists specifically to catch a regression here.
- Do not let the shadow candidate call's own tool activity get folded into the production
  reviewer's `(run_id, seq)` `tools.jsonl` group — that would silently corrupt `cost_proxy_score`
  attribution for every future retro/dashboard read of Architecture-Verify/Security-Review's
  historical cost, not just this ticket's own data.
- Do not widen `Security-Review`'s trigger condition while wiring its shadow call — the trigger
  check at :1347-1348 (raw `tags` OR `suggested_skills`) is itself a prior hardening fix
  (`TCK-20260705-WORKFLOW-SECURITY-GATE`'s finding #6) and is explicitly out of this ticket's scope
  to touch.
- Do not extend this pattern to the pre-Implement Review phase's separate architecture-reviewer call
  (:618-644, against prose `plan.md`) — explicitly Out of Scope; it is a different call site with a
  different input shape (prose plan, not a diff) and no `ARCH_VERIFY_SCHEMA`/`archCheckResults`
  static-check pairing to attach a shadow call to in the same way.
- Do not build the promotion/"enough evidence" decision logic here — only the bounded stop-condition
  gate (point 6 above). Building the comparison-decision milestone is a distinct, not-yet-ticketed
  Bucket-B item per this ticket's own Out of Scope.
- Do not silently "fix" this ticket's own new sidecar-adjacency test failures by loosening the
  test's assertions instead of updating them to the new, correct 13-count/13-adjacency-list shape —
  per CLAUDE.md's Gate Integrity rule, a failing test here is real signal about a placement mistake
  (see Risk 4 above), not friction to route around.
