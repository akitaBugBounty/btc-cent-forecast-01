"""BTC 4h-ahead point forecast (make.fun btc-cent-forecast-01).

Method: damped mean reversion to the trailing 24h mean.
    forecast = last + 0.2 * (mean(prices[-1440:]) - last)

Why: the score is mean absolute error in cents, so the honest point
forecast is the conditional median of the price 240 minutes out. Over the
six sealed practice cases, 4h returns mean-revert: every momentum variant
tested made things WORSE than persistence, while reversion to the 24h mean
beat persistence everywhere it was measured:
  - dense walk-forward, 264 checkpoints (every 60 min inside each case):
    persistence 45,117 cents, this method (beta 0.2) 43,157 cents (-4.3%),
    winning all 6 cases.
  - sparse walk-forward, 66 checkpoints (every 240 min, the final's own
    spacing): persistence 40,950 cents, this method 39,647 cents (-3.2%),
    winning 5 of 6 cases.
Beta 0.2 (not the walk-forward optimum 0.3-0.35) is deliberate: the gain
curve is flat from 0.15 to 0.35, and the smaller beta halves the damage on
the 5 real practice checkpoints, where reversion happened to lose
(n=5, standard error ~10,700 cents, so that loss is statistically
consistent with the walk-forward gain -- but prudence costs almost
nothing here). No trend-following, no fitted drift, no regime switch.

Stdlib only. Deterministic: same case in, same bytes out. Reads every
*.in file in $MAKEFUN_INPUT_DIR (default /input) in name order and writes
one /output/<id>.out per case: {"forecasts": [{"case": id, "price": x}]}.
"""

import json
import os
from pathlib import Path

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

WINDOW = 1440          # trailing 24h of 1-minute closes
BETA = 0.2             # damping on the pull toward the trailing mean
MIN_PRICE = 0.01
MAX_PRICE = 10_000_000


def price5(x: float) -> float:
    """Round to the pool's price scale (5 decimals of a dollar), clamped."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def forecast(prices) -> float:
    if not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    if not isinstance(last, (int, float)) or last != last or last in (float("inf"), float("-inf")):
        raise ValueError("last price is not a finite number")
    window = prices[-WINDOW:] if len(prices) > WINDOW else prices
    if any(not isinstance(x, (int, float)) or x != x or x in (float("inf"), float("-inf")) for x in window):
        raise ValueError("trailing window holds a non-finite price")
    mean = sum(window) / len(window)
    return price5(last + BETA * (mean - last))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = sorted(p for p in INPUT_DIR.iterdir() if p.name.endswith(".in"))
    for path in inputs:
        case_id = path.name[: -len(".in")]
        with open(path, "r", encoding="utf-8") as f:
            case = json.load(f)
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        price = forecast(markets[0]["prices"])
        out = {"forecasts": [{"case": case_id, "price": price}]}
        with open(OUTPUT_DIR / f"{case_id}.out", "w", encoding="utf-8") as f:
            f.write(json.dumps(out) + "\n")


if __name__ == "__main__":
    main()
