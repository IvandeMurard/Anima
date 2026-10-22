"""Anima web app on Aiven Runtime: one front-office page that replays the day live on the data layer.

Postgres and Valkey come from DATABASE_URL and VALKEY_URL (Runtime's default names for connected
services). POST /api/replay runs demo/run_demo.py's run_day() in a thread; GET /api/stream sends its
frames as server-sent events, from the start of the current run, so a refresh or a second screen
sees the whole day.

Usage:
  DATABASE_URL=postgresql://... VALKEY_URL=rediss://... uvicorn app.main:app --port 8080
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
from pathlib import Path

import psycopg
import valkey
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "demo"))
import run_demo  # noqa: E402  (demo/run_demo.py: the agent loop, shared with the CLI)

app = FastAPI(title="Anima")
RUN = {"id": 0, "frames": [], "running": False}     # one replay at a time: it resets the stores
LOCK = threading.Lock()


def check_postgres() -> dict:
    url = os.environ.get("DATABASE_URL")
    if not url:
        return {"ok": False, "error": "DATABASE_URL not set"}
    try:
        with psycopg.connect(url, connect_timeout=5) as pg:
            pg.execute("SELECT 1")
            return {"ok": True, "version": pg.info.server_version // 10000}
    except Exception as e:                       # report the failure, never the URL (it holds the password)
        return {"ok": False, "error": type(e).__name__}


def check_valkey() -> dict:
    url = os.environ.get("VALKEY_URL")
    if not url:
        return {"ok": False, "error": "VALKEY_URL not set"}
    try:
        vk = valkey.from_url(url, socket_connect_timeout=5, socket_timeout=5)
        vk.ping()
        info = vk.info("server")
        return {"ok": True, "version": info.get("valkey_version") or info.get("redis_version")}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def store_env_names() -> list[str]:
    """Names (never values) of env vars that look like store connections: shows what Runtime injected."""
    hints = ("DATABASE", "POSTGRES", "PG", "VALKEY", "REDIS", "URI", "URL", "AIVEN")
    return sorted(k for k in os.environ if any(h in k.upper() for h in hints))


@app.get("/api/health")
def health():
    """Always 200 so the app itself counts as up; the body says whether each store is reachable."""
    pg, vk = check_postgres(), check_valkey()
    return {"app": "ok", "postgres": pg, "valkey": vk, "ready": pg["ok"] and vk["ok"],
            "env_names": store_env_names(), "llm_available": bool(os.environ.get("ANTHROPIC_API_KEY"))}


# ------------------------------------------------------------------ replay
def replay(run_id: int, pace: float, parser: str):
    def emit(frame):
        with LOCK:
            if RUN["id"] == run_id:
                RUN["frames"].append({**frame, "run": run_id})
    pg = vk = None
    try:
        run_demo.PARSER = parser
        pg = psycopg.connect(os.environ["DATABASE_URL"])
        vk = valkey.from_url(os.environ["VALKEY_URL"])
        run_demo.run_day(pg, vk, emit, reset_stores=True, pace=pace)
    except Exception as e:                       # the type only: messages can carry connection details
        emit({"type": "error", "error": type(e).__name__})
    finally:
        if pg:
            pg.close()
        emit({"type": "done"})
        with LOCK:
            RUN["running"] = False


@app.post("/api/replay")
def start_replay(pace: float = 1.5, parser: str = "golden"):
    if parser not in ("golden", "llm"):
        raise HTTPException(400, "parser must be golden or llm")
    if parser == "llm" and not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set: the live parser is unavailable")
    with LOCK:
        if RUN["running"]:
            raise HTTPException(409, "a replay is already running")
        RUN["id"] += 1; RUN["frames"] = []; RUN["running"] = True
        run_id = RUN["id"]
    live.S["now"] = None                         # the tour resets the stores: a live day must restart
    threading.Thread(target=replay, args=(run_id, max(0.0, min(pace, 5.0)), parser), daemon=True).start()
    return {"run": run_id}


@app.get("/api/stream")
async def stream():
    async def frames():
        sent, run, last_ping = 0, None, time.monotonic()
        while True:
            with LOCK:
                if RUN["id"] != run:
                    run, sent = RUN["id"], 0
                batch = RUN["frames"][sent:]
            for f in batch:
                yield f"data: {json.dumps(f, ensure_ascii=False, default=str)}\n\n"
            sent += len(batch)
            if time.monotonic() - last_ping > 15:
                yield ": ping\n\n"; last_ping = time.monotonic()
            await asyncio.sleep(0.2)
    return StreamingResponse(frames(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ------------------------------------------------------------------ live mode ("Try it")
import live  # noqa: E402  (demo/live.py)

LIVE_LOCK = threading.Lock()


def live_call(fn, *args):
    """Run one live action on fresh connections; refuse while the guided tour is replaying."""
    with LOCK:
        if RUN["running"]:
            raise HTTPException(409, "the guided tour is replaying; wait for it to finish")
    if fn is not live.start and live.S["now"] is None:
        raise HTTPException(409, "press Start first")
    with LIVE_LOCK:
        pg = psycopg.connect(os.environ["DATABASE_URL"])
        vk = valkey.from_url(os.environ["VALKEY_URL"])
        try:
            out = fn(pg, vk, *args)
            return json.loads(live.dumps(out if fn is not live.start else live.state(pg, vk)))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"live step failed: {type(e).__name__}")
        finally:
            pg.close()


def need_llm():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(400, "ANTHROPIC_API_KEY not set: live reading of messages is unavailable")


@app.post("/api/live/start")
def live_start():
    return live_call(live.start)


@app.get("/api/live/state")
def live_state():
    return live_call(live.state)


@app.post("/api/live/guest")
def live_guest(body: dict):
    need_llm()
    return live_call(live.guest_message, str(body.get("text", ""))[:500], body.get("at"))


@app.post("/api/live/staff")
def live_staff(body: dict):
    need_llm()
    return live_call(live.staff_report, str(body.get("text", ""))[:500], body.get("at"))


@app.post("/api/live/ota")
def live_ota(body: dict):
    need_llm()
    return live_call(live.ota_request, str(body.get("text", ""))[:500], body.get("at"))


@app.post("/api/live/pos")
def live_pos(body: dict):
    return live_call(live.pos_receipt, str(body.get("text", ""))[:80])


@app.post("/api/live/outside")
def live_outside(body: dict):
    return live_call(live.outside_agent, str(body.get("text", ""))[:120])


@app.post("/api/live/validate")
def live_validate():
    return live_call(live.validate)


@app.post("/api/live/withdraw")
def live_withdraw():
    return live_call(live.withdraw)


@app.post("/api/live/ask/{index}")
def live_ask(index: int):
    return live_call(live.answer_anticipation, index)


@app.get("/")
def index():
    return FileResponse(ROOT / "app" / "static" / "index.html")
