---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-DOCS-SWEEP
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, documentation, claude-md]
---

# TCK-20260903-MONITORING-DATA-DOCS-SWEEP

## Title
Update docs, `CLAUDE.md`, `.gitattributes`, and workflow/skill prose to describe the unified per-week
`agent-monitoring/data/` layout, correcting the prior epic's already-stale `CLAUDE.md` claims

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child 7 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`, implementing the requester's explicit
instruction to also update "the rule, skill and related configuration." Confirmed via direct grep
this session:

- **`CLAUDE.md` itself is already stale today**, from the *already-shipped* prior tools-only epic,
  independent of this epic's own changes: line 94 ("Always stage `agent-monitoring/` (including
  `tools.jsonl`)... the monitoring tools auto-update `tools.jsonl` on every run") — factually wrong,
  the hook has written to a shard directory since 2026-09-02; lines 137/140 ("`agent-monitoring/
  tools.jsonl` is rewritten by a hook on nearly every tool call" plus an example command chaining
  `git add agent-monitoring/tools.jsonl`); line 254 (DoD checklist literally naming
  `agent-monitoring/runs.jsonl`/`agent-monitoring/events.jsonl`). These need fixing regardless of
  this epic landing, and additionally need to describe the new unified `data/` layout once it does.
- `docs/agent-monitoring/README.md` — confirmed already updated for the `tools` source by the prior
  epic (e.g. line 19's `tools/tools-YYYY-Www.jsonl` naming, lines 20-21's logical shorthand kept),
  but still correctly (for today) describes `runs.jsonl`/`events.jsonl` as single files — needs
  updating to the unified `data/YYYY-Www/{runs,events,tools}.jsonl` shape.
- `docs/agent-monitoring/schema.md` — per-source sections (beyond child 1's minimal write-path
  paragraph edits), the staleness-check description, and the Join Example Python snippet (confirmed
  this session to literally do `Path('agent-monitoring/runs.jsonl')`-style single-file reads).
- `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md` §6.
- `.gitattributes` — currently has, post children 1-2, one unified glob for the new layout plus
  (removed by child 2) none of the 3 legacy lines; confirm final state matches the target shape and
  no dangling reference remains.
- `.claude/workflows/implement-ticket.js` — confirmed this session to have **no functional file I/O**
  on these paths (delegates entirely to the Python tools) but has prose-only references inside
  template strings at multiple lines (confirmed: ~48-49, 269, 365, 369, 385, 563, 572, 1706) that
  should be corrected for accuracy even though no functional JS change is required.
- `.claude/skills/agent-monitoring-retro/SKILL.md` — check for path references (not yet checked this
  session).
- `docs/parity_ledger/infrastructure.yaml` `INFRA-291` — the entry the prior epic's consumer-migration
  child updated for the tools-only cutover; needs a further addendum for this epic's unification,
  via `tools/parity_ledger_writer.py::write_entry()` only, **never a raw YAML edit** (CLAUDE.md hard
  rule; the addendum pattern for this exact entry is already established by the prior epic).

## Scope
- Update every doc/config file named above to describe `agent-monitoring/data/YYYY-Www/{runs,events,
  tools}.jsonl` as the current physical layout, replacing every remaining reference to any of the 3
  retired shapes (monolithic `runs.jsonl`/`events.jsonl`, or the prior epic's `tools/tools-YYYY-
  Www.jsonl`) — except where a doc is deliberately describing historical/legacy shape in a "how we
  got here" note, which should stay accurate to history, not be rewritten away.
- Fix `CLAUDE.md`'s already-stale claims (lines 94, 137, 140, 254) as part of the same pass.
- Update `.gitattributes` if children 1/2 left anything inconsistent (confirm, don't assume clean).
- Add the `INFRA-291` addendum via `tools/parity_ledger_writer.py`.
- Run `make knowledge-index-update` at the end, per CLAUDE.md's "After Work" rule (docs were
  modified).

## Out of Scope
- Any functional code change — this ticket is docs/config/prose only.
- `.claude/workflows/implement-ticket.js`'s actual JS logic — confirmed no functional file I/O exists
  on these paths; only its template-string prose changes.
- Any new parity ledger entry beyond `INFRA-291`'s addendum, unless investigation finds this epic's
  changes genuinely require a new entry (unlikely — physical layout change, not a mechanics/behavior
  change) — document the finding either way.
- Rewriting any doc's historical/"how we got here" framing of the prior epic's tools-only shape into
  something that never happened — history stays accurate, only "current state" claims are corrected.

## Acceptance Criteria
- [x] Grep for `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and
      `agent-monitoring/tools/tools-` across `docs/`, `CLAUDE.md`, `.gitattributes`,
      `.claude/workflows/implement-ticket.js`, and `.claude/skills/` returns zero hits describing
      current physical layout (historical/"how we got here" references, if any, are excluded and
      individually justified).
- [x] `CLAUDE.md` lines 94, 137, 140, 254 (or their post-edit equivalents) no longer make the
      confirmed-stale claims identified above.
- [x] `.gitattributes` contains exactly the unified `data/*/*.jsonl`-style glob and no legacy lines.
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` entry has a new, date-stamped addendum
      describing this epic's unification, added via `tools/parity_ledger_writer.py` (confirmed by
      `git diff` showing a scoped, sanctioned-writer-shaped change, not a raw hand-edit).
- [x] `make knowledge-index-update` completes successfully.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — this ticket should describe the real, landed
  final shape, so should run after child 2 at minimum)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD, -CODEX-REMIGRATION,
  -REFERENTIAL-INTEGRITY (children 3-6 — no hard file-level dependency, but sequencing this ticket
  last avoids describing an interim/incomplete consumer state and matches the requester's own
  suggested ordering)
- TCK-20260902-MONITORING-SHARD-CONSUMERS — updated `INFRA-291` for the tools-only cutover; this
  ticket adds the further addendum for the full unification.

## Related Docs
- `CLAUDE.md`, `docs/agent-monitoring/README.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`, `docs/ai/system_overview.md`, `.gitattributes`,
  `.claude/workflows/implement-ticket.js`, `.claude/skills/agent-monitoring-retro/SKILL.md`,
  `docs/parity_ledger/infrastructure.yaml`.

## Related Stored Artifacts
None yet.

## Related Code Areas
None — docs/config only, no `src/`/`tools/` production code changes (per Graphify Integration's own
rule, `graphify update .` is not required for this ticket since no `src/`/`tests/` files change).

## Assumptions / Open Questions
- Sequenced last in `SEQUENCE.md` on the reasoning above — no hard technical blocker prevents running
  it earlier, but doing so risks describing a not-yet-true state that then needs a second edit pass.
- `.claude/skills/agent-monitoring-retro/SKILL.md`'s exact content was not checked this session —
  confirm at implementation time whether it needs any change.
- `layer: observability` matches this repo's established pattern; `documentation`/`claude-md` tags
  reflect this ticket's docs-and-CLAUDE.md-specific scope, distinct from the other children's
  code-focused `data-quality`/`hooks`/`dashboard`/`schema` tags.

## Implementation Notes
Implemented all 17 steps of `staging_artifacts/TCK-20260903-MONITORING-DATA-DOCS-SWEEP/plan.md`
in order, exactly as scoped:

1. `CLAUDE.md` — 5 edits (the 4 named lines 94/137/140/254 plus the plan-flagged 5th sub-edit at
   the Worktree & Branch Isolation section's own race-condition note, lines 136-140, which shares
   the same underlying fact). All now describe `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`.
2. `docs/agent-monitoring/schema.md` — line 11's "Two append-only JSONL files" corrected to "Three
   ... per UTC ISO week" (with the `tools`-joins-by-`seq` clarification), and the 3 section headers
   (50/139/368) reworded to `## \`<source>\` (\`agent-monitoring/data/YYYY-Www/<source>.jsonl\`)`
   naming the logical source, matching the body prose already correct below each. The Join Example
   (lines ~470-502) was read and confirmed untouched, per plan.
3. `docs/agent-monitoring/README.md` — lines 19 and 54 reworded from the intermediate
   `tools/tools-YYYY-Www.jsonl` shard shape to the unified per-week layout. Lines 17-18/20-21/102/
   106/128-129/138 (logical-shorthand convention) left untouched per plan.
4. `docs/guides/agent_monitoring.md` — lines 11, 24, 150 reworded to the per-week path. Line 165
   (generic "a runs.jsonl record, for any child, at any time") checked and confirmed genuinely
   conceptual, not a current-physical-layout claim — left untouched per plan's own conditional.
5. `docs/ai/system_overview.md` §6 (lines 229-247) — full rewrite of the bulleted file-shape block:
   the Sept-2-intermediate description (2 monolithic files + 1 sharded family) replaced with the
   real 3-source-per-week `agent-monitoring/data/YYYY-Www/` layout. The dated
   `TCK-20260705-MONITORING-RUNID-JOIN` historical note further down (lines 254-256) and the
   unrelated bare `agent-monitoring/events.jsonl` mention at line 131 (outside §6, describing the
   `reason_code` field, not physical layout) were both confirmed out of this step's scope and left
   untouched.
6. `docs/ai/ticket-lifecycle.md` — lines 578, 628, 639, 640 reworded, plus the plan-flagged 5th
   sub-edit at line 632 (the "Epic staleness check" paragraph's own bare `agent-monitoring/runs.jsonl`
   mention, same current-state-claim family). Line 456's `TCK-20260714-DATA-RUNS-VERIFY-REGEN` dated
   evidence citation confirmed historical and left untouched.
7. `docs/ai/workflows.md` — lines 140, 203, 204 reworded. Line 94's bare, unprefixed
   `runs.jsonl`/`events.jsonl` mention confirmed to not match either grep pattern and left untouched
   per plan (accepted logical-shorthand convention).
8. `docs/ai/agents.md` — line 279 reworded (parity-updater's discrepancy-record target path).
9-10. `.claude/skills/implement-ticket/SKILL.md:76` and `.claude/skills/simq-audit/SKILL.md:77` —
   identical write-discipline rule text reworded (path only; the "always go through record_run.py /
   record_events.py" rule substance is unchanged).
11. `.claude/skills/agent-monitoring-retro/SKILL.md` — frontmatter `description` (line 3) and body
   lines 8-9 reworded to the per-week source paths.
12. `.claude/workflows/implement-ticket.js` — lines 385 and 1706 reworded (both confirmed, before
   and after editing, to be inside a template-literal prompt string / diagnostic message, never a
   bare executable statement — verified via `git diff` manual review, matching the plan's guard).
   No other line in this file (comment blocks at 44-49, 265-272, 362-370, 560-573, including the
   bare `agent-monitoring/events.jsonl` mention at line 563) was touched — confirmed generic per
   plan.
13. `docs/testing/regression_policy.md:68` — the Zero-invocation skill-staleness row's bare
   `agent-monitoring/tools.jsonl` reference reworded to the per-week path; rest of the row unchanged.
14. `.gitattributes` — read and confirmed clean (exactly one unified `agent-monitoring/data/*/*.jsonl
   merge=union` glob, no legacy lines). No edit made, matching the plan's verification-only step.
15. `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` entry — a 4th, dated addendum was added
   via `tools/parity_ledger_writer.py::write_entry()` (never a raw YAML edit), followed by a
   separate, visible `python3 tools/parity_index.py build` Bash call per the module's own
   documented convention. **One deviation from the plan, found and self-corrected during
   implementation:** plan.md instructed appending the addendum to the `divergence_note` field,
   following what it described as "the identical pattern" the 3 prior addenda used. On reading the
   live entry, `divergence_note` actually holds a distinct, unrelated paragraph (the malformed-JSONL-
   line edge case) — the 3 prior addenda (`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`,
   `TCK-20260902-MONITORING-SHARD-CONSUMERS`, `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`) are all
   actually chained onto the `support_boundary` field, not `divergence_note`. Both plan.md and
   investigation.md misidentified the field. Caught this via a first pass that appended to
   `divergence_note` as literally instructed, then a post-write verification read of the raw file
   surfaced the addendum count/field mismatch; reverted that write with `git checkout --`, re-ran
   with the addendum appended to `support_boundary` instead (all other fields, including
   `divergence_note`, verified byte-identical before/after via a field-by-field Python diff against
   `git show HEAD:...`). `validate_entry()`'s 2 applicable rules (non-empty `id`; since
   `status == "verified"`, non-empty `v2_evidence` + `test_path`) passed on the corrected write. See
   the "Deviations" section appended to plan.md for the full record.
16. `make knowledge-index-update` — ran successfully (exit 0): "Incremental update complete: 10491
   chunks total (18 files re-embedded, 3275 from cache, 0 deleted)." The build output lands in the
   gitignored `knowledge-index/` directory — confirmed via `git status --porcelain --ignored`, no
   tracked-file diff resulted from this step.
17. Final verification sweep — all grep/guard commands from `test_plan.md` run; see Test Summary.

No functional code change was made anywhere (confirmed: `git status --porcelain | grep -E "^ M
src/|^ M tools/"` returns clean). `tests/agent_replay/test_no_mutation_snapshot.py` and
`tests/agent_replay/test_fixture_envelope.py` were not touched — both remain tracked exclusively
by the separate follow-up `TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS`.

## Test Summary
This is a docs/config-only ticket with no new pytest coverage (per test_plan.md — no behavior
changed). Verification was grep/content-based plus a scoped regression re-run:

- **Command 1** (AC's own 3-pattern grep across `docs/ CLAUDE.md .gitattributes
  .claude/workflows/implement-ticket.js .claude/skills/`): all surviving hits are in
  `docs/REGISTRY.yaml` (generated, frozen historical `related_code_areas`), `docs/audits/D23`/`D24`
  (dated audit evidence), `docs/agent-monitoring/schema.md` (the preserved "Since TCK-..."/"has
  since retired"/`git log --follow` historical migration sentences), `docs/parity_ledger/
  infrastructure.yaml` (other entries' frozen dated evidence, explicitly out of scope), or dated
  `docs/plans/`/`docs/plans/archive/`/`docs/engine/contracts/knowledge_gateway_mcp/` proposal/
  decision docs never named in plan.md's file list. Two additional hits inspected closely and
  confirmed explicitly out-of-scope per plan: `docs/ai/system_overview.md:131` (outside the Step 5
  §6 block) and `.claude/workflows/implement-ticket.js:563` (inside the plan's explicitly-excluded
  560-573 comment block). Zero unjustified current-state hits.
- **Command 2** (bare `agent-monitoring/tools\.jsonl` gap pattern, same file set): same pattern —
  all surviving hits are `docs/REGISTRY.yaml`, dated audits, `docs/parity_ledger/infrastructure.yaml`
  non-INFRA-291 entries, `docs/plans/archive/`, or docs never named in plan.md's scope
  (`docs/observability/agent_ops_dashboard_contract.md:397` confirmed dated per investigation.md;
  `docs/engine/contracts/knowledge_gateway_mcp/*`, `docs/ai/codex_posttool_adapter_real_command_proposal.md`
  confirmed conceptual/proposal-stage text, not named in plan.md). Zero unjustified hits.
- **Correction found during Verify**: an independent done-checker pass ran the full 3-pattern grep
  (including bare `events\.jsonl`/`runs\.jsonl`, which Command 2 above only checked for `tools.jsonl`)
  and found 2 live, non-dated, `status: active` reference docs this sweep's original commands missed:
  `docs/architecture/doc_updater_agent.md:134` and `docs/ai/replay_fixture_spec.md:25`, both bare
  `agent-monitoring/events.jsonl` mentions. Both fixed the same way as every other current-state
  reference in this ticket (repointed to `agent-monitoring/data/YYYY-Www/events.jsonl`). Re-ran the
  full corrected sweep after fixing: every remaining hit falls into an already-established excluded
  class (dated `_decision.md`/`docs/plans/`/`docs/engine/contracts/knowledge_gateway_mcp/` evidence
  snapshots, the preserved `schema.md` historical sentences, the excluded `implement-ticket.js:563`
  comment, `docs/ai/system_overview.md:131`'s field-schema description outside §6) — genuinely zero
  unjustified current-state hits now, not just claimed.
- **Command 3** (`CLAUDE.md` content re-check): 2 surviving lines (137, 254), both now correctly
  describe `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl`, not a bare single-file path.
- **Command 4** (`.gitattributes` cat + diff --stat): exactly the unified glob line present, zero
  legacy lines, zero diff to the file.
- **Command 5** (`INFRA-291` addendum): `grep -c "Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP"
  docs/parity_ledger/infrastructure.yaml` returns `1`. `tools/parity_index.py build` ran cleanly
  after the write (entry_count 2135, shard_count 9). Field-by-field Python comparison against
  `git show HEAD:docs/parity_ledger/infrastructure.yaml` confirmed every field except
  `support_boundary` byte-identical, and `support_boundary` is a pure superset (existing text + the
  4th addendum) — entry count (403) and id ordering unchanged across the whole shard.
- **Command 6** (`make knowledge-index-update`): completed successfully, exit 0.
- **Command 7** (no `src/`/`tools/` diff): `git status --porcelain | grep -E "^ M src/|^ M tools/"`
  returns clean.
- **Anti-Drift Guards**: Join Example hunk shows no changes (`git diff docs/agent-monitoring/
  schema.md | grep -A3 -B3 "Join Example|glob('\*/"` empty); archived/dated-doc non-touch guard
  clean; `implement-ticket.js` diff manually reviewed — both hunks are template-literal string
  content only, no executable statement touched. The parity-ledger pure-addition guard's raw
  `git diff | grep "^-"` count is nonzero (76 lines) because `write_entry()`'s `yaml.safe_dump()`
  re-wraps the entire multi-line `support_boundary` block scalar on every write (same behavior the
  3 prior addenda already produced) — this is re-serialization formatting, not content loss,
  confirmed by the field-by-field Python diff above.
- **Scoped regression pytest** (per test_plan.md): `pytest tests/tools/test_migrate_monitoring_data.py
  tests/integrity/test_merge_union_gitattributes.py tests/tools/test_doc_staleness_check.py
  tests/tools/test_doc_staleness_gate_wiring.py -v` → 40 passed, 3 skipped.
  `pytest tests/tools/ -k "parity_ledger_writer or parity_index_baseline"` → 34 passed (including
  `test_parity_index_baseline.py`, confirming the addendum did not require a baseline-drift update).
  `pytest tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` (adjacent architecture
  guard) → 10 passed.

## Files Changed
- `CLAUDE.md`
- `docs/agent-monitoring/schema.md`
- `docs/agent-monitoring/README.md`
- `docs/guides/agent_monitoring.md`
- `docs/ai/system_overview.md`
- `docs/ai/ticket-lifecycle.md`
- `docs/ai/workflows.md`
- `docs/ai/agents.md`
- `.claude/skills/implement-ticket/SKILL.md`
- `.claude/skills/simq-audit/SKILL.md`
- `.claude/skills/agent-monitoring-retro/SKILL.md`
- `.claude/workflows/implement-ticket.js` (prose-only, inside template-literal strings)
- `docs/testing/regression_policy.md`
- `docs/architecture/doc_updater_agent.md` (fixed during Verify — see Test Summary correction)
- `docs/ai/replay_fixture_spec.md` (fixed during Verify — see Test Summary correction)
- `docs/parity_ledger/infrastructure.yaml` (via `tools/parity_ledger_writer.py::write_entry()` only
  — `INFRA-291`'s `support_boundary` field, 4th addendum appended)
- `staging_artifacts/TCK-20260903-MONITORING-DATA-DOCS-SWEEP/plan.md` (Deviations section appended
  this run, documenting the `divergence_note`→`support_boundary` field correction)
- `tickets/inprogress/TCK-20260903-MONITORING-DATA-DOCS-SWEEP.md` (this file)
- `staging_artifacts/TCK-20260903-MONITORING-DATA-DOCS-SWEEP/investigation.md`,
  `staging_artifacts/TCK-20260903-MONITORING-DATA-DOCS-SWEEP/test_plan.md` (untracked, created
  during this run's own Investigate/Plan phases prior to Implement; carried forward unmodified by
  this Implement step)
- `agent-monitoring/data/2026-W36/tools.jsonl` (auto-updated by the `PostToolUse` hook during this
  session's own tool calls — not a manual edit)

No `src/` or `tools/` file was created, edited, or deleted. `.gitattributes` was read but not
edited (already clean).

## Completion Summary
Corrected all 18 confirmed stale references (plus 2 plan-flagged sub-edits, plus one out-of-scope
double-check on system_overview.md/implement-ticket.js that confirmed no further edit was needed)
to the retired `agent-monitoring/runs.jsonl`/`events.jsonl`/`tools.jsonl`/`tools/tools-YYYY-
Www.jsonl` physical shapes across `CLAUDE.md`, `docs/agent-monitoring/`, `docs/guides/`, `docs/ai/`,
`.claude/skills/`, `.claude/workflows/implement-ticket.js` (prose-only), and
`docs/testing/regression_policy.md` — replacing each with the real, landed
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout while leaving every dated "how we
got here" historical citation untouched. Added `INFRA-291`'s 4th parity-ledger addendum via the
sanctioned `tools/parity_ledger_writer.py` writer (correcting a field-name error in the plan itself,
found and fixed during implementation), and ran `make knowledge-index-update` successfully. All 4
Acceptance Criteria are satisfied; the full grep-based verification sweep and the scoped regression
pytest suite both pass clean. This is the final child (7 of 7) of
`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper)
independently re-ran the corrected AC grep sweep, confirmed the historical-preservation boundary
via direct diff reads, confirmed the `INFRA-291` addendum's self-correction genuine via a full
field-by-field YAML diff (only `support_boundary` changed, `divergence_note` byte-identical, pure
textual superset), confirmed the Join Example/`.gitattributes`/`implement-ticket.js` all untouched
or prose-only, and re-ran 84/84 regression tests. Architecture-Verify (architecture-reviewer):
**APPROVED** — zero functional code touched, parity ledger integrity confirmed programmatically
(403/403 entries, only one field of one entry changed), historical narrative confirmed
byte-identical, no scope creep into the tracked follow-up tickets. Verify (done-checker): initially
**BLOCKED** on a genuine gap its own re-run of the AC grep found — 2 live, non-dated reference docs
(`docs/architecture/doc_updater_agent.md:134`, `docs/ai/replay_fixture_spec.md:25`) the original
sweep missed (Command 2 only checked the `tools.jsonl` bare-mention gap, not `events.jsonl`/
`runs.jsonl`). Fixed both directly, re-ran the corrected sweep and confirmed every remaining hit
falls into an already-established excluded class, re-ran `make knowledge-index-update`. All 13
Definition-of-Done conditions now PASS.
