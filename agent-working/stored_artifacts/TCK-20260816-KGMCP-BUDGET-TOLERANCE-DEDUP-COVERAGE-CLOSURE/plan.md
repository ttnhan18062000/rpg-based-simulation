---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE

## Summary

Gap 1 is fixed by widening `assemble_within_budget()`'s per-statement cost to include the real,
measured cost of each statement's own matching `context[]`/`evidence[]` entries — not by
introducing a separate "truncate whole units" pass, and not by a statements-first-then-fill/orphan
design. This is a deliberate, evidence-backed merge of the ticket's own options (a) and (b): given
`assemble_packet()`'s existing downstream filter (`tools/knowledge_gateway_packet_assembly.py:786-789`,
read this session) already derives `final_context`/`final_evidence` strictly from
`included_statements`' `evidence_ids`, a statement and its context/evidence are architecturally
inseparable today — there is no code path that ships one without the other. Widening the *cost*
measured inside the existing single greedy loop (same sort order, same break-on-overflow semantics,
same statements-first priority policy) therefore *is* "truncate whole units together" (option a)
and simultaneously *is* "count context/evidence against the same budget without changing what gets
truncated" (option b) — they collapse into one design once the existing architecture is read
correctly. Option (b)'s literal "drop context but keep statement" variant is rejected: it would
require decoupling `final_context`/`final_evidence` from `included_statements` (a bigger,
unrequested architecture change) and would produce exactly the "unsupported statement" outcome the
ticket's own evidence-authority reasoning warns against. Option (c) (split sub-budgets) is rejected
as introducing an undefined tunable the proposal doc never specifies. `conflicts[]` — never owned
by any single statement — gets its own, separate truncation pass against the budget *remaining*
after statements/context/evidence, with its own new visible markers
(`conflicts_truncated`/`omitted_conflict_count`), since it genuinely is an independent truncation
event, unlike context/evidence (which can never be truncated independently of their statement under
this design).

Gap 2 closes by disclosure, not by force: a live re-run against the current 7-entry corpus (this
session, reusing `render_candidates()`/`deduplicate_statements()` directly) found the same 0 real
cross-provider content duplicates the investigation already found, confirming it is not a stale
finding. The ticket's own AC4 wording explicitly permits closing by "honestly re-confirmed as still
open with updated real reasoning" — this plan takes that path: lock the 0/7 finding in a regression
test and update the Phase 3 doc's disclosed-limitation language, and does **not** propose a corpus
extension, because the investigation already traced why no real, narrow, non-fabricated extension
is defensible (no organic near-miss exists in the corpus — see investigation.md Risks). The adjacent
`canonical_fragment_hash`-vs-`_content_hash()` parity dedup-identity divergence is ruled genuinely
out of scope: fixing it means editing `render_candidates()`'s `parity_ledger` block
(`:348-386`, read this session), which is squarely inside "the Parity adapter," explicitly excluded
by this ticket's own Out of Scope. It gets a regression-locking test only, and is flagged for a
future ticket.

## Steps

### Step 1 — Widen `assemble_within_budget()`'s per-statement cost to include context/evidence

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** In `assemble_within_budget()` (currently `:643-670`, confirmed by direct read this
session), change the signature to:

```python
def assemble_within_budget(
    statements: list[Statement],
    budget_requested: int,
    context_entries: Sequence[ContextEntry] = (),
    evidence_entries: Sequence[EvidenceEntry] = (),
) -> tuple[list[Statement], int]:
```

(add `Sequence` to the existing `from typing import Optional` import at `:63`.)

Build two lookup dicts once, up front: `context_by_id = {c.source_id: c for c in context_entries}`
and `evidence_by_id = {e.evidence_id: e for e in evidence_entries}` — safe as 1:1 maps because
`render_candidates()` (`:260-387`, read this session) assigns each candidate's `evidence_id` as
both `ContextEntry.source_id` and `EvidenceEntry.evidence_id` from the same local variable in every
one of its three provider blocks (confirmed at `:296`/`:304` for context_search, `:333`/`:341-342`
for graphify, `:372`/`:380` for parity_ledger).

Add a new helper, adjacent to `assemble_within_budget()`:

```python
def _statement_included_content_cost(
    statement: Statement,
    context_by_id: dict[str, ContextEntry],
    evidence_by_id: dict[str, EvidenceEntry],
) -> int:
    """Real, measured cost of a statement PLUS every context/evidence entry that would ship
    alongside it once included (mirrors assemble_packet()'s own included_evidence_ids filter at
    :786-789 exactly — a statement's evidence_ids is precisely what final_context/final_evidence
    get filtered by downstream, so this must sum over the same evidence_ids). Never a
    length*constant estimate (assemble_within_budget()'s own docstring, :648-649) — every term is
    a real kgmcp_char_heuristic_v1() call on real text/field content actually present on a real
    ContextEntry/EvidenceEntry.
    """
    cost = kgmcp_char_heuristic_v1(statement.text)
    for evidence_id in statement.evidence_ids:
        ctx = context_by_id.get(evidence_id)
        if ctx is not None:
            cost += kgmcp_char_heuristic_v1(ctx.summary)
        ev = evidence_by_id.get(evidence_id)
        if ev is not None:
            cost += kgmcp_char_heuristic_v1(ev.evidence_id)
            cost += kgmcp_char_heuristic_v1(ev.path or "")
            cost += kgmcp_char_heuristic_v1(ev.evidence_hash)
    return cost
```

Replace the loop's `cost = kgmcp_char_heuristic_v1(statement.text)` line with
`cost = _statement_included_content_cost(statement, context_by_id, evidence_by_id)`. Do not change
the sort key (`(priority_tier, i)`), the greedy `running_total + cost <= budget_requested` check, or
the `break`-on-first-overflow semantics — those are unrelated to Gap 1's own scope (the anti-drift
hazard on not reordering the pipeline applies here).

With `context_entries=()`/`evidence_entries=()` (the default), `_statement_included_content_cost()`
degrades to exactly `kgmcp_char_heuristic_v1(statement.text)` — not a special-cased "legacy mode,"
just the same formula correctly evaluating to zero extra terms when there is nothing to look up.
This is why `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate` (calls
`assemble_within_budget([short], budget_requested=1000)` with 2 positional args, asserts
`returned_short == kpa.kgmcp_char_heuristic_v1(short.text)` exactly — read at
`tests/tools/test_knowledge_gateway_packet_assembly.py:265-277` this session) and
`test_budget_returned_never_exceeds_budget_requested` (`:280-286`, also 2-arg calls) keep passing
unmodified — do not touch either test.

**Do NOT touch:** the sort key, the greedy break semantics, `deduplicate_statements()`,
`build_conflicts()`, or the `render → dedup → conflicts → truncation` step order in
`assemble_packet()` (`:727-730` docstring, "load-bearing and must not be reordered").

**Verify:** `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`,
`test_budget_returned_never_exceeds_budget_requested` (both keep passing, 2-arg legacy form),
`test_assemble_within_budget_accounts_context_and_evidence_bytes_not_just_statement_text` (new, this
plan's Step 6).

### Step 2 — Add a separate conflicts[] budget-truncation pass

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** `conflicts[]` is never owned by any single statement (`Conflict.subject` is a
`source_path`/`symbol` pair string, not linked to any `evidence_id` — confirmed by reading
`_structural_supersession_signal()`/`build_conflicts()` at `:579-638` this session), so it cannot
reuse Step 1's per-statement mechanism and needs its own pass, against whatever budget remains after
statements/context/evidence are assembled. Add:

```python
def truncate_conflicts_within_budget(
    conflicts: list[Conflict], remaining_budget: int
) -> tuple[list[Conflict], int]:
    """Real-measured, greedy, original-order truncation of conflicts[] against whatever budget
    remains after Step 8's statement+context+evidence assembly. Cost is the real sum of
    kgmcp_char_heuristic_v1() over each claim's real .value text -- the only prose-bearing field on
    a Conflict/ConflictClaim (see ConflictClaim at :562-568) -- never a length*constant estimate.
    Never reorders conflicts; drops the first conflict (and everything after it in list order) that
    would overflow, mirroring assemble_within_budget()'s own break-on-first-overflow discipline.
    """
    included: list[Conflict] = []
    running_total = 0
    for conflict in conflicts:
        cost = sum(kgmcp_char_heuristic_v1(claim.value) for claim in conflict.claims)
        if running_total + cost <= remaining_budget:
            included.append(conflict)
            running_total += cost
        else:
            break
    return included, running_total
```

**Do NOT touch:** `build_conflicts()` or `_structural_supersession_signal()` themselves — this step
only adds a truncation pass over their already-real output, never a new detection heuristic (the
existing `test_conflicts_never_populated_from_bare_topical_similarity` and
`test_no_semantic_or_embedding_dependency_introduced` guards must keep passing unmodified).

**Verify:** `test_conflicts_are_measured_against_budget_even_though_real_corpus_never_populates_them`
(new, Step 6).

### Step 3 — Thread the widened accounting and conflicts-truncation into `assemble_packet()` and `PacketAssembly`

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** In `PacketAssembly` (`:675-693`, read this session), add two new fields after
`omitted_statement_count`: `conflicts_truncated: bool` and `omitted_conflict_count: int`.

In `assemble_packet()` (`:726-828`, read this session):
- Change the call at `:770` from `assemble_within_budget(statements, budget_requested)` to
  `assemble_within_budget(statements, budget_requested, context_entries, evidence_entries)`.
- After the existing `budget_assembly_failed`/`else` branch that sets `final_statements`/
  `final_context`/`final_evidence`/`answer`/`budget_returned` (`:777-790`), compute
  `remaining_budget = max(budget_requested - budget_returned, 0)` and call
  `final_conflicts, conflicts_cost = truncate_conflicts_within_budget(conflicts, remaining_budget)`,
  then `omitted_conflict_count = len(conflicts) - len(final_conflicts)` and
  `conflicts_truncated = omitted_conflict_count > 0`. This runs identically in both the
  `budget_assembly_failed` branch (where `budget_returned` is forced to `0`, so
  `remaining_budget == budget_requested` — conflicts get a full, independent shot at the budget even
  when every statement was dropped) and the ordinary branch — no special-casing needed since
  `remaining_budget`'s formula already produces the right value in both cases.
- Change the `status` computation's `elif conflicts:` (`:795`) to `elif final_conflicts:` — status
  must reflect what is actually returned, exactly mirroring how `final_statements` (not raw
  `statements`) already drives `verification`/`provenance_providers` a few lines below.
- Change the constructor call's `conflicts=conflicts,` (`:821`) to `conflicts=final_conflicts,`, and
  add `conflicts_truncated=conflicts_truncated,` / `omitted_conflict_count=omitted_conflict_count,`.

**Do NOT touch:** the `render → dedup → negative-claim → conflicts(build) → truncation → §16
fallback` step order; the `budget_assembly_failed` boolean's own definition
(`bool(statements) and not included_statements`, `:777`) — unaffected by this step, since it reads
`statements`/`included_statements`, not conflicts.

**Verify:** all of Step 1/2's tests plus `test_deduplication_occurs_before_truncation_not_after`
(existing, unmodified — proves the pipeline order survived) and
`test_conflict_index_pairs_correspondence_invariant_raises_on_desync` (existing, unmodified).

### Step 4 — Thread `conflicts_truncated`/`omitted_conflict_count` into the MCP response

**Files:** `tools/knowledge_gateway_mcp.py`

**Change:** In `_run_knowledge_context()` (`:149-372`, read this session):
- Router-failure `fallback_response` dict (`:200-216`): add `"conflicts_truncated": False` and
  `"omitted_conflict_count": 0` alongside the existing `"budget_truncated": False`/
  `"omitted_statement_count": 0` at `:209-210` — nothing was ever computed on this early-failure
  path (router itself failed before packet assembly ran), mirroring the existing precedent exactly.
- Main response dict (`:268-280`): add `"conflicts_truncated": packet.conflicts_truncated,` and
  `"omitted_conflict_count": packet.omitted_conflict_count,` alongside the existing
  `"budget_truncated": packet.budget_truncated,`/`"omitted_statement_count": packet.omitted_statement_count,`
  at `:277-278`.

**Do NOT touch:** the Level 1/Level 2 cache-hit response paths (`:237-244`, `:259-264`) — those
return early with whatever the cache already stored; a cached packet written *after* this ticket's
fix will already carry the new fields via the write path below, so no separate threading is needed
there. Do not touch the cache-write hook calls (`:353-368`) — they already serialize whatever is in
`response` at that point, which now includes the two new keys automatically.

**Verify:** `test_new_truncation_markers_threaded_into_run_knowledge_context_response` (new, Step 7,
renamed from test_plan.md's provisional name — see Anti-Drift Notes below for why).

### Step 5 — Schema: add the two new fields additively

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`

**Change:** Add `"conflicts_truncated": { "type": "boolean" }` and
`"omitted_conflict_count": { "type": "integer" }` to the `properties` object, adjacent to the
existing `"budget_truncated"`/`"omitted_statement_count"` entries (`:124-125`, read this session).
The top-level schema's `additionalProperties` is confirmed NOT restricted (schema docstring at `:4`,
read this session, explicitly forbids adding `additionalProperties: false` here) — no
`schema_version` bump needed, matching the `budget_truncated`/`omitted_statement_count` precedent
INFRA-347 already established.

**Do NOT touch:** the request schema (which does stay closed with
`additionalProperties: false` per its own docstring) — only the response schema changes.

**Verify:** `test_knowledge_context_response_schema_accepts_new_context_truncation_marker_field`
(new, Step 7).

### Step 6 — Unit tests: AC1/AC3 new coverage + fix two existing budget-boundary tests

**Files:** `tests/tools/test_knowledge_gateway_packet_assembly.py`

**Change:**
1. Add `test_assemble_within_budget_accounts_context_and_evidence_bytes_not_just_statement_text` —
   construct a `Statement` whose `text` alone is small, plus a `ContextEntry`/`EvidenceEntry` pair
   sharing its `evidence_ids[0]` whose `summary`/`path`/`evidence_hash` are large; call
   `assemble_within_budget([stmt], budget, [ctx_entry], [ev_entry])` with `budget` sized to fit the
   statement alone but not the combined cost; assert the statement is now excluded (`included == []`)
   — proving the widened accounting genuinely changes inclusion, not just `budget_returned`'s number.
2. Add `test_conflicts_are_measured_against_budget_even_though_real_corpus_never_populates_them` —
   directly-constructed `Conflict`/`ConflictClaim` fixtures (mirrors the existing
   `test_conflict_only_surfaces_real_supersession_metadata` fixture style at `:380-`), call
   `truncate_conflicts_within_budget()` directly with a budget too small for all claims; assert
   truncation occurs and cost reflects real `claim.value` lengths, not a constant.
3. Add `test_budget_returned_reflects_combined_cost_when_context_and_evidence_are_supplied` — same
   statement as (1) but sized to fit the combined cost; assert the 4-arg call's `budget_returned` is
   strictly greater than the 2-arg call's `budget_returned` for the identical statement — this is the
   plan's answer to test_plan.md's provisional
   `test_budget_returned_semantics_documented_change_is_explicit_not_silent`: the field's value is a
   deterministic, testable function of which arguments were supplied (empty vs. real
   context/evidence), never an implicit hidden mode switch.
4. Add `test_assemble_within_budget_never_uses_length_times_constant_estimate` — assert
   `_statement_included_content_cost()` for two ContextEntry/EvidenceEntry pairs of different real
   lengths produces different real costs proportional to their actual `kgmcp_char_heuristic_v1()`
   values, not a fixed multiplier of the statement-only cost.
5. Fix `test_budget_truncation_produces_visible_marker_when_content_is_dropped` (`:672-687`) and
   `test_evidence_dependencies_excludes_paths_from_omitted_budget_truncated_statements` (`:728-744`):
   both currently set `budget_requested=cost_a` where `cost_a = kpa.kgmcp_char_heuristic_v1(text_a.strip())`
   — sized to admit exactly one statement under the OLD statement-only accounting. Under Step 1's
   real widened accounting (exercised because both tests go through `_assemble()` → `assemble_packet()`,
   which now always passes real `context_entries`/`evidence_entries`), `text_a`'s real combined cost
   is strictly larger than `cost_a` alone (its `ContextEntry.summary` duplicates `text_a` verbatim
   per `render_candidates()`, plus its `EvidenceEntry` fields add more), so `budget_requested=cost_a`
   would now admit **zero** statements (triggering the §16 failure branch, `omitted_statement_count
   == 2`) instead of the test's asserted `omitted_statement_count == 1`. This is a real, expected
   consequence of the ticket's own intended budget shrink — not a regression to work around. Update
   both tests' `budget_requested` to the real combined cost of `text_a` alone (derive it via real
   code, e.g. run `_assemble()` once with a large budget to read the real `ContextEntry`/
   `EvidenceEntry` the pipeline actually produces for `text_a`, then compute
   `kgmcp_char_heuristic_v1(text_a.strip()) + kgmcp_char_heuristic_v1(ctx.summary) +
   kgmcp_char_heuristic_v1(ev.evidence_id) + kgmcp_char_heuristic_v1(ev.path or "") +
   kgmcp_char_heuristic_v1(ev.evidence_hash)` — never hardcode a guessed literal). The tests'
   assertions themselves (`omitted_statement_count == 1`, `evidence_dependencies == ["docs/a.md"]`
   and not `"docs/b.md"`) stay unchanged — only the input budget value is corrected to match the new,
   real accounting.

**Do NOT touch:** `test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`
(`:689-698`, budget=10,000 — combined cost still trivially fits, unaffected) or
`test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too` (`:700-709`, budget=1 —
already in the failure branch under old accounting, unaffected by widening).

**Verify:** the 4 new tests above, plus the 2 corrected tests passing with their original
assertions intact.

### Step 7 — Integration tests: response/schema threading

**Files:** `tests/tools/test_knowledge_gateway_mcp.py`

**Change:** Add `test_new_truncation_markers_threaded_into_run_knowledge_context_response` — call
`_run_knowledge_context()` with a query/budget that forces conflicts truncation (requires a
monkeypatched provider result carrying `superseded_by`/`supersedes` to make `build_conflicts()`
non-empty, mirroring how existing conflict tests already monkeypatch providers) and assert
`response["conflicts_truncated"]`/`response["omitted_conflict_count"]` are present and correct,
alongside the existing `response["budget_truncated"]`/`response["omitted_statement_count"]`
assertions staying independently correct (not collapsed together). Add
`test_knowledge_context_response_schema_accepts_new_context_truncation_marker_field` — validate a
response dict containing the two new keys against `RESPONSE_VALIDATOR` and assert no
`ValidationError`.

**Do NOT touch:** `test_knowledge_context_response_schema_accepts_new_budget_marker_field` or
`test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker` (existing,
unmodified) — they test the pre-existing `budget_truncated`/`omitted_statement_count` fields, which
this ticket does not rename or restructure.

**Verify:** both new tests above.

### Step 8 — Gap 2 and adjacent-gap regression-locking tests (no fix, disclosure only)

**Files:** `tests/tools/test_knowledge_gateway_packet_assembly.py` (or a new sibling file
`tests/tools/test_kgmcp_baseline_corpus_dedup_coverage.py` if the corpus-driving fixture machinery
is large enough to warrant separation — implementer's call, either location is acceptable).

**Change:**
1. Add `test_live_corpus_has_zero_cross_provider_content_duplicates_documented_limitation` — runs
   the real gateway (`kgr.route()` → `call_providers_for_routing_decision()` →
   `render_candidates()` → `deduplicate_statements()`, the same real call chain this session's
   investigation used) against all 7 entries in
   `tools/agent-monitoring/kgmcp_baseline_corpus.py`, and asserts pre-dedup and post-dedup statement
   counts are equal for every entry (i.e., zero real cross-provider — or any-provider — content
   collisions today). This is a regression lock: if a future change causes real duplicate content to
   start appearing (or `deduplicate_statements()` stops detecting an existing one), this test fails
   and the finding must be re-evaluated, not silently drift further from documented reality.
2. Add `test_parity_ledger_evidence_hash_uses_canonical_fragment_hash_not_content_hash` — construct
   a `parity_result` fixture with `results.found=True` and a `record` whose `text` is byte-identical
   (post-`.strip()`) to a separately-supplied `context_search` result's `excerpt`; run
   `render_candidates()` on both; assert the two statements' `evidence_hash` values differ (parity's
   equals `record["canonical_fragment_hash"]`, context_search's equals `_content_hash(text)`) even
   though their `.text` is identical — locking in the real divergence this session's investigation
   found (`render_candidates()` parity block, `:348-386` for the assignment, `:279`/`:316` for the
   two `_content_hash(text)` assignments — all read this session), without fixing it. This test must
   NOT call `deduplicate_statements()` and assert non-collapse as its point — the point is the
   `evidence_hash` divergence itself, not a dedup outcome (no live corpus entry produces this
   scenario today per investigation.md, so this is fixture-only, matching `build_conflicts()`'s own
   established fixture-only precedent for untestable-against-real-providers logic).

**Do NOT touch:** `render_candidates()`'s `parity_ledger` block (`:348-386`) — this step adds
regression-locking tests for the *current* (divergent) behavior; it must never change
`evidence_hash = record["canonical_fragment_hash"]` to `_content_hash(text)` or vice versa. Fixing
this divergence is explicitly out of scope for this ticket (see Scope Guards).

**Verify:** both new tests above, both passing against unmodified `render_candidates()`.

### Step 9 — Re-run §21 #12 measurement against the fixed code; update the Phase 3 doc

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`,
`tests/tools/fixtures/kgmcp_phase3_pilot_acceptance_measurement_results.json` (runner output)

**Change:** After Steps 1-5 land, re-run the existing runner unmodified:
`.venv/bin/python3 tools/agent-monitoring/kgmcp_phase3_gateway_runner.py`. No runner code changes
are needed — `_compute_budget_compliance()` (`:398-427`, read this session) already measures
`kgmcp_char_heuristic_v1(json.dumps(response, sort_keys=True))` against the **full** response
payload (never `response["budget_returned"]`), which is exactly the ground-truth measurement Gap 1's
fix is meant to bring into tolerance — the runner needs no awareness of the new
`conflicts_truncated`/`omitted_conflict_count` fields to report correctly, since it measures raw
JSON size regardless of field names. Capture the real new `pass_count`/`of 7` from
`report["aggregate"]["ac2_budget_compliance"]`, and update:
- §21 #12's result line (`docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md:32`,
  currently `**FAIL**, 2/7`) and the detailed `## #12` section (`:110-136`) with the real new
  per-entry table and pass rate — honestly, including if it is still not 7/7. Do not edit the
  historical Q1-Q7 `full_payload_tokens` numbers' framing as if they were always this way; state
  plainly that this is the post-fix re-measurement, dated, distinguishable from the original FAIL
  finding.
- `docs/plans/knowledge-gateway-mcp-proposal.md` — the §21 acceptance-criteria status references to
  "budget tolerance ... FAIL" (investigation.md cites approximate locations around lines
  1502/1521-1523/1581 — confirm exact current line numbers before editing, since this ticket's own
  earlier edits to sibling docs may have already shifted them) get updated to the real new result.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §8 gets a one-line
  addition noting the tolerance is now measured against the full response payload scope
  (statements+context+evidence+conflicts), not statements alone, matching what §21 #12 actually
  measures (unchanged) and what `assemble_within_budget()` now actually bounds (changed).

**Do NOT touch:** `tools/agent-monitoring/kgmcp_phase3_gateway_runner.py` itself, or
`tools/agent-monitoring/kgmcp_baseline_corpus.py` (frozen corpus, read-only per Out of Scope).

**Verify:** the runner's own `report["aggregate"]["ac2_budget_compliance"]` output — not a pytest
test; this is AC2's own measurement-and-disclosure requirement, satisfied by the doc update itself.

### Step 10 — Parity ledger entry

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add a new entry `INFRA-356` (next available ID — confirmed via
`grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml`, current highest is INFRA-355,
this session) documenting this ticket's real behavior change: the widened
`assemble_within_budget()` accounting (Step 1), the new `truncate_conflicts_within_budget()` pass
(Step 2), the new `conflicts_truncated`/`omitted_conflict_count` fields (Steps 3-5), and the Gap 2/
adjacent-gap disclosure-only regression locks (Step 8, explicitly noted as NOT a fix). `status:
verified`, `priority: P1` (matches INFRA-347's own priority for the same subsystem — no P0 upgrade
implied by this ticket). `v2_evidence` must cite the real post-implementation line numbers (derive
these by reading the file fresh after Steps 1-5 land, not by estimating offsets from this plan's
pre-implementation line numbers). `test_path` cites the new tests from Steps 6-8. `support_boundary`
must explicitly state the two things this ticket does NOT do: it does not fix the
`canonical_fragment_hash`-vs-`_content_hash()` parity dedup-identity divergence (Step 8 locks it as
a regression guard only), and it does not add or propose a corpus extension for Gap 2.

Also correct `INFRA-347`'s existing `v2_evidence` string (`:9593-9698` currently, read this session)
in place — a 4th correction, consistent with the 3 already recorded there. Every line-range INFRA-347
cites that falls inside `assemble_within_budget()`, `assemble_packet()`, or the `PacketAssembly`
dataclass will shift once Steps 1-3's new helper functions and fields are inserted; re-read each
cited symbol's real post-implementation location (mirroring the "re-confirmed by direct read of each
cited symbol's real current location this session" methodology INFRA-347's own text already uses for
its 3rd correction) and update the citation numbers, without changing INFRA-347's own substantive
claims (it still correctly describes Phase 3's original dedup/budget-visibility hardening, which this
ticket extends, not replaces).

**Do NOT touch:** any other `docs/parity_ledger/infrastructure.yaml` entry (`INFRA-346`,
`INFRA-348`-`INFRA-355`) — none of them claim ownership of `assemble_within_budget()`'s accounting
scope (confirmed in investigation.md's Parity Ledger Overlap section).

**Verify:** `python3 tools/parity_ledger_validate.py` (or this repo's equivalent schema validator for
`docs/parity_ledger/*.yaml`) reports both the new INFRA-356 entry and the corrected INFRA-347 entry
as schema-valid. Schema requires (`docs/parity_ledger/schema.json`, read this session):
`id`/`text`/`status`/`priority` always; `v2_evidence`+`test_path` when `status` is
`verified`/`divergent`; `test_path` additionally required since this entry's `priority` is `P1`, not
`P0`, so the P0-specific rule doesn't independently force it, but the `verified`-status rule already
does.

## Scope Guards

- Do not touch `tools/knowledge_gateway_router.py` (frozen, already ledgered INFRA-335) or any
  Level 1/Level 2 cache mechanics, cache routing, or `changed_paths` integration in
  `tools/knowledge_gateway_cache.py` — Out of Scope.
- Do not touch `render_candidates()`'s `parity_ledger` block (`:348-386`) or any other part of "the
  Parity adapter" — Out of Scope; the adjacent `canonical_fragment_hash` divergence is
  regression-locked (Step 8), never fixed, in this ticket.
- Do not modify any existing entry in `tools/agent-monitoring/kgmcp_baseline_corpus.py` — Out of
  Scope; this plan proposes no corpus extension at all (Gap 2 closes by disclosure).
- Do not fabricate or add synthetic duplicate-content corpus entries anywhere, and do not present
  any constructed fixture as "corpus-derived" — Scope's explicit prohibition.
- Do not reorder `assemble_packet()`'s fixed `render → dedup → negative-claim → conflicts(build) →
  truncation → §16 fallback` pipeline — every step in this plan inserts new logic inside or after
  Step 8, never before it, and never changes dedup's or conflict-building's own relative position.
- Do not re-open or re-litigate Phase 4 (parity adapter) or Phase 5 (repeated-demand) findings — Out
  of Scope; Step 8's parity regression test observes Phase 4's shipped behavior, it does not
  evaluate or revise Phase 4's own design decisions.
- Do not change `omitted_statement_count`'s definition (`len(statements) - len(included_statements)`)
  — unaffected by this plan; only what drives a statement's inclusion/exclusion changes (Step 1), not
  what the field counts.
- Do not add `additionalProperties: false` to the response schema — its own docstring explicitly
  forbids this (Step 5).
- Never run `pytest tests/` (full suite) for this ticket's own verification — use the scoped
  commands in test_plan.md's "Scoped Pytest Commands" section.

## Dependency Map

- Step 1 has no dependency (self-contained function change).
- Step 2 has no dependency on Step 1 (separate function), but both are prerequisites for Step 3.
- Step 3 depends on Steps 1 and 2 (wires both into `assemble_packet()`/`PacketAssembly`).
- Step 4 depends on Step 3 (needs the new `PacketAssembly` fields to exist).
- Step 5 depends on Step 4 conceptually (documents the same new response keys) but can be done in
  parallel with Step 4's code — both just need to agree on the two field names.
- Step 6 depends on Steps 1-3 (tests the real functions/fields those steps introduce).
- Step 7 depends on Steps 3-5 (tests the response/schema threading).
- Step 8 is fully independent of Steps 1-7 — it locks in *current* (pre-fix and post-fix identical)
  dedup behavior and the parity divergence, neither of which Steps 1-7 touch. Can be done any time.
- Step 9 depends on Steps 1-5 landing and passing (re-measures against the fixed code).
- Step 10 depends on Steps 1-9 all being complete (cites real final line numbers and real test names,
  and documents the real re-measured pass rate from Step 9).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `assemble_within_budget()` genuinely accounts full payload | Steps 1, 2, 3 | `test_assemble_within_budget_accounts_context_and_evidence_bytes_not_just_statement_text`, `test_conflicts_are_measured_against_budget_even_though_real_corpus_never_populates_them` (Step 6) |
| AC2 — real re-measurement of §21 #12 produces honest new pass rate | Step 9 | `report["aggregate"]["ac2_budget_compliance"]` from the re-run (not a pytest test — a doc-recorded measurement) |
| AC3 — truncation of context/evidence/conflicts visibly marked, never silent | Steps 3, 4, 5 | `test_new_truncation_markers_threaded_into_run_knowledge_context_response`, `test_knowledge_context_response_schema_accepts_new_context_truncation_marker_field` (Step 7); `test_budget_returned_reflects_combined_cost_when_context_and_evidence_are_supplied` (Step 6) |
| AC4 — dedup gap genuinely closed or honestly re-confirmed open | Step 8 (disclosure, no fix) | `test_live_corpus_has_zero_cross_provider_content_duplicates_documented_limitation`, `test_parity_ledger_evidence_hash_uses_canonical_fragment_hash_not_content_hash` |
| AC5 — schema-valid parity ledger entry, INFRA-347 citations corrected | Step 10 | `python3 tools/parity_ledger_validate.py` (or repo-equivalent) |

## Anti-Drift Notes

- **`context[]`/`evidence[]` truncation is never independently marked** under this design — a
  statement's context/evidence can only ever be dropped together with the statement itself (the
  architecture already guarantees this 1:1 coupling downstream). test_plan.md's provisional
  `test_context_truncation_produces_visible_marker_distinct_from_statement_truncation` name is
  **reinterpreted** in Step 6/7 as testing `budget_returned`'s widened, real value (proving the
  accounting genuinely changed) rather than a separate boolean — because no scenario exists where
  context/evidence truncates independently of its owning statement under the chosen design. The
  genuinely independent truncation event is `conflicts[]`, which gets its own real
  `conflicts_truncated`/`omitted_conflict_count` markers (Steps 2-5). Do not invent a
  `context_truncated`/`omitted_context_count` field pair that can never be `True` when its paired
  `budget_truncated` is `False` — that would be a dead, always-redundant field, contrary to "typed
  records" discipline (every durable/observable field must carry real, independent information).
- **Two existing tests' `budget_requested` fixture values must change, not their assertions** (Step
  6, item 5) — this is a real, disclosed consequence of a real budget-accounting fix, not scope
  creep or an unrelated test break. Do not "fix" the tests by loosening their assertions instead
  (e.g., changing `omitted_statement_count == 1` to `>= 1`) — that would silently weaken the
  regression lock; recompute the real new boundary value instead.
- **`kgmcp_char_heuristic_v1()` must be called on real field content for every new cost term** —
  never a multiplier on the existing statement-only cost. This governs `_statement_included_content_cost()`
  (Step 1) and `truncate_conflicts_within_budget()` (Step 2) equally; both must be independently
  provable via `test_assemble_within_budget_never_uses_length_times_constant_estimate` (Step 6).
- **Do not let Step 9's re-measurement predict or round up the new pass rate before running it.**
  The runner's real output is the only source of truth for AC2; if it is still not 7/7, report that
  plainly in the doc, matching this ticket's own AC2 wording ("whatever it actually is").
- **Step 8's two new tests are locks, not fixes.** Neither may be satisfied by changing
  `render_candidates()`'s `parity_ledger` block or by adding corpus entries — both changes are
  explicitly Out of Scope. If either test's construction accidentally requires touching either of
  those, stop and re-check the fixture approach rather than widening scope.
- **`INFRA-347`'s corrected citations must be re-derived by reading the real post-implementation
  file, never estimated by adding a guessed line-delta to this plan's pre-implementation numbers**
  (Step 10) — this plan's own line numbers (e.g. `:643-670`, `:726-828`) are accurate as of this
  planning session only and will shift once Steps 1-3 insert new code.

## Deviations (recorded during Implementation)

- **Framing correction (both non-blocking Architecture Review notes, applied):** this plan's own
  Summary section frames Gap 1's fix as options (a) and (b) "collaps[ing] into one design" /
  option (b) being "simultaneously" achieved. Architecture Review found this framing overstates
  things — the real story is a genuine design choice (widen the cost function per-statement,
  including its owned context/evidence) with option (b)'s literal "drop context but keep the
  orphan statement" mechanism explicitly **rejected** as architecturally incompatible, not
  magically satisfied too. All doc/ticket prose written during Implementation (Step 9's doc
  updates, the ticket's own Implementation Notes) uses the corrected "(a) selected, (b) rejected"
  framing, not this plan's original "collapse into one design" language. The code itself
  (Steps 1-3) is unaffected — this is a framing/reporting correction only.
- **Step 9 honesty disclosure (per Architecture Review note 2, applied):** the real post-fix
  re-measurement is reported honestly as still 2/7 (real per-entry payload reduction of 11%-22%,
  not enough to cross the ±20% threshold), with explicit disclosure that the widened accounting
  does not count JSON structural overhead or untouched response fields the real
  `json.dumps(response)` measurement counts — see
  `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`'s "Post-fix
  re-measurement" section.
- **Step 7 test scope, third test discovered (not anticipated by this plan):** Step 6 item 5's own
  file-scoped grep only checked `tests/tools/test_knowledge_gateway_packet_assembly.py` for the
  `budget_requested=kpa.kgmcp_char_heuristic_v1(text_a.strip())` anti-pattern, and Step 7's "Do NOT
  touch" list named `test_knowledge_context_response_schema_accepts_new_budget_marker_field`
  (`tests/tools/test_knowledge_gateway_mcp.py`) as unaffected. This assumption was empirically
  false: that test has the identical anti-pattern and started failing once Step 1 landed, for the
  identical real reason Step 6 item 5 already diagnosed for its two sibling tests. Fixed the same
  way (input constant corrected via real code, assertions unchanged), applying the plan's own
  already-approved Step 6 item 5 reasoning to a test the plan itself missed. See the ticket's own
  Implementation Notes for the exact mechanism (had to derive `text_a`'s isolated cost via
  `render_candidates()` + `_statement_included_content_cost()` directly, not via
  `assemble_packet()`, since that test's monkeypatched `_run_search()` always returns both
  `text_a` and `text_b` together).
- **Step 7, newly discovered pre-existing bug (disclosed, not fixed):** while implementing
  `test_new_truncation_markers_threaded_into_run_knowledge_context_response`, discovered that
  `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json` types
  `conflicts[].automatic_resolution` as plain `"string"`, but every real `Conflict` object
  (`_structural_supersession_signal()`) always sets `automatic_resolution=None` — meaning no real
  code path can ever produce a schema-valid, non-empty `conflicts[]` response. This bug predates
  this ticket, is unrelated to budget/dedup accounting, and was never previously triggered (no
  real corpus entry populates `conflicts[]`, and no prior MCP-level test forced a real conflict
  through `RESPONSE_VALIDATOR.validate()`). Not fixed here — out of this ticket's own scope
  (concerns `automatic_resolution` nullable typing, not budget accounting). The new test works
  around it by deriving its probe cost via a direct `assemble_packet()` call that bypasses
  response-schema validation for the probe only, so the actual asserted response never carries a
  non-empty `conflicts[]`. Flagged for a follow-up ticket.
- **Step 9 required corrective action (disclosed, mirrors documented precedent):** the shared,
  gitignored `knowledge-index/retrieval_cache.db` was deleted before the final measurement run,
  since stale Level 1/Level 2 rows written before this fix landed would otherwise be served as
  cache hits and never exercise the new accounting — this mirrors the exact corrective-action
  precedent already documented in `phase3_pilot_acceptance_measurement.md`'s own "A required,
  disclosed corrective action during Implementation" section from the original measurement.
- **Step 9 side effect (disclosed, not investigated further, out of scope):** the full runner
  re-run also refreshed two criteria unrelated to #12 (`ac4_vs_phase1_cold_pass`, and the AC5
  recall check for `Q7_negative_knowledge`) in the committed fixture JSON. This ticket did not
  investigate or resolve that drift — flagged in the doc's "Overall honest verdict" Update
  paragraph, not silently absorbed.
- **Step 10 skipped, not deferred silently:** per explicit instruction from the driving session,
  Step 10 (the `INFRA-356` parity ledger entry and `INFRA-347` citation correction) was not
  implemented in this Implementer pass — left for the separate Parity phase, consistent with this
  session's established convention. The ticket's AC5 checkbox is left unchecked with this
  reasoning recorded.
