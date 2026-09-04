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

## Problem

Three enforcement gaps, one already-proven and two structurally evidenced:

1. **Two of the four architecture import-boundary tests use substring/regex matching, not AST.**
   `tests/architecture/test_phase18_import_boundaries.py` and
   `tests/architecture/test_phase19_observability_boundaries.py` are evadable by any non-literal
   import (`importlib`, import aliasing) — a documented, unimplemented todo in the repo's own
   `docs/plans/architecture_boundary_hardening_epic.md:135-136`. The other two boundary tests
   (`tests/architecture/test_api_read_model_guard.py`, `test_phase_domain_permissions.py`) already
   use `ast.walk`-based checks — the pattern to port to exists in this same test suite, it just
   isn't applied everywhere yet.
2. **The doc-update self-report gap recurs across the repo's own retro history.** Read in full
   this session: `agent-monitoring/retro/RETRO-2026-W33.md` and `RETRO-2026-W36.md`. Both weeks'
   `## Notes` sections independently surface the same defect — a `doc-updater`-added doc file not
   reflected back into the ticket's own `## Files Changed`/`## Related Docs` — caught by
   `done-checker`/Verify's existing `check_docs_to_update_coverage` re-derivation each time, and
   patched by hand rather than fixed structurally. W33 recommends baking the fix into
   `doc-updater.md`'s base prompt; W36 (3 weeks later) reports the **same pattern recurring 3 more
   times** (`ITEM-INSTANCE-HISTORY`, `RACE-RELATIONS-MATRIX`, `READINESS-SPEED-FORMULA`) and again
   proposes the same fix, unshipped. `Verify` already catches it downstream every time — the gap is
   that generation-time never internalized the fix, so the same catch-and-patch cycle repeats.
3. **The test-scoper background-hang pattern recurred despite already being a documented Hard
   Rule.** CLAUDE.md has carried "never end your turn while your own `run_in_background` command is
   still running" since 2026-08-17/18 specifically because of this failure mode. `RETRO-2026-W36`
   reports it recurring 3 more times regardless — direct, repository-native proof that a prose-only
   rule does not reliably prevent the failure it names, even when the rule already exists and is
   specific.

## Scope

### M1 — AST-based import-boundary enforcement (gated on nothing)

Port `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` from their
current substring/regex checks to `ast.walk`-based import-graph checks, mirroring
`test_api_read_model_guard.py`'s already-proven pattern in the same test suite. Concretely: parse
each source file's AST, walk `ast.Import`/`ast.ImportFrom` nodes directly (catching aliased and
`importlib.import_module(...)` forms the current regex cannot), and check the resolved module path
against the same boundary rules the existing tests already encode — this is a detection-mechanism
upgrade, not a change to what counts as a violation.

**Known risk, named explicitly**: AST-based import detection can produce false positives on
genuinely dynamic imports (conditional imports, plugin-style loading) that the current regex
happens to miss too, just for a different reason. Any such case found during porting should be
added as an explicit, commented allowlist entry — not silently special-cased.

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

**Target implementation is a real `Stop`/`PostToolUse`/turn-end deterministic hook or equivalent
state check** — not a prompt-only assertion. A turn-end prompt assertion inside `test-scoper.md`
is acceptable only as a documented fallback if implementation-time inspection proves the
background-task state genuinely cannot be checked deterministically (per the invariant above),
never as an equally-weighted default choice. The guard flags — and where the harness allows,
prevents — a `test-scoper` subagent ending its turn while its own `run_in_background` pytest
invocation is still running. This directly operationalizes the CLAUDE.md Hard Rule that has
existed since 2026-08-17/18 but has not, on its own, prevented the recurrence.

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

- M1: `test_phase18_import_boundaries.py` and `test_phase19_observability_boundaries.py` both use
  `ast.walk`-based detection; a synthetic aliased-import or `importlib`-based violation is caught
  post-change where it passed before (a real before/after check, not just a code read-through).
- M2: `check_docs_to_update_coverage` (or its replacement) is confirmed as the primary control,
  catching the reverse-direction case the three retro incidents describe, verified against at
  least one of the three real historical tickets that exhibited it — this must hold true
  independent of whether `doc-updater.md`'s prompt self-check fires. The prompt self-check exists
  and reduces how often the primary control needs to act, but is not itself the acceptance bar.
- M3: the background-hang guard is a real deterministic hook/state-check (not a prompt-only
  assertion) and demonstrably fires against a synthetic case where a `test-scoper` subagent would
  otherwise end its turn with a background pytest still running. If implementation genuinely
  cannot achieve deterministic detection, the documented fallback format (reason / fallback /
  residual risk) exists in this doc before M3 is considered complete — a silent prompt-only
  implementation does not satisfy this milestone.
- M4: zero recurrence of either target pattern confirmed across ≥2 consecutive weekly retros,
  feeding `roadmap.md`'s shared gate.

## References

- `roadmap.md` — shared exit gate; confirms no dependency exists between this epic and Epic G.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` (`docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html`) —
  Reassessment §3 ("Deterministic guardrails... upgraded"), Change Inventory rows for this epic's
  two items.
- `agent-monitoring/retro/RETRO-2026-W33.md`, `RETRO-2026-W36.md` — the real, repeated evidence
  this epic's priority is drawn from.
- `docs/plans/architecture_boundary_hardening_epic.md:135-136` — the repo's own prior, unshipped
  todo to upgrade the two regex-based boundary tests.
- `tests/architecture/test_api_read_model_guard.py`, `test_phase_domain_permissions.py` — the
  existing AST-based pattern M1 ports.
- `.claude/agents/doc-updater.md`, `.claude/agents/test-scoper.md` — the two agent prompts M2/M3
  modify.
- `CLAUDE.md` — the existing prose Hard Rule M3 operationalizes (dispatched-subagent
  `run_in_background` warning, carried since 2026-08-17/18).
