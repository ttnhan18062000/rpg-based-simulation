import pytest
import os
import signal

try:
    import resource
except ImportError:
    resource = None

TAXONOMY_MARKERS = {
    "legacy_characterization",
    "v2_contract",
    "differential",
    "intentional_divergence",
    "regression",
    "certification"
}

def pytest_addoption(parser):
    parser.addoption(
        "--resource-budget",
        action="store",
        default="medium",
        choices=["off", "small", "medium", "large"],
        help="Enforce resource and time budgets on tests: small, medium, large, or off (default: medium)",
    )

def timeout_handler(signum, frame):
    raise TimeoutError("Test execution exceeded the resource time limit.")

def pytest_runtest_setup(item):
    """
    Hook called before running every test to set strict resource and time limits.
    """
    budget = item.config.getoption("--resource-budget")
    if budget == "off":
        return

    # Define limits based on selection
    if budget == "small":
        mem_limit = 1024 * 1024 * 1024  # 1 GB
        time_limit = 15                 # 15 seconds
    elif budget == "large":
        mem_limit = 8 * 1024 * 1024 * 1024  # 8 GB
        time_limit = 600                    # 600 seconds
    else:  # medium
        mem_limit = 4 * 1024 * 1024 * 1024  # 4 GB
        time_limit = 60                     # 60 seconds

    # 1. Enforce Memory Limits
    if resource is not None:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (mem_limit, mem_limit))
        except ValueError:
            pass

    # 2. Enforce Time Limits
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(time_limit)
    except (ValueError, AttributeError):
        pass

def pytest_runtest_teardown(item, nextitem):
    """
    Hook called after running every test to disable active timers.
    """
    try:
        signal.alarm(0)
    except (ValueError, AttributeError):
        pass

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
