"""Generation command for the agent-orchestration/ contract.

Materializes a validated ContractBundle (see loader.py) as YAML files under a target directory.
Kept as a separate module from loader.py so the "read/validate" and "write" concerns stay
physically separated — this also keeps the write-guard's AST scan simple (only this file ever
performs filesystem writes).

Structural write-guard: `generate()` refuses to write to any resolved path outside
`agent-orchestration/` unless the caller explicitly passes `allow_outside_contract=True`. This is
a real path-containment check performed before every write, not a docstring convention and not a
generic --output-dir flag with no default restriction.

Zero network calls: this module only performs local filesystem I/O and YAML serialization.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml

from .errors import GeneratorWriteGuardError
from .loader import ContractBundle, RoleEntry, load_contract

_CONTRACT_SUBDIR = "agent-orchestration"


def _assert_write_allowed(repo_root: Path, target_path: Path, allow_outside_contract: bool) -> None:
    if allow_outside_contract:
        return
    contract_root = (repo_root / _CONTRACT_SUBDIR).resolve()
    resolved_target = target_path.resolve()
    if not resolved_target.is_relative_to(contract_root):
        raise GeneratorWriteGuardError(
            f"{target_path}: refuses to write outside {contract_root} "
            "without allow_outside_contract=True"
        )


def _write_yaml(repo_root: Path, path: Path, data: dict, *, allow_outside_contract: bool) -> None:
    _assert_write_allowed(repo_root, path, allow_outside_contract)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _role_entry_to_dict(role: RoleEntry) -> dict:
    data = asdict(role)
    data.pop("source_path")
    if data.get("inline_prompt_exception") is None:
        data.pop("inline_prompt_exception")
    return data


def generate(
    repo_root: Path,
    target_dir: Path,
    *,
    allow_outside_contract: bool = False,
) -> list[Path]:
    """Validate the contract at `repo_root` and materialize it as YAML files under `target_dir`.

    Returns the list of paths written. Raises GeneratorWriteGuardError before any write happens
    if `target_dir` resolves outside `repo_root / "agent-orchestration"` and
    `allow_outside_contract` is not True.
    """
    bundle: ContractBundle = load_contract(repo_root)

    written: list[Path] = []

    contract_path = target_dir / "contract.yaml"
    _write_yaml(repo_root, contract_path, bundle.contract, allow_outside_contract=allow_outside_contract)
    written.append(contract_path)

    workflow_path = target_dir / "workflows" / "implement-ticket.yaml"
    _write_yaml(repo_root, workflow_path, bundle.workflow, allow_outside_contract=allow_outside_contract)
    written.append(workflow_path)

    for role in bundle.roles:
        role_path = target_dir / "roles" / role.source_path.name
        _write_yaml(repo_root, role_path, _role_entry_to_dict(role), allow_outside_contract=allow_outside_contract)
        written.append(role_path)

    skills_path = target_dir / "skills.yaml"
    _write_yaml(repo_root, skills_path, bundle.skills, allow_outside_contract=allow_outside_contract)
    written.append(skills_path)

    monitoring_schema_path = target_dir / "monitoring-schema.yaml"
    _write_yaml(
        repo_root, monitoring_schema_path, bundle.monitoring_schema,
        allow_outside_contract=allow_outside_contract,
    )
    written.append(monitoring_schema_path)

    hook_events_path = target_dir / "hook-events.yaml"
    _write_yaml(repo_root, hook_events_path, bundle.hook_events, allow_outside_contract=allow_outside_contract)
    written.append(hook_events_path)

    hook_surface_policy_path = target_dir / "hook-surface-policy.yaml"
    _write_yaml(
        repo_root, hook_surface_policy_path, bundle.hook_surface_policy,
        allow_outside_contract=allow_outside_contract,
    )
    written.append(hook_surface_policy_path)

    terminal_statuses_path = target_dir / "terminal-statuses.yaml"
    _write_yaml(
        repo_root,
        terminal_statuses_path,
        {
            "terminal_status_schema_version": 1,
            "workflow_id": bundle.workflow["workflow_id"],
            "statuses": bundle.terminal_statuses,
        },
        allow_outside_contract=allow_outside_contract,
    )
    written.append(terminal_statuses_path)

    gate_policy_path = target_dir / "gate-policy.yaml"
    _write_yaml(repo_root, gate_policy_path, bundle.gate_policy, allow_outside_contract=allow_outside_contract)
    written.append(gate_policy_path)

    return written
