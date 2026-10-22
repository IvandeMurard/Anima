# Anima — hackathon kit (Accel AI Innovate Paris, 22 Oct 2026) — v4 (challenge: Data-Centric Agents, on Aiven)

**Hotels have amnesia.** Anima is a guest memory that keeps only what guests *said*, fuses it with live hotel context, and re-plans the stay as reality changes. A human always decides.

> ⚠️ **Synthetic data only.** Every guest is fake (`"synthetic": true`, `SYN-` names and numbers). Never add real guest data — production Anima is gated behind a DPIA.

## What's in the kit

| Path | What it is |
|---|---|
| `data/generate.py` | Builds the whole dataset (stdlib only). Edit here, never the JSON by hand. |
| `data/hotel.json` | Maison Lumen (fictional), 24 rooms: side, lift adjacency, category, desk. Housekeeping: 2 attendants on departures. |
| `data/guests.json` | 28 synthetic guests. 3 have memory. Every claim is **declared**, with source, purpose, layer and retention. Consent is recorded per purpose, each with its own date and channel. |
| `data/reservations.json` | 10 stayovers, 8 departures spread from 09:00, 10 arrivals → **87 % occupancy** (405 out of order). Only one arrival is locked (accessible room); the planner places all the others. |
| `data/housekeeping.json` | Room status at 07:00 + default cleaning queue. |
| `data/context.json` | World context: concert, train. **Never about a person.** |
| `data/events.json` | The day as 11 replayable events, each with the decision a correct system must make (`expect`). |
| `data/raw_inputs.json` | What the hotel *actually* receives (French WhatsApp, housekeeping text message, PMS webhooks, maintenance tickets, rail JSON) + a golden `target` per input for testing the LLM parser. |
| `reference/replay.py` | Deterministic reference planner (no LLM). Replays the day, checks every `expect`, and compares with a static plan (memory but no re-planning). **Our oracle.** It fails when the data is broken (checked by mutation). |
| `ARCHITECTURE.md` | Agent loop, Aiven services (Postgres + Valkey), deploy on Aiven Runtime, live vs recorded. |
| `schema.sql` | PostgreSQL schema: declared-only claims, consent per purpose, generated expiry, refusal log without guest id. |
| `demo/run_demo.py` | **Demo runner.** Replays the day through a Valkey stream; memory lives in Postgres + Valkey; the planner reads memory from the stores; cards on screen; end-of-day checks on the stores. Parser = golden stub until the LLM is plugged into `parse()`. |
| `demo/sandbox_setup.sh` | Local sandbox: PostgreSQL 16 + Valkey (same engines as Aiven). |
| `eval/parse_eval.py` | Scores the agent's parsing of raw inputs against the golden targets (field accuracy). `--self-test` included. |
| `PROBLEM.md` | Problem, evidence, what success looks like, acceptance criteria, KPIs. Start here. |
| `CLAUDE.md` | Context for Claude Code sessions on this repo. |
| `SCENARIO.md` | The demo screen by screen, the memory panel, build slices, roles, live variants. |
| `PITCH.md` | Problem statement, team pitch, 3-min pitch, judges' questions, hotelier call script. |

## Run

```bash
python data/generate.py      # regenerate the JSON
python reference/replay.py   # replay the day -> must print ALL PASS
python eval/parse_eval.py --self-test   # check the parser scorer
bash demo/sandbox_setup.sh              # local Postgres 16 + Valkey (Ubuntu/Debian)
python demo/run_demo.py --reset --pace 1.5   # the demo, through the data layer
# on Aiven: DATABASE_URL=... VALKEY_URL=... python demo/run_demo.py --reset
```

## Product rules (the reference planner enforces them)

| | Rule |
|---|---|
| R1 | **Consent first.** No consent → nothing personal is read. Withdrawal deletes the memory, live. |
| R2 | **Only what the guest said.** Memory stores declared claims under a consented purpose. Inferred attributes handed to Anima (e.g. by a traveller-side agent) are refused at the door; the refusal log keeps no link to the guest. |
| R3 | **Context is not a person.** Concerts, trains, maintenance inform decisions; they never become claims. A train is tracked only because the guest declared it. |
| R4 | **Human validates.** Anima informs, the planner recommends, a person clicks. No auto-action. |
| R5 | **No churn.** A re-plan keeps the current room if it still works. |
| R6 | **Lesser rooms only if the wait is > 30 min,** offered, never imposed. If no room meets every declared need, the planner says so and shows the least-bad options. |
| R7 | **In-house moves after 15:00,** once all arrivals are placed; the proposed room is held until a human decides. |
| R8 | **No silent upgrades.** Booked category first; an upgrade is flagged. |
| R9 | **Stale memory expires.** Not confirmed for 36 months → deleted at day start. A confirmation restarts the clock. |
| R10 | **Contradictions:** the newest declaration wins for this stay; the durable claim is kept and flagged to reconfirm. |

Housekeeping: work started before *now* is frozen; only the future is re-planned.

Retention: `working` claims end at check-out; `semantic` claims last 36 months rolling from their last confirmation.

## Where the LLM goes — and where it doesn't

- **Yes:** turn `raw_inputs` into structured events and *proposed* claims (tested against each `target`); write the explanation of each recommendation with citations; write the 2-sentence front-desk brief (text, or voice output).
- **No:** decide on its own, or write to memory directly. Proposals go through the write rule (R2). The decision core stays deterministic; the LLM version must reach the same decisions as `replay.py`.
- **Never:** process audio. No voice input (DPIA M-10). Voice output (TTS) only.
