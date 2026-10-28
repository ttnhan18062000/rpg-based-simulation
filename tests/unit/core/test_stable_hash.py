"""Unit tests for src.core.stable_hash.stable_int31 (TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID)."""
import pytest

from src.core.stable_hash import stable_int31


def test_stable_int31_is_repeatable_and_in_range():
    value = stable_int31("r2", "fa", 3)
    assert value == stable_int31("r2", "fa", 3)
    assert 0 <= value < 2 ** 31


def test_stable_int31_pinned_value():
    # Pinned so a change to the encoding or digest is a visible, deliberate edit.
    assert stable_int31("node_abc") == 1915432959


def test_stable_int31_distinct_tuples_differ():
    values = {
        stable_int31("r2", "fa", 3),
        stable_int31("r2", "fa", 4),
        stable_int31("r2", "fb", 3),
        stable_int31("fa", "r2", 3),   # order matters
        stable_int31("r2fa", 3),       # no concatenation collision
        stable_int31("r2", "fa", "3"), # str and int are distinct
    }
    assert len(values) == 6


@pytest.mark.parametrize("bad", [1.5, None, True, ("a",)])
def test_stable_int31_rejects_non_id_parts(bad):
    with pytest.raises(TypeError):
        stable_int31("r2", bad)
