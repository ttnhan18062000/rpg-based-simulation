---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-SIX-SKILLS-INVESTIGATION
artifact_type: test_plan
tags: [skills, process-improvement, investigation]
---

# Test Plan — TCK-20260705-SIX-SKILLS-INVESTIGATION

## Regression Surface
N/A — no code was touched. This is a read-only investigation into agent session-transcript history.

## New Tests Required
N/A — no code changed, no new automated test is warranted. Verification for this ticket instead means "can a reviewer re-run the exact counting commands and get the same numbers," addressed below.

## Scoped Pytest Commands
N/A — no pytest suite applies to a transcript-counting investigation.

## Reproducibility — How the Plan Phase Should Verify This Investigation's Claims

This project's reviewers have caught wrong numeric claims in this exact kind of ticket before (see `investigation.md`'s Prior Work section: an initial naive count of `docs/` edits landed at 528 against a claimed 659/669, traced to a two-absolute-repo-root path issue). Every number in `investigation.md` is reproducible from the scripts below. Re-run them verbatim against the same transcript directory to confirm.

### 1. Skill invocation counts

Script (saved during this investigation at `/tmp/claude-1000/-home-vboxuser-Work-rpg-based-simulation/ea1b0fe0-9aef-4d15-9e4a-9135f49eda71/scratchpad/count_skills.py`, reproduced in full below since scratchpad files are not durable):

```python
#!/usr/bin/env python3
import json, glob, collections

DIR = "/home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation"
files = sorted(glob.glob(DIR + "/*.jsonl"))

skill_counts = collections.Counter()

for fp in files:
    with open(fp, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if '"name": "Skill"' not in line and '"name":"Skill"' not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            def walk(o):
                if isinstance(o, dict):
                    if o.get("type") == "tool_use" and o.get("name") == "Skill":
                        skill = o.get("input", {}).get("skill", "<MISSING>")
                        skill_counts[skill] += 1
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(obj)

print(f"Total files scanned: {len(files)}")
print(f"Total Skill tool_use invocations found: {sum(skill_counts.values())}")
for skill, cnt in sorted(skill_counts.items(), key=lambda x: -x[1]):
    print(f"  {skill}: {cnt}")
```

**Expected output** (as of this investigation, 27 files): `Total files scanned: 27`, `Total Skill tool_use invocations found: 41`, with `graphify: 21`, `create-tickets: 6`, `implement-epic: 5`, `implement-ticket: 4`, `update-config: 2`, `artifact-design: 1`, `fewer-permission-prompts: 1`, `agent-monitoring-retro: 1`, and all of `test-driven-development`, `python-testing-patterns`, `backend-testing`, `architecture`, `brainstorming`, `doc-coauthoring` absent from the printed list (i.e. zero).

A quick non-Python sanity check for the same headline claim (zero invocations of the 6 target skills):

```bash
for s in test-driven-development python-testing-patterns backend-testing architecture brainstorming doc-coauthoring; do
  echo -n "$s: "
  grep -l "\"skill\":\"$s\"\|\"skill\": \"$s\"" \
    /home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation/*.jsonl 2>/dev/null | wc -l
done
```
Expected: `0` for every line (this counts *files containing at least one match*, a coarser but independent cross-check).

### 2. Edit/Write path counts (tests/, docs/architecture/, docs/) — path-normalized

**Critical methodology note:** two absolute repo roots appear across the 27 transcripts — `/home/vboxuser/Work/rpg-based-simulation/...` (current machine) and `/home/u24desktop/Working/rpg-based-simulation/...` (an older machine). Any script that strips only the current machine's absolute prefix will silently undercount `docs/`-path edits by ~140 events (528 vs. the correct 669) and must instead normalize on the `rpg-based-simulation/` marker common to both roots. This was independently rediscovered during this investigation and is the exact class of error the CLAUDE.md discipline is trying to prevent — re-verify this normalization step specifically, don't just re-run the final script and trust it.

```python
#!/usr/bin/env python3
import json, glob, re, collections

DIR = "/home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation"
files = sorted(glob.glob(DIR + "/*.jsonl"))
MARKER = "rpg-based-simulation/"

def to_rel(path):
    if not isinstance(path, str) or not path:
        return None
    idx = path.find(MARKER)
    if idx == -1:
        return None
    return path[idx + len(MARKER):]

tool_counts = collections.Counter()
paths = []

for fp in files:
    with open(fp, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or '"tool_use"' not in line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            def walk(o):
                if isinstance(o, dict):
                    if o.get("type") == "tool_use" and o.get("name") in ("Edit", "Write"):
                        rel = to_rel(o.get("input", {}).get("file_path", ""))
                        if rel is not None:
                            paths.append((o["name"], rel))
                            tool_counts[o["name"]] += 1
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(obj)

rels = [p for _, p in paths]
tests_paths = [p for p in rels if re.match(r'^tests/', p)]
docs_arch_paths = [p for p in rels if p.startswith("docs/architecture/")]
docs_all_paths = [p for p in rels if p.startswith("docs/")]

print(f"Edit: {tool_counts.get('Edit',0)}  Write: {tool_counts.get('Write',0)}  Total: {sum(tool_counts.values())}")
print(f"tests/ : {len(tests_paths)}")
print(f"docs/architecture/ : {len(docs_arch_paths)}")
print(f"docs/ (all) : {len(docs_all_paths)}")
```

**Expected output** (as of this investigation): `Edit: 1777  Write: 868  Total: 2645`, `tests/ : 281`, `docs/architecture/ : 9`, `docs/ (all) : 669`.

**Independent shell-based cross-check** (jq-based, no Python, catches the same normalization issue if done correctly):

```bash
for f in /home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation/*.jsonl; do
  jq -c 'select(.message.content? != null) | .message.content[]? | select(.type=="tool_use" and (.name=="Edit" or .name=="Write")) | .input.file_path' "$f" 2>/dev/null
done | grep -oE 'rpg-based-simulation/(tests|docs)/[^"]*' | sed 's#^rpg-based-simulation/##' > /tmp/all_edit_write_paths.txt

echo "tests/: $(grep -c '^tests/' /tmp/all_edit_write_paths.txt)"
echo "docs/architecture/: $(grep -c '^docs/architecture/' /tmp/all_edit_write_paths.txt)"
echo "docs/ (all): $(grep -c '^docs/' /tmp/all_edit_write_paths.txt)"
```
(Note: transcript JSON structure may nest tool_use blocks differently than a flat `.message.content[]?` in some entries — e.g. some lines in these 27 transcripts are top-level `{"type":"tool_use",...}` without a `.message` wrapper. If this jq one-liner returns 0 for everything, fall back to the Python walker above, which recursively searches the entire parsed object regardless of nesting depth — that's why the Python version was used as the source of truth for this investigation's numbers, and the jq command here is offered only as a partial cross-check.)

### 3. docs/ subdirectory categorization

```bash
# after running the Python script above with the additional line:
#   with open("/tmp/docs_all_paths.txt","w") as out:
#       for p in docs_all_paths: out.write(p + "\n")
sed -E 's#^docs/([^/]+)/.*#\1#; t; s#^docs/(.*)#\1 (top-level file)#' /tmp/docs_all_paths.txt | sort | uniq -c | sort -rn
```
Expected top entries: `331 audits`, `75 plans`, `49 engine`, `38 parity_ledger`, `29 mechanics` (all-edits-including-repeats count; unique-file counts are lower — see `investigation.md`'s table).

### 4. `tests/` subdirectory breakdown

```bash
sed -E 's#^tests/([^/]+)/.*#\1#; t; s#^tests/(.*)#\1 (top-level file)#' /tmp/tests_paths.txt | sort | uniq -c | sort -rn
```
Expected: `127 unit`, `64 integration`, `32 simulation_quality`, `10 perf`, `10 integrity`, `8 conftest.py`, `7 tools`, `7 certification`, `4 observability`, `4 architecture`, `3 regression`, `2 docs`, `1` each for `static`/`arena`/`api`.

### 5. In-repo precedent checks (independent of transcripts)

```bash
find /home/vboxuser/Work/rpg-based-simulation/tests -maxdepth 2 -iname "conftest.py" | wc -l
# Expected: 5

grep -rl "unittest.mock\|@pytest.fixture\|@pytest.mark.parametrize" /home/vboxuser/Work/rpg-based-simulation/tests 2>/dev/null | wc -l
# Expected: 303
```

### 6. `AskUserQuestion` sample for the `brainstorming` proxy

```bash
python3 - <<'EOF'
import json, glob
DIR = "/home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation"
count = 0
for fp in sorted(glob.glob(DIR + "/*.jsonl")):
    with open(fp, errors="replace") as f:
        for line in f:
            if "AskUserQuestion" not in line:
                continue
            try:
                obj = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            def walk(o):
                global count
                if isinstance(o, dict):
                    if o.get("type") == "tool_use" and o.get("name") == "AskUserQuestion":
                        count += 1
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(obj)
print("Total AskUserQuestion tool_use calls:", count)
EOF
# Expected: 36
```
Re-read each of the 36 (dump their `input.questions` field) and judge by hand whether any represent a from-scratch creative-feature design exploration (brainstorming's actual trigger) vs. a decision fork embedded in already-scoped ticket work. This investigation's judgment (all 36 are the latter) is a qualitative call, not a pure count — a reviewer should re-read the dump, not just re-run the count, to confirm or dispute the categorization.

### 7. Reconciling against the prior ticket's cited numbers

The prior ticket (`TCK-20260704-SKILL-TRIGGER-COVERAGE`) cited 281 / 9 / 659 for the same three metrics, over "the last 30 session transcripts." This investigation's 281 / 9 / 669 (path-normalized) match within the expected +10 delta for one additional day of work. If a reviewer re-runs these scripts and gets materially different numbers than 281 / 9 / 669, check first whether the transcript file count is still 27 (`ls /home/vboxuser/.claude/projects/-home-vboxuser-Work-rpg-based-simulation/*.jsonl | wc -l`) — if it has grown (more sessions since 2026-07-05), a delta proportional to elapsed time is expected and not itself evidence of a counting error.
