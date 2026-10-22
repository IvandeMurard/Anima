"""Anima live mode ("Try it"): a judge plays the guest, housekeeping or an outside AI agent, and
the front desk. Same agent loop as the guided tour, but on inputs nobody scripted:

  free text --Claude (agent/parser.py)--> proposed event + claims --write rule--> Valkey / Postgres
  --> memory read back FROM the stores --> planner tool (reference/replay.py) --> card + data ledger
  --> anticipations ("ask, don't assume") --> a human validates (decisions.validated_by)

Every view says what data was used, what was refused, what was forgotten, and what each tool
receives. Anticipations are never stored: they become memory only if the guest says yes.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

import run_demo as RD

CLAIRE = "G001"
CONTACT = {"G001": "+33 6 00 00 00 01 (SYN)"}
PURPOSE_OF = {"eta": "arrival coordination"}                  # everything else: stay personalisation
PLANNER_KEYS = {"quiet_room", "needs_desk", "eta", "ready_if_early", "extra_pillows"}

S = {"now": None, "seq": 100, "chat": [], "last": None, "decision_id": None, "anticipations": [],
     "log": [], "llm_calls": 0, "llm_ms": [], "pos_antic": [], "seen": {}}

# Every source gets a rule: what the guest says, we remember; what the hotel sees, we use; what we could guess, we refuse, or we ask.
SOURCES = [
    {"id": "whatsapp", "source": "Guest WhatsApp", "kind": "declared by the guest", "rule": "remember, with consent and an expiry"},
    {"id": "ota", "source": "OTA booking request (Booking.com)", "kind": "declared by the guest", "rule": "remember, with consent and an expiry"},
    {"id": "pms", "source": "PMS webhooks", "kind": "hotel operations", "rule": "use to plan, never stored about the guest"},
    {"id": "housekeeping", "source": "Housekeeping / maintenance", "kind": "live context", "rule": "use to plan, never stored about the guest"},
    {"id": "context", "source": "Rail status, local events", "kind": "live context", "rule": "use to plan; a train only if the guest declared it"},
    {"id": "pos", "source": "POS (bar, restaurant)", "kind": "behaviour", "rule": "never remembered; may only become a question"},
    {"id": "outside", "source": "Outside AI agents, reviews", "kind": "guess", "rule": "refused at the door, no guest id kept"},
]


def seen(source_id: str):
    S["seen"][source_id] = S["seen"].get(source_id, 0) + 1


def O():
    return RD.O


def hh(m: int) -> str:
    return O().hhmm(m)


def normalise_key(key: str) -> str:
    k = key.lower()
    if "quiet" in k or "noise" in k:
        return "quiet_room"
    if "desk" in k or "work" in k:
        return "needs_desk"
    if k in ("eta", "arrival", "arrival_time") or "eta" in k:
        return "eta"
    if "pillow" in k:
        return "extra_pillows"
    if "early" in k and "ready" in k:
        return "ready_if_early"
    return k


def log(kind: str, text: str):
    S["log"].append({"at": hh(S["now"]), "kind": kind, "text": text})


# ------------------------------------------------------------------ start / reset
def start(pg, vk):
    """New live day at 07:00: fresh world, seeded stores, morning sweep, first plan."""
    RD.O = RD.load_oracle()
    RD.reset(pg, vk)
    S.update(now=O().mins("07:00"), seq=100, chat=[], last=None, decision_id=None, anticipations=[], log=[],
             llm_calls=0, llm_ms=[], pos_antic=[], seen={})
    seen("outside"); seen("pms")
    W = O().W
    W.advance(S["now"])
    day_start = O().EVENTS[0]["detail"]["proposed_claim"]          # the traveller-side agent's guess
    with pg.cursor() as c:
        c.execute("DELETE FROM claims WHERE expires_at <= %s RETURNING claim_id", (RD.DAY,))
        S["expired"] = len(c.fetchall())
    pg.commit()
    refuse(pg, day_start["key"], day_start["origin"], day_start["source"])
    log("forget", f"{S['expired']} memory deleted: not confirmed for 36 months (content not kept)")
    RD.load_memory(pg, vk)
    O().place_all_arrivals(W, S["now"])
    S["chat"].append({"who": "system", "text": "Simulated WhatsApp with Maison Lumen (synthetic guest SYN-Claire Laurent). "
                      "Don't enter real personal data."})
    replan(pg, vk, "Day opens: PMS put Claire in 402 (street side)")
    set_time("08:30")                       # the morning has started: the PMS feed has already flowed in
    return replan(pg, vk, "08:30: Claire arrives today at 15:00 (booking)")


def send_draft(pg, vk, index: int):
    """Staff approve a reply Anima drafted: only then does the guest receive it."""
    if 0 <= index < len(S["chat"]) and S["chat"][index].get("draft"):
        S["chat"][index]["draft"] = False
        S["chat"][index]["sent"] = True
        log("human", f"front desk sent the drafted reply to Claire: “{S['chat'][index]['text'][:60]}…”")
    return state(pg, vk)


def refuse(pg, attribute, origin, source):
    with pg.cursor() as c:
        c.execute("""INSERT INTO refusals VALUES (%s,%s,%s,%s,1)
                     ON CONFLICT (day,attribute,origin,source) DO UPDATE SET count = refusals.count + 1""",
                  (RD.DAY, attribute, origin, source))
    pg.commit()
    log("refuse", f"refused '{attribute}' ({origin}, from {source}): not declared by the guest; logged without guest id")


PMS_FEED = ("express_check_out", "early_check_out")                 # keeps flowing while the judge plays


def set_time(hhmm: str | None):
    """Move the clock forward; the PMS webhooks of the day (check-outs) arrive on their own on the way."""
    if not hhmm:
        return
    t, W = O().mins(hhmm), O().W
    if t <= S["now"]:
        return
    for ev in O().EVENTS:
        at_ev = O().mins(ev["at"])
        if ev["type"] in PMS_FEED and S["now"] < at_ev <= t:
            W.advance(at_ev)
            d = ev["detail"]
            W.leaving[d["room"]] = O().mins(d.get("leaving_at") or d.get("left_at"))
            S["now"] = at_ev
            log("context", f"PMS webhook {ev['at']}: room {d['room']} leaving at {hh(W.leaving[d['room']])}")
            seen("pms")
    S["now"] = t
    W.advance(t)


# ------------------------------------------------------------------ inputs
def context_for_parser() -> dict:
    guests = []
    for gid, g in O().G.items():
        entry = {"guest_id": gid, "name": g["name"]}
        if gid in CONTACT:
            entry["contact"] = CONTACT[gid]
        if g["claims"]:
            entry["claims"] = [{"key": c["key"], "value": c["value"], "layer": c.get("layer"),
                                "statement": c["statement"]} for c in g["claims"]]
        guests.append(entry)
    return {"date": RD.DAY, "guest_directory": guests, "open_offers": []}


def call_parser(channel: str, sender: str | None, text: str) -> dict:
    sys.path.insert(0, str(RD.ROOT))
    from agent.parser import parse_llm
    item = {"channel": channel, "format": "text", "lang": "en", "from": sender, "payload": text}
    t0 = datetime.now()
    ev = parse_llm(item, context_for_parser())
    S["llm_calls"] += 1; S["llm_ms"].append(int((datetime.now() - t0).total_seconds() * 1000))
    return ev


def guest_message(pg, vk, text: str, at: str | None = None, ota: bool = False):
    if ota:     # OTA emails are masked: the request is matched through the reservation, not the guest's contact
        ev = call_parser("Booking.com reservation, special request field",
                         "OTA reservation R-G001 for SYN-Claire Laurent (guest email masked by the OTA)", text)
        seen("ota")
    else:
        ev = call_parser("WhatsApp (guest)", CONTACT[CLAIRE], text)   # a failed read changes nothing
        seen("whatsapp")
    set_time(at)
    if ota:
        S["chat"].append({"who": "system", "text": f"Booking.com special request: “{text}”", "parsed": ev})
    else:
        S["chat"].append({"who": "guest", "text": text, "at": hh(S["now"]), "parsed": ev})
    S["channel"] = "the Booking.com request" if ota else "WhatsApp"
    gid = ev.get("resolved_guest_id") or CLAIRE
    written, confirmed = [], []
    if ev["type"] == "guest_message":
        keys = list(ev.get("claims_to_write") or [])
        if ev.get("eta") and "eta" not in keys:
            keys.append("eta")
        for raw_key in keys:
            key = normalise_key(raw_key)
            value = ev["eta"] if key == "eta" and ev.get("eta") else True
            if write_claim(pg, vk, gid, key, value, text):
                written.append(key)
        for raw_key in ev.get("already_known") or []:
            if confirm(pg, gid, normalise_key(raw_key)):
                confirmed.append(normalise_key(raw_key))
        if ev.get("fallback_offered_by_guest"):
            log("intent", f"guest offers a fallback: {ev['fallback_offered_by_guest']}")
    elif ev["type"] == "guest_reply":
        for c in ev.get("claims_to_write") or []:
            if write_claim(pg, vk, gid, normalise_key(c["key"]), c["value"], text):
                written.append(normalise_key(c["key"]))
    else:
        apply_operational(ev)
    extra = [k for k in written if k not in PLANNER_KEYS]
    if extra and S["pos_antic"]:
        S["pos_antic"] = []                                   # asked, answered: now declared, the question is closed
        log("ask", f"Claire said it herself: {', '.join(extra)} is now declared memory for this stay")
    RD.load_memory(pg, vk)
    who = "Booking.com request" if ota else "Claire wrote"
    view = replan(pg, vk, f"{who}: \"{text}\"", parsed=ev, written=written, confirmed=confirmed)
    if not ota:
        reply = ("Noted, we'll have that ready for you. Thanks Claire!" if extra and set(written) <= set(extra)
                 else draft_reply(view["card"]))
        S["chat"].append({"who": "hotel", "draft": True, "text": reply, "at": hh(S["now"])})
    return state(pg, vk)


def ota_request(pg, vk, text: str, at: str | None = None):
    return guest_message(pg, vk, text, at, ota=True)


def pos_receipt(pg, vk, text: str):
    """Behaviour seen at the bar or restaurant: never becomes memory. At most, a question for the guest."""
    seen("pos")
    refuse(pg, f"POS: {text[:50]}", "behavioural", "POS (bar)")
    a = {"need": f"Seen at the bar: {text}. Not remembered.", "from": ["POS"],
         "ask": f"We'd be happy to have {text.split('×')[0].split(' x')[0].strip()} ready for you tomorrow too, would you like that?"}
    S["pos_antic"] = [a]
    S["anticipations"] = [x for x in S["anticipations"] if x.get("from") != ["POS"]] + [a]
    return state(pg, vk)


def write_claim(pg, vk, gid, key, value, said) -> bool:
    """The write rule (R1, R2): declared by the guest, under a purpose they consented to, this stay only."""
    purpose = PURPOSE_OF.get(key, "stay personalisation")
    if not RD.consented(pg, gid, purpose):
        refuse(pg, key, "declared, no consent for this purpose", "WhatsApp")
        return False
    S["seq"] += 1
    cid = f"C{S['seq']}"                                     # the planner cites claim ids starting with C
    claim = {"claim_id": cid, "guest_id": gid, "key": key, "value": value,
             "statement": f"Said in {S.get('channel', 'WhatsApp')} at {hh(S['now'])}: “{said[:90]}”",
             "origin": "declared", "source": f"{S.get('channel', 'WhatsApp')}, this stay", "purpose": purpose, "layer": "working",
             "confirmations": 1}
    store = RD.write_working(vk, gid, claim)
    log("write", f"{cid} {key}={value} written to Valkey {store} (expires at check-out), purpose: {purpose}")
    return True


def confirm(pg, gid, key) -> bool:
    with pg.cursor() as c:
        c.execute("""UPDATE claims SET confirmations = confirmations + 1, last_confirmed = %s
                     WHERE guest_id=%s AND key=%s RETURNING claim_id, confirmations, expires_at""", (RD.DAY, gid, key))
        row = c.fetchone()
    pg.commit()
    if row:
        log("confirm", f"{row[0]} said again: confirmed {row[1]}×, now kept until {row[2]} (clock restarted)")
    return bool(row)


def apply_operational(ev: dict):
    W, t = O().W, ev.get("type")
    if t == "out_of_service":
        W.oos[ev["room"]] = O().mins(ev["back_in_service"]) if ev.get("back_in_service") else None
        if W.planned.get(CLAIRE) == ev["room"]:
            W.planned[CLAIRE] = None
        if ev["room"] in W.pins:
            W.pins.remove(ev["room"])
        log("context", f"room {ev['room']} out of service ({ev.get('reason') or 'no reason given'})")
    elif t == "back_in_service":
        W.reclean[ev["room"]] = S["now"]
        log("context", f"room {ev['room']} back in service, needs a re-clean")
    elif t in ("express_check_out", "early_check_out"):
        W.leaving[ev["room"]] = O().mins(ev.get("leaving_at") or ev.get("left_at") or hh(S["now"]))
        log("context", f"room {ev['room']} leaving at {hh(W.leaving[ev['room']])}")


def staff_report(pg, vk, text: str, at: str | None = None):
    ev = call_parser("housekeeping app (text message)", None, text)
    seen("housekeeping")
    set_time(at)
    apply_operational(ev)
    RD.load_memory(pg, vk)
    replan(pg, vk, f"Housekeeping: \"{text}\"", parsed=ev)
    return state(pg, vk)


def outside_agent(pg, vk, attribute: str):
    """An outside AI agent pushes something it inferred about Claire: refused at the door, always."""
    seen("outside")
    refuse(pg, attribute[:60], "inferred", "traveller-side AI agent")
    return state(pg, vk)


def validate(pg, vk):
    if S["decision_id"]:
        with pg.cursor() as c:
            c.execute("UPDATE decisions SET validated_by=%s, validated_at=now() WHERE id=%s RETURNING room",
                      ("front desk (demo)", S["decision_id"]))
            room = c.fetchone()[0]
        pg.commit()
        log("human", f"front desk validated room {room} (decision #{S['decision_id']}): only now is it pushed to the tools")
        S["last"]["validated"] = True
    return state(pg, vk)


def withdraw(pg, vk, gid=CLAIRE):
    with pg.cursor() as c:
        c.execute("DELETE FROM consents WHERE guest_id=%s", (gid,))
        c.execute("SELECT count(*) FROM claims WHERE guest_id=%s", (gid,)); left = c.fetchone()[0]
    pg.commit()
    res = next((a for a in O().RES["arrivals"] if a["guest_id"] == gid), None)
    vk.delete(f"stay:{res['res_id'] if res else gid}:claims")
    log("forget", f"consent withdrawn: memory deleted in Postgres (left: {left}) and Valkey, same request")
    RD.load_memory(pg, vk)
    replan(pg, vk, "Claire withdrew her consent")
    return state(pg, vk)


def answer_anticipation(pg, vk, index: int):
    """The hotel asks the guest (a drafted WhatsApp question); nothing is stored until she answers."""
    if 0 <= index < len(S["anticipations"]):
        a = S["anticipations"][index]
        S["chat"].append({"who": "hotel", "text": a["ask"], "at": hh(S["now"]), "sent": True})
        log("ask", f"asked instead of assuming: {a['ask']}")
    return state(pg, vk)


# ------------------------------------------------------------------ plan, ledger, anticipations
def replan(pg, vk, trigger, parsed=None, written=(), confirmed=()):
    W, now = O().W, S["now"]
    p = O().plan_room(W, CLAIRE, now)
    with pg.cursor() as c:
        c.execute("""INSERT INTO decisions (at, guest_id, room, ready_by, cites, alternative)
                     VALUES (%s,%s,%s,%s,%s,%s) RETURNING id""",
                  (RD.at(hh(now)), CLAIRE, p["room"], p["ready_by"], sorted(p["cites"]), p["alternative"]))
        S["decision_id"] = c.fetchone()[0]
    pg.commit()
    room = O().ROOMS[p["room"]]
    eta_m, _ = O().eta_of(CLAIRE)
    S["last"] = {"trigger": trigger, "parsed": parsed, "written": list(written), "confirmed": list(confirmed),
                 "room": p["room"], "side": room["side"], "desk": room["desk"], "floor": room["floor"],
                 "ready_by": p["ready_by"], "wait": p["wait"], "prioritise": p["prioritise"],
                 "cites": sorted(p["cites"]), "alternative": p["alternative"], "no_fit": p["no_fit"],
                 "eta": hh(eta_m), "decision_id": S["decision_id"], "validated": False}
    S["anticipations"] = anticipate(p) + S["pos_antic"]
    log("plan", f"re-planned: room {p['room']}, ready {p['ready_by']}, wait {p['wait']} min (decision #{S['decision_id']}, waiting for a human)")
    return {"card": S["last"]}


def ledger(pg, vk):
    """What the agent used, kept aside, refused, forgot, and what each tool receives."""
    gl = RD.glossary()
    mem = RD.memory_snapshot(pg, vk, CLAIRE)
    for r in mem:
        gl.setdefault(r["claim_id"], r["statement"])
    last = S["last"] or {}
    cites = set(last.get("cites", []))
    used = [{"id": c, "what": gl.get(c, c), "kind": "context" if c.startswith("X-") else "memory",
             "store": next((r["store"] for r in mem if r["claim_id"] == c), "context feed")} for c in sorted(cites)]
    kept_aside = [{"id": r["claim_id"], "what": r["statement"], "store": r["store"],
                   "why": "not needed for this decision" if normalise_key_of(r) in PLANNER_KEYS
                   else "kept as said; no rule uses it yet"} for r in mem if r["claim_id"] not in cites]
    with pg.cursor() as c:
        c.execute("SELECT attribute, origin, source, count FROM refusals ORDER BY attribute")
        refused = [{"attribute": a, "origin": o, "source": s, "count": n} for a, o, s, n in c.fetchall()]
    shared = []
    if last:
        shared = [
            {"tool": "Housekeeping app", "gets": {"room": last["room"], "clean_first": last["prioritise"],
                                                  "ready_by": last["ready_by"]},
             "never": "who the guest is or why"},
            {"tool": "PMS (room assignment)", "gets": {"reservation": "R-G001", "room": last["room"]},
             "never": "the guest's statements"},
            {"tool": "Front-desk brief", "gets": {"room": last["room"], "reasons": sorted(cites)},
             "never": "anything refused or expired"},
        ]
    context = [{"id": s["id"], "what": s["summary"], "source": s["source"],
                "used_only_if": s.get("used_only_if")} for s in O().CTX["sources"]]
    return {"used": used, "kept_aside": kept_aside, "refused": refused,
            "forgotten": [e for e in S["log"] if e["kind"] == "forget"], "shared": shared,
            "pushed": bool(last.get("validated")), "context": context,
            "sources": [{**s, "seen": S["seen"].get(s["id"], 0)} for s in SOURCES]}


def normalise_key_of(row) -> str:
    for g in O().G.values():
        for c in g["claims"]:
            if c["claim_id"] == row["claim_id"]:
                return c["key"]
    return ""


def anticipate(p) -> list[dict]:
    """Needs Anima expects from what was DECLARED plus live context. Shown as questions, never stored."""
    out, d = [], O().declared
    eta_m, eta_claim = O().eta_of(CLAIRE)
    desk, quiet, early = d(CLAIRE, "needs_desk"), d(CLAIRE, "quiet_room"), eta_m < O().CHECK_IN
    if desk and early:
        out.append({"need": "She will want to work as soon as she arrives",
                    "from": [desk["claim_id"], eta_claim["claim_id"] if eta_claim else "eta"],
                    "ask": "Would you like the Wi-Fi code and a coffee ready when you arrive?"})
    if p["wait"] > 0:
        out.append({"need": f"She would wait {p['wait']} min for a room that fits",
                    "from": [c for c in sorted(p["cites"]) if c.startswith("C")][:2],
                    "ask": "Your room needs a little more time: shall we keep a quiet corner with a desk for you meanwhile?"})
    if quiet and O().ROOMS[p["room"]]["side"] == "courtyard":
        out.append({"need": "Concert tonight on the street side; she asked for quiet",
                    "from": [quiet["claim_id"], O().NOISE["id"]],
                    "ask": "There's a concert nearby tonight: would you like earplugs in the room just in case?"})
    if eta_claim and early:
        out.append({"need": "Her train is tracked only because she told us; if it is late, hold the room",
                    "from": [eta_claim["claim_id"], "X-TR-1"], "ask": None})
    return out[:3]


def draft_reply(card) -> str:
    if card["wait"] == 0:
        return (f"Thanks Claire! Your room ({card['room']}, {card['side']} side, with a desk) will be ready "
                f"by {card['ready_by']}. See you at {card['eta']}.")
    return (f"Thanks Claire! Your quiet room will be ready at {card['ready_by']}. "
            f"Until then we can set you up in a quiet corner with a desk.")


def state(pg, vk) -> dict:
    with pg.cursor() as c:
        c.execute("SELECT coalesce(sum(count), 0) FROM refusals"); blocked = c.fetchone()[0]
        c.execute("SELECT count(*), count(validated_by) FROM decisions"); n_dec, n_val = c.fetchone()
        c.execute("SELECT count(*) FROM claims WHERE origin <> 'declared'"); inferred = c.fetchone()[0]
    ms = S["llm_ms"]
    return {"now": hh(S["now"]), "chat": S["chat"], "card": S["last"], "anticipations": S["anticipations"],
            "ledger": ledger(pg, vk), "memory": RD.memory_snapshot(pg, vk, CLAIRE), "log": S["log"][-12:],
            "metrics": {"blocked": blocked, "expired": S.get("expired", 0), "decisions": n_dec, "validated": n_val,
                        "inferred_stored": inferred, "llm_calls": S["llm_calls"],
                        "llm_median_ms": sorted(ms)[len(ms) // 2] if ms else None,
                        "auto_actions": 0},
            "glossary": RD.glossary()}


def dumps(x) -> str:
    return json.dumps(x, ensure_ascii=False, default=str)
