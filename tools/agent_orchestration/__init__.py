"""Validator/generator tooling for the agent-working/agent-orchestration/ provider-neutral contract.

See agent-working/agent-orchestration/README.md and docs/architecture/agent_orchestration_contract.md for
what this contract is. This package only reads/writes under agent-working/agent-orchestration/ (validation)
or, via the explicit generation flag, files the caller names (generation) — see generator.py's
write-guard. It never touches tools/agent-monitoring/, .claude/, or tools/agent_replay/.
"""
