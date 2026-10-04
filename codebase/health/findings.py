"""The one normalised record every code-health adapter produces and the ratchet compares.

A `Finding` says "this tool measured this much of this rule at this place". The ratchet and the
registry both key on `(file, symbol, tool, rule)` and never on a line number, so moving code
within a file does not make an old violation look new.

Match keys by tool (python_code_craft_roadmap.md section 6.3):

- ruff:        `(file, None, "ruff", <rule code>)`, value = number of findings of that rule in the
               file. Ruff gives no enclosing symbol for most rules, so the unit is one file and one
               rule. Known limit: fixing one violation and adding another of the same rule in the
               same file in one change nets to zero and is not caught.
- complexipy:  `(file, "Class.method", "complexipy", "cognitive-complexity")`, value = the
               function's cognitive complexity, only for functions over the configured limit.
- line_count:  `(file, "Class.method", "line_count", "function-length")` and the same for
               `class-length`; `(file, None, "line_count", "module-length")`. Value = lines, only
               for functions over the fail limit and classes or modules over their limit.
- jscpd:       `(lower_path, "dup:" + higher_path, "jscpd", "duplicate-block")`, value = total
               duplicated lines between that pair of files (the pair is ordered so it has one key).
               A clone that moves inside either file keeps its key; a new clone between files that
               had none, or more duplicated lines between files that did, is new or worse.

- ast_grep:    `(file, "Class.method" | "<module>", "ast_grep", <rule id>)`, value = number of findings of that rule
               in that symbol. The symbol is the innermost enclosing def or class (computed from the file with the
               stdlib `ast`, `<module>` when there is none), so module-level findings keep a stable key. The rules
               live in `codebase/rules/`; the binary is `ast-grep`, never `sg`.

A function renamed, or moved to another file, surfaces as new. That is accepted: it is a real
change to the code, and the old row then shows as "gone" and can be deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Literal

TOOL_RUFF = "ruff"
TOOL_COMPLEXIPY = "complexipy"
TOOL_JSCPD = "jscpd"
TOOL_LINE_COUNT = "line_count"
TOOL_AST_GREP = "ast_grep"

Key = tuple[str, str | None, str, str]


@dataclass(frozen=True)
class Finding:
    """One measured violation. `line` is for display only and is not part of equality or the key."""

    file: str
    symbol: str | None
    tool: str
    rule: str
    value: int
    line: int | None = field(default=None, compare=False)

    @property
    def key(self) -> Key:
        """The line-independent identity used to match a finding to a baseline row."""
        return (self.file, self.symbol, self.tool, self.rule)


def aggregate(findings: Iterable[Finding], mode: Literal["sum", "max"]) -> list[Finding]:
    """Merge findings that share a key: add their values (counts) or keep the largest (measures)."""
    merged: dict[Key, Finding] = {}
    for finding in findings:
        seen = merged.get(finding.key)
        if seen is None:
            merged[finding.key] = finding
            continue
        value = seen.value + finding.value if mode == "sum" else max(seen.value, finding.value)
        lines = [n for n in (seen.line, finding.line) if n is not None]
        merged[finding.key] = Finding(*finding.key, value, min(lines) if lines else None)
    return sorted(merged.values(), key=lambda f: (f.file, f.symbol or "", f.tool, f.rule))
