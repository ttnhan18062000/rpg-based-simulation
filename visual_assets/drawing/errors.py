"""Errors raised by the drawing tools. The message is always safe to show the agent."""


class AdapterError(Exception):
    """A rejected or failed request. Message is safe to show the agent."""
