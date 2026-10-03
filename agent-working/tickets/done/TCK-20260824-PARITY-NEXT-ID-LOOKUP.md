---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260824-PARITY-NEXT-ID-LOOKUP
phase: done
date: 2026-08-24
tags: [ai, workflows, determinism]
---

# TCK-20260824-PARITY-NEXT-ID-LOOKUP

## Title
Deterministic next-ID and existing-entry lookup helpers for parity-updater's Parity phase

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P1

## Request Summary
`parity-updater`'s ledger updates currently require the agent to manually grep `docs/parity_ledger/*.yaml`
for two purely mechanical facts every Parity phase: (1) whether an entry already exists for the concern
at hand, and (2) what the next available ID is for a given shard when authoring a brand-new entry. Both
are deterministic lookups today done by hand/LLM judgment, wasting turns and risking a wrong "next ID"
guess. Add two small deterministic functions to `tools/gate_checks/parity_updater_static.py` (or a
sibling module if line count warrants a split — see Assumptions) mirroring the exact orchestrator-run
precedent already established by `expected_subsystems_for_files()`: wire the new helper(s) into
`.claude/workflows/implement-ticket.js`'s Parity phase as an additional `bash()` call run *before* the
`parity-updater` agent() call, injected into the agent's prompt as a hint alongside the existing
`Expected parity-ledger files per changed src/ file` line. This is explicitly NOT a new agent — the
`parity-updater` agent role stays exactly as-is; only its injected preamble context grows. Actual
judgment (whether matched content genuinely represents the same concern, whether a new entry is truly
warranted) remains with the agent.

## Scope
- In `tools/gate_checks/parity_updater_static.py` (current size: 119 lines — read the file directly at
  implementation time to confirm whether it is still a reasonable place to add two more functions, or
  whether a sibling module, e.g. `tools/gate_checks/parity_ledger_lookup.py`, is cleaner; either way,
  match the existing module's plain-function/no-argparse/`python3 -c "..."`-only-consumption style):
  1. A function that computes the next available ID for a given shard filename: parse all entries'
     `id` field for that shard, extract the shard's own alphabetic prefix (e.g. `INFRA`) and numeric
     suffix via regex (reuse/mirror `parity_ledger_writer.py`'s existing `_ID_PATTERN` /
     `docs/parity_ledger/schema.json`'s `id` pattern rather than inventing a new one), and return
     `{prefix}-{max+1}` zero-padded to the same width already observed in that shard's existing IDs
     (confirmed via direct inspection this session: IDs are NOT dense — `infrastructure.yaml` has 384
     entries total but its highest observed ID is `INFRA-379` — so "next ID" MUST be computed as
     max-numeric-suffix-plus-one, never entry-count-plus-one).
  2. A function that does a lightweight existing-entry search: given a query string (e.g. a ticket ID,
     function name, or file path) and an optional specific shard, search all entries' `text` and
     `v2_evidence` fields for a case-insensitive substring match, returning matching entry IDs plus a
     short excerpt. Explicitly NOT fuzzy/semantic search — a real, honest substring grep wrapped as a
     reusable function, consistent with this module's already-stated deterministic, non-fuzzy character.
- Add tests for both functions in `tests/tools/test_parity_updater_static.py` (or the sibling test file
  if a sibling module is chosen), following that file's existing fixture/`_write_ledger` helper pattern:
  at minimum, a next-ID test against a shard with ID gaps (proving max-plus-one, not count-plus-one), and
  a search test proving both a hit and a clean miss.
- Wire both functions into `.claude/workflows/implement-ticket.js`'s Parity phase (the full-call `else`
  branch only, around line 1204's `expectedSubsystemsOutput` `bash()` call): add a new orchestrator-run
  `bash()` call in the same phase, same pattern (individually-quoted argv elements, JSON output via
  `python3 -c "..."`, run before the `agent()` call at line 1215), and inject its output into the
  `parity-updater` prompt as an additional hint line, alongside the existing
  `Expected parity-ledger files per changed src/ file` line (~line 1222).
- Check `.claude/agents/parity-updater.md`'s `## Step 0 — Expected-Subsystem Context` section and
  `## What to Do` step 3 (`"If no entry exists for the new behavior: construct a new entry with the next
  available ID for that prefix"`) for whether either now makes an incomplete claim once the new hints are
  injected — update if so, leave alone if not.
- Update `docs/ai/agents.md`'s `parity-updater` section if it names the Step 0 static pre-check
  functions explicitly (it does, per the `GATE-DET-PARITY-UPDATER` precedent) — extend that same
  sentence to name the two new functions, following that same precedent's Step 5/6 pattern
  (`docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md` only if those
  already name the existing static functions explicitly enough that omitting the new ones would be a
  drift — confirm at implementation time rather than assuming all four need edits).

## Out of Scope
- Any new agent role or change to `parity-updater`'s core judgment responsibilities (matching content,
  choosing `status`, writing `divergence_note`, etc.) — stays entirely LLM-judged.
- Re-deriving or changing `expected_subsystems_for_files()` / `cross_reference_touched()` /
  `derive_mapping()` — those stay exactly as shipped by `TCK-20260705-GATE-DET-PARITY-UPDATER`.
- Changing `docs/parity_ledger/schema.json`'s `id` pattern or ID width convention itself.
- Widening the search function into fuzzy/semantic matching — must stay a literal substring grep.
- Any change to `parity_ledger_writer.py`'s write path or validation rules.
- Backfilling/renumbering any existing ledger IDs to close gaps.

## Acceptance Criteria
- [x] A next-available-ID function exists, is callable via `python3 -c "..."` per this module's existing
      convention, and returns `max-numeric-suffix + 1` (not `entry-count + 1`) for a shard with ID gaps —
      proven by a test fixture that reproduces a gapped-ID shard.
- [x] An existing-entry substring-search function exists, is callable the same way, returns entry IDs
      plus a short excerpt for a genuine case-insensitive substring hit, and returns an empty result (no
      false positive) for a query with no match — both proven by tests.
- [x] `.claude/workflows/implement-ticket.js`'s Parity phase (full-call branch) runs a new orchestrator
      `bash()` call before the `parity-updater` `agent()` call and injects its output into the agent's
      prompt as an additional hint line.
- [x] `.claude/agents/parity-updater.md` is updated if its existing Step 0/Step 3 text would otherwise
      make an incomplete claim about what context is injected; left alone with a stated reason if not.
- [x] `docs/ai/agents.md`'s `parity-updater` section names the two new functions, mirroring how it
      already names `expected_subsystems_for_files`/`cross_reference_touched`.
- [x] `pytest tests/tools/test_parity_updater_static.py` (or sibling test file) passes, and
      `node --check .claude/workflows/implement-ticket.js` reports no syntax errors.

## Related Tickets
- TCK-20260705-GATE-DET-PARITY-UPDATER (direct precedent — established `expected_subsystems_for_files`/
  `cross_reference_touched` and the orchestrator-bash-before-agent wiring pattern this ticket reuses)
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR, TCK-20260705-GATE-DET-DONE-CHECKER (sibling gate-determinism
  tickets, same design family — reference only, no scope overlap)
- TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL (built `parity_ledger_writer.py`'s validating write path
  and `_ID_PATTERN` — the ID regex this ticket's next-ID function must mirror, not reinvent)
- TCK-20260731-PARITY-INDEX-IMPORTER / TCK-20260731-PARITY-INDEX-BASELINE / TCK-20260731-PARITY-INDEX-EPIC
  (built the derived parity index tooling — read-only reference, no overlap)

## Related Docs
- docs/ai/agents.md (parity-updater section — Step 0 static pre-check paragraph to extend)
- docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md (Parity phase mentions —
  confirm at implementation time whether each needs a matching edit)
- docs/parity_ledger/schema.json (authoritative `id` field pattern — do not redefine)

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/{investigation,plan,test_plan}.md (direct
  precedent for module shape, test fixture style, and the orchestrator-bash-before-agent wiring)
- stored_artifacts/TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL/{investigation,plan,test_plan}.md
  (`_ID_PATTERN` / validation precedent to reuse)

## Related Code Areas
- tools/gate_checks/parity_updater_static.py
- tests/tools/test_parity_updater_static.py
- .claude/workflows/implement-ticket.js (Parity phase, ~lines 1149-1281)
- .claude/agents/parity-updater.md
- tools/parity_ledger_writer.py (`_ID_PATTERN` reference, read-only)
- docs/parity_ledger/*.yaml (read-only reference for fixture/regex verification)

## Assumptions / Open Questions
- Whether the two new functions belong in `tools/gate_checks/parity_updater_static.py` itself (119 lines
  today, same conceptual module) or a sibling file — left to the implementer's judgment per the request,
  based on the file's actual size/focus at implementation time. Wrong call here doesn't change scope, only
  file layout.
- `layer: ai` chosen per this repo's convention that `layer:ai` means the Claude agent/orchestration
  system, not gameplay AI/cognition — matches the direct precedent ticket's own `layer: ai`.
- Whether `docs/ai/workflows.md`/`system_overview.md`/`ticket-lifecycle.md` need edits is left for
  Investigate/Implement to confirm by checking whether those docs already name the existing static
  functions specifically enough that omitting the new ones would read as stale.
- Assumes the ID width convention is uniform per-shard (zero-padded to match existing width, e.g. 3
  digits) rather than needing to grow past 3 digits for any shard currently near that ceiling — not
  verified for every shard in this scoping pass; implementer should confirm no shard is within striking
  distance of `999` before hardcoding a fixed width.

## Implementation Notes

Kept both new functions in `tools/gate_checks/parity_updater_static.py` — at 203 lines post-change it
is still a single-focus module (src-to-ledger mapping + these two lookups), no clean seam justified a
sibling file.

- `next_available_id(shard_filename, ledger_dir="docs/parity_ledger")`: added a captured-group regex
  `_ID_PATTERN = re.compile(r"^([A-Z]+)-([0-9]{3})$")` that mirrors `tools/parity_ledger_writer.py`'s
  `_ID_PATTERN` (which itself mirrors `docs/parity_ledger/schema.json:9-11`'s `id` pattern), following
  this codebase's established precedent (`parity_ledger_writer.py`'s own docstring) of citing and
  duplicating the source pattern with a comment rather than importing a private cross-module name.
  Walks every entry's `id`, tracks the max numeric suffix (never `len(entries) + 1` — confirmed
  non-dense via `infrastructure.yaml`: 384 entries, highest id `INFRA-379`), and derives prefix +
  zero-pad width from the shard's own matched ids rather than a hardcoded shard→prefix table. Raises
  `ValueError` if no entry in the shard has an id matching `_ID_PATTERN` (per ticket Assumptions: a
  shard with no valid ids has no prefix to derive — genuinely ambiguous, so it raises rather than
  guessing).
- `search_existing_entries(query, ledger_dir="docs/parity_ledger", shard_filename=None)`: plain
  case-insensitive substring match (`str.lower().find`) over `text` and `v2_evidence`, per-shard or
  across all `CANONICAL_LEDGER_FILES`; returns one `{id, shard, matched_field, excerpt}` dict per field
  hit (an entry matching in both fields produces two results). Skips a missing/unparseable shard,
  mirroring `derive_mapping`'s existing legacy-data tolerance. Explicitly not fuzzy/semantic.
- Wired `next_available_id` into `.claude/workflows/implement-ticket.js`'s Parity phase (full-call
  branch): a new `bash()` call runs immediately after the existing `expectedSubsystemsOutput` call,
  reusing its JSON output to derive the distinct candidate shard set (no re-derivation of
  `expected_subsystems_for_files`'s own computation), computing `next_available_id` per shard, and
  catching `ValueError` per-shard into an `"unavailable: <reason>"` string rather than failing the
  phase (this is a hint for the agent, not a gate). Injected as a new
  `Next available ID per candidate shard` line in the `parity-updater` prompt, alongside the existing
  `Expected parity-ledger files per changed src/ file` line. Verified end-to-end against the real
  ledger (`src/core/builder.py`, `src/core/state.py` as inputs) — produced correct `max+1` values for
  every candidate shard, e.g. `INFRA-380` (one past the confirmed `INFRA-379` highest id) at the
  time this smoke test ran. **Post-merge update**: this ticket's own Parity-phase entry, originally
  authored as `INFRA-380`, was renumbered to `INFRA-381` when merging with `origin/main` — a
  concurrent session had independently landed its own, unrelated `INFRA-380` entry
  (`TCK-20260823-CI-STEP-SUMMARY-REPORTING`) in the gap between this ticket's authoring and its
  merge. Confirmed via direct `next_available_id('infrastructure.yaml')` re-run against the merged
  state that `INFRA-382` is the next real available id, i.e. `INFRA-381` was correctly free. This is
  the exact, expected race the function's own docstring already disclaims (it computes against
  whatever local view of the shard is passed to it at call time) — not a bug, and not something a
  single-branch smoke test could have caught before the merge.
- Did NOT wire `search_existing_entries` into the orchestrator flow, per ticket scope (no automatic
  query-string source) — instead documented it in `.claude/agents/parity-updater.md`'s Step 0 section
  as an agent-invoked Bash call, and updated Step 3's "next available ID" line to point back to the
  injected hint / `next_available_id` call.
- `docs/ai/agents.md`'s `parity-updater` section: extended Step 0 to name `next_available_id` (as
  part of the same orchestrator `bash()` step) and added a new paragraph naming
  `search_existing_entries` as an agent-invoked tool, per Acceptance Criteria.
- Judged that `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and `docs/ai/ticket-lifecycle.md`
  each state a specific, factual claim about exactly which static functions run "before the agent
  call" in Step 0 — since `next_available_id` is now a second bash() call also running before the
  agent call, leaving those sentences unchanged would be a real drift (an incomplete claim about what
  Step 0 does), so all three were given a minimal one-clause addition naming `next_available_id`.
  `search_existing_entries` was NOT added to any of the three, since it isn't part of the Step 0
  orchestrator flow those sentences describe.

## Test Summary

Added 6 new tests to `tests/tools/test_parity_updater_static.py`:
- `test_next_available_id_uses_max_suffix_not_count` — 3-entry gapped shard (max suffix 7), proves
  max+1 semantics rather than count+1.
- `test_next_available_id_derives_prefix_and_width_from_shard`
- `test_next_available_id_raises_on_shard_with_no_valid_ids`
- `test_search_existing_entries_finds_case_insensitive_substring_hit`
- `test_search_existing_entries_returns_empty_on_clean_miss`
- `test_search_existing_entries_scoped_to_single_shard`

`.venv/bin/python3 -m pytest tests/tools/test_parity_updater_static.py -q` — 16 passed (10 existing +
6 new), no regressions. `node --check .claude/workflows/implement-ticket.js` — no syntax errors.
Additionally smoke-tested the actual wired `bash()` snippets from `implement-ticket.js` against the
real `docs/parity_ledger/*.yaml` shards (not just the isolated unit tests) to confirm the JSON
piping/quoting between the two `python3 -c` calls works end-to-end.

Full scoped run (`tests/tools/` + the two `agent_orchestration_claude_adapter` structural-
conformance files) found a real, expected consequence: this ticket's +22-line diff to
`implement-ticket.js` shifted `FINALIZE_INCOMPLETE`'s call-site line numbers from `[1507, 1519]` to
`[1529, 1541]`, breaking the same hardcoded-baseline assertion in both
`test_terminal_status_conformance.py:69` and `test_terminal_status_extractor.py:101` — the third
time this exact pattern has recurred in this session (`TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-
SPLIT` and `TCK-20260824-HOTFIX-TERMINAL-STATUS-EXTRACTOR-DRIFT` fixed the first two occurrences).
Independently re-verified the true current value via the real extractor before editing (not just
trusting the failure message), then fixed both files this time — the earlier two incidents each
only caught one of the two sibling files, requiring a follow-up ticket; checking both explicitly
this time avoided that repeat. **This recurring pattern is worth flagging as a real, generalizable
test-design fragility**: both files assert absolute source line numbers for a rapidly-changing
file, so any future edit to `implement-ticket.js` above line ~1500 will break them again — a
follow-up ticket redesigning these two assertions to check something invariant (e.g. "exactly 2
call sites, N lines apart" or a relative-offset check) rather than literal line numbers would
prevent this from recurring a fourth time. Not fixed here — out of scope for this ticket, and a
real test-design change deserves its own ticket, not a drive-by rewrite bundled into an unrelated
feature addition.

Re-ran after the fix: `.venv/bin/python3 -m pytest tests/agent_orchestration_claude_adapter/
test_terminal_status_conformance.py tests/agent_orchestration_claude_adapter/
test_terminal_status_extractor.py -q` — 6 passed, 0 failed.

Full scoped command, independently re-run in full post-fix (not just trusting the test-scoper's
own earlier count): `.venv/bin/python3 -m pytest tests/tools/ tests/agent_orchestration_claude_adapter/test_phase_order_conformance.py tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py -q`
— **2457 passed, 23 FAILED, 23 skipped, 1 xfailed** (674s). The 23 failures are all in
`tests/tools/test_knowledge_search.py` — confirmed pre-existing and environment-caused, not
introduced by this ticket: `huggingface_hub.errors.LocalEntryNotFoundError` (this sandbox blocks
outgoing HuggingFace model-download traffic, a known, documented gap unrelated to
`parity_updater_static.py`/`implement-ticket.js`). None of the 23 failures are in any file this
ticket touched. The 23 "skipped" and 1 "xfailed" are separate, correctly-marked pre-existing
entries — not to be confused with the 23 environment-caused failures above (an easy miscount this
ticket's own draft first got wrong and then corrected after independently re-running the full
command directly rather than trusting the earlier summary).

## Files Changed
- tools/gate_checks/parity_updater_static.py (added `next_available_id`, `search_existing_entries`,
  `_ID_PATTERN`; docstring updated)
- tests/tools/test_parity_updater_static.py (6 new tests)
- .claude/workflows/implement-ticket.js (Parity phase: new `nextIdOutput` `bash()` call, new prompt
  hint line)
- .claude/agents/parity-updater.md (Step 0 section extended; Step 3 line updated)
- docs/ai/agents.md (`parity-updater` section: Step 0 extended, new paragraph for
  `search_existing_entries`)
- docs/ai/ticket-lifecycle.md, docs/ai/system_overview.md, docs/ai/workflows.md (Parity phase Step 0
  descriptions each given a minimal addition naming `next_available_id`)
- tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py,
  tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py — updated the
  hardcoded `FINALIZE_INCOMPLETE` call-site line-number baseline in both sibling files
  (`[1507, 1519]` → `[1529, 1541]`), a direct, expected consequence of this ticket's own +22-line
  diff to `implement-ticket.js` above those call sites. Independently re-verified the true current
  value via the real extractor before editing. The third occurrence of this exact drift pattern
  this session — flagged in Test Summary as a real, generalizable test-design fragility worth its
  own future ticket (redesign to an invariant check, not literal line numbers), not fixed at that
  root cause here.
- docs/parity_ledger/infrastructure.yaml — added a new entry documenting the
  `next_available_id`/`search_existing_entries` functions and their orchestrator/agent wiring
  (pure workflow-tooling entry, same pattern as `INFRA-263`/`264`/`265`/`315`/`379`). Authored by
  dogfooding this ticket's own new functions during the Parity phase as `INFRA-380`; independently
  re-verified via `yaml.safe_load` that no other entry in the shard lost any field in the process.
  **Renumbered to `INFRA-381` during the merge with `origin/main`**: a concurrent session had
  independently authored its own, unrelated `INFRA-380` entry in the interim — a real ID collision
  across branches, not a bug in the new lookup functions (they correctly compute the next-available
  id against whichever local shard state is passed in; two branches computing independently before
  either merges can legitimately collide once one lands first). Resolved by keeping the
  concurrent session's `INFRA-380` as-is and renumbering this ticket's own entry to `INFRA-381`
  (confirmed correct by re-running `next_available_id` against the merged state, which returned
  `INFRA-382` as the next free id).
- tickets/inprogress/TCK-20260824-PARITY-NEXT-ID-LOOKUP.md (this ticket — Implementation Notes, Test
  Summary, Files Changed, Completion Summary, Acceptance Criteria, Status)

## Completion Summary
Added two deterministic helper functions to `tools/gate_checks/parity_updater_static.py` —
`next_available_id` (max-numeric-suffix+1 per shard, reusing the schema's `id` pattern) and
`search_existing_entries` (plain case-insensitive substring search over `text`/`v2_evidence`) — both
covered by new tests. Wired `next_available_id` into `.claude/workflows/implement-ticket.js`'s Parity
phase as a new orchestrator `bash()` call that reuses `expected_subsystems_for_files`'s existing
output to compute per-candidate-shard next-IDs, injected into the `parity-updater` agent's prompt as
a new hint line. `search_existing_entries` was deliberately left un-auto-wired and instead documented
in `.claude/agents/parity-updater.md` as an agent-invoked tool, per ticket scope. Updated
`docs/ai/agents.md`'s `parity-updater` section (mandatory) plus three Parity-phase-describing docs
(`workflows.md`, `system_overview.md`, `ticket-lifecycle.md`) that would otherwise have gone stale on
what Step 0 actually runs.
