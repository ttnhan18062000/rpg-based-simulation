"""Store errors. A leaf module: imports nothing from the project."""

from __future__ import annotations


class StoreError(Exception):
    """Base class for every error the store raises."""


class ContractError(StoreError):
    """A record failed to parse or validate. `code` is stable and machine-readable.

    `field` is the dotted path of the first offending field when the failure is about one field, else `None`.
    It can echo producer-controlled text (an unknown key), so it is never trusted as safe to display.
    """

    def __init__(self, code: str, message: str, field: str | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.field = field


class StageError(StoreError):
    """A candidate package was refused before any byte was copied (so nothing was staged). Not a finding."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class IntakeError(StoreError):
    """An intake or review request cannot proceed (unknown id, not PASSED, staged bytes changed, ...)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class PngDecodeError(StoreError):
    """A PNG was refused by the bounded reader. `code` is one of: signature, crc, unsupported, dimensions, truncated, too_large,
    trailing_data, malformed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class RenderError(StoreError):
    """The store could not render a source with Aseprite (unavailable, failed, unsupported scale). `code` is stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class BuildError(StoreError):
    """`build` or `release` refused or failed. Nothing was written. `code` is stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ReadError(StoreError):
    """A read-only listing or lookup was refused (unknown kind, malformed or unknown id). `code` is stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class GateError(StoreError):
    """A human-gated command (`adopt`, `revoke`) refused. Nothing was written. `code` is stable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class IdentityError(StoreError):
    """A value is not a canonical identity of the requested type."""


class RegistryError(StoreError):
    """The semantic visual-key registry is malformed or a key is unknown."""
