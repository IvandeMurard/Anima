# Roadmap — Anima, hackathon day (22 Oct 2026)

> Single source of truth for who does what today. Tick boxes in commits; the repo is how we share information.
> **Hard deadline: 14:30.** Everything (deploy, videos, pitch) is done by then. These times replace the ones in `CLAUDE.md` and `SCENARIO.md`.
> Scope: Anima only (one node of the [Hospitality Multi-agent Architecture](https://github.com/IvandeMurard/Hospitality-Multi-agent-Architecture)). Synthetic data only.

**Owners:** `Ivan` (product, data, pitch) · `Collab` (build) · `AI` (Claude Code, always reviewed by a human before merge)

## Main message

**What hotel amnesia costs the hotel.** A regular who already complained is caught out at the desk, the front desk improvises, the hotel compensates, and the regular quietly doesn't come back. Then the "why now": hotels are plugging AI agents into guest data and fear liability and privacy. Guest comfort (35 min, a quiet room) is the illustration, not the headline.

## Timeline at a glance

| Time | Phase | Outcome everyone can see |
|---|---|---|
| 10:20 → 10:50 | **T0 — Aiven setup + framing** (no code) | Services running, GitHub connected, URIs in a local `.env` |
| 10:50 → 11:30 | **T1a — Walking skeleton** | A public URL on Aiven Runtime that says "Postgres ✓ Valkey ✓" |
| 11:30 → 12:30 | **T1b — Screens 1-4** | Replay of the morning: timeline, cards, memory panel |
| 12:30 → 12:40 | Safety video 1 | Recording of T1b |
| 12:40 → 13:45 | **T2 — Agent loop + memory hygiene** | LLM parser scored (AC1), screens 5-7, Validate, before/after; stale + contradiction on screen |
| **13:45** | **Freeze** | No new feature after this |
| 13:45 → 14:00 | Safety video 2 | Full replay recorded |
| 14:00 → 14:30 | Rehearse + submit | Pitch twice, links and videos submitted |

**Cut by default, only if ahead at 13:15:** voice brief, withdraw-consent button, screen 9. Never cut stale/contradiction (the challenge names them).

---

## T0 — Aiven setup (10:20 → 10:50, people, not code)

The AI cannot do this part: it needs console logins and admin rights. Start the services first, they take 5-10 minutes to come up.

1. [ ] `Ivan` Sign in at [console.aiven.io](https://console.aiven.io), join the hackathon organisation/project, check the team credits are applied
2. [ ] `Ivan` Create **Aiven for PostgreSQL**: name `anima-pg`, smallest plan, a European region (e.g. Paris/Frankfurt). Start it now
3. [ ] `Ivan` Create **Aiven for Valkey**: name `anima-valkey`, smallest plan, same region. Start it now
4. [ ] `Ivan` (org admin) Connect GitHub to the Aiven organisation and grant access to `IvandeMurard/Anima`. **This blocks every deploy; do it while the services start**
5. [ ] `Ivan` Add `Collab` to the GitHub repo with write access
6. [ ] `Ivan` When both services are *Running*, copy each **Service URI** into a local `.env` (git-ignored), never into the repo:
   ```
   DATABASE_URL=postgres://avnadmin:…@anima-pg-….aivencloud.com:PORT/defaultdb?sslmode=require
   VALKEY_URL=rediss://default:…@anima-valkey-….aivencloud.com:PORT
   ```
   Share them with `Collab` through a private channel
7. [ ] `Ivan` or `Collab` Smoke test from a laptop against Aiven (on Windows set `PYTHONUTF8=1` first):
   ```
   python reference/replay.py
   python demo/run_demo.py --reset
   ```
   Both must print `ALL PASS`. If `--reset` fails on `DROP SCHEMA public` or `FLUSHDB`, tell `AI` (fallback: drop the tables by name)

   On Windows, create the virtualenv **outside `%TEMP%`**: Windows application control blocks psycopg's compiled library there ("DLL load failed").
8. [ ] `Ivan` or `Collab` Check the T1a app against Aiven locally: `uvicorn app.main:app --port 8080`, open http://localhost:8080, expect "Postgres ✓ Valkey ✓"

**Framing (Ivan, same slot):**
- [ ] Read `research/` (BMAD discovery, in progress) and confirm the main message above; log it below
- [ ] Book 1-2 hotelier calls (script in `PITCH.md`). Ask what a room-related complaint from a regular costs them

## T1a — Walking skeleton (10:50 → 11:30)

Why first: Aiven Runtime is the riskiest unknown (new product, limited availability). Deploy something trivial, then build on a pipeline we know works.

- [x] `AI` `Dockerfile` (python:3.12-slim, `EXPOSE 8080`), `.dockerignore`, root `requirements.txt`, minimal FastAPI app with `GET /api/health` (Postgres `SELECT 1`, Valkey `PING`). Tested locally without stores; not yet against Aiven, Docker build not yet run
- [ ] `Ivan` Aiven console → **Runtime → Deploy application** → repo `IvandeMurard/Anima`, branch `main` → scan (it reads the port from `EXPOSE`) → deploy
- [ ] `Ivan` Application → **Connected services** → add `anima-pg` and `anima-valkey`. They arrive as `DATABASE_URL` and `VALKEY_URL` by default, which is what the code reads
- [ ] `Ivan` Open the public URL, see "Postgres ✓ Valkey ✓"

Pushing to GitHub does **not** redeploy: after every merge, click **Deploy latest commit**.

**Done when:** the public URL answers and both stores are green.

## T1b — Screens 1-4 (11:30 → 12:30)

- [ ] `AI` Refactor the `demo/run_demo.py` loop into `run_day(pg, vk, emit, reset, pace)`; CLI output unchanged; fresh planner state per run
- [ ] `AI` API: `POST /api/replay` (one run at a time), `GET /api/stream` (server-sent events, late joiners get the whole run)
- [ ] `AI` Page: timeline (raw inputs in original French) · recommendation card with citation chips · memory panel "What Anima knows about Claire" read from the stores (Postgres = durable, Valkey = until check-out) · global banner (blocked inferences, expired memories, no names) · live-vs-recorded strip
- [ ] `Collab` Review the page against `SCENARIO.md` screens 1-4, fix copy and layout
- [ ] `Ivan` Deploy latest commit, run the replay on the Aiven URL

**Done when:** oracle and CLI demo print `ALL PASS`; on the Aiven URL screens 1-4 match `SCENARIO.md`; the end-of-day checks panel shows `ALL PASS`; the parser is labelled "golden (recorded)".

## T2 — Agent loop + memory hygiene (12:40 → 13:45)

- [ ] `AI` + `Ivan` `PARSER=llm`: Claude, strict JSON, checked against `target`; `Ivan` owns the prompts and reviews failures
- [ ] `AI` Score with `python eval/parse_eval.py` → report the real % (target ≥ 90 %, AC1). Never report the golden 100 %
- [ ] `AI` Screens 5-7, before/after table framed as **what the hotel loses** (columns: "ignores her note", "honours the note, nobody re-plans", "Anima")
- [ ] `AI` Stale banner (screen 1), confirmation +1 (screen 7), contradiction (screen 10)
- [ ] `AI` Validate button writes `validated_by` / `validated_at` on `decisions` (AC8)
- [ ] `Collab` End-to-end review on the Aiven URL
- [ ] Only if ahead at 13:15: withdraw-consent button (screens 8, 11; never display Hugo's counterfactual), screen 9, voice brief (ElevenLabs, off by default)

## Pitch track (Ivan, in parallel all day)

- [ ] Rewrite the first 20 seconds around **what it costs the hotel** (regular caught out at the desk, compensation, lost repeat business), using the strongest sourced quote from `research/`
- [ ] Fill `PITCH.md` placeholders: `[N]` hoteliers, `[quote]`, `[€X]` per room per month. If there are no calls, say so plainly
- [ ] Live-vs-recorded table ready for the final screen
- [ ] Rehearse twice after the freeze

---

## What the AI can and cannot do today

### Claude Code (our build assistant)

| Can | Cannot / must not |
|---|---|
| Write and refactor code, Dockerfile, tests, docs | Log into Aiven, create services, connect GitHub, click Deploy |
| Run the oracle and the demo locally, against Aiven if given the URLs in a local `.env` | Hold or commit credentials; enter passwords anywhere |
| Draft and score the LLM parser prompts with `eval/parse_eval.py` | Report the golden parser's 100 % as a result |
| Research with sources (quotes, studies) and flag their strength | Invent quotes, traction, hotel partners or statistics |
| Draft pitch text and the roadmap | Decide scope cuts or the framing; that is Ivan's call |
| Prepare commits and branches | Push or merge without a human saying yes |
| Review diffs for bugs | Change the planner's decisions to make the demo look better (change `data/generate.py` and keep the oracle green instead) |
| | Call hoteliers, record the safety videos, pitch on stage |

### Anima's own AI (what the product does)

| The LLM does | The LLM never does |
|---|---|
| Turn raw inputs (French WhatsApp, housekeeping texts, webhooks) into a structured event + **proposed** claims, strict JSON | Write memory directly (a rule gate accepts or refuses every proposal) |
| Explain a recommendation with citations | Pick a room (the deterministic planner does) |
| Write the 2-sentence front-desk brief | Act without a human click |
| | Infer emotions, process audio or voice input, store anything a guest did not declare |

---

## How we work

- The repo is the shared channel: decisions, research and status live in files here, not in chat.
- Short branches, merged to `main` often; Aiven deploys from `main` (*Deploy latest commit*).
- After any change to data or planner: `python reference/replay.py` and `python demo/run_demo.py` must both print `ALL PASS`.
- Synthetic data only. No real names, phone numbers or messages, ever.

## Decision log

| Time | Decision | Why | By |
|---|---|---|---|
| 10:25 | Scope: Anima only, not the wider mesh | One node, one demo, one day | Ivan |
| 10:25 | Hard deadline 14:30; T3 merged into T2, voice / withdraw button / screen 9 cut by default | Time | Ivan |
| 10:25 | Main message: what hotel amnesia costs the hotel; guest comfort is the illustration | Pain felt as too weak when framed on the guest | Ivan |
| 10:25 | Deploy a walking skeleton before building screens | Aiven Runtime is the riskiest unknown | Ivan |
