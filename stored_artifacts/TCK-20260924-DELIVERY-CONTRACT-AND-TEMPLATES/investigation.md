---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES
date: 2026-09-24
tags: [delivery, documentation, claude-md]
---

# Investigation — TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES

## Confirmed facts

- `CLAUDE.md` was 440 lines before this ticket. Exact section boundaries read directly (not
  assumed from the plan's cited line numbers, which had drifted slightly): Commit Convention
  111–118, Worktree & Branch Isolation 129–170, CI Failure Triage 399–417, PR Lifecycle 418–431.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`'s `## Git & delivery
  process` section spans lines 280–318 (header at 280, `## Shared exit gates` at 319).
- Citation extraction (regex `TCK-[0-9]{8}-[A-Z0-9-]+` over the four CLAUDE.md regions): only 3
  ticket IDs are actually cited inline — `TCK-20260919-CLAUDE-MD-CHECKOUT-RACE-GUIDANCE-UNOWNED-
  AND-INCOMPLETE` (Worktree & Branch Isolation), `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`
  and `TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS` (CI Failure Triage). The roadmap.md
  section cites zero ticket IDs (it references CLAUDE.md sections by name instead). All 3 verified
  present in the new guide after the move, programmatically, not by eye.
- **AC8's mandatory pre-edit grep** (`grep -rl "CLAUDE\.md" tests/`) found 14 files. Read every one
  before editing anything:
  - `tests/docs/test_ci_triage_absent_run_branch.py` and
    `tests/docs/test_ci_per_directory_steps_documented.py` both slice `CLAUDE.md`'s text between
    the literal strings `"### CI Failure Triage"` and `"### PR Lifecycle"` and assert on its
    content — directly broken by collapsing that section to a pointer. This is exactly the
    settings.json-hook-shape-test failure mode the ticket's own Implementation Notes warned about
    (`TCK-20260924-SETTINGS-HOOK-PINNED-TEST-DRIFT`), caught here by following the mandated grep
    rather than trusting a directory-scoped test run.
  - `tests/docs/test_kernel_phase_names_consistent.py` scans `CLAUDE.md` for "Packetization"
    phase-name consistency — unrelated content, outside the four moved sections. Unaffected.
  - `tests/docs/test_prescan_mandate_instruction_draft.py` diffs a **pinned historical commit
    range** (`59b4bede`/`12f773c8`) for whether it touched `CLAUDE.md` — not a live-content
    assertion. Unaffected by an edit made in a new, later commit.
  - The remaining 10 files reference `CLAUDE.md` in docstrings/comments or for unrelated behavior
    (sidecar orchestration, monitoring bypass, secret-scan hook, registry generation, etc.) —
    confirmed by reading each, none asserts on the four sections being moved.
  - `grep -rl "ai_first_hardening_epics/roadmap" tests/` — zero results. No test pins `roadmap.md`.
- `extensions.worktreeConfig` is unset in this repo (`git config --get extensions.worktreeConfig`
  returns empty) — confirms `.git/config` is a single file shared by every worktree here, answering
  Assumption 2 empirically: `commit.template` set once propagates to every worktree's `git commit`.
- `docs/guides/agent_session_reset_boundaries.md` was read as the frontmatter/shape precedent for
  the new `docs/guides/delivery_process.md` (status/layer/authority/audience/tags frontmatter, H1
  title, no further structural requirement).

## Design decisions

1. **Section headers kept in `CLAUDE.md`, only bodies collapsed to pointers.** This keeps the
   cross-reference at line 388 ("...see 'CI Failure Triage' below") valid without editing it, and
   lets the two retargeted tests keep asserting `"### CI Failure Triage" in <file>` unchanged —
   only the file path constant needed to change, not the search string.
2. **The new guide keeps the exact heading text `"### CI Failure Triage"` / `"### PR Lifecycle"`**
   for the same reason: the two retargeted tests slice on these literal strings, and preserving
   them means the fix is a one-line file-path change per test, not a rewrite of their assertions.
3. **Machine-readable template spec placed at `tools/delivery/pr_template_spec.json`**, beside
   where `TCK-20260924-DELIVERY-PR-RENDERER` will build the renderer (Assumption 1's recommended
   option), rather than under `docs/`.
4. **`.gitmessage` written as `#`-prefixed comments, not literal fill-in text.** An unedited
   interactive commit against an all-comment message aborts (git's own behavior), rather than
   silently shipping the placeholder text as a real commit subject.
