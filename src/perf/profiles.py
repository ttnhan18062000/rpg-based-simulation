from src.config.profiles import RuntimeProfile, HardwareClass
from src.engine.cadence import SystemCadence


def make_perf_profile(
    name: str,
    *,
    ram_mb: int,
    workers: int,
    tick_budget_ms: float = 100.0,
    queue_depth: int = 1000,
    replay_buffer_kb: int = 8192,
    observability_budget_percent: float = 5.0,
    cadence: SystemCadence | None = None,
) -> RuntimeProfile:
    """
    Build a performance-oriented RuntimeProfile.

    These profiles are intentionally more generous than unit-test profiles.
    They are used to discover realistic engine limits before setting final
    production budgets.

    Resource strategy:
        Start from 512 MB, 1 GB, 2 GB, and 4 GB.
        Measure first.
        Then decide which profile is a good default.
    """
    # Default perf cadence mirrors PROD_DEFAULT for representative measurement
    effective_cadence = cadence or SystemCadence(
        strategic_intelligence=3,
        concern_evaluation=3,
        detour_suggestion=5,
        social_memory=5,
        biological=5,
        lifecycle=10,
    )
    return RuntimeProfile(
        name=name,
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=ram_mb,
        max_cpu_percent=90.0,
        max_worker_count=workers,
        max_queue_depth=queue_depth,
        max_replay_buffer_kb=replay_buffer_kb,
        max_tick_budget_ms=tick_budget_ms,
        max_observability_budget_percent=observability_budget_percent,
        max_work_debt=10000,
        cadence=effective_cadence,
    )


PERF_PROFILES = {
    "PERF_512MB_LOCAL": make_perf_profile(
        "PERF_512MB_LOCAL",
        ram_mb=512,
        workers=0,
    ),
    "PERF_1GB_LOCAL": make_perf_profile(
        "PERF_1GB_LOCAL",
        ram_mb=1024,
        workers=0,
    ),
    "PERF_2GB_LOCAL": make_perf_profile(
        "PERF_2GB_LOCAL",
        ram_mb=2048,
        workers=0,
        tick_budget_ms=1000.0,
    ),
    "PERF_4GB_LOCAL": make_perf_profile(
        "PERF_4GB_LOCAL",
        ram_mb=4096,
        workers=0,
    ),
    "PERF_512MB_CONC": make_perf_profile(
        "PERF_512MB_CONC",
        ram_mb=512,
        workers=4,
    ),
    "PERF_1GB_CONC": make_perf_profile(
        "PERF_1GB_CONC",
        ram_mb=1024,
        workers=4,
    ),
    "PERF_2GB_CONC": make_perf_profile(
        "PERF_2GB_CONC",
        ram_mb=2048,
        workers=4,
    ),
    "PERF_4GB_CONC": make_perf_profile(
        "PERF_4GB_CONC",
        ram_mb=4096,
        workers=4,
    ),
}
PERF_MATRIX = {
    "idle": {
        100: {"local": "PERF_512MB_LOCAL", "concurrent": "PERF_1GB_CONC"},
        1000: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        5000: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
    "movement": {
        100: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        500: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        1000: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
    "resource": {
        100: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        500: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        1000: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
    "combat": {
        10: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        50: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        100: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
    "strategic": {
        100: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        500: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        1000: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
    "mixed": {
        200: {"local": "PERF_1GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        500: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_2GB_CONC"},
        1000: {"local": "PERF_2GB_LOCAL", "concurrent": "PERF_4GB_CONC"},
    },
}
