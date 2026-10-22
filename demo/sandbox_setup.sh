#!/usr/bin/env bash
# Local sandbox for the demo: PostgreSQL 16 on :5433 + Valkey on :6380 (Ubuntu/Debian, run as root).
# On the day, replace both with Aiven services and set DATABASE_URL / VALKEY_URL instead.
set -euo pipefail
apt-get install -y -qq postgresql valkey-server
pip install -q -r "$(dirname "$0")/requirements.txt"
PGD=/var/lib/postgresql/anima-sb
mkdir -p "$PGD" && chown postgres "$PGD"
if [ ! -d "$PGD/pg" ]; then su postgres -c "/usr/lib/postgresql/16/bin/initdb -D $PGD/pg -A trust -U anima >/dev/null"; fi
su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D $PGD/pg -o '-p 5433 -k /var/run/postgresql' -l $PGD/pg.log start" || true
pgrep -x valkey-server >/dev/null || valkey-server --port 6380 --daemonize yes --save ""
sleep 2
psql -h /var/run/postgresql -p 5433 -U anima -d postgres -qtc "SELECT 1 FROM pg_database WHERE datname='anima'" | grep -q 1 \
  || psql -h /var/run/postgresql -p 5433 -U anima -d postgres -qc "CREATE DATABASE anima"
echo "sandbox ready: python demo/run_demo.py --reset --pace 1.5"
