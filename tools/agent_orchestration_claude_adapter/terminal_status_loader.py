"""Compatibility re-export of the provider-neutral terminal-status loader."""
from tools.agent_orchestration.terminal_statuses import (
    TerminalStatusValidationError,
    load_terminal_statuses,
    validate_terminal_statuses,
)

__all__ = ["TerminalStatusValidationError", "load_terminal_statuses", "validate_terminal_statuses"]
