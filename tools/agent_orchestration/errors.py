"""Named error type for the agent-orchestration/ contract validator.

Mirrors tools/agent_replay/fixture_envelope.py's FixtureValidationError pattern exactly: a
single flat exception class, no subclass hierarchy, raised with a message naming the exact
file path and the exact missing/malformed field.
"""
from __future__ import annotations


class ContractValidationError(Exception):
    """Raised by load_contract when a required agent-orchestration/ field is missing,
    malformed, or the YAML root is not a mapping."""


class GeneratorWriteGuardError(Exception):
    """Raised by generate() when a write target resolves outside agent-orchestration/ and the
    explicit allow_outside_contract flag was not passed."""
