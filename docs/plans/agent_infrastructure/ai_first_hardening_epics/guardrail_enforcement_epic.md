---
status: active
layer: ai
authority: P0
audience: agent
date: 2026-09-04
tags: [ai, hooks, security, agent-monitoring]
---

# Epic Plan — Guardrail Enforcement

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only, per direct
instruction; no `create-tickets` pass has run against this doc).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3 (READY TO FREEZE, 2026-09-04),
Bucket A / Horizon 0, inventory rows "AST-based import-boundary enforcement" and "Convert 2
proven-failing prose rules to hooks".
**Roadmap**: `roadmap.md` (this epic runs in parallel with Epic G — Governance & Capability
Policy; no dependency between them).
**Priority**: P0 — the "convert 2 prose rules" item carries the frozen proposal's only Observed
Failure motivation (Level A evidence) in the entire Bucket-A set. This is not a preventive
hardening call; the failure already happened, twice, in this repository's own retro history.

## M1 is superseded — do not implement, already done

Revised during the 2026-09-04 `create-tickets` investigation pass (PR #124): `test_phase18_import
_boundaries.py` and `test_phase19_observability_boundaries.py` were both independently confirmed —
by two separate investigation runs — to already use `ast.walk`/`ast.parse`-based import-graph
detection on `main`, mirroring `test_api_read_model_guard.py`'s pattern exactly as M1 below
describes. Both files were closed by **`TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC`**
(done, 2026-08-19) — running the current 8 relevant tests across all three files confirms 8/8
pass. This epic's own cited evidence, `docs/plans/architecture_boundary_hardening_epic.md:135-136`
("documented, unimplemented todo"), is itself stale: that doc was archived to
`docs/plans/archive/architecture_boundary_hardening_epic.md` on 2026-08-20 with an explicit
`Status: Resolved by TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` note the epic doc missed
when it was written. **Action for this milestone**: none — the work is done and live on `main`. One
genuinely open, narrower gap surfaced during the same investigation (not what M1 as originally
scoped asked for, and not itself a Bucket-A item here): `test_hot_path_does_not_import_heavy
_analyzers` deliberately preserves bare-prefix (non-`src.`-aware) substring semantics post-rewrite,
so it still misses 5 real, currently-shipping violations in `src/engine/kernel.py` — already
tracked as a known, documented gap in `docs/audits/D24_codebase_health_observatory.md` §K, not a
new finding here.

## Problem

Two enforcement gaps remain live (a third, AST-based import-boundary enforcement, is resolved —
see the superseded-M1 note above):

1. **The doc-update self-report gap recurs across the repo's own retro history.** Read in full
   this session: `agent-monitoring/retro/RETRO-2026-W33.md` and `RETRO-2026-W36.md`. Both weeks'
   `## Notes` sections independently surface the same defect — a `doc-updater`-added doc file not
   reflected back into the ticket's own `## Files Changed`/`## Related Docs` — caught by
   `done-checker`/Verify's existing `check_docs_to_update_coverage` re-derivation each time, and
   patched by hand rather than fixed structurally. W33 recommends baking the fix into
   `doc-updater.md`'s base prompt; W36 (3 weeks later) reports the **same pattern recurring 3 more
   times** (`ITEM-INSTANCE-HISTORY`, `RACE-RELATIONS-MATRIX`, `READINESS-SPEED-FORMULA`) and again
   proposes the same fix, unshipped. `Verify` already catches it downstream every time — the gap is
   that generation-time never internalized the fix, so the same catch-and-patch cycle repeats.
2. **The test-scoper background-hang pattern recurred despite already being a documented Hard
   Rule.** CLAUDE.md has carried "never end your turn while your own `run_in_background` command is
   still running" since 2026-08-17/18 specifically because of this failure mode. `RETRO-2026-W36`
   reports it recurring 3 more times regardless — direct, repository-native proof that a prose-only
   rule does not reliably prevent the failure it names, even when the rule already exists and is
   specific.

## Scope

### M1 — AST-based import-boundary enforcement — SUPERSEDED, see note above (gated on nothing)

~~Port `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` from
their current substring/regex checks to `ast.walk`-based import-graph checks, mirroring
`test_api_read_model_guard.py`'s already-proven pattern in the same test suite.~~ Already done by
`TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` — see "M1 is superseded" above. No action
remains under this milestone.

### Invariant governing M2 and M3 (added during planning discussion)

> Any rule promoted into this epic because of repeated prose-only failure must gain a
> deterministic enforcement or verification mechanism where technically feasible. Prompt
> reinforcement alone does not satisfy the milestone. Rewriting the prose more strongly is not a
> fix for a failure class that prose has already been proven not to prevent.

If repo inspection during implementation genuinely proves a deterministic check isn't feasible for
some part of either milestone, that must be documented explicitly — not silently left as
prompt-only — in the form: *deterministic enforcement not feasible because `<reason>`; fallback:
prompt guidance only; residual risk: `<named>`*.

### M2 — Doc-update self-report gap: structural fix (gated on nothing)

Two parts, but **not equally weighted** — the deterministic check is the milestone's actual
postcondition; the generation-time prompt change is defense-in-depth, not the primary control:

1. **Verify-time hardening (primary control)**: `check_docs_to_update_coverage` already re-derives
   ground truth from `investigation.md` and real `git status` rather than trusting `doc-updater`'s
   self-report — extend it to also check the reverse direction (a file `doc-updater` touched but
   that never made it into the ticket body), since that's the specific gap the three recurring
   retro incidents describe. This is the deterministic postcondition Verify enforces regardless of
   what `doc-updater` self-reports.
2. **Generation-time (defense-in-depth, not primary)**: bake an explicit self-check step into
   `doc-updater.md`'s base prompt — before reporting `docs_updated`, cross-reference the actual
   files touched against what will be written into the ticket's own `## Files Changed`/`## Related
   Docs` sections, flagging any mismatch in the same turn. This reduces how often the primary
   control needs to catch anything; it is not itself the fix, since it carries the same class of
   risk that motivated this epic in the first place.

### M3 — Test-scoper background-hang guard (gated on nothing)

**SHIPPED** by `TCK-20260904-TEST-SCOPER-HANG-GUARD` — a real, deterministic `SubagentStop` hook
(`tools/agent-monitoring/subagent_stop_background_guard.py`), wired as a new `SubagentStop` key in
`.claude/settings.json`'s `hooks` block (previously only `PreToolUse`/`PostToolUse` existed), and
verified by `tests/tools/test_subagent_stop_background_guard.py` (5 tests: fires on a still-running
background task, allows a completed one, allows the no-background-task common case, fails open on
malformed input, and respects `stop_hook_active` loop-prevention) plus
`tests/tools/test_settings_json_hooks_wiring.py` (proves the key is genuinely new, and that the
hook's command is not suffixed with the swallowing `|| true` every other hook in this file uses).

The hook reads a harness-populated `background_tasks` array directly off the `SubagentStop`
payload rather than parsing transcript JSONL: this ticket's implementation-time spike found both
live-capture avenues (a nested `claude` invocation, and a throwaway `.claude/settings.local.json`
diagnostic hook) blocked by this sandbox's own auto-mode classifier, so the real payload shape was
instead extracted directly from the installed Claude Code binary's own validation schema and
control-flow code — evidence stronger than a single live-fired example, since it is the schema
that produces every instance. That extraction revealed `background_tasks` (populated from a live
per-session task registry, non-empty exactly when in-flight background work exists) is a first-
party field purpose-built for this exact question, making the transcript-heuristic architecture
this milestone originally anticipated unnecessary. See
`tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.json` for the full citation, and
`staging_artifacts/TCK-20260904-TEST-SCOPER-HANG-GUARD/plan.md`'s Deviations section for the full
accounting. This directly operationalizes the CLAUDE.md Hard Rule that has existed since
2026-08-17/18 but had not, on its own, prevented the recurrence.

**Known same-batch coordination point**: `.claude/settings.json`'s `hooks` block is also expected to
be touched by `TCK-20260904-BASH-SECRET-SCAN-HOOK` (same batch), likely adding its own key under
`PreToolUse`. Both edits are additive (new sibling keys) and should not structurally conflict —
flagged here so a future reader understands why two tickets both touch this file in the same
window, not because either ticket is sequenced on the other.

### M4 — Horizon-0 exit signal (observation only, not implementation)

Confirm, after M2 and M3 have shipped and run for the stated window, that:
- Zero recurrence of the doc-update self-report gap across ≥2 subsequent weekly retro reports.
- Zero recurrence of the test-scoper background-hang pattern across ≥2 subsequent weekly retro
  reports.

This is the epic's contribution to the shared Horizon-0 → Horizon-1 gate defined in `roadmap.md`
— not a separate implementation task. Retro reports are already the detection mechanism (they
caught the recurrence three times); this milestone is about confirming the fix actually closes
what detection already proved was open.

## Out of scope

- Any new, general architecture-boundary rule beyond upgrading the two existing regex-based checks
  to AST — this epic strengthens enforcement of rules that already exist, it does not add new
  ones.
- Converting any other CLAUDE.md prose rule to a hook — only the two with direct, repeated,
  repository-native evidence of failure (M2, M3) are in scope here. The frozen proposal's own
  evidence standard (§60) is the reason: everything else in CLAUDE.md's Hard Rules remains prose
  until it has comparable evidence, not because prose is assumed sufficient elsewhere, but because
  converting it without evidence would be exactly the "preventive hardening without justification"
  pattern the freeze pass was built to catch.
- The general search-before-grep hook's nudge-vs-deny question (a live ambiguous-authority case
  the frozen proposal names separately) — related in spirit, not evidenced the same way, and not
  part of this epic's scope.

## Acceptance signal for this epic

- M1: none required — already shipped and verified upstream by
  `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (8/8 relevant tests pass).
- M2: **satisfied by `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`** (done) — extended
  `check_docs_to_update_coverage` in-place with a tier-agnostic reverse-direction check (a `docs/`
  path git shows touched that never made it into the ticket's own `## Files Changed`/`## Related
  Docs` text), wired into `run_static_precheck`'s existing blocking aggregation. Verified against
  the real `TCK-20260831-RACE-RELATIONS-MATRIX` historical incident, reproduced as a regression
  fixture proving the new check would have `FAIL`ed before that ticket's hand-patch. Scoped to
  `docs/` paths only (matching the forward check's own scope) — this means the check structurally
  cannot catch the `TCK-20260831-ITEM-INSTANCE-HISTORY` incident's actual gap
  (`src/core/state.py`, a non-`docs/` path); this is a disclosed, accepted limitation, not
  something this milestone's closure implies is also covered. `doc-updater.md`'s prompt self-check
  (Step 5 of that ticket's plan) exists as defense-in-depth but is not itself the acceptance bar,
  consistent with the original wording below.
- M3: **satisfied** — `tools/agent-monitoring/subagent_stop_background_guard.py`, a real
  deterministic `SubagentStop` hook (not a prompt-only assertion), wired in `.claude/settings.json`
  under a hook event key that did not previously exist, and demonstrably fires against a synthetic
  case where a `test-scoper`-shaped subagent would otherwise end its turn with a background pytest
  still running (`tests/tools/test_subagent_stop_background_guard.py::
  test_hook_fires_for_still_running_background_task`). `.claude/agents/test-scoper.md`'s existing
  `## Background Commands` prose section is kept verbatim as defense-in-depth (the hook fails open
  on any internal error, so the prose remains the backstop for exactly the cases the hook cannot
  catch).
- M4: zero recurrence of either target pattern confirmed across ≥2 consecutive weekly retros,
  feeding `roadmap.md`'s shared gate.

## References

- `roadmap.md` — shared exit gate; confirms no dependency exists between this epic and Epic G.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` (`docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html`) —
  Reassessment §3 ("Deterministic guardrails... upgraded"), Change Inventory rows for this epic's
  two items.
- `agent-monitoring/retro/RETRO-2026-W33.md`, `RETRO-2026-W36.md` — the real, repeated evidence
  this epic's priority is drawn from.
- `TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC` (done, 2026-08-19) — the real, closed ticket
  that already shipped M1 (see "M1 is superseded" above). `docs/plans/architecture_boundary_hardening_epic.md`
  (the doc this epic originally cited for M1's motivation) is now archived at
  `docs/plans/archive/architecture_boundary_hardening_epic.md` with a `Status: Resolved` note.
- `tests/architecture/test_api_read_model_guard.py`, `test_phase_domain_permissions.py` — the
  existing AST-based pattern the shipped M1 work ported.
- `.claude/agents/doc-updater.md`, `.claude/agents/test-scoper.md` — the two agent prompts M2/M3
  modify.
- `CLAUDE.md` — the existing prose Hard Rule M3 operationalizes (dispatched-subagent
  `run_in_background` warning, carried since 2026-08-17/18).
