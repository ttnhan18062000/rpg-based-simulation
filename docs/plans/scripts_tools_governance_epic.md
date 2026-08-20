---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, process-improvement]
---

# Epic Plan — Scripts & Tools Governance

**Tracking ticket:** `TCK-20260820-SCRIPTS-TOOLS-GOVERNANCE-EPIC`
**Source:** live session investigation, 2026-08-19/20 — not from the original D23/D24 audit tree.
**Priority:** P2 — no urgent breakage, but real, confirmed orphan debt and zero documented
convention to prevent it recurring.

## Problem

`scripts/` and `tools/` have coexisted with no documented rule distinguishing them, and no
mechanism catching files that stop being used. Investigated via direct cross-reference search
(Makefile, CI, tests, other scripts/tools files, docs) — not assumption:

1. **No README, doc, or CLAUDE.md section explains when to use `scripts/` vs. `tools/`.** The
   distinction that exists today is an inferred pattern, not a stated rule: `tools/` (52
   top-level files + 18 subdirs) is the living agent-infrastructure/governance ecosystem —
   tag/layer registries, frontmatter validation, knowledge search/KGMCP, the parity ledger,
   `agent-monitoring/`, `gate_checks/`, the Codex-integration cluster. `scripts/` (28 files) is
   almost entirely performance/release/certification pipeline utilities, apparently built
   per-milestone and often abandoned after.
2. **`tools/` is healthy**: only 2 of 52 top-level files (`extract_defs.py`, `test_docker.py`)
   have zero live cross-references anywhere — both last touched 2026-03-17, the earliest stretch
   of this repo's history. (`test_docker.py` is also misleadingly named — starts with `test_` but
   is a subprocess-running script, not a pytest file.)
3. **`scripts/` is not healthy**: only 2 of 28 files (`profile_api_payload.py`,
   `profile_memory.py`) are even referenced in the Makefile. Broadening to a whole-repo search,
   **6 of 28** have zero live references anywhere — `certification_long_run.py`,
   `merge_documents.py`, `process_pytest_report.py`, `refresh_proofs.py`, `run_perf_optimized.py`,
   `split_milestone.py`. Two of those (`merge_documents.py`, `process_pytest_report.py`) have
   never been referenced by anything, not even a historical ticket. The other four appear only in
   old `tickets/done/`/`docs/archive/` records — built for one past ticket, then abandoned.
4. **No mechanism exists to catch this going forward** — unlike several other checks this same
   investigation session found or built (epic-staleness, status-drift, working-log schema), there
   is no standing "orphaned script/tool" check anywhere in this repo.

## Scope for the eventual `create-tickets` pass

- Write an explicit, documented rule for `scripts/` vs. `tools/` — this requires a real decision,
  not just documentation of the status quo: either (a) codify the inferred distinction (`tools/` =
  living agent-infrastructure, wired into workflows/tests/Makefile; `scripts/` = narrower,
  point-in-time performance/release utilities, with an explicit expectation of periodic pruning),
  or (b) conclude `scripts/`'s poor health means it should be retired/merged into `tools/`
  entirely, given `tools/` is demonstrably the pattern that stays maintained. Not pre-decided here.
- Clean up the 6 confirmed-orphaned `scripts/` files and 2 confirmed-orphaned `tools/` files —
  archive or delete each, per the implementer's judgment on which if any still have reference
  value (matching how this session handled `docs/logic_checklist_exhaustive.md`'s archival).
- Fix `tools/test_docker.py`'s misleading `test_`-prefixed name regardless of the archive/delete
  decision, if it's kept.
- Build an ongoing orphan-check mechanism (a new `tools/gate_checks/*.py` script, following this
  repo's own established pattern for exactly this kind of check) that flags a `scripts/`/`tools/`
  file with zero live cross-references — the same population-level method used in this
  investigation, made permanent and repeatable, not a one-time manual sweep.
- Decide and document whether the new orphan-check is CI-wired or on-demand-only, consistent with
  this session's finding that several sibling tools in this family are Makefile-only by design.

## Out of scope

- Retroactively auditing every individual file's *content* quality (dead code inside a file that
  IS referenced) — this epic is about orphaned *files*, not code-quality review within live files.
- Any change to the `tools/agent_codex_*`/`agent_orchestration_*`/`agent_replay_*` subdirs — those
  are a separate, already-tracked initiative (`TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`,
  currently blocked) with its own governance question, not folded into this epic.

## Acceptance signal for this epic (not yet broken into child tickets)

- A real, documented rule exists for when to add to `scripts/` vs. `tools/` (or a decision to
  retire one in favor of the other).
- The 6 confirmed-orphaned `scripts/` files and 2 confirmed-orphaned `tools/` files each have a
  disposition (archived, deleted, or confirmed-kept with a stated reason) — not left as-is by
  default.
- A repeatable orphan-check exists and is wired into at least a Makefile target.

## References

- Live session investigation (this document's own Problem section is the primary evidence trail —
  no prior audit covered this).
