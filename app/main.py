"""Anima web app: thin FastAPI layer over the demo runner and the stores (Postgres + Valkey).

  POST /api/run                    replay the synthetic day through the stores (demo/run_demo.py --reset)
  GET  /api/state                  events, decisions, memory (Postgres + Valkey), refusals
  POST /api/decisions/{id}/validate  a human validates a recommendation (R4: no auto-action)
  GET  /api/health                liveness + store connectivity (Postgres SELECT 1, Valkey PING)

Config: DATABASE_URL, VALKEY_URL (Aiven connected services), PORT.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

import psycopg
import valkey
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

ROOT = Path(__file__).resolve().parent.parent
DB = os.environ.get("DATABASE_URL", "postgresql://anima@/anima?host=/tmp&port=5433")
VK = os.environ.get("VALKEY_URL", "redis://localhost:6380/0")
ANSI = re.compile(r"\x1b\[[0-9;]*m")

_env = ROOT / ".env"                                     # local only; on Aiven the env comes from the console
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

app = FastAPI(title="Anima")
_run_lock = threading.Lock()
_last_run: dict = {"status": "never", "output": ""}


def pg():
    return psycopg.connect(DB)


def vk():
    return valkey.from_url(VK)


@app.get("/api/health")
@app.get("/healthz")
def healthz():
    out = {"ok": True}
    try:
        with pg() as c:
            c.execute("SELECT 1")
        out["postgres"] = "up"
    except Exception as e:  # noqa: BLE001
        out["ok"], out["postgres"] = False, str(e)[:200]
    try:
        vk().ping()
        out["valkey"] = "up"
    except Exception as e:  # noqa: BLE001
        out["ok"], out["valkey"] = False, str(e)[:200]
    return out


@app.post("/api/run")
def run(pace: float = 0.0, parser: str = os.environ.get("PARSER", "llm" if os.environ.get("ANTHROPIC_API_KEY") else "golden")):
    if not _run_lock.acquire(blocking=False):
        raise HTTPException(409, "a run is already in progress")
    try:
        _last_run["status"] = "running"
        p = subprocess.run(
            [sys.executable, str(ROOT / "demo" / "run_demo.py"), "--reset", "--pace", str(pace)],
            capture_output=True, text=True, env={**os.environ, "DATABASE_URL": DB, "VALKEY_URL": VK, "PARSER": parser}, timeout=600,
        )
        _last_run["output"] = ANSI.sub("", p.stdout + p.stderr)
        _last_run["status"] = "pass" if p.returncode == 0 else "fail"
        _last_run["parser"] = parser
        return _last_run
    finally:
        _run_lock.release()


@app.get("/api/run")
def last_run():
    return _last_run


def _rows(cur, sql, args=()):
    cur.execute(sql, args)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@app.get("/api/state")
def state():
    try:
        with pg() as c, c.cursor() as cur:
            data = {
                "events": _rows(cur, "SELECT seq, at, type, source, payload FROM events ORDER BY seq"),
                "decisions": _rows(cur, """SELECT d.id, d.at, d.guest_id, g.name, d.room, d.ready_by, d.cites,
                                           d.alternative, d.validated_by, d.validated_at
                                           FROM decisions d LEFT JOIN guests g USING (guest_id) ORDER BY d.id"""),
                "claims": _rows(cur, """SELECT claim_id, guest_id, key, value, statement, purpose, layer,
                                        last_confirmed, confirmations, expires_at, needs_reconfirm
                                        FROM claims ORDER BY guest_id, claim_id"""),
                "consents": _rows(cur, "SELECT guest_id, purpose, given, via FROM consents ORDER BY 1, 2"),
                "refusals": _rows(cur, "SELECT day, attribute, origin, source, count FROM refusals"),
            }
    except psycopg.errors.UndefinedTable:
        data = {"events": [], "decisions": [], "claims": [], "consents": [], "refusals": []}
    v = vk()
    stay = {}
    for k in v.scan_iter("stay:*:claims"):
        stay[k.decode()] = {"ttl_s": v.ttl(k), "claims": [json.loads(x) for x in v.hvals(k)]}
    data["stay_memory"] = stay
    return json.loads(json.dumps(data, default=str))


@app.post("/api/decisions/{decision_id}/validate")
def validate(decision_id: int, by: str = "front-desk"):
    with pg() as c, c.cursor() as cur:
        cur.execute("""UPDATE decisions SET validated_by=%s, validated_at=now()
                       WHERE id=%s AND validated_at IS NULL RETURNING id""", (by, decision_id))
        if cur.fetchone() is None:
            raise HTTPException(404, "decision not found or already validated")
    return {"ok": True, "id": decision_id, "validated_by": by}


@app.get("/")
def index():
    return FileResponse(ROOT / "app" / "static" / "index.html")
