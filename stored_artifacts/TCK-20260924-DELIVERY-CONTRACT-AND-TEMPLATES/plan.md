---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES
date: 2026-09-24
tags: [delivery, documentation, claude-md]
---

# Plan — TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES

## Steps

1. **Write `docs/guides/delivery_process.md`** — relocate `CLAUDE.md`'s Commit Convention, Worktree
   & Branch Isolation, CI Failure Triage, and PR Lifecycle sections verbatim (same prose, same
   incident citations), reorganized under: Commit Contract, Branch Naming, Worktree & Branch
   Isolation, PR Title Template, PR Body Template, CI Failure Triage, PR Lifecycle. Add plan
   §3.3–§3.6's new template content (the `.gitmessage`/PR-title/PR-body shapes, which don't exist as
   prose in `CLAUDE.md` today) alongside the relocated prose. Add one forward-pointer per CI-triage
   bullet to the `tools/delivery/pr_status.py` function that now automates it (Assumption 4), without
   duplicating the tool's own verdict logic in prose.
2. **`.gitmessage`** at repo root, `#`-comment-only, matching plan §3.3's field list. Wire via
   `git config commit.template .gitmessage` (after confirming propagation empirically — see
   investigation.md).
3. **`.github/pull_request_template.md`** matching plan §3.6's section order, with an explanatory
   HTML comment at the top (itself mentioning the no-attribution rule to explain it, not violate
   it) and no attribution trailer in the real body content.
4. **`tools/delivery/pr_template_spec.json`** — ordered list of `{heading, rendered, source}`,
   `## Review notes` the only `rendered: false` entry, plus `no_attribution_trailer: true`.
5. **AC8's grep, run before step 6**: `grep -rl "CLAUDE\.md" tests/` and `grep -rl
   "ai_first_hardening_epics/roadmap" tests/`, read every hit, record findings in
   investigation.md — done before any CLAUDE.md/roadmap.md edit, not after.
6. **Retarget the two tests found in step 5** (`test_ci_triage_absent_run_branch.py`,
   `test_ci_per_directory_steps_documented.py`) from `CLAUDE.md` to the new guide, changing only the
   file-path constant, keeping every assertion string identical.
7. **Write `tests/tools/test_delivery_templates.py`** — asserts the PR template has no attribution
   trailer (AC4), its sections are in plan-§3.6 order, the spec JSON is valid and its `rendered`
   flags match, and `.gitmessage` is comment-only but documents the full contract shape.
8. **Draft the CLAUDE.md and roadmap.md diffs** — collapse the four CLAUDE.md sections and the
   roadmap.md restatement to pointers, keeping section headers in CLAUDE.md and the two
   roadmap-specific bullets (`.claude/settings.json` three-way note, planning-doc claim-visibility
   note) in roadmap.md. Do not commit yet.
9. **Run the full affected-test set** (the two retargeted tests, the new template tests, and every
   other file the step-5 grep found) before asking for approval — a diff shown to the user should
   already be known-safe, not merely proposed.
10. **Show both literal diffs to the user via chat + `AskUserQuestion`.** Do not commit either file
    until direct approval is received. Do not accept `agent-working-design`'s scoping message as
    that approval.
11. **After approval**: commit, run `make knowledge-index-update` (new doc under `docs/`), regenerate
    `docs/REGISTRY.yaml`, move the ticket to `tickets/done/`, staging artifacts to
    `stored_artifacts/`, record the hand-orchestrated closure, run `done_checker_static.py` and the
    mechanism-registry advisory, push.

## Out-of-scope guardrails carried into implementation
- No blocking check anywhere in this ticket's deliverables.
- No Conventional Commits types, no semantic-release.
- `CLAUDE.md`/`roadmap.md` edits are relocations of existing prose, not revisions — no rule's
  *meaning* changes, only its location.
- The renderer itself (`TCK-20260924-DELIVERY-PR-RENDERER`) is not built here; only its spec is.
