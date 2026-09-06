"""Completeness cross-check for TCK-20260906-SIMQ-CALIBRATION-AND-COMPLETENESS: validates the
named-pillar mapping ticket 1 recorded for all 65 ideas in design_merit_scorecard.html against the
10 real pillars (each already confirmed by ticket 1's own event-type audit to have real, scored
event coverage), and flags any structural inconsistency (a named pillar that isn't real, or a
named-pillar count that doesn't match the raw N/10 the axis still records)."""
import json
import re

VALID_PILLARS = {
    "COGNITION", "AGENCY", "COMBAT", "FACTION", "ECONOMY", "PROGRESSION",
    "SOCIAL", "INFORMATION", "WORLD", "NARRATIVE",
}
DORMANT_IDEAS = {56, 57, 62}

html = open("docs/brainstorm/design_merit_scorecard.html", encoding="utf-8").read()
rows = re.findall(r'<tr id="score-(\d+)">(.*?)</tr>', html, re.DOTALL)

gaps = []
passes = []
for idnum_s, block in rows:
    idnum = int(idnum_s)
    tds = re.findall(r'<td class="score">([^<]*)</td>', block)
    title_m = re.search(r'idea-title"><span class="num">\d+\.</span>\s*([^<]+)</td>', block)
    title = title_m.group(1).strip() if title_m else "?"
    pillar_reach = tds[3] if len(tds) > 3 else ""
    m = re.match(r"([A-Z, ]*)\s*\((\d+)/10\)", pillar_reach.strip())
    if not m:
        gaps.append({"idea": idnum, "title": title, "pillar_reach": pillar_reach, "issue": "unparseable Pillar Reach cell"})
        continue
    names_raw = m.group(1).strip().rstrip(",")
    claimed_count = int(m.group(2))
    names = [n.strip() for n in names_raw.split(",") if n.strip()]
    bad_names = [n for n in names if n not in VALID_PILLARS]
    if bad_names:
        gaps.append({"idea": idnum, "title": title, "pillar_reach": pillar_reach, "issue": f"unrecognized pillar name(s): {bad_names}"})
    elif len(names) != claimed_count and idnum not in DORMANT_IDEAS:
        gaps.append({"idea": idnum, "title": title, "pillar_reach": pillar_reach, "issue": f"named count {len(names)} != claimed raw count {claimed_count}"})
    else:
        passes.append({"idea": idnum, "title": title, "pillars": names, "raw_count": claimed_count})

print(json.dumps({"total_rows": len(rows), "pass_count": len(passes), "gap_count": len(gaps), "gaps": gaps}, indent=2))
