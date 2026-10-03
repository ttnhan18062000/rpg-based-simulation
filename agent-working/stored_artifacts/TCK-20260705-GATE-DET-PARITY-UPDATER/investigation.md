---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-PARITY-UPDATER
artifact_type: investigation
tags: [ai, workflows, determinism]
---

# Investigation — TCK-20260705-GATE-DET-PARITY-UPDATER

## Current Behavior

### `.claude/workflows/implement-ticket.js` — Parity phase (lines 540-608)

```
const parityNoSrcChange = implementation.files_changed.every(f => !f.startsWith('src/'))
const paritySkipEligible = parityNoSrcChange && !implementation.behavior_changed

let parityForceFullRun = false
if (paritySkipEligible) {
  // ... bash() call to tools/parity_ledger_scan.py's find_p0_intersection, direct bash — no agent()
  parityForceFullRun = p0ScanOutput.includes('P0_INTERSECTION_FOUND')
}

if (paritySkipEligible && !parityForceFullRun) {
  log(...); pushEvent('Parity', 'parity-updater', 'skipped', ...)
} else {
  const parity = await agent(
    `Update parity ledger for ticket ${tid}. ...`,
    { label: 'parity-update', agentType: 'parity-updater' }
  )
  const parityTs = ...
  pushEvent('Parity', 'parity-updater', 'ok', parityText.slice(0, 200), parityTs)
}
```

Confirmed facts (all three of the ticket's flagged questions):

1. **The Parity `agent()` call has no `schema:` property today.** Grep of every `schema:` usage in the
   file shows six phases with a schema (`scope`→`TICKET_SCHEMA`, `architecture-review`→`REVIEW_SCHEMA`,
   `implement`→`IMPL_SCHEMA`, `test-scope-and-run`→`TEST_SCHEMA`, `security-review`→
   `SECURITY_REVIEW_SCHEMA`, `done-check`→`DONE_SCHEMA`). `parity-update` (line 602) is the only one of
   the seven `agent()` calls without one — matches the ticket's assumption exactly.
2. **Skip-branch structure is exactly** `if (paritySkipEligible && !parityForceFullRun) { skip } else {
   full agent() call }` (lines 574-608). There is no third branch. Any new static check for this ticket
   belongs strictly inside the `else` block — never inside the `if`, which is TCK-20260705-
   WORKFLOW-PARITY-SKIP's own territory and out of scope to modify (ticket's own Out of Scope line
   confirms this).
3. **The skip branch's own safeguard (`find_p0_intersection`) is a different check from this ticket's.**
   It is a P0-only, evidence-substring-staleness check ("does any P0 entry's `v2_evidence` already cite
   one of the changed files"), run via direct `bash()` (not `agent()`) only when skip-eligible. This
   ticket's new check is a diff-cross-reference for ALL priorities, run only in the full-call branch. The
   two do not overlap or double-count: one gates whether the *skip* is safe; the other gates whether the
   *actual update* was thorough. No conflict.

### `.claude/agents/parity-updater.md` (read in full)

Lists the 8 canonical ledger files with a one-line subsystem description each (`substrate.yaml` → "World
generation, authoritative objects, determinism", etc.) — this is a **conceptual** description, not a
`src/` path mapping. No path-prefix table, no derivation logic. Confirms the ticket's premise: no
existing explicit `src/` → subsystem mapping lives in the agent prompt.

### Existing "mapping-adjacent" signals already in the pipeline (none of them are a deterministic mapping)

- `implementation.parity_subsystems` — `IMPL_SCHEMA` (line 438) already has this field: `{ type: 'array',
  items: { type: 'string' } }`, populated by the **implementer** agent as a self-report, constrained by
  prompt text (line 471) to the 8 canonical names. This is the closest thing to a "mapping" that exists
  today, but it is LLM self-report, not a derived/verifiable fact — exactly what this ticket's static
  check is meant to backstop, not something it can reuse as ground truth.
- `review.parity_entries_affected` — `REVIEW_SCHEMA` (line 367), populated by `architecture-reviewer`, a
  second, independent self-reported "affected entries" signal, also fed into the Parity prompt (line
  588).
- Both signals are shown to the parity-updater agent as *context* today but neither is checked against
  the actual git diff. Recommend (Plan-phase decision, not asserted as final) that the new static check
  treats both as informational only and does not treat either as authoritative for its own pass/fail
  determination — the entire point of a "static" backstop is not to trust self-reports.

### `tools/parity_ledger_scan.py` (read in full — reference module per ticket scope)

- `CANONICAL_LEDGER_FILES` — the 8-file tuple (`faction.yaml` explicitly excluded; confirmed via grep
  that `faction.yaml` has 0 `priority: P0` entries).
- `find_p0_intersection(files_changed, ledger_dir=...)` — substring-scans `v2_evidence` text of P0-only
  entries across the 8 canonical files against a changed-files list; returns `(ledger_filename, entry_id,
  changed_path)` triples. **Not directly reusable for this ticket's purpose**: it has no per-subsystem
  mapping output (it flags P0 staleness, not "which subsystem does this file belong to"), and it is
  scoped to P0 only, whereas this ticket must cover all priorities. The ticket's own scope note ("without
  assuming its exact function signatures fit this different purpose without adaptation") is validated —
  the constant (`CANONICAL_LEDGER_FILES`) is reusable by import; the function is not directly reusable,
  though its shape (iterate 8 files → parse YAML → scan `v2_evidence` string) is the right pattern to
  mirror.

### Deriving a `src/` → subsystem mapping from `v2_evidence` — quantified

Extracted every `` `src/....py` `` path cited in `v2_evidence` across the 8 canonical
`docs/parity_ledger/*.yaml` files:

- 270 total (file, subsystem) citations → **216 distinct `src/` paths**.
- **34 of those 216 paths (~16%) are cited in `v2_evidence` of MORE THAN ONE of the 8 subsystem files.**
  Examples: `src/core/state.py` (6 files), `src/engine/apply.py` (5), `src/observability/
  event_extractor.py` (5), `src/worldbuilding/compiler.py` (4), `src/worldbuilding/schema.py` (3),
  `src/engine/pipeline.py` (3), `src/engine/kernel.py` (3), `src/domains/campaigns/state.py` (3),
  `src/domains/adventure/scoring.py` (3), `src/core/updates.py` (3), `src/content/resolver.py` (3).

This is the single most important structural finding: **a derived mapping cannot be file → one
subsystem; it must be file → set-of-subsystems.** Shared infrastructure files (the authoritative apply
path, kernel, pipeline, event extractor, core state) are legitimately cited as evidence for several
subsystems at once, because one file's behavior spans multiple ledger-tracked concerns. See Risks below
for the consequence this has for the FAIL condition's semantics.

## Mechanics / Engine Constraints

None directly — this ticket is agent-workflow tooling (`.claude/`, `tools/`), not simulation mechanics
code. The only "law" in scope is the parity-ledger entry schema itself (`docs/parity_ledger/` entries:
`id`, `text`, `status`, `priority`, `v2_evidence`, `test_path`, `divergence_note`, `proof_type`) — a
"YAML file touched" fact is a file-level git-diff fact, independent of which specific entry ID inside it
changed. No Mechanics Bible chapter constrains this.

## Parity Ledger Overlap

This ticket does not update any parity-ledger entry itself (it builds tooling *around* the ledger), so
there is no entry ID this work "verifies." Relevant structural facts about the ledger surface it touches:
8 canonical files (`substrate`, `combat_movement`, `strategic_cognition`, `town_resource`, `progression`,
`social_narrative`, `world_dynamics`, `infrastructure`); `faction.yaml` stays excluded (0 P0 entries,
already excluded by the sibling `WORKFLOW-PARITY-SKIP` ticket's `CANONICAL_LEDGER_FILES`). No P0 entry
directly named in this ticket's own scope requires a `test_path` — the new module's own tests (see
`test_plan.md`) are the verification surface instead.

## Prior Work

- **`stored_artifacts/TCK-20260705-GATE-DET-DONE-CHECKER/`** (sibling ticket 1, DONE) — established the
  shared pattern this ticket must follow:
  - Module: `tools/gate_checks/done_checker_static.py` — plain functions returning `(status, evidence)`
    tuples, aggregated by a `run_*()` function returning `list[dict]` with `condition`/`status`/
    `evidence` keys. No argparse/CLI; consumed via `python3 -c "..."`.
  - Schema: `DONE_SCHEMA` (implement-ticket.js line 672) gained a new `verified_by: { type: 'array',
    items: { type: 'string' } }` field with a description explaining it distinguishes static-script-
    sourced conditions from pure LLM judgment (line 680) — direct precedent for this ticket's own
    `verified_by` addition to a new `PARITY_SCHEMA`.
  - Prompt wiring: the agent prompt (lines 696-728) has an explicit "Step 0" instructing the agent to run
    the static script via `python3 -c "..."` and cite its JSON output verbatim for the machine-checkable
    conditions, before judging the rest by hand.
  - Doc update: `docs/ai/agents.md`'s `done-checker` section gained a "Step 0 — static pre-check"
    subsection (lines 112-136) describing the script and the `verified_by` field.
  - Test location: `tests/tools/test_done_checker_static.py` — plain (unmarked, no `pytest.mark`) test
    file, imports directly from `tools.gate_checks.done_checker_static`, includes a coverage-honesty
    positive-control fixture per test per SEQUENCE.md decision 4.
- **`tools/parity_ledger_scan.py`** (from `TCK-20260705-WORKFLOW-PARITY-SKIP`) — established
  `CANONICAL_LEDGER_FILES` and the P0-substring-staleness check pattern; reusable by import for the
  8-file constant, not for its scan function (see above).

## Risks and Open Questions

1. **No existing authoritative `src/` → subsystem mapping.** Confirmed: only self-reported signals exist
   (`implementation.parity_subsystems`, `review.parity_entries_affected`). Must derive fresh from
   `v2_evidence` citations, per the ticket's own scope guidance — validated as the only viable source.

2. **Many-to-many overlap (16% of paths) means the mapping function must return `file → set(subsystems)`,
   not `file → subsystem`.** The FAIL condition's semantics must therefore be decided explicitly: does a
   shared file like `src/engine/apply.py` (cited in 5 of 8 files) require **all 5** ledger files to be
   touched, or does it require **at least one**? Requiring all 5 would make almost any change to a
   shared infra file trigger a wide, likely-spurious FAIL (most single-ticket changes plausibly only
   affect one subsystem's *behavior* even when they touch a file cited broadly as evidence). Requiring
   *any* is much closer to the intent ("this file matters to the ledger; did the agent touch parity at
   all in response") but is also a much weaker check. **Flagging as open — must be resolved at Plan,
   not assumed.** My read of the ticket's own wording ("flag any `src/` file that maps to a subsystem
   YAML but whose corresponding YAML file was NOT touched") suggests per-candidate-subsystem reporting
   (list every unmatched candidate) rather than collapsing to one aggregate boolean, so the LLM verdict
   can decide per-file whether the miss matters — this preserves detail without forcing an all-or-none
   requiring-all semantics baked into the static layer itself.

3. **Coverage gap for files not yet cited anywhere.** A brand-new `src/` file (or an existing file that
   happens to have never been cited as `v2_evidence`) has no mapping entry at all under this
   evidence-mining approach. The check's default for "no mapping found" must be explicit — most
   consistent with the ticket's Out-of-Scope framing (only `verified`/`divergent` status re-decision is
   excluded, not this) is to return `NA` (no ledger subsystem implicated) rather than silently `PASS` or
   silently omitting the file, so the absence of a mapping is visible in `verified_by`/evidence output
   rather than indistinguishable from "checked, no issue" — same anti-silent-failure principle as the
   `check_data_runs_clean` precedent in `done_checker_static.py`, which flags unparsable timestamps
   rather than treating them as automatically clean.

4. **Causality/timing issue — the most significant open question for Plan.** The ticket's scope text
   says the check runs on "the set of parity-ledger files actually touched/modified in the same Implement
   pass" — but at the point the Parity phase's `agent()` call is *about to* execute, the parity-ledger
   YAML files have **not yet** been touched by this ticket (the Implement phase only changes `src/`/
   `tests/`; `parity-updater` is the one who is supposed to touch the YAML files, and it hasn't run yet).
   This means:
   - A check run *before* the `parity-updater` agent call would, by construction, almost always find the
     ledger untouched (nothing has edited it yet) — trivially useless as a pre-flight gate on work not
     yet done.
   - A check run *after* `parity-updater` finishes (comparing the fresh git diff of `docs/parity_ledger/`
     against the derived candidate-subsystem set) is the only version of this check that means anything —
     but that is a **self-check the agent runs at the end of its own turn** (or the orchestrator runs
     after the `agent()` call returns), not something the prompt can "instruct parity-updater to run
     first" in the literal sense of "before doing anything."
   - The AC wording ("instructs parity-updater to run this check first and address any flagged file") is
     most sensibly read as: **first**, at the *start* of its turn, the agent computes the expected/
     candidate subsystem list from `implementation.files_changed` (this part genuinely can and should run
     first — it only needs the diff, not the ledger edits) and uses that as its own todo-list of which
     YAML files it is expected to touch; **then**, as the final step before returning (mirroring
     `done_checker_static.py`'s "Part B" self-check pattern, run after Finalize's own migration), it
     re-derives the candidate list and cross-references it against what it actually edited, reporting any
     miss in `verified_by`/its summary. This is structurally closer to done-checker's Part A + Part B
     split (compute expectations first, self-verify last) than to a single "run once before judging"
     step. **Recommend Plan adopt this two-step framing explicitly** rather than following the AC's
     literal "run first" wording as a single call site — otherwise the check either fires before there's
     anything to check, or doesn't fire at all.

5. **Whether to add `PARITY_SCHEMA` at all vs. surfacing only via `log()`/prose (ticket's own explicit
   open question).** Given the done-checker precedent already establishes `verified_by` as a schema field
   (not prose), and Parity is the *only* remaining phase-agent-call without any schema, adding a minimal
   `PARITY_SCHEMA` (mirroring `DONE_SCHEMA`'s shape: `entries_updated`, `p0_missing_test_path`, `summary`,
   `ts`, `verified_by`) is the more consistent choice and costs little — recommend Plan adopt a schema
   rather than the prose-only fallback, unless there's a reason (not found in this investigation) that
   Parity was deliberately left schema-less.

## Anti-Drift Hazards

- Do not fold the new module into `tools/parity_ledger_scan.py` — SEQUENCE.md decision 1 requires a
  sibling module (`tools/gate_checks/parity_updater_static.py`); `parity_ledger_scan.py` stays scoped to
  its own P0-staleness purpose from `WORKFLOW-PARITY-SKIP`.
- Do not touch the `if (paritySkipEligible && !parityForceFullRun) { ... }` branch or its
  `find_p0_intersection` call at all — explicitly Out of Scope, and a different check with different
  semantics (see Current Behavior point 3).
- Do not re-decide `status: verified`/`divergent` semantics — stays LLM-judged per ticket Out of Scope
  and the idea doc's own table.
- Do not add `faction.yaml` as a 9th canonical file — stays excluded, consistent with
  `CANONICAL_LEDGER_FILES` and the Parity prompt's own file list (implement-ticket.js line 592).
- The mapping-derivation function should be written as a general-purpose, independently importable
  function (not Parity-phase-name-coupled) inside `parity_updater_static.py`, since sibling Ticket 3
  (`GATE-DET-MECHANICS-AUDITOR`) is expected to reuse it rather than deriving a second, possibly-
  inconsistent mapping (SEQUENCE.md Dependency Notes).
- `verified_by` is the same field *name*/shape convention as `done-checker`'s (SEQUENCE.md decision 3),
  but it is a distinct field on a distinct new `PARITY_SCHEMA` — not a shared/global schema object.
- No JS test harness exists in this repo (`package.json` has no test runner; no `.test.js` files found
  anywhere) — `implement-ticket.js` schema/prompt wiring changes have no automated test today (same gap
  as the done-checker ticket before it); verification of the JS-side wiring is manual/structural review
  only. Do not invent a JS test framework to cover this — out of scope and inconsistent with how the
  done-checker ticket was verified.
