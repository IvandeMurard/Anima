"""Generate the SYNTHETIC hackathon dataset for Anima (Accel AI Innovate Paris, 22 Oct 2026). v2

Everything here is fake: every guest carries "synthetic": true and a "SYN-" name.
No real guest data may ever be added (DPIA gate).

The line that keeps "memory without surveillance" true:
  - About the PERSON, Anima stores only what they DECLARED, under a consented purpose,
    with a retention period. Inferred guesses are never written: they are proposed,
    then refused, and the refusal is shown.
  - About the STAY, the HOTEL and the WORLD (rooms, housekeeping, maintenance, trains,
    local events): as many sources as needed. Context never becomes a claim about a person.

Writes: hotel.json, guests.json, reservations.json, housekeeping.json, context.json,
        events.json, raw_inputs.json
Run:    python data/generate.py
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DAY = "2026-10-22"


def t(hhmm: str) -> str:
    return f"{DAY}T{hhmm}:00+02:00"


# ------------------------------------------------------------------ hotel
# 4 floors x 6 rooms. x01-x03 street side, x04-x06 courtyard.
# x03 and x04 sit next to the lift. x02, x05, x06 are Superior (with desk).
def room(floor: int, n: int) -> dict:
    superior = n in (2, 5, 6)
    return {"room": f"{floor}0{n}", "floor": floor, "side": "street" if n <= 3 else "courtyard",
            "lift_adjacent": n in (3, 4), "category": "superior" if superior else "standard",
            "desk": superior, "accessible": f"{floor}0{n}" == "306"}


HOTEL = {
    "synthetic": True, "name": "Maison Lumen (fictional)", "city": "Paris 11e", "rooms_total": 24,
    "standard_check_in": "15:00", "standard_check_out": "11:00",
    "housekeeping": {
        "attendants_on_departures": 2,
        "available_from": "08:00",
        "note": "Stayover service is done by a third attendant and is not modelled.",
        "minutes_departure_clean": 40,
        "minutes_reclean_after_maintenance": 30,
        "minutes_inspection": 10,
    },
    "category_rank": {"standard": 1, "superior": 2},
    "rooms": [room(f, n) for f in range(1, 5) for n in range(1, 7)],
}

# ------------------------------------------------------------------ guests and claims
# A claim is one statement held about a guest. Stored origin: "declared" only.
# layer "working" = this stay only; "semantic" = 36 months rolling from last confirmation.
# A newer declared claim for this stay overrides a durable one for this stay only, and the durable
# one is flagged for reconfirmation next stay (never silently overwritten).
RETENTION = {"working": "until check-out", "semantic": "36 months rolling from last_confirmed"}


def claim(cid, statement, key, value, source, purpose, first_seen, last_confirmed=None,
          confirmations=1, layer="semantic"):
    return {"claim_id": cid, "statement": statement, "key": key, "value": value,
            "origin": "declared", "source": source, "purpose": purpose,
            "first_seen": first_seen, "last_confirmed": last_confirmed or first_seen,
            "confirmations": confirmations, "layer": layer, "retention": RETENTION[layer]}


def consent(*purposes):
    """Consent is given per purpose, each with its own date and channel, decoupled from booking."""
    return {"purposes": [{"name": n, "given": d, "via": v} for n, d, v in purposes],
            "decoupled_from_booking": True}


P_STAY, P_ARRIVAL = "stay personalisation", "arrival coordination"

GUESTS = [
    {"guest_id": "G001", "name": "SYN-Claire Laurent", "stays_before": 2,
     "contact": "+33 6 00 00 00 01 (SYN)",
     "consent": consent((P_STAY, "2025-03-14", "front desk tablet"),
                        (P_ARRIVAL, "2026-10-19", "pre-arrival form")),
     "claims": [
         claim("C001", "Asks for a quiet room, away from the street", "quiet_room", True,
               "front desk note, stay 1; pre-arrival form, stay 2", P_STAY,
               "2025-03-14", "2025-11-06", confirmations=2),
         claim("C002", "Works on arrival this stay: needs a desk", "needs_desk", True,
               "pre-arrival form, this stay", P_STAY, "2026-10-19", layer="working"),
         claim("C003", "Told us at check-out that she waited 2h for her room, and asked us to "
                       "have it ready if she comes early again", "ready_if_early", True,
               "check-out feedback, stay 2 (a service failure on our side)", P_STAY, "2025-11-08"),
     ]},
    {"guest_id": "G007", "name": "SYN-Malik Benali", "stays_before": 4,
     "consent": consent((P_STAY, "2022-05-02", "guest app")),
     "claims": [
         claim("C070", "Asks for a quiet room (asked to move once because of street noise)",
               "quiet_room", True, "guest message, stay 3", P_STAY, "2025-09-20", "2026-04-11",
               confirmations=2),
         claim("C071", "Asks for a late check-out", "late_check_out", True,
               "front desk note, stay 1", P_STAY, "2023-05-20"),   # 41 months old on day D: expired
     ]},
    {"guest_id": "G008", "name": "SYN-Hugo Martin", "stays_before": 3,
     "consent": consent((P_STAY, "2025-01-10", "pre-arrival form")),
     "claims": [
         claim("C080", "Asks for two extra pillows", "extra_pillows", True,
               "pre-arrival form, stay 2", P_STAY, "2025-06-01", "2026-02-15", confirmations=2),
     ]},
    {"guest_id": "G012", "name": "SYN-Tom Reyes", "stays_before": 0, "consent": None, "claims": []},
]
for gid in ["G002", "G003", "G004", "G005", "G006", "G009", "G010", "G011"] + \
           [f"G0{n}" for n in range(13, 29)]:
    GUESTS.append({"guest_id": gid, "name": f"SYN-Guest {gid}", "stays_before": 0,
                   "consent": None, "claims": []})
GUESTS.sort(key=lambda g: g["guest_id"])
for g in GUESTS:
    g["synthetic"] = True

# ------------------------------------------------------------------ reservations (day D)
# 10 stayovers + 10 arrivals tonight on 23 sellable rooms (405 out of order) = 87 %.
# Only R-G004 is locked (accessible room). Every other arrival is placed by the planner.
STAYOVERS = {"102": "G010", "104": "G011", "105": "G005", "106": "G006", "202": "G009",
             "205": "G017", "302": "G007", "303": "G018", "401": "G019", "406": "G026"}
DEPARTURES = {"101": ("G020", "09:00"), "103": ("G021", "09:15"), "201": ("G022", "09:30"),
              "203": ("G023", "09:45"), "301": ("G024", "09:45"), "404": ("G025", "10:00"),
              "206": ("G003", "11:00"), "305": ("G002", "11:00")}   # known departure times (PMS)
RESERVATIONS = {
    "synthetic": True, "date": DAY,
    "arrivals": [
        {"res_id": "R-G001", "guest_id": "G001", "category": "superior", "nights": 2, "eta": "15:00",
         "pms_preassigned_room": "402", "pms_rule": "highest available floor in booked category"},
        {"res_id": "R-G004", "guest_id": "G004", "category": "superior", "nights": 3, "eta": "10:30",
         "assigned_room": "306", "locked": True,
         "lock_reason": "booking constraint (kept in the PMS; Anima does not need the reason)"},
        {"res_id": "R-G008", "guest_id": "G008", "category": "standard", "nights": 1, "eta": "17:00"},
        {"res_id": "R-G012", "guest_id": "G012", "category": "standard", "nights": 1, "eta": "17:30"},
    ] + [
        {"res_id": f"R-{g}", "guest_id": g, "category": "standard", "nights": 1, "eta": eta}
        for g, eta in [("G013", "14:00"), ("G014", "15:00"), ("G015", "15:30"), ("G016", "16:00"),
                       ("G027", "16:30"), ("G028", "18:00")]
    ],
    "departures": [{"guest_id": g, "room": r, "planned_check_out": dep} for r, (g, dep) in DEPARTURES.items()],
    "stayovers": [{"guest_id": g, "room": r} for r, g in STAYOVERS.items()],
}

# ------------------------------------------------------------------ housekeeping at 07:00
STATUS = {r["room"]: "vacant_clean" for r in HOTEL["rooms"]}
STATUS.update({r: "occupied_stayover" for r in STAYOVERS})
STATUS.update({r: "occupied_due_out" for r in DEPARTURES})
STATUS["405"] = "out_of_order"
HOUSEKEEPING = {
    "synthetic": True, "as_of": t("07:00"),
    "rooms": [{"room": k, "status": v} for k, v in sorted(STATUS.items())],
    "default_queue": ["101", "103", "201", "203", "301", "404", "206", "305"],
    "default_queue_rule": "by known departure time, then room number",
    "notes": {"405": "renovation until 2026-11-03 (out of order: off inventory)",
              "306": "held for R-G004 (booking constraint)"},
}

# ------------------------------------------------------------------ context (never about a person)
CONTEXT = {
    "synthetic": True,
    "sources": [
        {"id": "X-EVT-1", "kind": "local_event", "source": "city events feed (simulated)",
         "summary": "Live concert at Le Volta (fictional venue), 40 m away, street side",
         "window": [t("20:00"), t("23:30")], "affects": {"side": "street", "noise": "high"}},
        {"id": "X-TR-1", "kind": "transport", "source": "rail status API (simulated)",
         "summary": "TGV 6612 Lyon-Paris",
         "used_only_if": "a guest declared this train for arrival coordination"},
    ],
}

# ------------------------------------------------------------------ the day, as a replayable script
EVENTS = [
    {"seq": 1, "at": "07:00", "type": "day_start", "source": "PMS + housekeeping + events feed",
     "summary": "Day opens. PMS pre-assigned SYN-Claire Laurent to 402 (high floor, street side). "
                "A traveller-side AI agent pushes 'prefers high floors' for her (its own inference).",
     "detail": {"proposed_claim": {"guest_id": "G001", "statement": "Prefers a high floor", "key": "high_floor",
                                   "origin": "inferred", "source": "traveller-side AI agent (its own inference)"}},
     "expect": {"G001": {"recommend_room": "206", "ready_by": "11:50", "must_cite": ["C001", "X-EVT-1"],
                         "write_refused": "high_floor"},
                "G007": {"watch": True, "must_cite": ["C070", "X-EVT-1"], "no_option_yet": True,
                         "expired_and_deleted": "C071"},
                "why": "402 faces the street and a concert runs there tonight; she asked twice for quiet. "
                       "206 is courtyard with a desk and ready at 11:50, before her 15:00 ETA. The agent's "
                       "'high floor' guess is refused at the door: she never said it."}},
    {"seq": 2, "at": "08:15", "type": "express_check_out", "source": "PMS webhook",
     "detail": {"room": "206", "leaving_at": "09:30"},
     "summary": "Guest in 206 checks out online, leaving at 09:30 instead of 11:00.",
     "expect": {"G001": {"no_change": True}}},
    {"seq": 3, "at": "08:40", "type": "guest_message", "source": "WhatsApp (guest, FR)",
     "detail": {"from_contact": "+33 6 00 00 00 01 (SYN)",
                "write_claim": {"claim_id": "C005", "guest_id": "G001", "key": "eta", "value": "11:15",
                                "statement": "Arriving around 11:15 on the 9:04 TGV (TGV 6612)",
                                "train": "TGV 6612", "source": "WhatsApp, this stay",
                                "purpose": P_ARRIVAL, "layer": "working"}},
     "summary": "SYN-Claire Laurent: 'je prends le TGV de 9h04, je serai là vers 11h15'.",
     "expect": {"G001": {"recommend_room": "206", "keep_current": True, "prioritise_cleaning": "206",
                         "ready_by": "10:30", "static_ready_by": "11:50", "must_cite": ["C005", "C003"], "must_not_cite": ["X-EVT-1"],
                         "claim_written": "C005"},
                "why": "Same room, cleaned first: 206 empties at 09:30. In the normal queue it would be ready "
                       "at 11:50 (35 min wait); moved to the front it is ready at 10:30. Last time she waited 2h "
                       "and asked us not to repeat it."}},
    {"seq": 4, "at": "10:05", "type": "early_check_out", "source": "PMS webhook",
     "detail": {"room": "305", "left_at": "10:05"}, "summary": "Guest in 305 checks out early.",
     "expect": {"G001": {"no_change": True}}},
    {"seq": 5, "at": "10:20", "type": "out_of_service", "source": "housekeeping app message + maintenance ticket",
     "detail": {"room": "206", "back_in_service": "16:00"},
     "summary": "Housekeeping reports a leak in 206; maintenance ticket: plumber 15:00, back in service 16:00.",
     "expect": {"G001": {"recommend_room": "305", "ready_by": "11:10", "prioritise_cleaning": "305",
                         "no_alternative": True, "must_cite": ["C001", "C002"]},
                "why": "305 freed at 10:05. The attendant who just finished 206 takes it next instead of 203: "
                       "ready 11:10, before she arrives. No wait, so no lesser room is offered."}},
    {"seq": 6, "at": "11:05", "type": "arrival_imminent", "source": "rail status API",
     "detail": {"train": "TGV 6612", "arrived": "10:52"},
     "summary": "Her declared train arrived 10:52. Brief the front desk.",
     "expect": {"G001": {"rail_used_because": "C005", "brief_max_sentences": 2,
                         "brief_must_mention": ["third stay", "305", "desk"],
                         "brief_must_not_mention": ["high floor", "concert", "waited"]}}},
    {"seq": 7, "at": "11:15", "type": "check_in", "source": "PMS + front desk", "guest_id": "G001",
     "detail": {"confirm_claim": "C001", "said": "Oh, the courtyard side, perfect, thank you."},
     "summary": "SYN-Claire Laurent arrives and confirms she likes the quiet courtyard side.",
     "expect": {"G001": {"wait_minutes": 0, "confirmed": "C001", "confirmations": 3,
                         "last_confirmed": "2026-10-22"},
                "why": "Memory gets stronger when the guest confirms it: the 36-month clock restarts today."}},
    {"seq": 8, "at": "14:00", "type": "consent_withdrawn", "source": "guest app",
     "detail": {"guest_id": "G008"}, "summary": "SYN-Hugo Martin withdraws his consent in the app.",
     "expect": {"G008": {"claims_deleted": True}}},
    {"seq": 9, "at": "16:00", "type": "back_in_service", "source": "maintenance ticket",
     "detail": {"room": "206"}, "summary": "Plumber done: 206 back in service, needs a quick re-clean.",
     "expect": {"G007": {"suggest_room": "206", "ready_by": "16:40", "before": "20:00",
                         "needs_human_validation": True, "must_cite": ["C070", "X-EVT-1"],
                         "no_claim_created_from_context": True},
                "why": "The room with the leak becomes the answer for the guest under the concert."}},
    {"seq": 10, "at": "16:20", "type": "guest_reply", "source": "guest app (FR)",
     "detail": {"guest_id": "G007",
                "write_claim": {"claim_id": "C072", "guest_id": "G007", "key": "quiet_room", "value": False,
                                "statement": "No need to move tonight: he is going to the concert, back around 1am",
                                "source": "guest app, this stay", "purpose": P_STAY, "layer": "working",
                                "scope": "this stay"}},
     "summary": "SYN-Malik Benali declines the move: 'pas la peine, je vais au concert, je rentre vers 1h'.",
     "expect": {"G007": {"suggestion_withdrawn": True, "hold_released": "206",
                         "durable_kept": "C070", "reconfirm_next_stay": "C070", "stay_claim_written": "C072"},
                "why": "The newest thing he said wins for tonight. It does not erase what he asked for twice: "
                       "next stay, the front desk simply checks."}},
    {"seq": 11, "at": "17:00", "type": "arrivals", "source": "PMS",
     "summary": "SYN-Hugo Martin (3 past stays, consent withdrawn) and SYN-Tom Reyes (first stay, no consent) arrive.",
     "expect": {"G008": {"cites_nothing": True, "would_have_cited_before_withdrawal": "C080"},
                "G012": {"cites_nothing": True}}},
]

# ------------------------------------------------------------------ raw, messy inputs + parsing targets
# What the hotel actually receives. Job #1 of the LLM on the day: raw -> `target`.
# The team tests its parser against `target` (golden), not against the event text.
RAW_INPUTS = [
    {"seq": 2, "channel": "PMS webhook", "format": "json",
     "payload": {"event": "folio.express_checkout", "room": "206", "departure_time": t("09:30")},
     "target": {"type": "express_check_out", "room": "206", "leaving_at": "09:30"}},
    {"seq": 3, "channel": "WhatsApp (guest)", "format": "text", "lang": "fr",
     "from": "+33 6 00 00 00 01 (SYN)",
     "payload": "Bonjour ! Finalement je prends le TGV de 9h04, je serai là vers 11h15. "
                "Je dois bosser en arrivant, si jamais la chambre n'est pas prête un coin calme suffira :)",
     "target": {"type": "guest_message", "resolved_guest_id": "G001", "eta": "11:15", "train_departure": "09:04",
                "claims_to_write": ["eta"], "already_known": ["needs_desk"],
                "fallback_offered_by_guest": "quiet corner if room not ready"}},
    {"seq": 4, "channel": "PMS webhook", "format": "json",
     "payload": {"event": "reservation.checked_out", "room": "305", "at": t("10:05")},
     "target": {"type": "early_check_out", "room": "305", "left_at": "10:05"}},
    {"seq": 5, "channel": "housekeeping app (text message)", "format": "text", "lang": "fr",
     "payload": "206 salle de bain finie mais le robinet fuit, ça coule par terre. "
                "SYN-Karim (maintenance) dit plombier vers 15h, je bloque la chambre",
     "target": {"type": "out_of_service", "room": "206", "reason": "leaking tap", "back_in_service": None,
                "note": "time unknown from this message alone"}},
    {"seq": 5, "channel": "maintenance ticket", "format": "json",
     "payload": {"ticket": "M-2210-04", "room": "206", "issue": "leak", "plumber_eta": "15:00",
                 "expected_back_in_service": "16:00"},
     "target": {"type": "out_of_service", "room": "206", "back_in_service": "16:00"}},
    {"seq": 6, "channel": "rail status API (simulated)", "format": "json",
     "payload": {"train": "TGV 6612", "status": "arrived", "station": "Paris Gare de Lyon", "at": "10:52"},
     "target": {"type": "arrival_imminent", "train": "TGV 6612", "arrived": "10:52"}},
    {"seq": 9, "channel": "maintenance ticket", "format": "json",
     "payload": {"ticket": "M-2210-04", "room": "206", "status": "resolved", "at": "16:00"},
     "target": {"type": "back_in_service", "room": "206"}},
    {"seq": 10, "channel": "guest app (text)", "format": "text", "lang": "fr", "from": "SYN app user G007",
     "payload": "Merci mais pas la peine de changer, je vais au concert ce soir, je rentre vers 1h",
     "target": {"type": "guest_reply", "resolved_guest_id": "G007", "declines_offer": "206",
                "claims_to_write": [{"key": "quiet_room", "value": False, "layer": "working", "scope": "this stay"}]}},
]

if __name__ == "__main__":
    files = {"hotel.json": HOTEL, "guests.json": GUESTS, "reservations.json": RESERVATIONS,
             "housekeeping.json": HOUSEKEEPING, "context.json": CONTEXT,
             "events.json": {"synthetic": True, "date": DAY, "events": EVENTS},
             "raw_inputs.json": {"synthetic": True, "inputs": RAW_INPUTS}}
    for name, obj in files.items():
        (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", name)
