# Architecture for the challenge — "Data-Centric Agents" on Aiven

The challenge asks for agents that **reason over, act on and learn from changing data**, deployed on **Aiven Runtime** with Aiven data services. Judging: customer problem, agent capability, data at the core, evidence, pitch. Separate Aiven prize for best use of the platform.

## The agent loop (answers "Agent Capability")

The decision core (`reference/replay.py`) is a **tool**, not the product. The agent orchestrates:

```
raw input arrives (WhatsApp, HK app text, PMS webhook, ticket, rail API)
  1. parse_input(raw)            -> structured event + PROPOSED claims        [LLM]
  2. write_claim(proposal)       -> accepted / refused by rule R2 (logged)    [rule gate]
  3. read_memory(guest, scope)   -> only declared, consented, non-expired     [Postgres + Valkey]
  4. plan_room / plan_move(...)  -> recommendation + citations + wait         [deterministic tool]
  5. explain(recommendation)     -> card text + 2-sentence brief, cites ids   [LLM]
  6. request_validation(card)    -> waits for a human click                   [UI]
  7. on human answer / new event -> loop; confirmations update memory (R9)
```

Multi-step, tool-using, event-driven, with memory that expires, gets reconfirmed and resolves contradictions. The LLM never writes memory or picks a room directly.

## Aiven services — one job each

| Service | Holds | Why this service |
|---|---|---|
| **PostgreSQL** | Durable memory (`claims`), consents per purpose, decisions, refusal log, event log, rooms, housekeeping jobs | Relational truth, audit trail, retention by SQL (`expires_at`) |
| **Valkey** | This-stay memory (`stay:{res_id}:claims`) with **TTL at check-out**; the live event stream (Valkey Streams `XADD events`); the housekeeping queue (sorted set) | Working memory that *expires by itself* = R9 enforced by the datastore, not by code |
| Kafka (optional) | Event stream, if the team prefers it to Valkey Streams | Only if someone on the team knows it. Don't add services for the prize. |
| ClickHouse / OpenSearch | Not needed | Say so if asked: we used what the data needed. |

Story for the Aiven prize: **"Forgetting is a feature of the data layer."** Stay memory dies at check-out by TTL in Valkey; durable memory expires after 36 months by SQL in Postgres; withdrawal deletes in one transaction.

## Data model — see `schema.sql`

- `claims(claim_id, guest_id, key, value, origin CHECK (origin='declared'), source, purpose, layer, first_seen, last_confirmed, confirmations, expires_at, needs_reconfirm)`
- `consents(guest_id, purpose, given, via)` — one row per purpose
- `refusals(day, attribute, origin, source, count)` — **no guest_id column**
- `decisions(id, at, guest_id, room, ready_by, cites[], alternative, validated_by, validated_at)`
- `events(seq, at, type, source, payload jsonb)`
- Valkey: `stay:R-G001:claims` (hash) `EXPIREAT` check-out timestamp; `events` (stream); `hk:queue` (sorted set by priority)

## Deploy on Aiven Runtime (checked against Aiven docs)

1. Code in a **GitHub repo** with a **Dockerfile** at the root (FastAPI + static front, or front on Vercel calling the API).
2. Create PostgreSQL and Valkey services in the Aiven console (team credits).
3. Runtime → *Deploy application* → pick repo/branch → scan → deploy.
4. Connect services to the app (*Connected services*): map Postgres to `DATABASE_URL`, Valkey to `VALKEY_URL`.
5. Pushing to GitHub does **not** redeploy: use *Deploy latest commit*. Budget 10 minutes for the first deploy and do it **before 12:00**, with T1.

Someone with admin rights must connect the GitHub account to the Aiven organisation: do it at 09:15, not at 15:30.

## Live vs recorded (the rules ask for this explicitly)

| Part | Status in the demo |
|---|---|
| Hotel, guests, day script | **Recorded scenario**, synthetic, safe to share |
| Parsing of the raw inputs by the agent | **Live** run, scored by `eval/parse_eval.py` (% of fields correct) |
| Memory writes, expiry, refusals, decisions | **Live** on Aiven Postgres + Valkey |
| Before/after (35 min vs 0) | Computed live by the oracle on the recorded scenario |
| Voice brief (if on) | Live TTS of a generated text |

Put this table on screen for 5 seconds at the end of the demo.
