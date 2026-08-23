import pandas as pd
import numpy as np

WINDOW = "15min"
Z_THRESHOLD = 3.2

def load_data(path="data/transactions_labeled.csv"):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df

def build_windows(df):
    """Aggregate transactions into per-merchant, per-window features."""
    df = df.set_index("timestamp")
    grouped = (
        df.groupby("merchant_id")
        .resample(WINDOW)
        .agg(
            txn_count=("transaction_id", "count"),
            avg_amount=("amount", "mean"),
            fraud_count=("is_fraud_spike", "sum"),  # for evaluation only, not used by detector
        )
    )
    grouped["avg_amount"] = grouped["avg_amount"].fillna(0)
    grouped = grouped.reset_index()

    # non-home-city ratio per window
    home_cities = df.reset_index().groupby("merchant_id")["city"].agg(lambda x: x.mode()[0])
    df_reset = df.reset_index()
    df_reset["is_away"] = df_reset.apply(
        lambda r: r["city"] != home_cities[r["merchant_id"]], axis=1
    )
    away_ratio = (
        df_reset.set_index("timestamp")
        .groupby("merchant_id")
        .resample(WINDOW)["is_away"]
        .mean()
        .fillna(0)
        .reset_index()
        .rename(columns={"is_away": "away_ratio"})
    )

    merged = grouped.merge(away_ratio, on=["merchant_id", "timestamp"], how="left")
    merged["away_ratio"] = merged["away_ratio"].fillna(0)
    return merged

def compute_zscores(windows_df):
    """Compute rolling z-scores per merchant for txn_count and avg_amount."""
    windows_df = windows_df.sort_values(["merchant_id", "timestamp"])
    results = []

    for merchant_id, group in windows_df.groupby("merchant_id"):
        group = group.copy()
        roll_mean = group["txn_count"].rolling(window=20, min_periods=5).mean()
        roll_std = group["txn_count"].rolling(window=20, min_periods=5).std().replace(0, np.nan)
        group["txn_count_z"] = (group["txn_count"] - roll_mean) / roll_std

        amt_mean = group["avg_amount"].rolling(window=20, min_periods=5).mean()
        amt_std = group["avg_amount"].rolling(window=20, min_periods=5).std().replace(0, np.nan)
        group["avg_amount_z"] = (group["avg_amount"] - amt_mean) / amt_std

        results.append(group)

    return pd.concat(results).fillna(0)

def flag_spikes(windows_df, z_threshold=Z_THRESHOLD, away_ratio_threshold=0.5, min_txns=5):
    reliable = windows_df["txn_count"] >= min_txns

    windows_df["flag_velocity"] = (windows_df["txn_count_z"] > z_threshold) & reliable
    windows_df["flag_amount"] = (windows_df["avg_amount_z"] > z_threshold) & reliable
    windows_df["flag_geo"] = (windows_df["away_ratio"] > away_ratio_threshold) & reliable

    windows_df["predicted_spike"] = (
        windows_df["flag_velocity"] | windows_df["flag_amount"] | windows_df["flag_geo"]
    ).astype(int)

    windows_df["actual_spike"] = (windows_df["fraud_count"] > 0).astype(int)
    return windows_df

if __name__ == "__main__":
    df = load_data()
    windows = build_windows(df)
    windows = compute_zscores(windows)
    windows = flag_spikes(windows)

    windows.to_csv("detector/window_predictions.csv", index=False)

    print(f"Total windows analyzed: {len(windows)}")
    print(f"Predicted spikes: {windows['predicted_spike'].sum()}")
    print(f"Actual fraud windows: {windows['actual_spike'].sum()}")
    print(windows[windows["predicted_spike"] == 1][
        ["merchant_id", "timestamp", "txn_count", "txn_count_z", "avg_amount_z", "away_ratio", "actual_spike"]
    ].head(10))