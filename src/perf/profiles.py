from src.config.profiles import RuntimeProfile, HardwareClass


def make_perf_profile(
    name: str,
    *,
    ram_mb: int,
    workers: int,
    tick_budget_ms: float = 100.0,
    queue_depth: int = 1000,
    replay_buffer_kb: int = 8192,
    observability_budget_percent: float = 5.0,
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
