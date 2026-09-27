---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX
artifact_type: investigation
phase: inprogress
date: 2026-09-25
tags: [observability, testing]
---

# Investigation — TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX

## Trigger

The user inspected the monitoring files this branch actually emitted and found
`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`'s per-ticket write path never
fired in practice for `runs.jsonl`/`events.jsonl`. agent-working-design verified this independently
and relayed the findings; this investigation re-derives and extends them directly against the real
code and real emitted files rather than trusting the relay.

## What the branch actually emits — confirmed directly

```
git diff --name-status origin/main origin/github-delivery-process-epic -- agent-monitoring/data/
```
(re-run against the branch's state as of this investigation; shape unchanged from the finding that
triggered it):

- `A  agent-monitoring/data/2026-W39/<TCK-ID>.tools.jsonl` for several tickets — the per-ticket
  `tools.jsonl` path (`post_tool_hook.py`) **does** fire.
- `M  agent-monitoring/data/2026-W39/events.jsonl`, `M ... runs.jsonl` — **every single ticket's**
  run/event records landed in the shared files. Zero `.runs.jsonl`/`.events.jsonl` per-ticket files
  were ever created, despite `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE`'s own
  Acceptance Criteria and Test Summary claiming otherwise.

## Root cause 1 (headline) — a fourth, unmigrated copy of the write-target formula

`tools/agent-monitoring/record_hand_orchestrated_closure.py` (lines ~321-330) — the wrapper
CLAUDE.md instructs **every hand-orchestrated ticket close** to use, and the one every ticket in
today's batch actually went through — still hardcodes the shared paths:

```python
iso_week = datetime.now(timezone.utc).strftime("%G-W%V")
runs_file = Path("agent-monitoring/data") / iso_week / "runs.jsonl"
events_file = Path("agent-monitoring/data") / iso_week / "events.jsonl"
...
run_ok = write_line(runs_file, json.dumps(run_record, separators=(",", ":")))
...
events_ok = write_lines(events_file, lines)
```

This script calls `record_run.validate_record()`, `record_events.validate_record()`,
`record_events.warn_vocabulary_drift()`, and `record_events.compute_tool_stats()` — reusing those
modules' *validation* logic — but **never calls their write functions**. It reimplements the
file-write step inline, using the pre-`TCK-20260924-...` hardcoded shared path. `record_run.py` and
`record_events.py` themselves were correctly updated to branch on an identifier; this wrapper was
missed entirely. `TCK-20260924-...`'s own test suite exercised `record_run.append_run_record()` /
equivalent write functions directly, never the wrapper real closes go through — a green test suite
proved the writer works, not that the writer is the one being called. (Confirmed: this pattern —
"unit tests over a component don't prove that component is on the call path a real close takes" —
is this investigation's central methodological finding, echoed in every defect below.)

## Root cause 2 — a fourth AND fifth copy exist; the "3-copy" framing undercounted

A full sweep (`grep -rn '"agent-monitoring/data"' tools/ .claude/` plus `grep -rn iso_week`)
across every file that constructs an `agent-monitoring/data/<week>/...` write path finds **five**
independent copies of "compute iso_week, then either `<id>.<kind>.jsonl` or `<kind>.jsonl`":

| # | File | Keys by | Branches per-identifier? |
|---|---|---|---|
| 1 | `tools/agent-monitoring/record_run.py` | `run_id` | Yes |
| 2 | `tools/agent-monitoring/record_events.py` | `run_id` | Yes |
| 3 | `tools/retrieval_events.py` | `run_id` | Yes |
| 4 | `tools/agent-monitoring/record_hand_orchestrated_closure.py` | — (hardcoded shared) | **No — the headline bug** |
| 5 | `tools/agent-monitoring/shadow_reviewer_events.py` | — (hardcoded shared) | **No — a second, independent miss** |

`post_tool_hook.py` (`tools.jsonl`) is a sixth site, correctly branching, but keys by `ticket_id`
(see Root cause 3).

`shadow_reviewer_events.py` (`TCK-20260904-SHADOW-REVIEWER-LOGGING`) writes shadow-candidate-review
events, always to the shared `events.jsonl` — no per-identifier branch was ever added, unlike
`record_events.py`/`retrieval_events.py` which at least attempted one. Its own docstring says it is
"deliberately NOT built on top of `tools/retrieval_events.py`" and reproduces the pattern directly —
which is exactly how it ended up as an independent, out-of-sync copy. Narrower blast radius than
Root cause 1: it only fires when the full `Workflow`-based `implement-ticket.js` pipeline runs a
shadow-reviewer candidate, not during hand-orchestrated closures (today's actual usage pattern) —
but it is a real, confirmed 5th (6th counting `post_tool_hook.py`) site, not a hypothetical one.

**No sixth copy found** beyond these — the sweep's grep patterns (`"agent-monitoring/data"`,
`iso_week`) cover every module that constructs a write path by construction, and every other hit
(`generate_retro.py`, `build_index.py`, `verify_referential_integrity.py`, etc.) is a **read**-side
`DEFAULT_*_FILE`/`DATA_DIR` constant used for globbing across the whole `agent-monitoring/data/`
tree, not a per-identifier write-target computation.

## Root cause 3 — the identifier itself disagrees across the sites that do branch

- `record_run.py`, `record_events.py`, `retrieval_events.py` all key by **`run_id`**.
- `post_tool_hook.py` keys by **`ticket_id`** — a different field, read from a different place
  (the `.claude/current_run` sidecar's `ticket_id` key, vs. the caller-supplied `run_id` argument
  the other three receive directly).

In practice, every hand-orchestrated session this batch set `run_id == ticket_id` in its own
sidecar (confirmed: every `.claude/current_run` write this session used the same TCK-ID string for
both fields) — so this divergence has been latent, not yet causing an actual file split. It is
still a real defect: nothing enforces the two stay equal, and a future session that sets them
differently (e.g. a multi-ticket batch `run_id` distinct from any single `ticket_id`) would split
`tools.jsonl` from `runs.jsonl`/`events.jsonl` silently.

## The user's design decision, confirmed via agent-working-design

**Key per PR/batch, not per ticket.** This 14-ticket batch should have produced exactly **three**
files for the whole PR (`<batch-id>.runs.jsonl`, `<batch-id>.events.jsonl`,
`<batch-id>.tools.jsonl`), not up to ~42 (14 tickets × 3 kinds). The unit of squash-merge-conflict
avoidance is the PR/branch, not the ticket — multiple tickets on one branch already don't conflict
with *each other* (they're sequential commits on one branch); the conflict this whole effort exists
to avoid is between **two different branches'** concurrent monitoring writes at merge time. A
per-ticket key was already finer-grained than the actual failure mode requires.

## Design questions resolved directly, not assumed

**What identifier is visible at write time, and how, without a subprocess.**
`post_tool_hook.py` fires on every tool call with no existing subprocess use anywhere in the file
(confirmed: `grep -n "subprocess\|Popen" post_tool_hook.py` — zero hits) — adding a `git
rev-parse`/`git symbolic-ref` shell-out per call would be a new, real cost on the hottest path in
the system. Resolved without a subprocess: read `.git` directly.

- In a git **worktree** checkout (this repo's normal mode — confirmed: `cat .git` in this worktree
  prints `gitdir: /home/u24desktop/Working/rpg-based-simulation/.git/worktrees/doc-tag-enforcement`,
  a gitlink **file**, not a directory), the real per-worktree `HEAD` lives at
  `<that gitdir>/HEAD`, not at `.git/HEAD` (which doesn't exist as a real file here at all).
- In a plain (non-worktree) checkout, `.git` is a real directory and `.git/HEAD` is the file
  directly.
- That `HEAD` file's content is either `ref: refs/heads/<branch>\n` (attached — the common case;
  confirmed live: this worktree's real `HEAD` currently reads
  `ref: refs/heads/github-delivery-process-epic`) or a raw 40-hex-character commit SHA (**detached**
  HEAD — the exact case `git rev-parse --abbrev-ref HEAD` would misreport as the literal string
  `"HEAD"`, per agent-working-design's warning; a bare file read makes this distinguishable instead
  of ambiguous).
- Two small file reads (`.git`, then the resolved `HEAD`), no subprocess, no parsing beyond a
  `startswith("ref: ")` check. Cheap enough to redo on every `post_tool_hook.py` invocation without
  needing a disk-based cache for correctness — though a module-level memoization is added anyway
  (see plan.md) since nothing prevents an in-process reuse of the same resolved value within one
  Python process lifetime (`record_hand_orchestrated_closure.py`'s own single invocation calls the
  resolver multiple times — once per file kind).

**Detached-HEAD fallback — must not silently become the shared file.**
agent-working-design's own session ran detached all day, so this is not a hypothetical edge case
in this repo's actual usage. Plan: a small `.claude/current_batch` sidecar (parallel to the
existing `.claude/current_run` pattern already used reliably throughout this session), written
once whenever the resolver successfully reads a real branch name, read as the fallback whenever
`HEAD` resolves to a raw SHA. Self-healing: the first non-detached invocation in a worktree
populates it; every later detached invocation in that same worktree recovers the last known real
identifier instead of degrading immediately. Only if *both* the live branch read and the sidecar
fallback are unavailable does the resolver fall back to a clearly-labeled `detached-<short-sha>`
identifier with a printed warning — never the bare shared filename.

**Consolidation compatibility.** `tools/agent-monitoring/monitoring_consolidation.py`'s
`consolidate_jsonl_kind()` discovers per-identifier files via `week_dir.glob(f"*.{kind}.jsonl")` —
generic over whatever prefix precedes `.<kind>.jsonl`. It does not parse or validate the prefix
itself anywhere. **Confirmed compatible with a per-PR/batch identifier unchanged** — the "delete
only after a successful fold-in" property is per-file, not per-identifier-shape, so it needs no
code change, only new/updated tests describing the new identifier shape in its fixtures.

**The `implement-ticket.js:631` read-path gap — narrower than first described, still worth fixing.**
That line does `from record_events import ...; load_jsonl(record_events.EVENTS_FILE)`. Confirmed
directly: `record_events.py` **no longer defines `EVENTS_FILE` as a module attribute at all**
(`grep -n "^EVENTS_FILE" record_events.py` — zero hits; removed by
`TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, predating this whole epic). The embedded Python
snippet is wrapped in `try/except: pass`, so this has been a **silent `AttributeError`, already a
permanent no-op, since before this epic started** — not a live correctness risk this ticket's
redesign newly introduces or worsens; it was already fully inert. Still fixed here (cheap, once the
shared resolver exists, and this ticket is already touching every other write/read site of the same
shape) rather than left broken with a note, since leaving a known dead branch behind after finding
it would be worse than the disclosed-gap precedent this repo otherwise follows.

## Branch decision

agent-working-design relayed the user's explicit decision: **land this on
`github-delivery-process-epic`, riding PR #246** — not a fresh branch off `origin/main`. Reasoning
(confirmed sound): the defect is in code this same PR introduces; shipping #246 with a per-PR write
path that never fires in the repo's actual (hand-orchestrated) usage would land a feature that is
inert on the only path that matters today.

**Consequence, disclosed rather than discovered by a reviewer:** this fix changes the shape of the
very files this branch's own earlier commits wrote. Rows from every ticket before this one's own
commit land in the shared `2026-W39/{runs,events}.jsonl`; rows from this ticket onward land in the
new per-PR file. Both are visible in the same PR diff. This is the correct, disclosed final state
of a mid-PR migration — not a leftover bug — and is stated as such in this ticket rather than left
for a reviewer to puzzle out.

## Acceptance evidence, not inference

Per agent-working-design's explicit instruction: once the fix lands, this branch's own next
hand-orchestrated closure must itself land in a single per-PR file, checked directly against the
real emitted file after pushing — not inferred from a passing test suite. (This investigation's own
central finding — a green test suite over the writer functions proved nothing about which writer a
real close calls — is exactly the failure mode a "trust the tests" acceptance check would repeat.)
