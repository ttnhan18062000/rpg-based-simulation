"""tools/semantic_control_plane/ -- schema/validator tooling for the Simulation Semantic Control
Plane (TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION).

A sibling package to `tools/mechanism_registry/`, not an extension of it: these three schemas'
`rule_id` resolution depends on a `docs/world_rules/` corpus scan `tools/mechanism_registry/` has
never needed, and `registries/mechanisms.yaml` is only a foreign-key target for these schemas, not
their own home file. `registry.py` imports `MechanismRegistry` from `tools.mechanism_registry`
read-only for `mechanism_id` resolution rather than re-parsing `mechanisms.yaml`.

Re-exports `rule_catalog.py`'s/`registry.py`'s public names, mirroring
`tools/mechanism_registry/__init__.py`'s own re-export shape.
"""
from tools.semantic_control_plane.registry import (
    DuplicateYamlKeyError,
    VALID_RULE_CLASSIFICATIONS,
    VALID_RULE_MECHANISM_EDGE_TYPES,
    check_duplicate_keys,
    consumers_of,
    producers_for,
    validate_all,
    validate_mechanism_causal_edges,
    validate_rule_classifications,
    validate_rule_mechanism_edges,
)
from tools.semantic_control_plane.rule_catalog import (
    DEFAULT_WORLD_RULES_PATH,
    scan_rule_ids,
)

__all__ = [
    "DEFAULT_WORLD_RULES_PATH",
    "DuplicateYamlKeyError",
    "VALID_RULE_CLASSIFICATIONS",
    "VALID_RULE_MECHANISM_EDGE_TYPES",
    "check_duplicate_keys",
    "consumers_of",
    "producers_for",
    "scan_rule_ids",
    "validate_all",
    "validate_mechanism_causal_edges",
    "validate_rule_classifications",
    "validate_rule_mechanism_edges",
]
