"""Anima demo runner: replays the synthetic day THROUGH the data layer.

  raw inputs --XADD--> Valkey stream `anima:events` --XREAD--> agent loop
  agent loop: parse -> rule-gated memory ops (Postgres + Valkey) -> load memory FROM the stores
              -> planner tool (reference/replay.py) -> decision row in Postgres -> card on screen

What is real here: Postgres tables (schema.sql), Valkey stream, Valkey this-stay memory with
EXPIREAT at check-out, SQL expiry sweep, cascade delete on consent withdrawal, decisions log.
What is a stub: the parser. PARSER=golden replays the golden targets (recorded). Plug the LLM
parser into `parse()` on the day; every run writes eval/predictions.json for eval/parse_eval.py.

Usage:
  DATABASE_URL=postgresql://... VALKEY_URL=redis://... python demo/run_demo.py --reset [--pace 1.5]
Defaults point at the local sandbox (Postgres :5433 via /var/run/postgresql, Valkey :6380).
Exit code 1 if the end-of-day checks on the stores fail.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import valkey

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("oracle", ROOT / "reference" / "replay.py")
O = importlib.util.module_from_spec(spec); spec.loader.exec_module(O)          # planner tool + world model

DB = os.environ.get("DATABASE_URL", "postgresql://anima@/anima?host=/var/run/postgresql&port=5433")
VK = os.environ.get("VALKEY_URL", "redis://localhost:6380/0")
PARSER = os.environ.get("PARSER", "golden")
PARIS = timezone(timedelta(hours=2))
DAY = O.DAY
STREAM = "anima:events"
RAW = json.loads((ROOT / "data" / "raw_inputs.json").read_text(encoding="utf-8"))["inputs"]
B, D, G_, Y, R, X = "\033[1m", "\033[2m", "\033[32m", "\033[33m", "\033[31m", "\033[0m"


def at(hhmm: str, day: str = DAY) -> datetime:
    return datetime.fromisoformat(f"{day}T{hhmm}:00").replace(tzinfo=PARIS)


def checkout_ts(res: dict) -> int:
    d = datetime.fromisoformat(DAY) + timedelta(days=res["nights"])
    return int(at("11:00", d.date().isoformat()).timestamp())


# ------------------------------------------------------------------ stores
def reset(pg, vk):
    with pg.cursor() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        c.execute((ROOT / "schema.sql").read_text(encoding="utf-8"))
    vk.flushdb()
    stay_of = {a["guest_id"]: a for a in O.RES["arrivals"]}
    with pg.cursor() as c:
        for g in O.ORIGINAL.values():
            c.execute("INSERT INTO guests VALUES (%s,%s,%s)", (g["guest_id"], g["name"], g["stays_before"]))
            for p in (g.get("consent") or {}).get("purposes", []):
                c.execute("INSERT INTO consents VALUES (%s,%s,%s,%s)", (g["guest_id"], p["name"], p["given"], p["via"]))
            for cl in g["claims"]:
                if cl["layer"] == "semantic":
                    c.execute("""INSERT INTO claims (claim_id,guest_id,key,value,statement,origin,source,purpose,layer,
                                 first_seen,last_confirmed,confirmations) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                              (cl["claim_id"], g["guest_id"], cl["key"], json.dumps(cl["value"]), cl["statement"],
                               cl["origin"], cl["source"], cl["purpose"], "semantic", cl["first_seen"],
                               cl["last_confirmed"], cl["confirmations"]))
                else:
                    write_working(vk, g["guest_id"], cl, stay_of)
    pg.commit()


def write_working(vk, gid, claim, stay_of=None):
    stay_of = stay_of or {a["guest_id"]: a for a in O.RES["arrivals"]}
    res = stay_of.get(gid)
    key = f"stay:{res['res_id'] if res else gid}:claims"
    vk.hset(key, claim["claim_id"], json.dumps(claim))
    if res:
        vk.expireat(key, checkout_ts(res))           # this-stay memory forgets by itself at check-out
    return key


def load_memory(pg, vk):
    """The planner reads memory FROM the stores, not from files."""
    for gid, g in O.G.items():
        g["consent"], g["claims"] = None, []
    with pg.cursor() as c:
        c.execute("SELECT guest_id, purpose, given, via FROM consents")
        for gid, p, given, via in c.fetchall():
            O.G[gid]["consent"] = O.G[gid]["consent"] or {"purposes": [], "decoupled_from_booking": True}
            O.G[gid]["consent"]["purposes"].append({"name": p, "given": str(given), "via": via})
        c.execute("""SELECT claim_id, guest_id, key, value, statement, origin, source, purpose, layer,
                     first_seen, last_confirmed, confirmations, needs_reconfirm FROM claims""")
        for row in c.fetchall():
            cid, gid, key, value, st, origin, src, purpose, layer, fs, lc, n, rc = row
            O.G[gid]["claims"].append({"claim_id": cid, "key": key, "value": value, "statement": st,
                                       "origin": origin, "source": src, "purpose": purpose, "layer": layer,
                                       "first_seen": str(fs), "last_confirmed": str(lc), "confirmations": n,
                                       "needs_reconfirm": rc})
    for k in vk.scan_iter("stay:*:claims"):
        for raw in vk.hvals(k):
            cl = json.loads(raw)
            gid = cl.get("guest_id") or next(a["guest_id"] for a in O.RES["arrivals"] if f"stay:{a['res_id']}:claims" == k.decode())
            O.G[gid]["claims"].append(cl)


def consented(pg, gid, purpose) -> bool:
    with pg.cursor() as c:
        c.execute("SELECT 1 FROM consents WHERE guest_id=%s AND purpose=%s", (gid, purpose))
        return c.fetchone() is not None


def log_decision(pg, now, gid, p):
    with pg.cursor() as c:
        c.execute("""INSERT INTO decisions (at, guest_id, room, ready_by, cites, alternative)
                     VALUES (%s,%s,%s,%s,%s,%s)""",
                  (now, gid, p.get("room"), p.get("ready_by"), sorted(p.get("cites", [])), p.get("alternative")))


# ------------------------------------------------------------------ agent steps
def parser_context(open_offers: list[dict]) -> dict:
    """What the agent already holds when an input arrives: guests with memory (from the stores) + open offers."""
    guests = [{"guest_id": gid, "name": g["name"], "contact": g.get("contact"),
               "memory": [{"key": c["key"], "layer": c["layer"], "statement": c["statement"]} for c in g["claims"]]}
              for gid, g in O.G.items() if g["claims"]]
    return {"day": DAY, "guests_with_memory": guests, "open_offers": open_offers}


def parse(item: dict, context: dict) -> dict:
    """Step 1. PARSER=golden replays the golden target (recorded); PARSER=llm calls Claude (demo/llm_parser.py)."""
    if PARSER == "golden":
        return dict(item["target"])
    if PARSER == "llm":
        from llm_parser import parse_llm
        return parse_llm(item, context)
    raise SystemExit(f"unknown PARSER={PARSER!r} (golden | llm)")


def card(title, lines, color=G_):
    print(f"\n{color}{B}┃ {title}{X}")
    for ln in lines:
        print(f"{color}┃{X} {ln}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="drop and seed the sandbox stores")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds between events (1.5 for a live demo)")
    a = ap.parse_args()
    pg, vk = psycopg.connect(DB), valkey.from_url(VK)
    if a.reset:
        reset(pg, vk)
    raw_by_seq = {}
    for i, item in enumerate(RAW):
        raw_by_seq.setdefault(item["seq"], []).append((i, item))

    # producer: the day's events land on the Valkey stream
    vk.delete(STREAM)
    for ev in O.EVENTS:
        vk.xadd(STREAM, {"seq": ev["seq"], "event": json.dumps(ev, ensure_ascii=False)})
    print(f"{D}{vk.xlen(STREAM)} events on Valkey stream '{STREAM}' · Postgres {pg.info.server_version // 10000} · parser={PARSER}{X}")

    static = O.static_day()          # baseline computed on the morning's knowledge, like the oracle
    predictions, last, refused_total, open_offers = [], {}, 0, []
    W = O.W
    for _id, fields in vk.xread({STREAM: "0"}, count=100)[0][1]:
        ev = json.loads(fields[b"event"]); now_s = ev["at"]; now = O.mins(now_s); d = ev.get("detail", {})
        typ, ex = ev["type"], ev.get("expect", {})
        print(f"\n{B}{now_s}{X}  {ev['summary']}")
        for i, item in raw_by_seq.get(ev["seq"], []):
            out = parse(item, parser_context(open_offers)); predictions.append({"index": i, "output": out})
            if PARSER == "llm":
                print(f"{D}  → parsed: {json.dumps(out, ensure_ascii=False)[:150]}{X}")
            shown = item["payload"] if isinstance(item["payload"], str) else json.dumps(item["payload"], ensure_ascii=False)
            print(f"{D}  ← {item['channel']}: {shown[:110]}{X}")
        W.advance(now)
        with pg.cursor() as c:
            c.execute("INSERT INTO events VALUES (%s,%s,%s,%s,%s)",
                      (ev["seq"], at(now_s), typ, ev["source"], json.dumps(d)))
        # ---- rule-gated memory operations on the stores
        if typ == "day_start":
            with pg.cursor() as c:
                c.execute("DELETE FROM claims WHERE expires_at <= %s RETURNING claim_id", (DAY,))
                expired = [r[0] for r in c.fetchall()]
                pc = d["proposed_claim"]
                if pc.get("origin") != "declared":                       # R2: refused at the door
                    c.execute("""INSERT INTO refusals VALUES (%s,%s,%s,%s,1)
                                 ON CONFLICT (day,attribute,origin,source) DO UPDATE SET count = refusals.count + 1""",
                              (DAY, pc["key"], pc["origin"], pc["source"])); refused_total += 1
            card("Memory hygiene", [f"{len(expired)} memory expired (36 months without confirmation) and deleted",
                                    f"{refused_total} inferred attribute blocked (no guest attached)"], Y)
        elif typ == "express_check_out":
            W.leaving[d["room"]] = O.mins(d["leaving_at"])
        elif typ == "guest_message":
            wc = d["write_claim"]
            if consented(pg, wc["guest_id"], wc["purpose"]):
                key = write_working(vk, wc["guest_id"], {**wc, "origin": "declared", "confirmations": 1})
                card("Memory write", [f"{wc['claim_id']} '{wc['statement']}' → Valkey {key}, TTL {vk.ttl(key)//3600} h (until check-out)"], Y)
        elif typ == "early_check_out":
            W.leaving[d["room"]] = O.mins(d["left_at"])
        elif typ == "out_of_service":
            W.oos[d["room"]] = O.mins(d["back_in_service"]) if d.get("back_in_service") else None
            if W.planned.get("G001") == d["room"]:
                W.planned["G001"] = None
            if d["room"] in W.pins:
                W.pins.remove(d["room"])
        elif typ == "back_in_service":
            W.reclean[d["room"]] = now
        elif typ == "consent_withdrawn":
            gid = d["guest_id"]
            with pg.cursor() as c:
                c.execute("DELETE FROM consents WHERE guest_id=%s", (gid,))
                c.execute("SELECT count(*) FROM claims WHERE guest_id=%s", (gid,)); left = c.fetchone()[0]
            for k in vk.scan_iter("stay:*:claims"):
                if k.decode() == f"stay:R-{gid}:claims":
                    vk.delete(k)
            card("Consent withdrawn", [f"{gid}: consent rows deleted, claims left in Postgres: {left} (cascade)"], Y)
        elif typ == "check_in":
            with pg.cursor() as c:
                c.execute("""UPDATE claims SET confirmations = confirmations + 1, last_confirmed = %s
                             WHERE claim_id=%s RETURNING confirmations, expires_at""", (DAY, d["confirm_claim"]))
                n, exp = c.fetchone()
            p = last["G001"]; wait = max(0, O.mins(p["ready_by"]) - now)
            card("Check-in", [f"Room {p['room']} · wait {wait} min · nothing asked twice",
                              f"{d['confirm_claim']} confirmed ({n}×), now kept until {exp}"])
        elif typ == "guest_reply":
            wc = d["write_claim"]; gid = wc["guest_id"]
            write_working(vk, gid, {**wc, "origin": "declared", "confirmations": 1})
            with pg.cursor() as c:
                c.execute("UPDATE claims SET needs_reconfirm = true WHERE guest_id=%s AND key=%s AND layer='semantic'",
                          (gid, wc["key"]))
            W.holds.discard(ex[gid]["hold_released"])
            card("Contradiction handled", [f"{wc['claim_id']} (this stay) wins tonight; durable {ex[gid]['durable_kept']} kept, flagged to reconfirm",
                                           f"offer withdrawn, {ex[gid]['hold_released']} released"], Y)
        pg.commit()
        load_memory(pg, vk)                                              # planner reads the stores

        # ---- planner tool + explanation card
        if typ == "arrival_imminent":
            print(f"  {B}🔊 Brief:{X} {O.brief('G001', last['G001'], now)}")
        if "G001" in ex and typ not in ("check_in", "arrival_imminent"):
            prev = last.get("G001")
            p = O.plan_room(W, "G001", now); last["G001"] = p; log_decision(pg, at(now_s), "G001", p)
            if ex["G001"].get("no_change") and prev and prev["room"] == p["room"]:
                print(f"  {D}no change: Claire stays in {p['room']} (ready {p['ready_by']}){X}")
            else:
                card(f"Claire Laurent → room {p['room']}",
                     [f"ready {p['ready_by']} · wait {p['wait']} min · cleaned first: {p['prioritise']}",
                      f"because: {', '.join(sorted(p['cites']))}" + (f" · alternative: {p['alternative']}" if p["alternative"] else ""),
                      "[ Validate ]  (human decides)"])
        if typ == "day_start":
            O.place_all_arrivals(W, now)
        if "G007" in ex and typ in ("day_start", "back_in_service"):
            s = O.move_suggestion(W, "G007", now, O.mins("20:00"))
            log_decision(pg, at(now_s), "G007", {"room": s["room"], "ready_by": s.get("ready_by"), "cites": s["cites"]})
            if s["room"]:
                open_offers = [{"guest_id": "G007", "room": s["room"], "ready_by": s.get("ready_by")}]
            card("Malik Benali (302, street side)",
                 [f"suggest {s['room']} ready {s.get('ready_by')} before the 20:00 concert · because: {', '.join(sorted(s['cites']))}"
                  if s["room"] else "concert tonight on his side · watching, no move before 15:00"])
        if typ == "arrivals":
            for gid in ("G008", "G012"):
                p = O.plan_room(W, gid, now); log_decision(pg, at(now_s), gid, p)
                card(f"{O.G[gid]['name']} → room {p['room']}", [f"memory used: {sorted(p['cites']) or 'none'}"])
        pg.commit()
        time.sleep(a.pace)

    (ROOT / "eval" / "predictions.json").write_text(json.dumps(predictions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{B}Before / after{X}")
    print(f"  memory but no re-planning: {static['planned_room']} out of service at the desk → {static['wait']} min wait")
    print(f"  Anima: room {last['G001']['room']} → 0 min")

    # ---- end-of-day checks on the stores themselves
    fails = 0
    def chk(ok, msg):
        nonlocal fails; fails += not ok; print(f"  {'PASS' if ok else R + 'FAIL' + X}  {msg}")
    print(f"\n{B}Checks on Postgres + Valkey{X}")
    with pg.cursor() as c:
        c.execute("SELECT claim_id, confirmations, needs_reconfirm FROM claims ORDER BY 1"); rows = {r[0]: r for r in c.fetchall()}
        chk("C071" not in rows, "stale C071 deleted by the SQL expiry sweep")
        chk(rows.get("C001", (0, 0))[1] == 3, "C001 confirmed 3 times")
        chk(rows.get("C070", (0, 0, False))[2] is True, "C070 kept and flagged to reconfirm")
        chk("C080" not in rows, "G008's memory deleted by cascade on consent withdrawal")
        c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='refusals'")
        chk("guest_id" not in [r[0] for r in c.fetchall()], "refusal log has no guest_id column")
        c.execute("SELECT count(*) FROM decisions"); chk(c.fetchone()[0] > 0, "decisions logged")
        c.execute("SELECT count(*) FROM claims WHERE origin <> 'declared'"); chk(c.fetchone()[0] == 0, "only declared claims stored")
    chk(static["wait"] == 35 and static["broken"], f"baseline matches the oracle (35 min, room out of service): got {static['wait']}")
    ttl = vk.ttl("stay:R-G001:claims")
    chk(ttl > 0, f"Claire's this-stay memory expires by itself in {ttl // 3600} h (Valkey TTL)")
    print(f"\n{D}Recorded scenario (synthetic) · parser={PARSER} · memory ops and decisions live on Postgres + Valkey{X}")
    print(f"{'ALL PASS' if not fails else f'{fails} FAIL'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
