# Submission texts — ready to paste (do not submit without Ivan)

> Drafted 22 Oct 2026 for the "Data-Centric Agents" challenge. Product numbers come from `eval/PARSER_REPORT.md` and `demo/run_demo.py`; research figures from `research/`, with their flags. Before pasting:

## Project name

Anima

## One-line pitch (≤ 120 characters)

Guest memory for hotel AI agents: keeps only what guests said, forgets on schedule, re-plans the stay, a human decides.

*(119 characters.)*

## The data layer in action

Anima is a hotel agent whose behaviour is defined by its data: what a guest declared, for which purpose, until when, and what is happening in the hotel right now. Remove the data and it does nothing, which is the point.

**What data the agent uses**
- **Declared guest claims** ("asks for a quiet room", "arrives around 11:15", "works on arrival"), each with its origin (always `declared`), source (front-desk note, pre-arrival form, WhatsApp), the purpose the guest consented to, and an expiry. Inferred attributes are refused at write time.
- **Live hotel context:** PMS webhooks (check-outs), housekeeping texts, maintenance tickets, rail status, local events. These move the plan; they are never stored as guest facts.
- **Decisions:** every recommendation, the claim ids it cites, and who validated it, when.

**Where it lives (Aiven)**
- **Aiven for PostgreSQL — durable memory and audit trail.** `claims` (declared only, enforced by a `CHECK` constraint), `consents` (one row per purpose), `decisions` (with `validated_by` / `validated_at`), `events`, and `refusals`, which has **no guest id column** by design. Durable memory expires by SQL: `expires_at` is computed as 36 months after the last confirmation, and a sweep deletes what has expired. Withdrawing consent deletes the guest's memory by cascade, in one transaction.
- **Aiven for Valkey — this-stay memory and the live day.** Stay-only claims sit in a hash per reservation whose **TTL is the check-out time**, so the datastore forgets them by itself. Raw inputs are appended to a Valkey stream (`XADD`) and the agent loop reads them in order (`XREAD`).
- **Aiven Runtime** runs the FastAPI app and the agent, connected to both services.

**How it flows**
1. A raw message arrives (guest WhatsApp, housekeeping text, PMS webhook, ticket, rail status) and goes onto the Valkey event stream.
2. The LLM parses it into a structured event plus *proposed* claims (strict JSON schema). It never writes memory.
3. A rule gate accepts or refuses each proposal: declared and consented → written to Postgres (durable) or Valkey (this stay); inferred → refused and counted, with no name attached.
4. The agent reads only declared, consented, unexpired memory, calls the deterministic planner (room, housekeeping order, ready time), and the card shows its reasons as citations to claim ids and context sources.
5. The front desk validates with one click; the decision is logged. Confirmations ("the courtyard side, perfect") strengthen a claim and restart its clock; contradictions keep the durable claim and flag it to reconfirm, instead of silently overwriting it.
6. Each tool gets only what it needs: housekeeping receives "clean 206 first by 10:30", never why. A data ledger on every recommendation shows what was used, refused, forgotten, and shared with which tool.
7. Anticipation is "ask, don't assume": the agent turns a declared need plus context into a question for the guest, and stores nothing until the guest confirms.

**Forgetting is a feature of the data layer:** stay memory dies at check-out by Valkey TTL; durable memory expires after 36 months unconfirmed by SQL in Postgres; consent withdrawal deletes immediately.

## Evidence it works

Recorded scenario: one synthetic day at a 24-room hotel at 87 % occupancy, 07:00 to 17:00, replayed end to end. Memory writes, expiry, refusals and decisions run live on Aiven Postgres and Valkey.

| What | Result |
|---|---|
| **Outcome vs a no-re-planning baseline** | The baseline remembers the guest's need but nobody re-plans: she waits **35 min** for a room found out of service at the desk. Anima: **0 min**, in a room ready 5 minutes before she arrives. Times she has to repeat a declared need: **3 → 0**. Computed by the oracle (`reference/replay.py`), not hand-written. |
| **Parser accuracy** | Live model outputs on the 8 raw inputs of the day (29 scored fields): **97 %** on the first, untuned prompt (French inputs). After tuning the prompt on this scenario: 100 % on 3 consecutive French runs, and **29/29** on one run of the English rewording of the same messages. There is no held-out set, so read it as "works on our day", not a benchmark; 97 % is the honest figure for new messages. Structured fields (times, rooms, ids) were never wrong; misses were wording in free text. Target was ≥ 90 %. |
| **Cost** | ≈ **$0.009 per message** (≈ $0.074 for the day's 8 messages). The planner is deterministic code. |
| **Latency** | ≈ **1.5 s** median per message; the 8 messages of the day parse in 14-17 s. The first call after a deploy is slower (up to ~11 s while the output schema compiles), so we send one warm-up message. |
| **Decisions** | 11 of 11 scenario events match the oracle's expected decision (`reference/replay.py` prints `ALL PASS`). |
| **Checks on the live stores** | 9/9 pass (`demo/run_demo.py`): stale claim deleted by the SQL expiry sweep; claim confirmed 3 times; contradicted claim kept and flagged; memory deleted by cascade on consent withdrawal; refusal log has no guest id column; decisions logged; only declared claims stored; baseline matches the oracle (35 min); this-stay memory expires by itself (Valkey TTL). |
| **Trust guardrails** | **0** inferred attributes stored · **0** actions without a human click · consent withdrawal deletes in the same transaction. |

What is live and what is recorded: the hotel, guests and day script are a recorded synthetic scenario; parsing, memory operations, expiry, refusals and decisions are live. No real guest data, phone numbers or hotel systems are involved.

## The one pitch slide

**Anima — guest memory for hotel AI agents that only keeps what guests said**

**Who:** front-office teams of independent and boutique hotels (20-80 rooms) on cloud PMS (Apaleo, Mews). The hotel pays; the front desk uses it; the guest sees and controls what is kept.

**The problem — the hotel pays for amnesia three times:**
- The gesture: a study found it takes about **80 % of the room price** to win a guest back to neutral after their room wasn't what they booked *(scenario experiment, Sweden, 2022)*.
- The regular: **19 %** of UK guests who weren't recognised as returning took their business elsewhere *(Mews, vendor survey, 2022)*.
- The staff: Cornell found a front-desk departure costs **30 % of salary**, and co-workers lose 20 % of their productivity for up to 16 days *(2006, US)*. What they knew about the regulars leaves with them *(our claim)*.

**Why now:** hotels are plugging AI agents into guest data, and the default way that AI remembers is by profiling. Hotels' top fears about guest-facing AI are **liability (56 %)** and **privacy (54 %)** *(h2c 2026, 113 chains, sponsored)*. Guests accept AI using what they said (**61 %**) far more than data gathered about them (**34 %**) *(Mews, July 2026, 3,250 travellers incl. France, vendor)*. The CNIL has already fined **Accor €600,000** over consent taken at booking *(2022)*. Remembering is becoming free (Oracle OPERA, Revinate, Twilio); governed memory isn't.

**How we reach first users:** 3 Paris boutique hotels as design partners (target; none signed yet, no hotelier interviewed yet), then distribution through the PMS marketplaces hotels already buy from (Apaleo, Mews), priced per room per month. Next steps: a real WhatsApp line after a DPIA, MCP connectors into the PMS and staff tools, one 30-day pilot measuring repeated requests, room complaints and gestures given.

## Links

- **GitHub repo:** https://github.com/IvandeMurard/Anima
- **Demo:** https://01a16305-f79d-72fb-adbc-726cf35ecd80-8080.eur-1.aiven.app
