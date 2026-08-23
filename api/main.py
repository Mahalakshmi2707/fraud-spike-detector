from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
import os

app = FastAPI(title="Fraud Spike Detector API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



AUDIT_LOG_PATH = "api/audit_log.jsonl"

class TransactionWindow(BaseModel):
    merchant_id: str
    window_start: str
    txn_count: int
    avg_amount: float
    away_ratio: float
    merchant_avg_txn_count: float
    merchant_std_txn_count: float
    merchant_avg_amount: float
    merchant_std_amount: float

Z_THRESHOLD = 3.2
AWAY_RATIO_THRESHOLD = 0.5
MIN_TXNS = 5

def evaluate_window(w: TransactionWindow):
    reasons = []

    if w.txn_count < MIN_TXNS:
        return {
            "flagged": False,
            "confidence": "low",
            "reasons": ["Not enough transactions in window to evaluate reliably"],
        }

    txn_z = (w.txn_count - w.merchant_avg_txn_count) / (w.merchant_std_txn_count or 1)
    amount_z = (w.avg_amount - w.merchant_avg_amount) / (w.merchant_std_amount or 1)

    if txn_z > Z_THRESHOLD:
        reasons.append(f"Transaction velocity {txn_z:.1f}σ above merchant's normal baseline")
    if amount_z > Z_THRESHOLD:
        reasons.append(f"Average amount {amount_z:.1f}σ above merchant's normal baseline")
    if w.away_ratio > AWAY_RATIO_THRESHOLD:
        reasons.append(f"{w.away_ratio*100:.0f}% of transactions from non-home city")

    flagged = len(reasons) > 0
    return {
        "flagged": flagged,
        "confidence": "high" if len(reasons) > 1 else ("medium" if flagged else "low"),
        "reasons": reasons if reasons else ["No anomaly detected"],
        "scores": {"txn_velocity_z": round(txn_z, 2), "avg_amount_z": round(amount_z, 2), "away_ratio": w.away_ratio},
    }

def log_audit(payload: dict, result: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": payload,
        "result": result,
    }
    os.makedirs("api", exist_ok=True)
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

@app.post("/evaluate")
def evaluate(window: TransactionWindow):
    result = evaluate_window(window)
    log_audit(window.dict(), result)
    return result

@app.get("/audit-log")
def get_audit_log(limit: int = 20):
    if not os.path.exists(AUDIT_LOG_PATH):
        return []
    with open(AUDIT_LOG_PATH) as f:
        lines = f.readlines()[-limit:]
    return [json.loads(line) for line in lines]

@app.get("/health")
def health():
    return {"status": "ok"}