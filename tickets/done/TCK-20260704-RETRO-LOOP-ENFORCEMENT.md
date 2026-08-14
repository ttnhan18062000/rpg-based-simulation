---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260704-RETRO-LOOP-ENFORCEMENT
phase: done
date: 2026-07-04
tags: [agent-monitoring, retro, process-improvement, hooks]
---

# TCK-20260704-RETRO-LOOP-ENFORCEMENT

## Title
Add /agent-monitoring-retro skill and a cadence nudge hook — the retro loop has never actually run

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
`docs/guides/agent_monitoring.md` documents the retro cadence rule: run `make agent-monitoring-retro` weekly, after every 5+ completed tickets, or before changing any agent prompt/phase/tier rule. Direct data investigation found this has **never actually happened**: 299 `implement-ticket` runs have completed since `agent-monitoring/` was built (2026-06-12), but `agent-monitoring/retro/RETRO-ALL.md` is a zero-data smoke-test artifact from the tool's initial build day, never regenerated since. Concrete, measurable cost of this gap: 13.3% of events (246/1845) have empty `summary` fields — precisely the "Summary Quality" issue the retro report is designed to surface — and nobody has ever looked, because the report has never been generated for real.

The cadence rule has no enforcement mechanism — it's a sentence in a doc, competing with nothing that would actually remind anyone to act on it. Gate failures are rare (3 total across all history: 2 `DOD_BLOCKED`, 1 `NEEDS_HUMAN_INPUT`), so this isn't about a missed failure pattern — it's that the entire "what to improve" feedback loop this observability system exists to feed has been collecting data into a void.

User decisions (2026-07-04): add a real `/agent-monitoring-retro` skill (not just rely on the `make` target), and add a proactive nudge hook rather than relying on manual cadence discipline or `/loop` setup.

## Scope
- Add `.claude/skills/agent-monitoring-retro/SKILL.md` wrapping `make agent-monitoring-retro` — triggered by `/agent-monitoring-retro`, following the existing skill format (see `python-performance-optimization/SKILL.md` for the frontmatter/structure pattern).
- Add a `PostToolUse` hook to `.claude/settings.json` (mirrors the existing graphify/context-search nudge hooks) that:
  - Counts completed (`final_status`/`status` == `DONE`) `implement-ticket` runs in `agent-monitoring/runs.jsonl` with a `start_ts`/`ts` later than the newest file's mtime under `agent-monitoring/retro/RETRO-*.md` (excluding `RETRO-ALL.md`, which is not a dated weekly report).
  - Once that count crosses 5, injects `additionalContext` reminding to run `/agent-monitoring-retro` — advisory, not blocking, consistent with this repo's existing hook philosophy (nudge, don't halt the workflow).
- Update `docs/ai/skills.md` to list the new skill under "Built-in Skills" or a new "Observability" section.
- Update `docs/guides/agent_monitoring.md` if the enforcement mechanism changes how the cadence rule should be described (e.g., "the hook will remind you" rather than pure human discipline).

## Out of Scope
- Actually running the retro right now to generate a real report over the 299 accumulated runs — that's a one-time catch-up action, not part of building the tooling; can be done manually once this ticket's skill exists, or as a follow-on.
- Fixing the 13.3% empty-summary rate itself — that's a downstream finding a real retro run would surface and prioritize; this ticket only makes it possible to see it going forward.
- A hard block (rejecting further ticket work until retro runs) — explicitly rejected in favor of a nudge, matching this repo's established "hooks nudge, don't block" pattern (see `idea_agent_gate_determinism.md`'s more deliberate discussion of when escalation to a hard block is and isn't warranted).

## Acceptance Criteria
- [ ] `/agent-monitoring-retro` skill exists and runs `make agent-monitoring-retro` when invoked.
- [ ] A new hook counts completed `implement-ticket` runs since the last dated retro report and injects a reminder once the count crosses 5, without blocking any tool call.
- [ ] The hook correctly handles the "no dated retro report has ever existed" case (treats it as if the threshold was already crossed, since 299 runs already exceed 5).
- [ ] `docs/ai/skills.md` and `docs/guides/agent_monitoring.md` reflect the new skill and hook.
- [ ] Existing hooks in `.claude/settings.json` are not modified or reordered — this is purely additive.

## Related Tickets
None.

## Related Docs
- docs/guides/agent_monitoring.md (the documented, never-enforced cadence rule)
- docs/agent-monitoring/README.md
- docs/ai/skills.md
- docs/ai/agent_infrastructure_audit.md (originally flagged hooks as "nudge, don't block" as a governance characteristic — this ticket extends that same pattern to a new case rather than introducing a new philosophy)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .claude/skills/ (new: agent-monitoring-retro/SKILL.md)
- .claude/settings.json (new PostToolUse hook)
- tools/agent-monitoring/generate_retro.py (existing — wrapped, not modified)
- agent-monitoring/retro/ (existing — where the hook checks for the last dated report)
- docs/ai/skills.md
- docs/guides/agent_monitoring.md

## Assumptions / Open Questions
- The hook's ticket-count check requires reading `runs.jsonl` on relevant tool calls — this should be cheap (small file, simple JSON parse) but worth confirming it doesn't add noticeable latency to every tool call the way the existing hooks don't.
- Whether the reminder should fire on every subsequent tool call once the threshold is crossed (noisy) or only once per session — leaning toward "once per session" but left for the implementer to decide against the existing hook patterns' precedent.

## Implementation Notes

- Added `.claude/skills/agent-monitoring-retro/SKILL.md` following the
  `python-performance-optimization/SKILL.md` frontmatter/structure pattern
  (`name` + `description` frontmatter, `# Title`, "When to Use"/"What This
  Skill Does"/"Quick Start" sections). It wraps `make agent-monitoring-retro`
  and documents the retrospective process (fill in `## Notes`, commit report).
- Added `tools/agent-monitoring/retro_nudge_hook.py` as a dedicated hook
  script (mirrors the existing `pre_tool_hook.py`/`post_tool_hook.py` pattern
  rather than a fragile inline `python3 -c` one-liner, since the logic needs
  file globbing, JSONL scanning, and date parsing across legacy/new field
  names). It:
  - Reads `agent-monitoring/runs.jsonl`, tolerating both legacy (`agent`,
    `status`, `started_at`) and current (`workflow`, `final_status`,
    `start_ts`) field names — confirmed both forms exist in the real data
    (320 records use `workflow`, 8 legacy records use `agent`).
  - Computes the cutoff as the max mtime of `agent-monitoring/retro/RETRO-*.md`
    excluding `RETRO-ALL.md`. Since no dated report currently exists, the glob
    is empty and cutoff defaults to `0.0` (epoch), so every real `DONE`
    `implement-ticket` run counts — correctly treating "no dated report has
    ever existed" as "threshold already crossed", per the acceptance
    criterion. Verified live: the hook fired mid-implementation reporting
    "304 implement-ticket runs...".
  - Once count >= 5, injects `additionalContext` via
    `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "..."}}`,
    matching the exact shape used by the existing graphify/context-search
    nudge hooks.
  - Wrapped in `try/except: pass`, invoked with `2>/dev/null || true` in
    `.claude/settings.json`, so it is advisory-only and can never fail or
    block a tool call.
- **Open question resolved (fire once per session):** confirmed
  `pre_tool_hook.py`/`post_tool_hook.py` both read a real `session_id` field
  from the hook's stdin JSON payload (`payload.get("session_id", "")`) and use
  it for per-session bookkeeping (`.claude/.current_session_id`). Reused the
  same extraction. The new hook writes `.claude/.retro_nudge_state.json`
  (gitignored, alongside the other hook temp files) containing
  `{"session_id": ..., "ts": ...}` the first time it fires; on every
  subsequent call in the same session it short-circuits before doing any
  file I/O beyond reading that small state file. If `session_id` is ever
  absent from the payload (not observed in practice, but defensive), it falls
  back to a 1-hour cooldown keyed off `ts` instead of silence-forever.
- Registered the new hook as an additional entry in the `PostToolUse` array
  in `.claude/settings.json` with `matcher: "*"` (same matcher as the primary
  `post_tool_hook.py` entry — there is no tool-name-specific signal for "a
  ticket just completed", so it must re-evaluate on general tool activity;
  cost is bounded because the per-session marker short-circuits everything
  after the first nudge). No existing hook entries were modified, reordered,
  or removed — purely additive, verified by re-reading the file after the
  edit and confirming `PreToolUse` and the first two `PostToolUse` entries
  are byte-identical to before.
- Added `.claude/.retro_nudge_state.json` to `.gitignore` next to the other
  hook temp files (`.claude/.tool_start`, `.claude/.current_session_id`,
  `.claude/current_run`).
- Updated `docs/ai/skills.md`: added an "Observability" section (before
  "Configuration") describing the skill and hook, plus a row in the
  "Project-Level Skill Files" table.
- Updated `docs/guides/agent_monitoring.md`'s "When to Run" section to state
  the cadence rule is now hook-enforced (advisory, once per session, never
  blocking), not pure human discipline.
- Did not touch `tools/agent-monitoring/generate_retro.py` — wrapped as-is
  per scope.
- Out-of-scope items left untouched: did not run a real retro over the 299+
  accumulated runs (one-time catch-up, explicitly out of scope), did not fix
  the empty-summary rate.

## Test Summary
- `python3 -c "import json; json.load(open('.claude/settings.json'))"` —
  confirms the edited settings file is still valid JSON.
- Manually piped a synthetic `{"session_id": "test-session-abc", ...}`
  payload into `retro_nudge_hook.py` twice: first call printed the
  `additionalContext` nudge (304 runs detected, as expected against real
  repo data with zero dated retro reports); second call with the same
  `session_id` produced no output, confirming the once-per-session dedup via
  `.claude/.retro_nudge_state.json`.
- Live-observed the hook firing for real as a `PostToolUse:Edit` /
  `PostToolUse:Bash` hookSpecificOutput during this session's own tool calls,
  confirming the wiring in `.claude/settings.json` is live and functioning
  end-to-end, not just correct in isolation.
- No automated test suite exists for `.claude/` hooks in this repo (they are
  shell-invoked Python scripts outside pytest's collection scope, consistent
  with `pre_tool_hook.py`/`post_tool_hook.py` having no dedicated test file
  either) — verification here is manual/behavioral, matching existing
  precedent for this class of file.

## Files Changed
- `.claude/skills/agent-monitoring-retro/SKILL.md` (new)
- `tools/agent-monitoring/retro_nudge_hook.py` (new)
- `.claude/settings.json` (additive: new `PostToolUse` hook entry)
- `.gitignore` (additive: `.claude/.retro_nudge_state.json`)
- `docs/ai/skills.md` (new "Observability" section + table row)
- `docs/guides/agent_monitoring.md` ("When to Run" section updated)

## Completion Summary
Added a real `/agent-monitoring-retro` skill wrapping `make agent-monitoring-retro`,
plus a `PostToolUse` hook that advisory-nudges (once per session, never
blocking) once 5+ `implement-ticket` runs have completed DONE since the last
dated retro report — correctly treating "no dated report has ever existed" as
an already-crossed threshold, which matches the real current state (304 DONE
runs, 0 dated reports). Docs updated to reflect the hook-enforced cadence.
Purely additive to `.claude/settings.json`; no existing hooks changed.
