import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid

random.seed(42)
np.random.seed(42)

NUM_MERCHANTS = 20
NUM_DAYS = 30
START_DATE = datetime(2026, 7, 1)

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
          "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Vellore"]
PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]

def make_merchants(n):
    merchants = []
    for i in range(n):
        merchants.append({
            "merchant_id": f"M{i+1:03d}",
            "home_city": random.choice(CITIES),
            "avg_txns_per_day": random.randint(20, 100),
            "avg_amount": random.uniform(300, 3000),
            "amount_std": random.uniform(50, 500),
        })
    return merchants

def generate_normal_transactions(merchants, num_days, start_date):
    rows = []
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        for m in merchants:
            # daily txn count varies a bit around the merchant's average
            n_txns = max(0, int(np.random.normal(m["avg_txns_per_day"], m["avg_txns_per_day"] * 0.15)))
            for _ in range(n_txns):
                ts = current_date + timedelta(
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59),
                    seconds=random.randint(0, 59)
                )
                amount = max(10, np.random.normal(m["avg_amount"], m["amount_std"]))
                rows.append({
                    "transaction_id": str(uuid.uuid4())[:8],
                    "merchant_id": m["merchant_id"],
                    "timestamp": ts,
                    "amount": round(amount, 2),
                    "customer_id": f"C{random.randint(1, 5000):05d}",
                    "payment_method": random.choice(PAYMENT_METHODS),
                    "city": m["home_city"] if random.random() > 0.1 else random.choice(CITIES),
                    "is_fraud_spike": 0  # will be overwritten in step 3 for injected spikes
                })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    merchants = make_merchants(NUM_MERCHANTS)
    df = generate_normal_transactions(merchants, NUM_DAYS, START_DATE)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # save merchants profile too, we'll need it in step 3 and step 4
    pd.DataFrame(merchants).to_csv("data/merchants.csv", index=False)
    df.to_csv("data/synthetic_transactions.csv", index=False)

    print(f"Generated {len(df)} normal transactions across {NUM_MERCHANTS} merchants over {NUM_DAYS} days.")
    print(df.head())