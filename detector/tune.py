import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score
from baseline import load_data, build_windows, compute_zscores

def flag_spikes_custom(windows_df, z_threshold, away_ratio_threshold, min_txns):
    reliable = windows_df["txn_count"] >= min_txns
    flag_velocity = (windows_df["txn_count_z"] > z_threshold) & reliable
    flag_amount = (windows_df["avg_amount_z"] > z_threshold) & reliable
    flag_geo = (windows_df["away_ratio"] > away_ratio_threshold) & reliable
    return (flag_velocity | flag_amount | flag_geo).astype(int)

if __name__ == "__main__":
    df = load_data()
    windows = build_windows(df)
    windows = compute_zscores(windows)
    y_true = (windows["fraud_count"] > 0).astype(int)

    z_options = [2.5, 3.0, 3.2, 3.5, 4.0]
    away_options = [0.4, 0.5, 0.6, 0.7]
    min_txns_options = [3, 5, 8]

    results = []
    for z in z_options:
        for away in away_options:
            for mt in min_txns_options:
                y_pred = flag_spikes_custom(windows, z, away, mt)
                p = precision_score(y_true, y_pred, zero_division=0)
                r = recall_score(y_true, y_pred, zero_division=0)
                f1 = f1_score(y_true, y_pred, zero_division=0)
                results.append({"z_threshold": z, "away_ratio_threshold": away,
                                 "min_txns": mt, "precision": p, "recall": r, "f1": f1})

    results_df = pd.DataFrame(results).sort_values("f1", ascending=False)
    results_df.to_csv("detector/threshold_sweep.csv", index=False)

    print("Top 10 threshold combinations by F1 score:")
    print(results_df.head(10).to_string(index=False))