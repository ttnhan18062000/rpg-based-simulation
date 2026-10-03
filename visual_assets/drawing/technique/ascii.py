"""Text rendering of a colour grid with a legend."""

from __future__ import annotations

from collections import Counter


def ascii_grid(grid: list[list[str]]) -> tuple[list[str], dict[str, str]]:
    """Turn a hex grid into text rows plus a legend. '.' is transparent; opaque colours get
    letters/digits in order of first appearance (most opaque colours first by frequency)."""
    counts = Counter(c for row in grid for c in row if not c.endswith("00"))
    symbols = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    legend = {}
    for i, (c, _) in enumerate(counts.most_common()):
        legend[c] = symbols[i] if i < len(symbols) else "?"
    rows = ["".join("." if c.endswith("00") else legend[c] for c in row) for row in grid]
    return rows, {sym: col for col, sym in legend.items()}
