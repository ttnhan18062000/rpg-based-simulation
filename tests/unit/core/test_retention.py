import pytest
from src.core.retention import BoundedBuffer, OverflowPolicy, RetentionError


def test_bounded_list_overflow_evict_oldest():
    """Verify that EVICT_OLDEST drops the head when full."""
    buf = BoundedBuffer(capacity=3, policy=OverflowPolicy.EVICT_OLDEST)
    
    buf.append(1)
    buf.append(2)
    buf.append(3)
    assert len(buf) == 3
    
    buf.append(4)
    assert len(buf) == 3
    assert buf[0] == 2
    assert buf[2] == 4


def test_bounded_list_reject():
    """Verify that REJECT fails to add items when full."""
    buf = BoundedBuffer(capacity=2, policy=OverflowPolicy.REJECT)
    
    buf.append("A")
    buf.append("B")
    
    with pytest.raises(RetentionError):
        buf.append("C")
    
    assert len(buf) == 2
    assert buf[0] == "A"


def test_truncate_newest():
    """Verify that TRUNCATE_NEWEST drops the incoming item."""
    buf = BoundedBuffer(capacity=2, policy=OverflowPolicy.TRUNCATE_NEWEST)
    
    buf.append("first")
    buf.append("second")
    
    kept = buf.append("third")
    assert kept is False
    assert len(buf) == 2
    assert buf[1] == "second"
