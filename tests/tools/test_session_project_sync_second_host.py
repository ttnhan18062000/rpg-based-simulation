"""TCK-20261114-PROJECT-SYNC-SECOND-HOST: two hosts write one Project, each only its own `Host facts` segment. No network."""
from datetime import datetime, timezone

from tools.agent_working_paths import TICKETS
from tools.sessions import project_sync as ps

T = TICKETS.as_posix()
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
CFG = {"pilot_lanes": ["rpg"], "pilot_start": "2026-11-12", "done_window_days": 14, "stale_branch_days": 14}
A, B = "u24desktop", "ubuntu"  # A sorts first, so it is the lowest host tag
TID = "TCK-20261114-TWO"
STALE_BEFORE = NOW.timestamp() - 14 * 86400
OLD, FRESH = STALE_BEFORE - 86400, STALE_BEFORE + 86400


def copy(title="Origin title", folder="inprogress", blocked=False, tid=TID):
    return ps.TicketCopy(tid, folder, f"{T}/{folder}/{tid}.md", title, "hotfix", blocked, "2026-11-14")


def fact(host, title="Branch title", folder="inprogress", blocked=False, activity=0.0, seat=None, tid=TID):
    seat = seat if seat is not None else ("rpg-implementer-u24" if host == A else "rpg-implementer")
    return ps.BranchFact(host, f"rpg-{host}", f"/wt/{host}", seat, "rpg", (copy(title, folder, blocked, tid),), activity)


def item(host_facts="", branch="", **fields):
    return {"Ticket ID": TID, "Title": f"{TID}: x", "Host facts": host_facts, "Branch": branch, "_item_id": "I1", "_draft_id": "D1", **fields}


def plan_for(host, branches, items=(), main=None, tid=TID):
    main = main if main is not None else []
    index = {tid: [(c.folder, c.path) for c in main]} if main else {}
    loaded = {c.path: c for c in main}
    return ps.build_plan(index, lambda p: loaded[p], list(branches), [], list(items), host, "abc @ now", CFG, lambda p: None, NOW)


def derive(host, branches, current=None, main=()):
    return ps.derive_item(TID, list(main), list(branches), None, current, host, "s", STALE_BEFORE)


def seg(state, seats="", domains="rpg"):
    return f"state={state}" + (f" seat={seats}" if seats else "") + (f" domain={domains}" if domains else "")


def facts_text(a=None, b=None):
    return "; ".join(x for x in (f"{A}: {a}" if a else "", f"{B}: {b}" if b else "") if x)


# ---- encoding

def test_host_facts_round_trip_and_a_malformed_segment_is_a_finding_not_an_error():
    text = facts_text(seg("progress", "a,b"), seg("blocked", "c"))
    assert ps.format_host_facts(ps.parse_host_facts(text)) == text
    findings: list[str] = []
    parsed = ps.parse_host_facts(f"{A}: state=bogus; nonsense; {B}: {seg('filing', domains='')}", findings)
    assert list(parsed) == [B] and len(findings) == 2


def test_a_segment_stores_recorded_seats_only_and_the_placeholder_is_made_at_render_time():
    unrecorded = fact(B, seat="rpg (seat not recorded)")
    item_, _ = derive(B, [unrecorded])
    assert "seat=" not in item_["Host facts"] and item_["Seat"] == "rpg (seat not recorded)"
    filing, _ = derive(B, [fact(B, folder="todos")])
    assert filing["Host facts"] == f"{B}: state=filing domain=rpg" and filing["Seat"] == ""  # a filing segment gives no seat


# ---- status from the union

def test_blocked_comes_from_another_hosts_segment_and_origin_blocked_counts_only_with_an_empty_union():
    cur = item(facts_text(b=seg("blocked", "rpg-implementer")))
    assert derive(A, [fact(A)], cur)[0]["Status"] == "Blocked"
    assert derive(A, [], cur)[0]["Status"] == "Blocked"  # A has no copy and still sees B's blocked
    origin_blocked = [copy(folder="todos", blocked=True)]
    assert derive(A, [], item(), main=origin_blocked)[0]["Status"] == "Blocked"
    assert derive(A, [], item(facts_text(b=seg("progress"))), main=origin_blocked)[0]["Status"] == "In progress"


def test_stale_only_when_every_working_host_is_stale():
    assert derive(A, [fact(A, activity=OLD)], item(facts_text(b=seg("stale"))))[0]["Status"] == "Stale"
    assert derive(A, [fact(A, activity=FRESH)], item(facts_text(b=seg("stale"))))[0]["Status"] == "In progress"
    assert derive(A, [fact(A, activity=OLD)], item(facts_text(b=seg("progress"))))[0]["Status"] == "In progress"
    assert derive(A, [], item(facts_text(b=seg("stale"))))[0]["Status"] == "Stale"
    assert derive(A, [fact(A, folder="todos")], item(facts_text(b=seg("stale"))))[0]["Status"] == "Stale"  # filing is not working


def test_seat_and_domain_are_the_union_of_the_segments_and_shrink_when_a_host_leaves():
    both = item(facts_text(seg("progress", "rpg-implementer-u24"), seg("progress", "rpg-implementer", "perf")))
    derived, _ = derive(A, [fact(A)], both)
    assert derived["Seat"] == "rpg-implementer, rpg-implementer-u24" and derived["Domain"] == "perf, rpg"
    left, _ = derive(B, [fact(B)], item(facts_text(a=seg("progress", "rpg-implementer-u24"))))
    assert left["Seat"] == "rpg-implementer, rpg-implementer-u24"
    only_b, _ = derive(A, [], item(facts_text(a=seg("progress", "rpg-implementer-u24"), b=seg("progress", "rpg-implementer"))))
    assert only_b["Seat"] == "rpg-implementer" and only_b["Host facts"] == facts_text(b=seg("progress", "rpg-implementer"))


def test_own_segment_is_replaced_and_the_other_hosts_kept_byte_for_byte():
    other = seg("blocked", "rpg-implementer", "perf")
    derived, _ = derive(A, [fact(A)], item(facts_text(a=seg("filing"), b=other)))
    assert derived["Host facts"] == facts_text(seg("progress", "rpg-implementer-u24"), other)


# ---- content rule M4

def title(host, current, main=(), branches=None):
    branches = [fact(host, f"{host} branch")] if branches is None else branches
    return derive(host, branches, current, main)[0]["Title"]


def test_content_rule_no_holder_one_holder_and_two_holders():
    origin = [copy("Origin")]
    assert derive(A, [], item(), main=origin)[0]["Title"] == f"{TID}: Origin"  # no holder: origin
    assert title(A, item(), origin) == f"{TID}: {A} branch"  # exactly one holder, this host: its own copy
    cur = item(facts_text(b=seg("progress")), Title=f"{TID}: B kept", Tier="standard")
    kept, _ = derive(A, [], cur, origin)  # exactly one holder, another host: keep the current value
    assert kept["Title"] == f"{TID}: B kept" and kept["Tier"] == "standard"
    created, _ = derive(A, [], None, origin)
    assert created["Title"] == f"{TID}: Origin"  # no current item: origin's copy
    two = item(facts_text(seg("progress"), seg("progress")), Title=f"{TID}: whatever")
    assert title(B, two, origin) == f"{TID}: Origin" and title(A, two, origin) == f"{TID}: Origin"  # origin has a copy: every host


def test_content_rule_two_holders_without_origin_only_the_lowest_host_tag_writes_its_copy():
    two = item(facts_text(seg("progress"), seg("progress")), Title=f"{TID}: current")
    assert title(A, two) == f"{TID}: {A} branch"
    assert title(B, two) == f"{TID}: current"


def test_a_plan_note_names_the_rule_when_two_hosts_hold_the_ticket():
    plan = plan_for(A, [fact(A)], [item(facts_text(b=seg("progress")))], main=[copy()])
    assert any("held by" in n and "origin's copy" in n for n in plan.notes)


def test_only_legacy_hosts_and_no_own_copy_keep_the_items_current_status():
    legacy = {"Branch": f"{A}:rpg-old"}
    assert derive(B, [], item("", Status="Stale", **legacy), main=[copy()])[0]["Status"] == "Stale"
    assert derive(B, [], item("", Status="Blocked", **legacy), main=[copy()])[0]["Status"] == "Blocked"
    assert derive(B, [], item("", Status="Stale", **legacy), main=[copy(folder="done")])[0]["Status"] == "Done"  # origin still wins
    own = derive(B, [fact(B)], item("", Status="Stale", **legacy), main=[copy()])[0]
    assert own["Status"] == "In progress"  # this host has a copy: the normal union applies
    real = item(facts_text(a=seg("progress", "rpg-implementer-u24")), Status="Blocked", Branch=f"{A}:rpg-old")
    assert derive(B, [], real, main=[copy()])[0]["Status"] == "In progress"  # the other host has a real segment: union, not the kept value
    mixed = item(facts_text(a=seg("progress", "rpg-implementer-u24")), Status="In progress", Branch=f"{A}:rpg-old, {B}:rpg-x")
    blocked_here = derive(B, [fact(B, blocked=True)], mixed, main=[copy()])[0]
    assert blocked_here["Status"] == "Blocked"  # this host's own segment: the normal union
    # Blocked set by this host is not copied into a legacy state: with this host's copy gone and a real u24 segment, it clears
    assert derive(B, [], item(facts_text(a=seg("progress")), Status="Blocked"), main=[copy()])[0]["Status"] == "In progress"


# ---- archive guard, legacy segments, hash

def test_archive_guard_keeps_an_item_that_carries_another_hosts_facts():
    held = item(facts_text(b=seg("progress")))
    plan = plan_for(A, [], [held])
    assert plan.archives == [] and any("not archived" in f and B in f for f in plan.findings)
    mine_only = item(facts_text(a=seg("progress")))
    assert plan_for(A, [], [mine_only]).archives == [(TID, "no ticket file for this ID")]


def test_a_legacy_other_host_branch_entry_counts_as_a_segment_and_keeps_seat_and_domain():
    legacy = item("", branch=f"{B}:rpg-old", Seat="rpg-implementer", Domain="rpg", Host=B)
    derived, _ = derive(A, [fact(A)], legacy)
    assert derived["Status"] == "In progress" and "rpg-implementer" in derived["Seat"] and "rpg-implementer-u24" in derived["Seat"]
    assert derived["Host facts"] == facts_text(seg("progress", "rpg-implementer-u24"))  # a legacy segment is never written
    assert plan_for(A, [], [legacy]).archives == []
    filing_only = item("", branch=f"{B}:rpg-old [filing]")
    assert derive(A, [], filing_only, main=[copy()])[0]["Status"] == "To do"


def test_hash_v3_a_v2_item_with_no_host_facts_is_a_hash_only_update_and_a_segment_is_a_real_change():
    c = [copy()]
    derived, _ = derive(A, [], None, c)
    v2_fields = {k: v for k, v in derived.items() if k in ps.HASH_FIELDS_V2}
    live = {**v2_fields, "Sync hash": ps.sync_hash(v2_fields, "v2"), "_item_id": "I", "_draft_id": "D"}
    plan = plan_for(A, [], [live], main=c)
    assert plan.hand_edits == [] and [ch for _, ch in plan.updates] == [["Sync hash"]]
    assert plan.updates[0][0]["Sync hash"].startswith("v3:")
    with_branch = plan_for(A, [fact(A)], [live], main=c)
    assert with_branch.hand_edits == [] and "Host facts" in with_branch.updates[0][1]


def test_a_change_to_host_facts_alone_makes_an_update():
    derived, _ = derive(A, [fact(A)], None, [copy()])
    stale = {k: v for k, v in derived.items() if k != "Host facts"}
    live = {**stale, "Host facts": "", "_item_id": "I", "_draft_id": "D"}
    live["Sync hash"] = ps.sync_hash(live)
    plan = plan_for(A, [fact(A)], [live], main=[copy()])
    assert plan.hand_edits == [] and [ch for _, ch in plan.updates] == [["Host facts"]]


# ---- convergence

def settle(items, plan):
    by_id = {i["Ticket ID"]: i for i in items}
    for derived in plan.creates:
        by_id[derived["Ticket ID"]] = {**derived, "_item_id": f"N-{derived['Ticket ID']}", "_draft_id": "D"}
    for derived, _ in plan.updates:
        by_id[derived["Ticket ID"]] = derived
    for tid, _ in plan.archives:
        by_id.pop(tid, None)
    return list(by_id.values())


def run_hosts(order, branches, main, items=()):
    items, plans = list(items), []
    for host in order:
        plan = plan_for(host, branches[host], items, main)
        plans.append(plan)
        items = settle(items, plan)
    return plans, items


def test_convergence_one_holder_per_ticket_a_then_b_then_a_leaves_an_empty_third_plan():
    t2 = "TCK-20261114-OTHER"
    main = [copy(), copy(tid=t2)]
    index_main = {TID: [copy()], t2: [copy(tid=t2)]}

    def plan_multi(host, branches, items):
        index = {t: [(c.folder, c.path) for c in cs] for t, cs in index_main.items()}
        loaded = {c.path: c for cs in index_main.values() for c in cs}
        return ps.build_plan(index, lambda p: loaded[p], list(branches), [], list(items), host, "s", CFG, lambda p: None, NOW)

    branches = {A: [fact(A)], B: [fact(B, tid=t2)]}
    items, plans = [], []
    for host in (A, B, A):
        plan = plan_multi(host, branches[host], items)
        plans.append(plan)
        items = settle(items, plan)
    assert main and plans[0].creates and plans[1].creates
    assert plans[2].updates == [] and plans[2].archives == [] and plans[2].creates == []


def test_convergence_two_holders_with_an_origin_copy_a_b_a_b_leaves_an_empty_fourth_plan():
    plans, items = run_hosts((A, B, A, B), {A: [fact(A, "A title")], B: [fact(B, "B title")]}, [copy("Origin")])
    assert plans[3].updates == [] and plans[3].archives == [] and plans[3].creates == []
    assert items[0]["Title"] == f"{TID}: Origin" and set(ps.parse_host_facts(items[0]["Host facts"])) == {A, B}


def test_convergence_two_holders_without_origin_a_b_a_b_empty_fourth_plan_and_the_lowest_tag_title_wins():
    plans, items = run_hosts((A, B, A, B), {A: [fact(A, "A title")], B: [fact(B, "B title")]}, [])
    assert plans[3].updates == [] and plans[3].archives == [] and plans[3].creates == []
    assert items[0]["Title"] == f"{TID}: A title"


def test_convergence_m7c_both_segments_already_present_different_titles_no_origin_a_b_a():
    start = item(facts_text(seg("progress", "rpg-implementer-u24"), seg("progress", "rpg-implementer")), Title=f"{TID}: B title",
                 Status="In progress", Host=f"{A}, {B}", Branch=f"{B}:rpg-{B}, {A}:rpg-{A}")
    branches = {A: [fact(A, "A title")], B: [fact(B, "B title")]}
    plans, items = run_hosts((A, B, A), branches, [], [start])
    assert plans[2].updates == [] and plans[2].archives == []
    written = [d["Title"] for p in plans for d, ch in p.updates if "Title" in ch]
    assert written == [f"{TID}: A title"]  # only the lowest tag's Title is ever written
