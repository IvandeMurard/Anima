# LLM parser report (AC1)

## Held-out set, 22 Oct 13:02

10 new synthetic inputs the prompt was never tuned on: `eval/heldout.json`. The set has 4 guest WhatsApp messages (2 from G001's number, 2 from unknown numbers), 1 guest reply to an open offer (the offer is given in the item's `context`), 2 housekeeping texts, 1 maintenance ticket JSON, 1 PMS webhook JSON with a different payload shape (room as an integer) and 1 rail status JSON with a different payload shape. The texts are messy English. All golden targets were written and saved before the first parser call and were not changed afterwards. Run: `python eval/run_heldout.py`. It calls `parse_llm(item, context)` with an explicit context: the guest directory from `data/guests.json`, no open offers from the recorded day, and only the item's own offers. It scores with the field rules of `eval/parse_eval.py` (it imports `norm`; matches must be exact after lowercasing; lists must match in order; `note` is not scored). `agent/parser.py` was unchanged (prompt v3). There was **one run**.

| | Score |
|---|---|
| **Held-out, prompt v3 unchanged, one run** | **47/47 = 100 %** |

- **Misses:** none. The two hard cases passed:
  - Ticket `M-2210-11`: the only time given was a technician slot, `"technician_slot": "14:30-15:00"`. It returned `back_in_service: null`.
  - G001 restated a need already in memory ("still need a quiet room pls not on the street side"). It returned `already_known: ["quiet_room"]` and `claims_to_write: ["eta"]` only, so the need was not written again.
- **Other fields on new wording:**
  - Free text matched exactly: `"sofa in lobby if room not ready"` and `"blocked toilet"`.
  - New claim keys matched the targets: `late_check_out`, `high_floor`.
  - A missed train was ignored: "missed the 9:04 … now on the 10:04" gave `10:04`.
  - A flight was not taken for a train: `train_departure` was null.
  - The integer room `118` came back as the string `"118"`.
  - The reply declined offer 310 and proposed `needs_desk = false`, this stay.
  - Extra key `reason: "no hot water"` on the ticket (not scored).
- **Latency and cost:** median 1.9 s per input, max 8.9 s. 43,599 tokens in and 618 out, about **$0.093 for 10 inputs ($0.009 per input)**. Nearly all input tokens are the guest directory and the system prompt.
- **Caveats:**
  - Small set: 10 inputs, 47 fields, one run.
  - I wrote the targets after reading the prompt, so they follow its conventions ("<fallback> if <condition>", adjective + noun reasons, `snake_case` keys). A guest phrasing far from those conventions, or a run with different key names (for example `cot` vs `baby_cot`), would show up as misses that this set does not test.
  - Synthetic messages written by the team, not real hotel traffic.
- **The honest sentence to say on stage:** "On 10 messy messages the parser had never seen, written and labelled before we ran it, it got 47 of 47 fields right in one run, about a cent per message. It's a small synthetic set, so read it as 'generalises beyond our demo script', not as a benchmark."

## English inputs, 22 Oct 12:15 (current dataset)

At 12:15 the guest and staff messages were switched to English so judges can read them (ROADMAP decision log). The three free-text inputs were rewritten as messy English texting with the same facts: #1 WhatsApp ("taking the 9:04 TGV so ill be there around 11:15. gotta work as soon as i arrive, if the room isnt ready a quiet corner is fine :)"), #3 housekeeping text ("tap is leaking … plumber around 3pm, im blocking the room"), #7 guest-app reply ("thx but no need to change rooms, im going to the concert tonight, back around 1am"). No golden target changed: the English wording already matches "quiet corner if room not ready" and "leaking tap". `agent/parser.py` was **not** touched (prompt v3, as below).

| | Score from `eval/parse_eval.py` |
|---|---|
| **English inputs, prompt v3 unchanged, one run** | **29/29 = 100 %** |

- **Misses:** none. Free-text fields came back exact (`fallback_offered_by_guest: "quiet corner if room not ready"`, `reason: "leaking tap"`); "plumber around 3pm" was again kept out of `back_in_service` (null); #7 proposed `quiet_room=false`, this stay. Extra key `reason: "leak"` on #4 (not scored).
- **Cost and latency:** 34,778 tokens in, 395 out, ≈ $0.074 per run; median 1.5 s per input, max 6.1 s (first call), wall 16.5 s.
- **Caveat:** prompt v3 was tuned on the French versions of these same 8 messages. The English texts are new wording, but the facts and targets are identical, so this is **not a held-out set**. One run only.
- **The honest sentence to say on stage:** "Recorded scenario, 8 synthetic messy inputs: 29 of 29 fields correct, live, with a prompt we tuned this morning on the same scenario; there's no held-out set yet, so treat it as 'works on our day', not a benchmark."

## History: French inputs (before 12:15)

Recorded scenario, synthetic data, 8 raw inputs, **29 scored fields** (the `note` key is not scored). Measured 22 Oct 2026 with `python eval/run_llm_parse.py`, which calls `parse_llm` on every input, writes `eval/predictions.json` and runs `python eval/parse_eval.py`. Nothing in `data/`, the targets or the scorer was changed.

### Result (French inputs)

| | Score from `eval/parse_eval.py` |
|---|---|
| **First live run, untuned prompt** | **28/29 = 97 %** |
| Final prompt (v3), 3 consecutive runs | 29/29 = 100 %, 29/29 = 100 %, 29/29 = 100 % |

AC1 (≥ 90 %) passes on every run, including the first one. **How to say it:** "recorded scenario, 8 inputs, 97 % of fields correct with an untuned prompt; 100 % on 3 runs after tuning the prompt on the same 8 inputs". The 100 % comes from tuning on these same 8 inputs (no held-out set), so the honest number for new messages is closer to the untuned 97 %. It is not the golden replay: `PARSER=golden` copies the targets, while these are live model outputs.

### Per input, final prompt (last v3 run on French inputs; `eval/predictions.json` now holds the English run)

| # | Channel | Fields | Correct | Notes |
|---|---|---|---|---|
| 0 | PMS webhook (express checkout) | 3 | 3 | |
| 1 | WhatsApp, French | 7 | 7 | guest resolved by phone number; `needs_desk` recognised from "je dois bosser en arrivant" |
| 2 | PMS webhook (checked out) | 3 | 3 | |
| 3 | Housekeeping text, French | 4 | 4 | `back_in_service: null`: "plombier vers 15h" is a plumber visit, not a return time |
| 4 | Maintenance ticket | 3 | 3 | extra key `reason: "leak"` (not scored) |
| 5 | Rail status JSON | 3 | 3 | |
| 6 | Maintenance ticket (resolved) | 2 | 2 | |
| 7 | Guest app reply, French | 4 | 4 | declines offer 206; proposes `quiet_room=false`, this stay |
| | **Total** | **29** | **29** | |

### All runs

| Prompt | Runs | Scores | Fields missed |
|---|---|---|---|
| v1 (untuned) | 1 | 28/29 = 97 % | #7 `claims_to_write`: proposed `returns_late: "around 01:00"` instead of `quiet_room: false` |
| v2: open offers carry the claim keys they were based on, plus a rule for replies | 3 | 28, 28, 29 /29 (97, 97, 100 %) | #1 `fallback_offered_by_guest`: "quiet **area** if room not ready" vs "quiet **corner**" (2 of 3 runs) |
| v3 (final): "translate the sender's words literally, no synonyms" | 3 | 29, 29, 29 /29 (100 %) | none |

### Failures and why (French runs)

1. **#7, reply to an offer (v1).** The model proposed a claim for the detail it saw ("je rentre vers 1h") rather than for the need the offer addressed. The context listed the open offer (room 206) but not *why* it was offered. Fix: the planner's recommendation card already cites C070; `default_context` now turns cited claim ids into keys (`based_on_claims: ["quiet_room", ...]`), and the prompt says a reply's claims cover only that need. That is context the live agent has, not the answer.
2. **#1, free-text fallback (v2).** "un coin calme" came back as "quiet area" or "quiet corner": both are right, but the scorer matches exact strings. Fix: a general rule to translate the guest's own words literally. That also fits the product rule that memory keeps what the guest declared, not a paraphrase.
3. **Remaining risk.** Two fields are free text (`reason`, `fallback_offered_by_guest`) and only exact matches score. On new messages, expect wording misses on those fields first. Structured fields (times, rooms, ids, types) were never wrong in any run.

## Model and prompt approach

- **Model:** `claude-sonnet-5-5`, Anthropic Python SDK (`anthropic` 0.109.1), `messages.create`, `output_config.effort = "low"` (adaptive thinking stays short).
- **Strict JSON:** structured outputs (`output_config.format = json_schema`). The schema comes from the golden target shapes: one object shape per event type (`express_check_out`, `early_check_out`, `guest_message`, `out_of_service`, `arrival_imminent`, `back_in_service`, `guest_reply`), combined with `anyOf` under a root `{"event": ...}`. `parse_llm` returns the inner event. A forced tool was not an option: Sonnet 5.5 returns a 400 on forced `tool_choice`.
- **Temperature 0 is not used:** Sonnet 5.5 returns a 400 on any non-default `temperature`. The strict schema and low effort keep outputs stable: the three v3 runs used the same input tokens and scored the same 29/29 (output tokens varied by one at most).
- **Refusals:** server-side fallback is on (`anthropic-beta: server-side-fallback-2026-07-01`, `fallbacks: "default"`). A `refusal` or `max_tokens` stop raises instead of returning partial JSON.
- **Prompt:** a system prompt with general rules (extract only what is stated, `HH:MM` local time, short lowercase British-English free text, literal translation) and one paragraph per event type, written as field definitions. Its examples are invented ("broken window", "faulty lock", "any room if sea view unavailable", "sea_view"). **No few-shot example comes from the dataset**, and no target string appears in the prompt.
- **No leakage:** the user message holds only `channel`, `format`, `lang`, `from` and `payload` of the item, plus context. **Context** = the guest directory (id, name, contact, declared claims with key, value, layer and statement, from `data/guests.json`) and the planner's open offers before the input's `seq` (room, time, and the keys of the claims the recommendation cited). Open offers are read from the oracle's recorded recommendations in `data/events.json` (`expect.*.suggest_room` / `must_cite`), the same decisions the planner makes live at seq 9. Nothing else from `events.json` is sent: no summaries, no details. In the demo, these offers can come from the planner's live state instead (pass `context=`).
- **Boundaries:** the model never writes memory (`claims_to_write` are proposals for the write rule, R2) and never picks a room (`declines_offer` only names the room of an existing offer).

## Cost and latency (8 inputs, final prompt)

| | Value |
|---|---|
| Tokens per run | ~34,800 in (~4,300 per input, mostly the guest directory), ~395 out |
| Cost per run | **≈ $0.074** (at $2 / $10 per M tokens), ≈ $0.009 per input |
| Latency per input | median 1.4-1.7 s, max 3.1-4.3 s; the first call after a schema change takes ~11 s (one-time schema compilation, cached 24 h) |
| Wall time, 8 inputs in sequence | 14-15 s |

For the live demo, do one warm-up call before going on stage so nobody waits ~11 s. Cutting the directory to guests with a contact or claims would roughly halve input tokens; at this scale it isn't worth it.

## Wiring into `demo/run_demo.py` (not applied: another session owns that file)

Replace the body of `parse()` (around line 126):

```python
def parse(item: dict) -> dict:
    """Step 1. PARSER=golden replays the golden target (recorded); PARSER=llm calls agent/parser.py (live)."""
    if PARSER == "golden":
        return dict(item["target"])
    if PARSER == "llm":
        sys.path.insert(0, str(ROOT))
        from agent.parser import parse_llm
        return parse_llm(item)
    raise SystemExit(f"unknown PARSER={PARSER!r} (golden | llm)")
```

`main()` already writes `eval/predictions.json` from `parse()`, so `PARSER=llm python demo/run_demo.py --reset` followed by `python eval/parse_eval.py` scores the live run. Deploy notes: set `ANTHROPIC_API_KEY` on Aiven Runtime, copy `agent/` into the image, and install `demo/requirements.txt`, which now includes `anthropic>=0.109`.

## Files

- `agent/__init__.py`, `agent/parser.py`: `parse_llm(item, context=None, *, with_usage=False)`, `default_context(item)`, `SCHEMA`, `SYSTEM`.
- `eval/run_llm_parse.py`: live run plus scoring; `--dry-run` prints the prompt for input #1 and the schema, with no API call. The key comes from the environment; if it is unset, only the `ANTHROPIC_API_KEY` line of `.env` is read.
- `demo/requirements.txt`: `anthropic>=0.109` added.
