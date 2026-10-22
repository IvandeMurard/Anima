# Anima — Problem discovery, 22 Oct 2026

> About 45 minutes of desk research during the hackathon, using the BMAD Analyst's market and domain research frame: problem, evidence, who feels it and who pays, landscape, risks, open questions.
> **Rule:** every figure and quote below was opened and read in a primary or press source, unless marked **unverified** (search summary only, or page blocked) or **secondhand** (read in an article citing the study, not in the study). Quotes are verbatim and under 25 words.
> **Strength scale** (same spirit as `PROBLEM.md`):
> - **Strong:** independent or large sample, recent, method published.
> - **Medium:** recent, decent sample, but vendor-run or sponsored.
> - **Directional:** vendor-run, old, or narrow.
> - **Anecdotal:** single case, blog or forum.
>
> There is still **no hotelier interview**. That remains the weakest link.

---

## 1. Verdict in five lines

1. **The "hotel amnesia" pain is real but chronic and low-intensity, and the public evidence for it is old or vendor-made.** The Mews UK survey dates from 2022, and the room-readiness polls stop in 2016. No source measures how often a request is lost between the front desk, housekeeping and maintenance.
2. **The pain that is growing, with recent and better evidence, is trust in what AI may remember.** In Mews' July 2026 survey of 3,250 travellers, 61 % accept AI using what they *declared*, against 43 % for their online behaviour and 34 % for social data. Twilio's late-2025 global survey found that 54 % say AI agents rarely or never have context about them, yet 66 % are uneasy giving an agent their full history. On the hotel side, 56 % of chains cite liability and 54 % privacy as their top blockers for guest-facing AI (h2c, Oct 2026).
3. **The guest feels the pain** (repeating themselves, waiting for a room). **The hotel pays**, but doesn't measure it (69 % of chains still enter preferences by hand, figure secondhand). That makes the model **B2B2C**: the hotel buys, and the guest sees and controls the memory. Pure B2C (guest-owned, portable preferences) is being taken by platforms (ChatGPT memory, Mindtrip, Layla, Meta's Muse), not a wedge a startup can hold.
4. **Recommendation: a light pivot of the framing, not a hard pivot.** Keep the engine and the buyer. Move the headline from "hotels forget their guests" to "**the consented memory layer that hotel AI agents go through**: only what the guest declared, acted on while the day changes, forgotten on schedule". Recent data supports this framing better than the amnesia one, and the distribution channel exists (Apaleo's MCP server and Agent Hub).
5. **What would justify a hard pivot:** hotelier calls that say "we don't lose requests" *and* "AI memory isn't a worry for us". Until then, the risk is urgency rather than the problem itself: Revinate and Twilio both shipped guest-memory features on 15 Oct 2026.

---

## 2. Evidence table

### 2a. Demand-side evidence

| # | Figure or finding | Publisher · title · date | Sample / method | Flags | Strength |
|---|---|---|---|---|---|
| E1 | Travellers comfortable with AI using **stated preferences 61 %**, past stay history 56 %, online behaviour 43 %, external/social data 34 % | Mews · "Travelers want AI to track room rates, not plan their itinerary" · 15 Oct 2026 · [hotel-online](https://www.hotel-online.com/news/travelers-want-ai-to-track-room-rates-not-plan-their-itinerary) · [Hospitality Net](https://www.hospitalitynet.org/news/4134954/travelers-want-ai-to-track-room-rates-not-plan-their-itinerary) | 3,250 travellers in FR, DE, IT, NL, ES, SE, UK, US; July 2026. No further method published | Vendor (Mews). Includes France | **Medium**: recent, large, multi-country |
| E2 | **57 %** would rather stay in control of their trip than hand decisions to AI. Only **41 %** want AI personalising the room. UK: only **30 %** rate personalisation during a stay as important (40 % on average) | Same as E1 | Same as E1 | Vendor | Medium |
| E3 | **72 %** in Spain would be more willing to use AI services if they had transparency and control over their data | Same as E1 | Spain sub-sample, size not given | Vendor, one country | Directional |
| E4 | **89 %** prefer a blend of AI and human service, or AI working in the background. Human staff matter most for the front-desk welcome (**66 %**) | Mews · "89% of guests want AI working behind the scenes, not running the front desk" · 7 Oct 2026 · [hotel-online](https://www.hotel-online.com/news/89-of-guests-want-ai-working-behind-the-scenes-not-running-the-front-desk-mews-finds) | Same survey as E1 | Vendor | Medium |
| E5 | **54 %** of consumers say AI agents rarely or never have previous context about them. **66 %** would not want, or are uneasy, giving an AI agent all previous context. **51 %** are uncomfortable sharing personal or financial information with AI agents | Twilio global conversational-AI report · 13 Nov 2025 · via PPC Land · [link](https://ppc.land/twilio-finds-businesses-overestimate-ai-chatbot-satisfaction-by-31/) | 4,800 online shoppers in 15 countries, plus 457 business leaders. Online survey by Method Research, distributed by RepData, Aug-Oct 2025 | Vendor (Twilio sells memory). All industries, not hotels | **Medium**: method published, large, global. *The "remember me, but not everything" paradox* |
| E6 | **75 %** say they repeat information already shared with an AI agent. **89 %** of brands believe their AI recognises returning customers. **68 %** stopped using an AI agent mid-interaction because it lacked basic information about them | Twilio 2026 Customer Insights Series (India) · MediaNews4U · 21 Sep 2026 · [link](https://www.medianews4u.com/68-of-indian-consumers-abandon-ai-over-poor-memory-twilio/) | India: 350 consumers, 35 business leaders; fielded 9 Apr-1 May 2026 | Vendor. India only. All industries | Directional. Illustrates the **perception gap** |
| E7 | Barriers to guest-facing AI: unclear liability for AI errors **56 %**, data privacy and security **54 %**, guests' willingness to share data **53 %**, accuracy/bias 52 %. AI agents named as a key innovation area by **70 %**. Agents used or planned: staff-facing **70 %** vs guest-facing **55 %** | h2c · "New h2c Study: AI Adoption Is Widespread Among Hotel Chains…" · 1 Oct 2026 · [Hospitality Net](https://www.hospitalitynet.org/news/4134680/new-h2c-study-ai-adoption-is-widespread-among-hotel-chains-but-enterprise-readiness-remains-limited) | 122 responses from 113 chains (8,200+ properties) | Sponsored (Shiji, Cendyn and others). Chains, not boutique hotels | **Medium**: verified in the h2c release |
| E8 | **69 %** of chains enter or enrich guest preference data manually; **19 %** use AI to extract preferences. AI-powered personalisation use **fell from 22 % to 16 %**. Only **13 %** report measurable AI ROI (the 13 % is also in the h2c release) | h2c 2026, cited by T. Ronson (Pertlink), "Forget Me Not", Hospitality Net, Oct 2026 · [link](https://www.hospitalitynet.org/opinion/4134698/forget-me-not) | Same study. N = 67-122 per question, unweighted | **Secondhand**: 69 % and 22→16 % not found in the h2c press pages; the author is a consultant | Medium if confirmed in the full report; **check before putting on a slide** |
| E9 | **59 %** of returning guests were overlooked as returning; **19 %** took their business elsewhere; **15 %** annoyed by "have you stayed with us before?"; **47 %** would give personal information for a personalised service | Mews · "Hotels losing out on £1.8 billion in revenue a night…" · 5 Jul 2022 · [link](https://www.mews.com/en/press/hotels-losing-out-on-1-8-billion-in-revenue-a-night-by-failing-to-personalize-guest-stays) | UK travellers. Sample size and method not published | Vendor, **old**, UK only | Directional |
| E10 | **66 %** "always" or often wait for their room even after standard check-in time; only **23 %** say rooms are always ready | hospitalityPulse · "2016 Check-In Experience Survey" · 14 Nov 2016 · [Hospitality Net](https://www.hospitalitynet.org/news/4079347.html) | 285 self-selected participants, a mix of **hoteliers and travellers**; nine questions on a vendor website | Vendor, **old**, self-selected, US | Directional |
| E11 | Rooms not ready on arrival named as a complaint by **45 %** (second after rude staff at 69 %) | Thistle Hotels survey, 2014, via DJS Research · [link](https://www.djsresearch.co.uk/SportLeisureAndTourismMarketResearchInsightsAndFindings/article/Survey-Reveals-Most-Common-Holiday-Complaints-01467) | 2,000 guests, UK | Hotel brand, **very old**, wording unknown | Directional, **unverified** (not opened) |
| E12 | Maintenance is the largest category of unplanned tasks (**33 %**; 45 % of tasks routed to a department). About 1 in 6 inbound guest texts arrive between 7 pm and 7 am | HelloShift · "Hotel Operations Index" · 8 Sep 2026 · [Hotel Tech Report](https://hoteltechreport.com/news/helloshift-releases-hotel-operations-index-drawing-on-a-decade-of-first-party-hotel-operations-data) | HelloShift platform data since 2014; number of hotels not disclosed | Vendor. **Gives no rate of lost requests** | Directional |
| E13 | **68 %** of US travellers say they would stay loyal to hotels with standout personalised experiences over points programmes | Mews-commissioned poll via Hotel Management · 2025 · [link](https://www.hotelmanagement.net/data-trends/mews-survey-reveals-majority-travelers-put-personalized-experiences-over-rewards) | About 2,000 US adults who travelled in the last 12 months | Vendor; stated intent | Directional, **unverified** (blocked) |
| E14 | Mews guest insights cannot automatically recognise returning guests who book through an OTA, because the email is masked | Mews Help Center · [link](https://help.mews.com/s/article/How-to-identify-returning-guests-using-guest-insights-in-Mews-Operations) | Product documentation | Vendor | Directional, **unverified** (search summary). A structural cause of non-recognition |
| E15 | Hospitality churn averages 40.5 %. Turnover is highest in housekeeping and F&B; the front desk is "more stable but not immune" | Cloudbeds 2025; Netchex blog, Jun 2026 · [link](https://netchex.com/blog/hospitality-turnover-in-2026-industry-benchmarks-and-what-they-mean-for-your-labor-budget/) | Not checked | Vendors | Directional, **unverified** |
| E16 | France: reception, housekeeping and F&B are the roles under strain, with "particularly high" turnover. UMIH estimates about 200,000 positions are missing each year | L'Écho touristique · [link](https://www.lechotouristique.com/article/recrutement-dans-lhotellerie-crise-et-solutions) | Trade press citing UMIH | Date not checked | Directional, **unverified** |
| E17 | Only about **2-5 %** of travellers would let AI book without oversight | Hooray Agency white paper, Jul 2026, citing Skift/McKinsey · [PDF](https://lab.hooray.agency/wp-content/uploads/2026/07/What-AI-Knows-about-the-Traveler-Hooray-Agency-White-Paper.pdf) | Secondhand | Agency | Directional, **unverified** |
| E18 | Satisfied guests still switch hotels | Cornell Chronicle · "Hotel study's surprising results: some satisfied customers don't come back" · [link](https://news.cornell.edu/node/279407) | About 1,700 former guests of two three-star hotels; 24.1 % response | Academic, old, two properties | Directional, **unverified** |
| E19 | Marriott fined **£18.4m** by the UK ICO (GDPR Art. 32) after the Starwood breach, which exposed guest data including VIP status and loyalty numbers | Infosecurity Magazine / Mayer Brown · Oct-Nov 2020 · [link](https://www.infosecurity-magazine.com/news/marriott-fined-184m-over-data/) | Regulator decision | Old; a chain; a breach, not profiling | **Strong** as a fact. Weak as proof of boutique-hotel fear |

### 2b. Landscape: who already builds pieces of this

| # | Fact | Source · date | Flags |
|---|---|---|---|
| L1 | Revinate launched a "data activation platform" where Chat "logs that interest to the guest's profile" and "every question adds to their profile" | Revinate via hotel-online · 15 Oct 2026 · [link](https://www.hotel-online.com/news/revinate-launches-hospitalitys-first-data-activation-platform-guest-data-that-does-the-work) | Vendor. Accumulates *inferred interest*, which is the opposite of Anima's declared-only rule |
| L2 | Twilio announced **Conversation Memory**, persistent memory across interactions with humans or AI | Twilio press · 15 Oct 2026 · [link](https://www.twilio.com/en-us/press/releases/twilio-introduces-the-next-generation-of-its-platform-for-the-ag) | **Unverified** (search summary) |
| L3 | Apaleo: "The MCP Server provides AI agents a standardised way to read hotel data and perform actions." It builds on Agent Hub, launched earlier in 2025; an "MCP Alpha Group" is open | Hospitality Net · 23 Sep 2025 · [link](https://www.hospitalitynet.org/news/4129031.html) | Vendor news. **Anima's distribution channel** |
| L4 | Mem0 raised about $24M (seed + Series A, Oct 2025) and is YC-backed; reported as memory provider for AWS's Agent SDK. Letta raised a $10M seed (2024) | Pulse 2.0 · [link](https://pulse2.com/mem0-24-million-raised-for-powering-memory-layer-for-ai-agents/) | **Unverified** (search summary). Generic memory; none consent-first or hospitality-specific |
| L5 | YC hotel companies: Axelrod (S26, autonomous front- and back-of-house software), Riviera (W25, "AI employees" for hotels), Zaplar (S26, unified hotel stack). **No YC Request for Startups on hospitality or agent memory found** | YC directory · [link](https://www.ycombinator.com/companies/industry/Travel) | **Unverified** (search summaries; RFS page not opened) |
| L6 | Layla reports >$1B in planned trip value from 5M+ users (company figures, Mar 2026). Mindtrip monetises through booking commissions | Invest in Berlin · [link](https://invest-in.berlin/n/berlins-layla-hits-1b-in-ai-planned-trip-value/) | **Unverified**, company-reported |
| L7 | Meta's "Muse" agent finds, compares and books hotels, integrated with WhatsApp | hotel-online · Sep 2026 · [link](https://www.hotel-online.com/news/meta-unveils-muse-as-an-ai-agent-is-your-hotel-ready-to-be-found) | **Unverified** |
| L8 | Sirma positions "connected AI agents" for hotel operations | Hospitality Net · Oct 2026 · [link](https://www.hospitalitynet.org/news/4134633/sirma-brings-connected-ai-agents-to-hotel-operations-as-h2c-study-signals-hospitalitys-next-ai-phase) | **Unverified** (title only) |

Not covered in the time box: the guest-profile features of Oracle OPERA, Cendyn, Canary and HiJiffy, and Zep's funding.

---

## 3. Quote bank (verbatim, grouped by theme)

### A. Guests trust what they declared, not what was gathered (the strongest and newest theme)
- "Guests trust the data they share, not the data gathered about them" — Mews press release, section heading, 15 Oct 2026 (E1).
- "it lands best when it's built on what they chose to share" — same release.
- "Get that wrong and even good AI feels intrusive." — Josef Starýchfojtů, CPTO, Mews, same release.
- "57% of travelers say they would rather stay in control of their trip" — same release.
- "Fifty-one percent report discomfort sharing personal or financial information with AI agents." — Twilio global report, Nov 2025, via PPC Land (E5).

### B. Being forgotten and repeating yourself
- "More than half of consumers (54%) say AI agents rarely or never have previous context about them." — Twilio, Nov 2025 (E5).
- "75% of consumers say they have to repeat information they have already shared" — Twilio India, Sep 2026 (E6). *Cross-industry.*
- "Yet, over half (59%) were overlooked as a returning guest." — Mews, Jul 2022 (E9). *Old, UK.*
- "hoteliers infuriate 15% of guests further by asking the question 'have you stayed with us before?'" — same.
- "69% of hotel chains still enter or enrich guest preference data manually" — T. Ronson (Pertlink), Hospitality Net, Oct 2026, citing h2c (E8). *Secondhand.*
- "The AI heard the guest perfectly. The hotel then forgot" — same piece. *Consultant opinion.*
- "puede seguir sintiéndose como un desconocido al registrarse en recepción" ("may still feel like a stranger when checking in at the front desk") — Skift, content sponsored by Mindtrip, 29 Jun 2026.

### C. Memory is moving to the guest's side (the B2C signal)
- "¿Qué ocurre cuando un asistente de IA conoce a un viajero mejor que las marcas que compiten por su negocio?" ("What happens when an AI assistant knows a traveller better than the brands competing for their business?") — Skift / Mindtrip, 29 Jun 2026.
- "los viajeros deberían tener un mayor control sobre su información personal y sus preferencias" ("travellers should have more control over their personal information and preferences") — same.
- "This one is legible to her and closed to you." — Markus Busch, hospitality.today, via Hospitality Net, Sep 2026 ([link](https://www.hospitalitynet.org/opinion/4134566/the-agent-remembers-what-she-liked-not-where-she-stayed)), on ChatGPT-style assistant memory.
- "A preference is portable. A hotel is not." — same.

### D. A human stays in the loop
- "89% prefer a blend of AI and human service or AI working unobtrusively in the background." — Mews, 7 Oct 2026 (E4).
- "Human staff remain especially important for restaurant service (72%) and front-desk welcomes (66%)." — same.
- "unclear liability in the event of AI errors (56%)" — h2c, 1 Oct 2026 (E7).

### E. Room readiness (old or anecdotal only)
- "66% said they "always" or often have to wait for their room to be ready, even if they arrived past standard check in time." — hospitalityPulse, Nov 2016 (E10). *Old, self-selected.*
- Paraphrases, **unverified** (search summaries, not opened):
  - A guest with a confirmed early check-in found the suite not ready until 5 pm; the apology was a cheesecake and a beer (Loyalty Lobby, Jan 2026, [link](https://loyaltylobby.com/2026/01/06/reader-question-awful-stay-at-the-ritz-carlton-new-york-nomad-how-to-proceed/)).
  - A Hyatt guest waited until about 5 pm after a 3 pm check-in; the brand offered 2,500 points (View from the Wing, [link](https://viewfromthewing.com/what-does-a-hotel-owe-you-when-your-rooms-not-ready-at-check-in-time-2)).

### F. Hotelier voice
- **I found no recent, verbatim hotelier quote about requests lost in handoffs.** One consultancy blog says front office and housekeeping managers rated their communication between "poor" and "complete disaster" (RoomChecking; sample not stated; not opened; anecdotal, **unverified**). This is exactly the gap today's calls must fill.

---

## 4. Counter-evidence: what argues the pain is weak or already solved

1. **Personalisation isn't what most guests ask for.** Only 41 % want AI personalising the room, and in the UK only 30 % rate personalisation during a stay as important (E2).
2. **Hotels are pulling back from AI personalisation.** Its use fell from 22 % to 16 % (secondhand), and only 13 % of chains see measurable AI ROI (E7, E8). Chains plan more staff-facing agents (70 %) than guest-facing ones (55 %).
3. **Room waits are tolerated and cheaply compensated.** The data is from 2014-2016; recent cases show token gestures (points, a drink). Nothing recent links room readiness to churn.
4. **Recognition isn't the only reason guests return.** Satisfied guests still switch (E18, old).
5. **Incumbents shipped memory this month.** Revinate (L1) and Twilio (L2) on 15 Oct 2026, plus Mews guest insights and Mem0 (L4). "An AI that remembers the guest" is no longer a differentiator on its own; "remembers only what was declared, and forgets on schedule" still is (Revinate's design goes the other way).
6. **Traveller-side agents that push preferences to hotels are still rare:** about 2-5 % would let AI book unsupervised (E17, unverified). Screen 1's traveller agent is a forward-looking scenario, not today's volume. Present it that way.
7. **The front desk is the *more stable* department;** turnover is highest in housekeeping and F&B (E15, unverified). Knowledge leaks more on the handoff side than from the front desk's memory of guests.
8. **The 2022 Mews "59 %" is UK-only, has no published method and is four years old.** On its own it can't carry the problem slide.
9. **The "remember me" demand has a ceiling:** 66 % are uneasy giving an AI their full history (E5). This argues against "total recall" products. It *supports* Anima's minimal memory, but caps how much guests will declare.

---

## 5. Best three for the pitch slide and the "customer problem" criterion

1. **"Guests trust the data they share, not the data gathered about them."** (Mews, 3,250 travellers in 8 countries including France, 15 Oct 2026.) Show the figures: AI using *stated preferences* 61 %, *online behaviour* 43 %, *social data* 34 %. This is Anima's rule (declared only, no inference), published a week ago by the PMS our buyers use. **Strength: medium (vendor).**
2. **Hotels want AI agents but fear exactly this: unclear liability for AI errors (56 %) and data privacy (54 %).** (h2c AI Opportunity Study, 113 hotel chains, 1 Oct 2026, verified in the h2c release.) 70 % name AI agents as a key innovation area. That is the buyer's pain in the buyer's own survey. **Strength: medium (sponsored, chains).** Add "69 % still enter guest preferences by hand" only after checking the full report.
3. **The paradox: 54 % say AI agents rarely or never know their context, yet 66 % are uneasy handing an agent their full history.** (Twilio, 4,800 consumers in 15 countries, Nov 2025, method published.) In one line: guests want to be remembered, but not profiled, and that is Anima's position. **Strength: medium (vendor, cross-industry).**

Close with our own measured scenario (35 min wait → 0; asked three times → 0) and **one hotelier quote from today**. That quote would outrank all three.

---

## 6. Open questions for hotelier calls (today)

1. "When a guest tells you something before arrival (arrival time, a quiet room, a desk), where does it go, and who reads it before they arrive?" *Looking for a handoff story, in their words.*
2. "Last month, how many times did a guest arrive to a room that wasn't ready, or had a problem? What did you offer them?" *Frequency, and the cost of compensation.*
3. "How do you know a guest is returning, especially when they booked through Booking.com?" *Tests OTA email masking (E14).*
4. "When a receptionist leaves, what leaves with them?" *Turnover and knowledge loss.*
5. "If an assistant suggested moving a room up the housekeeping queue, would you click validate? What would it need to show you?" *Acceptance and explainability (pilot KPI ≥ 70 %).*
6. "If an AI remembered guests for you, what would worry you most: GDPR, mistakes, or guests finding it creepy?" *Checks E7 at a boutique hotel rather than a chain.*
7. "Would you pay for this per room per month through your PMS marketplace? Who decides: you or the owner?" *Who pays.*
8. "Has a guest ever asked what you keep about them, or asked you to delete it?" *Tests whether guest control is felt, or only principled.*

**Kill signal:** if all three calls answer Q1 with "it works fine" *and* Q6 with "not worried", then the amnesia pain is weak and boutique hotels don't feel the trust angle either. In that case, consider the hard pivot: sell the consent and memory layer to the vendors building hotel agents (via Apaleo or Mews marketplaces) rather than to hotels.
