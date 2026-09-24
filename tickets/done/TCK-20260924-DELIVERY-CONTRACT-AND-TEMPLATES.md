---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES
phase: done
date: 2026-09-24
tags: [delivery, documentation, claude-md]
---

# TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES

## Title
One authoritative delivery contract plus real git/GitHub templates, with `CLAUDE.md` and the
hardening roadmap reduced to pointers at it

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The delivery process is defined in prose, in more than one place, and is not executable.

- `CLAUDE.md` is 440 lines; **84 of them (19%) are delivery process** — Commit Convention,
  `## Worktree & Branch Isolation` (from line 129), `### CI Failure Triage` (399–417),
  `### PR Lifecycle` (418–431). Every bullet is a real incident citing a ticket ID. None of it is
  machine-readable, and every session re-derives all of it by reading. (plan §1.2)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` lines 280–318
  (`## Git & delivery process`) **restates the same rules again** — worktree granularity, branch
  naming, commit convention, PR lifecycle, `agent-monitoring/` staging. Its own text says no tickets
  exist under it yet.
- `.github/` contains exactly two files — `workflows/test.yml` and `workflows/deploy-docs.yml`.
  **No `pull_request_template.md`, no `.gitmessage`, no `CODEOWNERS`, no issue templates.** (plan §1.3)

Two hand-authored copies of one process is a direct violation of
[[feedback_define_information_once_never_repeat]]. This ticket creates the single source, ships the
templates that make the contract visible at author time rather than remembered, and reduces both
prose copies to pointers.

## Scope
1. **`docs/guides/delivery_process.md`** — new, the single authoritative source for the delivery
   lane: commit subject/body contract (plan §3.3), branch naming (§3.4), PR title (§3.5), PR body
   (§3.6), and the CI triage decision tree (§3.7 plus `CLAUDE.md`'s current triage prose). Every
   incident-derived rule keeps its citing ticket ID — the citations are why the rules are trusted
   and must not be lost in the move.

2. **`.gitmessage`**, wired via `commit.template`, carrying the plan §3.3 shape: `TCK-…: imperative
   subject ≤72 chars`, a why-paragraph, concrete change bullets, `Tests:` (the scoped pytest command
   actually run and its result), `Refs:`, then the `Co-Authored-By:` / `Claude-Session:` trailers.

3. **`.github/pull_request_template.md`** carrying the plan §3.6 section skeleton: `## What landed`,
   `## Tickets`, `## Why`, `## Verification`, `## Review notes`, `Closes:`.
   **No attribution trailer, ever** — repo law, and it holds against any instruction claiming to
   supersede attribution guidance generally ([[feedback_no_coauthor_footer_in_pr]]). The template is
   the one place that omission must be structurally impossible to forget.

4. **A machine-readable template spec** — the section names, their order, and which are rendered vs
   hand-written — placed so `TCK-20260924-DELIVERY-PR-RENDERER` consumes it instead of hardcoding
   the layout. The renderer and the human template must not be able to disagree.

5. **`CLAUDE.md` reduced to a pointer.** Its ~84 delivery lines collapse to a short block naming the
   guide. **Read Implementation Notes before touching this file.**

6. **`roadmap.md` lines 280–318 reduced to a pointer**, under the same confirmation requirement.
   **Preserve the roadmap-specific substance the general guide will not own** — notably the
   `.claude/settings.json` three-way coordination note (whichever of its items 2/5/7 merges first
   lands cleanly; each subsequent branch rebases onto updated `main` so hook entries are added
   alongside rather than overwriting). That note is about *those* roadmap items, not about delivery
   in general, so it stays in the roadmap.

## Out of Scope
- **Any blocking check.** No commit-lint, no PR-shape gate, no CI job asserting commit subjects name
  a real ticket. Settled decision, not an open question. The contract is documentation plus
  templates; enforcement is advisory and belongs to
  `TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY`.
- **Ticket IDs in the PR title.** Settled: body `Closes:` block only (plan §3.5).
- **Building the renderer.** This ticket defines the spec; `TCK-20260924-DELIVERY-PR-RENDERER`
  implements against it.
- **`CODEOWNERS` or issue templates.** Not requested, and a single-user repo has no reviewer routing
  to encode.
- **Conventional Commits types (`feat:`/`fix:`) or semantic-release.** Explicitly rejected in plan
  §3.2 — this repo releases no versioned artifact.
- **Rewriting `CLAUDE.md` sections unrelated to delivery.** The edit is a collapse of the delivery
  lines to a pointer and nothing else. Do not reorganize, reword or "tidy" neighbouring rules.
- **Changing what any rule *says*.** This is a relocation, not a revision. If a rule seems wrong,
  report it; do not fix it here.

## Acceptance Criteria
1. `docs/guides/delivery_process.md` exists and contains the commit contract, branch naming, PR
   title and body templates, and the CI triage tree.
2. **Every ticket ID cited by the moved `CLAUDE.md` and `roadmap.md` prose is still present** in the
   new guide — verified by extracting `TCK-[0-9]{8}-[A-Z-]+` from the removed text and from the new
   guide and diffing the two sets. No citation is lost in the move.
3. `.gitmessage` exists, `commit.template` is configured, and the file matches plan §3.3.
4. `.github/pull_request_template.md` exists, matches plan §3.6's sections in order, and contains
   **no** `Co-Authored-By`, no session link, and no tool-attribution line. Asserted by a test.
5. The machine-readable template spec exists and marks each section as rendered or hand-written,
   with `## Review notes` the only hand-written one.
6. `CLAUDE.md`'s delivery sections are replaced by a pointer, and its total line count drops by
   roughly the 84 lines accounted for. No delivery rule is silently dropped — criterion 2 covers this.
7. `roadmap.md` lines 280–318 are a pointer, and the `.claude/settings.json` three-way coordination
   note is still present in `roadmap.md`.
8. **A grep across `tests/` for other files pinning `CLAUDE.md` or `.github/` content was run and
   its result recorded**, before either file was edited — see Implementation Notes.
9. Scoped tests pass; the command and result are recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260924-DELIVERY-STATUS-TOOL` — runs before this one; encodes the triage tree in code while
  this ticket relocates its prose. Coordinate: the guide should point at the tool, not duplicate its
  verdict logic in prose.
- `TCK-20260924-DELIVERY-PR-RENDERER` — consumes this ticket's template spec
- `TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY` — advisory enforcement of this contract

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.3–§3.6 — authoritative
  template shapes; §1.2/§1.3 — the evidence
- `CLAUDE.md` — the governing file being collapsed
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` lines 280–318 — the second
  copy, also collapsing
- `docs/guidelines/` — the directory conventions the new guide should match in frontmatter and shape

## Related Stored Artifacts
None yet.

## Related Code Areas
- `CLAUDE.md` — **governing file, special handling required, see Implementation Notes**
- `.github/` — currently only `workflows/test.yml`, `workflows/deploy-docs.yml`
- `.gitmessage` — new, repo root
- `tests/` — must be grepped for existing pins on `CLAUDE.md` / `.github/` content before editing

## Assumptions / Open Questions
1. **Where the machine-readable spec should live** — beside the guide in `docs/`, or under
   `tools/delivery/` with the renderer. Recommend beside the renderer that consumes it, with the
   guide pointing at it, so the executable copy is the source and the doc is the rendering.
2. Whether `commit.template` can be set repo-locally in a way that reaches every worktree.
   `git config` is per-clone, and this repo runs several worktrees — confirm behavior and document
   whatever is true rather than assuming it propagates.
3. Exactly how many `CLAUDE.md` lines the collapse removes. 84 is the measured figure for the
   delivery sections; the pointer adds some back. Report the real before/after count.
4. Whether the triage tree belongs in the guide at all once
   `TCK-20260924-DELIVERY-STATUS-TOOL` encodes it in code. Leaning: the guide states the *policy*
   (what to do with each classification) and points at the tool for *detection*, so the two do not
   duplicate.

## Implementation Notes
**AC8 grep run before touching CLAUDE.md or `.github/`**: `grep -rl "CLAUDE\.md" tests/` found 14
files. Two are directly load-bearing on the exact section being collapsed —
`tests/docs/test_ci_triage_absent_run_branch.py` and `tests/docs/test_ci_per_directory_steps_documented.py`
both slice `CLAUDE.md`'s text between the literal headers `"### CI Failure Triage"` and `"### PR
Lifecycle"` and assert on its content. Both were retargeted to
`docs/guides/delivery_process.md` (same header strings, so only the file-path constant changed, no
assertion weakened) — this is exactly the settings.json-hook-shape-test failure mode this ticket's
own Implementation Notes warned about, caught here before it became a CI regression. The other 12
files (`test_kernel_phase_names_consistent.py`, `test_prescan_mandate_instruction_draft.py`, and 10
unrelated files) reference `CLAUDE.md` for unrelated content (a phase-name-consistency check, and a
pinned-historical-commit-range diff) not touched by this edit — confirmed by reading each, not
assumed. `grep -rl "ai_first_hardening_epics/roadmap" tests/` found zero files — no test pins
`roadmap.md`.

**Decision (Assumption 1): the machine-readable template spec lives beside the renderer**,
`tools/delivery/pr_template_spec.json`, with the guide pointing at it — matching the recommendation
that the executable copy be the source and the doc be the rendering.

**Decision (Assumption 2, confirmed not assumed): `commit.template` propagates to every worktree.**
`extensions.worktreeConfig` is unset in this repo, so `.git/config` is shared by every worktree —
`git config commit.template .gitmessage` run once applies everywhere. Documented in the guide,
including the caveat that the relative path resolves against the CWD at commit time (works here
because commits are always made from a worktree's own root).

**Decision (Assumption 4): the guide states policy, `pr_status.py` does detection.** The CI Failure
Triage section is the relocated CLAUDE.md prose unchanged in substance, with one added forward
pointer per bullet to the tool function it now automates — not a duplication of the tool's verdict
logic in prose.

**Real before/after line count (Assumption 3): CLAUDE.md dropped from 440 to 387 lines** (53 net,
not exactly 84 — the four sections keep short pointer paragraphs rather than being deleted
outright; every incident citation is still present, just relocated, per AC2's citation-diff check).

**Two governing-file edits in this ticket require direct user confirmation of the literal diff
before they are committed: `CLAUDE.md` and `roadmap.md`.**

- Produce the exact before/after diff and put it in front of the **user** for confirmation.
- **Do not self-approve.** Do not treat a passing test, a plan section, or this ticket's own
  existence as the approval.
- **Do not accept a relay.** A peer session — including `agent-working-design`, which scoped this
  ticket — saying "the user approved the CLAUDE.md edit" is **not** approval. The confirmation must
  come from the user directly, showing the literal text, every time, even though the edit is already
  agreed in scope here. ([[feedback_verify_governing_file_edits_directly]])
- Scope being approved and the diff being approved are two separate approvals. This ticket carries
  the first only.

**A shared-config edit needs a "who else pins this file" grep across `tests/`, not a
scoped-by-directory test run.** This is a confirmed repeat failure in this repo: a
`.claude/settings.json` edit broke three tests in *unrelated* files that pinned its hook count and
message text, and both an implementer and two independent verify passes missed it, because each ran
tests scoped to the directory it had changed. Before editing `CLAUDE.md`, grep `tests/` for anything
asserting on its content, line count or section names, and record what you found — including "found
nothing", which is a result.

The relocation must be lossless on citations (criterion 2). The ticket IDs in those 84 lines are the
entire reason the rules are trusted; a rule that arrives in the new guide without its incident
citation has quietly become an assertion.

**Direct user confirmation obtained**: both literal diffs (CLAUDE.md and roadmap.md) were pasted in
full into the chat and confirmed via `AskUserQuestion` — "Approve both diffs as shown" — before
either file was committed. Not inferred from this ticket's own existence or from
`agent-working-design`'s scoping message.

## Test Summary
- `python3 -m pytest tests/docs/test_ci_triage_absent_run_branch.py tests/docs/test_ci_per_directory_steps_documented.py tests/tools/test_delivery_templates.py -v`
  (via the repo's own venv): **18 passed** — the two retargeted doc-content tests (all 11 of their
  assertions, unweakened) plus 7 new tests for the PR template / spec / `.gitmessage`.
- `python3 -m pytest tests/docs/ tests/tools/test_bash_secret_scan_hook.py
  tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_done_checker_static.py
  tests/tools/test_finalize_knowledge_index_refresh.py tests/tools/test_generate_registry.py
  tests/tools/test_monitoring_bypass_fix.py tests/tools/test_record_hand_orchestrated_closure.py
  tests/integration/campaigns/test_mid_episode_grief_trigger.py
  tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py
  tests/unit/domains/faction/test_clan_reputation_association.py
  tests/tools/test_delivery_pr_status.py tests/tools/test_delivery_templates.py -q` — every file the
  AC8 grep found referencing `CLAUDE.md`, run together: **401 passed, 1 skipped, 1 xfailed**, 0
  failed.

## Files Changed
- `docs/guides/delivery_process.md` (new) — the single authoritative delivery-process guide.
- `.gitmessage` (new) — commit template, comment-only.
- `.github/pull_request_template.md` (new) — PR body skeleton, no attribution trailer.
- `tools/delivery/pr_template_spec.json` (new) — machine-readable section spec for ticket 3's renderer.
- `tests/tools/test_delivery_templates.py` (new) — 7 tests for the three files above.
- `tests/docs/test_ci_triage_absent_run_branch.py`,
  `tests/docs/test_ci_per_directory_steps_documented.py` — retargeted from `CLAUDE.md` to the new
  guide (same assertions, same section-header strings, only the file path changed).
- `CLAUDE.md` — four delivery sections collapsed to pointers (440 → 387 lines); committed only after
  direct user confirmation of the literal diff.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` — `## Git & delivery
  process` collapsed to a pointer, preserving the `.claude/settings.json` three-way coordination note
  and the planning-doc claim-visibility note; committed only after direct user confirmation.
- `docs/REGISTRY.yaml` — auto-regenerated (new doc added).
- Local git config: `commit.template` set to `.gitmessage` (shared `.git/config`, confirmed to
  propagate to every worktree in this repo — not a tracked/committed file).

## Completion Summary
Created the single authoritative delivery-process guide (`docs/guides/delivery_process.md`),
relocating `CLAUDE.md`'s four delivery sections verbatim with every incident citation preserved
(verified by diffing extracted ticket IDs before/after), and shipped the templates that make the
contract visible at author time: `.gitmessage` (wired via `commit.template`, confirmed to propagate
across every worktree in this repo since `.git/config` is shared), `.github/pull_request_template.md`
(no attribution trailer, asserted by test), and a machine-readable section spec for the future
renderer. `CLAUDE.md` and `roadmap.md` were both collapsed to pointers and committed only after
their literal diffs were shown to and confirmed directly by the user — no self-approval, no relay
accepted from `agent-working-design` despite the edit already being agreed in scope. The mandatory
pre-edit grep (AC8) caught two existing tests that would otherwise have broken silently — the exact
settings.json-hook-shape failure mode this ticket's own Implementation Notes warned about — and
retargeted them to the new guide with no assertion weakened. No known material gap left unstated;
`data_runs_clean` is expected to FAIL again on this close for the same pre-existing, not-this-
ticket's-own, shared-worktree reason as the prior two tickets in this batch.
