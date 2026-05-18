import pytest
import os

TAXONOMY_MARKERS = {
    "legacy_characterization",
    "v2_contract",
    "differential",
    "intentional_divergence",
    "regression",
    "certification"
}

def pytest_collection_modifyitems(config, items):
    """
    Enforces taxonomy markers for all tests in tests/parity/.
    Also enforces 'id' requirement for intentional_divergence.
    """
    errors = []
    
    for item in items:
        # Get relative path from project root
        rel_path = os.path.relpath(str(item.fspath), os.getcwd())
        
        # Only enforce for tests in tests/parity
        if rel_path.startswith("tests/parity"):
            item_markers = {m.name for m in item.iter_markers()}
            
            # 1. Check for at least one taxonomy marker
            if not (item_markers & TAXONOMY_MARKERS):
                errors.append(
                    f"Test '{item.nodeid}' in parity suite is missing a taxonomy marker. "
                    f"Must have one of: {', '.join(sorted(TAXONOMY_MARKERS))}"
                )
            
            # 2. Check for 'id' if intentional_divergence is used
            for marker in item.iter_markers(name="intentional_divergence"):
                if not marker.kwargs.get("id"):
                    errors.append(
                        f"Test '{item.nodeid}' is marked as 'intentional_divergence' but is missing an 'id' argument."
                    )
    
    if errors:
        # We raise a UsageError during collection to stop the run early
        # and provide a clear list of all non-compliant tests.
        raise pytest.UsageError("\n" + "\n".join(errors))
