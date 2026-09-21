# Plan — TCK-20260921-SESSION-CONTEXT-RESET-TRIAL

1. Write `tools/agent-monitoring/session_start_handover_hook.py` — reads stdin, checks
   `source == "clear"`, lists `.claude/handover/*.md` paths + first-line titles only as
   `additionalContext`, fails open on any error. Tests via real subprocess (I/O contract) +
   direct calls (listing logic).
2. Gitignore `.claude/handover/` — session-local working state, meaningless in another clone.
3. Write `docs/guides/agent_session_reset_boundaries.md`: HARD/SOFT/NEVER definitions, universal
   blockers, the full per-process-type boundary map (amended scope, from the user directly, to
   cover every agent-working process type, not just "batch landed"), and the handover note format
   (~2k tokens, keyed by role name). Kept short — read at every boundary.
4. Add a one-line "evaluate reset boundary per `docs/guides/agent_session_reset_boundaries.md`"
   pointer to the final step of 5 skills: `implement-ticket`, `implement-epic`, `create-tickets`,
   `agent-monitoring-retro`, `simq-audit`. Committable directly, per the batch's own approval-gate
   split.
5. Investigate `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` per the explicit verify-or-leave-out instruction —
   see `investigation.md`. Verified the mechanism's existence and basic semantics from the
   installed CLI's own strings and official docs; could not verify the specific default value from
   a primary source. Decision: leave the env-var override out of the settings.json approval-gate
   text entirely, per the brief's own fallback instruction.
6. Capture a real "before" baseline via Ticket 1's tool (read-only, aggregate numbers only) and
   record the trial protocol for a real future "after" comparison — this ticket cannot manufacture
   elapsed real usage, so the "after" measurement is a follow-up, not claimed here.
7. Prepare, but do NOT commit, the two approval-gated pieces: (a) one CLAUDE.md pointer line to the
   new boundary doc, plus a short new "batch read-only checks into one call" rule (from the
   original brief, unrelated to the amendment); (b) the `SessionStart` hook registration JSON for
   `.claude/settings.json` (the env-var override is not part of this, per step 5). Exact text goes
   in the end-of-batch report for the user to see verbatim before it lands.
8. Close via the standard hand-orchestrated path, folded into this same batch's single close-out
   with Ticket 1.
