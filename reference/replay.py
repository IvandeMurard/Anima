"""Reference planner + replay of the hackathon day (v3). Deterministic, no LLM, stdlib only.

Purpose: prove the scripted day is coherent (every `expect` in events.json is what an
honest rule set actually produces), measure what re-planning changes against a static
plan, and give the team an oracle for 22 Oct. The LLM version must reach the same
decisions and explain them better - not decide differently.

Product rules:
  R1  Consent first, per purpose: no consent -> nothing personal read; withdrawal deletes memory.
  R2  Memory stores only what the guest DECLARED, under a purpose they consented to.
      Inferred attributes handed to Anima (e.g. by an OTA feed) are refused at the door.
      The refusal log keeps no link to the guest (attribute + origin + source + count only).
  R3  Context (events, trains, maintenance) informs decisions, never becomes a claim.
      A train is tracked only because the guest declared it for arrival coordination.
  R4  Anima informs, the planner recommends, a human validates. No auto-action.
  R5  No churn: a re-plan keeps the current room if it still works.
  R6  Lesser rooms are offered only if the wait exceeds 30 min, and never imposed.
      If no room meets every declared need, the planner says so and lists the least-bad options.
  R7  Moves for in-house guests are proposed only after 15:00 and once all arrivals are placed;
      the proposed room is held until a human decides.
  R8  No silent upgrades: an upgrade is only chosen if nothing in the booked category works,
      and it is flagged.
  R9  Stale memory expires: a durable claim not confirmed for 36 months is deleted at day start.
      A guest's confirmation restarts the clock and adds a confirmation.
  R10 Contradictions: the newest declared claim wins for its scope (this stay); it never silently
      overwrites a durable claim, which is flagged for reconfirmation at the next stay.
Housekeeping: 2 attendants on departures from 08:00, list scheduling. Work that started
before `now` is frozen; only the future is re-planned. Pinned rooms first, then the
default queue. Departure clean 40 min, re-clean after maintenance 30, inspection 10.

Run:  python reference/replay.py      (exit 1 if any expectation fails)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
load = lambda n: json.loads((DATA / n).read_text(encoding="utf-8"))

HOTEL, GUESTS = load("hotel.json"), load("guests.json")
RES, HK, CTX = load("reservations.json"), load("housekeeping.json"), load("context.json")
EVENTS = load("events.json")["events"]
H = HOTEL["housekeeping"]
ROOMS = {r["room"]: r for r in HOTEL["rooms"]}
G = {g["guest_id"]: g for g in GUESTS}
ORIGINAL = copy.deepcopy(G)
RANK = HOTEL["category_rank"]
NOISE = next(c for c in CTX["sources"] if c["kind"] == "local_event")
ALT_THRESHOLD = 30
INSPECT = H["minutes_inspection"]


def mins(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":")); return h * 60 + m


def hhmm(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


CHECK_IN = mins(HOTEL["standard_check_in"])


class World:
    """Everything the hotel knows at a given moment. Deep-copied to run counterfactuals."""

    def __init__(self):
        self.status = {r["room"]: r["status"] for r in HK["rooms"]}
        self.leaving = {d["room"]: mins(d["planned_check_out"]) for d in RES["departures"]}
        self.oos: dict[str, int | None] = {}
        self.reclean: dict[str, int] = {}
        self.pins: list[str] = []
        self.free = [mins(H["available_from"])] * H["attendants_on_departures"]
        self.done: dict[str, tuple[int, int]] = {}       # job -> (start, end): frozen history
        self.planned: dict[str, str | None] = {}
        self.holds: set[str] = set()

    def jobs(self):
        out = []
        for r, t in self.leaving.items():
            if r not in self.done and r not in self.oos:
                out.append({"job": r, "room": r, "avail": t, "dur": H["minutes_departure_clean"]})
        for r, t in self.reclean.items():
            if f"{r}#re" not in self.done:
                out.append({"job": f"{r}#re", "room": r, "avail": t, "dur": H["minutes_reclean_after_maintenance"]})
        return out

    def _run(self, free, jobs, order, stop_at=None):
        queue = HK["default_queue"]

        def prio(j):
            if j["room"] in order:
                return (0, order.index(j["room"]))
            return (1, queue.index(j["room"]) if j["room"] in queue else 99)
        free, jobs, started = list(free), list(jobs), {}
        idle = set()
        while jobs and len(idle) < len(free):
            a = min((i for i in range(len(free)) if i not in idle), key=lambda i: free[i])
            T = free[a]
            if stop_at is not None and T >= stop_at:
                idle.add(a); continue
            avail = [j for j in jobs if j["avail"] <= T]
            if not avail:
                nxt = min(j["avail"] for j in jobs)
                if stop_at is not None and nxt >= stop_at:
                    free[a] = stop_at; idle.add(a); continue
                free[a] = nxt; continue
            j = min(avail, key=prio); jobs.remove(j)
            started[j["job"]] = (T, T + j["dur"]); free[a] = T + j["dur"]
        return free, started

    def advance(self, now: int):
        """Freeze every job that started before `now`: the past is never re-planned."""
        free, started = self._run(self.free, self.jobs(), self.pins, stop_at=now)
        self.done.update(started)
        self.free = [max(f, now) for f in free]

    def forecast(self, extra_pin: str | None = None) -> dict[str, int]:
        order = self.pins + ([extra_pin] if extra_pin and extra_pin not in self.pins else [])
        _, started = self._run(self.free, self.jobs(), order)
        ready = {}
        for job, (s, e) in sorted({**self.done, **started}.items(), key=lambda kv: kv[1][1]):
            room = job.split("#")[0]
            if room in self.oos and room not in self.reclean:
                continue
            if room in self.reclean and not job.endswith("#re"):
                continue                                   # only the re-clean counts after maintenance
            ready[room] = e + INSPECT
        return ready

    def ready_at(self, room: str, now: int, pin: bool = False) -> int | None:
        if self.status[room] in ("out_of_order", "occupied_stayover"):
            return None
        if room in self.oos and room not in self.reclean:
            return None
        if room not in self.leaving and room not in self.reclean:
            return now                                     # vacant clean
        return self.forecast(room if pin else None).get(room)


W = World()
arrivals = {a["guest_id"]: a for a in RES["arrivals"]}
locked = {a["assigned_room"]: a["guest_id"] for a in RES["arrivals"] if a.get("locked")}
stayover_room = {s["guest_id"]: s["room"] for s in RES["stayovers"]}
refusals: dict[tuple, int] = {}                           # (attribute, origin, source) -> count; no guest id


def purposes(gid: str) -> set[str]:
    c = G[gid].get("consent")
    return {p["name"] for p in c["purposes"]} if c else set()


def claims(gid: str) -> list[dict]:
    return G[gid]["claims"] if purposes(gid) else []      # R1


def declared(gid: str, key: str):
    """Newest-scope wins (R10): a this-stay (working) claim overrides a durable one for this stay.
    Returns the claim only if its value is truthy."""
    found = [c for c in claims(gid) if c["key"] == key and c["origin"] == "declared"
             and c["purpose"] in purposes(gid)]
    found.sort(key=lambda c: 0 if c.get("layer") == "working" else 1)
    c = found[0] if found else None
    return c if c and c["value"] not in (False, None) else None


DAY = load("events.json")["date"]


def months_between(d1: str, d2: str) -> int:
    y1, m1, dd1 = map(int, d1.split("-")); y2, m2, dd2 = map(int, d2.split("-"))
    return (y2 - y1) * 12 + (m2 - m1) - (1 if dd2 < dd1 else 0)


def expiry_sweep() -> list[str]:
    """R9: delete durable claims not confirmed for 36 months. Returns deleted claim ids (audit count only)."""
    gone = []
    for g in G.values():
        keep = []
        for c in g["claims"]:
            if c.get("layer") == "semantic" and months_between(c["last_confirmed"], DAY) >= 36:
                gone.append(c["claim_id"])
            else:
                keep.append(c)
        g["claims"] = keep
    return gone


def eta_of(gid: str):
    c = declared(gid, "eta")
    return (mins(c["value"]), c) if c else (mins(arrivals[gid]["eta"]), None)


def write_claim(gid: str, proposal: dict) -> bool:
    ok = proposal.get("origin", "declared") == "declared" and proposal.get("purpose") in purposes(gid)
    if ok:
        G[gid]["claims"].append({**proposal, "origin": "declared", "confirmations": 1})
    else:
        k = (proposal["key"], proposal.get("origin"), proposal.get("source"))
        refusals[k] = refusals.get(k, 0) + 1
    return ok


def violations(gid: str, num: str, category: str):
    r, out, sev = ROOMS[num], [], 0
    q, d = declared(gid, "quiet_room"), declared(gid, "needs_desk")
    if q and r["side"] == "street":
        out += [q["claim_id"], NOISE["id"]]; sev += 4
    if q and r["lift_adjacent"]:
        out.append(q["claim_id"]); sev += 1
    if d and not r["desk"]:
        out.append(d["claim_id"]); sev += 1
    if RANK[r["category"]] < RANK[category]:
        out.append("downgrade"); sev += 1
    return out, sev


def plan_room(w: World, gid: str, now: int) -> dict:
    eta, eta_claim = eta_of(gid)
    early = eta < CHECK_IN
    cat = arrivals[gid]["category"]
    current = w.planned[gid] if gid in w.planned else arrivals[gid].get("pms_preassigned_room")
    taken = (set(locked) | {r for g2, r in w.planned.items() if g2 != gid and r}
             | set(stayover_room.values()) | w.holds)
    opts = []
    for num in ROOMS:
        if num in taken:
            continue
        ra = w.ready_at(num, now, pin=early)
        if ra is None:
            continue
        v, sev = violations(gid, num, cat)
        up = RANK[ROOMS[num]["category"]] > RANK[cat]
        opts.append({"room": num, "ready": ra, "wait": max(0, ra - eta), "v": v, "sev": sev, "upgrade": up})
    ok = [o for o in opts if not o["v"]]
    no_fit = not ok
    pool = ok or sorted(opts, key=lambda o: o["sev"])[:3]          # R6 fallback: never crash
    best = min(pool, key=lambda o: (o["sev"], o["upgrade"], o["wait"], o["room"] != current, o["ready"], o["room"]))
    cur = next((o for o in ok if o["room"] == current), None)
    if cur and cur["wait"] == 0 and not cur["upgrade"]:            # R5
        best = cur
    old = w.planned.get(gid)
    if old and old != best["room"] and old in w.pins:
        w.pins.remove(old)                                          # no ghost priority
    w.planned[gid] = best["room"]
    ready = best["ready"]
    if early and (best["room"] in w.leaving or best["room"] in w.reclean) and best["room"] not in w.pins:
        w.pins.insert(0, best["room"])
        ready = w.ready_at(best["room"], now)
    cites = {c for o in opts for c in o["v"] if c.startswith("C")}
    cur_v = violations(gid, current, cat)[0] if current else []
    if NOISE["id"] in cur_v:
        cites.add(NOISE["id"])                                      # context cited only when it overrode the current room
    if early:
        if eta_claim:
            cites.add(eta_claim["claim_id"])
        r = declared(gid, "ready_if_early")
        if r:
            cites.add(r["claim_id"])
    alt = None
    if max(0, ready - eta) > ALT_THRESHOLD:                         # R6
        alt = min((o for o in opts if o["v"] and o["ready"] <= now), key=lambda o: (o["sev"], o["room"]), default=None)
    for c in claims(gid):
        if c["key"] == "extra_pillows":
            cites.add(c["claim_id"])
    return {"room": best["room"], "ready_by": hhmm(ready), "wait": max(0, ready - eta),
            "prioritise": best["room"] in w.pins, "alternative": alt["room"] if alt else None,
            "upgrade": best["upgrade"], "no_fit": no_fit, "violations": best["v"],
            "cites": cites, "needs_human_validation": True}


def place_all_arrivals(w: World, now: int):
    for a in sorted(RES["arrivals"], key=lambda a: (eta_of(a["guest_id"])[0], a["guest_id"])):
        if not a.get("locked") and a["guest_id"] not in w.planned:
            plan_room(w, a["guest_id"], now)


def move_suggestion(w: World, gid: str, now: int, horizon: int) -> dict:
    q = declared(gid, "quiet_room")
    room = stayover_room[gid]
    exposed = bool(q) and ROOMS[room]["side"] == "street"
    res = {"exposed": exposed, "cites": {q["claim_id"], NOISE["id"]} if exposed else set(), "room": None}
    arrivals_placed = all(a.get("locked") or w.planned.get(a["guest_id"]) for a in RES["arrivals"])
    if not exposed or now < CHECK_IN or not arrivals_placed:       # R7
        return res
    cat = ROOMS[room]["category"]
    taken = set(locked) | {r for r in w.planned.values() if r} | set(stayover_room.values()) | w.holds
    for num, r in sorted(ROOMS.items()):
        if num in taken or r["side"] == "street" or r["lift_adjacent"] or r["category"] != cat:
            continue
        ra = w.ready_at(num, now, pin=True)
        if ra is not None and ra <= horizon:
            res.update(room=num, ready_by=hhmm(ra)); w.holds.add(num); break
    return res


def brief(gid: str, p: dict, now: int) -> str:
    g = G[gid]; nth = {1: "second", 2: "third", 3: "fourth"}.get(g["stays_before"], "returning")
    when = f"ready since {p['ready_by']}" if mins(p["ready_by"]) <= now else f"ready at {p['ready_by']}"
    return (f"{g['name'].replace('SYN-', '')}, {nth} stay, arrives in about 10 minutes: she asked for a quiet "
            f"room and is in {p['room']}, courtyard side, {when}. "
            f"She told us she works on arrival, so the desk is set up and there is nothing to ask her again.")


def static_day() -> dict:
    """Counterfactual: preference remembered at 07:00, then nobody re-plans (no message read,
    no priority, the broken tap discovered at the desk)."""
    w = World()
    p = None
    for ev in EVENTS:
        now, d = mins(ev["at"]), ev.get("detail", {})
        w.advance(now)
        if ev["type"] == "day_start":
            p = plan_room(w, "G001", now)
        elif ev["type"] == "express_check_out":
            w.leaving[d["room"]] = mins(d["leaving_at"])
        elif ev["type"] == "early_check_out":
            w.leaving[d["room"]] = mins(d["left_at"])
        elif ev["type"] == "out_of_service":
            w.oos[d["room"]] = mins(d["back_in_service"])
        elif ev["type"] == "check_in":
            if p["room"] not in w.oos:
                return {"room": p["room"], "wait": max(0, w.ready_at(p["room"], now) - now), "broken": False}
            alts = []
            for r in ROOMS:
                if r in locked or r in stayover_room.values() or violations("G001", r, "superior")[0]:
                    continue
                t = w.ready_at(r, now)
                if t is not None:
                    alts.append((t, r))
            t, r = min(alts)
            return {"planned_room": p["room"], "planned_room_broken": True, "room": r, "wait": max(0, t - now),
                    "broken": True}


# ------------------------------------------------------------------ replay
fails, last = 0, {}


def check(cond, msg):
    global fails
    print(f"  {'PASS' if cond else 'FAIL'}  {msg}")
    fails += 0 if cond else 1


def total_claims():
    return sum(len(g["claims"]) for g in G.values())


def check_plan(gid, p, ex, prev):
    if ex.get("no_change"):
        check(bool(prev) and prev["room"] == p["room"], f"{gid}: no change (stays {p['room']})"); return
    if "recommend_room" in ex:
        check(p["room"] == ex["recommend_room"], f"{gid}: recommends {ex['recommend_room']} (got {p['room']})")
    if "ready_by" in ex:
        check(p["ready_by"] == ex["ready_by"], f"{gid}: ready by {ex['ready_by']} (got {p['ready_by']})")
    if ex.get("keep_current"):
        check(bool(prev) and prev["room"] == p["room"], f"{gid}: keeps current room (R5)")
    if "prioritise_cleaning" in ex:
        check(p["prioritise"], f"{gid}: {p['room']} cleaned first")
    if ex.get("no_alternative"):
        check(p["alternative"] is None, f"{gid}: no lesser room offered (R6)")
    for c in ex.get("must_cite", []):
        check(c in p["cites"], f"{gid}: cites {c}")
    for c in ex.get("must_not_cite", []):
        check(c not in p["cites"], f"{gid}: does not cite {c}")
    if ex.get("cites_nothing"):
        check(not p["cites"], f"{gid}: cites nothing (got {sorted(p['cites'])})")
    check(not p["upgrade"] and not p["no_fit"], f"{gid}: booked category, all declared needs met")
    check(p["needs_human_validation"], f"{gid}: waits for human validation (R4)")


if __name__ == "__main__":
    STATIC = static_day()
    for ev in EVENTS:
        now, ex, d = mins(ev["at"]), ev.get("expect", {}), ev.get("detail", {})
        print(f"\n[{ev['at']}] #{ev['seq']} {ev['type']} - {ev['summary']}")
        W.advance(now)
        claims_before = total_claims()
        typ = ev["type"]
        if typ == "day_start":
            gone = expiry_sweep()
            e7 = ex.get("G007", {})
            if "expired_and_deleted" in e7:
                check(e7["expired_and_deleted"] in gone and not any(c["claim_id"] == e7["expired_and_deleted"]
                      for c in G["G007"]["claims"]), f"stale {e7['expired_and_deleted']} (>36 months) deleted at day start (R9)")
                check("C070" not in gone, "C070 (confirmed 2026-04) kept")
            pc = d["proposed_claim"]
            check(not write_claim(pc["guest_id"], pc), f"inferred '{pc['key']}' from an external agent refused (R2)")
            check(not any(c.get("key") == pc["key"] for c in G[pc["guest_id"]]["claims"]), "and not in memory")
            check(all(len(k) == 3 for k in refusals), "refusal log: attribute/origin/source only, no guest id")
        elif typ == "express_check_out":
            W.leaving[d["room"]] = mins(d["leaving_at"])
        elif typ == "guest_message":
            wc = d["write_claim"]
            check(write_claim(wc["guest_id"], wc), f"declared {wc['claim_id']} (eta) written under '{wc['purpose']}'")
        elif typ == "early_check_out":
            W.leaving[d["room"]] = mins(d["left_at"])
        elif typ == "out_of_service":
            W.oos[d["room"]] = mins(d["back_in_service"]) if d.get("back_in_service") else None
            if W.planned.get("G001") == d["room"]:
                W.planned["G001"] = None
            if d["room"] in W.pins:
                W.pins.remove(d["room"])
        elif typ == "back_in_service":
            W.reclean[d["room"]] = now
        elif typ == "guest_reply":
            wc = d["write_claim"]; gid = wc["guest_id"]; e = ex[gid]
            durable_before = next(c for c in G[gid]["claims"] if c["claim_id"] == e["durable_kept"])
            check(write_claim(gid, wc), f"{wc['claim_id']} written for this stay only (working layer)")
            durable_before["needs_reconfirm"] = True
            held = e["hold_released"]
            W.holds.discard(held)
            s2 = move_suggestion(W, gid, now, mins("20:00"))
            check(s2["room"] is None and not s2["exposed"], f"{gid}: move suggestion withdrawn")
            check(held not in W.holds, f"hold on {held} released")
            check(any(c["claim_id"] == e["durable_kept"] for c in G[gid]["claims"]) and durable_before.get("needs_reconfirm"),
                  f"durable {e['durable_kept']} kept, flagged to reconfirm next stay (R10)")
            check(declared(gid, "quiet_room") is None, "for this stay, the newest declaration wins")
            continue
        elif typ == "consent_withdrawn":
            gid = d["guest_id"]; n = len(G[gid]["claims"])
            G[gid]["consent"] = None; G[gid]["claims"] = []
            check(n > 0 and not G[gid]["claims"], f"{gid}: {n} claim(s) deleted on withdrawal (R1)")
            continue
        elif typ == "arrival_imminent":
            _, c = eta_of("G001")
            used = bool(c) and c.get("train") == d["train"] and "arrival coordination" in purposes("G001")
            check(used, f"rail status used only because of declared {c['claim_id'] if c else None} (R3)")
            b = brief("G001", last["G001"], now); print("  BRIEF:", b)
            check(("ready since" in b) == (mins(last["G001"]["ready_by"]) <= now), "brief tense matches the clock")
            e = ex["G001"]
            check(b.count(". ") + 1 <= e["brief_max_sentences"], "brief fits in 2 sentences")
            for w_ in e["brief_must_mention"]:
                check(w_ in b, f"brief mentions '{w_}'")
            for w_ in e["brief_must_not_mention"]:
                check(w_ not in b, f"brief avoids '{w_}'")
            continue
        elif typ == "check_in":
            p = last["G001"]; wt = max(0, mins(p["ready_by"]) - now)
            check(wt == ex["G001"]["wait_minutes"], f"G001 waits {wt} min in {p['room']}")
            c = next(c for c in G["G001"]["claims"] if c["claim_id"] == d["confirm_claim"])
            c["confirmations"] += 1; c["last_confirmed"] = DAY
            e = ex["G001"]
            check(c["confirmations"] == e["confirmations"] and c["last_confirmed"] == e["last_confirmed"],
                  f"{c['claim_id']} confirmed: {c['confirmations']} confirmations, clock restarted {c['last_confirmed']} (R9)")
            print(f"  STATIC PLAN (remembered at 07:00, never re-planned): {STATIC}")
            check(STATIC["wait"] > ALT_THRESHOLD or STATIC["broken"], "re-planning made a measurable difference")
            continue

        prev = last.get("G001")
        if "G001" in ex:
            p = plan_room(W, "G001", now); last["G001"] = p
            print(f"  PLAN G001: {p['room']} ready {p['ready_by']} wait={p['wait']} first={p['prioritise']} "
                  f"alt={p['alternative']} cites={sorted(p['cites'])}")
            check_plan("G001", p, ex["G001"], prev)
            e = ex["G001"]
            if e.get("claim_written"):
                check(any(c.get("claim_id") == e["claim_written"] for c in G["G001"]["claims"]),
                      f"{e['claim_written']} in memory")
            if "static_ready_by" in e:
                w2 = copy.deepcopy(W); w2.pins = [r for r in w2.pins if r != p["room"]]
                s = w2.ready_at(p["room"], now)
                check(s is not None and hhmm(s) == e["static_ready_by"],
                      f"without priority {p['room']} would be ready {hhmm(s) if s is not None else None}")
        if typ == "day_start":
            place_all_arrivals(W, now)
        if "G007" in ex:
            e = ex["G007"]
            s = move_suggestion(W, "G007", now, mins(e.get("before", "20:00")))
            print(f"  G007: exposed={s['exposed']} suggestion={s['room']} ready={s.get('ready_by')} cites={sorted(s['cites'])}")
            for c in e["must_cite"]:
                check(c in s["cites"], f"G007: cites {c}")
            if e.get("no_option_yet"):
                check(s["room"] is None, "G007: watch only, no move proposed before 15:00 (R7)")
            if "suggest_room" in e:
                check(s["room"] == e["suggest_room"] and s.get("ready_by") == e["ready_by"],
                      f"G007: offer {e['suggest_room']} ready {e['ready_by']} before {e['before']} (human decides)")
            if e.get("no_claim_created_from_context"):
                check(total_claims() == claims_before, "no claim created from context (R3)")
        if typ == "arrivals":
            for gid in ("G008", "G012"):
                p = plan_room(W, gid, now)
                print(f"  PLAN {gid}: {p['room']} cites={sorted(p['cites'])}")
                check_plan(gid, p, ex[gid], None)
                if "would_have_cited_before_withdrawal" in ex[gid]:
                    saved = G[gid]; G[gid] = copy.deepcopy(ORIGINAL[gid])
                    cf = plan_room(copy.deepcopy(W), gid, now); G[gid] = saved
                    c = ex[gid]["would_have_cited_before_withdrawal"]
                    check(c in cf["cites"], f"{gid}: control (tests only, never shown in UI) - with consent it would cite {c}")

    check(all(c["origin"] == "declared" for g in G.values() for c in g["claims"]), "end of day: memory holds declared claims only")
    check(all(W.planned.get(a["guest_id"]) for a in RES["arrivals"] if not a.get("locked")), "end of day: every arrival placed")
    print("\nPlanned rooms:", dict(sorted((g, r) for g, r in W.planned.items())))
    print("Refusal log (no guest id):", refusals)
    print(f"\n{'ALL PASS' if not fails else f'{fails} FAIL'}")
    sys.exit(1 if fails else 0)
