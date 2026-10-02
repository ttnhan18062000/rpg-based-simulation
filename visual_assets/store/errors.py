"""Store errors. A leaf module: imports nothing from the project."""

from __future__ import annotations


class StoreError(Exception):
    """Base class for every error the store raises."""


class ContractError(StoreError):
    """A record failed to parse or validate. `code` is stable and machine-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class IdentityError(StoreError):
    """A value is not a canonical identity of the requested type."""


class RegistryError(StoreError):
    """The semantic visual-key registry is malformed or a key is unknown."""
