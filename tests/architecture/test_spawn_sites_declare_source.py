"""Static spawn-site guard (TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK, AC5).

Every call to ``generator.spawn_*`` in ``src/`` creates an entity that reaches the world as a mid-run add, so its enclosing function must hand a
``SpawnSource`` to the update (``entity_spawn_sources``), or the site must sit in ``OFF_SITES`` below. A new spawn site then fails here, at unit-test
time, instead of after a 5000-tick gate run, which is how the camp spawn went unseen.

``OFF_SITES`` is a ratchet: it may only shrink. An entry whose site is now tagged, or no longer exists, fails until it is removed. Each entry names
its gating flag(s) and the ruling that put it OFF. The guard asserts each flag exists in the flag registry, defaults OFF, and is not turned on by
any gate world (its profile, its world files, or the harness flags), so an OFF site cannot wake in the gate unseen. Removed sites (the camp spawn,
the camp raid spawn, the density top-up) are never listed: once they are gone there is nothing to find.

Scope: ``src/certification/`` builds tick-0 scenario worlds (INITIAL, never an ``entities_add``) and ``generator.py`` defines the spawners; both are
excluded. The AST matches a call ``<receiver named generator>.spawn_*(...)`` anywhere in a function; it does not follow a result across functions, and "tagged" (`_mentions_tag`) is function-wide: any mention of `entity_spawn_sources` in the enclosing function counts for every spawn call in it, so a function with two spawn calls and one tag is read as tagged,
which is why a site that returns its spawn to a caller (``CalamityService._spawn_world_boss``) is listed at the function that makes the call.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
GATE_CONFIG = REPO / "tests" / "simulation_quality" / "rpg_gate" / "config.yaml"
PROFILES = REPO / "config" / "simulation_quality" / "profiles"
WORLDS = REPO / "data" / "worlds"
EXCLUDED_PREFIXES = ("src/certification/", "src/systems/world_systems/generator.py")
TAG = "entity_spawn_sources"
ON_VALUES = {"ON", "STRICT", "SHADOW"}


@dataclass(frozen=True)
class Gate:
    flag: str
    ruling: str


@dataclass(frozen=True)
class OffSite:
    """A spawn site the designer or owner ruled OFF: untagged on purpose, held shut by its flag(s). ``count`` is how many calls the function makes."""

    file: str
    function: str
    callee: str
    count: int
    gates: Tuple[Gate, ...]
    state: str = "OFF"

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.file, self.function, self.callee)


OFF_SITES: Tuple[OffSite, ...] = (
    OffSite("src/world/boss.py", "check_for_boss_spawn", "spawn_monster", 1, (Gate("ENABLE_WORLD_BOSS_SPAWN", "owner decision 14"),)),
    OffSite("src/world/boss.py", "check_for_lair_spawn", "spawn_monster", 1, (Gate("ENABLE_WORLD_BOSS_SPAWN", "owner decision 14"),)),
    OffSite("src/world/calamity.py", "_spawn_world_boss", "spawn_monster", 1, (Gate("ENABLE_WORLD_BOSS_SPAWN", "owner decision 14"),)),
    OffSite("src/world/calamity.py", "process_world_dynamics", "spawn_magical_demonic_entity", 1,
            (Gate("ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH", "DEV-002 / TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH"),)),
    OffSite("src/world/creature_territory.py", "process_territories", "spawn_monster", 1,
            (Gate("ENABLE_CREATURE_TERRITORY_LIFECYCLE", "D67/D70 stays OFF; DEV-002 / TCK-20260831-CREATURE-TERRITORY-LIFECYCLE"),)),
    # camp.py makes two calls to the same spawner, behind two different flags (rpg-planner ruling 2026-10-19: both OFF).
    OffSite("src/world/camp.py", "process_camps", "spawn_natural_creature_offspring", 2,
            (Gate("ENABLE_CAMP_NEST_SPREAD", "D70 / TCK-20261014-CAMPS-STOP-SPAWNING-MONSTERS-FROM-NOTHING-D70"),
             Gate("ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH", "DEV-002 / TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH"))),
)


def _receiver(node: ast.expr) -> Optional[str]:
    return node.id if isinstance(node, ast.Name) else getattr(node, "attr", None)


def _mentions_tag(func: ast.AST) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.keyword) and node.arg == TAG:
            return True
        if isinstance(node, ast.Name) and node.id == TAG:
            return True
        if isinstance(node, ast.Attribute) and node.attr == TAG:
            return True
    return False


def find_spawn_sites(root: Path, src: str = "src") -> List[Tuple[str, str, str, bool]]:
    """Every ``generator.spawn_*`` call under ``root/src`` as (file, innermost enclosing function, callee, that function carries a SpawnSource)."""
    found: List[Tuple[str, str, str, bool]] = []
    funcs = (ast.FunctionDef, ast.AsyncFunctionDef)
    for path in sorted((root / src).rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(EXCLUDED_PREFIXES):
            continue
        for func in (n for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))) if isinstance(n, funcs)):
            nested = {id(c) for inner in ast.walk(func) if inner is not func and isinstance(inner, funcs) for c in ast.walk(inner)}
            tagged = _mentions_tag(func)
            for call in (n for n in ast.walk(func) if isinstance(n, ast.Call) and id(n) not in nested):
                f = call.func
                if isinstance(f, ast.Attribute) and f.attr.startswith("spawn_") and _receiver(f.value) == "generator":
                    found.append((rel, func.name, f.attr, tagged))
    return found


def check_sites(sites: Sequence[Tuple[str, str, str, bool]], off_sites: Iterable[OffSite]) -> List[str]:
    """Violations of the ratchet: an untagged site that is not listed, a listed site that is tagged, stale or miscounted."""
    problems: List[str] = []
    listed = {s.key: s for s in off_sites}
    seen: Dict[Tuple[str, str, str], int] = {}
    for file, function, callee, tagged in sites:
        key = (file, function, callee)
        entry = listed.get(key)
        if tagged:
            if entry is not None:
                problems.append(f"stale allowlist entry {file}:{function}:{callee}: the site now passes a SpawnSource, remove the entry")
            continue
        if entry is None:
            problems.append(f"{file}:{function} calls generator.{callee} without handing a SpawnSource (entity_spawn_sources) to the update")
            continue
        seen[key] = seen.get(key, 0) + 1
    for key, entry in listed.items():
        if key in seen and seen[key] != entry.count:
            problems.append(f"allowlist entry {entry.file}:{entry.function}:{entry.callee} expects {entry.count} call(s), found {seen[key]}")
        elif key not in seen and not any((f, fn, c) == key for f, fn, c, _ in sites):
            problems.append(f"stale allowlist entry {entry.file}:{entry.function}:{entry.callee}: no such spawn site any more, remove the entry")
    return problems


def check_gates(off_sites: Iterable[OffSite], flag_defaults: Mapping[str, str], gate_worlds: Sequence[str], root: Path = REPO) -> List[str]:
    """Each gating flag is registered, defaults OFF, and no gate world turns it on (profile, world files, harness flags)."""
    problems: List[str] = []
    flags = {g.flag for s in off_sites for g in s.gates}
    for flag in sorted(flags):
        if flag not in flag_defaults:
            problems.append(f"{flag} is not in the feature-flag registry (a typo, or the flag was removed: update the entry)")
        elif flag_defaults[flag] != "OFF":
            problems.append(f"{flag} defaults to {flag_defaults[flag]}, not OFF: its OFF site is spawning untagged entities")
        for world in gate_worlds:
            profile = root / "config" / "simulation_quality" / "profiles" / f"{world}.yaml"
            if profile.exists():
                on = (yaml.safe_load(profile.read_text(encoding="utf-8")) or {}).get("feature_flags", {}) or {}
                if str(on.get(flag, "OFF")) in ON_VALUES:
                    problems.append(f"gate world {world} turns {flag} on in {profile.name}")
            for world_file in (root / "data" / "worlds" / world).rglob("*.yaml"):
                if flag in world_file.read_text(encoding="utf-8"):
                    problems.append(f"gate world {world} names {flag} in {world_file.relative_to(root).as_posix()}")
    return problems


def _flag_defaults() -> Dict[str, str]:
    from src.domains.optimization.feature_flags import FeatureFlagManager

    return FeatureFlagManager().serialize()


def _gate_worlds() -> List[str]:
    return list(yaml.safe_load(GATE_CONFIG.read_text(encoding="utf-8"))["worlds"])


def _harness_flags() -> Dict[str, object]:
    from tools.test_architecture.rpg_gate_harness import PIN_SETTINGS

    return dict(PIN_SETTINGS["flags"])


# --------------------------------------------------------------------------------------------- the real tree
def test_every_spawn_site_in_src_hands_a_spawn_source_or_is_ruled_off():
    assert check_sites(find_spawn_sites(REPO), OFF_SITES) == []


def test_the_tagged_humanoid_birth_site_is_seen_and_needs_no_entry():
    sites = find_spawn_sites(REPO)
    assert ("src/world/reproduction_humanoid.py", "process_reproduction", "spawn_humanoid_offspring", True) in sites


def test_every_off_site_is_held_shut_by_a_registered_off_by_default_flag_no_gate_world_turns_on():
    assert check_gates(OFF_SITES, _flag_defaults(), _gate_worlds()) == []
    assert not [k for k in _harness_flags() if str(k).startswith("ENABLE_")], "the gate harness must not set a feature flag"


def test_every_off_site_names_a_ruling_and_the_off_state():
    for site in OFF_SITES:
        assert site.state == "OFF" and site.gates and all(g.flag.startswith("ENABLE_") and g.ruling for g in site.gates), site


# --------------------------------------------------------------------------------------------- the guard fires
def _tree(tmp_path: Path, body: str, name: str = "world/new_site.py") -> Path:
    target = tmp_path / "src" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return tmp_path


UNSOURCED = "def process(generator, state):\n    mob = generator.spawn_monster(state=state)\n    return StateUpdate(entities_add=[mob])\n"
SOURCED = ("def process(generator, state):\n    mob = generator.spawn_monster(state=state)\n"
           "    return StateUpdate(entities_add=[mob], entity_spawn_sources={mob.id: SpawnSource(SpawnKind.INITIAL)})\n")


def test_a_new_unsourced_spawn_site_fails_the_guard(tmp_path):
    problems = check_sites(find_spawn_sites(_tree(tmp_path, UNSOURCED)), ())
    assert len(problems) == 1 and "new_site.py:process calls generator.spawn_monster without" in problems[0]


def test_a_sourced_spawn_site_passes_the_guard(tmp_path):
    assert check_sites(find_spawn_sites(_tree(tmp_path, SOURCED)), ()) == []


def test_a_stale_allowlist_entry_fails_when_the_site_is_gone(tmp_path):
    stale = OffSite("src/world/new_site.py", "gone", "spawn_monster", 1, (Gate("ENABLE_X", "r"),))
    problems = check_sites(find_spawn_sites(_tree(tmp_path, SOURCED)), (stale,))
    assert len(problems) == 1 and "stale allowlist entry" in problems[0] and "no such spawn site" in problems[0]


def test_an_allowlist_entry_whose_site_now_passes_a_source_fails_until_removed(tmp_path):
    entry = OffSite("src/world/new_site.py", "process", "spawn_monster", 1, (Gate("ENABLE_X", "r"),))
    problems = check_sites(find_spawn_sites(_tree(tmp_path, SOURCED)), (entry,))
    assert len(problems) == 1 and "now passes a SpawnSource" in problems[0]


def test_an_extra_call_beside_a_listed_site_fails_the_count(tmp_path):
    two = "def process(generator, state):\n    generator.spawn_monster(state=state)\n    generator.spawn_monster(state=state)\n"
    entry = OffSite("src/world/new_site.py", "process", "spawn_monster", 1, (Gate("ENABLE_X", "r"),))
    problems = check_sites(find_spawn_sites(_tree(tmp_path, two)), (entry,))
    assert len(problems) == 1 and "expects 1 call(s), found 2" in problems[0]


def test_a_flipped_flag_default_fails_the_gate_check():
    flipped = {**_flag_defaults(), "ENABLE_CAMP_NEST_SPREAD": "ON"}
    problems = check_gates(OFF_SITES, flipped, _gate_worlds())
    assert any("ENABLE_CAMP_NEST_SPREAD defaults to ON" in p for p in problems)


def test_a_flag_missing_from_the_registry_fails_the_gate_check():
    defaults = {k: v for k, v in _flag_defaults().items() if k != "ENABLE_CAMP_NEST_SPREAD"}
    assert any("ENABLE_CAMP_NEST_SPREAD is not in the feature-flag registry" in p for p in check_gates(OFF_SITES, defaults, _gate_worlds()))


def test_a_gate_world_that_turns_a_flag_on_fails_the_gate_check(tmp_path):
    profiles = tmp_path / "config" / "simulation_quality" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "w1.yaml").write_text('feature_flags:\n  ENABLE_CAMP_NEST_SPREAD: "ON"\n', encoding="utf-8")
    (tmp_path / "data" / "worlds" / "w1").mkdir(parents=True)
    problems = check_gates(OFF_SITES, _flag_defaults(), ["w1"], root=tmp_path)
    assert problems == ["gate world w1 turns ENABLE_CAMP_NEST_SPREAD on in w1.yaml"]
