import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

def evaluate(path="detector/window_predictions.csv"):
    df = pd.read_csv(path)

    y_true = df["actual_spike"]
    y_pred = df["predicted_spike"]

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    print("=== Fraud Spike Detector — Evaluation ===")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1 Score:  {f1:.3f}")
    print()
    print(f"True Positives:  {tp}   (correctly flagged fraud windows)")
    print(f"False Positives: {fp}   (flagged normal windows — false alarms)")
    print(f"False Negatives: {fn}   (missed fraud windows)")
    print(f"True Negatives:  {tn}   (correctly ignored normal windows)")
    print()
    # false positive cost framing — relevant to the track's "explainable, bounded" bar
    fp_rate = fp / (fp + tn) if (fp + tn) > 0 else 0
    print(f"False Positive Rate: {fp_rate*100:.2f}% (fraction of normal windows wrongly flagged)")

    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}

if __name__ == "__main__":
    evaluate()