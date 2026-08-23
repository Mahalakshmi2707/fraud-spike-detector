# Fraud spike detector

Built for the Razorpay AI Buildathon — Track 02: AI Risk Manager.

Detects fraud-pattern spikes (velocity bursts, amount anomalies, geo-impossible
activity) in merchant transaction streams, with two detection layers, an
explainable API, a full audit trail, and a live dashboard.

## Why this approach

Fraud detection systems live or die on the trade-off between catching fraud
(recall) and not annoying legitimate merchants with false alarms (precision).
Rather than pick one model and hope, this project builds two and compares
them honestly:

| Model | Precision | Recall | F1 | Behavior |
|---|---|---|---|---|
| Rule-based (z-score) | 0.83 | 0.38 | 0.53 | Conservative, explainable, few false alarms |
| Isolation Forest (ML) | 0.27 | 0.64 | 0.38 | Catches more fraud, more noise |

The rule-based detector is precision-heavy, on purpose — it's what runs the
`/evaluate` endpoint and drives the audit trail, since false positives cost
merchant trust. The ML model is included as a comparison layer to show the
recall the system is leaving on the table, and could feed a secondary review
queue rather than an automatic action.

Thresholds (`z=3.2`, `away_ratio=0.5`, `min_txns=5`) were not hand-picked —
they came from a systematic sweep over 60 threshold combinations
(`detector/tune.py`), optimizing for F1 on a held-out labeled set.

## Architecture

```
Synthetic transaction generator (data/generate_data.py)
        |
Labeled fraud spikes injected (data/inject_spikes.py)
        |
Rule-based detector (detector/baseline.py) --- ML comparison (detector/ml_model.py)
        |
Evaluation (detector/evaluate.py, detector/tune.py)
        |
FastAPI service (api/main.py) --- /evaluate, /audit-log, /health
        |
React dashboard (fraud-dashboard/) --- live testing UI + audit log view
```

Every `/evaluate` call is logged to `api/audit_log.jsonl` with the full
input, the decision, and the specific reasons behind it — nothing is a
black box.

## What counts as a spike

Three independently-flagged patterns, computed per merchant in 15-minute
windows:

1. **Velocity burst** — transaction count far above the merchant's rolling
   baseline (z-score)
2. **Amount anomaly** — average transaction amount far above baseline
3. **Geo-impossible spike** — a high share of transactions suddenly coming
   from a city that isn't the merchant's usual one

A window needs at least 5 transactions before any flag is trusted, to avoid
noise from small samples.

## Running it

**Backend**
```bash
cd fraud-spike-detector
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

python data/generate_data.py
python data/inject_spikes.py
python detector/baseline.py
python detector/evaluate.py
python detector/ml_model.py

uvicorn api.main:app --reload
```
API docs: http://127.0.0.1:8000/docs

**Frontend**
```bash
cd fraud-dashboard
npm install
npm run dev
```
Dashboard: http://localhost:5173

## Project structure

```
fraud-spike-detector/
├── data/
│   ├── generate_data.py       # synthetic normal transactions
│   ├── inject_spikes.py       # labeled fraud spike injection
│   ├── merchants.csv
│   └── transactions_labeled.csv
├── detector/
│   ├── baseline.py            # rule-based z-score detector
│   ├── ml_model.py            # Isolation Forest comparison
│   ├── evaluate.py            # precision/recall/F1
│   └── tune.py                # threshold sweep
├── api/
│   └── main.py                # FastAPI service + audit logging
├── fraud-dashboard/            # React frontend
└── requirements.txt
```

## Honest limitations

- Trained and evaluated on synthetic data, not real Razorpay transactions —
  real fraud patterns are messier and this would need retuning
- 15-minute fixed windows; a production system would likely use a sliding
  window
- The rule-based detector's precision (0.83) comes at the cost of missing
  ~62% of fraud windows (recall 0.38) — acceptable for an auto-action system,
  not acceptable as the only line of defense
