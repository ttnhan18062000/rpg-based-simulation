---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT
artifact_type: plan
tags: [ai, mcp, testing]
---

# Implementation Plan — TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT

## Summary

Investigate already ran the real measurement by hand (`staging_artifacts/.../investigate_measurement_script.py`
against `agent-monitoring/events.jsonl` and `tickets/working_log.csv`) and produced two real,
independently-reproducible result sets: 17/521 conservative repeated-demand pairs (primary,
events.jsonl) and 372/1411 (secondary, working_log.csv). Both figures were independently re-derived
during Planning directly from the preserved raw JSON outputs (see "Independent Re-Verification"
below) and match investigation.md exactly. This plan formalizes that one-off measurement into a
committed, reproducible artifact — mirroring Phase 0-4's own `tools/agent-monitoring/kgmcp_phase{N}_
*_runner.py` + `tests/tools/fixtures/kgmcp_phase{N}_*_results.json` + `tests/tools/test_kgmcp_
phase{N}_*.py` pattern — writes the honest results doc and parity-ledger entry the investigation
flagged, and annotates (without overclaiming) the proposal doc's Phase 5 section with the real,
negative-leaning recommendation. No gateway/cache source file is touched anywhere in this plan.

## Independent Re-Verification (Planning phase, before trusting Investigate's numbers)

Re-derived directly from the preserved raw output JSONs in
`staging_artifacts/TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT/`:

- `investigate_events_jsonl_measurement_output.json`: `total_tickets`=521, `conservative_repeated_
  pair_count`=17 (`len(pairs)`=17 confirmed by direct list length, not just the counter field),
  `strong` (shares camel/path)=15, `ref_only`=2, `tag_only_pair_count`=427,
  `distinct_tickets_in_repeated_pairs`=30 → 30/521 = 5.75% (rounds to the reported 5.8%), pairwise
  density 17/C(521,2) = 17/135,460 = 0.01255% (rounds to the reported 0.0126%). All match
  investigation.md exactly.
- `investigate_working_log_measurement_output.json`: `total_tickets`=1411, `conservative_repeated_
  pair_count`=372, `strong_symbol_or_path_pair_count`=282, `tag_only_pair_count_not_counted`=10347,
  `distinct_tickets_in_repeated_pairs`=261 → 261/1411 = 18.4975% (rounds to the reported 18.5%),
  density 372/C(1411,2) = 372/994,755 = 0.03740% (rounds to the reported 0.0374%). All match
  investigation.md exactly.

No discrepancy found. The plan below builds on these numbers as verified fact, not as trusted
investigation output.

## Steps

### Step 1 — Freeze the two input snapshot fixtures

**Files:**
- `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` (new)
- `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` (new)

**Change:** `agent-monitoring/events.jsonl` and `tickets/working_log.csv` are both live,
append-only files that keep growing after this ticket closes (every ticket's workflow appends to
both — see "Other Writers" below). Re-running the measurement against the *live* files later would
silently change the counted numbers and break reproducibility, exactly the failure mode Phase 0-4's
own `tools/agent-monitoring/kgmcp_baseline_corpus.py::CORPUS` frozen-corpus discipline exists to
prevent (confirmed: `CORPUS` is a hand-authored, never-live-queried Python constant, per
investigation.md:26-31). Freeze a point-in-time copy of exactly the rows this ticket's own
Investigate phase measured:
- From `agent-monitoring/events.jsonl`, replicate the extraction in
  `staging_artifacts/.../investigate_measurement_script.py::load_investigate_events()`
  (`investigate_measurement_script.py:106-123`, already read): filter `phase == "Investigate"`,
  dedup to the first event per `run_id`, keep only `{run_id, summary, ts}` per record.
  **Self-contamination guard (Architecture Review 1st pass — required, not optional):** this
  ticket's own Investigate-phase event has *already* landed in the live `agent-monitoring/events.jsonl`
  by the time this Implement step runs (confirmed live during Review: the file already contains
  Scope/Investigate/Plan events for `run_id == "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"`,
  making the raw live-file count 522, not 521). Any ticket whose own methodology is "count
  Investigate-phase summaries across tickets" will structurally self-taint by Implement time, because
  its own mandatory monitoring write is itself one more record in the exact dataset being measured —
  this is a first-class hazard of this measurement design, not a one-off fluke. The extraction MUST
  explicitly exclude `run_id == "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"` (this ticket's
  own ID) via an explicit `if run_id == THIS_TICKET_ID: continue` (or equivalent filter) in the Step 2
  runner's extraction function — never left to incidental timing. Write the resulting list as
  `kgmcp_phase5_events_investigate_snapshot.json`. Verify the written file has exactly 521 records
  (matches `investigate_events_jsonl_measurement_output.json`'s `total_tickets: 521`, independently
  re-confirmed above, and provably excludes this ticket's own run_id) — if the count comes out to 522
  or any value other than 521, the correct fix is to check the exclusion filter, never to silently
  adjust the expected-count assertion to match whatever the live file happens to contain.
- From `tickets/working_log.csv`, extract `{ticket_id, title, summary}` for every row with
  non-empty `title` or `summary` (investigation.md:44-52 states this is `title`+`summary` columns of
  the `timestamp,ticket_id,title,status,summary,artifacts_path` schema). Write as
  `kgmcp_phase5_working_log_snapshot.json`. Verify exactly 1,411 records (matches investigation.md:153
  and the re-verified `total_tickets: 1411` above).

**Do NOT touch:** `agent-monitoring/events.jsonl`, `tickets/working_log.csv` themselves — read-only
sources, copied not modified. Do not snapshot the full raw JSONL lines (which carry many unrelated
fields) — only the three/four fields the measurement method actually consumes, per the cited
extraction functions.

**Other writers to these shared resources (must be accounted for, not silently ignored):**
- `agent-monitoring/events.jsonl` is appended by every ticket's workflow phases via the monitoring
  event recorder (per CLAUDE.md: "Every implement-ticket workflow run... must record... at least one
  event entry to `agent-monitoring/`"). This ticket's own workflow run will itself append new
  Investigate/Plan/etc. events to the live file as it executes — those new events must NOT leak into
  the frozen snapshot. Take the snapshot from the file as it exists as of Step 1's own commit, then
  never re-read the live file for measurement purposes again.
- `tickets/working_log.csv` is appended by every ticket's own "After Work" step (CLAUDE.md: "Append
  to the bottom of `tickets/working_log.csv`"), including this very ticket's own close-out append. As
  with events.jsonl, the frozen snapshot must be taken before this ticket's own working_log.csv
  append happens (i.e., during Implement, not deferred to Finalize) so this ticket's own working_log
  row is never accidentally included in its own measurement's frozen input.

**Verify:** new fixture-shape assertions in Step 3's test file (`len(snapshot) == 521` /
`== 1411`).

### Step 2 — Port the measurement script into a committed runner

**File:** `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` (new)

**Change:** Copy the measurement logic from `staging_artifacts/.../investigate_measurement_script.py`
verbatim where unchanged, specifically:
- `CAMEL_RE`, `_CAMEL_MIN_LEN`, `PATH_RE`, `TICKET_RE`, `PARITY_ID_RE`
  (`investigate_measurement_script.py:41-52`) — unchanged, including the false-positive-preventing
  tightening already applied (lowercase-letter-required CamelCase regex, ≥6-char minimum).
- `INTENT_KEYWORDS`, `normalize()`, `classify_intent()`, `extract_identifiers()`
  (`investigate_measurement_script.py:54-103`) — unchanged.
- `candidate_tags_from_text(*texts: str, root=None) -> set[str]` imported unmodified from
  `tools/registry_query.py:17-30` (confirmed signature by direct read; matches
  `investigate_measurement_script.py:37`'s existing import) — never reimplemented in the new runner.
- Replace `load_investigate_events()`'s live-file read (`investigate_measurement_script.py:106-123`,
  which opens `agent-monitoring/events.jsonl` directly) with a read of Step 1's frozen
  `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json`. Add an equivalent
  `load_working_log_rows()` that reads Step 1's frozen `kgmcp_phase5_working_log_snapshot.json`
  instead of parsing `tickets/working_log.csv` live (the original script's secondary-source logic
  was run ad hoc and not preserved as a named function — the working-log pairwise loop must be
  ported into the same shape as the primary loop, both driven by the same `records`/pairwise-compare
  code path to avoid duplicating the comparison logic twice).
- Run both the primary (events) and secondary (working_log) measurements in one `main()`, writing a
  single combined output fixture: `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_
  results.json` with top-level keys `primary` and `secondary`, each shaped like the existing raw
  outputs (`total_tickets`, `intent_distribution`, `conservative_repeated_pair_count`,
  `strong_pair_count`, `tag_only_pair_count`, `distinct_tickets_in_repeated_pairs`, and a `pairs`
  list — full list for primary (17 entries, small), a `pairs_sample` (first 20) for secondary (372
  entries, to keep the fixture a reasonable size, mirroring `investigate_working_log_measurement_
  output.json`'s own existing `pairs_sample` field name).
- `if __name__ == "__main__": main()`, run once by hand to produce the committed fixture — mirrors
  `INFRA-344`'s own v2_evidence citation of `kgmcp_phase2_gateway_runner.py::main()` as "written the
  committed fixture, run once by hand," not wired into any recurring CI/test-time execution path.

**Do NOT touch:** `tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, or `tools/registry_query.py` (imported only — read,
never edited).

**Verify:** hand-run `python3 tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_
runner.py` and confirm the printed/written numbers exactly match the independently-re-verified
figures above (17/521, 372/1411) before committing the fixture — if the ported runner produces a
different number than the frozen-snapshot input should yield, that is a porting bug to fix before
proceeding, not a number to adjust downstream docs to match.

### Step 3 — Reproducibility and correctness unit tests

**File:** `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` (new)

**Change:** Implement all 5 tests test_plan.md's "New Tests Required" section specifies for this
file, mirroring the AST-inspection / content-hash-snapshot conventions already used in
`tests/tools/test_kgmcp_phase4_direct_tool_comparison.py:1-10` (docstring, already read) as a
pattern to follow, not to copy verbatim (that file tests a live-gateway-calling runner; this one
tests a pure-data-transform runner, so no gateway mocking is needed here):

1. `test_camel_regex_excludes_bare_acronyms_and_digit_joined_tokens` — asserts `CAMEL_RE` does not
   match `INFRA`, `STRAT`, `TOWN`, `TCK`, `E2E`, and does match `EventRecorder`,
   `ResourceNodeUpdate`, `DecisionTraceIndex`.
2. `test_parity_id_regex_extracts_specific_entries_not_bare_prefixes` — asserts `PARITY_ID_RE`
   matches `INFRA-206`/`STRAT-227`/`TOWN-173` but not a bare `INFRA`.
3. `test_intent_classifier_buckets_known_summaries_correctly` — a small fixed table of real
   summaries (drawn from the frozen Step 1 snapshot, e.g. the `TCK-20260619-E22C-REST-API` /
   `TCK-20260702-OBSISO-TRACE-ASYNC` pair — real matched-pair data found in the preserved
   `investigate_events_jsonl_measurement_output.json:31,58-59`, not named in investigation.md's own
   prose) classify into the expected bucket.
4. `test_repeated_pair_requires_same_intent_and_specific_identifier_not_tag_alone` — two synthetic
   records sharing only a tag are NOT counted; two sharing intent + a specific identifier ARE.
5. `test_phase5_measurement_reproduces_committed_fixture_counts` — re-runs `main()` (or the
   underlying pure functions) against the frozen Step 1 snapshot fixtures and asserts the output
   exactly equals the committed `kgmcp_phase5_repeated_demand_measurement_results.json` counts (17
   primary / 372 secondary conservative pairs, 521 / 1411 total tickets, 30 / 261
   tickets-involved) — this is the load-bearing reproducibility guarantee the ticket's own scope
   requires (re-running produces the same real numbers, not a one-off side effect).
6. `test_events_snapshot_excludes_this_tickets_own_run_id` (Architecture Review 1st pass, required)
   — asserts the committed `kgmcp_phase5_events_investigate_snapshot.json` fixture contains zero
   records with `run_id == "TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT"` — the permanent,
   checkable guard against the confirmed-live self-contamination hazard (this ticket's own mandatory
   Investigate-phase monitoring write landing in the exact dataset it measures).

Also add the two anti-drift guard tests test_plan.md's "Anti-Drift Test Guards" section names:
- an assertion that `candidate_tags_from_text` is *imported* (via `ast` module inspection of the
  runner's import statements, mirroring `test_kgmcp_phase4_direct_tool_comparison.py`'s own `ast`
  usage) rather than reimplemented in the new runner file.
- an assertion that the frozen snapshot fixtures' record counts (521 / 1411) are read from the
  committed snapshot files, not from a live re-open of `agent-monitoring/events.jsonl` /
  `tickets/working_log.csv` (guard against a future edit accidentally reverting Step 2's live→frozen
  swap).

**Do NOT touch:** any existing test file under `tests/tools/test_kgmcp_phase*.py` or
`tests/tools/test_registry_query.py` / `tests/tools/test_tag_registry.py` — those must stay green,
unmodified, per test_plan.md's Regression Surface.

**Verify:** `pytest tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py -v` all green, plus
re-run of the full Regression Surface command from test_plan.md's Scoped Pytest Commands section.

### Step 4 — Real results doc

**File:** `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` (new)

**Change:** Create the doc, mirroring `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_
tool_comparison.md:1-20`'s structure (frontmatter, "Source ticket" line, headline-result heading,
data table/breakdown) — already read as the structural precedent. Required content, stated plainly
per this ticket's own honest-framing requirement:

- Frontmatter: `status: active`, `layer: ai`, `authority: P1`, `audience: agent`,
  `tags: [ai, mcp, testing]` (mirrors the sibling phase docs' frontmatter shape).
- `# Knowledge Gateway MCP — Phase 5 Repeated-Demand Measurement Results`.
- "Source ticket: `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT`" line, one sentence on what
  question this measures (real repeated/semantically-equivalent question demand across this repo's
  own historical Investigate-phase and ticket-log text) and what it does not (it is not a gateway
  call-site measurement — no `tools/knowledge_gateway_*.py` file was touched).
- **Data source and method** section: both real sources used (primary: `agent-monitoring/
  events.jsonl` Investigate-phase summaries, 521 distinct tickets; secondary/corroborating:
  `tickets/working_log.csv`, 1,411 tickets), the 4-signal conservative equivalence method (normalize
  → extract identifiers [tags/CamelCase symbols/file paths/ticket+parity IDs] → classify intent [6
  buckets] → require same-intent AND shared-specific-identifier, never tag-alone), and the disclosed
  CamelCase-regex false-positive bug caught and fixed mid-measurement (748→372 secondary-source
  correction, per investigation.md:259-268).
- **Real numbers** section, stated as a table: primary 17/521 pairs (15 strong symbol/path, 2
  ticket/parity-ID-only), 30/521 tickets involved (5.8%), pairwise density 0.0126%; secondary
  372/1411 pairs (282 strong), 261/1411 tickets involved (18.5%), pairwise density 0.0374%; 427
  primary / 10,347 secondary tag-only pairs explicitly reported as NOT counted.
- **Qualitative reading** paragraph: state plainly that the large majority of matched pairs are
  natural incremental/sequential investigation of an evolving codebase, not literal same-question
  recurrence — cite the `TCK-20260619-E21B-REGEN-SERVICE` / `TCK-20260806-PUSH-SHAPER-DEFERRED-
  INSTRUMENTATION` example and the `TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`/`-UNDISCLOSED`
  counter-example from investigation.md:172-179.
- **Cross-reference to Phase 3/4 economics** section, stating plainly (mirrors investigation.md:228-
  255): Phase 3's real FAIL on budget-tolerance (2/7) and on the token half of criterion #18 (a
  genuine Level-2-warm cache hit's own median token count, 2865, is *larger* than both baselines);
  Phase 4's real 7/7 negative gateway-vs-direct-tool comparison. State the reasoning explicitly: a
  broadened-match Phase 5 hit would reach the *same* cache/packet machinery already measured
  unfavorable, so there is no evidence a broadened hit performs any differently — it would very
  plausibly reproduce the same FAIL/negative outcome more often, not resolve it.
- **Recommendation** section, stated as the literal sentence: "Proceed with Phase 5's remaining two
  bullets (canonical entity IDs/aliases; conservative semantic candidate matching) only after Phase
  3's own disclosed gaps (budget-tolerance FAIL; token-count regression on a genuine cache hit)
  close — not now, not never." Do not soften this into "proceed" or harden it into "never."
- A closing line explicitly stating this doc's own real finding does NOT itself declare Phase 5
  built, does not modify any gateway source file, and does not authorize or block any future
  child ticket — mirrors `phase4_direct_tool_comparison.md`'s own closing-disclaimer convention
  ("does not characterize... nor does it declare Phase 4 complete").

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`,
`phase4_direct_tool_comparison.md`, `phase4_workflow_recommendation.md` — read as structural
precedent only, not edited.

**Verify:** Step 5's doc-structure and doc-vs-fixture content-lock tests.

### Step 5 — Doc-structure and no-overclaim tests

**File:** `tests/docs/test_phase5_repeated_demand_measurement_doc.py` (new)

**Change:** Two tests, mirroring `tests/docs/test_redaction_retention_policy_doc.py:1-9`'s static
doc-structure-assertion pattern (already read: asserts required headings/phrases present via plain
string containment, never runtime behavior):

1. `test_infra_355_parity_entry_matches_committed_measurement_numbers` — reads both the new
   `docs/parity_ledger/infrastructure.yaml` `INFRA-355` entry (Step 6) and the committed
   `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` (Step 2), asserts
   the entry's stated numbers (17/521/5.8%, 372/1411/18.5%) are byte-consistent with the fixture —
   never independently hand-typed and liable to drift.
2. `test_phase5_proposal_doc_annotation_does_not_overclaim_done` — reads
   `docs/plans/knowledge-gateway-mcp-proposal.md`, asserts the literal strings `"Add canonical
   entity IDs and aliases. **Done"`, `"Reuse results across compatible phrasings. **Done"`, and `"Add
   conservative semantic candidate matching with deterministic validation. **Done"` are absent (none
   of Phase 5's 3 bullets may be marked Done, since nothing was built), while a real string
   confirming the added narrative paragraph exists (e.g. containing `TCK-20260816-KGMCP-P5-REPEATED-
   DEMAND-MEASUREMENT` within the Phase 5 section) is present.

**Do NOT touch:** `tests/docs/test_redaction_retention_policy_doc.py`,
`tests/docs/test_phase4_workflow_recommendation_doc.py` — read as precedent only.

**Verify:** `pytest tests/docs/test_phase5_repeated_demand_measurement_doc.py -v` green.

### Step 6 — `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 5 annotation

**File:** `docs/plans/knowledge-gateway-mcp-proposal.md`

**Change:** The Phase 5 section currently reads (lines 1451-1455, already read):
```
### Phase 5: Entity-Aware Reuse

- Add canonical entity IDs and aliases.
- Reuse results across compatible phrasings.
- Add conservative semantic candidate matching with deterministic validation.
```
None of the 3 bullets get a `**Done** (`TCK-...`)` inline annotation — nothing was built; this
ticket is measurement-only, per its own Out of Scope. Instead, add a narrative paragraph
**after** the 3-bullet list and **before** the `### Phase 6` header (line 1457), mirroring the
existing Phase 3 precedent at lines 1354-1364 ("Completion of Phase 3 is the first
production-capable pilot boundary... `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` performed
the first real measurement of this boundary's §21 Pilot Acceptance Criteria... This measurement does
not itself declare Phase 3 production-capable...") — a factual, non-overclaiming pointer paragraph,
not a bullet annotation. Content: state that
`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` performed the first real measurement of
repeated/semantically-equivalent question demand for this phase (17/521 primary, 372/1411
secondary conservative pairs; see
`docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` for full
detail), found a small, mostly-non-literal, real signal, and — cross-referenced against Phase 3/4's
own already-measured unfavorable per-hit economics — recommended proceeding with the remaining two
bullets only after Phase 3's own disclosed gaps close, not now. State plainly that this paragraph
does not itself declare any Phase 5 bullet built, and does not authorize or block a future child
ticket.

Placing the paragraph after the bullet list (not interleaved into individual bullets) means a
*future* child ticket that eventually builds and marks one bullet `**Done** (`TCK-...`)` can do so
without needing to touch or restructure this paragraph — the two edits are additive and
non-conflicting by construction.

**Do NOT touch:** the bullet list's own 3 lines (wording unchanged), any other `### Phase N` section,
§11.2, §18.1, §21.

**Other writers to this shared doc:** every Phase 0-4 ticket in this same epic family has previously
edited this same file's own per-phase sections (confirmed: Phase 3/4 bullets carry inline
`**Done** (`TCK-...`)` annotations from their own respective tickets, lines 1302-1449). This ticket's
edit is scoped to only the Phase 5 section (lines 1451-1456) and does not touch any other phase's
already-landed annotations — no collision with prior tickets' edits, since those are already merged,
static text elsewhere in the file.

**Verify:** Step 5's `test_phase5_proposal_doc_annotation_does_not_overclaim_done`.

### Step 7 — `docs/parity_ledger/infrastructure.yaml` `INFRA-355` entry

**File:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry (schema confirmed at `docs/parity_ledger/schema.json`: `id` pattern
`^[A-Z]+-[0-9]{3}$`, `required: [id, text, status, priority]`; `status in {verified, divergent,
missing, unsupported, legacy_verified}` and if `status` is `verified`/`divergent` then `v2_evidence`
and `test_path` are also required strings). Next available ID confirmed by direct `grep -o
"INFRA-[0-9]*" docs/parity_ledger/infrastructure.yaml | sort -n | tail` re-run during Planning: max
existing is `INFRA-354`, so `INFRA-355` is correct and still free as of this plan.

- `id: INFRA-355`
- `status: verified`
- `priority: P2` — decided here (test_plan.md/investigation.md left this open as "P1 or P2"): P2 is
  chosen because this entry's closest precedent is `INFRA-353` (Phase 4 workflow-recommendation
  evaluation — an evaluation-only ticket where no code/capability was built, P2), not `INFRA-344`
  (a live-gateway-calling measurement runner with dual-signal cache-hit verification, P1). This
  ticket's runner is a pure offline data-transform over frozen text, closer in kind to INFRA-353's
  evaluation than INFRA-344's live-system measurement.
- `text`: states, per the `INFRA-344`/`INFRA-353` "certifies methodology not conclusion" precedent
  (both entries' own `text` fields, already read, explicitly state "This entry certifies the
  measurement tool itself as real, correct, and tested — it does NOT claim the measured... performance
  succeeded" / "does NOT certify that any particular workflow integration is correct or beneficial"):
  this entry certifies that (a) a real, non-corpus, non-synthetic data source was used and
  justified over the rejected retro-aggregate source, (b) the equivalence-detection method
  genuinely mirrors §11.2's conservative multi-signal shape (never string-only, never
  embedding-only), (c) the measurement is genuinely reproducible (re-running the committed runner
  against the frozen committed snapshot reproduces the exact 17/521 and 372/1411 numbers, per Step
  3's test), and (d) the real, honest count/rate was reported without adjustment. It does NOT
  certify that Phase 5 is warranted or that the recommendation itself is correct — that is a
  separate, later, human-reviewer call, exactly as `INFRA-344`/`INFRA-353` draw the same line for
  their own respective tickets.
- `v2_evidence`: cites `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`
  (Step 2), `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json` (Step 2),
  `tests/tools/fixtures/kgmcp_phase5_events_investigate_snapshot.json` /
  `kgmcp_phase5_working_log_snapshot.json` (Step 1), and
  `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md` (Step 4).
- `test_path`: `"tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py,
  tests/docs/test_phase5_repeated_demand_measurement_doc.py"` (both new test files, comma-separated
  string, mirroring `INFRA-344`'s own descriptive multi-clause `test_path` string style).
- `proof_type: regression`
- `support_boundary`: the same "certifies methodology, not conclusion" sentence as `text`, mirroring
  `INFRA-353`'s own populated `support_boundary` field (already read) rather than leaving it null.
- `divergence_note: null` (status is `verified`, not `divergent` — no divergence declared).

**Do NOT touch:** any existing `INFRA-*` entry (append-only ledger; no existing entry edited or
reordered).

**Other writers to this shared resource:** `docs/parity_ledger/infrastructure.yaml` is appended to
by every KGMCP-family ticket in this epic (INFRA-339 through INFRA-354 so far, one entry per child
ticket). Re-confirm the max existing ID immediately before appending (not just trust this plan's
already-confirmed `INFRA-354`), in case another ticket lands first — if `INFRA-355` is already
taken by the time Implement runs, use the next free ID instead and update every cross-reference in
Steps 4/5/6 to match.

**Verify:** `docs/parity_ledger/schema.json`-validation (however this repo's existing CI/lint step
validates the ledger — reuse it, do not hand-write a bespoke validator), plus Step 5's
`test_infra_355_parity_entry_matches_committed_measurement_numbers`.

## Scope Guards

Directly from the ticket's Out of Scope and investigation.md's Anti-Drift Hazards — this plan must
not:
- Build any part of Phase 5's canonical-entity-ID, alias-consolidation, or semantic-candidate-
  matching machinery. Nothing under `tools/knowledge_gateway_*.py` is created or modified by any
  step.
- Modify `tools/knowledge_gateway_cache.py`, `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or any other gateway/cache/router source file.
- Close Phase 3's own two disclosed gaps (budget-tolerance FAIL; dedup never real-corpus-proven) —
  referenced as context only.
- Make the Knowledge Gateway a mandatory phase, gate, or ticket step in any workflow — no
  `.claude/workflows/*.js`, `.claude/agents/*.md`, or `.claude/skills/*/SKILL.md` file is touched by
  any step.
- Round the 5.8%/18.5% figures up into "demand is proven" or down into "no demand exists" — the
  results doc (Step 4) and parity entry (Step 7) must state the real, mixed figures plainly.
- Reuse the pre-regex-fix 748-pair number anywhere — only the corrected 372 (and 17 primary) numbers
  are used in any committed artifact.
- Mark any of proposal §20 Phase 5's 3 bullets `**Done**` — nothing was built.
- Treat the new `INFRA-355` entry as certifying that Phase 5 is warranted — it certifies methodology
  only, per Step 7's explicit `text`/`support_boundary` wording.
- Edit `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md`.

## Dependency Map

- Step 1 (frozen snapshots) must land before Step 2 (runner reads them) and before Step 3 (tests
  exercise the runner against them).
- Step 2 (runner + committed results fixture) must land before Step 3 (tests assert against the
  fixture), Step 4 (doc cites the fixture's numbers), and Step 7 (parity entry cites the fixture's
  numbers).
- Step 4 (results doc) must land before Step 5's doc-vs-fixture content-lock test, and before Step 6
  (proposal paragraph references the doc's path).
- Step 6 and Step 7 are independent of each other but both depend on Step 2/Step 4.
- Steps 3 and 5 are both verification steps and can be written in either order relative to each
  other, but both require their respective upstream artifact (Step 2's fixture; Step 4's doc, Step
  6's paragraph, Step 7's entry) to exist first.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: A real, existing, non-corpus data source is used, with explicit reasoning for why it's a valid real signal | Already satisfied by Investigate (events.jsonl primary, working_log.csv secondary, retro/ rejected — investigation.md's "Candidate source" subsections); formalized into the frozen snapshots by Step 1 | Step 3's `len(snapshot) == 521 / 1411` assertions; Step 4's "Data source and method" section |
| AC2: The equivalence-detection method mirrors §11.2's conservative, multi-signal approach (never raw-string-only or embedding-only) | Step 2 (ports the 4-signal method unchanged); documented in Step 4 | Step 3 tests 1, 2, 4 (`test_camel_regex_excludes_bare_acronyms...`, `test_parity_id_regex_extracts_specific_entries...`, `test_repeated_pair_requires_same_intent_and_specific_identifier_not_tag_alone`) |
| AC3: The real count/rate is reported honestly, including a null/negative result if that's what the data shows | Step 4 (results doc states 17/521, 372/1411, and the qualitative "mostly not literal repeats" reading plainly); Step 6 (proposal paragraph states the same real numbers, no rounding) | Step 5's `test_infra_355_parity_entry_matches_committed_measurement_numbers`; Step 3's `test_phase5_measurement_reproduces_committed_fixture_counts` |
| AC4: The recommendation explicitly cross-references Phase 3/4's real per-hit-economics findings rather than treating repeated-demand alone as sufficient | Step 4's "Cross-reference to Phase 3/4 economics" section (cites the real FAIL/2-7 and 7/7 negative findings by file path); Step 6's proposal paragraph restates the same cross-reference briefly | Step 5's doc-structure test (asserts the doc contains the Phase 3/4 file-path citations — extend `test_phase5_proposal_doc_annotation_does_not_overclaim_done`'s sibling assertions if a dedicated check is added, or cover via a plain string-containment assertion in the same test file) |
| AC5: A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added, certifying methodology not the recommendation's conclusion, mirroring `INFRA-344`/`INFRA-353` | Step 7 | Step 5's `test_infra_355_parity_entry_matches_committed_measurement_numbers`; ledger schema validation |

## Anti-Drift Notes

- **Numbers are locked.** Every committed artifact (runner output fixture, results doc, proposal
  paragraph, parity entry) must state exactly 17/521 (primary) and 372/1411 (secondary) — these were
  independently re-verified during Planning directly from the raw JSON outputs, not merely copied
  from investigation.md's prose. Any discrepancy discovered during Implement between the ported
  runner's fresh output and these numbers is a porting bug in Step 2 to fix, never a downstream
  number to adjust to match a buggy re-implementation.
- **The frozen-snapshot discipline (Step 1) is load-bearing, not optional.** Both
  `agent-monitoring/events.jsonl` and `tickets/working_log.csv` are live, growing files that other
  tickets — including this ticket's own close-out `working_log.csv` append — write to continuously.
  If Implement skips freezing snapshots and instead points the runner at the live files, the
  "reproducible" test (Step 3, test 5) will pass today and silently start failing (or silently
  producing different numbers with no failure at all, if the assertions aren't tight) the moment any
  other ticket closes. Freeze first, wire the runner to the frozen copy only.
- **`INFRA-355` certifies methodology, not the "wait" conclusion.** Do not let Parity phase (or any
  later reader) treat the existence of a `verified` parity entry as evidence that Phase 5 should
  eventually be built — Step 7's own `text`/`support_boundary` wording explicitly disclaims this,
  mirroring `INFRA-344`/`INFRA-353`.
- **Epic-closure reasoning (for Parity/Completion Summary phase — do not re-derive, cite this
  directly):** the parent epic, `tickets/todos/knowledge-gateway-mcp-phase5/TCK-20260816-KNOWLEDGE-
  GATEWAY-MCP-PHASE5-EPIC.md`, already explicitly anticipates and accepts this exact kind of outcome
  as a complete, valid epic result. Its own Scope states: "If the first child ticket's own honest
  measurement does NOT find real demand: this epic's real, honest deliverable is that finding
  itself, reported plainly — mirroring `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION`'s
  own precedent... The remaining two candidate child tickets are scoped only if warranted, not built
  regardless." Its own AC8 states: "if it finds insufficient demand, the epic closes honestly on
  that single finding without needing to build anything further, and this is treated as full
  success, not an incomplete epic." This ticket's real finding — a small, real, mostly-non-literal
  signal that is explicitly *insufficient to justify Phase 5's investment right now*, per this
  ticket's own AC1 wording ("insufficient to justify Phase 5's investment") — falls squarely within
  that anticipated outcome, even though it is phrased as a conditional deferral ("only after Phase
  3's gaps close") rather than a flat "no demand at all." This ticket's own Completion Summary
  (written in Parity phase) should state plainly that the epic may close on this single finding, per
  its own AC8, without scoping the remaining two candidate child tickets now.
- **False-positive discipline.** Investigate already caught and fixed a real false-positive bug in
  its own CamelCase regex (748→372 secondary-source pairs) mid-measurement. Step 3's tests 1/2 exist
  specifically to prevent this exact class of regression recurring silently if the regex is ever
  touched again in the future.

## Deviations (recorded during Implement)

- **Steps 6-7 were not executed by this Implement pass**, per an explicit instruction from this
  session's orchestration establishing a per-phase ownership convention for this ticket: Step 6
  (proposal-doc Phase 5 annotation) belongs to Document-Update, and Step 7 (`INFRA-355` parity
  entry) belongs to Parity phase — neither is Implement's job in this session's pipeline split.
  This is a deviation from this plan's literal Step-6/7 assignment to "Implement," not from the
  plan's *content* — Step 6's and Step 7's own specified content (the exact narrative paragraph
  text, the exact `INFRA-355` field values) is unchanged and should be applied verbatim by
  whichever later phase executes them. Step 5's two doc-vs-artifact tests were still written now
  (per plan), and both currently fail exactly because Steps 6/7 have not yet landed — this is
  disclosed in the test file's own module docstring and in the ticket's Implementation
  Notes/Acceptance Criteria, not silently worked around.
- **Minor additive field**: the Step 2 runner's per-source output dict includes one extra key not
  listed in Step 2's enumerated shape, `ref_only_pair_count` (count of conservative pairs whose only
  shared identifier is a ticket/parity ID, no shared code symbol or file path) — a straightforward
  derivative of data the runner already computes (mirrors the investigation's own console-reported
  "ref_only" breakdown), added for the results doc's own "15 strong / 2 ref-only" table row. It does
  not replace or alter any of the fields Step 2 did specify.
