# What hotel amnesia costs the hotel — BMAD recon summary, 22 Oct 2026

> BMAD `bmad-deep-recon`, Run mode, analyst voice Mary. Time-boxed to 40 minutes, done during the hackathon. Full run with sources, memlog and digests: `_bmad-output/planning-artifacts/research/user-voice-hotel-amnesia-cost-to-the-hotel-2026-10-22/research.md`.
> This builds on `research/discovery-2026-10-22.md` (cited as **[D]** with its item numbers) and does not repeat it.
> **Opened** = page fetched and read this run. **Unverified** = seen only in a search-result summary. Quotes are verbatim and under 25 words. No figure or quote is invented. No hotelier has been interviewed yet.

## 1. Verdict (5 lines)

1. **Pain strength: medium.** Each link of the hotel-cost chain has a sourced number, but nobody measures the whole chain at an independent hotel, and no hotelier says it publicly. It is a *hidden cost*, not a burning pain.
2. **The strongest links** are the price of putting a failure right (~80 % of the room price to get a guest back to neutral, scenario study), the cost of a front-desk departure (30 % of salary; co-workers lose 20 % productivity for up to 16 days), and the fact that hotels fear AI liability (56 %) and privacy (54 %).
3. **Light pivot confirmed.** Keep the same product and lead with the hotel-cost framing. Nothing found supports a hard pivot. Incumbents now ship "remembering" for free (Oracle OPERA), so the wedge is *governed* memory: declared only, purpose, retention, refusal, a human click.
4. **B2B2C confirmed.** Each cost lands on the hotel (gestures, staff time, turnover, CNIL exposure). The guest feels it but pays nothing. No source argues for B2C.
5. **What would change this:** calls where hoteliers say regulars are rarely caught out and that gestures are trivial. The counter-evidence (repeat guests can be a small share of revenue; few guests leave over being forgotten) is real.

## 2. The hotel-cost chain (one sourced item per link)

| Link | What it costs the hotel | Source and strength |
|---|---|---|
| **0. Cause: the declared need is lost** | 69 % of chains enter or enrich guest preferences by hand; 19 % extract them with AI; 42 % have a central guest profile database | h2c 2026 via T. Ronson, "Forget Me Not", Hospitality Net, Oct 2026. Opened, but the figure is **secondhand**: it is not on the h2c report page we opened. Medium |
| | In Infor HMS, a preference stays on one stay unless someone saves it to the profile | Infor HMS documentation, 2026. Unverified. Directional |
| **1. Regular caught out → compensation** | To bring a guest back to neutral after a downgrade to a smaller room, compensation had to be "just over 80% of the original room reservation price" | Edström et al., *J. Service Theory & Practice* 32(7), 2022. Opened. Scenario study, Sweden, n = 40 + 150. Medium |
| | Empathy or an apology follows in under 75 % of service-recovery moments; follow-up is the weakest step | Coyle Hospitality (mystery shopping, 525 upscale hotel visits), Hotel-Online, Apr 2014. Opened. Old. Directional |
| **2. Complaint → reputation → price** | A 1-point gain on a 5-point review scale allowed an 11.2 % price rise at the same occupancy, which suggests the same lever works in reverse | Anderson, Cornell CHR, 2012. Unverified (snippet). Old. Directional |
| **3. Lost repeat guest → revenue** | Across 24 independent hotels (>50,000 guests), enrolled guests returned ~50 % more often, worth **$405-$780 a year per guest** in extra revenue | Cornell Hospitality Report on Stash Hotel Rewards, via Loyalty360. Unverified (several trade write-ups agree). Vendor-linked case, ~2015. Directional |
| | 19 % of UK guests who were not recognised took their business elsewhere | Mews 2022 [D: E10]. Vendor, old. Directional |
| **4. Knowledge leaves with staff** | "The average cost of turnover at the front desk was 30 percent of salary, or an average dollar figure of nearly $5,900" | Hinkin & Tracey, Cornell CHR, via Hospitality Net, May 2006. Opened. Old, preliminary, US. Medium as a mechanism |
| | Co-workers "lost 20 percent of their productivity for up to 16 days when a colleague left the front desk" | Same. Opened |
| | Hotel turnover runs at 70-80 % a year | Netchex blog citing SHRM 2025. Unverified. Vendor. Directional (cf. 40.5 % in [D: E16]) |
| **5. AI / GDPR exposure** | Top concerns about guest-facing autonomous AI: liability for errors **56 %**, privacy and security **54 %**, guests' reluctance to share data **53 %** | h2c AI Opportunity Study 2026 (122 responses, 113 chains), via a Sirma release on Hospitality Net, Oct 2026. Opened. Sponsored, chains. Medium |
| | CNIL fined **Accor €600,000** (Aug 2022): guests booking a stay were signed up for a newsletter with partner offers through a pre-ticked box, and unsubscribing failed | CNIL deliberation SAN-2022-017 (PDF not text-readable) + Siècle Digital and L'Écho touristique (search summaries agree). Medium. Regulator, France, chain |
| | Only 13 % of chains report measurable AI ROI | h2c report page (Cendyn-sponsored), Hospitality Net, Oct 2026. Opened. Medium |

**How to say it:** the hotel pays three times. First it pays the gesture, sized like part of the room price. Then the regular comes back less often. And every receptionist who leaves takes the guest notes in their head with them. Now hotels want AI to fix it, and their top fears are liability and privacy.

## 3. Evidence table (new items only; see [D] for E1-E20 and L1-L7)

| # | Figure / finding | Publisher · title · date · URL | Sample / method | Flags | Strength |
|---|---|---|---|---|---|
| N1 | Front-desk turnover = 30 % of salary (~$5,900); co-workers −20 % productivity for up to 16 days | Cornell CHR (Hinkin & Tracey) via Hospitality Net · "Cornell Researchers Demonstrate Use of Turnover Calculator" · May 2006 · [link](https://www.hospitalitynet.org/news/4027532.html) | CHR web turnover calculator, preliminary; n not stated | **Old**, US, academic | Medium (opened) |
| N2 | ~80 % of room price (CI 68-92 %) needed to neutralise a room downgrade | Edström et al. · "Where service recovery meets its paradox" · JSTP 32(7), 2022 · [link](https://www.emerald.com/insight/content/doi/10.1108/JSTP-06-2021-0120/full/html) | Scenario experiment, n = 40 + 150, Sweden | Academic; lab scenario | Medium (opened) |
| N3 | Monetary + non-monetary compensation beats either alone | Fu et al. · IJHM · 2015 · [link](https://research.polyu.edu.hk/en/publications/monetary-or-nonmonetary-compensation-for-service-failure-a-study-/) | Not seen | Academic, old | Directional, **unverified** |
| N4 | Returning members +$405-$780/guest/yr; 24 independent hotels, >50k guests | Cornell Hospitality Report (Stash case) via Loyalty360 · ~2015 · [link](https://loyalty360.org/Content-Gallery/Daily-News/Study-Shows-Stash-Hotel-Rewards-Customers-Increase-Spend-by-Nearly) | 2+ years of transactions | Vendor-linked, old, **independents** (rare) | Directional, **unverified** |
| N5 | +1 review point → +11.2 % price at the same occupancy | Anderson · Cornell CHR · 2012 · [link](https://ecommons.cornell.edu/entities/publication/d64bbbba-651a-4e13-a058-af3e2e82f4cf) | Travelocity transaction data | Old | Directional, **unverified** |
| N6 | h2c 2026: liability 56 %, privacy 54 %, willingness to share 53 %, proactive agents 70 % | Sirma release · Hospitality Net · Oct 2026 · [link](https://www.hospitalitynet.org/news/4134633/sirma-brings-connected-ai-agents-to-hotel-operations-as-h2c-study-signals-hospitalitys-next-ai-phase) | 122 responses, 113 chains | Sponsored; chains; vendor release | Medium (opened; confirms [D: E7]) |
| N7 | h2c 2026: 8,200+ properties; 91 % use AI; 28 % senior-led strategy; 13 % measurable ROI | h2c report page (Cendyn) · Hospitality Net · 14 Oct 2026 · [link](https://www.hospitalitynet.org/news/4134842/h2c-hotel-chain-tech-report-2026-the-ai-opportunity) | Same | Sponsored; chains | Medium (opened) |
| N8 | h2c via Ronson: 42 % have a central guest profile DB; 15 % an MCP-type data access layer. Twilio APAC 2026: 70 % repeat information, but only **5 %** ended the relationship | T. Ronson · "Forget Me Not" · Hospitality Net · Oct 2026 · [link](https://www.hospitalitynet.org/opinion/4134698/forget-me-not) | h2c as above; Twilio 7,652 consumers, 18 markets | Opinion piece; secondhand; cross-industry | Medium (opened) |
| N9 | CNIL fines Accor €600k: pre-ticked consent at booking, unsubscribe failures | CNIL · SAN-2022-017 · 3 Aug 2022 · [PDF](https://www.cnil.fr/sites/default/files/atoms/files/deliberation_de_la_formation_restreinte_no_san-2022-017_du_3_aout_2022_concernant_la_societe_accor_sa.pdf); [Siècle Digital](https://siecledigital.fr/2022/08/18/le-groupe-hotelier-accor-condamne-par-la-cnil-pour-manquements-au-rgpd/) | Regulator decision | France; chain; PDF not text-readable | Medium (two press summaries agree) |
| N10 | Coyle: 525 upscale visits; apology <75 %; follow-up weakest | Coyle Hospitality · Hotel-Online · 3 Apr 2014 · [link](https://www.hotel-online.com/news/the-new-service-recovery-paradox-step-it-up-with-follow-up1) | Mystery shopping, 11,000 data points | Old; upscale | Directional (opened) |
| N11 | Hotel turnover 70-80 %/yr; ~$5,475 direct cost per hourly worker (SHRM 2025) | Netchex blog · 2026 · [link](https://netchex.com/blog/real-cost-hospitality-turnover-2026/) | Not seen | Vendor; US | Directional, **unverified** |
| N12 | France BMO 2025: 52,400 hiring projects for "employés de l'hôtellerie" | France Travail · BMO 2025 · [PDF](https://www.lechotouristique.com/wp-content/uploads/2026/03/bmo2025-rapport-france.pdf) | Employer survey | France; not reception-specific | Directional, **unverified** |
| N13 | GHR end-2025: average booking rate 57 %; 46 % of members see a decline vs 2024; margins under pressure | GHR · press release · Dec 2025 · [PDF](https://cdn.ghr.fr/IMG/pdf/cp_ghr_fetesfinannee2025.pdf) | Member panel, 10-22 Dec 2025 | France; trade body | Directional, **unverified** |
| N14 | Oracle OPERA Cloud Assistant: room assignment from "guest preferences, stay history and operational parameters"; no extra cost to existing customers (trade press) | Oracle · press release · 16 Jun 2026 · [link](https://www.oracle.com/news/announcement/new-ai-capabilities-in-oracle-opera-cloud-supercharge-hotel-operations-2026-06-16/) | Product announcement | Vendor; chains PMS | Medium, **unverified** (snippet of primary) |
| N15 | Canary: AI messaging with preference-based suggestions and auto-tickets; #1 HotelTechAwards 2026; 20,000+ hotels (self-reported) | Canary · product page · 2026 · [link](https://canarytechnologies.com/products/ai-guest-messaging) | Marketing | Vendor | Directional, **unverified** |
| N16 | Sirma.AI Enterprise: an agent layer to "build, orchestrate and govern AI agents" (Vela, Marta); no guest memory mentioned | Sirma release · Hospitality Net · Oct 2026 (as N6) | Announcement | Vendor | Medium (opened) |
| N17 | Agent memory (Mem0, Letta, Zep): deletion after the fact; no write-time consent, purpose or retention found; no Zep consent docs | DEV Community guide; Mem0 FAQ · 2026 · [link](https://dev.to/plur9/is-ai-agent-memory-gdpr-compliant-a-developers-guide-412) | Developer guides | Secondary; vendor FAQ | Directional, **unverified** |
| N18 | YC RFS Fall 2026: 13 requests incl. "The Trust Layer"; none on hospitality or agent memory | BigIdeasDB capture of ycombinator.com/rfs · Aug 2026 · [link](https://bigideasdb.com/yc-request-for-startups-2026) | Third-party capture | Official page not opened | Directional, **unverified** |
| N19 | Night auditor: "no one really told me anything in the pass off" | r/TalesFromTheFrontDesk via a mirror · Oct 2026 · [link](https://redlib.hackliberty.org/r/TalesFromTheFrontDesk) | One post | US; front desk | Anecdotal, **unverified** |
| N20 | "most of what goes wrong at a front desk was known, an hour earlier, by somebody who has now gone home" | ProStay blog · 2026 · [link](https://www.prostay.com/blog/hotel-shift-handover-front-desk-2026/) | Opinion | PMS vendor | Anecdotal, **unverified** |
| N21 | Hotel guest notes called a guest "very, very picky" (free-text notes become a liability) | One Mile at a Time · [link](https://onemileatatime.com/hotel-very-very-picky/) | One case | Blog; chain | Anecdotal, **unverified** |

**Searched and not found:** any study of how often a declared request is lost or what it costs an independent hotel. A recent verbatim quote from an independent hotelier or GM on regulars caught out or knowledge leaving with staff (EN or FR). A UMIH, GHR, Atout France, Coach Omnium or In Extenso study on guest recognition, repeat-guest share or reception turnover (Coach Omnium 2018 polled 370 independent hoteliers on distribution, not on memory). The 69 % figure in the primary h2c report. A Cendyn guest-memory product.

## 4. Counter-evidence

1. **Repeat guests can be a small share of revenue:** 88 % of revenue comes from first-time guests, and 71 % of second-stay guests never come back a third time (Bookboost vendor blog, paraphrased from a search summary, dataset unnamed, unverified). If that holds for boutique hotels, the cost of amnesia is small per hotel.
2. **Few people leave over being forgotten:** in Twilio APAC 2026, 70 % repeat information but only 5 % ended the relationship (N8, cross-industry).
3. **Recovery can work:** hoteliers believe a well-handled complaint rebuilds loyalty. Coyle states the recovery paradox as a premise but does not measure it (N10). Real-world gestures are often small: a drink, points, a cheesecake ([D: §3E]). The 80 % figure is a lab scenario.
4. **"Remembering" is commoditising:** Oracle OPERA gives preference-based room assignment to existing customers at no extra cost (N14); Revinate, Canary and Mews ship profile memory ([D: L1-L2]).
5. **Hotels are pulling back from AI personalisation** (22 % → 16 %) and only 13 % see ROI (N7, N8). French independents report falling bookings and squeezed margins (GHR, N13), so budgets are tight.
6. **Front desk is the more stable department;** turnover is worst in housekeeping and F&B ([D: E16]).
7. **The academic cost links are old** (2006, 2012, 2014, 2015), and the only post-2020 cost study is a scenario experiment.

## 5. The 3 items for the pitch's first 20 seconds

1. **The gesture:** "To win back a guest whose room wasn't what they booked, a hotel has to give back about 80 % of the room price, just to get back to neutral." (Edström et al., *J. Service Theory & Practice*, 2022, scenario study.) Say "a study found" and show the flag on the slide.
2. **The knowledge that walks out:** "When a receptionist leaves, it costs 30 % of their salary, and the colleagues left behind lose 20 % of their productivity for up to 16 days." (Cornell Center for Hospitality Research.) The data is from 2006, so say "Cornell found" and don't claim it's recent. Then add: "and everything they knew about your regulars leaves with them." That last line is our claim, not a sourced finding.
3. **Why now:** "Hotels are plugging AI into guest data, and their top two fears are liability (56 %) and privacy (54 %)" (h2c 2026, 113 chains, sponsored). "France's privacy regulator has already fined a hotel group €600,000 over guest consent taken at booking" (CNIL v Accor, 2022).

**Replace item 2 with a hotelier's own words from today's calls if you get one.** A real number from a real Paris hotel ("last month we comped X") beats all three.

## 6. Five questions for hotelier calls today

1. "Think of the last regular who was caught out at the desk: the wrong room, a request forgotten. What happened, and what did you give them? Roughly how many euros?" *(Measures links 1-2 in € at a boutique hotel.)*
2. "When your last receptionist left, what did they know about your guests that nobody else knew? How did you find out?" *(Link 4, in their words; the quote for the pitch.)*
3. "Where do guest preferences live today: the PMS profile, a note on the booking, a notebook, someone's head? Do they survive a Booking.com reservation?" *(Link 0; tests OTA masking [D: E15] and stay-only notes.)*
4. "Roughly what share of your nights or revenue comes from returning guests? Would you notice if a regular stopped coming?" *(Tests counter-evidence #1: is the repeat base big enough to matter?)*
5. "If an AI agent plugged into your PMS remembered guests for you, what would stop you from switching it on: GDPR/CNIL, mistakes, guests finding it creepy, or price? Would €X per room per month through your PMS marketplace be a yes?" *(Link 5, plus who pays; confirms B2B2C.)*

**Kill or adjust signal:** if 2 of 3 hoteliers answer Q1 with "rarely, and a coffee fixes it" and Q4 with "under 10 % repeat", drop the hotel-cost headline. Go back to the trust and governance message from [D] ("the consented memory layer hotel AI agents go through"). That would still be a light pivot, not a hard one.

## Assumptions logged (Ivan was not available to answer framing questions)

- Buyer: GM or owner of an independent/boutique hotel (20-80 rooms) on a cloud PMS; user: the front office (from `PROBLEM.md`).
- France/Paris first; EU/US evidence accepted with a region flag (from `PITCH.md`: Paris design partners).
- Preset forced to *quick* (40-minute time box): one main round plus one verification round, `normal` validation (spot-check load-bearing claims only), red team off. Counter-evidence was searched for explicitly instead.
- No subagents: the lead ran searches inline in parallel batches to fit the time box.
- `research/discovery-2026-10-22.md` treated as one imported source and cited, not re-researched.
- "Sirma" in the brief taken to be Sirma.AI (hotel AI agent layer, h2c-linked release, Oct 2026).
- Not done for lack of time: the HTML briefing, the `bmad-review` prose/structure polish pass, and the semantic citation check by a fresh subagent. The mechanical citation check passed (24/24 markers resolve).
