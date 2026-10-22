# Pitch material (v5 — challenge: Data-Centric Agents)

> Main message (decided 10:25, `ROADMAP.md`): **what hotel amnesia costs the hotel.** Guest comfort (the 35-min wait, the quiet room) is the illustration, not the headline.
> Every figure below comes from `research/bmad-recon-hotel-cost-2026-10-22.md` or `research/discovery-2026-10-22.md`, with the flag those files give it. **No hotelier has been interviewed yet.** `[N]`, `[quote]`, `[€X]` and `[X] %` stay as placeholders until real data exists.

## BuilderBase — Create a Team (do not submit without Ivan)

**Team name:** Anima

**Problem statement** (478 / 500 characters):

> Hotels pay for their own amnesia. A regular's request lives in one receptionist's head. When it's lost, the hotel pays a gesture, the regular comes back less often, and when staff leave, what they knew leaves too. Now hotels plug AI agents into guest data, fearing liability and privacy most. Remembering is becoming free; Anima is governed memory: only what guests said, each item with a purpose and an expiry, re-planned as the day changes, with a human validating every move.

**Open team:** ✅ (visible in the team browser).

## The one pitch slide (required by the challenge: who, why now, first users)

**Anima — governed guest memory for hotel AI agents**

- **What amnesia costs the hotel — it pays three times:**
  1. **The gesture.** To win back a guest whose room wasn't what they booked, a hotel had to give back about **80 % of the room price**, just to get back to neutral. *A study found — scenario experiment, Sweden, n = 40 + 150, 2022.*
  2. **The regular.** **19 %** of UK guests who weren't recognised as returning took their business elsewhere. *Mews survey (PMS vendor), UK, 2022, method not published.*
  3. **The staff.** A front-desk departure costs **30 % of salary**, and co-workers lose **20 % of their productivity for up to 16 days**. *Cornell found — 2006, US, preliminary.* What they knew about your regulars leaves with them. *(Our claim, not a sourced finding.)*
- **Why now:** hotels are plugging AI agents into guest data (Apaleo shipped an MCP server for AI agents in 2025; 70 % of chains name AI agents a key innovation area). Their top fears about guest-facing AI: **liability for errors 56 %, privacy 54 %** (*h2c 2026, 113 chains, sponsored*). Guests accept AI using what they **said** (**61 %**) far more than social or external data gathered about them (**34 %**) (*Mews, July 2026, 3,250 travellers in 8 countries incl. France, vendor*). France's regulator has already fined **Accor €600,000** over consent taken at booking (*CNIL, 2022*).
- **Why Anima:** remembering is becoming free (Oracle OPERA, Revinate, Twilio all ship it). **Governed memory** isn't: only what the guest declared, a purpose and a retention clock on every item, inferred guesses refused, a human click before anything happens.
- **Who:** front-office teams of independent and boutique hotels (20-80 rooms) on modern PMS (Apaleo, Mews). The hotel pays; the front desk uses it; the guest sees and controls what is kept.
- **First users (target, none signed):** 3 Paris boutique hotels as design partners ([N] hotelier calls so far); then distribution through the Apaleo and Mews marketplaces, priced per room per month ([€X], to test).
- **Evidence (from the demo, synthetic):** 35 min wait → 0 on the recorded day; asked for quiet 3 times → 0; [X] % of fields correctly extracted from messy French inputs (live, `eval/parse_eval.py`).

## How we answer each judging criterion

| Criterion | Our answer on stage |
|---|---|
| Customer problem & value | The hotel pays for amnesia three times: the gesture, the regular who comes back less often, the knowledge that leaves with each receptionist (sourced and flagged on the slide). Guest comfort is how it shows up at the desk. [Hotelier quote, if we get one.] |
| Agent capability | Multi-step tool loop: parse → rule-gated write → memory read → planner tool → explanation → human validation; reacts to an event stream. |
| Data at the core | Memory that expires (Valkey TTL, 36-month SQL rule), gets stronger when confirmed, resolves contradictions, refuses inferences. Remove the data and the agent is useless — that's the point. |
| Evidence | Before/after vs two baselines, read as what the hotel loses (35 → 0 min, 3 → 0 asks); parser accuracy on golden targets ([X] %); oracle tests that fail when data is broken. |
| Execution & pitch | One front-desk screen, three beats, before/after table, live-vs-recorded table. |

## Team pitch — 60 seconds (09:00, or in BuilderBase messages)

> Hotels forget their guests. Someone asks for a quiet room on two stays and still has to ask again on the third. I've spent the past year building agentic systems for hotels, and I've prepared a full synthetic hotel day: 24 rooms at 87 % occupancy, a French WhatsApp message, a housekeeping text, a leaking tap, a concert, and a reference planner that already passes every decision of the day and shows what re-planning saves. Today we build the agent that reads the mess, remembers only what guests said, and re-plans the stay live, with voice briefs for the front desk. I need a frontend person and a backend/AI person. You'll have something real on screen by noon.

## 3-minute pitch

| Time | Beat | What to say (slide shows the flags) |
|---|---|---|
| 0:00-0:20 | **The hotel pays three times** | "When a hotel forgets a regular, it pays three times. The gesture: a study found it takes about 80 % of the room price to win a guest back to neutral. The regular: in a Mews survey, 19 % of unrecognised UK guests went elsewhere. The staff: Cornell found a receptionist leaving costs 30 % of a salary, and what they knew about your regulars leaves too." *Slide flags: scenario study, Sweden, 2022 · vendor survey, UK, 2022 · Cornell, 2006 · last line is our claim.* |
| 0:20-0:35 | **Why now** | "Now hotels are plugging AI agents into guest data. In a sponsored survey of 113 chains, their top fears are liability, 56 %, and privacy, 54 %. Guests, in a Mews vendor survey, accept AI using what they said, 61 %, far more than social data gathered about them, 34 %. And France's CNIL has already fined Accor €600,000 over consent taken at booking." |
| 0:35-1:55 | **Demo** | Screen 1: the PMS put her on the street side under tonight's concert; Anima moves her and **refuses a guess it was handed** ("prefers high floors"), because she never said it. Screen 3: a messy French WhatsApp, she arrives at 11:15; her room jumps the housekeeping queue — **35 minutes of waiting avoided**. Screen 5: a tap breaks in 206 — **re-planned to 305, ready before she arrives, and she never knew**. Screen 6: the two-sentence brief for the front desk. Then the before/after table, read as **what the hotel loses** (below). |
| 1:55-2:25 | **Why it's different** | "Remembering is becoming free. Oracle announced preference-based room assignment in OPERA in June; Revinate and Twilio announced memory features last week. What nobody ships is memory a hotel can defend: only what the guest declared, a purpose and an expiry on every item, guesses refused, a human click before anything moves. That is aimed squarely at the two fears hotels named: liability and privacy." Data-protection assessment written *before* any real guest. |
| 2:25-3:00 | **Status + ask** | Honest status: synthetic data, no hotel connected yet. **If calls happened:** "[N] hoteliers told us this week: [quote]." **If none:** "We haven't spoken to a hotelier yet. The costs you saw are published studies, flagged. Next week we ask five questions, and we know the answer that would make us drop this headline." Next: one pilot with an independent hotel on Apaleo or Mews, measuring repeated requests, room complaints and gestures given. Ask: intros to boutique hotel groups. |

Fill [N] and [quote] from the calls. **If there are none, say so plainly.** Never fake traction. If a hotelier gives a real number ("last month we comped [€X]"), it replaces the 80 % line: one real Paris hotel beats all three studies.

## Before / after (final screen) — what the hotel loses

Numbers computed by `reference/replay.py` (synthetic day). Column headers as on screen.

| | **Ignores her note** (PMS rule only) | **Honours the note, nobody re-plans** | **Anima** |
|---|---|---|---|
| Room | 402, street side, under tonight's concert | 206, found **out of service** at the desk | **305**, courtyard, desk |
| Wait on arrival (11:15) | 0 min | **35 min** (305 ready 11:50 in the normal queue) | **0 min** (305 ready 11:10) |
| Times she has to ask for quiet | a **third** time | 0 | 0 |
| What the hotel loses | A regular who asked twice is caught out again: a complaint, a gesture to make ([€X]), and a regular less likely to come back | The exact failure she complained about last time, at the counter: the front desk improvises, the hotel pays a gesture ([€X]) | Nothing to put right. Three cards validated by the front desk, each with its reason |
| Malik in 302 (asked for quiet) | concert under his window | concert under his window | offered 206 at 16:40; he declines (going to the concert); his durable "quiet" is kept and flagged to reconfirm |

Say it out loud: **remembering is not enough, and it is no longer what hotels pay for. The memory has to be acted on while the day changes, and the hotel has to be able to defend what it keeps.**

## Judges' questions — one-line answers

| Question | Answer |
|---|---|
| "My receptionist would have prioritised 206." | At 08:40, with eight departures and the queue running, the message sits in a WhatsApp inbox and nobody links it to the housekeeping queue. Anima does, and shows why. (Back it with a hotelier quote if we get one.) |
| "Mews and Opera already store guest preferences." | Yes, and remembering is now close to free: Oracle announced OPERA Cloud room assignment from "guest preferences, stay history and operational parameters" in June 2026 (trade press reports no extra cost to existing customers; we haven't checked that in the primary). Revinate launched profile memory and Twilio announced Conversation Memory on 15 Oct (Twilio's not checked beyond a search summary). So we don't sell remembering. We sell **governed** memory: declared only, a purpose and a retention clock per item, inferred guesses refused, a human click. Revinate goes the other way: "every question adds to their profile." Governance is what hotels say they fear getting wrong (liability 56 %, privacy 54 %). |
| "Sirma just launched hotel agents (Marta, Vela)." | Yes — a layer to "build, orchestrate and govern AI agents" across hotel systems. Their announcement says nothing about guest memory. We'd rather plug into an orchestrator like theirs than compete with it. |
| "Then why won't the PMS build it?" | Oracle already built the remembering part, which is why we don't compete on it. We plan to distribute through PMS marketplaces (Apaleo, Mews) rather than against them. Write-time consent, purpose and retention per item, and cross-channel capture are the parts a PMS has the least incentive to build. |
| "Is the 80 % real?" | It's from scenario experiments: people in Sweden (n = 40 and 150) reacting to an imagined room downgrade, so a lab number, not hotel accounts. Real gestures are often small (a drink, points). That's why we say "a study found", and why our first hotelier question asks what they actually gave, in euros. |
| "Do regulars even matter to a boutique hotel?" | Maybe not everywhere. One vendor blog (unverified) says most revenue comes from first-time guests, and in a cross-industry Twilio survey only 5 % ended a relationship over repeating themselves. That's why question 4 asks each hotel its repeat share, and it's part of our kill signal. |
| "Feature or company?" | Thesis: every hotel agent, ours or others', will need one governed memory layer it can be audited on. Test: one pilot hotel, measure repeated requests, room-related complaints and gestures given over a month. What would kill it: front desks don't follow the recommendations, or a month of pilot shows no drop in repeated requests and room complaints. |
| "Who pays, how much?" | The hotel, as a per-room monthly subscription through the marketplace: the costs land on the hotel, the guest pays nothing. Hypothesis: [€X] per room per month, to be tested in the pilot. |
| "Have you talked to hotels?" | **If none:** "Not yet, and we won't pretend otherwise. The cost chain comes from published studies, flagged on the slide; the most recent cost study is a lab scenario. No hotelier has confirmed it in their own words. Our five questions are ready, and if two of three hoteliers say a regular is rarely caught out, a coffee fixes it, and under 10 % of guests return, we drop the cost headline and lead with governance." **If calls happened:** "[N] this week. [quote]." Give the number they gave, if any. |
| "Why you?" | Two years co-founding a B2G data SaaS, from discovery to MVP and a sales process; led a 10-tool consolidation onto one SaaS for 500+ users across 100+ care facilities; front-of-house experience in restaurants; a year building hotel agents on Apaleo. |
| "Why would guests share?" | We only ask for what changes their stay, show them what we keep, and let them withdraw it. A Mews survey (vendor, July 2026) found 61 % accept AI using preferences they stated, against 34 % for social or external data. Adoption is what the pilot measures. |
| "Privacy?" | Consent per purpose, separate from booking (the CNIL fined Accor €600,000 in 2022 over a pre-ticked box at booking); declared claims only; 36-month retention, stay-only for stay needs; no emotional inference; no audio. DPIA written before any real data. |

**Used, with their flags:** Edström et al. 2022 (scenario study), Mews 2022 (vendor, old, UK), Cornell 2006 (old, US), h2c 2026 (sponsored, chains), Mews 2026 (vendor), CNIL v Accor 2022 (press summaries agree; PDF not text-readable), Oracle OPERA (unverified snippet of the primary), Revinate (opened), Twilio (unverified).
**Not used on purpose:** "69 % of chains enter preferences by hand" (secondhand, not in the h2c report pages); Stash/Cornell "$405-$780 per returning guest" and Anderson "+11.2 % price per review point" (unverified, old); "room readiness costs up to 15 % of revenue" (no published method); named traveller-agent products (2-5 % would let AI book unsupervised, unverified).

## Message to the organizers (BuilderBase messages or Luma)

> Hi! Looking forward to the 22nd. Two quick questions: (1) Can teams bring prepared synthetic datasets and design docs, or should all code be written on the day? (2) Will the challenge be announced before the event, or at kickoff? Thanks — Ivan

## Hotelier call script (10 min, ask in French if the hotelier is French)

Target: GMs, owners or front-office managers of independent/boutique hotels (20-80 rooms), Paris first.

1. "Think of the last regular who was caught out at the desk: the wrong room, a request forgotten. What happened, and what did you give them? Roughly how many euros?" *(The gesture, in € at a boutique hotel.)*
2. "When your last receptionist left, what did they know about your guests that nobody else knew? How did you find out?" *(Knowledge leaving with staff, in their words: the quote for the pitch.)*
3. "Where do guest preferences live today: the PMS profile, a note on the booking, a notebook, someone's head? Do they survive a Booking.com reservation?" *(Where the declared need gets lost; tests OTA email masking.)*
4. "Roughly what share of your nights or revenue comes from returning guests? Would you notice if a regular stopped coming?" *(Is the repeat base big enough to matter?)*
5. "If an AI agent plugged into your PMS remembered guests for you, what would stop you from switching it on: GDPR/CNIL, mistakes, guests finding it creepy, or price? Would [€X] per room per month through your PMS marketplace be a yes?" *(The AI/GDPR fear at a boutique hotel, plus who pays.)*

**Kill or adjust signal:** if 2 of 3 hoteliers answer Q1 with "rarely, and a coffee fixes it" **and** Q4 with "under 10 % repeat", drop the hotel-cost headline. Go back to the trust and governance message ("the consented memory layer hotel AI agents go through"). That is still a light pivot, not a hard one.

Write down **exact words**, not your interpretation. One real quote, or one real euro figure, beats every statistic on the slide.

## Safety-video narration (read over the screen recording)

### Video 1 — screens 1-4 (about 80 seconds)

> This is Maison Lumen, a synthetic 24-room hotel, 87 % full tonight. Every guest and message here is synthetic, and in this recording the French messages are read by our recorded reference parser, labelled "golden".
>
> Left, the day's raw inputs as they arrive. Centre, what Anima recommends and why. Right, what Anima knows about Claire, read live from Postgres and Valkey.
>
> Claire is a regular. She asked twice for a quiet room, and last time she waited two hours for it. The hotel has already paid for that once.
>
> 07:00. The PMS put her in 402, street side, under tonight's concert. Anima proposes 206, courtyard side, with a desk, and cites its sources. A traveller-side agent pushed "prefers high floors". Claire never said that, so it is refused, and the banner counts it without a name. The same sweep deletes a memory nobody confirmed in 36 months.
>
> 08:15, 206 will be free earlier. Nothing to change.
>
> 08:40, a WhatsApp in French: she'll be here at 11:15, not 15:00. In the normal queue 206 is ready at 11:50, a 35-minute wait, the exact failure she complained about. Anima moves 206 to the front of the housekeeping queue: ready at 10:30. The front desk clicks Validate.
>
> 10:05, 305 checks out early. The plan already holds, so nothing moves. Nothing in this hotel moves without a human click.

### Video 2 — the full day (about 90 seconds)

Lines marked *[if built]* are read only if that screen made it past the 13:45 freeze (with both, it runs about 100 seconds: speak briskly or drop the 16:00 line).

> One synthetic day at Maison Lumen, in two minutes. Claire, a regular, asked twice for a quiet room and last time waited two hours: the kind of miss a hotel pays for.
>
> 07:00. Anima moves her off the street side, refuses a guess pushed by a traveller's AI agent, and deletes a memory past its 36 months.
>
> 08:40. A French WhatsApp: she arrives at 11:15. Her room jumps the housekeeping queue. Thirty-five minutes of waiting avoided.
>
> 10:20. A housekeeper texts that 206's tap is leaking. Anima switches her to 305, ready at 11:10, before she arrives. She never knew.
>
> 11:05. Her train is in. The front desk gets a two-sentence brief: nothing to ask her again.
>
> 11:15. "The courtyard side, perfect." Her quiet-room memory is confirmed a third time, and its clock restarts.
>
> *[if built]* 14:00. Hugo withdraws consent. His memory is gone, from both stores, on screen.
>
> *[if built]* 16:00. 206 is fixed, and Anima suggests offering it to Malik, who asked for quiet.
>
> 16:20. Malik replies he's going to the concert. For tonight, his newest word wins; his "quiet" is kept, to reconfirm next stay. Never silently overwritten.
>
> What the hotel loses. Ignore her note: she asks a third time, under a concert. Honour it without re-planning: 35 minutes waiting for a broken room. Anima: zero minutes, nothing to put right, every move validated by a person. Parser on this run: [live, X % on our golden set / golden, recorded].
