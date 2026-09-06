"""Validation entry point for the agent-orchestration/ contract.

`load_contract()` reads and validates all files under `agent-orchestration/`
(contract.yaml, workflows/implement-ticket.yaml, all roles/*.yaml, skills.yaml,
monitoring-schema.yaml, hook-events.yaml, hook-surface-policy.yaml, terminal-statuses.yaml,
gate-policy.yaml), raising ContractValidationError on any missing
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
from .terminal_statuses import TerminalStatusValidationError, load_terminal_statuses

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
_REQUIRED_HOOK_SURFACE_POLICY_KEYS = (
    "hook_surface_policy_version",
    "providers",
    "activation_candidates",
    "activation_prerequisites",
)
_REQUIRED_ACTIVATION_CANDIDATE_KEYS = ("provider", "event", "status", "writer_functions")
_REQUIRED_ACTIVATION_PREREQUISITE_KEYS = ("id", "description")
_AUTHORIZATION_IMPLYING_KEYS = ("approved", "granted", "authorized")
_REQUIRED_GATE_POLICY_KEYS = ("gate_policy_version", "workflow_id", "gates")
_REQUIRED_GATE_ENTRY_KEYS = ("phase", "gate_type", "on_fail_status")
_GATE_TYPE_EXTRA_KEYS = {
    "agent_verdict": ("verdict_enum", "pass_value"),
    "static_check": ("invocation", "check_module", "check_function"),
    "agent_result_field": ("result_field", "pass_value"),
}
_REQUIRED_ARTIFACT_REQUIREMENTS_KEYS = ("required_files", "exempt_tier")


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
    hook_surface_policy: dict[str, Any]
    terminal_statuses: list[dict[str, Any]]
    continuation_policy: "ContinuationPolicy | None"
    gate_policy: dict[str, Any]
    artifact_requirements: dict[str, Any] | None


@dataclass(frozen=True)
class ContinuationPolicy:
    mode: str
    instruction: str
    non_gates: list[str]


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

    artifact_requirements = data.get("artifact_requirements")
    if artifact_requirements is not None:
        if not isinstance(artifact_requirements, dict):
            raise ContractValidationError(f"{path}: 'artifact_requirements' must be a mapping")
        _require_keys(path, artifact_requirements, _REQUIRED_ARTIFACT_REQUIREMENTS_KEYS, context="artifact_requirements")
        required_files = artifact_requirements["required_files"]
        if not isinstance(required_files, list) or not required_files or not all(
            isinstance(item, str) and item.strip() for item in required_files
        ):
            raise ContractValidationError(f"{path}: artifact_requirements.required_files must be a non-empty list of strings")
        exempt_tier = artifact_requirements["exempt_tier"]
        if not isinstance(exempt_tier, str) or not exempt_tier.strip():
            raise ContractValidationError(f"{path}: artifact_requirements.exempt_tier must be a non-empty string")

    return data


def _normalize(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _load_workflow_yaml(path: Path, terminal_statuses: list[dict[str, Any]]) -> tuple[dict[str, Any], ContinuationPolicy | None]:
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

    policy = data.get("continuation_policy")
    if policy is None:
        return data, None
    if not isinstance(policy, dict):
        raise ContractValidationError(f"{path}: 'continuation_policy' must be a mapping")
    mode, instruction, non_gates = policy.get("mode"), policy.get("instruction"), policy.get("non_gates")
    if mode != "continue_until_terminal_or_hard_gate":
        raise ContractValidationError(f"{path}: continuation_policy.mode must be 'continue_until_terminal_or_hard_gate'")
    if not isinstance(instruction, str) or not instruction.strip():
        raise ContractValidationError(f"{path}: continuation_policy.instruction must be a non-empty string")
    if not isinstance(non_gates, list) or not non_gates or not all(isinstance(item, str) and item.strip() for item in non_gates):
        raise ContractValidationError(f"{path}: continuation_policy.non_gates must be a non-empty list of strings")
    reserved = {_normalize(entry["value"]) for entry in terminal_statuses if entry["value"] != "DONE"}
    if any(_normalize(item) in reserved for item in non_gates):
        raise ContractValidationError(f"{path}: continuation_policy.non_gates contains reserved terminal status")
    return data, ContinuationPolicy(mode=mode, instruction=instruction, non_gates=list(non_gates))


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

        companion_assets = entry.get("companion_assets", [])
        if not isinstance(companion_assets, list):
            raise ContractValidationError(
                f"{path}: skills[{idx}] 'companion_assets' must be a list, got {type(companion_assets).__name__}"
            )
        for j, elem in enumerate(companion_assets):
            if not isinstance(elem, str):
                raise ContractValidationError(
                    f"{path}: skills[{idx}] 'companion_assets' must be a list of strings, got {type(elem).__name__} at index {j}"
                )
        entry["companion_assets"] = companion_assets

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


def _reject_authorization_implying_keys(path: Path, entry: dict[str, Any], context: str) -> None:
    for key in _AUTHORIZATION_IMPLYING_KEYS:
        if entry.get(key) is True:
            raise ContractValidationError(
                f"{path}: {context} carries authorization-implying key '{key}' with a true value — "
                "activation_prerequisites/activation_candidates entries must never imply "
                "authorization was granted"
            )


def _load_hook_surface_policy_yaml(path: Path, hook_events: dict[str, Any]) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_HOOK_SURFACE_POLICY_KEYS)

    if not isinstance(data["hook_surface_policy_version"], int):
        raise ContractValidationError(
            f"{path}: 'hook_surface_policy_version' must be an int, got "
            f"{type(data['hook_surface_policy_version']).__name__}"
        )

    normalized_ids = {entry["id"] for entry in hook_events["hook_types"]}

    providers = data["providers"]
    if not isinstance(providers, dict) or not providers:
        raise ContractValidationError(f"{path}: 'providers' must be a non-empty mapping")
    for provider_name, provider in providers.items():
        if not isinstance(provider, dict):
            raise ContractValidationError(f"{path}: providers.{provider_name} is not a mapping")
        if provider.get("enabled_events") is None:
            raise ContractValidationError(
                f"{path}: providers.{provider_name} missing required field 'enabled_events'"
            )
        enabled_events = provider["enabled_events"]
        if not isinstance(enabled_events, list) or not all(isinstance(e, str) for e in enabled_events):
            raise ContractValidationError(
                f"{path}: providers.{provider_name}.enabled_events must be a list of strings"
            )
        not_normalized = set(enabled_events) - normalized_ids
        if not_normalized:
            raise ContractValidationError(
                f"{path}: providers.{provider_name}.enabled_events contains ids not normalized in "
                f"hook-events.yaml's hook_types: {sorted(not_normalized)}"
            )

        available_events = provider.get("available_events")
        if available_events is not None:
            if not isinstance(available_events, list) or not all(isinstance(e, str) for e in available_events):
                raise ContractValidationError(
                    f"{path}: providers.{provider_name}.available_events must be a list of strings"
                )
            not_available = set(enabled_events) - set(available_events)
            if not_available:
                raise ContractValidationError(
                    f"{path}: providers.{provider_name}.enabled_events contains ids not present in "
                    f"providers.{provider_name}.available_events: {sorted(not_available)}"
                )

    activation_candidates = data["activation_candidates"]
    if not isinstance(activation_candidates, list):
        raise ContractValidationError(f"{path}: 'activation_candidates' must be a list")
    for idx, candidate in enumerate(activation_candidates):
        if not isinstance(candidate, dict):
            raise ContractValidationError(f"{path}: activation_candidates[{idx}] is not a mapping")
        for key in _REQUIRED_ACTIVATION_CANDIDATE_KEYS:
            if candidate.get(key) is None:
                raise ContractValidationError(
                    f"{path}: activation_candidates[{idx}] missing required field '{key}'"
                )
        writer_functions = candidate["writer_functions"]
        if not isinstance(writer_functions, list) or not all(isinstance(w, str) for w in writer_functions):
            raise ContractValidationError(
                f"{path}: activation_candidates[{idx}].writer_functions must be a list of strings"
            )
        candidate_provider_name = candidate["provider"]
        provider_entry = providers.get(candidate_provider_name)
        if provider_entry is None:
            raise ContractValidationError(
                f"{path}: activation_candidates[{idx}].provider '{candidate_provider_name}' is not "
                "declared in 'providers'"
            )
        candidate_available = provider_entry.get("available_events") or []
        if candidate["event"] not in candidate_available:
            raise ContractValidationError(
                f"{path}: activation_candidates[{idx}].event '{candidate['event']}' is not in "
                f"providers.{candidate_provider_name}.available_events"
            )
        _reject_authorization_implying_keys(path, candidate, f"activation_candidates[{idx}]")

    activation_prerequisites = data["activation_prerequisites"]
    if not isinstance(activation_prerequisites, list) or len(activation_prerequisites) == 0:
        raise ContractValidationError(f"{path}: 'activation_prerequisites' must be a non-empty list")
    seen_ids: set[str] = set()
    for idx, prerequisite in enumerate(activation_prerequisites):
        if not isinstance(prerequisite, dict):
            raise ContractValidationError(f"{path}: activation_prerequisites[{idx}] is not a mapping")
        for key in _REQUIRED_ACTIVATION_PREREQUISITE_KEYS:
            if prerequisite.get(key) is None:
                raise ContractValidationError(
                    f"{path}: activation_prerequisites[{idx}] missing required field '{key}'"
                )
        prerequisite_id = prerequisite["id"]
        if prerequisite_id in seen_ids:
            raise ContractValidationError(
                f"{path}: activation_prerequisites[{idx}] duplicate id '{prerequisite_id}'"
            )
        seen_ids.add(prerequisite_id)
        _reject_authorization_implying_keys(path, prerequisite, f"activation_prerequisites[{idx}]")

    return data


def _load_gate_policy_yaml(path: Path) -> dict[str, Any]:
    data = _load_yaml_mapping(path)
    _require_keys(path, data, _REQUIRED_GATE_POLICY_KEYS)

    if not isinstance(data["gate_policy_version"], int):
        raise ContractValidationError(
            f"{path}: 'gate_policy_version' must be an int, got {type(data['gate_policy_version']).__name__}"
        )

    gates = data["gates"]
    if not isinstance(gates, list) or len(gates) == 0:
        raise ContractValidationError(f"{path}: 'gates' must be a non-empty list")
    for idx, entry in enumerate(gates):
        if not isinstance(entry, dict):
            raise ContractValidationError(f"{path}: gates[{idx}] is not a mapping")
        for key in _REQUIRED_GATE_ENTRY_KEYS:
            if entry.get(key) is None:
                raise ContractValidationError(f"{path}: gates[{idx}] missing required field '{key}'")

        gate_type = entry["gate_type"]
        extra_keys = _GATE_TYPE_EXTRA_KEYS.get(gate_type)
        if extra_keys is None:
            raise ContractValidationError(
                f"{path}: gates[{idx}] has unrecognized gate_type '{gate_type}' — expected one of "
                f"{sorted(_GATE_TYPE_EXTRA_KEYS)}"
            )
        for key in extra_keys:
            if entry.get(key) is None:
                raise ContractValidationError(f"{path}: gates[{idx}] (gate_type={gate_type!r}) missing required field '{key}'")

        on_fail_status = entry["on_fail_status"]
        if not isinstance(on_fail_status, list) or not on_fail_status or not all(
            isinstance(item, str) for item in on_fail_status
        ):
            raise ContractValidationError(f"{path}: gates[{idx}].on_fail_status must be a non-empty list of strings")

    for optional_key in ("gateless_phases", "excluded_outcomes"):
        entries = data.get(optional_key)
        if entries is None:
            continue
        if not isinstance(entries, list) or not entries or not all(isinstance(e, dict) for e in entries):
            raise ContractValidationError(f"{path}: '{optional_key}' must be a non-empty list of mappings")

    return data


def load_contract(root: Path) -> ContractBundle:
    """Load and validate the full agent-orchestration/ contract rooted at `root`.

    `root` is the repository root — the contract directory itself is `root / "agent-orchestration"`.
    """
    contract_dir = root / "agent-orchestration"

    contract = _load_contract_yaml(contract_dir / "contract.yaml")
    try:
        terminal_statuses = load_terminal_statuses(root)
    except TerminalStatusValidationError as error:
        raise ContractValidationError(str(error)) from error
    workflow, continuation_policy = _load_workflow_yaml(contract_dir / "workflows" / "implement-ticket.yaml", terminal_statuses)

    roles_dir = contract_dir / "roles"
    role_paths = sorted(roles_dir.glob("*.yaml"))
    if not role_paths:
        raise ContractValidationError(f"{roles_dir}: no role files found")
    roles = [_load_role_yaml(path) for path in role_paths]

    skills = _load_skills_yaml(contract_dir / "skills.yaml")
    monitoring_schema = _load_monitoring_schema_yaml(contract_dir / "monitoring-schema.yaml")
    hook_events = _load_hook_events_yaml(contract_dir / "hook-events.yaml")
    hook_surface_policy = _load_hook_surface_policy_yaml(
        contract_dir / "hook-surface-policy.yaml", hook_events
    )
    gate_policy = _load_gate_policy_yaml(contract_dir / "gate-policy.yaml")

    return ContractBundle(
        contract=contract,
        workflow=workflow,
        roles=roles,
        skills=skills,
        monitoring_schema=monitoring_schema,
        hook_events=hook_events,
        hook_surface_policy=hook_surface_policy,
        terminal_statuses=terminal_statuses,
        continuation_policy=continuation_policy,
        gate_policy=gate_policy,
        artifact_requirements=contract.get("artifact_requirements"),
    )
