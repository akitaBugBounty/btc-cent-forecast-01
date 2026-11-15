# btc-cent-forecast-01

Forecast Bitcoin's US-dollar price 240 minutes after a checkpoint, scored on
mean absolute error in cents. Entry for make.fun `btc-cent-forecast-01`.

## Method

Damped mean reversion to the trailing 24-hour mean:

```
forecast = last + 0.2 * (mean(prices[-1440:]) - last)
```

`main.py` (Python 3.13, stdlib only) reads every `*.in` case in
`$MAKEFUN_INPUT_DIR` (default `/input`) and writes one
`/output/<id>.out` per case: `{"forecasts": [{"case": id, "price": x}]}`.
Deterministic, ~0.02 s per case.

## Why this, and what it measured

The score is MAE, so the right point forecast is the conditional median of
the price 240 minutes out. On the six sealed practice cases (BTC minute
closes, Nov 2026), 4h returns mean-revert: every momentum variant tested
made things *worse* than persistence, while reversion to the 24h mean beat
persistence in both walk-forwards run on the practice data:

- Dense walk-forward, 264 checkpoints (every 60 min inside each case):
  persistence 45,117 cents vs this method (beta 0.2) 43,157 cents (-4.3%),
  winning all 6 cases.
- Sparse walk-forward, 66 checkpoints (every 240 min, the final's own
  spacing): persistence 40,950 cents vs this method 39,647 cents (-3.2%),
  winning 5 of 6 cases.

Beta 0.2, not the walk-forward optimum 0.3-0.35, is deliberate: the gain
curve is flat from 0.15 to 0.35, and the smaller beta halves the damage on
the 5 real practice checkpoints, where reversion happened to lose
(48,728 vs persistence 47,055 cents, n=5, standard error ~7,200 cents --
statistically consistent with the walk-forward gain, but prudence costs
almost nothing here). No trend-following, no fitted drift, no regime
switch. The house baseline is persistence; a prize needs beating it.
