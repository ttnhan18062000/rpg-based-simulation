from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T", contravariant=True)


@runtime_checkable
class Authoritative(Protocol):
    """
    Marker protocol for types that are strictly authoritative.
    Used for structural enforcement in tests and persistence.
    """
    pass


@runtime_checkable
class Degradable(Protocol):
    """
    Marker protocol for systems or data that can be shed under pressure.
    Core simulation semantics must NOT implement this.
    """
    pass


class KernelContractError(Exception):
    """Raised when a kernel law or resource envelope is violated."""
    pass
