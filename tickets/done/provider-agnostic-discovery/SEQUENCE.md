# Implementation Sequence — provider-agnostic-discovery

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260721-PROVIDER-AGNOSTIC-EPIC  (epic tier — scope-only parent, tracks the 5 children below; no deps in this batch)
2. TCK-20260721-AGENTS-DIR-DISPOSITION  (depends on: TCK-20260721-PROVIDER-AGNOSTIC-EPIC — can run in parallel with #3, #4)
3. TCK-20260721-CODEX-CAPABILITY-MATRIX  (depends on: TCK-20260721-PROVIDER-AGNOSTIC-EPIC — can run in parallel with #2, #4)
4. TCK-20260721-MONITORING-WRITER-DECISION  (depends on: TCK-20260721-PROVIDER-AGNOSTIC-EPIC — can run in parallel with #2, #3)
5. TCK-20260721-ORCHESTRATION-CONTRACT-ADR  (depends on: TCK-20260721-AGENTS-DIR-DISPOSITION, TCK-20260721-CODEX-CAPABILITY-MATRIX, TCK-20260721-MONITORING-WRITER-DECISION — must not start until all three land)
6. TCK-20260721-CODEX-REPLAY-PROOF  (depends on: TCK-20260721-CODEX-CAPABILITY-MATRIX, TCK-20260721-MONITORING-WRITER-DECISION, TCK-20260721-ORCHESTRATION-CONTRACT-ADR — last in the sequence)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place — in
particular, tickets 5 and 6 both consume evidence produced by earlier tickets and must not
lock in decisions ahead of that evidence landing. Tickets 2, 3, and 4 have no dependency on
each other and may be implemented in parallel once the parent epic (#1) is scoped.
Re-run `/implement-epic` with the same folder after any gate failure — already-done tickets
are skipped automatically.

## Containment Rule (applies to all 5 child tickets, #2-#6)

Every child ticket in this batch may create only isolated contract, replay, fixture,
diagnostic, or decision-record work. None may modify production Claude/Codex workflows,
hooks, monitoring writers, live ticket artifacts, or the shared monitoring JSONL corpus.
This is a discovery-only epic — no provider-runtime implementation ticket may be created
until all 5 discovery outputs (from tickets #2-#6) are complete, evidence-backed, and
explicitly approved. See the parent epic (TCK-20260721-PROVIDER-AGNOSTIC-EPIC) for the
full exit-gate criteria.

## Known Open Decisions (deliberately not pre-resolved by this batch)

Several tickets carry explicit open questions that must be resolved during that ticket's
own Scope/Investigate phase, not assumed from this planning session:

- **TCK-20260721-AGENTS-DIR-DISPOSITION**: whether `WorkflowRegistry` (`src/lab/registry.py`)
  is intended future production wiring or itself dead/unwired code — it is currently
  instantiated nowhere in `src/`, only referenced by its own test file.
- **TCK-20260721-ORCHESTRATION-CONTRACT-ADR**: which ADR filename/numbering convention to
  adopt — no repo-wide convention currently exists; the two real precedent docs
  (`docs/architecture/simulation_watchdog.md`, `performance_optimization.md`) both ignore
  the one unused template that prescribes numbered `ADR-XXX` files.
- **TCK-20260721-CODEX-REPLAY-PROOF**: whether "must not invoke production hooks" permits
  sandboxed/isolated-cwd invocation of the real hook scripts (mirroring
  `test_post_tool_hook.py`'s existing pattern) or requires avoiding those scripts entirely.

## Related, Not Duplicated

This batch was created from `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md`,
itself derived from `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md`
after 5 rounds of cross-agent review (Claude Code + Codex). A separate finding,
`idea_provider_agnostic_agent_orchestration_finding_01_claude.md`, discovered mid-review that
`.agents/workflows/` and `.agents/skills/` are live-parsed by `WorkflowRegistry` with a
currently-passing test dependency — this is folded into TCK-20260721-AGENTS-DIR-DISPOSITION's
scope, not tracked as a separate ticket.
