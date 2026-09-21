# Investigation — TCK-20260921-SESSION-CONTEXT-RESET-TRIAL

## (d) `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` — verification result

Explicitly instructed to verify from an authoritative source (official docs or the installed
CLI's own strings) before using, and to record + leave it out rather than guess if unverifiable.

**Confirmed, from the installed CLI binary's own strings (v2.1.278,
`~/.local/share/claude/versions/2.1.278`)**: the literal string `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`
exists, alongside sibling constants (`DISABLE_AUTO_COMPACT`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`,
`testPctOverride`, `CLAUDE_CODE_BLOCKING_LIMIT_OVERRIDE`, `table_no_match`/`table_exact`/
`table_default`/`matchedWindowKey`) consistent with a real threshold-override mechanism.

**Confirmed, from official docs (docs.claude.com — read via search-engine-surfaced excerpts; a
direct `WebFetch` of the settings page itself failed with a TLS error, the same class of network
restriction this repo's own CLAUDE.md already documents for other hosts)**: `CLAUDE_AUTOCOMPACT_
PCT_OVERRIDE` is genuinely mentioned in official Claude Code documentation, described as
controlling when compaction triggers "partway through the auto-compact window rather than when the
window fills," and stated to apply to subagents as well. `CLAUDE_CODE_AUTO_COMPACT_WINDOW` is a
separate, sibling variable controlling the window SIZE itself (in absolute tokens), not the
percentage threshold within it.

**NOT confirmed from a primary source I could read directly**: the specific default percentage.
Every source giving a number (~83%, "1-100 accepted", "clamped so it can only lower, never raise,
the threshold") is a third-party blog post or a GitHub issue (user reports, not confirmed platform
behavior) — exactly the class of source the brief said to distrust. I could not independently
verify this number from the CLI's own strings (the binary confirms the mechanism exists, not its
numeric default) or from a primary docs page I could load directly (blocked by network
restriction).

**A plausible but unconfirmed reconciliation of the brief's own tension** ("our observed ~967k
peaks don't fit the reported ~83% default"): 83% of a 200K-token window is ~166K, nowhere near
967K — but 83% of a ~1.16M-token window is ~967K almost exactly. If this account's actual
auto-compact window (via `CLAUDE_CODE_AUTO_COMPACT_WINDOW` or an extended-context model default)
is closer to ~1.16M than 200K, the observed peaks and the third-party-reported 83% default are NOT
actually in tension — they're consistent, just against a larger window than the third-party posts
assumed. This is a plausible explanation, not a confirmed one; I have no way to read this account's
actual configured window size from here.

**Decision, per the brief's own explicit fallback**: recommend NOT proposing a specific numeric
`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` value in the settings.json approval-gate text. The mechanism's
existence is confirmed; its exact default and this account's specific window size are not, and
guessing a number to write into a shared, every-session-affecting settings file is exactly the
class of action this repo's own risk-handling convention exists to prevent. The SessionStart hook
registration (item a) IS fully specified and tested — that part of the settings.json change is
ready; the env-var override is not, and is left out.

## (a)-(c) Hook, handover format, boundary map

Built and tested `tools/agent-monitoring/session_start_handover_hook.py` (8 tests, real subprocess
invocation for the I/O contract, direct calls for the listing logic) and
`docs/guides/agent_session_reset_boundaries.md` (the map + handover format, kept short per
instruction — read at every boundary). Verified the map's own claims against real skill/workflow
behavior rather than accepting the peer's draft as given:
- "Formal Workflow runs: phase agents already get fresh contexts" — confirmed: every phase in
  `implement-ticket.js`/`implement-epic.js` dispatches via a new `Agent()` call, which starts with
  no prior conversation history. Only the orchestrating session's own context is what a reset
  boundary is ever about for this row.
- "Hand-orchestrated ticket: after Investigate/Plan = SOFT" — confirmed against CLAUDE.md's own
  Workflow Rule ("Before Work" creates `staging_artifacts/{ticket_id}/` with `plan.md`/
  `investigation.md`; "During Work" keeps them aligned with actual work) — once those exist, the
  working state genuinely lives in files, not just conversation.
- "Whether a background completion notice survives `/clear`" — left explicitly as **unknown**, per
  instruction, rather than assumed either way; no way to test this without actually losing this
  session's own context to find out.
- "Epic: between children, `SEQUENCE.md` updated = HARD" — confirmed against this session's own
  repeated real practice this same day (the Headroom epic close and its child-ticket handling).

## (e) Trial protocol and real baseline

Captured a real "before" baseline via Ticket 1's own tool, read-only, aggregate numbers only (no
raw content copied anywhere): `real_token_usage.py --since 2026-09-07` — 40,250 requests, 69
compaction boundaries, average context 482k/request, max 968k, 19,174.9M cache-read tokens total.
Independently reproduces the peer's own quoted background figures almost exactly (40,039 vs.
40,250 requests — a few more hours of real usage passed between the two reads; every other figure
matches within rounding), confirming the tool itself is measuring the same real thing the peer's
own scratch scripts measured.

**Protocol, to run for real once the handover/reset practice has been in use for a comparable real
period** (this ticket cannot manufacture an "after" — that requires real elapsed usage):
1. Re-run the identical command (`real_token_usage.py --since <post-adoption date>`) over a window
   of comparable length to the 14-day baseline above.
2. Compare, specifically: average context/request, max context/request, and cache-read tokens/day
   (the single largest cost driver per the baseline's own totals — ~78% of all tokens).
3. A real improvement claim needs the comparison to control for the same confound this repo's own
   `CLAUDE.md` already names for cross-ticket cost comparisons — different sessions/batches differ
   by orders of magnitude in scope, so compare like periods (e.g., a full week against a full
   week), not cherry-picked days.
4. Record the result in a follow-up to this ticket, not assumed here.
