import pytest
from src.engine.observability import SignalCollector
from unittest.mock import MagicMock


def test_signal_collector_bounded_history():
    """
    M7 Law: No Unbounded History. Trending must use fixed-size windows.
    Verifies that SignalCollector doesn't aggregate unbounded lists.
    """
    collector = SignalCollector(profile_name="TEST", sampling_interval=1)
    
    # Simulate 1000 ticks of sampling
    for i in range(1, 1001):
        collector.collect_platform_signals(i)
        
    # Internally we should only have running sums/averages or fixed deques.
    # We verify the collectors internal state doesn't have 1000 items.
    
    # M7 Law: Trending must use fixed-size windows (deque maxlen=5).
    assert len(collector._rss_history) == 5
    
    # We also check that snapshot doesn't grow.
    kernel = MagicMock()
    kernel.state.tick = 1000
    kernel.status.signal_history = []
    kernel.replay.buffer_usage_kb = 0
    
    snapshot = collector.get_snapshot(kernel)
    snapshot_dict = snapshot.__dict__
    assert len(snapshot_dict) < 20 # Bounded field set


def test_sampling_cadence_enforced():
    """
    M7 Law: RSS sampling is every N ticks by default.
    """
    # Sampling every 5 ticks
    collector = SignalCollector(profile_name="TEST", sampling_interval=5)
    
    # Tick 1: No sampling
    signals1 = collector.collect_platform_signals(1)
    assert collector._cached_rss_mb == 0.0
    
    # Mocking self._process.memory_info
    collector._process.memory_info = MagicMock(return_value=MagicMock(rss=100 * 1024 * 1024))
    
    # Tick 5: First sample
    collector.collect_platform_signals(5)
    assert collector._cached_rss_mb == 100.0
    
    # Tick 6: Use cached value (Mock memory change but it shouldn't be seen)
    collector._process.memory_info.return_value.rss = 200 * 1024 * 1024
    collector.collect_platform_signals(6)
    assert collector._cached_rss_mb == 100.0 # STALE (As intended)
    
    # Tick 10: New sample
    collector.collect_platform_signals(10)
    assert collector._cached_rss_mb == 200.0
