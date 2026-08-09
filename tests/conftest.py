import pytest
import os
import signal
from src.core.items import ItemRegistry

# Step 1: Capture hardcoded defaults BEFORE bootstrap.
_PRE_BOOTSTRAP_ITEMS = dict(ItemRegistry._items)
_PRE_BOOTSTRAP_BACKUP = dict(ItemRegistry._backup_items)

# Step 2: Trigger bootstrap so catalog items (small_potion, etc.) are loaded.
import src.core.registries  # noqa: E402, F401

# Step 3: Capture post-bootstrap registry (full catalog).
_POST_BOOTSTRAP_ITEMS = dict(ItemRegistry._items)
_POST_BOOTSTRAP_BACKUP = dict(ItemRegistry._backup_items)

# Step 4: Build canonical test state = full catalog PLUS pre-bootstrap weights/values
# for items that exist in both. This ensures catalog-only items (small_potion) are
# always present, while hardcoded items (iron_ore) retain their original properties
# (e.g. weight=2.0) that many tests depend on.
_CANONICAL_ITEMS: dict = {**_POST_BOOTSTRAP_ITEMS, **_PRE_BOOTSTRAP_ITEMS}
_CANONICAL_BACKUP: dict = {**_POST_BOOTSTRAP_BACKUP, **_PRE_BOOTSTRAP_BACKUP}

# ResourceRegistry has the identical real-code hazard as ItemRegistry above:
# src/runtime/bootstrap.py calls ResourceRegistry.bootstrap({}) (an empty dict) on the real
# runtime bootstrap path. Any test that exercises it leaves ResourceRegistry empty for the rest
# of the process (TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET) -- capture the canonical
# post-import state (full real catalog, populated by src.core.registries's own module-level
# bootstrap above) so it can be restored the same way ItemRegistry already is.
from src.core.registries import ResourceRegistry
_CANONICAL_RESOURCES: dict = dict(ResourceRegistry._resources)

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
    # Profilers (e.g. Memray) inflate virtual address space — use --resource-budget off when profiling.
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


def _restore_canonical_registry() -> None:
    """Restore ItemRegistry to the canonical test state."""
    ItemRegistry._items = dict(_CANONICAL_ITEMS)
    ItemRegistry._backup_items = dict(_CANONICAL_BACKUP)


@pytest.fixture(autouse=True)
def _reset_item_registry():
    """Restore ItemRegistry to canonical test state before and after each test.

    AuthoritativeApplyPipeline.refine() calls ItemRegistry.bootstrap(catalog)
    on every run, which overwrites pre-bootstrap weights/values (e.g. iron_ore
    weight 2.0→1.0, value 1→12). The canonical state is the full catalog with
    pre-bootstrap values applied for items that exist in both, so:
    - catalog-only items (small_potion, wolf_pelt, ...) are always present
    - hardcoded items (iron_ore, wood, ...) keep their original properties
    """
    _restore_canonical_registry()
    yield
    _restore_canonical_registry()


@pytest.fixture(autouse=True)
def _reset_resource_registry():
    """Restore ResourceRegistry to canonical test state before and after each test.

    src/runtime/bootstrap.py calls ResourceRegistry.bootstrap({}) on the real runtime
    bootstrap path -- any test exercising it left ResourceRegistry empty for the rest of the
    process, silently failing resource-kind lookups (e.g. ResourceOpportunityProvider) in
    unrelated later tests (TCK-20260809-TEST-ISOLATION-RESOURCE-REGISTRY-RESET).
    """
    ResourceRegistry._resources = dict(_CANONICAL_RESOURCES)
    yield
    ResourceRegistry._resources = dict(_CANONICAL_RESOURCES)


@pytest.fixture(scope="session", autouse=True)
def _observability_worker_thread_sentinel():
    """Session-scoped sentinel that fails the suite if QueueDrainWorker threads accumulate.

    Counts active drain-worker threads at session start and end. Fails only if the
    count grew — pre-existing workers (before > 0) are tolerated so isolated runs
    against a warm process are not penalised.
    """
    from tests.tools.memory_probe import count_drain_workers
    before = count_drain_workers()
    yield
    after = count_drain_workers()
    leaked = after - before
    if leaked > 0:
        pytest.fail(
            f"QueueDrainWorker thread leak detected: {leaked} thread(s) remained after test session "
            f"(before={before}, after={after}). "
            "A test created a QueueDrainWorker without calling shutdown(). "
            "Check tests that create Kernel or EventRecorder instances."
        )
