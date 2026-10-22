# CLAUDE.md — Anima (hackathon build)

You are working on **Anima**, a guest memory for hotel AI agents, built at Accel AI Innovate Paris (22 Oct 2026), challenge **"Data-Centric Agents"** (agents that reason over, act on and learn from changing data; deploy on **Aiven Runtime**, data on Aiven services).

Read first, in this order: `PROBLEM.md` (problem, success, acceptance criteria, KPIs) → `SCENARIO.md` (the demo, screen by screen, build slices) → `ARCHITECTURE.md` (agent loop, Aiven Postgres + Valkey, deploy) → `README.md` (files, rules R1-R10) → `PITCH.md`.

## Non-negotiables

- **Synthetic data only.** Every guest is fake (`SYN-` names). Never add real personal data, real phone numbers or real messages.
- **Memory stores only what the guest declared**, under a consented purpose, with retention. Inferred attributes are refused at write time; the refusal log has no guest id.
- **No auto-action.** Every recommendation waits for a human click.
- **No audio processing, no voice input** (DPIA). Voice *output* (TTS brief) is optional and off by default.
- **No emotional inference.**
- All docs, code and comments in **English**. Guest and staff messages in the dataset are in English so judges read them instantly, kept messy like real input (typos, abbreviations, run-on texting). Decided 22 Oct 12:15; they were French before.
- Label honestly: what is live vs recorded; "synthetic", never "validated with hotels".

## Commands

```bash
python data/generate.py                       # regenerate data/*.json (edit generate.py, never the JSON)
python reference/replay.py                    # oracle: must print ALL PASS
python eval/parse_eval.py --self-test         # parser scorer self-test
python eval/parse_eval.py                     # score eval/predictions.json (written by the demo)
bash demo/sandbox_setup.sh                    # local Postgres 16 :5433 + Valkey :6380 (Debian/Ubuntu, root)
python demo/run_demo.py --reset --pace 1.5    # demo through Postgres + Valkey; must print ALL PASS
# on Aiven: DATABASE_URL=... VALKEY_URL=... python demo/run_demo.py --reset
```

## How the pieces fit

- `reference/replay.py` is the **decision core** (deterministic planner + world model + tests). The agent calls it as a tool. Do not change its decisions to make a demo look better: if an expectation must change, change `data/generate.py` and keep the oracle passing.
- `demo/run_demo.py` streams the day through Valkey, keeps memory in Postgres (`schema.sql`) and Valkey (this-stay memory with TTL at check-out), reads memory back from the stores, calls the planner, logs decisions, and checks the stores at the end.
- `parse()` in `demo/run_demo.py` is a **stub** (`PARSER=golden` replays golden targets). Today's main build task: implement `PARSER=llm` with strict JSON output, then score it with `eval/parse_eval.py` (target ≥ 90 % of fields, AC1). Never report the golden 100 % as a result.

## Today's priorities (see SCENARIO.md slices)

1. **T1 by 12:00:** deploy on Aiven Runtime (GitHub repo + Dockerfile, Postgres + Valkey connected via `DATABASE_URL` / `VALKEY_URL`), timeline + cards + memory panel for screens 1-4. Record safety video 1 at 12:30.
2. **T2 by 14:30:** LLM parser (AC1), screens 5-7, Validate button, before/after table.
3. **T3 by 15:30:** memory hygiene screens (stale, contradiction), withdraw consent, voice brief (optional, cut first).
4. **No new feature after 15:30.** Rehearse, record safety video 2, freeze.

## Working style

- Small, verifiable steps. After any change to data or planner: run the oracle and the demo; both must print `ALL PASS`.
- Prefer cutting scope over adding risk. Cut order if late: voice → withdraw button → screen 9. Keep stale/contradiction: the challenge names them.
