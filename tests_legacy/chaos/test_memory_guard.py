import pytest
import time
import os

def test_deliberate_memory_leak():
    """Verify that the ResourceWatchdog kills the process if it leaks too much."""
    print("\nStarting deliberate leak...")
    leak = []
    # Each strike is 0.5s. We need 3 strikes (> 1.5s total).
    # Watchdog limit is 1024MB.
    # We'll leak ~1.2GB.
    try:
        for i in range(12):
            # 100MB of bytes
            leak.append(bytearray(100 * 1024 * 1024))
            print(f"Leaked {len(leak) * 100} MB")
            time.sleep(0.6) # Wait for watchdog check
    except MemoryError:
        print("Hit MemoryError (Tier 1 RLIMIT likely)")
        raise
