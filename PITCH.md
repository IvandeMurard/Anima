# Pitch material (v4 — challenge: Data-Centric Agents)

## BuilderBase — Create a Team (do not submit without Ivan)

**Team name:** Anima

**Problem statement** (439 / 500 characters):

> Hotels have amnesia. What they know about a guest lives in one person's head, so guests repeat themselves every stay, and the AI agents now entering hotel systems are about to fix it the worst way: profiling people who never agreed to it. Anima is a guest memory that keeps only what guests said, fuses it with live hotel context (rooms, housekeeping, trains, local events) and re-plans the stay as reality changes. A human always decides.

**Open team:** ✅ (visible in the team browser).

## The one pitch slide (required by the challenge: who, why now, first users)

**Anima — memory for hotel agents that only keeps what guests said**

- **Who:** front-office teams of independent and boutique hotels (20-80 rooms) on modern PMS (Apaleo, Mews). The guest feels it; the front desk uses it.
- **Why now:** hotels are plugging AI agents into their systems (Apaleo shipped the first PMS MCP server in 2025; 70 % of respondents from 113 hotel chains expect proactive AI agents to be a key innovation area within two years). Their top three fears about guest-facing AI: liability for errors (56 %), data privacy (54 %), guests' willingness to share data (53 %) — h2c AI Opportunity Study 2026, sponsored, chains only.
- **First users:** 3 Paris boutique hotels as design partners from [hotelier calls]; then distribution through the Apaleo and Mews marketplaces, priced per room per month ([€X], to test).
- **Evidence (from the demo):** 35 min wait → 0 on the recorded day; [X] % of fields correctly extracted from messy French inputs (live, `eval/parse_eval.py`).

## How we answer each judging criterion

| Criterion | Our answer on stage |
|---|---|
| Customer problem & value | Guests repeat themselves; requests die in the handoff between front desk, housekeeping and maintenance. [Hotelier quote.] |
| Agent capability | Multi-step tool loop: parse → rule-gated write → memory read → planner tool → explanation → human validation; reacts to an event stream. |
| Data at the core | Memory that expires (Valkey TTL, 36-month SQL rule), gets stronger when confirmed, resolves contradictions, refuses inferences. Remove the data and the agent is useless — that's the point. |
| Evidence | Before/after vs a no-re-plan baseline (35 → 0 min); parser accuracy on golden targets; oracle tests that fail when data is broken. |
| Execution & pitch | One front-desk screen, three beats, before/after table, live-vs-recorded table. |

## Team pitch — 60 seconds (09:00, or in BuilderBase messages)

> Hotels forget their guests. Someone asks for a quiet room on two stays and still has to ask again on the third. I've spent the past year building agentic systems for hotels, and I've prepared a full synthetic hotel day: 24 rooms at 87 % occupancy, a French WhatsApp message, a housekeeping text, a leaking tap, a concert, and a reference planner that already passes every decision of the day and shows what re-planning saves. Today we build the agent that reads the mess, remembers only what guests said, and re-plans the stay live, with voice briefs for the front desk. I need a frontend person and a backend/AI person. You'll have something real on screen by noon.

## 3-minute pitch (16:00)

| Time | Beat | Content |
|---|---|---|
| 0:00-0:20 | **Problem** | "Hotels have amnesia." Claire asked for a quiet room twice and waited 2 hours last time; the PMS just put her on the street side, under tonight's concert. |
| 0:20-0:40 | **Why now** | AI agents are entering hotel systems: PMS platforms now expose them directly (Apaleo shipped the first PMS MCP server in 2025), and travellers are starting to use AI agents of their own. Agents will act on guest data. The rules exist (GDPR); nobody enforces them where agents read the data. |
| 0:40-2:00 | **Demo** | Screens 1, 3, 5, 6, then the before/after table: PMS rule = street side; memory without re-planning = 35 min wait in a broken room; Anima = 0 min. Say the three beats. |
| 2:00-2:30 | **Why it's different** | Not another guest profile: memory with rules. Only what guests said, refused guesses shown, consent you can withdraw on screen, a human validating every move. Data-protection assessment written *before* any real guest. |
| 2:30-3:00 | **Status + ask** | Honest status: synthetic data, no hotel connected yet. What [N] hoteliers told us this week: [quote]. Next: one pilot with an independent hotel on Apaleo or Mews. Ask: intros to boutique hotel groups. |

Fill [N] and [quote] from the calls. **If there are none, say so plainly.** Never fake traction.

## Judges' questions — one-line answers

| Question | Answer |
|---|---|
| "My receptionist would have prioritised 206." | At 08:40, with eight departures and the queue running, the message sits in a WhatsApp inbox and nobody links it to the housekeeping queue. Anima does, and shows why. (Back it with a hotelier quote.) |
| "Sirma just launched hotel agents (Marta, Vela)." | Yes — orchestration across systems, built on years of integrations. Their announcement says nothing about guest memory or consent. We'd rather plug into an orchestrator like theirs than compete with it. |
| "Mews and Opera already store guest preferences." | Yes, in profile fields. Our bet, to be checked in this week's calls: those fields are filled unevenly and nothing acts on them while the day changes. Anima captures what guests say across channels, keeps it under consent rules, and re-plans with it. |
| "Then why won't the PMS build it?" | It might; that's why we plan to distribute through PMS marketplaces (Apaleo, Mews) rather than against them. Consent governance and cross-channel capture are the parts a PMS has the least incentive to build. |
| "Feature or company?" | Thesis: every hotel agent, ours or others', will need one consented memory layer it can be audited on. Test: one pilot hotel, measure repeated requests and room-related complaints over a month. What would kill it: front desks don't follow the recommendations, or a month of pilot shows no drop in repeated requests and room complaints. |
| "Who pays, how much?" | The hotel, as a per-room monthly subscription through the marketplace. Hypothesis: [€X] per room per month, to be tested in the pilot (Ivan sets X before the 22nd). |
| "Have you talked to hotels?" | Answer with the calls. |
| "Why you?" | Two years co-founding a B2G data SaaS, from discovery to MVP and a sales process; led a 10-tool consolidation onto one SaaS for 500+ users across 100+ care facilities; front-of-house experience in restaurants; a year building hotel agents on Apaleo. |
| "Why would guests share?" | We only ask for what changes their stay, show them what we keep, and let them withdraw it. That's the design; adoption is what the pilot measures. |
| "Privacy?" | Consent per purpose, separate from booking; declared claims only; 36-month retention, stay-only for stay needs; no emotional inference; no audio. DPIA written before any real data. |

**Removed on purpose:** survey statistics on data sharing (not comparable across studies) and named traveller-agent products (not verified). Only Apaleo's MCP server is a checked fact.

## Message to the organizers (BuilderBase messages or Luma)

> Hi! Looking forward to the 22nd. Two quick questions: (1) Can teams bring prepared synthetic datasets and design docs, or should all code be written on the day? (2) Will the challenge be announced before the event, or at kickoff? Thanks — Ivan

## Hotelier call script (10 min, ask in French if the hotelier is French)

Target: front-office managers or owners of boutique hotels (20-80 rooms). Ideally, one front-office manager also reads `SCENARIO.md` for 20 minutes.

1. "When a returning guest arrives, how do you know what they asked for last time?" (Where is it written? Who can see it? Is it filled in every time?)
2. "Tell me about the last time a guest had to ask again for something they had already asked for."
3. "A guest arrives at 11:00 instead of 15:00. What actually happens in the next hour?"
4. "What changes your room plan during a day?" (housekeeping, maintenance, departures...)
5. "If a tool suggested the right room, with the reason, who would validate it? How much time would they have?"
6. "What do you pay for this today, and who decides on the purchase?"

Write down **exact words**, not your interpretation. One real quote in the pitch beats any statistic.
