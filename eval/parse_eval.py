"""Parser evaluation: how well does the agent turn raw inputs into structured events?

This is the "Evidence It Works" number on the agent side. On the day, the agent's
parser writes its outputs to eval/predictions.json:

    [{"index": 0, "output": {...}}, {"index": 1, "output": {...}}, ...]

where `index` is the position of the input in data/raw_inputs.json. This script compares
each output with the golden `target`, field by field, and prints per-input and overall
field accuracy, plus the inputs that failed. Keys present in the target are scored;
extra keys in the output are reported but not penalised.

Run:
    python eval/parse_eval.py                          # scores eval/predictions.json
    python eval/parse_eval.py --self-test              # targets vs themselves (must be 100 %) + a broken copy
Report it honestly in the demo: "recorded scenario, N inputs, X % of fields correct".
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = json.loads((ROOT / "data" / "raw_inputs.json").read_text(encoding="utf-8"))["inputs"]


def norm(v):
    if isinstance(v, str):
        return v.strip().lower()
    if isinstance(v, list):
        return [norm(x) for x in v]
    if isinstance(v, dict):
        return {k: norm(x) for k, x in v.items()}
    return v


def score(predictions: list[dict]) -> tuple[int, int, list[str]]:
    by_index = {p["index"]: p.get("output", {}) for p in predictions}
    ok = total = 0
    lines = []
    for i, item in enumerate(RAW):
        target, out = item["target"], by_index.get(i, {})
        hits = []
        for k, v in target.items():
            if k == "note":
                continue
            total += 1
            good = k in out and norm(out[k]) == norm(v)
            ok += good
            if not good:
                hits.append(f"{k}: expected {v!r}, got {out.get(k, '<missing>')!r}")
        extra = sorted(set(out) - set(target))
        status = "OK  " if not hits else "MISS"
        lines.append(f"  {status} #{i} {item['channel']}" + ("" if not hits else "\n        " + "\n        ".join(hits))
                     + (f"\n        (extra keys, not scored: {extra})" if extra else ""))
    return ok, total, lines


def report(name: str, preds: list[dict]) -> float:
    ok, total, lines = score(preds)
    print(f"\n== {name}")
    print("\n".join(lines))
    pct = 100 * ok / total if total else 0.0
    print(f"  fields correct: {ok}/{total} = {pct:.0f} %")
    return pct


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        perfect = [{"index": i, "output": copy.deepcopy(x["target"])} for i, x in enumerate(RAW)]
        assert report("self-test: targets as predictions", perfect) == 100.0
        broken = copy.deepcopy(perfect)
        broken[1]["output"]["eta"] = "11:51"                 # misread time in the French WhatsApp
        broken[3]["output"].pop("back_in_service", None)     # dropped a field
        assert report("self-test: two injected errors", broken) < 100.0
        print("\nself-test passed")
        sys.exit(0)
    path = ROOT / "eval" / "predictions.json"
    if not path.exists():
        sys.exit(f"missing {path} - write the parser's outputs there first (see docstring)")
    report("agent parser", json.loads(path.read_text(encoding="utf-8")))
