---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP
artifact_type: investigation
tags: [registry, process-improvement, debugging, data-quality]
---

# Investigation — TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP

## Current Behavior

### Re-verified evidence for `TCK-20260904-WORKING-LOG-CSV-PARSER`'s Finding 2 (all claims hold)

Re-derived independently, not trusted from the prior artifact:

- `sed -n '2,1587p' tickets/working_log.csv` vs `sed -n '1595,3180p' tickets/working_log.csv`:
  1586 lines each, `diff -q` reports **no differences** — byte-for-byte identical, same
  relative order, confirmed today (file has grown to 3400 physical lines total since the
  prior investigation's 3376, i.e. ~24 new legitimate rows appended since, consistent with
  normal ticket-closure cadence, not a second incident).
- Line 1594 and line 1 are both exactly
  `timestamp,ticket_id,title,status,summary,artifacts_path` — the embedded duplicate header
  row still sits at line 1594, unchanged.
- `git show 5993cac3 --numstat -- tickets/working_log.csv` → `1640  0  tickets/working_log.csv`
  — confirmed pure +1640/−0 insertion, zero deletions, for this one file in this one commit.

### Root cause: confirmed squash-merge, not a real three-way merge

`git log 5993cac3 -1 --format="%P"` → **one parent** (`0d77b687761e21da70e91902c983e1f60f4d434a`).
A genuine three-way `git merge` commit always has two (or more) parents; a single-parent
commit is, by definition, not the product of git's merge machinery — it is an ordinary
linear commit whose diff happens to be large. `gh pr view 90 --json baseRefName,headRefName,
mergeCommit` confirms `5993cac3` **is** GitHub's recorded merge commit for PR #90
(`m1-quick-wins` → `main`), and the commit message is the literal concatenation of ~20+
individual per-ticket commit messages from that branch (`* TCK-20260826-HOTFIX-...`, `*
TCK-20260824-ROLLOUT-FLAG-DECISIONS`, etc.) — the exact shape GitHub produces for a
**squash-merge** (it concatenates every squashed commit's message into the one new commit's
body). This is direct, positive confirmation, not inference from absence: PR #90 was
squash-merged.

**Why this fully explains the incident:** `merge=union` is a git *merge driver* — a plugin
that git's merge machinery (`git merge`, `git rebase`, `git cherry-pick -m`, GitHub's
"Create a merge commit" button) invokes per-file only when it needs to three-way-merge two
divergent versions of that file against a common ancestor. A squash-merge does not perform
a three-way merge at all: GitHub computes the diff between the PR branch tip and current
`main`, and applies that diff as a single new commit directly on `main` — mechanically
equivalent to `git diff merge-base..branch-tip | git apply` followed by one commit, with
exactly one parent (current `main` tip). No merge driver of any kind is invoked, because no
`git merge` operation ever runs. If `m1-quick-wins` was a long-lived branch (its own
commits span TCK-20260824 through the batch's close, i.e. it was open across multiple days
while `main` also advanced via other squash-merged PRs), the diff GitHub computed for
`tickets/working_log.csv` was "everything the branch head has that this specific diff
algorithm decided differs from current `main`" — which, given the branch's own base was
stale relative to `main`'s intervening appends, can reproduce the full set of `main`'s own
already-appended rows as a synthetic "addition" in the squash diff. `merge=union` was never
given a chance to deduplicate this because it never ran.

### Systemic finding: squash-merge is this repo's de facto standard for GitHub PRs, not a one-off

- Repo-wide: `git log --oneline HEAD | wc -l` → 197 total commits; `git log --merges --oneline
  HEAD | wc -l` → **2** real merge commits total (`aebe8eee "Merge origin/main (concurrent
  session's local monitoring-sync commits reconciled)"` and `c29d9df7 "Merge branch
  'resource-enhance'"` — both look like manual/local `git merge` operations, not GitHub PR
  merges). That is 2/197 ≈ 1% of history.
- Directly checked the 5 most recently merged PRs (#142, #141, #140, #139, #138) via `gh pr
  view <N> --json mergeCommit` then `git log -1 --format="%P" <sha>` for each: **all five**
  merge commits have exactly one parent (the immediately preceding commit's SHA), i.e. all
  five were squash-merged.
- `gh repo view --json squashMergeAllowed,mergeCommitAllowed,rebaseMergeAllowed` shows all
  three GitHub merge strategies are technically *allowed* at the repo-settings level, but
  actual practice — confirmed by both the historical merge-commit ratio and the 5/5 sample
  of recent PRs — is squash-merge for essentially every normal PR landing.
- **Conclusion**: `merge=union` can almost never actually engage for a normal PR-based
  contribution to this repo, because the standard landing mechanism (GitHub squash-merge)
  never invokes git's merge machinery for any file, ever — regardless of whether that file
  has a merge driver configured. `merge=union` remains correct/useful only for the rare
  cases outside the standard PR flow: a manual local `git merge`/`git pull` between two
  local branches, or (per `.gitattributes`' own comment) a genuine `git rebase`/`cherry-pick
  -m` scenario, none of which represent how this repo's own documented "PR Lifecycle"
  workflow (`CLAUDE.md`) actually lands work today.

### Existing regression test's real scope vs. what actually happened

`tests/integrity/test_merge_union_gitattributes.py`
(`test_concurrent_branch_appends_merge_without_conflict_markers`, parametrized over 5
tracked filenames including `tickets/working_log.csv`) does exactly what its own docstring
says: it inits a throwaway repo, creates two local branches that each append a distinct line
to the same tracked file, then runs a **real `git merge branch-a --no-edit`** command and
asserts it auto-resolves via the union driver with no conflict markers. This test is
correct and still passes — it proves the git-level `merge=union` mechanism itself works
exactly as designed for a genuine three-way merge. **It is not, and never claimed to be, a
test of GitHub's squash-merge path.** The ticket that shipped it
(`TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`) scoped it as "a regression test confirming
the already-shipped merge=union .gitattributes entries... actually resolve a concurrent
two-branch edit" — which it does, faithfully, for the `git merge` scenario. The **gap** is
not a bug in the test; it is that this scenario is not representative of how this repo's PRs
actually land (squash-merge, confirmed above), so a git-merge-level guarantee gives no
practical protection against the actual, dominant landing mechanism. Confirmed by reading
`TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS.md` in full: its own Scope/Assumptions never
mention squash-merge, GitHub's merge-strategy setting, or PR landing mechanics at all —
the investigation that produced it evidently never considered that the git-level guarantee
and the repo's actual PR-merge convention could diverge.

### Not unique to `tickets/working_log.csv` — a second live instance found

Spot-checked the other file family covered by `merge=union`
(`agent-monitoring/data/*/*.jsonl`, 46 files across `2026-W23`–`2026-W37` plus
`unknown-week`). Rather than eyeball individual files, ran an exact-duplicate-line sweep
(`sort file | uniq -d`) across the highest-volume recent shards:

| File | Total lines | Distinct duplicated lines |
|---|---|---|
| `agent-monitoring/data/2026-W35/tools.jsonl` | 29510 | 1 |
| `agent-monitoring/data/2026-W36/tools.jsonl` | 32683 | **79** |
| `agent-monitoring/data/2026-W35/events.jsonl` | 953 | 2 |
| `agent-monitoring/data/2026-W35/runs.jsonl` | 111 | 0 |
| `agent-monitoring/data/2026-W36/events.jsonl` | 1145 | 0 |
| `agent-monitoring/data/2026-W36/runs.jsonl` | 128 | 1 |

`agent-monitoring/data/2026-W36/tools.jsonl`'s 79 duplicated lines are not scattered
coincidences: a contiguous-block search (`lines[i] == lines[i+409]` for a long run) finds
physical lines 22830–22908 (79 lines) are byte-for-byte identical to lines 23239–23317, a
fixed +409 offset for the entire block. Sampled one pair directly (line 22831 vs 23240):
identical JSON down to the microsecond `"ts"` field
(`"2026-09-04T16:20:30.311347Z"`) — this rules out "two independent tool calls that
happened to look the same" and confirms it is the **same defect class**: a whole-block
duplication from the same squash-merge mechanism, just two orders of magnitude smaller in
this instance (79 rows vs. ~1586). This is a genuine, real, broader-impact finding: the
`merge=union` gap is not specific to `tickets/working_log.csv`, it is inherent to every file
covered by that attribute, because the root cause (squash-merge bypassing all merge
drivers) is a property of the repo's PR-landing convention, not of any one file.

### `tools/validate_working_log.py` is currently failing (silently — not wired into any gate)

Ran `python3 tools/validate_working_log.py` directly against the live file: **exits 1**,
reporting a "Duplicate ticket IDs in working_log.csv" error listing several hundred ticket
IDs (a direct, mechanical consequence of Finding 2's ~1586-row duplication — `run_validation`'s
check 1, `tools/validate_working_log.py:41-50`, builds its `ids` list from every row with a
non-`None` `record`, i.e. every `clean` **and** every `is_duplicate=True` row, without
filtering on `is_duplicate`; the tolerant parser's own `is_duplicate`/`duplicate_of_line`
signal, built by `TCK-20260904-WORKING-LOG-CSV-PARSER` specifically to flag this class, is
computed but never consulted by this particular check), plus a separate batch of
pre-existing "empty field 'artifacts_path'" errors unrelated to this ticket's scope (do not
conflate — those are a residual gap from `TCK-20260819-HOTFIX-WORKING-LOG-LEGACY-SCHEMA-ROWS`'s
own documented 17-row leftover, not new). `grep -rn "validate_working_log" .github/workflows/
Makefile tools/gate_checks/` returns **zero hits** — this script is not invoked by CI, by
`make`, or by any gate check; it is a standalone manual tool. So the failure is real but
currently silent: nobody is notified today, and it will surface with a large, confusing
error dump the moment anyone wires it into a gate (e.g. as a natural follow-on to this
ticket) without first accounting for `is_duplicate` rows in check 1.

## Mechanics / Engine Constraints

Not applicable. `tickets/working_log.csv`, `.gitattributes`, and
`agent-monitoring/data/*/*.jsonl` are agent-tooling/process bookkeeping and repository
merge configuration, not simulation subsystems — no `docs/mechanics/` chapter or
`docs/engine/` contract governs git merge behavior or process-log file formats. This
mirrors the identical conclusion already reached by
`stored_artifacts/TCK-20260904-WORKING-LOG-CSV-PARSER/investigation.md` and
`stored_artifacts/TCK-20260705-WORKING-LOG-BACKFILL/investigation.md`.

## Docs Requiring Update

None.

The `.gitattributes` file itself (path: `.gitattributes`, under the repo root, not `docs/`)
is not a `docs/` path and is not edited by this investigation regardless — any comment
clarifying the squash-merge caveat is a Plan/Implementation decision, and per Gate Integrity
this investigation makes no edits.

`docs/parity_ledger/infrastructure.yaml` (path: `docs/parity_ledger/infrastructure.yaml`,
under `docs/parity_ledger/`) mentions `tickets/working_log.csv` in three existing entries
(as a *data source* other measurements read, e.g. the KGMCP Phase 5 repeated-demand
methodology entries) but none of those entries are about the file's own merge/duplication
integrity — none requires a status or evidence change for this ticket's findings.

No `docs/mechanics/` chapter, `docs/engine/` contract, or `docs/guidelines/
intentional_divergences.md` entry applies, for the same reason given in "Mechanics / Engine
Constraints" above — this is not a simulation-behavior change.

## Parity Ledger Overlap

None. Confirmed by direct grep of `docs/parity_ledger/` for `working_log`/`merge=union`/
`gitattributes` terms: the only hits (`docs/parity_ledger/infrastructure.yaml`, three
locations) reference `tickets/working_log.csv` purely as a data source for unrelated
measurements (dashboard velocity computation, KGMCP Phase 5 repeated-demand methodology
snapshots), not as a subject of parity tracking itself. No P0 entries touched.

## Prior Work

- `TCK-20260904-WORKING-LOG-CSV-PARSER` (stored_artifacts) — original discovery of Finding
  2 (this ticket's entire premise), shipped `tools/working_log_parser.py`'s tolerant parser
  with `is_duplicate`/`duplicate_of_line`/`duplicate_row_count` fields, and the narrow
  `knowledge_search.py` embedded-header-row guard. This ticket builds directly on that work
  and does not re-implement any of it (per this ticket's own Out of Scope).
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (tickets/done) — shipped the `merge=union`
  `.gitattributes` entries and `tests/integrity/test_merge_union_gitattributes.py`. Its own
  investigation explicitly rejected building a custom auto-renumbering merge driver as
  unnecessary, reasoning that the shipped `merge=union` + regression test closed the gap. As
  this ticket demonstrates, that reasoning held for the mechanism it tested (real `git
  merge`) but did not anticipate that the repo's actual PR-landing convention (squash-merge)
  bypasses the mechanism entirely.
- `TCK-20260902-MONITORING-SHARD-MIGRATION` / `TCK-20260903-MONITORING-DATA-MIGRATION` /
  `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY` — retired the legacy monolithic
  `agent-monitoring/{tools,runs,events}.jsonl` files in favor of the current
  `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` shard layout, reflected in
  `.gitattributes`' current `agent-monitoring/data/*/*.jsonl merge=union` glob (confirmed by
  reading `tests/integrity/test_merge_union_gitattributes.py`'s own docstrings for these
  three tests, which record the migration history). The W36 tools.jsonl duplication found in
  this investigation happened on the *current* shard layout, i.e. it is a live, current-format
  instance, not a legacy artifact left over from a since-retired file shape.

## Risks and Open Questions

1. **This investigation confirms squash-merge as the root cause with direct evidence
   (single-parent commit + GitHub-recorded merge SHA + concatenated commit-message shape +
   5/5 recent-PR sample), but cannot fully reconstruct *why* the `m1-quick-wins` branch's
   squash diff specifically reproduced ~1586 already-`main` rows** (e.g. whether the branch
   was rebased/re-based incorrectly mid-flight, force-pushed after diverging further, or
   simply stayed open across several other PRs' worth of `working_log.csv` appends without
   ever syncing from `main`). This does not change the recommended remediation (the
   mechanism-level fix does not depend on the exact branch-hygiene mistake), but Plan should
   not assume a specific proximate trigger beyond "a long-open branch's squash diff against a
   moved-forward `main`" without further evidence, since none was found or sought beyond what
   was needed to confirm squash-merge as the delivery mechanism.
2. **Whether other `merge=union`-covered shards beyond the two spot-checked (`2026-W35`,
   `2026-W36` `tools`/`events`/`runs`) also carry undetected duplicate blocks is not fully
   swept** — this investigation deliberately spot-checked per the ticket's own instruction
   ("spot-check 1–2 other files"), not an exhaustive audit of all 46 files. Plan should decide
   whether a full sweep (cheap to script, using the same offset-detection method used here)
   is worth doing as part of this ticket or deferred.
3. **Remediation of the already-present duplication is Plan's decision, not this
   investigation's** — three real options were evaluated (see below); this investigation
   recommends but does not decide.
4. **`validate_working_log.py`'s check-1 gap (does not consult `is_duplicate` before flagging
   "Duplicate ticket IDs") is a related, real defect this investigation surfaced as a side
   effect of testing current state, not something the ticket's own Scope explicitly names.**
   Whether closing it belongs to this ticket (it is adjacent to AC2/AC3's "close any coverage
   gap" framing) or should be filed as its own follow-up is an open question for Plan — this
   investigation recommends folding it in, since it is a small, well-understood, low-risk fix
   directly informed by evidence gathered here, and leaving it open means the very validator
   meant to catch exactly this class of defect stays permanently red and thus useless the
   moment anyone tries to actually enforce it.

## Anti-Drift Hazards

- **Do not rewrite, reorder, or delete any row inside the existing ~1586-row duplicate block,
  the embedded header row at line 1594, or the W36 tools.jsonl 79-line duplicate block** as
  part of closing this ticket's git-mechanics/test-coverage scope — the hard "never rewrite
  historical rows" constraint from both `TCK-20260904-WORKING-LOG-CSV-PARSER` and this
  ticket's own Scope applies to any remediation decision, and this investigation's own
  evidence-gathering only read these files, never modified them.
- **Do not conflate the squash-merge root-cause fix with an attempt to prevent squash-merges
  outright** — this ticket's Related Docs/Scope frame this as closing a test-coverage gap and
  deciding on remediation of already-present duplication, not changing the repo's GitHub
  merge-strategy settings (`gh repo view` shows `squashMergeAllowed`/`mergeCommitAllowed`/
  `rebaseMergeAllowed` are all a org/repo-level setting outside this ticket's Related Code
  Areas).
- **Do not treat the 79-line `agent-monitoring/data/2026-W36/tools.jsonl` duplication as
  something to fix in this ticket** — the ticket's Scope is about the git-merge mechanics gap
  and the `tickets/working_log.csv` duplication specifically; the W36 finding is evidence for
  "is this systemic" (ticket's own investigate-instruction #6), not a second remediation
  target, unless Plan explicitly decides to widen scope.
- **Do not silently fix `validate_working_log.py`'s check-1 `is_duplicate`-blind gap without
  flagging it as a real, separate finding** — it was discovered as a side effect of testing
  current behavior, not requested directly by the ticket's literal Scope bullets, so Plan must
  make an explicit call on whether it's in-scope (see Risk 4).
- **Do not assume the existing `tests/integrity/test_merge_union_gitattributes.py` is wrong
  or needs its assertions changed** — it correctly tests real `git merge` behavior and should
  keep passing exactly as-is; any new test for the squash-merge gap is additive, not a
  replacement.
