# Investigation — TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE

## What exists today
`tools/mechanism_registry/mechanism_registry_changed_code_check.py` has a pure, tested core
(`check_drift(old_data, new_data, changed_files)`, `check_replacements(old_data, new_data)`) and a
git-diff CLI wrapper (`check_drift_from_git(base_ref, head_ref)` / `main()`), invoked today only via
`make mechanism-registry-changed-code-check` — advisory-only in CI, never in the ticket lifecycle.
`main()` always returns 0.

## Measurement (run before any code was written, per explicit instruction)

**1. Historical drift rate.** Ran the CLI from the registry's foundation commit (`8ab22a916`,
2026-09-17) through `origin/main` (2026-09-20): **0 drift findings, 0 `implemented_by`
replacements.** Verified this wasn't a no-op invocation: the registry genuinely grew 89→93
mechanisms in that span (`git show <ref>:registries/mechanisms.yaml` + a `len()` check at both
ends). Correction applied after peer review: this is **0/0 over a three-day window in which the
only sessions touching cited code were the registry-aware program itself** — not a property of
"the registry's entire life," and not strong evidence that the check is either useless or
unnecessary. It says nothing about the future case the advisory exists for: an unrelated,
registry-unaware session touching cited code later.

**2. Real multi-ticket batch-PR bundling.** `git show --stat 97a0e5d96` (#229) bundles six distinct
ticket IDs in one squash-merge commit. Confirms this repo's real PR shape routinely mixes unrelated
tickets' changes together — the premise that makes "changed files = diff against origin/main" the
wrong default at close time.

**3. The "changed files" definition — resolved empirically, not by preference.**
Tested on my own current branch (`headroom-batch3-work`): `git diff --name-only origin/main...HEAD`
mixes in files from at least 4 unrelated tickets committed on the same branch. Using that as
"changed files" for one ticket's advisory would misattribute drift across tickets with nothing to
do with each other.

Instead, tested `git log --grep=<ticket-id> origin/main..HEAD` against an already-closed sibling
ticket on this same branch (`TCK-20260916-HEADROOM-SAVINGS-AND-HARM-VERDICT`) — it isolates exactly
that ticket's own commit (`78285e208`), and `git show --name-only` on it returns exactly that
ticket's own files. This works because every commit in this repo already references its ticket ID
(CLAUDE.md's Commit Convention).

**Definition chosen:** "changed files" for a ticket's own close-time advisory = the union of (a)
every file touched by any commit on the branch whose message matches the ticket ID
(`git log --grep=<ticket-id>`), and (b) the current working tree's uncommitted state (`git status
--porcelain`, staged + unstaged + untracked). (b) exists specifically because a hand-orchestrated
closer who commits everything in one final closing commit would otherwise run the advisory before
that commit exists, see nothing, and read "no drift" as if it were a real negative — a silent
fail-open in the direction that looks like success. Per peer's flagged concern, the check now
considers uncommitted state rather than depending on commit-before-check ordering.

**Boundary, recorded rather than hidden:** this `--grep`-based definition is **pre-merge only**. On
`main`, after a squash-merge, the branch's many per-ticket commits collapse into one commit whose
message carries every bundled ticket ID (see finding 2, `97a0e5d96`'s six IDs) — running the same
query over post-merge history would match that single commit for all six and over-attribute every
file to every ticket. This is a boundary of where the tool runs (close time, on the ticket's own
branch, pre-merge), not a defect to fix — but it must never be used to backfill historical findings
against `main`, and the code/ticket both say so explicitly.

## Existing precedent followed
- `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` — the pattern being copied: unconditional, non-blocking
  side effect at close, all tiers.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` — why a pipeline-only
  advisory is not enough; most real closes in this repo are hand-orchestrated.
- The three existing Finalize-tail advisories in `implement-ticket.js`
  (`check_monitoring_write_recorded`, `check_tag_drift`, `check_workflow_meta_conformance`) — same
  shape: runs after status is already `DONE`, prints a WARNING, never changes the return status or
  exit code.

## Conclusion: worth wiring, with honest caveats
- The check's historical hit rate is 0/0 — we have no evidence yet of what a real positive looks
  like in this repo. The planted-drift and planted-no-drift AC tests exist specifically to prove the
  wiring works, since real history can't demonstrate it yet.
- The value is prospective (catching a *future* registry-unaware session), which this measurement
  argues for but cannot itself demonstrate.
- The changed-files definition depends on commit-message hygiene (every commit already references
  its ticket ID, by convention). If that convention lapses, the definition silently degrades to
  "nothing found" — fail-open in the same direction the advisory already fails open (never blocks).
  Not a new risk class; recorded here and in the code so a future reader doesn't mistake the
  mechanism for unconditional.
