"""Score the LLM parser on eval/heldout.json: 10 inputs it was never tuned on.

Each item is parsed with an explicit context: the guest directory from data/guests.json (same
shape as agent.parser.default_context) plus the item's own open offers, never its target.
Fields are scored with the rules of eval/parse_eval.py (exact match after strip/lowercase,
`note` not scored, extra keys reported but not penalised).

Run:
    python eval/run_heldout.py                  # live: one call per input, prints outputs and score
    python eval/run_heldout.py --out FILE       # also writes the raw outputs as JSON to FILE

ANTHROPIC_API_KEY comes from the environment or the git-ignored .env (see run_llm_parse.py).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "eval"))

from agent.parser import EFFORT, MODEL, default_context, parse_llm  # noqa: E402
from parse_eval import norm  # noqa: E402
from run_llm_parse import PRICE_IN, PRICE_OUT, load_key_from_dotenv  # noqa: E402

HELDOUT = json.loads((ROOT / "eval" / "heldout.json").read_text(encoding="utf-8"))["inputs"]


def context_for(item: dict) -> dict:
    ctx = default_context({"seq": -1})  # guest directory only: no offers from the recorded day
    ctx["open_offers"] = item.get("context", {}).get("open_offers", [])
    return ctx


def score_one(target: dict, out: dict) -> tuple[int, int, list[str]]:
    ok = total = 0
    misses = []
    for k, v in target.items():
        if k == "note":
            continue
        total += 1
        good = k in out and norm(out[k]) == norm(v)
        ok += good
        if not good:
            misses.append(f"{k}: expected {v!r}, got {out.get(k, '<missing>')!r}")
    return ok, total, misses


def main() -> None:
    if not load_key_from_dotenv():
        sys.exit("ANTHROPIC_API_KEY not set (env or .env).")
    rows, outputs = [], []
    ok_all = total_all = 0
    for i, item in enumerate(HELDOUT):
        t0 = time.perf_counter()
        out, usage = parse_llm(item, context_for(item), with_usage=True)
        dt = time.perf_counter() - t0
        ok, total, misses = score_one(item["target"], out)
        ok_all += ok
        total_all += total
        extra = sorted(set(out) - set(item["target"]))
        rows.append((dt, usage.input_tokens, usage.output_tokens))
        outputs.append({"index": i, "output": out})
        print(f"{'OK  ' if not misses else 'MISS'} #{i} {item['channel']:<32} {ok}/{total}  {dt:4.1f}s"
              f"  in={usage.input_tokens} out={usage.output_tokens}")
        for m in misses:
            print(f"        {m}")
        if extra:
            print(f"        (extra keys, not scored: {extra})")
    tin, tout = sum(r[1] for r in rows), sum(r[2] for r in rows)
    lat = sorted(r[0] for r in rows)
    median = (lat[len(lat) // 2 - 1] + lat[len(lat) // 2]) / 2 if len(lat) % 2 == 0 else lat[len(lat) // 2]
    cost = tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT
    print(f"\nmodel={MODEL} effort={EFFORT} · {len(rows)} held-out inputs · latency median {median:.1f}s "
          f"max {lat[-1]:.1f}s · tokens in={tin} out={tout} · cost ${cost:.4f} (${cost / len(rows):.4f}/input)")
    print(f"held-out fields correct: {ok_all}/{total_all} = {100 * ok_all / total_all:.0f} %")
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(
            json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
