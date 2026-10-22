"""Anima demo runner: replays the synthetic day THROUGH the data layer.

  raw inputs --XADD--> Valkey stream `anima:events` --XREAD--> agent loop
  agent loop: parse -> rule-gated memory ops (Postgres + Valkey) -> load memory FROM the stores
              -> planner tool (reference/replay.py) -> decision row in Postgres -> card on screen

What is real here: Postgres tables (schema.sql), Valkey stream, Valkey this-stay memory with
EXPIREAT at check-out, SQL expiry sweep, cascade delete on consent withdrawal, decisions log.
Parser: PARSER=golden replays the golden targets (recorded); PARSER=llm calls agent/parser.py (live).
Every run writes eval/predictions.json for eval/parse_eval.py.

`run_day()` emits typed frames (dicts); the CLI prints them, the web app (app/main.py) streams them.

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


def load_oracle():
    """Fresh planner tool + world model: replay.py keeps the day's state in module globals."""
    spec = importlib.util.spec_from_file_location("oracle", ROOT / "reference" / "replay.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


O = load_oracle()
DB = os.environ.get("DATABASE_URL", "postgresql://anima@/anima?host=/var/run/postgresql&port=5433")
VK = os.environ.get("VALKEY_URL", "redis://localhost:6380/0")
PARSER = os.environ.get("PARSER", "golden")
PARIS = timezone(timedelta(hours=2))
DAY = O.DAY
STREAM = "anima:events"
RAW = json.loads((ROOT / "data" / "raw_inputs.json").read_text(encoding="utf-8"))["inputs"]
MEMORY_GUESTS = ("G001", "G007", "G008")      # the guests with declared memory in the scenario
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


def memory_snapshot(pg, vk, gid) -> list[dict]:
    """What Anima knows about one guest, read straight from the stores (for the memory panel)."""
    rows = []
    with pg.cursor() as c:
        c.execute("""SELECT claim_id, statement, source, purpose, confirmations, expires_at, needs_reconfirm
                     FROM claims WHERE guest_id=%s ORDER BY claim_id""", (gid,))
        for cid, st, src, purpose, n, exp, rc in c.fetchall():
            rows.append({"claim_id": cid, "statement": st, "origin": f"declared ×{n}" if n > 1 else "declared",
                         "source": src, "purpose": purpose, "kept_until": str(exp), "store": "Postgres",
                         "needs_reconfirm": rc})
    res = next((a for a in O.RES["arrivals"] if a["guest_id"] == gid), None)
    key = f"stay:{res['res_id'] if res else gid}:claims"
    ttl = vk.ttl(key)
    for raw in vk.hvals(key):
        cl = json.loads(raw)
        rows.append({"claim_id": cl["claim_id"], "statement": cl["statement"], "origin": "declared",
                     "source": cl["source"], "purpose": cl["purpose"], "kept_until": "check-out",
                     "store": "Valkey", "ttl_hours": ttl // 3600 if ttl > 0 else None, "needs_reconfirm": False})
    return sorted(rows, key=lambda r: r["claim_id"])


def consented(pg, gid, purpose) -> bool:
    with pg.cursor() as c:
        c.execute("SELECT 1 FROM consents WHERE guest_id=%s AND purpose=%s", (gid, purpose))
        return c.fetchone() is not None


def log_decision(pg, now, gid, p):
    with pg.cursor() as c:
        c.execute("""INSERT INTO decisions (at, guest_id, room, ready_by, cites, alternative)
                     VALUES (%s,%s,%s,%s,%s,%s)""",
                  (now, gid, p.get("room"), p.get("ready_by"), sorted(p.get("cites", [])), p.get("alternative")))


def glossary() -> dict:
    """Citation ids -> what they mean, so a card can show why (claims and world context)."""
    g = {cl["claim_id"]: cl["statement"] for guest in O.ORIGINAL.values() for cl in guest["claims"]}
    for ev in O.EVENTS:
        wc = ev.get("detail", {}).get("write_claim")
        if wc:
            g[wc["claim_id"]] = wc["statement"]
    for src in O.CTX["sources"]:
        g[src["id"]] = src["summary"]
    return g


# ------------------------------------------------------------------ agent steps
def parse(item: dict) -> dict:
    """Step 1. PARSER=golden replays the golden target (recorded); PARSER=llm calls agent/parser.py (live)."""
    if PARSER == "golden":
        return dict(item["target"])
    if PARSER == "llm":
        sys.path.insert(0, str(ROOT))
        from agent.parser import parse_llm
        return parse_llm(item)
    raise SystemExit(f"unknown PARSER={PARSER!r} (golden | llm)")


def card(emit, seq, now_s, kind, title, lines, tone="plan", **data):
    emit({"type": "card", "seq": seq, "at": now_s, "kind": kind, "title": title, "lines": lines, "tone": tone, **data})


def plan_card(emit, seq, now_s, gid, p):
    room = O.ROOMS[p["room"]]
    card(emit, seq, now_s, "plan", f"{O.G[gid]['name'].removeprefix('SYN-')} → room {p['room']}",
         [f"ready {p['ready_by']} · wait {p['wait']} min · cleaned first: {p['prioritise']}",
          f"because: {', '.join(sorted(p['cites']))}" + (f" · alternative: {p['alternative']}" if p["alternative"] else ""),
          "[ Validate ]  (human decides)"],
         guest_id=gid, room=p["room"], side=room["side"], desk=room["desk"], floor=room["floor"],
         ready_by=p["ready_by"], wait=p["wait"], prioritise=p["prioritise"], cites=sorted(p["cites"]),
         alternative=p["alternative"], validate=True)


def run_day(pg, vk, emit, reset_stores=False, pace=0.0) -> int:
    """Replay the day through Postgres + Valkey, emitting frames. Returns the number of failed checks."""
    global O
    O = load_oracle()
    if reset_stores:
        reset(pg, vk)
    raw_by_seq = {}
    for i, item in enumerate(RAW):
        raw_by_seq.setdefault(item["seq"], []).append((i, item))

    # producer: the day's events land on the Valkey stream
    vk.delete(STREAM)
    for ev in O.EVENTS:
        vk.xadd(STREAM, {"seq": ev["seq"], "event": json.dumps(ev, ensure_ascii=False)})
    emit({"type": "start", "events": vk.xlen(STREAM), "stream": STREAM, "postgres": pg.info.server_version // 10000,
          "parser": PARSER, "day": DAY, "glossary": glossary(),
          "guests": {gid: O.G[gid]["name"] for gid in MEMORY_GUESTS}})

    static = O.static_day()          # baseline computed on the morning's knowledge, like the oracle
    predictions, last, refused_total, expired = [], {}, 0, []
    W = O.W
    for _id, fields in vk.xread({STREAM: "0"}, count=100)[0][1]:
        ev = json.loads(fields[b"event"]); now_s = ev["at"]; now = O.mins(now_s); d = ev.get("detail", {})
        typ, ex, seq = ev["type"], ev.get("expect", {}), ev["seq"]
        emit({"type": "event", "seq": seq, "at": now_s, "event_type": typ, "source": ev["source"], "summary": ev["summary"]})
        for i, item in raw_by_seq.get(seq, []):
            out = parse(item); predictions.append({"index": i, "output": out})
            shown = item["payload"] if isinstance(item["payload"], str) else json.dumps(item["payload"], ensure_ascii=False)
            emit({"type": "raw", "seq": seq, "channel": item["channel"], "payload": shown, "parsed": out, "parser": PARSER})
        W.advance(now)
        with pg.cursor() as c:
            c.execute("INSERT INTO events VALUES (%s,%s,%s,%s,%s)",
                      (seq, at(now_s), typ, ev["source"], json.dumps(d)))
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
            card(emit, seq, now_s, "hygiene", "Memory hygiene",
                 [f"{len(expired)} memory expired (36 months without confirmation) and deleted",
                  f"{refused_total} inferred attribute blocked (no guest attached)"], "info",
                 expired=len(expired), blocked=refused_total)
        elif typ == "express_check_out":
            W.leaving[d["room"]] = O.mins(d["leaving_at"])
        elif typ == "guest_message":
            wc = d["write_claim"]
            if consented(pg, wc["guest_id"], wc["purpose"]):
                key = write_working(vk, wc["guest_id"], {**wc, "origin": "declared", "confirmations": 1})
                card(emit, seq, now_s, "memory_write", "Memory write",
                     [f"{wc['claim_id']} '{wc['statement']}' → Valkey {key}, TTL {vk.ttl(key)//3600} h (until check-out)"],
                     "info", claim_id=wc["claim_id"], guest_id=wc["guest_id"])
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
            card(emit, seq, now_s, "consent", "Consent withdrawn",
                 [f"{gid}: consent rows deleted, claims left in Postgres: {left} (cascade)"], "info", guest_id=gid)
        elif typ == "check_in":
            with pg.cursor() as c:
                c.execute("""UPDATE claims SET confirmations = confirmations + 1, last_confirmed = %s
                             WHERE claim_id=%s RETURNING confirmations, expires_at""", (DAY, d["confirm_claim"]))
                n, exp = c.fetchone()
            p = last["G001"]; wait = max(0, O.mins(p["ready_by"]) - now)
            card(emit, seq, now_s, "check_in", "Check-in",
                 [f"Room {p['room']} · wait {wait} min · nothing asked twice",
                  f"{d['confirm_claim']} confirmed ({n}×), now kept until {exp}"],
                 guest_id="G001", room=p["room"], wait=wait)
        elif typ == "guest_reply":
            wc = d["write_claim"]; gid = wc["guest_id"]
            write_working(vk, gid, {**wc, "origin": "declared", "confirmations": 1})
            with pg.cursor() as c:
                c.execute("UPDATE claims SET needs_reconfirm = true WHERE guest_id=%s AND key=%s AND layer='semantic'",
                          (gid, wc["key"]))
            W.holds.discard(ex[gid]["hold_released"])
            card(emit, seq, now_s, "contradiction", "Contradiction handled",
                 [f"{wc['claim_id']} (this stay) wins tonight; durable {ex[gid]['durable_kept']} kept, flagged to reconfirm",
                  f"offer withdrawn, {ex[gid]['hold_released']} released"], "info", guest_id=gid)
        pg.commit()
        load_memory(pg, vk)                                              # planner reads the stores

        # ---- planner tool + explanation card
        if typ == "arrival_imminent":
            card(emit, seq, now_s, "brief", "Brief", [O.brief("G001", last["G001"], now)], guest_id="G001")
        if "G001" in ex and typ not in ("check_in", "arrival_imminent"):
            prev = last.get("G001")
            p = O.plan_room(W, "G001", now); last["G001"] = p; log_decision(pg, at(now_s), "G001", p)
            if ex["G001"].get("no_change") and prev and prev["room"] == p["room"]:
                card(emit, seq, now_s, "no_change", "No change",
                     [f"no change: Claire stays in {p['room']} (ready {p['ready_by']})"], "quiet",
                     guest_id="G001", room=p["room"], ready_by=p["ready_by"])
            else:
                plan_card(emit, seq, now_s, "G001", p)
        if typ == "day_start":
            O.place_all_arrivals(W, now)
        if "G007" in ex and typ in ("day_start", "back_in_service"):
            s = O.move_suggestion(W, "G007", now, O.mins("20:00"))
            log_decision(pg, at(now_s), "G007", {"room": s["room"], "ready_by": s.get("ready_by"), "cites": s["cites"]})
            card(emit, seq, now_s, "suggestion", "Malik Benali (302, street side)",
                 [f"suggest {s['room']} ready {s.get('ready_by')} before the 20:00 concert · because: {', '.join(sorted(s['cites']))}"
                  if s["room"] else "concert tonight on his side · watching, no move before 15:00"],
                 guest_id="G007", room=s["room"], ready_by=s.get("ready_by"), cites=sorted(s["cites"]),
                 validate=bool(s["room"]))
        if typ == "arrivals":
            for gid in ("G008", "G012"):
                p = O.plan_room(W, gid, now); log_decision(pg, at(now_s), gid, p)
                card(emit, seq, now_s, "arrival", f"{O.G[gid]['name']} → room {p['room']}",
                     [f"memory used: {sorted(p['cites']) or 'none'}"], guest_id=gid, room=p["room"], cites=sorted(p["cites"]))
        pg.commit()
        with pg.cursor() as c:
            c.execute("SELECT coalesce(sum(count), 0) FROM refusals"); blocked = c.fetchone()[0]
        emit({"type": "memory", "seq": seq, "at": now_s, "blocked": blocked, "expired": len(expired),
              "guests": {gid: memory_snapshot(pg, vk, gid) for gid in MEMORY_GUESTS}})
        time.sleep(pace)

    (ROOT / "eval" / "predictions.json").write_text(json.dumps(predictions, ensure_ascii=False, indent=1), encoding="utf-8")
    emit({"type": "before_after", "static_room": static["planned_room"], "static_wait": static["wait"],
          "anima_room": last["G001"]["room"], "anima_wait": 0})

    # ---- end-of-day checks on the stores themselves
    results = []
    def chk(ok, msg):
        results.append({"ok": bool(ok), "msg": msg})
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
    fails = sum(not r["ok"] for r in results)
    emit({"type": "checks", "results": results, "fails": fails, "parser": PARSER})
    return fails


# ------------------------------------------------------------------ CLI
def print_frame(f: dict):
    t = f["type"]
    if t == "start":
        print(f"{D}{f['events']} events on Valkey stream '{f['stream']}' · Postgres {f['postgres']} · parser={f['parser']}{X}")
    elif t == "event":
        print(f"\n{B}{f['at']}{X}  {f['summary']}")
    elif t == "raw":
        print(f"{D}  ← {f['channel']}: {f['payload'][:110]}{X}")
    elif t == "card" and f["kind"] == "no_change":
        print(f"  {D}{f['lines'][0]}{X}")
    elif t == "card" and f["kind"] == "brief":
        print(f"  {B}🔊 Brief:{X} {f['lines'][0]}")
    elif t == "card":
        color = Y if f["tone"] == "info" else G_
        print(f"\n{color}{B}┃ {f['title']}{X}")
        for ln in f["lines"]:
            print(f"{color}┃{X} {ln}")
    elif t == "before_after":
        print(f"\n{B}Before / after{X}")
        print(f"  memory but no re-planning: {f['static_room']} out of service at the desk → {f['static_wait']} min wait")
        print(f"  Anima: room {f['anima_room']} → 0 min")
    elif t == "checks":
        print(f"\n{B}Checks on Postgres + Valkey{X}")
        for r in f["results"]:
            print(f"  {'PASS' if r['ok'] else R + 'FAIL' + X}  {r['msg']}")
        print(f"\n{D}Recorded scenario (synthetic) · parser={f['parser']} · memory ops and decisions live on Postgres + Valkey{X}")
        print(f"{'ALL PASS' if not f['fails'] else str(f['fails']) + ' FAIL'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="drop and seed the sandbox stores")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds between events (1.5 for a live demo)")
    a = ap.parse_args()
    pg, vk = psycopg.connect(DB), valkey.from_url(VK)
    fails = run_day(pg, vk, print_frame, reset_stores=a.reset, pace=a.pace)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
