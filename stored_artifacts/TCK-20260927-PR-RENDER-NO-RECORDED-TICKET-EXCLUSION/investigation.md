---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION
artifact_type: investigation
tags: [delivery, ai]
---

# Investigation: TCK-20260927-PR-RENDER-NO-RECORDED-TICKET-EXCLUSION

## Confirmed premise (both submissions of evidence re-verified directly)

Re-ran the exact isolated repro the ticket's Request Summary cites, from this session's own PR
#251 checkout, before writing any code:

```python
from tools.delivery import pr_render
result = pr_render.render()  # untouched, real commit-subject discovery
full_body = result["body"]
minimal_lines = [l for l in full_body.splitlines()
                 if "MONITORING-BATCH-SIDECAR-UNSEEDED" not in l]
# ...strip its id from Closes:...
comparison = pr_render.compare_generated_body(minimal_body, full_body, spec)
```
Result: `differing_sections == ['## What landed', '## Tickets', '## Why', '## Verification', 'Closes:']`
— matches the ticket's own cited output exactly. Confirmed real, not a stale claim.

## Open Question resolved: does anything else consume `discover_tickets()`?

```
grep -rln "discover_tickets\|from tools.delivery import pr_render\|from pr_render import\|import pr_render" tools/ tests/
```
Result: only `tools/delivery/pr_render.py` (itself) and `tests/tools/test_delivery_pr_render.py`.
`tools/delivery/pre_push_advisory_hook.py` — read in full — does not import `pr_render` or call
`discover_tickets()` at all; it has its own independent commit-subject scan
(`check_commit_subjects()`) for a different purpose (advisory subject-format checking, not PR-body
rendering). **No other consumer exists today**, so there is no risk of a pre-exclusion set being
fed to the wrong place — resolved cleanly, no design accommodation needed for a second consumer.

## Design: where the exclusion record lives

**Retraction, same session, before implementation started.** The first pass of this investigation
chose a committed JSON file, `tools/delivery/pr_exclusions.json`, reasoning that "the exclusion
file's lifecycle is bounded by the branch's own lifecycle for free" because a finished branch gets
deleted after squash-merge. **That reasoning was wrong** — the design peer caught it, and I
verified the correction myself before accepting it rather than taking their word for it: a
squash-merge produces one commit on `main` containing the full diff of the source branch; deleting
the source branch ref afterwards removes only the ref, not content already committed onto `main`.
I have first-hand evidence of exactly this mechanism from earlier in this same session — the
`monitoring-and-delivery-batch-2.*.jsonl` per-identifier shard files landed on `main` when PR #250
merged and stayed there, needing an explicit follow-up commit to consolidate away; nothing about
that branch's deletion removed them automatically. A committed `pr_exclusions.json` would suffer
the identical fate: it lands on `main` at merge, accumulates across every PR that ever used it
(since nothing deletes old entries), and two concurrent PRs recording an exclusion in the same
shared file conflict at merge time — the same shared-file class this lane has already spent
tickets fixing for `tickets/working_log.csv` and `docs/REGISTRY.yaml`. Rejected.

**Adopted instead: an HTML comment embedded in the PR body itself**
(`<!-- pr-render:exclude TCK-... reason="..." -->`), the peer's own proposed alternative, verified
sound rather than accepted on say-so:

- Never touches git history — it lives in GitHub's own PR `body` field, not a repo file. No
  squash-merge accumulation, no cross-PR shared-file conflict, because it is scoped to exactly one
  PR by construction (GitHub gives every PR its own `body`).
- `check_against_live()` already fetches the live PR's `title`/`body` via `gh pr view --json
  title,body` (line ~314 pre-fix) — reading the exclusion comments back out of that same fetch is
  free, no new I/O.
- Satisfies AC3 genuinely: a `--check --pr N` run with no operator flags reads the exclusions from
  the live body it already has to fetch anyway, so any session or CI job reproduces the same
  result with zero remembered state.
- Consistent with existing precedent already in this exact module — `_REVIEW_NOTES_PLACEHOLDER`
  is itself an HTML comment (`"<!-- UNFILLED: write review notes by hand before opening the PR
  -->"`), so an HTML-comment-as-machine-readable-marker convention is not new here.
- Bootstrapping: before a PR exists, there is no live body to read from yet, so the *first* render
  (used to compose the initial `--body-file` for `gh pr create`) takes the exclusion from a CLI
  flag — which also causes `render()` to emit the comment into its own output, so the created PR's
  body carries the marker from the start and every later `--check` can read it back.

## Existing precedent for the record's shape

Not applicable in the same way after the retraction above — there is no separate file/registry
shape to design; the record's shape is the HTML comment's own regex-matched fields
(`ticket_id`, `reason`), embedded directly in rendered body text near `Closes:`.

## Resolved Open Question: exclusion reason

**Required, not optional** — the ticket's own leaning. A reason-less exclusion is indistinguishable
from an accidental omission to a later reader (exactly the ambiguity `review_notes_hand_filled`
exists to avoid for the Review-notes case); requiring it costs nothing at record time and pays off
every time someone re-reads the file.
