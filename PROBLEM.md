# Anima — Problem, success, acceptance criteria, KPIs

> Status: hackathon build (Accel AI Innovate Paris, 22 Oct 2026, challenge "Data-Centric Agents"). Synthetic data only. Nothing here is validated with a live hotel yet.

## 1. The problem

**Hotels make guests pay for their own amnesia.**

Every hotel says it knows its guests. In practice, what a guest tells the hotel doesn't reach the moment it matters. It gets lost in two places:

1. **Between stays.** Memory lives in one receptionist's or concierge's head, and leaves when they do. The guest asks for a quiet room, and on the next stay has to ask again.
2. **Within a day.** Information gets lost in the handoff between front desk, housekeeping and maintenance. The guest said they'd arrive early; housekeeping never knew; the room they were promised turns out to be broken, and they find out at the desk.

**And the fix the market is heading for makes it worse.** AI agents are entering hotel systems and traveller apps. The default way an agent "remembers" a guest is to profile them: infer, aggregate, keep everything. That's exactly what hotels fear most, and what guests didn't agree to.

**Anima's position:** a hotel should remember **only what the guest actually said**, act on it while the day changes, and forget it on schedule.

### Who has the problem

| | Guest | Hotel (the buyer) |
|---|---|---|
| **Who** | Returning guests and anyone who tells the hotel something ahead of arrival | Independent and boutique hotels, 20-80 rooms, on modern cloud PMS (Apaleo, Mews). User: the front-office team. Buyer: GM or owner |
| **What they live** | Repeating themselves, waiting for a room, getting the wrong one, nobody coming back to them | Front desk improvising at the counter, complaints, compensation gestures, regulars who quietly don't come back |
| **What it costs them** | Time, and the feeling of being a stranger at a place they chose again | Front-desk time, room-related complaints, lost repeat business, and GDPR exposure as soon as AI starts "remembering" |

### Evidence — and how strong it is

| Evidence | Strength |
|---|---|
| **Our recorded scenario** (synthetic, `reference/replay.py`): with the preference remembered but nobody re-planning, Claire waits **35 min** for a room that was found broken at the desk, and has to ask for quiet a **3rd** time. With Anima: **0 min**, **0** repeated requests. | Measured, reproducible, synthetic. Shows the mechanism, not the market. |
| **Mews, 2022** (UK travellers, methodology not published): 59 % of returning guests were not recognised as returning; 19 % took their business elsewhere because of it; 47 % would share personal information for a personalised service. | Vendor survey, old, UK only. Directional. |
| **h2c AI Opportunity Study 2026** (122 responses, 113 hotel chains, sponsored): top concerns about guest-facing autonomous AI are liability for errors (56 %), data privacy (54 %), guests' willingness to share data (53 %). 70 % expect proactive AI agents to be a key innovation area within two years. | Recent, hotel-side, chains not boutique hotels, sponsored. |
| **Hotelier interviews** | **None yet.** Get one quote today (call script in `PITCH.md`). This is the weakest link. |

Deliberately not used: "room readiness costs up to 15 % of revenue" (Access Hospitality 2026, no published methodology) and older small polls on room readiness.

## 2. What success looks like

| Horizon | Success means |
|---|---|
| **Today (demo, 16:00)** | A judge watches one day at a hotel and sees, in under 2 minutes: the guest says something once; the agent acts on it while the day changes (train, housekeeping, broken tap); it refuses a guess it was handed; it forgets on schedule. The before/after is on screen: 35 min → 0. Running on Aiven, with what is live and what is recorded labelled. |
| **30-day pilot (one boutique hotel)** | Front desk follows most recommendations without being asked to; returning guests stop repeating declared needs; room-related complaints drop against the previous month; zero data stored that a guest didn't declare. |
| **12 months** | Distributed through PMS marketplaces (Apaleo, Mews). Anima is the memory layer hotel agents go through: what they may remember, for how long, and why. |

**What would prove us wrong:** front desks ignore the recommendations, or a month of pilot shows no drop in repeated requests or room-related complaints, or guests refuse to declare anything.

## 3. Acceptance criteria — today's build

Each criterion is testable. "Oracle" means `reference/replay.py`; "demo" means `demo/run_demo.py`.

| # | Given | When | Then | Checked by |
|---|---|---|---|---|
| AC1 | The 8 raw inputs (French WhatsApp, housekeeping text, PMS webhooks, tickets, rail JSON) | The LLM parser runs live | ≥ 90 % of fields match the golden targets | `eval/parse_eval.py` |
| AC2 | An attribute pushed by an external agent with `origin: inferred` | The agent tries to write it | It is refused; the refusal is logged without any guest id; nothing appears on the guest's memory panel | oracle #1, demo checks |
| AC3 | Claire's ETA changes to 11:15 via WhatsApp | The message is processed | Her room is moved to the front of the housekeeping queue; ready 10:30 instead of 11:50; the card cites C003 and C005 | oracle #3 |
| AC4 | Room 206 goes out of service at 10:20 | The maintenance input is processed | She is re-planned to 305, ready 11:10, with no wait and no lesser room offered | oracle #5 |
| AC5 | A durable claim not confirmed for 36 months | Day start | It is deleted (SQL on Postgres) | oracle #1, demo checks |
| AC6 | Malik declines the move ("pas la peine, je vais au concert") | The reply is processed | A this-stay claim wins for tonight; his durable "quiet" claim is kept and flagged to reconfirm; the held room is released | oracle #10, demo checks |
| AC7 | Hugo withdraws consent | The withdrawal is processed | His memory is gone from Postgres and Valkey; at 17:00 he is placed with no memory used | oracle #8, #11, demo checks |
| AC8 | Any recommendation | It is shown | It waits for a human click; nothing is executed automatically | oracle (R4) |
| AC9 | The whole day | It is replayed | End to end in under 2 minutes, deployed on Aiven Runtime with Postgres + Valkey, with a live-vs-recorded table on screen | demo + deploy |

**Definition of done for the demo:** AC1-AC9 pass, the oracle prints `ALL PASS`, the demo prints `ALL PASS`, a safety video is recorded.

## 4. KPIs

| Layer | KPI | Today (recorded scenario) | Pilot target (hypothesis) |
|---|---|---|---|
| **North star (guest)** | Declared needs a guest had to repeat, per stay | 3 → 0 | 0 for returning guests with consent |
| Guest | Minutes waiting for a room that fits what they declared | 35 → 0 | Median 0 for arrivals that declared an ETA |
| Hotel | Recommendations accepted by the front desk | n/a | ≥ 70 % (below that, the product isn't trusted) |
| Hotel | Room-related complaints per 100 arrivals | n/a | Down vs the previous month |
| Hotel | Front-desk minutes per arrival | n/a | Down vs baseline (measure in week 1) |
| Agent | Parser field accuracy on the golden set | Measured live today (AC1) | ≥ 95 % on the hotel's real message mix |
| Agent | Decisions matching the oracle | 100 % (11/11 events) | 100 % on replayed days |
| **Trust guardrails** | Inferred claims stored | 0 | 0, always |
| | Claims past retention still stored | 0 | 0, always |
| | Actions executed without human validation | 0 | 0 until a separate decision says otherwise |
| | Time from consent withdrawal to deletion | Immediate (same transaction) | < 1 min |

## 5. Out of scope today

Real guest data · real PMS integration (Apaleo sandbox comes later) · voice input or any audio processing (DPIA) · emotional inference · autonomous actions · pricing and billing.

## 6. Assumptions to validate (in this order)

1. Front desks lose guest requests in handoffs often enough to care. *(Hotelier quote today.)*
2. A front desk will act on a recommendation it didn't ask for if it shows why. *(Pilot acceptance rate.)*
3. Guests will declare needs when they see what is kept and can withdraw it. *(Pilot declaration rate.)*
4. Hotels will pay per room per month for this, through their PMS marketplace. *(Pilot conversion.)*
