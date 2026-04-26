from src_legacy.config.profiles import RuntimeProfile, HardwareClass

def test_profile_instantiation():
    try:
        p = RuntimeProfile(
            name="test_b",
            hardware_class=HardwareClass.CLASS_A,
            max_ram_mb=1024,
            max_cpu_percent=90.0,
            max_worker_count=4,
            max_queue_depth=100,
            max_replay_buffer_kb=512,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=16.6,
            # Milestone B fields should have defaults, but let's test explicit
            sampling_interval_ticks=20,
            recovery_watermark=0.75,
            dwell_time_ticks=15,
            confidence_window_ticks=10
        )
        print("Profile instantiation successful.")
        print(f"Sampling Interval: {p.sampling_interval_ticks}")
        print(f"Recovery Watermark: {p.recovery_watermark}")
    except Exception as e:
        print(f"Instantiation failed: {e}")

if __name__ == "__main__":
    test_profile_instantiation()
