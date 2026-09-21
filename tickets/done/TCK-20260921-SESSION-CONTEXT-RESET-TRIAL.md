---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260921-SESSION-CONTEXT-RESET-TRIAL
phase: done
date: 2026-09-21
tags: [ai, process-improvement, agent-monitoring]
---

# TCK-20260921-SESSION-CONTEXT-RESET-TRIAL

## Title
Session context-reset at safe boundaries — a handover format, a reachability hook, a full
per-process boundary map, and a measured trial protocol against Ticket 1's real token telemetry

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Companion to `TCK-20260921-REAL-TOKEN-TELEMETRY`: the same background measurement (average context
481k/request, 72% of input from requests ≥500k, only 69 compactions over 14 real days) motivates
resetting context deliberately at real boundaries rather than letting it grow unmanaged. This
ticket builds the mechanism (a handover note format + a `SessionStart` hook that makes existing
notes reachable after `/clear`) and, per a mid-batch amendment from the user, a full boundary map
covering every agent-working process type this repo runs — not only "a batch landed."

## Scope
- (a) `SessionStart` hook (`source == "clear"`) listing `.claude/handover/*.md` paths + first-line
  titles only, as `additionalContext`. Gitignored. Keyed by role name, not `cwd`.
- (b) A ~2k-token handover note format: role, open branches/PRs, pending user decisions, pointers —
  never restating standing rules (memory/CLAUDE.md already hold them).
- (c) A full HARD/SOFT/NEVER boundary map, per the amendment: universal blockers, plus a
  per-process-type table (PR lifecycle, hand-orchestrated tickets, formal `Workflow` runs, epics,
  planning/design, investigation/retro, cross-session waits, CI triage, RPG simulation runs) — one
  short doc, `docs/guides/agent_session_reset_boundaries.md`, owning both the map and the format.
  Each relevant skill's final step gets a one-line pointer to it, not a copy.
- (d) Investigate `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, verified from an authoritative source (the
  installed CLI's own strings, or official docs) before proposing any value — leave it out if it
  can't be verified.
- (e) A trial protocol comparing avg/max context per request and cache-read/day, before and after,
  using Ticket 1's `real_token_usage.py`. Ticket 1 landed first.
- Two pieces held for direct user approval before landing (not this ticket's own call): the exact
  CLAUDE.md wording (one pointer line to the boundary doc, plus a short "batch read-only checks
  into one call" rule from the original brief), and the `.claude/settings.json` hook registration
  (affects every session in this repo). Both prepared as exact text, neither committed here.

## Out of Scope
- Actually running the "after" half of the trial protocol — this ticket cannot manufacture elapsed
  real usage under the new practice; that comparison is a real future follow-up, not claimed here.
- Any numeric `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` value — investigated and deliberately left out; see
  Assumptions/Open Questions and `investigation.md` for why.
- Committing the CLAUDE.md wording or the settings.json hook registration — both held for the
  user's own direct, verbatim-text approval, per this session's own established discipline for
  governing/shared-config files.
- Redesigning any of the 5 named skills beyond their one-line pointer — no phase/logic changes.

## Acceptance Criteria
- [x] `tools/agent-monitoring/session_start_handover_hook.py` exists, tested, fails open on every
      error/missing-directory/empty-directory case, never injects note BODIES (paths + first-line
      titles only).
- [x] `docs/guides/agent_session_reset_boundaries.md` exists: HARD/SOFT/NEVER definitions,
      universal blockers, the full per-process boundary map (verified against real skill/workflow
      behavior, not accepted as given — see Implementation Notes for the specific claims checked),
      and the handover format. Kept short by design.
- [x] 5 skills (`implement-ticket`, `implement-epic`, `create-tickets`, `agent-monitoring-retro`,
      `simq-audit`) each carry the one-line pointer; `test_workflow_meta_conformance.py` confirms
      no phase-title regression.
- [x] `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` investigated from 2 independent authoritative sources
      (installed CLI binary strings, official docs); the specific default value/semantics-with-
      this-account's-window explicitly left unconfirmed and left out of any proposed change,
      exactly per the brief's own fallback instruction.
- [x] A real "before" baseline captured via Ticket 1's tool, independently reproducing the peer's
      own quoted background figures within a few hours' expected drift; the protocol for a real
      future "after" comparison is documented, not fabricated.
- [x] The two approval-gated pieces are prepared as exact text and held, not committed —
      confirmed via `git diff` showing neither `CLAUDE.md` nor `.claude/settings.json` touched by
      this ticket's own commits.

## Related Tickets
- `TCK-20260921-REAL-TOKEN-TELEMETRY` (done) — this ticket's own trial protocol depends on that
  one's tool; landed first in the same batch.
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` (done) — the closest precedent for a real
  before/after measured trial with an honestly-stated "can't fully measure this yet" limitation.

## Related Docs
- `docs/guides/agent_session_reset_boundaries.md` (new)
- `CLAUDE.md` — pointer line prepared, not yet added (approval-gated).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260921-SESSION-CONTEXT-RESET-TRIAL/` — `investigation.md`, `plan.md`,
  `test_plan.md`.

## Related Code Areas
- `tools/agent-monitoring/session_start_handover_hook.py` (new)
- `docs/guides/agent_session_reset_boundaries.md` (new)
- `.claude/skills/{implement-ticket,implement-epic,create-tickets,agent-monitoring-retro,simq-audit}/SKILL.md`
- `.gitignore`
- `.claude/settings.json` (approval-gated, not yet touched)
- `CLAUDE.md` (approval-gated, not yet touched)

## Assumptions / Open Questions
- **Whether a background completion notice survives a `/clear` is genuinely unknown** — recorded
  as unknown in the boundary map itself, per instruction, rather than assumed either way. Would
  need a real test that deliberately risks losing a session's context to resolve, which this
  ticket does not attempt.
- **`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`'s exact default and how it interacts with this account's own
  configured auto-compact window remain unconfirmed.** A plausible reconciliation of the brief's
  own "83% doesn't fit our ~967k peaks" tension exists (an ~1.16M-token window would make 83% and
  ~967k consistent, not contradictory) — but this is a hypothesis, not a confirmed fact, and no
  proposed override value is offered on the strength of it.
- Handover notes are role-keyed, one file per role — if two concurrent sessions share a role name
  by coincidence (unlikely given this repo's own naming convention, but not structurally
  prevented), they would overwrite each other's note. Not solved here; would need a real
  reported case to justify solving.

## Implementation Notes
Verified the amendment's own boundary-map claims against real skill/workflow behavior rather than
transcribing the draft as given (the amendment explicitly asked for this): confirmed formal
`Workflow` phase agents genuinely start with fresh contexts (every phase in
`implement-ticket.js`/`implement-epic.js` dispatches via a new `Agent()` call); confirmed
hand-orchestrated tickets' post-Investigate/Plan SOFT classification against CLAUDE.md's own
Workflow Rule (`staging_artifacts/` genuinely holds the working state once written); confirmed the
epic between-children HARD classification against this same session's own real practice earlier
today (the Headroom epic close, `SEQUENCE.md` updates). Left the one claim I could not verify
(background-notice survival across `/clear`) explicitly marked unknown rather than guessed.

Investigated `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` per the explicit two-source verification bar: found
the literal string in the installed CLI binary (v2.1.278) alongside sibling threshold-override
constants, and found the mechanism (not the specific default number) corroborated in official
docs.claude.com content. Could not verify the specific default percentage or this account's actual
configured window size from a primary source I could read directly — recorded that explicitly and
left the env-var override out of the approval-gate text entirely, rather than propose a specific
number on unconfirmed grounds. The `SessionStart` hook registration itself IS fully specified and
tested, and is the only piece actually proposed for the settings.json approval gate.

Did not commit `CLAUDE.md` or `.claude/settings.json` changes — both held for the user's own
direct, verbatim-text approval, matching this session's own established, repeatedly-applied
discipline for governing/shared-config files (a peer's relay of "the user approved this" is not
itself sufficient for a change of this class; the exact text needs to reach the user directly).

## Test Summary
- `pytest tests/tools/test_session_start_handover_hook.py -v` — 8 passed.
- `pytest tests/tools/test_workflow_meta_conformance.py -q` — 25 passed, 1 xfailed (unchanged by
  the 5 skill pointer additions).
- `validate_frontmatter.py docs/guides/agent_session_reset_boundaries.md` — OK, no violations.
- Real baseline read (read-only, aggregate numbers only, nothing copied into the repo) — see
  `investigation.md` for the exact figures and their cross-check against the peer's own quoted
  background numbers.

## Files Changed
- `tools/agent-monitoring/session_start_handover_hook.py` (new)
- `tests/tools/test_session_start_handover_hook.py` (new, 8 tests)
- `docs/guides/agent_session_reset_boundaries.md` (new)
- `.gitignore` — added `.claude/handover/`
- `.claude/skills/implement-ticket/SKILL.md`, `.claude/skills/implement-epic/SKILL.md`,
  `.claude/skills/create-tickets/SKILL.md`, `.claude/skills/agent-monitoring-retro/SKILL.md`,
  `.claude/skills/simq-audit/SKILL.md` — one-line pointer each.
- `stored_artifacts/TCK-20260921-SESSION-CONTEXT-RESET-TRIAL/` (new).
- `CLAUDE.md` — landed in two passes, both with the user's own direct, verbatim approval via
  `AskUserQuestion`, never on a peer's relay alone: (1) one new bullet in "### After Work" (later
  replaced, see next) and one new bullet in "## Proactive Tool Use" (batch independent read-only
  checks into one call); (2) the "After Work" bullet REPLACED with a version naming four concrete
  stopping points (ticket closed, `Workflow` run finished, plan/batch handed off, a wait begun on
  another session's report), plus a new sentence appended to PR Lifecycle step 6 and a new sentence
  appended to CI Failure Triage step 5 — both pointing at the same boundary doc at the exact moment
  each of those flows reaches its own natural stopping point. Confirmed via `git diff origin/main
  -- CLAUDE.md` that the full diff contains exactly these four bullets/sentences and nothing else.
- `.claude/settings.json` — the `SessionStart` hook registration, also with direct user approval,
  new array (nothing existed to merge into, confirmed via `grep` beforehand); JSON validated after.

## Completion Summary
Built and tested the reachability mechanism (hook + gitignored handover directory) and the single
short doc that owns both the handover format and the full per-process boundary map the user's own
mid-batch amendment asked for — verified against real skill/workflow behavior rather than
transcribed as given, with the one genuinely unknown claim (background-notice survival across
`/clear`) left explicitly unknown. Investigated the auto-compact override env var to the two-source
verification bar the brief set, confirmed the mechanism but not its exact default, and correctly
left the numeric proposal out rather than guess. Captured a real, independently-corroborating
"before" baseline via Ticket 1's own tool and documented the trial protocol for measuring a real
future "after," without fabricating a comparison that hasn't happened yet.

Both governing-file changes landed across two rounds, each with the user's own direct, literal-text
approval obtained independently via `AskUserQuestion` — never committed on a peer's relay of "the
user approved this" alone, matching this session's own standing, repeatedly-applied rule for
`CLAUDE.md`/`.claude/settings.json`. Round 1: the reset-boundary pointer, the batch-read-only-checks
rule, and the `SessionStart` hook registration, verified with a real smoke test (piping
`{"source":"clear"}`/`{"source":"startup"}` into the hook against a genuine handover note in this
checkout, not just the synthetic suite). Round 2: extended the reset-boundary reminder to every
process the boundary map covers — the "After Work" bullet replaced with one naming concrete
stopping points, plus a sentence each appended to PR Lifecycle step 6 and CI Failure Triage step 5.
Every round's `CLAUDE.md` diff against `origin/main` was read back and confirmed to contain only
the approved lines before pushing. No known material gap left unstated.
