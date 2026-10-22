"""Anima web app on Aiven Runtime. T1a: walking skeleton.

Proves the deploy pipeline before any screen is built: one page and one health endpoint that
reach Aiven Postgres and Valkey through DATABASE_URL and VALKEY_URL (Runtime's default names
for connected services). The demo replay (screens 1-4) plugs in here in T1b.

Usage:
  DATABASE_URL=postgresql://... VALKEY_URL=rediss://... uvicorn app.main:app --port 8080
"""
from __future__ import annotations

import os

import psycopg
import valkey
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Anima")


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


@app.get("/api/health")
def health():
    """Always 200 so the app itself counts as up; the body says whether each store is reachable."""
    pg, vk = check_postgres(), check_valkey()
    return {"app": "ok", "postgres": pg, "valkey": vk, "ready": pg["ok"] and vk["ok"]}


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Anima</title>
<style>
  body { font: 16px/1.5 system-ui, sans-serif; max-width: 40rem; margin: 3rem auto; padding: 0 1rem; color: #1a1a1a; background: #fafaf7; }
  h1 { margin-bottom: .25rem; } p.sub { color: #666; margin-top: 0; }
  li { list-style: none; font-size: 1.25rem; margin: .5rem 0; }
  .ok { color: #1a7f37; } .ko { color: #cf222e; }
  small { color: #666; }
</style></head>
<body>
  <h1>Anima</h1>
  <p class="sub">Guest memory for hotel agents · synthetic data only · running on Aiven Runtime</p>
  <ul id="stores"><li>Checking the data layer…</li></ul>
  <small>Demo replay (screens 1-4) arrives in T1b.</small>
<script>
fetch("/api/health").then(r => r.json()).then(h => {
  const row = (name, s) => `<li class="${s.ok ? "ok" : "ko"}">${name} ${s.ok ? "✓" : "✗"} <small>${s.ok ? (s.version ? "v" + s.version : "") : s.error}</small></li>`;
  document.getElementById("stores").innerHTML = row("Postgres", h.postgres) + row("Valkey", h.valkey);
}).catch(() => { document.getElementById("stores").innerHTML = '<li class="ko">Health check failed</li>'; });
</script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE
