import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score, f1_score
from baseline import load_data, build_windows, compute_zscores

FEATURES = ["txn_count", "avg_amount", "away_ratio", "txn_count_z", "avg_amount_z"]

def train_isolation_forest(windows_df, contamination=0.05):
    X = windows_df[FEATURES].fillna(0)
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42
    )
    model.fit(X)
    return model

def predict(model, windows_df):
    X = windows_df[FEATURES].fillna(0)
    raw_pred = model.predict(X)  # -1 = anomaly, 1 = normal
    windows_df["ml_predicted_spike"] = (raw_pred == -1).astype(int)
    windows_df["ml_anomaly_score"] = -model.decision_function(X)  # higher = more anomalous
    return windows_df

if __name__ == "__main__":
    df = load_data()
    windows = build_windows(df)
    windows = compute_zscores(windows)
    windows["actual_spike"] = (windows["fraud_count"] > 0).astype(int)

    model = train_isolation_forest(windows, contamination=0.01)
    windows = predict(model, windows)

    y_true = windows["actual_spike"]
    y_pred = windows["ml_predicted_spike"]

    p = precision_score(y_true, y_pred, zero_division=0)
    r = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    print("=== Isolation Forest — Evaluation ===")
    print(f"Precision: {p:.3f}")
    print(f"Recall:    {r:.3f}")
    print(f"F1 Score:  {f1:.3f}")

    windows.to_csv("detector/ml_predictions.csv", index=False)