"""LLM parser (step 1 of the agent loop): raw hotel input -> structured event + PROPOSED claims.

Claude reads the raw input (French WhatsApp, housekeeping text, PMS webhook, ticket, rail JSON) with
the context the agent already holds (guests with memory, open offers) and returns strict JSON that
validates against EVENT_SCHEMA (structured outputs). It never writes memory and never decides:
proposals go through the write rule (R2) and the deterministic planner, as before.

The golden targets in data/raw_inputs.json are NOT shown to the model; eval/parse_eval.py scores them.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
MODEL = os.environ.get("ANIMA_MODEL", "claude-opus-5-5")


def _load_dotenv():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

HHMM = {"type": "string", "description": "local time, 24h HH:MM"}
NULLABLE_HHMM = {"anyOf": [HHMM, {"type": "null"}]}
CLAIM_KEYS = ["quiet_room", "needs_desk", "ready_if_early", "late_check_out", "extra_pillows", "eta"]  # keys of the data model; "eta" holds the declared train too


def _event(type_: str, desc: str, props: dict) -> dict:
    return {
        "type": "object",
        "description": desc,
        "properties": {"type": {"type": "string", "enum": [type_]}, **props},
        "required": ["type", *props],
        "additionalProperties": False,
    }


EVENT_SCHEMA = {
    "anyOf": [
        _event("express_check_out", "A guest announced they will leave a room early (folio express checkout).",
               {"room": {"type": "string"}, "leaving_at": HHMM}),
        _event("early_check_out", "A guest has already checked out of a room.",
               {"room": {"type": "string"}, "left_at": HHMM}),
        _event("guest_message", "A message from a guest with memory, about their arrival or stay.", {
            "resolved_guest_id": {"type": "string", "description": "guest_id matched from the sender's contact"},
            "eta": NULLABLE_HHMM,
            "train_departure": NULLABLE_HHMM,
            "claims_to_write": {"type": "array", "items": {"type": "string", "enum": CLAIM_KEYS},
                                "description": "keys of NEW facts the guest declared in this message, not already in memory"},
            "already_known": {"type": "array", "items": {"type": "string", "enum": CLAIM_KEYS},
                              "description": "keys the guest repeated that memory already holds for this stay"},
            "fallback_offered_by_guest": {"anyOf": [{"type": "string"}, {"type": "null"}],
                                          "description": "a fallback the guest offers, short English phrase '<what> if <condition>'"},
        }),
        _event("out_of_service", "A room cannot be sold (damage, leak, maintenance).", {
            "room": {"type": "string"},
            "reason": {"anyOf": [{"type": "string"}, {"type": "null"}],
                       "description": "short English noun phrase, e.g. 'broken lock'"},
            "back_in_service": {**NULLABLE_HHMM, "description": "only if this input states it explicitly, else null"},
        }),
        _event("arrival_imminent", "A tracked train (declared by a guest) has arrived.",
               {"train": {"type": "string", "description": "e.g. 'TGV 1234'"}, "arrived": HHMM}),
        _event("back_in_service", "A room that was out of service is usable again.", {"room": {"type": "string"}}),
        _event("guest_reply", "A guest answers an offer the hotel made.", {
            "resolved_guest_id": {"type": "string"},
            "declines_offer": {"anyOf": [{"type": "string"}, {"type": "null"}],
                               "description": "room number of the declined offer, null if accepted"},
            "claims_to_write": {"type": "array", "items": {
                "type": "object",
                "properties": {"key": {"type": "string", "enum": CLAIM_KEYS}, "value": {"type": "boolean"},
                               "layer": {"type": "string", "enum": ["working", "semantic"]},
                               "scope": {"type": "string", "enum": ["this stay", "durable"]}},
                "required": ["key", "value", "layer", "scope"], "additionalProperties": False}},
        }),
    ]
}

SYSTEM = """You are the input parser of Anima, a guest memory for a hotel front office.
You turn one raw input (often messy French text, or a system JSON) into one structured event.

Rules:
- Extract only what the input says. Never infer preferences, emotions or traits.
- Times: 24h HH:MM, hotel local time. Convert ISO timestamps to their local HH:MM.
- Resolve a guest only by matching the sender's contact or app user id to the context. Never guess.
- Claims: a claim is a fact the guest DECLARED. Use 'working' / 'this stay' for things true only for
  this stay; 'semantic' / 'durable' only if the guest says it is a lasting preference.
- A message that turns down an offer for this stay does not erase a durable preference: write a
  this-stay claim, never a durable one.
- Output English values; keep room numbers and train numbers as written."""


_client: anthropic.Anthropic | None = None


def parse_llm(item: dict, context: dict) -> dict:
    """item: one raw input (target removed). context: guests with memory + open offers."""
    global _client
    _client = _client or anthropic.Anthropic()
    raw = {k: v for k, v in item.items() if k != "target"}
    user = ("Context the agent already holds:\n" + json.dumps(context, ensure_ascii=False, indent=1)
            + "\n\nRaw input:\n" + json.dumps(raw, ensure_ascii=False, indent=1))
    r = _client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": EVENT_SCHEMA}},
    )
    if r.stop_reason == "refusal":
        raise RuntimeError(f"parser refused input seq {item.get('seq')}: {r.stop_details}")
    text = next(b.text for b in r.content if b.type == "text")
    return json.loads(text)
