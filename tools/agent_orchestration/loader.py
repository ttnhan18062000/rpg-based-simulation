"""Validation entry point for the agent-orchestration/ contract.

`load_contract()` reads and validates all six files under `agent-orchestration/`
(contract.yaml, workflows/implement-ticket.yaml, all roles/*.yaml, skills.yaml,
monitoring-schema.yaml, hook-events.yaml), raising ContractValidationError on any missing
required field, malformed value, or non-mapping YAML root. Mirrors
tools/agent_replay/fixture_envelope.py's load_fixture() shape: a single validation entry
point returning a frozen dataclass on success. Only yaml.safe_load and the stdlib are used —
no new third-party dependency, no network calls.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .errors import ContractValidationError

_REQUIRED_CONTRACT_KEYS = ("version", "name")
_REQUIRED_WORKFLOW_KEYS = ("workflow_version", "workflow_id", "phases", "agents")
_REQUIRED_PHASE_KEYS = ("name", "tiers")
_REQUIRED_ROLE_KEYS = ("role_version", "role_id", "description", "phases", "has_agent_file")
_REQUIRED_SKILLS_KEYS = ("skills_version", "skills")
_REQUIRED_SKILL_ENTRY_KEYS = ("id", "description", "workflows", "roles")
_REQUIRED_MONITORING_SCHEMA_KEYS = ("schema_version", "fields")
_REQUIRED_MONITORING_FIELD_NAMES = ("execution_id", "run_id", "ticket_id")
_REQUIRED_HOOK_EVENTS_KEYS = ("hook_schema_version", "hook_types")
_REQUIRED_HOOK_TYPE_KEYS = ("id", "description")


@dataclass(frozen=True)
class RoleEntry:
    role_version: int
    role_id: str
    description: str
    phases: list[str]
    has_agent_file: bool
    inline_prompt_exception: str | None
    source_path: Path


@dataclass(frozen=True)
class ContractBundle:
    contract: dict[str, Any]
    workflow: dict[str, Any]
    roles: list[RoleEntry]
    skills: dict[str, Any]
    monitoring_schema: dict[str, Any]
    hook_events: dict[str, Any]


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ContractValidationError(f"{path}: YAML root is not a mapping")
    return raw


def _require_keys(path: Path, data: dict[str, Any], keys: tuple[str, ...], context: str = "") -> None:
    for key in keys:
        if data.get(key) is None:
            location = f"{context} " if context else ""
            raise ContractValidationError(f"{path}: {location}missing required field '{key}'")


def _load_contract_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_CONTRACT_KEYS)
    if not isinstance(data["version"], int):
        raise ContractValidationError(f"{path}: 'version' must be an int, got {type(data['version']).__name__}")
    return data


def _load_workflow_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_WORKFLOW_KEYS)

    phases = data["phases"]
    if not isinstance(phases, list) or len(phases) == 0:
        raise ContractValidationError(f"{path}: 'phases' must be a non-empty list")
    for idx, phase in enumerate(phases):
        if not isinstance(phase, dict):
            raise ContractValidationError(f"{path}: phases[{idx}] is not a mapping")
        for key in _REQUIRED_PHASE_KEYS:
            if phase.get(key) is None:
                raise ContractValidationError(f"{path}: phases[{idx}] missing required field '{key}'")

    agents = data["agents"]
    if not isinstance(agents, list) or len(agents) == 0:
        raise ContractValidationError(f"{path}: 'agents' must be a non-empty list")

    return data


def _load_role_yaml(path: Path) -> RoleEntry:
    data = _load_yaml_mapping(path)
    for key in _REQUIRED_ROLE_KEYS:
        if data.get(key) is None:
            raise ContractValidationError(f"{path}: missing required field '{key}'")
    return RoleEntry(
        role_version=data["role_version"],
        role_id=data["role_id"],
        description=data["description"],
        phases=data["phases"],
        has_agent_file=data["has_agent_file"],
        inline_prompt_exception=data.get("inline_prompt_exception"),
        source_path=path,
    )


def _load_skills_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_SKILLS_KEYS)

    skills = data["skills"]
    if not isinstance(skills, list) or len(skills) == 0:
        raise ContractValidationError(f"{path}: 'skills' must be a non-empty list")
    for idx, entry in enumerate(skills):
        if not isinstance(entry, dict):
            raise ContractValidationError(f"{path}: skills[{idx}] is not a mapping")
        for key in _REQUIRED_SKILL_ENTRY_KEYS:
            if entry.get(key) is None:
                raise ContractValidationError(f"{path}: skills[{idx}] missing required field '{key}'")

    return data


def _load_monitoring_schema_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_MONITORING_SCHEMA_KEYS)

    fields = data["fields"]
    if not isinstance(fields, dict):
        raise ContractValidationError(f"{path}: 'fields' must be a mapping")
    for name in _REQUIRED_MONITORING_FIELD_NAMES:
        if name not in fields:
            raise ContractValidationError(f"{path}: 'fields' missing required entry '{name}'")

    return data


def _load_hook_events_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_HOOK_EVENTS_KEYS)

    hook_types = data["hook_types"]
    if not isinstance(hook_types, list) or len(hook_types) == 0:
        raise ContractValidationError(f"{path}: 'hook_types' must be a non-empty list")
    for idx, entry in enumerate(hook_types):
        if not isinstance(entry, dict):
            raise ContractValidationError(f"{path}: hook_types[{idx}] is not a mapping")
        for key in _REQUIRED_HOOK_TYPE_KEYS:
            if entry.get(key) is None:
                raise ContractValidationError(f"{path}: hook_types[{idx}] missing required field '{key}'")

    return data


def load_contract(root: Path) -> ContractBundle:
    """Load and validate the full agent-orchestration/ contract rooted at `root`.

    `root` is the repository root — the contract directory itself is `root / "agent-orchestration"`.
    """
    contract_dir = root / "agent-orchestration"

    contract = _load_contract_yaml(contract_dir / "contract.yaml")
    workflow = _load_workflow_yaml(contract_dir / "workflows" / "implement-ticket.yaml")

    roles_dir = contract_dir / "roles"
    role_paths = sorted(roles_dir.glob("*.yaml"))
    if not role_paths:
        raise ContractValidationError(f"{roles_dir}: no role files found")
    roles = [_load_role_yaml(path) for path in role_paths]

    skills = _load_skills_yaml(contract_dir / "skills.yaml")
    monitoring_schema = _load_monitoring_schema_yaml(contract_dir / "monitoring-schema.yaml")
    hook_events = _load_hook_events_yaml(contract_dir / "hook-events.yaml")

    return ContractBundle(
        contract=contract,
        workflow=workflow,
        roles=roles,
        skills=skills,
        monitoring_schema=monitoring_schema,
        hook_events=hook_events,
    )
