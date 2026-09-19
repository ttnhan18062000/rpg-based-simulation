"""tools/mechanism_registry/ -- the mechanism registry tooling package.

TCK-20260916-MECHANISM-REGISTRY-TOOLS-PACKAGE. Groups the 14 tools this epic added under
tools/mechanism_registry/, matching the tools/gate_checks/ precedent (a real package, not a flat
pile of same-topic files in tools/ directly).

`registry.py` is the one module renamed by this move (`mechanism_registry.py` -> `registry.py`) --
a module and a package cannot share a name. Every other module keeps its original basename
unchanged, so a rename here is purely a change of parent path, not identity -- lower risk than
also renaming basenames.

This re-exports registry.py's public names so `from tools.mechanism_registry import X` (the
existing, already-widely-used import shape across this package's own sibling modules and the test
suite) keeps working without churn -- callers reaching for the schema reader/validator/priority
functions never need to know the module inside the package is called `registry`.
"""
from tools.mechanism_registry.registry import (
    MechanismRegistry,
    RUNTIME_INSTRUMENTS,
    STATIC_INSTRUMENTS,
    VALID_INSTRUMENTS,
    VALID_STATES,
    VALID_VERDICTS,
    DependencyCycleError,
    all_mechanisms_combined_view,
    build_system_rollup,
    build_verification_view,
    count_unaudited_edges_in_transitive_dependents,
    mechanisms_by_system,
    parse_implemented_by_entry,
    priority,
    symbol_defined_in_file,
    transitive_dependencies_of,
    transitive_dependents,
    unverified_priority_ranking,
    validate,
    verification_records_from_registry,
)

__all__ = [
    "MechanismRegistry",
    "RUNTIME_INSTRUMENTS",
    "STATIC_INSTRUMENTS",
    "VALID_INSTRUMENTS",
    "VALID_STATES",
    "VALID_VERDICTS",
    "DependencyCycleError",
    "all_mechanisms_combined_view",
    "build_system_rollup",
    "build_verification_view",
    "count_unaudited_edges_in_transitive_dependents",
    "mechanisms_by_system",
    "parse_implemented_by_entry",
    "priority",
    "symbol_defined_in_file",
    "transitive_dependencies_of",
    "transitive_dependents",
    "unverified_priority_ranking",
    "validate",
    "verification_records_from_registry",
]
