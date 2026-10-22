"""Run the LLM parser over every raw input and write eval/predictions.json for parse_eval.py.

Run:
    python eval/run_llm_parse.py              # live: calls the model, writes predictions, scores them
    python eval/run_llm_parse.py --dry-run    # no API call: prints the prompt and schema for input #1

ANTHROPIC_API_KEY comes from the environment; if unset, only that one key is read from the
git-ignored .env at the repo root (no other value is read, nothing is printed).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.parser import MODEL, EFFORT, SCHEMA, SYSTEM, build_user_message, default_context, parse_llm  # noqa: E402

RAW = json.loads((ROOT / "data" / "raw_inputs.json").read_text(encoding="utf-8"))["inputs"]
OUT = ROOT / "eval" / "predictions.json"
PRICE_IN, PRICE_OUT = 2.00, 10.00  # USD per million tokens, claude-sonnet-5-5


def load_key_from_dotenv() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    os.environ["ANTHROPIC_API_KEY"] = value
                    return True
    return False


def dry_run() -> None:
    item = RAW[1]
    print("== system\n" + SYSTEM)
    print("\n== user (input #1, target withheld)\n" + build_user_message(item, default_context(item)))
    print("\n== schema\n" + json.dumps(SCHEMA, indent=1)[:1500] + " ...")


def main() -> None:
    if "--dry-run" in sys.argv:
        dry_run()
        return
    if not load_key_from_dotenv():
        sys.exit("ANTHROPIC_API_KEY not set (env or .env). Use --dry-run to inspect the prompt.")
    preds, rows = [], []
    t_all = time.perf_counter()
    for i, item in enumerate(RAW):
        t0 = time.perf_counter()
        out, usage = parse_llm(item, with_usage=True)
        dt = time.perf_counter() - t0
        preds.append({"index": i, "output": out})
        rows.append((i, item["channel"], dt, usage.input_tokens, usage.output_tokens))
        print(f"#{i} {item['channel']:<32} {dt:5.1f}s  in={usage.input_tokens} out={usage.output_tokens}")
    wall = time.perf_counter() - t_all
    OUT.write_text(json.dumps(preds, ensure_ascii=False, indent=2), encoding="utf-8")
    tin, tout = sum(r[3] for r in rows), sum(r[4] for r in rows)
    cost = tin / 1e6 * PRICE_IN + tout / 1e6 * PRICE_OUT
    lat = sorted(r[2] for r in rows)
    print(f"\nmodel={MODEL} effort={EFFORT} · {len(rows)} inputs · wall {wall:.1f}s · "
          f"latency median {lat[len(lat) // 2]:.1f}s max {lat[-1]:.1f}s · "
          f"tokens in={tin} out={tout} · cost ${cost:.4f}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    subprocess.run([sys.executable, str(ROOT / "eval" / "parse_eval.py")], check=False)


if __name__ == "__main__":
    main()
