import pandas as pd
import numpy as np
import random
from datetime import timedelta
import uuid

random.seed(7)
np.random.seed(7)

NUM_SPIKE_EVENTS = 40  # total injected fraud events across the dataset
PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet"]
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
          "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Vellore"]

def inject_velocity_burst(merchant, start_time, txns_range=(200, 400)):
    n = random.randint(*txns_range)
    rows = []
    window_minutes = random.randint(15, 90)  # burst duration
    for _ in range(n):
        ts = start_time + timedelta(seconds=random.randint(0, window_minutes * 60))
        amount = max(10, np.random.normal(merchant["avg_amount"] * 0.6, merchant["amount_std"]))
        rows.append(_make_row(merchant, ts, amount, merchant["home_city"]))
    return rows

def inject_amount_anomaly(merchant, start_time, txns_range=(15, 40)):
    n = random.randint(*txns_range)
    rows = []
    window_minutes = random.randint(30, 180)
    for _ in range(n):
        ts = start_time + timedelta(seconds=random.randint(0, window_minutes * 60))
        amount = merchant["avg_amount"] + merchant["amount_std"] * random.uniform(6, 12)
        rows.append(_make_row(merchant, ts, amount, merchant["home_city"]))
    return rows

def inject_geo_spike(merchant, start_time, txns_range=(20, 60)):
    n = random.randint(*txns_range)
    rows = []
    window_minutes = random.randint(20, 120)
    far_city = random.choice([c for c in CITIES if c != merchant["home_city"]])
    for _ in range(n):
        ts = start_time + timedelta(seconds=random.randint(0, window_minutes * 60))
        amount = max(10, np.random.normal(merchant["avg_amount"], merchant["amount_std"]))
        rows.append(_make_row(merchant, ts, amount, far_city))
    return rows

def _make_row(merchant, ts, amount, city):
    return {
        "transaction_id": str(uuid.uuid4())[:8],
        "merchant_id": merchant["merchant_id"],
        "timestamp": ts,
        "amount": round(max(10, amount), 2),
        "customer_id": f"C{random.randint(1, 5000):05d}",
        "payment_method": random.choice(PAYMENT_METHODS),
        "city": city,
        "is_fraud_spike": 1
    }

if __name__ == "__main__":
    df = pd.read_csv("data/synthetic_transactions.csv", parse_dates=["timestamp"])
    merchants = pd.read_csv("data/merchants.csv").to_dict("records")

    min_ts, max_ts = df["timestamp"].min(), df["timestamp"].max()
    injectors = [inject_velocity_burst, inject_amount_anomaly, inject_geo_spike]

    all_spike_rows = []
    for _ in range(NUM_SPIKE_EVENTS):
        merchant = random.choice(merchants)
        injector = random.choice(injectors)
        random_offset_seconds = random.randint(0, int((max_ts - min_ts).total_seconds()))
        start_time = min_ts + timedelta(seconds=random_offset_seconds)
        all_spike_rows.extend(injector(merchant, start_time))

    spike_df = pd.DataFrame(all_spike_rows)
    full_df = pd.concat([df, spike_df], ignore_index=True)
    full_df = full_df.sort_values("timestamp").reset_index(drop=True)

    full_df.to_csv("data/transactions_labeled.csv", index=False)

    print(f"Injected {len(spike_df)} fraudulent transactions across {NUM_SPIKE_EVENTS} spike events.")
    print(f"Total transactions: {len(full_df)}  |  Fraud rate: {full_df['is_fraud_spike'].mean()*100:.2f}%")
    print(full_df["is_fraud_spike"].value_counts())