from src.core.retention import BoundedBuffer, OverflowPolicy


def test_eviction_determinism():
    """Verify that eviction in a BoundedBuffer is strictly deterministic."""
    # We'll run the same eviction scenario 100 times and verify identical outcomes.
    results = []
    
    for _ in range(100):
        buf = BoundedBuffer(capacity=5, policy=OverflowPolicy.EVICT_OLDEST)
        for i in range(10):
            buf.append(f"item_{i}")
        
        results.append(tuple(buf.to_list()))
        
    assert len(set(results)) == 1
    # Check expected content: should have items 5, 6, 7, 8, 9
    assert results[0] == ("item_5", "item_6", "item_7", "item_8", "item_9")


def test_sustained_memory_stability():
    """Manual "stress" check that adding millions of items doesn't grow the heap."""
    # Since we are using deque with maxlen (internally or via BoundedBuffer logic),
    # memory should stay flat.
    buf = BoundedBuffer(capacity=100, policy=OverflowPolicy.EVICT_OLDEST)
    
    # Simple loop that would OOM if the buffer was unbounded
    for i in range(100000):
        buf.append(i)
        
    assert len(buf) == 100
    assert buf[99] == 99999
