---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260720-SKILL-MAPPING-DEDUP
artifact_type: test_plan
tags: [tagging, workflows, skills]
---

# Test Plan — TCK-20260720-SKILL-MAPPING-DEDUP

## Regression Surface

Existing tests that must keep passing after the single-source migration lands, grouped by domain.
All are `unit` (no `integration`/`arena-combat` tests touch this area — this is pure agent/workflow
tooling, not simulation runtime).

- `tests/tools/test_tag_registry.py` — all 21 tests, especially the append-only guarantees:
  `test_add_tag_rejects_duplicate_tag`, `test_add_tag_is_append_only_existing_entries_unchanged`,
  `test_load_registry_raises_on_duplicate_tag`. If Plan chooses resolution (a) (schema widened
  going-forward-only) or (c) (separate location), these must all still pass unmodified. If Plan
  chooses resolution (b) (rewrite the 4 existing rows), `test_add_tag_is_append_only_existing_entries_unchanged`
  and the append-only framing in these tests' docstrings/module docstring become the explicit,
  documented invariant break called for by AC4 — do not leave them silently passing while the
  invariant they encode is quietly violated elsewhere.
- `tests/tools/test_tag_skill_mapping_check.py` — all 10 tests. Their fate depends directly on
  AC3's decision (see New Tests Required below) — either they keep passing as-is (module
  repurposed), or they are explicitly retired/migrated (module removed), never left dangling
  against files that no longer contain independently-maintained copies.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — specifically the tests using
  `_write_tag_registry_fixture()` (lines 58-67, 641, 666, 689) — confirms the dashboard's `tags`
  facet (`ingest.py:51-52`, `sorted(tag_registry.load_registry(...).keys())`) is unaffected by any
  additive schema change to registry entries.
- `tests/tools/test_tag_report.py` — `categorize_tag()` reads only `entry["category"]`
  (`tools/tag_report.py:56-68`); confirms an additive `triggers_skill`-style field (if resolution
  (a)/(b) is chosen) does not break category reporting.
- `tests/tools/test_validate_frontmatter.py` — imports canonical-form/registry constants from
  `tag_registry.py`; confirms none of those imports are renamed/removed by this ticket's changes.

## New Tests Required

Per acceptance criteria (AC numbering follows the ticket body):

- **AC1 (single stored location; editing it changes all 4 consumers' output with zero other file
  edits)**
  - Test name: `test_single_source_change_propagates_to_all_four_consumers` (exact shape depends on
    Plan's chosen mechanism — e.g. if consumers read via a shared Python helper, this is a unit test
    against that helper called once per consumer-format-adapter; if the Node workflows shell out,
    this may need a `subprocess`-invoking integration-style test)
  - Category: unit (or integration if it must actually invoke `python3 -c` subprocess calls from a
    test harness)
  - Verifies: changing exactly one stored value (e.g. one `triggers_skill` field, or one entry in
    the new dedicated location) changes what each of the 4 consumers would compute/emit — the ticket's
    own AC1 wording, "verified by editing the single source and confirming all 4 outputs reflect the
    change with zero other file edits."
  - Location: `tests/tools/test_tag_registry.py` (if mapping lives on registry rows) or a new
    `tests/tools/test_skill_mapping.py`-equivalent (if resolution (c) is chosen — new dedicated
    module).

- **AC2 (debugging's conditional carve-out preserved losslessly)**
  - Test name: `test_debugging_carveout_preserved_in_single_source` (or per Plan's actual function
    names)
  - Category: unit
  - Verifies: the single source encodes the full `(default_skill, carveout_agent, carveout_paths)`
    shape — not flattened to a plain string — and each of the 4 consumers can still reconstruct the
    conditional branch (default `/debugging-strategies` vs. `Agent(subagent_type: "world-debugger")`
    when a `Related Code Areas` path matches one of the 5 carve-out prefixes). Mirrors
    `test_normalize_target_captures_skill_and_carveout_paths` in the existing drift-checker tests —
    reuse its exact expected tuple as a fixture if `tag_skill_mapping_check.py` is repurposed rather
    than removed.
  - Location: same module as the AC1 test.

- **AC3 (tag_skill_mapping_check.py's fate explicitly decided and implemented)**
  - If **removed**: no new test — instead, confirm via `git log`/PR diff that all 10 existing tests
    in `tests/tools/test_tag_skill_mapping_check.py` were deliberately deleted (not left orphaned),
    and that `docs/guidelines/tag_taxonomy.md`'s Scenario 5 row (line 34) is updated to stop
    pointing at a now-deleted module.
  - If **repurposed** (e.g. into "each of the 4 consumers reads the live source rather than
    embedding a literal copy"):
    - Test name: `test_check_consumers_read_live_source_not_embedded_copy` (replacing the current
      `check_tag_skill_mapping_consistency`'s pairwise-compare premise)
    - Category: architecture guard
    - Verifies: each of the 4 (or fewer, if some collapse into a single runtime-read consumer)
      remaining text artifacts either (a) is generated/read from the single source at read time, or
      (b) if it must remain static prose (e.g. `ticket-scoper.md`'s LLM prompt content,
      `ticket_tagging.md`'s human doc), that its rendered content still matches the single source's
      current value — same normalized-comparison approach `normalize_target()` already uses, just
      pointed at 1-vs-N instead of N-vs-N.
    - Location: `tools/tag_skill_mapping_check.py` (repurposed in place) and
      `tests/tools/test_tag_skill_mapping_check.py` (repurposed in place).

- **AC4 (append-only invariant preserved or break explicitly justified/recorded)**
  - Test name: depends on resolution chosen:
    - (a)/(c): no new test needed beyond AC1's — existing `test_add_tag_rejects_duplicate_tag` and
      `test_add_tag_is_append_only_existing_entries_unchanged` already assert the invariant holds;
      confirm they still pass unmodified.
    - (b): `test_add_tag_permits_authorized_rewrite_of_named_legacy_rows` (or similar) — a
      **new, narrowly-scoped** test asserting the rewrite path exists and is restricted to exactly
      the 4 named legacy `process-skill-signal` rows (not a general-purpose update mechanism) —
      plus an explicit update to `test_add_tag_is_append_only_existing_entries_unchanged`'s
      docstring/assertions if its current blanket claim no longer holds.
  - Category: unit
  - Location: `tests/tools/test_tag_registry.py`.

- **AC5 (one of the 3 candidate resolutions, or an explicitly justified 4th, chosen and documented
  during this ticket's own Investigate/Plan)**
  - No pytest test — this is a documentation/decision-record requirement, satisfied by Plan.md's own
    "Decision" section (mirroring `TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK/plan.md`'s "Decision:
    Allowlist as a Disclosed 5th Copy" precedent) plus this ticket's Implementation Notes. Verify by
    manual review at Verify/done-checker time, not by an automated test.

- **AC6 (`docs/guides/ticket_tagging.md`'s "Skill Suggestions From Tags" section describes the
  single source, not a 4th hand-maintained copy)**
  - No pytest test — doc-prose change, verified by manual review (same precedent as the drift-check
    ticket's own AC5/Step 6, which also had "no dedicated automated test for doc prose").

- **AC7 (`docs/ai/agents.md`'s ticket-scoper section reviewed/updated if description no longer
  matches)**
  - No pytest test — doc-prose change, verified by manual review. Note: current text at
    `docs/ai/agents.md:44` already describes the mechanism generically ("skill/agent invocations
    mapped from the ticket's `Process/Skill-signal` tags") without naming the 4-copy implementation
    detail — Plan should confirm whether this line needs any edit at all, or whether it already reads
    correctly under the new single-source mechanism.

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_tag_skill_mapping_check.py -q
python3 -m pytest tests/tools/test_agent_ops_dashboard_ingest.py -q
python3 -m pytest tests/tools/test_tag_report.py tests/tools/test_validate_frontmatter.py -q
```

Combined single-run form for convenience during implementation:

```
python3 -m pytest tests/tools/test_tag_registry.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_tag_report.py tests/tools/test_validate_frontmatter.py -q
```

Never `pytest tests/` — scope stays at `tests/tools/`, the same domain
`TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK`'s own test plan used, per this repo's Testing Rule.

If Plan's chosen mechanism adds any Node-side behavior to `implement-ticket.js`/`create-tickets.js`
(e.g. a `python3 -c` subprocess call), there is no existing JS test harness for these workflow files
in this repo — confirm during Plan whether a smoke-level manual invocation (not a new automated JS
test suite) is the accepted verification method, consistent with how these files are verified
elsewhere (they have no `tests/` coverage today).

## Anti-Drift Test Guards

- **Guard against a silently-flattened `debugging` carve-out.** Any single-source design that
  reduces the carve-out to a plain string (losing the agent + path-set structure) must fail a test —
  this is the direct regression `test_normalize_target_captures_skill_and_carveout_paths` and the
  new AC2 test exist to catch. Do not let a "simpler" single-source schema silently drop this.
  Same for the `src/worldgeneration/`-excluded-mention edge case
  (`test_normalize_target_ignores_excluded_path_mentioned_outside_carveout_list`) — if the single
  source re-derives carve-out paths via regex/parsing rather than storing them as a structured list,
  this exact false-positive risk re-applies and needs its own guard.
- **Guard against `tag_skill_mapping_check.py` becoming dead code that silently always passes.** If
  repurposed rather than removed (AC3), the repurposed check must have a test that can actually fail
  — i.e. inject a real divergence between a consumer's rendered output and the live single source
  and assert the check catches it (mirrors the existing
  `test_check_tag_skill_mapping_consistency_detects_injected_divergence` pattern). A check that
  always trivially passes because it compares a value to itself is worse than no check.
  If **removed** instead, confirm no `python3 -m pytest tests/tools/` invocation still references
  the deleted module (a stale import would fail loudly at collection time, which is an acceptable
  and expected outcome to catch during Implement — not something to suppress).
- **Guard against a new undisclosed hardcoded copy.** If resolution (a) uses a fallback map for the
  4 legacy rows, add or extend a test asserting that fallback map's keys are exactly the 4 known
  legacy tags (`{"api-design", "debugging", "performance", "security"}`) — same shape as
  `KNOWN_TAGS` today — so a future 5th tag added only to the fallback (or only to the registry, and
  missed in the fallback) fails loudly rather than silently diverging. This directly extends
  `tag_skill_mapping_check.py`'s own disclosed-limitation pattern to the new code path.
- **Guard against scope creep into `TCK-20260720-CREATE-TICKETS-TAG-SCOPE-FIX`'s territory.** No new
  or modified test in this ticket's scope should assert on `create-tickets.js`'s tag-*category*
  validation/restriction logic — only on the tag->skill mapping table. If a test touches
  `create-tickets.js`'s Structure-phase category-restriction code path, it has drifted out of scope.
- **Guard against the append-only invariant being weakened project-wide by accident.** If resolution
  (a) or (c) is chosen (invariant preserved), `test_add_tag_rejects_duplicate_tag` and
  `test_add_tag_is_append_only_existing_entries_unchanged` must still pass completely unmodified —
  any edit to those two tests during this ticket's implementation is itself a signal that scope has
  silently drifted toward resolution (b) without the explicit AC4/AC5 sign-off that resolution
  requires.
