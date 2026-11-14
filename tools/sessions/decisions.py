"""Decision vocabulary and amendment index for session role cards (read-only).

`registries/session_decisions.yaml` maps the short names a card uses to `path[#section]`. A card source
lists the names it uses under `## Cites` (outside `## Card`, so the list is not injected). A doc that
accepts an amendment says so in an optional frontmatter key `amends: [path#section, ...]`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from tools.sessions.roster import REPO_ROOT

DECISIONS_REL_PATH = Path("registries/session_decisions.yaml")
TEMPLATE_DIR = Path("docs/guidelines/session_roles")
ACTIVE_STATUSES = ("active", "authoritative")
NONE_MARKER = "none"

_CARD = re.compile(r"^## Card\s*\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)
_CITES = re.compile(r"^## Cites\s*\n(.*?)(?=^## |\Z)", re.DOTALL | re.MULTILINE)
_CITE_LINE = re.compile(r"^\s*[-*]\s*(\S+)\s*->\s*(\S+)\s*$")
_DOC_PATH = re.compile(r"(?<![\w/.-])(docs/[\w./-]+\.md)")
_DECISION_TOKEN = re.compile(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*_(?:adr|decisions?)\b")
_FRONTMATTER_HEAD_LINES = 60


class DecisionsError(ValueError):
    """The vocabulary file is not shaped as the loader requires."""


@dataclass(frozen=True)
class Decision:
    name: str
    path: str  # without the #section
    section: str | None
    aliases: tuple[str, ...]

    @property
    def target(self) -> str:
        return f"{self.path}#{self.section}" if self.section else self.path

    @property
    def spellings(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


def split_target(target: str) -> tuple[str, str | None]:
    path, _, section = target.partition("#")
    return path, (section or None)


def covers(amended: str, cited: str) -> bool:
    """An `amends:` target covers a cited target: same path, and the sections are equal or either is absent."""
    a_path, a_section = split_target(amended)
    c_path, c_section = split_target(cited)
    return a_path == c_path and (a_section is None or c_section is None or a_section == c_section)


def load_decisions(root: Path = REPO_ROOT) -> dict[str, Decision]:
    path = root / DECISIONS_REL_PATH
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DecisionsError(f"{path}: {exc}") from exc
    entries = (data or {}).get("decisions")
    if not isinstance(entries, dict):
        raise DecisionsError(f"{path}: `decisions` must be a mapping")
    out: dict[str, Decision] = {}
    for name, body in entries.items():
        if not isinstance(body, dict) or not isinstance(body.get("path"), str):
            raise DecisionsError(f"{path}: {name}: needs a `path`")
        file_path, section = split_target(body["path"])
        out[str(name)] = Decision(str(name), file_path, section, tuple(str(a) for a in body.get("aliases") or ()))
    return out


def card_text(source: str) -> str:
    match = _CARD.search(source)
    return match.group(1) if match else ""


def parse_cites(source: str) -> dict[str, str] | None:
    """`short_name -> target` from the `## Cites` section; None when the section is absent."""
    match = _CITES.search(source)
    if match is None:
        return None
    cites: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.strip().lstrip("-* ").lower() == NONE_MARKER:
            continue
        found = _CITE_LINE.match(line)
        if found:
            cites[found.group(1)] = found.group(2)
    return cites


def _spelling_regex(spelling: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w-]){re.escape(spelling)}(?![\w-])")


def names_used(card: str, vocab: dict[str, Decision]) -> set[str]:
    """Vocabulary names whose name or alias appears in the card text."""
    return {d.name for d in vocab.values() if any(_spelling_regex(s).search(card) for s in d.spellings)}


def unlisted_references(card: str, vocab: dict[str, Decision]) -> list[str]:
    """Doc paths and `*_adr` / `*_decision(s)` tokens in a card that resolve to no vocabulary entry."""
    paths = {d.path for d in vocab.values()}
    spellings = {s for d in vocab.values() for s in d.spellings}
    missing = [p for p in _DOC_PATH.findall(card) if p not in paths]
    missing += [t for t in _DECISION_TOKEN.findall(card) if t not in spellings]
    return sorted(set(missing))


def heading_slugs(text: str) -> set[str]:
    slugs = set()
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if match:
            slug = re.sub(r"[^\w\s-]", "", match.group(1).lower())
            slugs.add(re.sub(r"\s+", "-", slug.strip()))
    return slugs


def target_problem(target: str, root: Path = REPO_ROOT) -> str | None:
    path, section = split_target(target)
    file = root / path
    if not file.is_file():
        return f"{path}: no such file"
    if section and section not in heading_slugs(file.read_text(encoding="utf-8")):
        return f"{path}: no heading for #{section}"
    return None


def _frontmatter(path: Path) -> dict | None:
    try:
        head = path.read_text(encoding="utf-8").splitlines()[:_FRONTMATTER_HEAD_LINES]
    except (OSError, UnicodeDecodeError):
        return None
    if not head or head[0].strip() != "---":
        return None
    try:
        end = head.index("---", 1)
    except ValueError:
        return None
    try:
        data = yaml.safe_load("\n".join(head[1:end]))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


@dataclass(frozen=True)
class Amendment:
    doc: str  # repo-relative path of the amending doc
    targets: tuple[str, ...]
    problem: str | None = None  # set when `amends:` is not a list of strings


def amending_docs(root: Path = REPO_ROOT) -> list[Amendment]:
    """Docs under docs/ with an `amends:` key whose own status is active or authoritative."""
    found = []
    for path in sorted((root / "docs").rglob("*.md")):
        fm = _frontmatter(path)
        if not fm or "amends" not in fm or fm.get("status") not in ACTIVE_STATUSES:
            continue
        rel = path.relative_to(root).as_posix()
        value = fm["amends"]
        if isinstance(value, list) and all(isinstance(v, str) for v in value):
            found.append(Amendment(rel, tuple(value)))
        else:
            found.append(Amendment(rel, (), "`amends:` must be a list of path#section strings"))
    return found
