#!/usr/bin/env python3
"""
Reader and validator for the three new registries the Simulation Semantic Control Plane's M0
milestone introduces (TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION):

  1. `registries/rule_mechanism_edges.yaml` -- Rule -> Mechanism typed edges
     (rule_id, mechanism_id, edge_type, evidence, date).
  2. `registries/mechanism_causal_edges.yaml` -- Mechanism -> Mechanism directed causal edges
     (producer_mechanism_id, consumer_mechanism_id, evidence, date). Physically distinct from (1):
     no shared `edge_type` field, no merged row shape (`roadmap.md` names this exact merge as a
     mistake an earlier draft already made).
  3. `registries/rule_classifications.yaml` -- one realization-classification record per Rule ID
     (rule_id, classification, evidence, review_date). Never mechanically derived from (1) or (2)
     -- see `validate_rule_classifications()`'s own docstring and
     `docs/plans/mechanism_tier_model_initiative.md` §3's "declared, not derived" precedent.

Mirrors `tools/mechanism_registry/registry.py`'s own `validate(data) -> List[str]` /
`check_duplicate_keys(path)` split: `validate_*()` functions never raise for a business-logic
violation, only for structurally unreadable input, and return every violation found in one pass
("build the failure loud", `tools/mechanism_registry/registry.py:45-49`). Duplicate-YAML-key
corruption (the same `yaml.safe_load()` silent-last-value-wins risk documented at
`tools/mechanism_registry/registry.py:210-257`) is checked separately, against the real file path,
since a parsed dict can no longer show that a key was written twice.

`mechanism_id` resolution reuses `tools.mechanism_registry.registry.MechanismRegistry` (imported,
never modified) rather than re-parsing `registries/mechanisms.yaml`. `rule_id` resolution reuses
`rule_catalog.scan_rule_ids()`.

Usage:
  python3 tools/semantic_control_plane/registry.py    # validate the real committed files
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.mechanism_registry.registry import MechanismRegistry
from tools.semantic_control_plane.rule_catalog import (
    DEFAULT_WORLD_RULES_PATH,
    scan_rule_ids,
)

_DEFAULT_REGISTRIES_PATH = _REPO_ROOT / "registries"
_DEFAULT_RULE_MECHANISM_EDGES_PATH = _DEFAULT_REGISTRIES_PATH / "rule_mechanism_edges.yaml"
_DEFAULT_CAUSAL_EDGES_PATH = _DEFAULT_REGISTRIES_PATH / "mechanism_causal_edges.yaml"
_DEFAULT_CLASSIFICATIONS_PATH = _DEFAULT_REGISTRIES_PATH / "rule_classifications.yaml"

VALID_RULE_MECHANISM_EDGE_TYPES = frozenset(
    {"REALIZES", "PARTIALLY_REALIZES", "CONSTRAINED_BY"}
)
VALID_RULE_CLASSIFICATIONS = frozenset(
    {"SUPPORTED", "PARTIAL", "CONFLICTING", "MISSING", "INERT-OFF", "UNKNOWN"}
)


class DuplicateYamlKeyError(ValueError):
    """Raised when the same key appears twice in one YAML mapping. Mirrors
    `tools.mechanism_registry.registry.DuplicateYamlKeyError` -- the identical
    `yaml.safe_load()` silent-last-key-wins risk applies to these three hand-edited YAML files
    too, and is caught the same way: a dedicated loader, not a post-hoc check on the already-
    collapsed dict."""


def _load_yaml_checking_duplicate_keys(path: Path):
    class _DuplicateKeyCheckingLoader(yaml.SafeLoader):
        pass

    def _construct_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False):
        mapping: dict = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in mapping:
                raise DuplicateYamlKeyError(
                    f"duplicate key {key!r} at {path.name}:{key_node.start_mark.line + 1} "
                    "(yaml.safe_load() would silently keep only the LAST occurrence's value)"
                )
            value = loader.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping

    _DuplicateKeyCheckingLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
    )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=_DuplicateKeyCheckingLoader)


def check_duplicate_keys(
    rule_mechanism_edges_path: Path = _DEFAULT_RULE_MECHANISM_EDGES_PATH,
    causal_edges_path: Path = _DEFAULT_CAUSAL_EDGES_PATH,
    classifications_path: Path = _DEFAULT_CLASSIFICATIONS_PATH,
) -> List[str]:
    """No mapping in any of the three files may define the same key twice. Returns a list of
    error strings (empty if clean), the same shape `validate_*()`'s own errors use, so a caller
    can merge the two. Must run against real file paths -- see
    `_load_yaml_checking_duplicate_keys()`'s docstring for why."""
    errors: List[str] = []
    for path in (rule_mechanism_edges_path, causal_edges_path, classifications_path):
        try:
            _load_yaml_checking_duplicate_keys(path)
        except DuplicateYamlKeyError as e:
            errors.append(str(e))
    return errors


def validate_rule_mechanism_edges(
    data: dict, known_rule_ids: Set[str], known_mechanism_ids: Set[str]
) -> List[str]:
    """Invariants: (1) `edge_type` is one of `VALID_RULE_MECHANISM_EDGE_TYPES`; (2) `rule_id`
    resolves against `known_rule_ids` (a live `docs/world_rules/**/*.md` heading scan); (3)
    `mechanism_id` resolves against `known_mechanism_ids`; (4) no duplicate
    `(rule_id, mechanism_id, edge_type)` triple -- the triple is the key, not the
    `(rule_id, mechanism_id)` pair, so two rows sharing a Rule and a mechanism under two distinct
    edge types are both legitimate, independently-evidenced relations."""
    errors: List[str] = []
    edges = data.get("edges", []) or []
    seen_triples: Set[Tuple[str, str, str]] = set()
    for edge in edges:
        rule_id = edge.get("rule_id")
        mechanism_id = edge.get("mechanism_id")
        edge_type = edge.get("edge_type")

        if edge_type not in VALID_RULE_MECHANISM_EDGE_TYPES:
            errors.append(
                f"rule_mechanism edge (rule_id={rule_id!r}, mechanism_id={mechanism_id!r}) has "
                f"edge_type {edge_type!r}, not one of {sorted(VALID_RULE_MECHANISM_EDGE_TYPES)}"
            )
        if rule_id not in known_rule_ids:
            errors.append(f"rule_mechanism edge references unresolved rule_id {rule_id!r}")
        if mechanism_id not in known_mechanism_ids:
            errors.append(
                f"rule_mechanism edge references unresolved mechanism_id {mechanism_id!r}"
            )

        triple = (rule_id, mechanism_id, edge_type)
        if triple in seen_triples:
            errors.append(
                f"duplicate rule_mechanism edge triple (rule_id={rule_id!r}, "
                f"mechanism_id={mechanism_id!r}, edge_type={edge_type!r})"
            )
        seen_triples.add(triple)
    return errors


def validate_mechanism_causal_edges(data: dict, known_mechanism_ids: Set[str]) -> List[str]:
    """Invariants: (1) `producer_mechanism_id` resolves against `known_mechanism_ids`; (2)
    `consumer_mechanism_id` resolves against `known_mechanism_ids`; (3) `producer_mechanism_id ==
    consumer_mechanism_id` on one row is rejected -- a mechanism cannot meaningfully produce input
    for itself within one directed causal fact; (4) no duplicate directed
    `(producer_mechanism_id, consumer_mechanism_id)` pair -- the reversed pair after the forward
    one already exists is NOT a duplicate, since the edge is directed and both are independently
    valid facts. Never inspects an `edge_type` field -- this schema has none, and never shares one
    with `validate_rule_mechanism_edges()`'s own enum."""
    errors: List[str] = []
    edges = data.get("edges", []) or []
    seen_pairs: Set[Tuple[str, str]] = set()
    for edge in edges:
        producer = edge.get("producer_mechanism_id")
        consumer = edge.get("consumer_mechanism_id")

        if producer not in known_mechanism_ids:
            errors.append(
                f"mechanism causal edge references unresolved producer_mechanism_id {producer!r}"
            )
        if consumer not in known_mechanism_ids:
            errors.append(
                f"mechanism causal edge references unresolved consumer_mechanism_id {consumer!r}"
            )
        if producer == consumer:
            errors.append(
                f"mechanism causal edge is self-producing: producer_mechanism_id == "
                f"consumer_mechanism_id == {producer!r}"
            )

        pair = (producer, consumer)
        if pair in seen_pairs:
            errors.append(
                f"duplicate directed mechanism causal edge (producer_mechanism_id={producer!r}, "
                f"consumer_mechanism_id={consumer!r})"
            )
        seen_pairs.add(pair)
    return errors


def consumers_of(mechanism_id: str, edges: List[dict]) -> List[str]:
    """Every mechanism_id that `mechanism_id` produces input for -- computed by traversal over
    `edges` at call time, never a stored inverse row (a stored inverse would disagree with the
    real forward edges within a month, the same reasoning
    `tools.mechanism_registry.registry.MechanismRegistry.dependents_of()` already documents for
    `depends_on`)."""
    return [
        e["consumer_mechanism_id"]
        for e in edges
        if e.get("producer_mechanism_id") == mechanism_id
    ]


def producers_for(mechanism_id: str, edges: List[dict]) -> List[str]:
    """Every mechanism_id that produces input for `mechanism_id` -- the symmetric traversal of
    `consumers_of()`, same computed-not-stored rule."""
    return [
        e["producer_mechanism_id"]
        for e in edges
        if e.get("consumer_mechanism_id") == mechanism_id
    ]


def validate_rule_classifications(data: dict, known_rule_ids: Set[str]) -> List[str]:
    """Invariants: (1) `classification` is one of `VALID_RULE_CLASSIFICATIONS`; (2) `rule_id`
    resolves against `known_rule_ids`; (3) no duplicate `rule_id` -- at most one record per Rule
    ID present in the file. A Rule with NO record is not an error (§7's UNKNOWN-permanence
    discipline: an absent mapping is not a violation); only a *second* row for an already-present
    `rule_id` is rejected.

    `UNKNOWN` is accepted with zero special-case normalization -- this function has no
    normalization step at all, so a loaded `"UNKNOWN"` string is never rewritten to `"MISSING"` or
    dropped by anything in this module.

    Deliberately does NOT take `registries/rule_mechanism_edges.yaml` or
    `registries/mechanism_causal_edges.yaml` data as input, and no function anywhere in this
    package derives or writes a classification value from that edge data -- the whole point of
    this schema being a separate, human-judgment record (`architecture.md` §3/§4,
    `docs/plans/mechanism_tier_model_initiative.md` §3's "declared, not derived" precedent for the
    `system` tier)."""
    errors: List[str] = []
    classifications = data.get("classifications", []) or []
    seen_rule_ids: Set[str] = set()
    for record in classifications:
        rule_id = record.get("rule_id")
        classification = record.get("classification")

        if classification not in VALID_RULE_CLASSIFICATIONS:
            errors.append(
                f"rule classification for rule_id {rule_id!r} is {classification!r}, not one of "
                f"{sorted(VALID_RULE_CLASSIFICATIONS)}"
            )
        if rule_id not in known_rule_ids:
            errors.append(f"rule classification references unresolved rule_id {rule_id!r}")
        if rule_id in seen_rule_ids:
            errors.append(f"duplicate rule classification record for rule_id {rule_id!r}")
        seen_rule_ids.add(rule_id)
    return errors


def validate_all(
    base_path: Path = _DEFAULT_REGISTRIES_PATH,
    world_rules_path: Path = DEFAULT_WORLD_RULES_PATH,
) -> List[str]:
    """Loads all three registries from `base_path`, resolves `known_rule_ids` (live scan of
    `world_rules_path`) and `known_mechanism_ids` (via `MechanismRegistry`), runs the three
    schema-specific `validate_*()` functions plus `check_duplicate_keys()`, and returns the merged
    error list -- the combined entry point mirroring
    `tools.mechanism_registry.registry.main()`'s own merge-don't-raise philosophy."""
    rule_mechanism_edges_path = base_path / "rule_mechanism_edges.yaml"
    causal_edges_path = base_path / "mechanism_causal_edges.yaml"
    classifications_path = base_path / "rule_classifications.yaml"

    errors = check_duplicate_keys(
        rule_mechanism_edges_path, causal_edges_path, classifications_path
    )

    with open(rule_mechanism_edges_path, "r", encoding="utf-8") as f:
        rule_mechanism_data = yaml.safe_load(f) or {}
    with open(causal_edges_path, "r", encoding="utf-8") as f:
        causal_edges_data = yaml.safe_load(f) or {}
    with open(classifications_path, "r", encoding="utf-8") as f:
        classifications_data = yaml.safe_load(f) or {}

    known_rule_ids = scan_rule_ids(world_rules_path)
    known_mechanism_ids = {m["id"] for m in MechanismRegistry().all_mechanisms()}

    errors += validate_rule_mechanism_edges(
        rule_mechanism_data, known_rule_ids, known_mechanism_ids
    )
    errors += validate_mechanism_causal_edges(causal_edges_data, known_mechanism_ids)
    errors += validate_rule_classifications(classifications_data, known_rule_ids)
    return errors


def main(argv: List[str] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    errors = validate_all()
    if errors:
        print(f"FAIL: {len(errors)} violation(s) across the semantic control plane registries")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK: rule_mechanism_edges.yaml, mechanism_causal_edges.yaml, rule_classifications.yaml valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
