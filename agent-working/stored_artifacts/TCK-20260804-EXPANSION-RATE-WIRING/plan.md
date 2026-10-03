---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260804-EXPANSION-RATE-WIRING
artifact_type: plan
tags: [agent-monitoring, observability]
---

# Implementation Plan — TCK-20260804-EXPANSION-RATE-WIRING

## Decision: Option A (plumbing-only), confirmed after independent verification

Before writing this plan, I independently re-verified investigation.md's central citations rather
than taking its summary on trust:

- `tools/context_packet_assembler.py:36-43` — read directly. `EXPANSION_POLICY_STUB` and its
  comment are exactly as quoted: a plain string constant citing "Open Decisions 5/6 (expansion
  escalation semantics)" as deferred, deliberately typed so the field "can never accidentally
  expose a field resembling real escalation semantics."
- `docs/plans/archive/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md:93-95`
  — read directly. Confirmed verbatim: "Open Decisions 5 (promotion sample-size/thresholds) and 6
  (MCP tool vs. adapter-library exposure) — both still explicitly deferred; **do not force-resolve
  either just because this phase touches adjacent code**."
- `tests/tools/test_context_packet_assembler.py:311-323` — read directly. Confirmed
  `test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic` exists, asserts
  `packet.expansion_policy` contains `"not_yet_resolved"`, and asserts `max_expansions`/`trigger`/
  `threshold` are absent from it — i.e. a real, currently-passing regression test whose explicit
  job is to fail if this exact epic family's escalation-policy field ever stops being a stub.
  `stored_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/test_plan.md:66` and `plan.md:212,332`
  confirm this test was intentionally authored for exactly this purpose, not an incidental guard.
- `tools/retrieval_events.py` — read in full. Confirmed the 3 `wrap_*()` signatures and confirmed
  `emit_retrieval_event()`'s exact kwarg-forwarding mechanics (see Step 1 below) — a real
  correctness detail, independently verified, not assumed from the ticket's framing.

This evidence is exactly as investigation.md represented it, not overstated. Given that three
separately-shipped tickets in the same epic family (`CONTEXT-PACKET-SCHEMA`,
`CONTEXT-PACKET-ASSEMBLY`, and the module itself) have independently refused to give
`expansion_policy` real escalation content — one of them backing that refusal with a dedicated,
currently-passing regression test — implementing a real trigger for this ticket's sibling fields
(`expansion_reason`/`expansion_count`) would implement the same deferred escalation semantics
through the monitoring-event side door while the packet-contract front door explicitly refuses to,
for the identical stated reason ("do not force-resolve... just because this phase touches adjacent
code"). **This plan adopts Option A: plumbing-only.** `expansion_rate` will continue to read 0.0%
in practice after this ticket ships — an honest, disclosed limitation, not a bug — until a future
ticket actually resolves Open Decisions 5/6 and designs a real trigger for one specific producer.

## Summary

Add optional, never-fabricated `expansion_reason: str | None = None` /
`expansion_count: int | None = None` keyword-only parameters to all 3 `wrap_*()` functions in
`tools/retrieval_events.py` (`wrap_hybrid_retrieval`, `wrap_retrieval_cache_check`,
`wrap_context_packet_assembly`). Each wrapper forwards a supplied value to
`emit_retrieval_event()` verbatim; when a caller omits it (the default, `None`), the key must be
genuinely absent from the emitted record — not present with a literal `null` value — matching
`emit_retrieval_event()`'s existing `**retrieval_fields` pass-through behavior for every other
optional field. No new escalation/retry/trigger logic is added anywhere; no producer in this
codebase will call these new parameters yet, so `expansion_rate` legitimately stays 0.0%. Add the
tests test_plan.md specifies, update `docs/agent-monitoring/schema.md`'s field description to
disclose the permanent-0%-today state and why, and amend the existing `INFRA-297` parity ledger
entry's `v2_evidence` in place (no new entry) to describe the added optional parameters, following
the same in-place-amendment precedent that entry already used for the prior
`TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE` addition.

## Verified correctness detail: `emit_retrieval_event()`'s kwarg-forwarding behavior

`tools/retrieval_events.py:123-135`:
```python
record = {
    "run_id": run_id,
    "seq": seq,
    "ts": ts if ts is not None else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "phase": phase,
    "agent": agent,
    "summary": summary,
    "status": status,
    "retrieval_event_schema_version": retrieval_event_schema_version,
    **retrieval_fields,
}
```
`retrieval_fields` is whatever `**kwargs` the caller passed to `emit_retrieval_event()`. If a
wrapper naively called `emit_retrieval_event(..., expansion_reason=expansion_reason,
expansion_count=expansion_count)` unconditionally, then omitting the wrapper's own
`expansion_reason` argument (default `None`) would still produce
`record["expansion_reason"] = None` — a literal null key present in the JSON record, not an
absent key. This would fail `test_wrapper_omits_expansion_fields_when_not_supplied` (test_plan.md)
and would itself be a form of silent fabrication (a `None`-valued key is not "genuinely absent").

The codebase already has the correct pattern for this, in the same file:
`wrap_retrieval_cache_check()` (`tools/retrieval_events.py:244-263`) conditionally builds a
`retrieval_fields` dict —
```python
retrieval_fields = {
    "cache_level": cache_level,
    "cache_status": result.status,
    "latency_ms": latency_ms,
}
if "corpus_generation" in check_kwargs:
    retrieval_fields["corpus_generation"] = check_kwargs["corpus_generation"]
if "retrieval_version" in check_kwargs:
    retrieval_fields["retrieval_version"] = check_kwargs["retrieval_version"]
```
— then spreads it with `**retrieval_fields` into the `emit_retrieval_event()` call. Every step
below follows this exact established pattern for `expansion_reason`/`expansion_count`: build a
small dict conditionally (`if expansion_reason is not None: ...`), and spread it (`**`) into the
`emit_retrieval_event()` call. `wrap_hybrid_retrieval()` and `wrap_context_packet_assembly()`
currently pass their retrieval fields as literal keyword arguments (not a pre-built dict) directly
in the `emit_retrieval_event(...)` call — Steps 1 and 3 below introduce a small conditional dict
for just the two new optional fields in those two functions, spread alongside the existing literal
kwargs (Python allows mixing literal `key=value` args and a trailing `**dict` in the same call, as
long as no key collides — `expansion_reason`/`expansion_count` do not collide with any existing
literal key in either function).

## Steps

### Step 1 — Add optional expansion pass-through to `wrap_hybrid_retrieval()`

**Files:** `tools/retrieval_events.py` (function at current lines 154-199)
**Change:** Add `expansion_reason: str | None = None, expansion_count: int | None = None` as
keyword-only parameters, placed after `ts: str | None = None` and before `**hybrid_kwargs` (must
precede the `**kwargs` catch-all per Python syntax). Do not fold them into `**hybrid_kwargs` —
they must be captured as named parameters so they are never accidentally forwarded to the wrapped
`hybrid_fuse_and_filter(**hybrid_kwargs)` call. Immediately before the `emit_retrieval_event(...)`
call, build:
```python
optional_expansion_fields = {}
if expansion_reason is not None:
    optional_expansion_fields["expansion_reason"] = expansion_reason
if expansion_count is not None:
    optional_expansion_fields["expansion_count"] = expansion_count
```
Then add `**optional_expansion_fields` as the final argument to the existing
`emit_retrieval_event(...)` call (after `adequacy_verdict=...`). Do not change any existing
literal argument in that call.
**Do NOT touch:** `hybrid_fuse_and_filter()` itself, `candidate_k()`, the `adequacy_verdict`
computation, or any other field in this function's `emit_retrieval_event()` call.
**Verify:** `test_wrapper_omits_expansion_fields_when_not_supplied` and
`test_wrapper_forwards_expansion_fields_when_supplied` (`TestWrapHybridRetrieval`, per
test_plan.md).

### Step 2 — Add optional expansion pass-through to `wrap_retrieval_cache_check()`

**Files:** `tools/retrieval_events.py` (function at current lines 210-265)
**Change:** Add `expansion_reason: str | None = None, expansion_count: int | None = None` as
keyword-only parameters after `ts: str | None = None`, before `**check_kwargs`. This function
already builds a `retrieval_fields` dict conditionally (for `corpus_generation`/
`retrieval_version`) before the `emit_retrieval_event(...)` call — extend that same dict:
```python
if expansion_reason is not None:
    retrieval_fields["expansion_reason"] = expansion_reason
if expansion_count is not None:
    retrieval_fields["expansion_count"] = expansion_count
```
placed alongside the existing two `if "..." in check_kwargs:` blocks. No new dict or new spread
site is needed — this function's existing `**retrieval_fields` spread into
`emit_retrieval_event(...)` already covers the new fields once added to the dict.
**Do NOT touch:** The `dispatch` mapping, `check_index_cache`/`check_query_cache`/
`check_packet_cache`, or the `cache_status`/`cache_level`/`latency_ms` keys already unconditionally
in `retrieval_fields`.
**Verify:** `test_wrapper_omits_expansion_fields_when_not_supplied` and
`test_wrapper_forwards_expansion_fields_when_supplied` (`TestWrapRetrievalCacheCheck`).

### Step 3 — Add optional expansion pass-through to `wrap_context_packet_assembly()`

**Files:** `tools/retrieval_events.py` (function at current lines 276-322)
**Change:** Same shape as Step 1 (this function also passes fields as literal kwargs, not a
pre-built dict). Add `expansion_reason: str | None = None, expansion_count: int | None = None` as
keyword-only parameters after `ts: str | None = None`, before `**assemble_kwargs`. Build the same
`optional_expansion_fields` conditional dict pattern as Step 1, and spread it as the final argument
to the existing `emit_retrieval_event(...)` call (after `adequacy_verdict=...`).
**Do NOT touch:** `assemble_context_packet()` itself, `EXPANSION_POLICY_STUB`, or
`ContextPacket.expansion_policy` in `tools/context_packet_assembler.py` — that field is a
deliberately separate, deliberately-stubbed sibling concept guarded by
`test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic`, and is explicitly out of
scope for this ticket (see Scope Guards below). Do not touch `selected_count`,
`cited_source_hashes`, or `exclusion_reason_counts` computation.
**Verify:** `test_wrapper_omits_expansion_fields_when_not_supplied` and
`test_wrapper_forwards_expansion_fields_when_supplied` (`TestWrapContextPacketAssembly`).

### Step 4 — Add the 7 new tests to `tests/tools/test_retrieval_events.py`

**Files:** `tests/tools/test_retrieval_events.py`
**Change:** Extend the 3 existing per-wrapper classes (`TestWrapHybridRetrieval`,
`TestWrapRetrievalCacheCheck`, `TestWrapContextPacketAssembly`) — do not create new top-level
classes, per test_plan.md's stated 1-class-per-wrapper convention. Add:
- `test_wrapper_omits_expansion_fields_when_not_supplied` — one per wrapper class (3 total). Call
  the wrapper with no `expansion_reason`/`expansion_count` kwargs (all other required kwargs
  supplied as the existing tests in that class already do). Assert
  `"expansion_reason" not in written and "expansion_count" not in written` on the parsed JSON
  record — not `written.get(...) is None`, which would pass even if the key were present with a
  null value.
- `test_wrapper_forwards_expansion_fields_when_supplied` — one per wrapper class (3 total). Call
  the wrapper with `expansion_reason="manual_widen"`, `expansion_count=1` added to an otherwise
  normal invocation. Assert `written["expansion_reason"] == "manual_widen"` and
  `written["expansion_count"] == 1`, verbatim.
- `test_wrap_functions_never_fabricate_expansion_reason_internally` — one test, exercises all 3
  wrappers. For each wrapper, call it across several varied realistic inputs that could plausibly
  be mistaken for an expansion signal by a future careless edit — a cache `MISS` (not just `HIT`)
  for `wrap_retrieval_cache_check`, a `noisy`-triggering candidate/selected ratio (per
  `compute_adequacy_verdict`'s existing `NOISY_RATIO_THRESHOLD` logic) for
  `wrap_hybrid_retrieval`, and a nonzero `exclusion_reason_counts` (an `excluded` list with at
  least one entry) for `wrap_context_packet_assembly` — with no `expansion_reason`/
  `expansion_count` kwargs supplied in any case. Assert both keys are absent from every resulting
  record. This is a regression guard, not a test of new behavior: it must keep passing forever,
  since its entire purpose is catching a future accidental auto-population.
Also add, in `tests/tools/test_generate_retro.py` (only if the corpus-wide regression test does not
already exist — check first per test_plan.md's own instruction):
- `test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger` — integration
  test running the existing, unmodified `compute_retrieval_metrics()` against the real
  `agent-monitoring/events.jsonl` retrieval-event cohort (or an equivalent fixture cohort
  containing only events with no `expansion_reason`/`expansion_count` set, if isolating from the
  live file is more appropriate — follow whatever pattern
  `tests/tools/test_generate_retro.py`'s existing retrieval-metric tests already use for
  event-source selection) and asserts `expansion_rate == 0.0`. This is an explicit, disclosed
  regression guard against a future accidental fabrication silently making this non-zero, not a
  placeholder assertion.
**Do NOT touch:** `test_wrapper_emits_exactly_one_retrieval_event` or any other existing test in
either file — test_plan.md confirms zero existing tests need modification, since
`emit_retrieval_event`'s record shape is additive/dict-based, not key-set-enumerated at this layer.
**Verify:** `pytest tests/tools/test_retrieval_events.py tests/tools/test_generate_retro.py -v`
shows 0 failures, 0 skips, with all 7 new tests present and passing, and the pre-existing test
count unchanged in content.

### Step 5 — Update `docs/agent-monitoring/schema.md`'s field description

**Files:** `docs/agent-monitoring/schema.md` (line 287)
**Change:** Current text: `| `expansion_reason` / `expansion_count` | string / int | Present only
if a follow-up expansion occurred. |`. Replace with a version that keeps the existing accurate
claim and adds an explicit disclosure that no producer triggers this today and why, e.g.:
`| `expansion_reason` / `expansion_count` | string / int | Present only if a follow-up expansion
occurred. As of TCK-20260804-EXPANSION-RATE-WIRING, all 3 `wrap_*()` producers in
`tools/retrieval_events.py` accept these as optional pass-through parameters, but no producer in
this codebase currently supplies them — Open Decisions 5/6 (expansion escalation semantics, see
`tools/context_packet_assembler.py`'s `EXPANSION_POLICY_STUB`) remain deferred, so
`expansion_rate` (`generate_retro.py::compute_retrieval_metrics()`) reads 0.0% in practice. This is
an intentional, disclosed limitation, not a bug. |`
Keep the exact wording aligned with whatever Step 1-3 actually implement; do not describe a
trigger mechanism that does not exist.
**Do NOT touch:** Any other row in the schema table, or the "Provenance" paragraph immediately
below it (lines 290+).
**Verify:** No automated test covers doc prose directly; manually confirm the updated line reads
consistently with Steps 1-3's actual signatures. If `docs/` files are modified, run
`make knowledge-index-update` per CLAUDE.md's After Work section.

### Step 6 — Amend `INFRA-297`'s `v2_evidence` in `docs/parity_ledger/infrastructure.yaml`

**Files:** `docs/parity_ledger/infrastructure.yaml` (entry `INFRA-297`, currently at lines
6237-6285)
**Change:** `INFRA-297` already accurately describes the 3 `wrap_*()` functions and
`emit_retrieval_event()`; it was already amended in place once before, for
`TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE`, by appending a descriptive clause inside the
`emit_retrieval_event()` bullet's parenthetical (visible today at
`docs/parity_ledger/infrastructure.yaml` in the `:91-143` bullet: "TCK-20260803-RETRIEVAL-EVENT-TS-OVERRIDE
added an optional keyword-only `ts: str | None = None` param — ..."). Follow the identical
in-place-amendment precedent: append a similar clause to each of the 3 wrapper bullets (`:154-199`
wrap_hybrid_retrieval, `:210-265` wrap_retrieval_cache_check, `:276-322`
wrap_context_packet_assembly) noting that `TCK-20260804-EXPANSION-RATE-WIRING` added optional
keyword-only `expansion_reason`/`expansion_count` params, forwarded to `emit_retrieval_event()`
only when supplied (never defaulted/fabricated), with no producer in this codebase supplying them
yet. Do not attempt to hand-recompute the exact new line-range numbers for the whole entry (the
prior ts-override amendment did not renumber the base `:91-143`/`:154-199`/etc. ranges either,
treating them as approximate historical anchors) — a later `parity-updater` pass or Finalize's
registry regeneration is where exact line numbers get reconciled if the convention requires it.
Also append one sentence to `support_boundary` clarifying that this addition does not change the
"no producer wired" characterization already established there for `expansion_reason`/
`expansion_count` — that characterization predates this ticket and remains true after it. Leave
`status: verified`, `priority: P2`, `proof_type: regression`, and `test_path:
tests/tools/test_retrieval_events.py` unchanged — all remain accurate.
**Do NOT touch:** `INFRA-298`, `INFRA-299`, or any other entry in this file. Do not create a new
`INFRA-3xx` entry — this is a minor additive extension of the same module/field-set INFRA-297
already covers, consistent with how the ts-override change was handled.
**Verify:** No test asserts on parity-ledger YAML prose directly; confirm the file still parses as
valid YAML (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`)
after editing.

## Scope Guards

Explicit list of things this plan must NOT touch, derived from the ticket's Out of Scope section
and investigation.md's Anti-Drift Hazards:

- Do not invent any real expansion trigger, threshold, or retry logic in `tools/hybrid_retrieval.py`,
  `tools/retrieval_cache.py`, or `tools/context_packet_assembler.py`. No caller anywhere in this
  ticket's change set may ever call any `wrap_*()` function twice for the same logical request, or
  auto-derive `expansion_reason`/`expansion_count` from any other field's value.
- Do not touch `ContextPacket.expansion_policy` or `EXPANSION_POLICY_STUB` in
  `tools/context_packet_assembler.py` — a deliberately separate, still-stubbed sibling field
  guarded by its own regression test.
- Do not force-resolve Open Decisions 5/6 — they remain the epic's decisions for a future ticket.
- Do not touch `generate_retro.py::compute_retrieval_metrics()`'s `expansion_rate` formula
  (lines ~699-711 per the ticket) — already correct and out of scope.
- Do not build a general-purpose retry/backoff framework for retrieval.
- Do not wire `tools/hybrid_retrieval.py`/`tools/context_packet_assembler.py` into any real
  (non-shadow) production workflow path — remains deferred per the backlogged epic
  `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`.
- Do not modify `implement-ticket.js`'s existing `SHADOW_CONTEXT_PACKET_ENABLED` call site
  (`INFRA-299`) — unrelated to this ticket's scope.
- Do not fabricate a fake/synthetic expansion event anywhere in production code paths. Test
  fixtures that already use `"budget_exceeded"` as an example schema value
  (`tests/tools/test_retrieval_events.py:118`) remain unchanged — they test schema validation, not
  a real trigger.
- Do not modify `record_events.py`'s `REQUIRED`/`VALID_STATUS` sets or `writer.py`'s append
  mechanism.

## Dependency Map

Steps 1, 2, and 3 are independent of each other (different functions, same file — implement and
verify each individually before moving to the next, but none blocks another). Step 4 depends on
Steps 1-3 being complete (tests exercise the new parameters). Steps 5 and 6 (docs/parity ledger)
depend on Steps 1-3's exact final parameter names/placement but not on Step 4; they can proceed in
parallel with Step 4 once Steps 1-3 land. Recommended order: 1 → 2 → 3 → 4 → 5 → 6 (matches the
ticket's own Implementation Notes/Test Summary/Files Changed narrative flow), but 5 and 6 may swap
or run concurrently.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Investigation explicitly determines whether real expansion-triggering caller behavior exists, with evidence | Pre-plan (investigation.md, independently re-verified in this plan's Decision section) | N/A (evidence-based finding, not a test) |
| Plan makes an explicit, disclosed decision between plumbing-only vs. minimal-real-trigger, with rationale | This plan's "Decision" section | N/A |
| Whatever is implemented is tested; no fabricated/fake expansion rate asserted | Steps 1-4 | `test_wrapper_omits_expansion_fields_when_not_supplied` (x3), `test_wrapper_forwards_expansion_fields_when_supplied` (x3), `test_wrap_functions_never_fabricate_expansion_reason_internally`, `test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger` |
| `docs/agent-monitoring/schema.md`'s field description remains accurate to what was implemented | Step 5 | Manual review (no doc-prose test) |
| No fabricated or silent expansion data anywhere in the change | Steps 1-4 (conditional-dict pattern; anti-fabrication test) | `test_wrap_functions_never_fabricate_expansion_reason_internally`, `test_wrapper_omits_expansion_fields_when_not_supplied` (x3) |

## Anti-Drift Notes

- **The `None`-vs-absent-key distinction is the single most important correctness detail in this
  ticket.** `emit_retrieval_event()`'s `**retrieval_fields` mechanism means any kwarg literally
  passed — even with value `None` — becomes a literal `null` in the emitted JSON record. Every
  wrapper change must use the conditional-dict-then-spread pattern (already established by
  `wrap_retrieval_cache_check()` for `corpus_generation`/`retrieval_version`), never an
  unconditional `expansion_reason=expansion_reason` literal kwarg.
- **`expansion_reason`/`expansion_count` must be captured as named keyword-only parameters, not
  swept into `**hybrid_kwargs`/`**check_kwargs`/`**assemble_kwargs`.** If they were left to fall
  into the catch-all, they would get forwarded into the wrapped function call itself
  (`hybrid_fuse_and_filter(**hybrid_kwargs)` etc.), which do not accept these parameters and would
  raise a `TypeError` — and even if they happened to be silently accepted, it would violate the
  "read-only wrapper, does not alter the wrapped function's call contract" property this module's
  own docstring establishes.
- **This ticket's fix does not make `expansion_rate` non-zero in the live `agent-monitoring/events.jsonl`
  corpus.** That is expected and correct, not a leftover TODO — state this plainly in the ticket's
  Completion Summary per investigation.md's own instruction.
- **`ContextPacket.expansion_policy` and this ticket's `expansion_reason`/`expansion_count` are
  sibling-but-distinct fields covering the same deferred concept from two different layers**
  (packet-contract vs. monitoring-event). Keeping them both stubbed/unpopulated is the entire point
  of this ticket's Option A decision — implementing one while leaving the other stubbed would be
  fine (they are legitimately separate mechanisms), but implementing a real trigger for either one
  without resolving Open Decisions 5/6 first is the hazard this plan exists to avoid.
- Per CLAUDE.md, stage `agent-monitoring/tools.jsonl` and run `make knowledge-index-update` (Step 5
  touches `docs/`) before Finalize.
