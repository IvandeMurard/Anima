# Demo scenario — "A day at Maison Lumen" (v4, challenge: Data-Centric Agents)

One front-office screen, three zones:
- **Left:** the day's timeline. Raw inputs arrive in their original form.
- **Centre:** the live recommendation card: what, why, from which source. It waits for a human click.
- **Right:** the **memory panel**, "What Anima knows about Claire".

We replay 22 Oct from 07:00 to 17:00 in about 2 minutes. The hotel is at 87 % tonight and departures are spread from 09:00, so housekeeping is genuinely busy.

## The story in one line

SYN-Claire Laurent asked twice for a quiet room, and last time waited 2 hours for it. Today the hotel remembers, refuses a guess it is handed, and keeps her plan true while her train, the housekeeping queue and a leaking tap change it.

## Before / after (final screen) — computed by `reference/replay.py`

| | PMS rule only | Preference known, queue not linked to it | **Anima** |
|---|---|---|---|
| Room | 402, street side, under tonight's concert | 206 — found **out of service** at the desk | **305**, courtyard, desk |
| Wait on arrival (11:15) | 0 min | **35 min** (305 ready 11:50 in the normal queue) — the exact failure she complained about | **0 min** (305 ready 11:10) |
| Times she has to ask for quiet | a third time | 0 | 0 |
| Malik in 302 (asked for quiet) | concert under his window | concert under his window | offered 206 at 16:40; he declines (going to the concert); his durable "quiet" is kept and flagged to reconfirm |

Say it out loud: remembering is not enough. The memory has to be *acted on* while the day changes.

**Prepared answer to "my receptionist would have prioritised 206":** "At 08:40, with eight departures and the queue running, the message sits in a WhatsApp inbox and nobody links it to the housekeeping queue. Anima does, and shows why." Back it with an exact hotelier quote (call script, question 3).

## Memory panel — "What Anima knows about Claire"

| Claim | Origin | Source | Purpose (consented on) | Kept until |
|---|---|---|---|---|
| Asks for a quiet room (C001) | declared ×2 | front desk note, pre-arrival form | stay personalisation (2025-03-14, front desk tablet) | 36 months after last confirmation |
| Works on arrival, needs a desk (C002) | declared | pre-arrival form | stay personalisation | check-out |
| Waited 2h last time, asked us to avoid it (C003) | declared | check-out feedback (our failure) | stay personalisation | 36 months |
| Arrives ~11:15 on TGV 6612 (C005, written live at 08:40) | declared | WhatsApp | arrival coordination (2026-10-19, pre-arrival form) | check-out |

The "prefers high floors" pushed by a traveller-side agent never reaches the panel. A **global banner** (not next to Claire's card) shows a counter: "1 inferred attribute blocked today". No name is attached to it.

**Memory hygiene, visible on screen (the challenge asks for stale and contradicting memories):**
- **Stale:** at 07:00 the global banner shows "1 memory expired (36 months without confirmation) and deleted" — Malik's old "late check-out" (C071, last confirmed May 2023).
- **Stronger:** at 11:15 Claire says "the courtyard side, perfect" → C001 goes to 3 confirmations, its 36-month clock restarts today.
- **Contradiction:** at 16:20 Malik replies "pas la peine, je vais au concert" → a this-stay claim wins for tonight; his durable "quiet" (C070) is **kept**, flagged "reconfirm next stay". Never silently overwritten.

A **Withdraw consent** button on each guest. We use it live on SYN-Hugo Martin at 14:00: his panel empties, and at 17:00 he is placed like a first-time guest.

## Screen by screen

| # | Sim. time | Raw input (left) | Card (centre) | Click |
|---|---|---|---|---|
| 1 | 07:00 | PMS pre-assigned **402**; a traveller-side agent pushes "prefers high floors"; expiry sweep runs | "Move to **206** (courtyard, desk, ready 11:50 for a 15:00 arrival). 402 faces the street and a concert runs there tonight [C001] [X-EVT-1]." Global banner: *1 inferred attribute blocked · 1 memory expired.* | Validate |
| 2 | 08:15 | PMS webhook: 206 leaves at 09:30 instead of 11:00 | No change. | — |
| 3 | 08:40 | **WhatsApp, in French:** "je prends le TGV de 9h04, je serai là vers 11h15…" | C005 appears in the panel. "She now arrives at 11:15. In the normal queue 206 is ready at 11:50 (35 min wait). Clean it first: ready 10:30. Last time she waited 2h [C003] [C005]." Queue view: 206 jumps ahead of 201, 203, 301, 404. | Validate |
| 4 | 10:05 | 305 checks out early | No change (R5). | — |
| 5 | 10:20 | **Housekeeping app text:** "206 salle de bain finie mais le robinet fuit…" + maintenance ticket (back 16:00) | "206 out of service. Switch to **305**: the attendant who just finished 206 takes it next instead of 203, ready 11:10, before she arrives." | Validate |
| 6 | 11:05 | Rail API: TGV 6612 arrived 10:52 (tracked only because she told us) | **Brief** (text, or voice if on): "Claire Laurent, third stay, arrives in about 10 minutes: she asked for a quiet room and is in 305, courtyard side, ready at 11:10. She told us she works on arrival, so the desk is set up and there is nothing to ask her again." | Play |
| 7 | 11:15 | Check-in; Claire: "the courtyard side, perfect" | ✓ 0 min wait, nothing asked twice. C001 → 3 confirmations, clock restarted. Before/after table. | — |
| 8 | 14:00 | SYN-Hugo Martin withdraws consent in the app | His panel empties, live. | — |
| 9 | 16:00 | Maintenance ticket: 206 resolved | "206 is back, ready 16:40. SYN-Malik Benali (302, street side) asked for a quiet room [C070]; concert at 20:00 [X-EVT-1]. Offer him 206?" | Human decides |
| 10 | 16:20 | **Guest app, in French:** "pas la peine de changer, je vais au concert, je rentre vers 1h" | "Offer withdrawn, 206 released. For tonight his newest word wins; 'quiet' (C070) kept, to reconfirm next stay." | — |
| 11 | 17:00 | Arrivals: Hugo (consent withdrawn), Tom (first stay) | Standard rooms, no memory used, nothing cited. | — |

**Three beats to say out loud:**
1. **Screen 3:** it read a messy French message and moved her room to the front of the queue: 35 minutes of waiting avoided.
2. **Screen 5:** a tap broke, and she never knew.
3. **Screen 1:** it refused a guess it was handed, because she never said it.

**The callback:** the room with the leak becomes the offer for Malik, and he says no. The memory handles it without forgetting what he asked for twice.

**For the frontend:** the counterfactual "with consent, Hugo would have had two extra pillows" exists only in the tests. Never display it: showing it would mean keeping data he asked us to delete.

## No live variant

We do not send live messages from a teammate's phone: that would put a real number and a real message into the system. If a judge asks "what if her train came in earlier?", answer verbally: no quiet room with a desk could be ready before 10:30, so the card would offer a day room to work in right away, then 206 at 10:30, and the front desk would choose (R6).

## Build slices (each one demoable)

| Slice | Done by | Contents | If we stop here |
|---|---|---|---|
| **T1** | 12:00 | Event replay, timeline, cards from the reference planner, memory panel (read-only), screens 1-4. **Deployed on Aiven Runtime with Postgres + Valkey** (see `ARCHITECTURE.md`) | "It remembers, refuses a guess, explains." Presentable. |
| **Safety video 1** | 12:30 | Screen-record T1 | Plays if everything breaks later. |
| **T2** | 14:30 | Agent loop (parse → write rule → memory → planner tool → explain), scored by `eval/parse_eval.py`; screens 5-7, Validate button, queue view, before/after table | The core of the pitch. |
| **T3** | 15:30 | Memory hygiene (screens 1 banner, 7, 10), withdraw button (screens 8, 11), screen 9, voice brief (ElevenLabs TTS, off by default) | Bonus — but memory hygiene is named in the challenge: cut voice first. |
| **Safety video 2** | 15:45 | Screen-record the full replay | Plays if the live demo breaks at 16:00. |

**"No fit" card template** (needed if the LLM parsing ever shifts the data): "No room meets every need she declared. Three options, and what each one gives up." Never pick silently.

**No new feature after 15:30.** If time is short, cut in this order: voice, withdraw button, screen 9. Keep stale/contradiction (screens 7 and 10): the challenge asks for them by name.

## Voice: option, not default

- **On:** text-to-speech of the 2-sentence brief, for a front desk under pressure.
- **Off by default,** visible as a toggle.
- **No voice input, no audio processing** (DPIA M-10). If the official challenge requires voice input, either write a one-page DPIA addendum before the 22nd (synthetic actors, demo only, no retention), or skip. No improvised exception on the day.

## Suggested stack

- **Backend:** Python + FastAPI in a GitHub repo with a Dockerfile (Aiven Runtime deploys from GitHub); port `reference/replay.py` as the planner tool; `schema.sql` for Postgres.
- **LLM:** Claude for (a) raw input → structured event + *proposed* claims (strict JSON, checked against `target`), (b) explanations with citations, (c) the brief.
- **Frontend:** Lovable or Next.js on Vercel: timeline, card, memory panel, queue, toggle.
- **Data:** Aiven PostgreSQL (durable memory, decisions, refusals, events) + Aiven Valkey (this-stay memory with TTL at check-out, event stream, housekeeping queue). See `ARCHITECTURE.md`.
- **Voice:** ElevenLabs TTS.

## Team (3-4 people)

| Role | Owns |
|---|---|
| Product / pitch / data (Ivan) | Scenario, dataset, prompts, parser tests vs `target`, pitch, scope calls |
| Frontend | Timeline, card, memory panel, queue, Validate/Withdraw buttons, toggle |
| Backend / AI | Event bus, decision core, LLM parsing + explanations, API |
| (Optional) Voice / design | ElevenLabs brief, polish, both safety videos |

## Open risk

**The official challenge is "to be revealed".** If it imposes a theme, keep the engine and re-skin the story: messy inputs → consented memory → continuous re-plan → human validation fits "agents", "voice", "operations" or "trust". Decide in the first 15 minutes.
