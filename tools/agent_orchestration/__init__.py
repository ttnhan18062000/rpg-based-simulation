"""Validator/generator tooling for the agent-orchestration/ provider-neutral contract.

See agent-orchestration/README.md and docs/architecture/agent_orchestration_contract.md for
what this contract is. This package only reads/writes under agent-orchestration/ (validation)
or, via the explicit generation flag, files the caller names (generation) — see generator.py's
write-guard. It never touches tools/agent-monitoring/, .claude/, or tools/agent_replay/.
"""
