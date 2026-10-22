#!/usr/bin/env bash
# Local sandbox on macOS (Homebrew): Postgres 16 :5433 + Valkey :6380, venv, then the web app on :8000.
set -euo pipefail
cd "$(dirname "$0")/.."
export LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8          # Postgres refuses to start without a valid locale
brew list postgresql@16 >/dev/null 2>&1 || brew install postgresql@16
brew list valkey >/dev/null 2>&1 || brew install valkey
PG=/opt/homebrew/opt/postgresql@16/bin
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
mkdir -p .sandbox
[ -d .sandbox/pg ] || $PG/initdb -D .sandbox/pg -U anima --auth=trust >/dev/null
$PG/pg_ctl -D .sandbox/pg status >/dev/null || $PG/pg_ctl -D .sandbox/pg -o "-p 5433 -k /tmp" -l .sandbox/pg.log start
sleep 1
$PG/psql -h /tmp -p 5433 -U anima -d postgres -qtc "SELECT 1 FROM pg_database WHERE datname='anima'" | grep -q 1 \
  || $PG/createdb -h /tmp -p 5433 -U anima anima
/opt/homebrew/opt/valkey/bin/valkey-cli -p 6380 ping >/dev/null 2>&1 \
  || /opt/homebrew/opt/valkey/bin/valkey-server --port 6380 --daemonize yes --save ""
export DATABASE_URL="postgresql://anima@/anima?host=/tmp&port=5433" VALKEY_URL="redis://localhost:6380/0"
echo "sandbox ready → http://localhost:8000"
exec .venv/bin/uvicorn app.main:app --reload --port 8000
