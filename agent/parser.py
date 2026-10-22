"""LLM parser (AC1): one raw input -> one structured event with PROPOSED claims.

The LLM only reads and structures. It never writes memory (proposals go through the write
rule, R2) and never picks a room (that is the deterministic planner in reference/replay.py).

    from agent.parser import parse_llm
    event = parse_llm(item)            # item = one entry of data/raw_inputs.json

The output has the same shape as item["target"]. The item's own `target` is never sent to
the model: only channel, format, language, sender and payload, plus the context a live
agent would hold (guest directory with declared claims, and the planner's open offers).

Strict JSON comes from structured outputs (output_config.format) with a schema derived
from the golden target shapes: one object shape per event type.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODEL = os.environ.get("ANIMA_PARSER_MODEL", "claude-sonnet-5-5")
EFFORT = os.environ.get("ANIMA_PARSER_EFFORT", "low")
DAY = "2026-10-22"

# ------------------------------------------------------------------ schema
STR = {"type": "string"}
NSTR = {"anyOf": [{"type": "string"}, {"type": "null"}]}


def _obj(type_name: str, props: dict) -> dict:
    return {"type": "object",
            "properties": {"type": {"type": "string", "enum": [type_name]}, **props},
            "required": ["type", *props], "additionalProperties": False}


EVENT_SHAPES = [
    _obj("express_check_out", {"room": STR, "leaving_at": STR}),
    _obj("early_check_out", {"room": STR, "left_at": STR}),
    _obj("guest_message", {
        "resolved_guest_id": NSTR, "eta": NSTR, "train_departure": NSTR,
        "claims_to_write": {"type": "array", "items": STR},
        "already_known": {"type": "array", "items": STR},
        "fallback_offered_by_guest": NSTR}),
    _obj("out_of_service", {"room": STR, "reason": NSTR, "back_in_service": NSTR}),
    _obj("arrival_imminent", {"train": STR, "arrived": STR}),
    _obj("back_in_service", {"room": STR}),
    _obj("guest_reply", {
        "resolved_guest_id": NSTR, "declines_offer": NSTR,
        "claims_to_write": {"type": "array", "items": {
            "type": "object",
            "properties": {"key": STR,
                           "value": {"anyOf": [{"type": "boolean"}, {"type": "string"}, {"type": "number"}]},
                           "layer": {"type": "string", "enum": ["working", "semantic"]},
                           "scope": {"type": "string", "enum": ["this stay", "durable"]}},
            "required": ["key", "value", "layer", "scope"], "additionalProperties": False}}}),
]
SCHEMA = {"type": "object", "properties": {"event": {"anyOf": EVENT_SHAPES}},
          "required": ["event"], "additionalProperties": False}

# ------------------------------------------------------------------ prompt
SYSTEM = """You are the input parser of Anima, a guest memory for hotel AI agents (synthetic data).
You turn ONE raw input (guest WhatsApp or app message in French, housekeeping text, PMS webhook,
maintenance ticket, rail status JSON) into ONE structured event, using the JSON schema you are given.
You only read and structure. You never decide anything, never pick or suggest a room, never write
memory: anything under claims_to_write is a proposal that a separate write rule will check.

General rules
- Extract only what the input states. Never infer, never guess, no emotional inference. If a field
  is not stated in this input alone, use null (or an empty list).
- Times are "HH:MM", 24-hour, hotel local time. Drop dates and UTC offsets ("2026-10-22T07:05:00+02:00" -> "07:05", "7h" -> "07:00").
- Rooms are strings ("412"). Free-text values are short, lowercase, British English, no articles,
  no trailing punctuation, written in English even when the input is French. Translate the
  sender's own words literally, word for word; do not paraphrase or pick a synonym.

Event types (field "type")
- express_check_out: the PMS reports an express / online check-out; leaving_at = the announced departure time.
- early_check_out: the PMS reports that a reservation is checked out (the guest has left); left_at = when.
- guest_message: a guest writes to the hotel about their arrival or needs.
  - resolved_guest_id: match the sender against the guest directory (contact or id); null if no match.
  - eta: the arrival time the guest announces. train_departure: departure time of the train they say they take.
  - claims_to_write: keys of facts the guest newly declares in this message that belong in memory.
    Use snake_case keys; an announced arrival time is "eta". Do not list facts already in memory.
  - already_known: keys of claims already in this guest's memory that the message states again
    (the same need, said again). Not claims that are merely related to something in the message.
  - fallback_offered_by_guest: what the guest says they would accept if things are not ready,
    written as "<fallback> if <condition>" (e.g. "any room if sea view unavailable"); null if none.
- out_of_service: a room is blocked or cannot be sold.
  - reason: the defect itself in 1-3 words, adjective + noun style (e.g. "broken window", "faulty lock"); null if not stated.
  - back_in_service: only an explicitly stated time when the room is expected back in service.
    The time a technician comes is not a back-in-service time: then use null.
- arrival_imminent: a train or flight declared by a guest has arrived. train = the train name as given; arrived = time.
- back_in_service: a room that was out of service is usable again (e.g. maintenance ticket resolved).
- guest_reply: a guest answers a proposal from the hotel.
  - resolved_guest_id: as above.
  - declines_offer: the room of the open offer to this guest that they decline (see open_offers); null if they accept or none.
  - claims_to_write: objects {key, value, layer, scope}, only for what the reply says about the
    need the offer was made for (the offer's based_on_claims); other details of the reply are not claims.
    Reuse that claim's key, with the value the guest now states: declining a move offered for
    "sea_view" means sea_view is false for this stay.
    layer "working" + scope "this stay" for something true for this stay only;
    layer "semantic" + scope "durable" only if the guest says it is always true.

Answer with the JSON object only."""


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def default_context(item: dict) -> dict:
    """What a live agent knows when the input arrives: guests and their declared claims, and the
    planner's open offers (recommendations made before this input, waiting for a guest answer).
    Never the item's target, never the event log's summaries."""
    guests = []
    for g in _load("guests.json"):
        entry = {"guest_id": g["guest_id"], "name": g["name"]}
        if g.get("contact"):
            entry["contact"] = g["contact"]
        if g.get("claims"):
            entry["claims"] = [{"key": c["key"], "value": c["value"], "layer": c["layer"],
                                "statement": c["statement"]} for c in g["claims"]]
        guests.append(entry)
    # the planner's recommendation card cites claim ids; give the parser their keys
    claim_keys = {c["claim_id"]: c["key"] for g in _load("guests.json") for c in g.get("claims", [])}
    offers = []
    for ev in _load("events.json")["events"]:
        if ev["seq"] >= item.get("seq", 0):
            break
        for gid, exp in ev.get("expect", {}).items():
            if isinstance(exp, dict) and exp.get("suggest_room"):
                offers.append({"guest_id": gid, "room": exp["suggest_room"], "offered_at": ev["at"],
                               "based_on_claims": [claim_keys.get(c, c) for c in exp.get("must_cite", [])]})
    return {"date": DAY, "guest_directory": guests, "open_offers": offers}


def build_user_message(item: dict, context: dict) -> str:
    raw = {k: item[k] for k in ("channel", "format", "lang", "from", "payload") if k in item}
    return ("<context>\n" + json.dumps(context, ensure_ascii=False) + "\n</context>\n\n"
            "<raw_input>\n" + json.dumps(raw, ensure_ascii=False) + "\n</raw_input>")


_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic  # imported lazily so the dry run works without the SDK
        _client = anthropic.Anthropic()
    return _client


def parse_llm(item: dict, context: dict | None = None, *, with_usage: bool = False):
    """Parse one raw input. Returns the event dict (same shape as item["target"]);
    with_usage=True returns (event, usage) for cost reporting."""
    ctx = context if context is not None else default_context(item)
    response = _get_client().messages.create(
        model=MODEL,
        max_tokens=4000,
        # Sonnet 5.5 rejects non-default temperature; determinism comes from the strict schema
        # and low effort (adaptive thinking stays short).
        output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
        system=SYSTEM,
        messages=[{"role": "user", "content": build_user_message(item, ctx)}],
        # server-side fallback: if a safety classifier declines, the API reroutes by category
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
        extra_body={"fallbacks": "default"},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"parser refused: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("parser output truncated (max_tokens)")
    text = next(b.text for b in response.content if b.type == "text")
    event = json.loads(text)["event"]
    return (event, response.usage) if with_usage else event
