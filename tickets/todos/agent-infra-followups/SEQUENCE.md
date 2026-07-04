# Agent Infra Follow-ups — Implementation Sequence

Five tickets filed 2026-07-04 from investigating the AI agent orchestration layer beyond the
original audit (`docs/ai/agent_infrastructure_audit.md`): a hardcoded-timestamp bug and a missing
revert mechanism in `UpdateSimulationKnowledgeWorkflow`, three underused skills never wired into
`CLAUDE.md`'s proactive-invocation table, a retro loop that's never actually run, and an
uncontrolled ticket-tag vocabulary. None of these share a hard blocking dependency — this order is
a recommendation (quick, isolated wins first; design-heavy standard-tier work last), not a
dependency chain `implement-epic` must enforce.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260704-LABKNOWLEDGE-TIMESTAMP | Tiny, isolated hotfix (two hardcoded literals in `src/lab/workflows.py`) — do first as a quick win, and because ticket 5 below touches the same file/function; landing this first avoids ticket 5 having to rebase around it |
| 2 | TCK-20260704-SKILL-TRIGGER-COVERAGE | Independent, doc-only (`CLAUDE.md` table rows), no code risk — quick win |
| 3 | TCK-20260704-RETRO-LOOP-ENFORCEMENT | Independent (new skill + new hook, additive to `.claude/settings.json`), small-medium scope |
| 4 | TCK-20260704-TAG-TAXONOMY | Independent, but standard tier — more design work than 1-3 (needs a taxonomy doc + validator changes + agent prompt update) |
| 5 | TCK-20260704-LABKNOWLEDGE-REVERT | Standard tier, the largest and most novel of the five (real feature design, not a mechanical copy of an existing pattern); benefits from ticket 1 being done first since both touch `UpdateSimulationKnowledgeWorkflow` |

## Dependency Notes
- Tickets 2-4 have no dependencies on each other or on tickets 1/5, and can be done in any order
  relative to each other.
- Ticket 1 and ticket 5 both touch `src/lab/workflows.py`'s `UpdateSimulationKnowledgeWorkflow` —
  their own tickets explicitly describe them as unrelated concerns (a bug fix vs. a new feature),
  not a technical prerequisite. Sequencing ticket 1 first is a hygiene recommendation (small fix
  before a bigger change to the same function) rather than a hard requirement — ticket 5 does not
  functionally depend on ticket 1's fix.
- Ticket 5 is the only one requiring the full standard-tier pipeline (Investigate → Plan →
  Architecture Review) before implementation — expect it to take meaningfully longer than 1-4.
